# Addok plugin for France specifics

## Installation

    pip install addok-france


## Configuration

- Add QUERY_PROCESSORS_PYPATHS

    QUERY_PROCESSORS_PYPATHS = [
        …,
        "addok_france.extract_address",
        "addok_france.clean_query",
    ]

- Add PROCESSORS_PYPATHS

    PROCESSORS_PYPATHS = [
        …,
        "addok_france.glue_ordinal",
        "addok_france.fold_ordinal",
        "addok_france.flag_housenumber",
        …,
    ]

- Replace default `make_labels` by France dedicated one:

    SEARCH_RESULT_PROCESSORS_PYPATHS = [
        'addok_france.make_labels',
        …,
    ]
