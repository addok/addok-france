import re

from addok.helpers.text import Token

TYPES = [
    'avenue', 'rue', 'boulevard', 'all[ée]es?', 'impasse', 'place',
    'chemin', 'rocade', 'route', 'l[ôo]tissement', 'mont[ée]e', 'c[ôo]te',
    'clos', 'champ', 'bois', 'taillis', 'boucle', 'passage', 'domaine',
    'étang', 'etang', 'quai', 'desserte', 'pré', 'porte', 'square', 'mont',
    'r[ée]sidence', 'parc', 'cours?', 'promenade', 'hameau', 'faubourg',
    'ilot', 'berges?', 'via', 'cit[ée]', 'sent(e|ier)', 'rond[- ][Pp]oint',
    'pas(se)?', 'carrefour', 'traverse', 'giratoire', 'esplanade', 'voie',
    'chauss[ée]e',
]
TYPES_REGEX = '|'.join(
    map(lambda x: '[{}{}]{}'.format(x[0], x[0].upper(), x[1:]), TYPES)
)
ORDINAL_REGEX = 'bis|ter|quater|quinquies|sexies|[a-z]'


def clean_query(q):
    q = re.sub('c(e|é)dex ?[\d]*', '', q, flags=re.IGNORECASE)
    q = re.sub(r'\bbp ?[\d]*', '', q, flags=re.IGNORECASE)
    q = re.sub(r'\bcs ?[\d]*', '', q, flags=re.IGNORECASE)
    q = re.sub('\d{,2}(e|[eè]me) ([eé]tage)', '', q, flags=re.IGNORECASE)
    q = re.sub(' {2,}', ' ', q, flags=re.IGNORECASE)
    q = re.sub('[ -]s/[ -]', ' sur ', q, flags=re.IGNORECASE)
    q = re.sub('[ -]s/s[ -]', ' sous ', q, flags=re.IGNORECASE)
    q = re.sub('^lieux?[ -]?dits?\\b(?=.)', '', q, flags=re.IGNORECASE)
    q = q.strip()
    return q


def extract_address(q):
    m = extract_address_pattern.search(q)
    return m.group() if m else q
extract_address_pattern = re.compile(
    r'(\b\d{1,4}( *(' + ORDINAL_REGEX + '))?,? +(' + TYPES_REGEX + ') .*(\d{5})?).*',  # noqa
    flags=re.IGNORECASE)


def neighborhood(iterable, first=None, last=None):
    """
    Yield the (previous, current, next) items given an iterable.

    You can specify a `first` and/or `last` item for bounds.
    """
    iterator = iter(iterable)
    previous = first
    current = next(iterator)  # Throws StopIteration if empty.
    for next_ in iterator:
        yield (previous, current, next_)
        previous = current
        current = next_
    yield (previous, current, last)


def glue_ordinal(tokens):
    """Glue '3' and 'bis'."""
    previous = None
    for _, token, next_ in neighborhood(tokens):
        if token.isdigit():
            previous = token
        elif previous is not None:
            # Matches "bis" either followed by a type or nothing.
            if (ordinal_pattern.match(token) and
                    (not next_ or (next_ and types_pattern.match(next_)))):
                raw = '{} {}'.format(previous, token)
                # Space removed to maximize chances to get a hit.
                token = token.update(raw.replace(' ', ''), raw=raw)
            else:
                yield previous
            previous = None
            yield token
        else:
            yield token

ordinal_pattern = re.compile(r'\b(' + ORDINAL_REGEX + r')\b',
                             flags=re.IGNORECASE)
types_pattern = re.compile(TYPES_REGEX, flags=re.IGNORECASE)


def fold_ordinal(s):
    """3bis => 3b."""
    if s not in _CACHE:
        rules = (
            ("(\d{1,4})bis\\b", "\g<1>b"),
            ("(\d{1,4})ter\\b", "\g<1>t"),
            ("(\d{1,4})quater\\b", "\g<1>q"),
            ("(\d{1,4})quinquies\\b", "\g<1>c"),
            ("(\d{1,4})sexies\\b", "\g<1>s"),
        )
        _s = s
        for pattern, repl in rules:
            _s = re.sub(pattern, repl, _s, flags=re.IGNORECASE)
        _CACHE[s] = _s
    return Token(_CACHE[s], raw=s.raw)
_CACHE = {}


def remove_leading_zeros(s):
    """0003 => 3."""
    return Token(re.sub("0*(\d+)", "\g<1>", s, flags=re.IGNORECASE), raw=s)


def make_labels(helper, result):
    if not result.labels:
        housenumber = getattr(result, 'housenumber', None)

        def add(labels, label):
            labels.insert(0, label)
            if housenumber:
                label = '{} {}'.format(housenumber, label)
                labels.insert(0, label)

        city = result.city
        postcode = result.postcode
        names = result._rawattr('name')
        if not isinstance(names, (list, tuple)):
            names = [names]
        for name in names:
            labels = []
            label = name
            add(labels, label)
            if city and city != label:
                if postcode:
                    label = '{} {}'.format(label, postcode)
                    add(labels, label)
                label = '{} {}'.format(label, city)
                add(labels, label)
            result.labels.extend(labels)
