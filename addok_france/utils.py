import re

TYPES = [
    "av(enue)?",
    "r(ue)?",
    "b(oulevar)?d",
    "all([ée]es?)?",
    "imp(asse)?",
    "pl(ace)?",
    "che(min)?",
    "rocade",
    "route",
    "rte",
    "l[ôo]t(issement)?",
    "mont[ée]e",
    "c[ôo]te",
    "clos",
    "champ",
    "bois",
    "taillis",
    "boucle",
    "passage",
    "domaine",
    "[ée]tang",
    "quai",
    "desserte",
    "pr[ée]",
    "porte",
    "square",
    "mont",
    "r[ée]sidence",
    "parc",
    "cours?",
    "promenade",
    "hameau",
    "faubourg",
    "[îi]lot",
    "berges?",
    "via",
    "cit[ée]",
    "sent(e|ier)",
    "rond[- ]point",
    "pas(se)?",
    "carrefour",
    "traverse",
    "giratoire",
    "esplanade",
    "voie",
    "chauss[ée]e",
]
TYPES_REGEX = "|".join(TYPES)
ORDINAL_REGEX = "bis|ter|quater|quinquies|sexies|[a-z]"

FOLD = {
    "bis": "b",
    "ter": "t",
    "quater": "q",
    "quinquies": "c",
    "sexies": "s",
}

# Try to match address pattern when the search string contains extra info (for
# example "22 rue des Fleurs 59350 Lille" will be extracted from
# "XYZ Ets bâtiment B 22 rue des Fleurs 59350 Lille Cedex 23").
EXTRACT_ADDRESS_PATTERN = re.compile(
    r"(\b\d{1,4}( *("
    + ORDINAL_REGEX
    + "))?,? +("
    + TYPES_REGEX
    + ") .*(\d{5})?).*",  # noqa
    flags=re.IGNORECASE,
)

# Match "bis", "ter", "b", etc.
ORDINAL_PATTERN = re.compile(r"\b(" + ORDINAL_REGEX + r")\b", flags=re.IGNORECASE)

# Match "rue", "boulevard", "bd", etc.
TYPES_PATTERN = re.compile(r"\b(" + TYPES_REGEX + r")\b", flags=re.IGNORECASE)


# Match number + ordinal, once glued by glue_ordinal (or typed like this in the
# search string, for example "6bis", "234ter").
FOLD_PATTERN = re.compile(r"^(\d{1,4})(" + ORDINAL_REGEX + ")$", flags=re.IGNORECASE)


# Match number once cleaned by glue_ordinal and fold_ordinal (for example
# "6b", "234t"…)
NUMBER_PATTERN = re.compile(r"\b\d{1,4}[a-z]?\b", flags=re.IGNORECASE)

CLEAN_PATTERNS = (
    (r"([\d]{5})", r" \1 "),
    (r"(^| )(b\.?p\.?|cs|tsa|cidex) *(n(o|°|) *|)[\d]+ *", r"\1"),
    (r"([\d]{2})[\d]{3}(.*)c(e|é)dex ?[\d]*", r"\1\2"),
    (r"c(e|é)dex ?[\d]*", ""),
    (r"\d{,2}(e|[eè]me) ([eé]tage)", ""),
    (" {2,}", " "),
    ("[ -]s/[ -]", " sur "),
    ("[ -]s/s[ -]", " sous "),
    ("^lieux?[ -]?dits?\\b(?=.)", ""),
)
CLEAN_COMPILED = list(
    (re.compile(pattern, flags=re.IGNORECASE), replacement)
    for pattern, replacement in CLEAN_PATTERNS
)


def clean_query(q):
    for pattern, repl in CLEAN_COMPILED:
        q = pattern.sub(repl, q)
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
        current = next(iterator)  # Throws StopIteration if empty.
    except StopIteration:
        pass
    else:
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
            if ORDINAL_PATTERN.match(token) and (
                not next_ or TYPES_PATTERN.match(next_)
            ):
                raw = "{} {}".format(previous, token)
                # Space removed to maximize chances to get a hit.
                token = previous.update(raw.replace(" ", ""), raw=raw)
            else:
                # False positive.
                yield previous
            previous = None
        yield token


def flag_housenumber(tokens):
    # Only keep first match (avoid noise in the middle of the search query).
    found = False
    for previous, token, next_ in neighborhood(tokens):
        if (
            (token.is_first or (next_ and TYPES_PATTERN.match(next_)))
            and NUMBER_PATTERN.match(token)
            and not found
        ):
            token.kind = "housenumber"
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
            s = s.update("{}{}".format(number, FOLD.get(ordinal.lower(), ordinal)))
    return s


def remove_leading_zeros(s):
    """0003 => 3."""
    # Limit digits from 1 to 3 in order to avoid processing postcodes.
    return re.sub(r"\b0+(\d{1,3})\b", "\g<1>", s, flags=re.IGNORECASE)


def make_labels(helper, result):
    if result.labels:
        return
    housenumber = getattr(result, "housenumber", None)

    def add(labels, label):
        labels.insert(0, label)
        if housenumber:
            label = "{} {}".format(housenumber, label)
            labels.insert(0, label)

    city = result.city
    postcode = result.postcode
    names = result._rawattr("name")
    if not isinstance(names, (list, tuple)):
        names = [names]
    for name in names:
        labels = []
        label = name
        if postcode and result.type == "municipality":
            add(labels, "{} {}".format(label, postcode))
            add(labels, "{} {}".format(postcode, label))
        add(labels, label)
        if city and city != label:
            add(labels, "{} {}".format(label, city))
            if postcode:
                label = "{} {}".format(label, postcode)
                add(labels, label)
                label = "{} {}".format(label, city)
                add(labels, label)
        result.labels.extend(labels)
