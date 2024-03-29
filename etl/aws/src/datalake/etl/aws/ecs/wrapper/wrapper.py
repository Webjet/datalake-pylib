import base64
import json
import logging
import signal
import socket
import sys
import uuid
from datetime import datetime

from .actions import END, START, parse_actions
from .args import parse_argv, parse_cli, parse_config, parse_os_args
from .command import get_command
from .metrics import SingleMetric, WrapperMetrics
from .process import WrapperProcess


def get_dimensions(job: str, metrics: WrapperMetrics) -> dict:
    return {
        "Team": metrics.team,
        "Group": metrics.group,
        "Job": job,
    }


def main() -> None:

    # ************************
    # PARSE ARGV and OS ENV
    # ************************

    args = parse_argv()
    oenv = parse_os_args()

    # ************************
    # GET UUID
    # ************************

    request_uuid = uuid.uuid4()
    if "ExecutionId" in oenv and oenv["ExecutionId"]:
        request_uuid = oenv["ExecutionId"]

    now = datetime.utcnow()

    logging.basicConfig(
        format="%(asctime)s %(levelname)5s %(message)s",
        level=logging.DEBUG if args.debug else logging.INFO,
    )

    logging.info("HTN: {0}".format(socket.gethostname()))
    logging.info("UID: {0}".format(request_uuid))
    logging.info("ARV: {0}".format(sys.argv))
    logging.info("OSV: {0}".format(oenv))

    # ************************
    # PARSE CONFIG and CLI (cli-json)
    # ************************

    config = parse_config(
        config_path=args.config,
    )
    cli = parse_cli(cli_json=args.cli_json, config=config)

    logging.info("ARG: {0}".format(args))
    logging.info("CFG: {0}".format(config))
    logging.info("CLI: {0}".format(cli))

    oenv.update(
        {
            "_execution": {
                "config": config,
                "cli": cli,
            }
        }
    )

    # ************************
    # METRICS
    # ************************

    metrics = WrapperMetrics(
        namespace=config["metrics"]["namespace"],
        team=config["metrics"]["team"],
        group=cli["group"],
        aws_region=config["metrics"]["region"],
    )
    logging.info("MTS: {0}".format(metrics))

    # ************************
    # ACTIONS
    # ************************

    actions = parse_actions(actions=cli["actions"], oenv=oenv)
    logging.info("ACT: {0}".format(actions))

    metrics.add(
        SingleMetric(
            metric_name="Start",
            dimensions=get_dimensions(cli["job"], metrics),
            value=1,
        )
    )
    if not args.dry:
        _ = metrics.send()

    # ************************
    # PROCESS
    # ************************

    # NOTE: Execute start actions
    actions.execute(stage=START, dry=args.dry)

    # NOTE: Use OENV from actions for parsing the command
    cmd = get_command(entrypoint=cli["entrypoint"], command=cli["command"], oenv=actions.oenv)

    logging.info("CMD: {0}".format(cmd))

    request = {
        "uuid": str(request_uuid),
        "host": socket.gethostname(),
        "args": sys.argv,
        "oenv": oenv,
        "config": config,
        "cli": cli,
        "cmd": cmd,
        "dry": args.dry,
        "timestamp": now.isoformat(),
    }
    request_b64 = base64.b64encode(json.dumps(request).encode("utf-8"))
    logging.info("REQ: {0}".format(request_b64.decode("utf-8")))

    # ************************
    # Wrapper Process
    # ************************

    proc = WrapperProcess(
        cmd=cmd,
        metrics=metrics,
        rate=int(config["metrics"]["rate"]),
        dimensions=get_dimensions(cli["job"], metrics),
        timeout=int(config["wrapper"]["timeout"]),
    )

    signals_to_handle = [signal.SIGTERM]
    for sig in signals_to_handle:
        signal.signal(sig, proc.signal_handler)

    exit_code, duration, p = proc.run(dry=args.dry, retries=cli["retries"])

    # NOTE: Get StdOut and StdErr
    stdout: str = None
    try:
        stdout = p.stdout.read() if p else None
    except Exception:
        pass

    stderr: str = None
    try:
        stderr = p.stderr.read() if p else None
    except Exception:
        pass

    logging.info("EXC: {0}".format(exit_code))

    if exit_code != 0 and p:
        logging.error("ERR: {0}".format(stderr))

    if args.verbose:
        logging.info("OUT: {0}".format(stdout))
        logging.info("ERR: {0}".format(stderr))
    else:
        logging.debug("OUT: {0}".format(stdout))

    logging.info("DUR: {0}".format(int(round(duration, 0))))

    # NOTE: Send metrics about the process
    metrics.add(
        SingleMetric(
            metric_name="Duration",
            dimensions=get_dimensions(cli["job"], metrics),
            value=int(round(duration, 0)),
            unit="Seconds",
        ),
        SingleMetric(
            metric_name="Exit",
            dimensions=get_dimensions(cli["job"], metrics),
            value=0 if exit_code == 0 else 1,
        ),
        SingleMetric(
            metric_name="Exit",
            dimensions={"Team": metrics.team},
            value=0 if exit_code == 0 else 1,
        ),
        SingleMetric(
            metric_name="End",
            dimensions=get_dimensions(cli["job"], metrics),
            value=1,
        ),
    )

    if not args.dry:
        _ = metrics.send()

    # NOTE: Update oenv with process data.
    actions.oenv.update(
        {
            "ExitCode": exit_code,
            "Duration": int(round(duration, 0)),
            "StdOut": stdout,
            "StdErr": stderr,
        }
    )

    actions.execute(stage=END, dry=args.dry)

    # NOTE: Return exit code to caller
    exit(exit_code)
