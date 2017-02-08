# Addok plugin for France specifics

## Installation

    # No pypi release yet.
    pip install git+https://github.com/addok/addok-france


## Configuration

- Add QUERY_PROCESSORS

    QUERY_PROCESSORS = [
        …,
        "addok_france.extract_address",
        "addok_france.clean_query",
    ]

- Add PROCESSORS

    PROCESSORS = [
        …,
        "addok_france.glue_ordinal",
        "addok_france.fold_ordinal",
        "addok_france.flag_housenumber",
        …,
    ]

- Replace default `match_housenumber` and `make_labels` by France dedicated ones:

    SEARCH_RESULT_PROCESSORS = [
        'addok_france.match_housenumber',
        'addok_france.make_labels',
        …,
    ]
