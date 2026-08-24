"""Canonical Alberta street addresses, for matching Buildium scope labels onto
map homes.

Edmonton and Calgary are numbered grids: '11207, 11209 51 Street NW' has no
alphabetic street name at all, so any matcher that requires a street *word*
throws the whole Front Porch book away. The street here is a designator
(number or name) + a type + a quadrant, and everything before it is one or
more house numbers.
"""
import re

TYPES = {
    'street': 'st', 'st': 'st', 'avenue': 'ave', 'ave': 'ave', 'av': 'ave',
    'drive': 'dr', 'dr': 'dr', 'boulevard': 'blvd', 'blvd': 'blvd',
    'road': 'rd', 'rd': 'rd', 'crescent': 'cres', 'cres': 'cres',
    'way': 'way', 'place': 'pl', 'pl': 'pl', 'close': 'close',
    'court': 'crt', 'crt': 'crt', 'ct': 'crt', 'lane': 'lane',
    'link': 'link', 'common': 'common', 'commons': 'common',
    'crossing': 'crossing', 'mews': 'mews', 'gate': 'gate', 'bay': 'bay',
    'circle': 'circle', 'terrace': 'terr', 'terr': 'terr', 'green': 'green',
    'grove': 'grove', 'gardens': 'gdns', 'heath': 'heath', 'hill': 'hill',
    'landing': 'landing', 'manor': 'manor', 'park': 'park', 'parkway': 'pkwy',
    'passage': 'passage', 'path': 'path', 'point': 'point', 'ridge': 'ridge',
    'rise': 'rise', 'row': 'row', 'square': 'sq', 'trail': 'trail',
    'view': 'view', 'villas': 'villas', 'village': 'village', 'walk': 'walk',
    'wynd': 'wynd', 'circuit': 'circuit', 'cove': 'cove', 'glen': 'glen',
    'hollow': 'hollow', 'island': 'island', 'key': 'key', 'meadow': 'meadow',
    'mount': 'mount', 'promenade': 'promenade', 'vista': 'vista',
    'bend': 'bend', 'edge': 'edge', 'estates': 'estates', 'harbor': 'harbor',
    'harbour': 'harbor', 'haven': 'haven', 'hts': 'hts', 'heights': 'hts',
    'mile': 'mile', 'rr': 'rr',
}
QUAD = {'nw': 'nw', 'sw': 'sw', 'ne': 'ne', 'se': 'se',
        'northwest': 'nw', 'southwest': 'sw',
        'northeast': 'ne', 'southeast': 'se'}

# Buildium tacks these on; none of them are part of an address.
_TAG = re.compile(
    r'\s*[-(]?\s*\b(?:Skysda|Monarch|Harder|Barry|Fairbridge|Vicki)\s*\d*\s*'
    r'(?:&\s*\d+)?\s*\)?', re.I)
_ANNOT = re.compile(
    r'\s*[-(]\s*(?:Offboard\w*|OFFBAORDED|OFRFBOARDED|Returning|INACTIVE|'
    r'New\s+PMA|OFF\s*MARKET|DO\s*NOT\s*USE|FIRE|RENO|Terminat\w*)\b.*$', re.I)
_CODE = re.compile(r'^\s*(?:SF|RP|MF)\s*\d+\s*[-–]?\s*', re.I)
_LEAD_UNIT = re.compile(r'^\s*(?:#|unit\s+|apt\s+|suite\s+|ste\s+)\s*[\w-]+\s*,?\s+', re.I)
_TRAIL_UNIT = re.compile(r'\s*[-–]\s*#\s*\w+\s*$')
CITY_RE = re.compile(
    r',?\s*\b(Edmonton|Calgary|Beaumont|Leduc|Spruce\s+Grove|St\.?\s*Albert|'
    r'Sherwood\s+Park|Fort\s+Saskatchewan|Morinville|Okotoks|Cochrane|'
    r'Airdrie|Chestermere|Strathmore|High\s+River|Devon|Stony\s+Plain|'
    r'Fort\s+McMurray|Alces)\b.*$', re.I)


_ORD = re.compile(r'^(\d+)(?:st|nd|rd|th)$')


def _words(s):
    out = []
    for w in re.sub(r'[^a-z0-9 ]+', ' ', s.lower()).split():
        m = _ORD.match(w)          # '54th Street' and '54 Street' are one street
        out.append(m.group(1) if m else w)
    return out


def parse(label):
    """-> {'houses': set(str), 'street': 'canonical street key' or None}

    'SF201 - 11207, 11209 51 Street NW - Barry1' -> {11207,11209}, '51 st nw'
    'SF174 - 261 - 305 Collicott Drive'          -> {261..305 odd+even}, 'collicott dr'
    '#26 18120 28 Ave SW'                        -> {18120}, '28 ave sw'
    """
    s = label
    s = _CODE.sub('', s)
    s = _TAG.sub(' ', s)
    s = _ANNOT.sub('', s)
    mc = CITY_RE.search(s)
    city = re.sub(r'\s+', ' ', mc.group(1)).lower().replace('.', '') if mc else ''
    s = CITY_RE.sub('', s)
    s = _TRAIL_UNIT.sub('', s)
    s = re.sub(r'\s*\(\s*\)\s*', ' ', s)
    # A leading '#551' is a unit number in '#551 Dunluce Road NW' but the
    # street number in '#415 301 Redstone Blvd NE'. Only strip it when what
    # remains still names a house — otherwise the address loses its number.
    hint, hashed = '', bool(re.match(r'^\s*#', s))
    mh = _LEAD_UNIT.match(s)
    if mh:
        rest = s[mh.end():]
        if re.search(r'\b\d{1,6}\b', rest):
            hint = re.sub(r'[^\w-]', '', mh.group(0))
            s = rest
    w = _words(s)
    if not w:
        return {'houses': set(), 'street': None, 'clean': '', 'core': set(),
                'has_type': False, 'hint': hint, 'city': city}

    # Find the street type token nearest the end (quadrant may follow it).
    ti = None
    for i in range(len(w) - 1, -1, -1):
        if w[i] in TYPES and i > 0:
            ti = i
            break
    if ti is None:
        # No street type at all ('205 McKenney NW'). Leading numbers are the
        # house, the alphabetic remainder is the street.
        i = 0
        while i < len(w) and re.fullmatch(r'\d{1,6}[a-z]?', w[i]):
            i += 1
        core = {t for t in w[i:] if t not in QUAD and not t.isdigit()}
        quad = next((QUAD[t] for t in w[i:] if t in QUAD), '')
        street = ' '.join(sorted(core) + ([quad] if quad else []))
        return {'houses': set(w[:i]) or set(re.findall(r'\d{2,6}', ' '.join(w))),
                'street': street or None, 'clean': ' '.join(w),
                'core': core, 'has_type': False, 'hint': hint, 'city': city}

    quad = ''
    if ti + 1 < len(w) and w[ti + 1] in QUAD:
        quad = QUAD[w[ti + 1]]

    # The designator is the run of tokens immediately before the type that
    # belongs to the street name: a single number ('51 Street'), possibly with
    # a letter ('16A Ave'), or one-to-three words ('Legacy Glen Place').
    dstart = ti
    if re.fullmatch(r'\d+[a-z]?', w[ti - 1]):
        dstart = ti - 1
    else:
        j = ti - 1
        while j > 0 and not re.fullmatch(r'\d{2,6}', w[j - 1]) and (ti - j) < 3:
            j -= 1
        dstart = j
    street = ' '.join(w[dstart:ti] + [TYPES[w[ti]]] + ([quad] if quad else []))

    # Every number before the designator is a house number. Ranges and
    # shorthand runs are expanded: '9811 - 9825', '13923, 25, 27, 29'.
    head = w[:dstart]
    nums = [t for t in head if t.isdigit()]
    houses = set()
    if nums:
        base = nums[0]
        houses.add(base)
        for n in nums[1:]:
            houses.add(n if len(n) >= len(base) else base[:len(base) - len(n)] + n)
        # a two-number head that reads as a range covers everything between,
        # stepping by 2 (same parity) or 1
        if len(nums) == 2 and not hashed and re.search(r'\d\s*[-–]\s*\d', s):
            a, b = sorted(int(x) for x in houses)
            if 0 < b - a <= 400:
                step = 2 if (b - a) % 2 == 0 else 1
                houses |= {str(x) for x in range(a, b + 1, step)}
    if not houses:
        # Some map labels put the number last ('Fenwyck Boulevard 77').
        houses = {t for t in w[ti + 1:] if re.fullmatch(r'\d{1,6}', t)}
    core = {t for t in w[dstart:ti] if t not in QUAD}
    return {'houses': houses, 'street': street, 'clean': ' '.join(w),
            'core': core, 'has_type': True, 'hint': hint, 'city': city}


def street_key(street, loose=False):
    """Quadrant-insensitive form, for comparing a label that carries the
    quadrant against one that omits it."""
    if not street:
        return None
    parts = street.split()
    if loose and parts and parts[-1] in QUAD:
        parts = parts[:-1]
    return ' '.join(parts)


def same_place(a, b):
    """Do two parsed addresses denote the same street, with a shared house
    number? Never true on a house number alone — that would match any street
    in the grid — and never true on a street alone."""
    if not a['street'] or not b['street']:
        return False
    shared = a['houses'] & b['houses']
    if not shared:
        return False
    # When both sides name a town, they have to be the same town: '156 Park
    # Street' exists in Cochrane and in Edmonton.
    if a['city'] and b['city'] and a['city'] != b['city']:
        return False
    if a['street'] == b['street']:
        return True
    # one side omitted the quadrant
    qa = a['street'].split()[-1] in QUAD
    qb = b['street'].split()[-1] in QUAD
    if qa != qb and street_key(a['street'], True) == street_key(b['street'], True):
        return True
    # One side wrote no street type at all ('205 McKenney NW' vs '205
    # McKenney Avenue'). Fall back to the street's own name words, which still
    # has to agree exactly — plus the shared house number already required.
    if (not a['has_type'] or not b['has_type']) and a['core'] and b['core']:
        return a['core'] == b['core']
    return False
