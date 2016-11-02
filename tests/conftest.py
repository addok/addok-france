def pytest_configure():
    from addok.config import config
    config.QUERY_PROCESSORS = [
        "addok_france.extract_address",
        "addok_france.clean_query",
        "addok_france.remove_leading_zeros",
        "addok_france.glue_ordinal",
        "addok_france.fold_ordinal",
    ]
    config.HOUSENUMBER_PROCESSORS = [
        "addok_france.remove_leading_zeros",
        "addok_france.glue_ordinal",
        "addok_france.fold_ordinal",
    ]
    config.SEARCH_RESULT_PROCESSORS = [
        'addok.helpers.results.match_housenumber',
        'addok_france.make_labels',
        'addok.helpers.results.score_by_importance',
        'addok.helpers.results.score_by_autocomplete_distance',
        'addok.helpers.results.score_by_ngram_distance',
        'addok.helpers.results.score_by_geo_distance',
    ]
