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
        "addok_france.glue_ordinal",
        "addok_france.fold_ordinal",
    ]

- Add HOUSENUMBER_PROCESSORS

    HOUSENUMBER_PROCESSORS = [
        "addok_france.glue_ordinal",
        "addok_france.fold_ordinal",
    ]

- Replace default make_labels `addok.helpers.results.make_labels` by France
  dedicated one:

    SEARCH_RESULT_PROCESSORS = [
        …,
        'addok_france.make_labels',
        …,
    ]
