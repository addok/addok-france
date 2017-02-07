def pytest_configure():
    from addok.config import config
    config.QUERY_PROCESSORS = [
        "addok_france.extract_address",
        "addok_france.clean_query",
        "addok_france.remove_leading_zeros",
    ]
    config.SEARCH_RESULT_PROCESSORS = [
        'addok_france.match_housenumber',
        'addok_france.make_labels',
        'addok.helpers.results.score_by_importance',
        'addok.helpers.results.score_by_autocomplete_distance',
        'addok.helpers.results.score_by_ngram_distance',
        'addok.helpers.results.score_by_geo_distance',
    ]
    config.PROCESSORS = [
        "addok.helpers.text.tokenize",
        "addok.helpers.text.normalize",
        "addok_france.preprocess_housenumber",
        "addok_france.flag_housenumber",
        "addok.helpers.text.synonymize",
    ]
