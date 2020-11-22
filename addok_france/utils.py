import re

TYPES = [
    'av(enue)?', 'r(ue)?', 'b(oulevar|l?v?)?d', 'all([ée]es?)?', 'imp(asse)?', 'pl(ace)?',
    'che?(m(in)?)?', 'rocade', 'r(ou)?te', 'l[ôo]t(issement)?', 'mont[ée]e', 'c[ôo]te',
    'clos', 'ch(am)?p', 'bois', 'taillis', 'b(ou)?cle', 'pass(age)?', 'dom(aine)?',
    'eta?ng', 'éta?ng', 'desserte', 'pré', 'porte', 'squ?(are)?', 'mont',
    'r[ée]s(idence)?', 'parc', 'cours?', 'pro?m(enade)?', 'ham(eau)?', 'f(aubour|b|bour)?g',
    'ilot', 'ber(ges?)?', 'via', 'cit[ée]', 'sent(e|ier)', 'rond[- ][Pp]oint', 'rd?pt',
    'pas(se)?', 'carr?(efour)?', 'trav(erse)?', 'giratoire', 'espl?(anade)?', 'voie',
    'chauss[ée]e', 'aer(odrome)?', 'gr(ande?)?', 'gr(e|es|s)?', 'anc(ien(ne)?)?', 'c(en)?tre',
    'devi(ation)?', 'dig(ue)?', 'embr(anchement)?', 'jard(in)?', 'j(et)?te', 'p(asserel)?le',
    'p(or)?te', 'p(lace)?tte', 'p(arvis|rv|vr)', 'q(ua|rt)(ier)?', 'qu?(ai)?',
    'r(uel)?le','t(erra)?sse','tunn?(el)?', 'viad(uc)?', 'v(il)?la',
]
TYPES_REGEX = '|'.join(
    map(lambda x: '[{}{}]{}'.format(x[0], x[0].upper(), x[1:]), TYPES)
)
ORDINAL_REGEX = 'bis|ter|quater|quinquies|sexies|[a-z]'

FOLD = {
    'bis': 'b',
    'ter': 't',
    'quater': 'q',
    'quinquies': 'c',
    'sexies': 's',
}

# Try to match address pattern when the search sting contains extra info (for
# example "22 rue des Fleurs 59350 Lille" will be extracted from
# "XYZ Ets bâtiment B 22 rue des Fleurs 59350 Lille Cedex 23").
EXTRACT_ADDRESS_PATTERN = re.compile(
    r'(\b\d{1,4}( *(' + ORDINAL_REGEX + '))?,? +(' + TYPES_REGEX + ') .*(\d{5})?).*',  # noqa
    flags=re.IGNORECASE)

# Match "bis", "ter", "b", etc.
ORDINAL_PATTERN = re.compile(r'\b(' + ORDINAL_REGEX + r')\b',
                             flags=re.IGNORECASE)

# Match "rue", "boulevard", "bd", etc.
TYPES_PATTERN = re.compile(r'\b(' + TYPES_REGEX + r')\b', flags=re.IGNORECASE)


# Match number + ordinal, once glued by glue_ordinal (or typed like this in the
# search string, for example "6bis", "234ter").
FOLD_PATTERN = re.compile(r'^(\d{1,4})(' + ORDINAL_REGEX + ')$',
                          flags=re.IGNORECASE)


# Match number once cleaned by glue_ordinal and fold_ordinal (for example
# "6b", "234t"…)
NUMBER_PATTERN = re.compile(r'\b\d{1,4}[a-z]?\b', flags=re.IGNORECASE)


def clean_query(q):
    q = re.sub(r'(^| )((b(oi)?te|case) postale|b\.?p\.?|cs|tsa|cidex) *(n(o|°|) *|)[\d]+ *',
               r'\1', q, flags=re.IGNORECASE)
    q = re.sub(r'([\d]{2})[\d]{3}(.*)c(e|é)dex ?[\d]*', r'\1\2',
               q, flags=re.IGNORECASE)
    q = re.sub(r'([^\d ])([\d]{5})([^\d]|$)', r'\1 \2 ',
               q, flags=re.IGNORECASE)
    q = re.sub(r'c(e|é)dex ?[\d]*', '', q, flags=re.IGNORECASE)
    q = re.sub(r'\d{,2}(e|[eè]me|er) ([eé]tage)', '', q, flags=re.IGNORECASE)
    q = re.sub(r'((fax|t[eé]l|t[eé]l[eé]copieur)[ :,\.]*|)(\d{10}|[0-9][0-9][ -\./]\d\d[-\./ ]\d\d[-\./ ]\d\d[-\./ ]\d\d)', '', q, flags=re.IGNORECASE)
    q = re.sub(r' {2,}', ' ', q, flags=re.IGNORECASE)
    q = re.sub(r'[ -]s/[ -]', ' sur ', q, flags=re.IGNORECASE)
    q = re.sub(r'[ -]s/?s[ -]', ' sous ', q, flags=re.IGNORECASE)
    q = re.sub(r'^lieux?[ -]?dits?\b(?=.)', '', q, flags=re.IGNORECASE)
    q = re.sub(r' (\d{4}) ', r' 0\1 ', q, flags=re.IGNORECASE)
    q = q.strip()
    return q


def extract_address(q):
    m = EXTRACT_ADDRESS_PATTERN.search(q)
    return m.group() if m else q


def neighborhood(iterable, first=None, last=None):
    """
    Yield the (previous, current, next) items given an iterable.

    You can specify a `first` and/or `last` item for bounds.
    """
    iterator = iter(iterable)
    previous = first
    try:
        current = next(iterator)
    except StopIteration:  # StopIteration if empty.
        return

    for next_ in iterator:
        yield (previous, current, next_)
        previous = current
        current = next_
    yield (previous, current, last)


def glue_ordinal(tokens):
    previous = None
    for _, token, next_ in neighborhood(tokens):
        if next_ and token.isdigit():
            previous = token
            continue
        if previous is not None:
            # Matches "bis" either followed by a type or nothing.
            if (ORDINAL_PATTERN.match(token) and
                    (not next_ or TYPES_PATTERN.match(next_))):
                raw = '{} {}'.format(previous, token)
                # Space removed to maximize chances to get a hit.
                token = previous.update(raw.replace(' ', ''), raw=raw)
            else:
                # False positive.
                yield previous
            previous = None
        yield token


def flag_housenumber(tokens):
    # Only keep first match (avoid noise in the middle of the search query).
    found = False
    for previous, token, next_ in neighborhood(tokens):
        if ((token.is_first or (next_ and TYPES_PATTERN.match(next_)))
            and NUMBER_PATTERN.match(token) and not found):
            token.kind = 'housenumber'
            found = True
        yield token


def fold_ordinal(s):
    """3bis => 3b."""
    if s[0].isdigit() and not s.isdigit():
        try:
            number, ordinal = FOLD_PATTERN.findall(s)[0]
        except (IndexError, ValueError):
            pass
        else:
            s = s.update('{}{}'.format(number,
                         FOLD.get(ordinal.lower(), ordinal)))
    return s


GLUE_WORDS = ["mont", "val", "le", "la", "l", "champ"]

def glue_words(tokens):
    """ glue 'MONT GRIFFON' into 'MONTGRIFFON' """
    for _, token, next_ in neighborhood(tokens):
        if token != next_:
            yield token
        if token in GLUE_WORDS and next_ and next_.isalpha() and len(next_)>2:
            yield token.update(token+next_)


def glue_initials(tokens):
    """ glue 'F F I' into 'FFI' """
    initials = []
    for _, token, next_ in neighborhood(tokens):
        isinitial = len(token) == 1 and token.isalpha()
        if isinitial:
            initials.append(token)
        if not next_ or not isinitial:
            if len(initials) > 2:
                yield initials[0].update("".join(initials))
            else:
                for tk in initials:
                    yield tk
            initials = []
        if not isinitial:
            yield token


GLUE_REFS = re.compile(r'^(a|n|rn|d|rd|m|rm)[0-9]+$', flags=re.IGNORECASE)

def glue_refs(tokens):
    ref = None
    for _, token, next_ in neighborhood(tokens):
        print(ref, token, next_)
        if next_ and GLUE_REFS.match(token+next_):
            ref = token+next_
        elif next_ and ref and GLUE_REFS.match(ref+next_):
            ref = ref+next_
        elif ref:
            yield token.update(re.sub(r'^r(n|d)', r'\1', ref))
            ref  = None
        elif GLUE_REFS.match(token):
            yield token.update(re.sub(r'^r(n|d)', r'\1', token))
        else:
            yield token


def remove_leading_zeros(s):
    """0003 => 3."""
    # Limit digits from 1 to 3 in order to avoid processing postcodes.
    return re.sub(r"\b0+(\d{1,3})\b", "\g<1>", s, flags=re.IGNORECASE)


def make_labels(helper, result):
    if result.labels:
        return
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
        if postcode and result.type == 'municipality':
            add(labels, '{} {}'.format(label, postcode))
            add(labels, '{} {}'.format(postcode, label))
        add(labels, label)
        if city and city != label:
            add(labels, '{} {}'.format(label, city))
            if postcode:
                label = '{} {}'.format(label, postcode)
                add(labels, label)
                label = '{} {}'.format(label, city)
                add(labels, label)
        result.labels.extend(labels)
