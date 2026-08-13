#!/usr/bin/env python3
"""Apply a Buildium 'Vacant Units' export to the SFH pod map.

    python3 tools/sfh-vacancy/apply_vacancy.py "~/Downloads/Vacant_Units (5).xlsx"

Rules this script enforces (each one exists because it was got wrong before):
  * The report's own "Totals & Averages" row must equal the number of unit rows
    parsed, or we refuse to run.
  * A vacancy is only ever written to a door that already exists on the map.
    Unplaceable vacancies are REPORTED and carried into the page's audit
    bridge; they are never silently dropped and never invent a door.
  * The headline vacancy count must reconcile ON the page, from Buildium's
    active total down to what the map can show.

Run with --check to audit without writing.
"""
import json, re, sys, os, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vaclib, resolve

HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'sfh', 'index.html')
BLOB_RE = re.compile(r'(<script id="data" type="application/json">)(.*?)(</script>)', re.S)

# Doors the map carried twice (same home, same unit id). Buildium has one door
# per id, so the duplicate is a phantom that inflates the denominator.
PHANTOM_DOORS = [('1430 Aster Way NW', '19'), ('265 Collicott Drive', '265 Upper')]

# Properties present in Buildium but absent from the map, with coordinates
# geocoded via geocoder.ca (Nominatim mis-resolves Edmonton quadrant addresses
# that also exist in Calgary).
NEW_HOMES = [
    {'code': 'SF332', 'name': '1143 160 Street SW', 'type': 'Single-Family House',
     'addr': '1143 160 Street SW, Edmonton AB T6W 2W6', 'city': 'Edmonton',
     'lat': 53.422411, 'lng': -113.598616, 'unit': 'Full'},
    {'code': 'SF340', 'name': '#21 723 172 Street SW', 'type': 'Townhouse',
     'addr': '#21 723 172 Street SW, Edmonton AB T6W 2N6', 'city': 'Edmonton',
     'lat': 53.426935, 'lng': -113.616093, 'unit': '21'},
]

def load():
    raw = open(HTML, encoding='utf-8').read()
    m = BLOB_RE.search(raw)
    if not m:
        sys.exit('REFUSE: data blob not found in %s' % HTML)
    return raw, m, json.loads(m.group(2))

def haversine(a, b, c, d):
    from math import radians, sin, cos, asin, sqrt
    p, q, r, s = map(radians, (a, b, c, d))
    return 2 * 6371 * asin(sqrt(sin((r-p)/2)**2 + cos(p)*cos(r)*sin((s-q)/2)**2))

def assign_pod(blob, lat, lng):
    best, bid = 1e9, -1
    for p in blob['pods']:
        d = haversine(lat, lng, p['centroid'][0], p['centroid'][1])
        if d < best:
            best, bid = d, p['id']
    return (bid if best <= 30 else -1), best

def dedupe(blob):
    removed = []
    for hname, unit in PHANTOM_DOORS:
        for h in blob['homes']:
            if h['name'] != hname:
                continue
            seen, keep = set(), []
            for u in h['units']:
                k = resolve.nz(u['unit'])
                if k == resolve.nz(unit) and k in seen:
                    removed.append((hname, u['unit'])); continue
                seen.add(k); keep.append(u)
            h['units'] = keep
    return removed

def add_new_homes(blob, report):
    """Add whole properties Buildium reports but the map lacks."""
    recs, _ = vaclib.parse(report)
    byc = {}
    for r in recs:
        byc.setdefault(r['code'], []).append(r)
    added = []
    have = {resolve.nz(h['addr']) for h in blob['homes']}
    for spec in NEW_HOMES:
        rs = [r for r in byc.get(spec['code'], [])
              if not r['offboard'] and not r['internal']]
        if not rs:
            continue                      # no longer vacant -> nothing to add
        if resolve.nz(spec['addr']) in have:
            continue                      # already present
        rec = rs[0]
        beds, bath = '', ''
        m = re.match(r"'?-?\s*(\d*)\s*Bed?/?\s*([\d.]*)", rec['bedbath'] or '')
        if m:
            beds, bath = m.group(1), m.group(2)
        pod, dist = assign_pod(blob, spec['lat'], spec['lng'])
        home = {'name': spec['name'], 'type': spec['type'], 'addr': spec['addr'],
                'city': spec['city'], 'lat': spec['lat'], 'lng': spec['lng'],
                'pod': pod, 'code': spec['code'], 'rr': 1,
                'units': [{'unit': spec['unit'], 'beds': beds, 'bath': bath,
                           'sqft': rec['sqft'] or '0', 'rent': rec['rent'] or '',
                           'deposit': rec['rent'] or '', 'status': 'Vacant',
                           'pets': '', 'parking': '', 'term': '',
                           'email': '', 'phone': '',
                           'desc': '%s | added from the Buildium Vacant Units '
                                   'report; listing detail not yet in the Unit '
                                   'Summary.' % spec['code']}]}
        blob['homes'].append(home)
        added.append((spec['name'], pod, round(dist, 1)))
    return added

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    if not args:
        sys.exit(__doc__)
    report = os.path.expanduser(args[0])
    raw, m, blob = load()

    removed = dedupe(blob)
    added = add_new_homes(blob, report)

    R = resolve.resolve(blob, report)
    homes = blob['homes']
    target = {h[2] for h in R['hits']}
    if len(target) != len(R['hits']):
        sys.exit('REFUSE: %d report rows collapsed onto the same door'
                 % (len(R['hits']) - len(target)))

    before = sum(1 for h in homes for u in h['units'] if u['status'] == 'Vacant')
    to_vac, to_rent = [], []
    for i, h in enumerate(homes):
        for ui, u in enumerate(h['units']):
            want = 'Vacant' if (i, ui) in target else 'Rented'
            if u['status'] != want:
                (to_vac if want == 'Vacant' else to_rent).append(
                    (h['name'], u['unit']))
                u['status'] = want

    # permanent capture: stamp the Buildium code onto every home we could place,
    # so the next report matches by code instead of re-deriving from addresses
    stamped = 0
    for code, unit, (i, ui), lab in R['hits']:
        if not homes[i].get('code'):
            homes[i]['code'] = code; stamped += 1

    # ---- the bridge that has to close, from Buildium's own total downwards ----
    active = len(R['active'])
    notdoor = len(R['notdoors'])
    doors = active - notdoor
    mapped = len(target)
    unmapped = len(R['misses'])
    if mapped + unmapped != doors:
        sys.exit('REFUSE: bridge does not close: %d mapped + %d unmapped != %d '
                 'doors' % (mapped, unmapped, doors))
    after = sum(1 for h in homes for u in h['units'] if u['status'] == 'Vacant')
    if after != mapped:
        sys.exit('REFUSE: map shows %d vacant but %d resolved' % (after, mapped))

    audit = {
        'asof': R['meta']['asof'],
        'source': os.path.basename(report),
        'buildium_active': active,
        'not_a_door': [{'code': c, 'unit': u} for c, u, l in R['notdoors']],
        'doors': doors, 'mapped': mapped, 'unmapped': unmapped,
        'gaps': [{'code': c, 'unit': u, 'why': w} for c, u, l, w in
                 sorted(R['misses'])],
        'generated': datetime.date.today().isoformat(),
    }
    blob['audit'] = audit

    print('report %s (as of %s)' % (os.path.basename(report), R['meta']['asof']))
    print('  phantom doors removed : %d %s' % (len(removed), removed))
    print('  properties added      : %d %s' % (len(added), added))
    print('  codes stamped         : %d' % stamped)
    print('  vacant %d -> %d   (+%d newly vacant, -%d filled)  [before = post-dedupe/post-add]'
          % (before, after, len(to_vac), len(to_rent)))
    print('  BRIDGE  buildium active %d - %d non-door = %d doors'
          % (active, notdoor, doors))
    print('          %d mapped + %d unmapped = %d  OK' % (mapped, unmapped, doors))
    print('  homes %d | units %d | occupancy %.1f%%'
          % (len(homes), sum(len(h['units']) for h in homes),
             100.0 * (sum(len(h['units']) for h in homes) - after)
             / sum(len(h['units']) for h in homes)))
    for g in audit['gaps']:
        print('    GAP %-8s %-16s %s' % (g['code'], g['unit'], g['why'][:60]))

    if check:
        print('\n--check: no files written'); return
    out = json.dumps(blob, ensure_ascii=False, separators=(',', ':'))
    open(HTML, 'w', encoding='utf-8').write(
        raw[:m.start(2)] + out + raw[m.end(2):])
    print('\nwrote %s' % os.path.normpath(HTML))

if __name__ == '__main__':
    main()
