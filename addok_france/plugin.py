from addok import hooks
from addok.helpers import yielder

from .utils import (clean_query, extract_address, fold_ordinal, glue_ordinal,
                    make_labels)


@hooks.register
def addok_configure(config):
    config.QUERY_PROCESSORS.extend(
        map(yielder, [extract_address, clean_query, glue_ordinal,
                      fold_ordinal]))

    config.HOUSENUMBER_PROCESSORS.extend(
        [yielder(glue_ordinal), yielder(fold_ordinal)])

    default = 'addok.helpers.results.make_labels'
    if default in config.SEARCH_RESULT_PROCESSORS:
        idx = config.SEARCH_RESULT_PROCESSORS.index(default)
        config.SEARCH_RESULT_PROCESSORS[idx] = make_labels
