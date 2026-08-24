"""Resolve Buildium Vacant-Units scope/unit ids onto SFH-map homes/units.

Matching is deliberately unit-id-driven: a scope narrows the candidate homes,
but a vacancy is only ever recorded against a door that actually exists on the
map. Anything that does not resolve is REPORTED, never silently dropped.
"""
import re, vaclib
from collections import defaultdict

# Scopes whose label cannot reach the right home by address alone.
# Keyed by a substring of home['addr'] / home['name'].
OVERRIDE = {
    'SF351': '(Alces)',                    # Buildium spells it "Alcers"
    'SF175': '63 Fenwyck Boulevard 63',    # scope label is a range "61 - 83"
    'SF268': '101 Clydesdale Way',         # "Bridle Ridge Townhouses"
    'SF310': '9A Bayside Place',           # "Centennial Townhomes"
    'SF296': '10430 98 Avenue',            # "Station View Townhomes"
    'SF300': '10461 99 Avenue',            # "Station View Apartments"
    'SF350': '2104 2 Avenue NE',
    'SF137': 'Prairie Point Townhomes',    # Buildium says "Townhouses"
    'SF333': '7110 Keswick Drive SW',      # Buildium says "Keswick Common"
    'RP27':  '9730 106 Street NW',
    'RP169': 'Trails Edge',
    'RP158': '170 North Railway',
}
NO_HOME = set()                            # discovered, not assumed
NOT_A_DOOR = re.compile(r'site inspection', re.I)
PORTFOLIO_TAG = re.compile(
    r'\b(Skysda|Monarch|Harder|Barry|Vicki|Fairbridge)\s*\d*\s*&?\s*\d*', re.I)

def nz(s):
    s = s.lower()
    for a, b in [('street','st'),('avenue','ave'),('drive','dr'),('boulevard','blvd'),
                 ('northwest','nw'),('southwest','sw'),('northeast','ne'),('southeast','se')]:
        s = re.sub(r'\b%s\b' % a, b, s)
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', s).split())

ALCES_RE = re.compile(r'^(2\d{3})(b?)$')

def unit_tokens(u, code=None):
    """'12228 - Bsmt' -> ('12228','bsmt');  'Lower' -> (None,'lower')"""
    if code == 'SF351':
        m = ALCES_RE.match(nz(u))
        if m:
            return m.group(1), ('bsmt' if m.group(2) else 'main')
    u = re.sub(r'\s*-\s*(OFF MARKET|DO NOT|FIRE|RENO)\b.*$', '', u, flags=re.I)
    u = nz(u)
    m = re.match(r'^(\d{2,6})\s+(.*)$', u)
    if m and m.group(2):
        return m.group(1), m.group(2).strip()
    return None, u

def street_sig(lab):
    s = re.sub(r'^(?:SF|RP|MF)\s*\d+\s*-?\s*', '', lab)
    s = re.sub(r'\(\d+\s*vacanc\w*\)', '', s, flags=re.I)
    s = PORTFOLIO_TAG.sub('', s)
    s = re.sub(r'\s*-\s*(Offboard|Returning|INACTIVE).*$', '', s, flags=re.I)
    return nz(s)

def unit_match(app_unit, pref, suf):
    """Does an app unit id denote the same door as (pref, suf)?"""
    up, us = unit_tokens(app_unit)
    a = nz(app_unit)
    if pref and up and up != pref:
        return False
    if us == suf or a == (('%s %s' % (pref, suf)).strip() if pref else suf):
        return True
    # map ids may carry a stack letter the report omits: '213C' vs '213'
    if suf and re.fullmatch(r'\d+', suf) and re.fullmatch(r'%s[a-z]' % suf, a):
        return True
    if pref and not suf and re.fullmatch(r'%s[a-z]?' % pref, a):
        return True
    # garage-suite ids: report 'Bsmt - G4' vs map 'G4'
    if suf and re.fullmatch(r'g\d', us or '') and set(us.split()) < set(suf.split()):
        return True
    return False

def build_index(homes):
    idx = []
    for i, h in enumerate(homes):
        txt = nz(h['name']) + ' ' + nz(h['addr'])
        anums = set(re.findall(r'\d{2,6}', txt))          # address / name
        unums = set()                                      # unit ids
        for u in h['units']:
            unums |= set(re.findall(r'\d{2,6}', nz(u['unit'])))
        idx.append({'i': i, 'txt': txt, 'raw': h,
                    'anums': anums, 'unums': unums, 'nums': anums | unums})
    return idx

def resolve(blob, report_path):
    homes = blob['homes']
    idx = build_index(homes)
    recs, meta = vaclib.parse(report_path)
    active = [r for r in recs if not r['offboard'] and not r['internal']]
    byscope = defaultdict(list)
    for r in active:
        byscope[r['code']].append(r)

    hits, misses, notdoors = [], [], []
    for code, rs in byscope.items():
        lab = rs[0]['scope']
        if code in OVERRIDE:
            key = nz(OVERRIDE[code])
            scope_cands = [c for c in idx if key in c['txt']]
            snums, words = None, []
        else:
            sig = street_sig(lab)
            snums = set(re.findall(r'\d{2,6}', sig))
            words = [w for w in sig.split() if not w.isdigit() and len(w) > 3]
            scope_cands = None
        for r in rs:
            if NOT_A_DOOR.search(r['unit']):
                notdoors.append((code, r['unit'], lab)); continue
            pref, suf = unit_tokens(r['unit'], code)
            # Candidate homes. One weak number overlap is NOT enough — a lone
            # '#21' in a scope label otherwise matches any home with a unit 21.
            # Require two shared numbers, one plus a street-name word, or the
            # unit's own house number appearing in the home's ADDRESS (covers
            # range labels like '261 - 305 Collicott Drive' -> 265).
            pool = []
            for c in (scope_cands if scope_cands is not None else idx):
                if scope_cands is not None:
                    ok, shared, wordhit = True, set(), False
                else:
                    shared = snums & c['nums']
                    wordhit = any(w in c['txt'] for w in words)
                    ok = (len(shared) >= 2 or (shared and wordhit)
                          or (pref and pref in c['anums']))
                if not ok:
                    continue
                # Ranking, strongest signal first:
                #  1. the unit's house number IS this home's address, on the
                #     street named by the scope  ('265 - upper' inside the
                #     range label '261 - 305 Collicott Drive')
                #  2. how much of the scope's own address this home matches
                #  3. the unit's house number is this home's address
                #  4. that number merely appears among the home's unit ids
                pa = bool(pref and pref in c['anums'])
                c['_rank'] = (1 if pa and wordhit else 0,
                              len(shared),
                              1 if pa else 0,
                              1 if pref and pref in c['unums'] else 0,
                              1 if wordhit else 0)
                pool.append(c)
            if not pool:
                misses.append((code, r['unit'], lab, 'no home on map')); continue
            pool.sort(key=lambda c: c['_rank'], reverse=True)
            found = None
            for c in pool:
                for ui, u in enumerate(c['raw']['units']):
                    if unit_match(u['unit'], pref, suf):
                        found = (c['i'], ui); break
                if found: break
            if found:
                hits.append((code, r['unit'], found, lab))
            else:
                misses.append((code, r['unit'], lab, 'unit absent from: ' +
                               ', '.join(homes[c['i']]['name'][:22] for c in pool[:3])))
    return {'meta': meta, 'active': active, 'hits': hits,
            'misses': misses, 'notdoors': notdoors, 'byscope': byscope}
