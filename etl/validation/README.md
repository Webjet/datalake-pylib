# Validation Package

**Work in progress**

## Installation

Get command: (EARLY)

```bash
gpip get github.com/Webjet/datalake-pylib@etl.validation#name=datalake-etl.etl-validation\;branch=package.etl
```

On requirements:

```
github.com/Webjet/datalake-pylib@etl.validation#name=datalake-etl.etl-validation;branch=package.etl
```

## Import

```python
from datalake_etl import etl_validation
```

### Return schemas

```python
_RETURN_METHOD_SCHEMA = {
    "success": True or False,
    "fail": "Fail message (Customizable)"
}
```

```python
_RETURN_SCHEMA = {
    "success": True or False,
    "fail": {
        "message": "Fail message (Customizable)"
        ,"column": "Column where the fail occurs"
        ,"failindex": ["Array of columns"] | "Column"
        ,"type": ["Type of the column"]
        ,"value": "First value (Comparison)"
        ,"value2": "Second value (Comparison)"
        ,"time": "Datetime where the fail occurs (datetime)"
    }
}
```

```python
_FUNCTIONS_SCHEMA = {
    "column_to_check (case-sensitive)": ["Array of methods"]
}
```