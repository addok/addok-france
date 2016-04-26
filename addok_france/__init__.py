from addok.helpers import yielder

from . import utils
try:
    import pkg_resources
except ImportError:  # pragma: no cover
    pass
else:
    if __package__:
        VERSION = pkg_resources.get_distribution(__package__).version


clean_query = yielder(utils.clean_query)
extract_address = yielder(utils.extract_address)
fold_ordinal = yielder(utils.fold_ordinal)
glue_ordinal = yielder(utils.glue_ordinal)
make_labels = utils.make_labels
