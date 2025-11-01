# addok-france

Addok plugin for France-specific address geocoding with advanced query processing and result formatting.

## Features

- **Query preprocessing**: Extract and clean French address components
- **Ordinal number handling**: Proper processing of ordinal numbers (1er, 2ème, etc.)
- **House number flagging**: Specialized handling of French house numbers
- **French labels**: France-specific result label formatting

## Installation

```bash
pip install addok-france
```

## Configuration

### Query processors

Add France-specific query processors to handle address extraction and cleaning:

```python
QUERY_PROCESSORS_PYPATHS = [
    …,
    "addok_france.extract_address",
    "addok_france.clean_query",
]
```

### String processors

Add processors for ordinal numbers and house number handling:

```python
PROCESSORS_PYPATHS = [
    …,
    "addok_france.glue_ordinal",
    "addok_france.fold_ordinal",
    "addok_france.flag_housenumber",
    …,
]
```

### Result processors

Replace default `make_labels` with France-specific label formatting:

```python
SEARCH_RESULT_PROCESSORS_PYPATHS = [
    'addok_france.make_labels',
    …,
]
```

