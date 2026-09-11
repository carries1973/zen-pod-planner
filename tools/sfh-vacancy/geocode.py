"""Geocode Alberta addresses, through a cache committed next to this script.

Two lookups, in order: geocoder.ca (authoritative for Alberta civic addresses)
then Nominatim. Nominatim alone mis-resolves Edmonton quadrant addresses onto
their Calgary namesakes, which is how three Edmonton homes once landed in
Calgary on this map.

Every result is written to geocache.json so a re-run is deterministic and needs
no network. A miss is cached as null and reported, never guessed.
"""
import json, os, re, time, urllib.parse, urllib.request

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'geocache.json')
UA = 'zen-sfh-pod-map/1.0 (carries@zenresidential.ca)'
AB = ((48.9, -120.1), (60.1, -109.9))          # Alberta bounding box


def _load():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    return {}


def _save(c):
    json.dump(c, open(CACHE, 'w'), indent=1, sort_keys=True)


def _get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def _in_alberta(lat, lng):
    return AB[0][0] <= lat <= AB[1][0] and AB[0][1] <= lng <= AB[1][1]


_ABBR = [('street', 'St'), ('avenue', 'Ave'), ('drive', 'Dr'),
         ('boulevard', 'Blvd'), ('crescent', 'Cres'), ('road', 'Rd'),
         ('court', 'Crt'), ('place', 'Pl'), ('northwest', 'NW'),
         ('southwest', 'SW'), ('northeast', 'NE'), ('southeast', 'SE')]


def _abbrev(q):
    for a, b in _ABBR:
        q = re.sub(r'\b%s\b' % a, b, q, flags=re.I)
    return q


def _geocoder_ca(q):
    # geocoder.ca 500s on spelled-out street types; it wants '51 St NW'.
    u = 'https://geocoder.ca/?json=1&locate=' + urllib.parse.quote(_abbrev(q))
    d = _get(u)
    if 'latt' in d and 'longt' in d:
        lat, lng = float(d['latt']), float(d['longt'])
        std = d.get('standard') or {}
        conf = std.get('confidence')
        if _in_alberta(lat, lng) and not d.get('error'):
            return lat, lng, 'geocoder.ca', (d.get('postal') or ''), conf
    return None


def _nominatim(q, city=None):
    u = ('https://nominatim.openstreetmap.org/search?format=json&limit=5&'
         'addressdetails=1&countrycodes=ca&q=' + urllib.parse.quote(q))
    for hit in _get(u):
        lat, lng = float(hit['lat']), float(hit['lon'])
        if not _in_alberta(lat, lng):
            continue
        # Nominatim happily answers an Edmonton quadrant address with its
        # Calgary namesake; three homes on this map landed in the wrong city
        # that way. The town has to come back in the answer.
        if city and city.lower() not in hit.get('display_name', '').lower():
            continue
        return lat, lng, 'nominatim', (hit.get('address') or {}).get('postcode', ''), None
    return None


def _nominatim_abbrev(q, city=None):
    """Nominatim, but with street types abbreviated. OSM's Alberta data spells
    some streets 'Ave NW' and some 'Avenue Northwest', and a miss on one form is
    routinely a hit on the other — '11320 113A Avenue Northwest' failed while
    '11320 113A Ave NW' resolves."""
    a = _abbrev(q)
    return None if a == q else _nominatim(a, city)


def _postal(q, city=None, postal=None):
    """Last resort: place the property by its POSTAL CODE.

    A Canadian postal code resolves to a block face, not a building, so this is
    less precise than an address fix and the caller is told so by the returned
    source ('postal'). It is still far better than the alternative, which is a
    property silently absent from the map: the 2026-09-11 Buildium export
    carried a postal code for every unplaced property, including SF166
    '260230 RR 293' — a rural range road with no civic address, unplaceable on
    this map since the Aug-20 build, which Buildium states as Balzac T4B 2T3.
    """
    if not postal:
        return None
    u = ('https://nominatim.openstreetmap.org/search?format=json&limit=5&'
         'addressdetails=1&countrycodes=ca&postalcode='
         + urllib.parse.quote(postal))
    for hit in _get(u):
        lat, lng = float(hit['lat']), float(hit['lon'])
        if _in_alberta(lat, lng):
            return lat, lng, 'postal', postal, None
    return None


def lookup(query, city=None, refresh=False, postal=None):
    """-> (lat, lng, source, postal) or None. Cached by exact query string.

    `source` states HOW it was placed — 'geocoder.ca' and 'nominatim' are
    address-level, 'postal' is a block-face approximation. Callers report it so
    a coarse pin is never mistaken for a precise one.
    """
    cache = _load()
    key = query if not postal else '%s | postal=%s' % (query, postal)
    if not refresh and key in cache:
        v = cache[key]
        return tuple(v) if v else None
    got = None
    for fn in (_geocoder_ca, _nominatim, _nominatim_abbrev, _postal):
        try:
            if fn is _geocoder_ca:
                got = fn(query)
            elif fn is _postal:
                got = fn(query, city, postal)
            else:
                got = fn(query, city)
        except Exception as e:                 # network/parse — try the next one
            print('  geocode %s failed for %r: %s' % (fn.__name__, query, e))
            got = None
        if got:
            break
        time.sleep(1.1)                        # Nominatim asks for 1 req/sec
    cache[key] = list(got[:4]) if got else None
    _save(cache)
    return tuple(got[:4]) if got else None
