#!/usr/bin/env python3
"""Refresh the SFH pod map's availability from a Buildium Rent Roll export.

    python3 tools/sfh-vacancy/apply_rentroll.py "~/Downloads/Rent_Roll (11).xlsx"
    ... --check      audit only, write nothing

Why a rent roll rather than the Vacant Units report the older
apply_vacancy.py takes: the vacancy report lists only vacant doors, so a door
missing from it was indistinguishable from a leased door — a parse failure
looked exactly like a lease. The rent roll states BOTH sides of every door, so
the control here is coverage-against-source in both directions:

  * every active door in the roll lands on a map door, or is added, or is named;
  * every map door is claimed by the roll, or is removed with its reason named;
  * the bridge from Buildium's own totals down to the map is rendered ON the
    page and this script refuses to write when it stops closing.

The roll is at LEASE grain (one row per lease, history included) — rrlib
collapses it to doors before anything here runs.
"""
import json, re, sys, os, datetime
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vaclib, rrlib, resolve, cover, addr, geocode

HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    '..', '..', 'sfh', 'index.html')
BLOB_RE = re.compile(
    r'(<script id="data" type="application/json">)(.*?)(</script>)', re.S)

# Properties in the roll that the map has no pin for. City and property type
# are NOT in the rent roll — they are inferred here from the street pattern and
# door count, and every one is reported as inferred rather than ruled.
NEW_PROPS = {
    '11306 123 Street Northwest': {
        'query': '11306 123 Street NW, Edmonton, AB', 'city': 'Edmonton',
        'name': '11306 123 Street NW', 'type': 'Apartment',
        'why': 'inferred: Edmonton NW quadrant; 9 doors reads as a multiplex'},
    'SF76 #9B 13230 Fort Road NW': {
        'query': '13230 Fort Road NW, Edmonton, AB', 'city': 'Edmonton',
        'name': '#9B 13230 Fort Road NW', 'type': 'Townhouse',
        'why': 'inferred: Edmonton NW quadrant; "#9B" reads as a townhouse unit'},
    'SF343 - 4304 139 Avenue NW - #308': {
        'query': '4304 139 Avenue NW, Edmonton, AB', 'city': 'Edmonton',
        'name': '#308 4304 139 Avenue NW', 'type': 'Apartment',
        'why': 'inferred: Edmonton NW quadrant; "#308" reads as an apartment'},
    'SF248 87 Darlington Court': {
        'query': '87 Darlington Court, Sherwood Park, AB', 'city': 'Sherwood Park',
        'name': '87 Darlington Court', 'type': 'Single-Family House',
        'why': 'inferred: Darlington Court is in Sherwood Park; single whole door'},
}
# Deliberately absent: 'SF166 - 260230 RR 293'. A rural route with no town in
# the label cannot be placed without Carrie saying where it is, and a guessed
# pin is worse than a named gap.


# The rent roll carries one scope with no SF/RP code of its own. The ILS unit
# list names it: "SF354 - 11306 1213 Street - Inglewood 9 Plex". Evidenced from
# that export, not inferred.
SCOPE_CODE = {'11306 123 Street Northwest': 'SF354'}


def load():
    raw = open(HTML, encoding='utf-8').read()
    m = BLOB_RE.search(raw)
    if not m:
        sys.exit('REFUSE: data blob not found in %s' % HTML)
    return raw, m, json.loads(m.group(2))


def write_html(text):
    """Write the page atomically. A plain open(...,'w') truncates first, so a
    bug anywhere between the open and the write leaves the deliverable an empty
    file — which is exactly what happened once. Build it beside the target and
    rename it into place instead."""
    if not text or '<script id="data"' not in text:
        sys.exit('REFUSE: refusing to write a page with no data blob')
    tmp = HTML + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        fh.write(text)
    os.replace(tmp, HTML)


def haversine(a, b, c, d):
    from math import radians, sin, cos, asin, sqrt
    p, q, r, s = map(radians, (a, b, c, d))
    return 2 * 6371 * asin(sqrt(sin((r - p) / 2) ** 2
                                + cos(p) * cos(r) * sin((s - q) / 2) ** 2))


def assign_pod(blob, lat, lng):
    best, bid = 1e9, -1
    for p in blob['pods']:
        d = haversine(lat, lng, p['centroid'][0], p['centroid'][1])
        if d < best:
            best, bid = d, p['id']
    return (bid if best <= 30 else -1), best


def door_unit(d, code):
    """A map unit built from a rent-roll door alone: status is authoritative,
    listing detail (sqft, pets, contacts, copy) simply does not exist here."""
    return {'unit': d['unit'], 'beds': d['beds'], 'bath': d['bath'],
            'sqft': '0', 'rent': d['rent'] or '', 'deposit': '',
            'status': d['status'], 'pets': '', 'parking': '', 'term': '',
            'email': '', 'phone': '', 'rr': 1,
            'desc': '%s | door taken from the Buildium rent roll; listing '
                    'detail is not in the Unit Summary extract.'
                    % (code or d['scope'])}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    if not args:
        sys.exit(__doc__)
    report = os.path.expanduser(args[0])
    raw, m, blob = load()
    prev_audit = blob.get('audit') or {}
    homes = blob['homes']
    before_doors = sum(len(h['units']) for h in homes)
    before_vac = sum(1 for h in homes for u in h['units']
                     if u['status'] == 'Vacant')

    R = cover.resolve_all(blob, report)
    for coll in (R['doors'], R['active']):
        for d in coll:
            if not d['code'] and d['scope'] in SCOPE_CODE:
                d['code'] = SCOPE_CODE[d['scope']]
    R['hits'] = [(SCOPE_CODE.get(sc, c), u, k, sc, st)
                 for c, u, k, sc, st in R['hits']]
    for miss in R['misses']:
        miss['code'] = SCOPE_CODE.get(miss['scope'], miss['code'])
    asof = R['meta']['asof']
    active = R['active']
    doors_all = R['doors']

    # ---- 1. statuses, from the roll, onto the doors that resolved ----------
    target = {}
    for code, unit, key, scope, status in R['hits']:
        if key in target:
            sys.exit('REFUSE: two roll doors resolved onto the same map door '
                     '%s (%s / %s)' % (key, target[key][1], unit))
        target[key] = (code, unit, scope, status)
    by_door = {(d['scope'], d['unit']): d for d in active}
    flips = {'to_vacant': [], 'to_rented': []}
    for (i, ui), (code, unit, scope, status) in target.items():
        u = homes[i]['units'][ui]
        if u['status'] != status:
            flips['to_vacant' if status == 'Vacant' else 'to_rented'].append(
                (homes[i]['name'], u['unit']))
            u['status'] = status
        d = by_door[(scope, unit)]
        if d['preleased']:
            u['preleased'] = d['preleased']
        else:
            u.pop('preleased', None)
        # fill blanks only — never let the roll's sparse row erase listing data
        for src, dst in (('beds', 'beds'), ('bath', 'bath'), ('rent', 'rent')):
            if d[src] and not u.get(dst):
                u[dst] = d[src]

    # ---- 2. doors the roll has and the pin does not: add them --------------
    added_doors = []
    for miss in R['misses']:
        if miss['home'] is None:
            continue
        h = homes[miss['home']]
        h['units'].append(door_unit(miss['door'], miss['code']))
        if not h.get('code') and miss['code']:
            h['code'] = miss['code']
        added_doors.append((h['name'], miss['unit'], miss['door']['status']))

    # ---- 3. whole properties the map lacks --------------------------------
    added_homes, unplaceable = [], []
    noscope = {}
    for miss in R['misses']:
        if miss['home'] is None:
            noscope.setdefault(miss['scope'], []).append(miss['door'])
    for scope, ds in sorted(noscope.items()):
        spec = NEW_PROPS.get(scope)
        if not spec:
            unplaceable.append((scope, [d['unit'] for d in ds],
                                'no pin on the map and no location supplied'))
            continue
        got = geocode.lookup(spec['query'], spec['city'])
        if not got:
            unplaceable.append((scope, [d['unit'] for d in ds],
                                'geocoder could not place %r' % spec['query']))
            continue
        lat, lng, src, postal = got
        pod, dist = assign_pod(blob, lat, lng)
        code = ds[0]['code']
        homes.append({
            'name': spec['name'], 'type': spec['type'],
            'addr': '%s, %s AB%s' % (spec['name'], spec['city'],
                                     ' ' + postal if postal else ''),
            'city': spec['city'], 'lat': lat, 'lng': lng, 'pod': pod,
            'code': code, 'rr': 1,
            'units': [door_unit(d, code) for d in ds]})
        added_homes.append((spec['name'], len(ds), pod, round(dist, 1),
                            src, spec['why']))

    # ---- 3b. permanent capture: stamp the Buildium code on every pin the roll
    # reached, so the next report — and the ILS listing join — match by code
    # instead of re-deriving from addresses. Stamp the code that owns most of
    # the pin's doors, not merely the first one seen.
    owners = {}
    for code, unit, (i, ui), scope, status in R['hits']:
        if code:
            owners.setdefault(i, Counter())[code] += 1
    # Doors added in step 2 count too — a pin that Buildium reached only with
    # NEW doors would otherwise never be stamped, and the ILS listing join
    # would miss every ad against it.
    for miss in R['misses']:
        if miss['home'] is not None and miss['code']:
            owners.setdefault(miss['home'], Counter())[miss['code']] += 1
    # A pin can hold doors from SEVERAL codes — the map keeps one pin for
    # 18120 28 Ave SW while Buildium splits it across SF316/318/320/322/323/…
    # Keep every code, or the ILS listing join silently misses those ads.
    stamped = 0
    for i, c in owners.items():
        best = c.most_common(1)[0][0]
        allc = sorted(c)
        if homes[i].get('code') != best or homes[i].get('codes') != allc:
            homes[i]['code'] = best
            if len(allc) > 1:
                homes[i]['codes'] = allc
            else:
                homes[i].pop('codes', None)
            stamped += 1

    # ---- 4. map doors the active roll does not claim -----------------------
    off_parsed = {s: addr.parse(s) for s in
                  {d['scope'] for d in doors_all if d['offboard'] or d['internal']}}
    active_parsed = {s: addr.parse(s) for s in {d['scope'] for d in active}}
    idx_addr = {i: cover.home_addr(h) for i, h in enumerate(homes)}
    removed = []
    drop = {}
    for i, ui in R['unclaimed']:
        drop.setdefault(i, set()).add(ui)
    # A door already claimed elsewhere at the same address is a duplicate pin,
    # not a stale door — say so, rather than blaming an off-boarding that has
    # nothing to do with it.
    claimed_at, claimed_street = {}, {}
    for (i, ui) in R['claimed']:
        a = idx_addr[i]
        uid = resolve.nz(homes[i]['units'][ui]['unit'])
        if a['street'] and a['houses']:
            for hn in a['houses']:
                claimed_at.setdefault((a['street'], hn, uid), homes[i]['name'])
            # Same street, distinctive (non-numeric) id: the map splits SF46
            # across 8405 and 8409, so 'BSM-C2' can be pinned at the sibling.
            if not uid.replace(' ', '').isdigit():
                claimed_street.setdefault(
                    (addr.street_key(a['street'], True), uid), homes[i]['name'])
    for i, uis in drop.items():
        h = homes[i]
        ha = idx_addr[i]
        off = next((s for s, pa in off_parsed.items() if addr.same_place(pa, ha)), None)
        act = next((s for s, pa in active_parsed.items() if addr.same_place(pa, ha)), None)
        for ui in uis:
            u = h['units'][ui]
            dup, uid = None, resolve.nz(u['unit'])
            if ha['street']:
                for hn in ha['houses']:
                    dup = claimed_at.get((ha['street'], hn, uid))
                    if dup and dup != h['name']:
                        break
                    dup = None
                if not dup and not uid.replace(' ', '').isdigit():
                    d2 = claimed_street.get(
                        (addr.street_key(ha['street'], True), uid))
                    if d2 and d2 != h['name']:
                        dup = d2
            if dup:
                why = 'the same door is already pinned as "%s"' % dup[:44]
            elif off:
                why = 'off-boarded in Buildium (%s)' % off[:44]
            elif act:
                why = 'door id not in %s' % act[:44]
            else:
                why = 'property is not in the rent roll at all'
            removed.append({'home': h['name'], 'unit': u['unit'],
                            'was': u['status'], 'why': why})
        h['units'] = [u for k, u in enumerate(h['units']) if k not in uis]
    dropped_homes = [h['name'] for h in homes if not h['units']]
    blob['homes'] = homes = [h for h in homes if h['units']]

    # ---- 5. the bridge, from Buildium's own totals down to the map ---------
    lease_rows = len(R['recs'])
    all_doors = len(doors_all)
    dupes = R['dupes']
    excluded = all_doors - len(active) - len(dupes)
    notdoor = len(R['notdoors'])
    doors = len(active) - notdoor
    matched = len(target)
    newdoors = len(added_doors) + sum(n for _, n, _, _, _, _ in added_homes)
    gap = sum(len(u) for _, u, _ in unplaceable)
    if matched + newdoors + gap != doors:
        sys.exit('REFUSE: bridge does not close: %d matched + %d added + %d '
                 'unplaced != %d active doors' % (matched, newdoors, gap, doors))
    after_doors = sum(len(h['units']) for h in homes)
    if after_doors != doors - gap:
        sys.exit('REFUSE: map holds %d doors but the roll accounts for %d'
                 % (after_doors, doors - gap))
    after_vac = sum(1 for h in homes for u in h['units'] if u['status'] == 'Vacant')
    roll_vac = sum(1 for d in active if d['status'] == 'Vacant')
    # SF168's 'Site Inspections' is carried as a vacant unit in Buildium but it
    # is not a door; it must come out of the vacancy numerator too, or the map
    # shows a vacancy that can never be leased.
    notdoor_vac = sum(1 for c, u, s in R['notdoors']
                      if by_door[(s, u)]['status'] == 'Vacant')
    unplaced_vac = sum(1 for s, us, _ in unplaceable
                       for d in noscope.get(s, []) if d['status'] == 'Vacant')
    placeable_vac = roll_vac - notdoor_vac - unplaced_vac
    if after_vac != placeable_vac:
        sys.exit('REFUSE: map shows %d vacant, roll says %d placeable vacant '
                 '(%d roll - %d non-door - %d unplaced)'
                 % (after_vac, placeable_vac, roll_vac, notdoor_vac, unplaced_vac))

    # The change log describes a TRANSITION, not a run. Re-running against the
    # same roll is a no-op, and a no-op must not erase the record of what the
    # previous run actually did to the map.
    changed = bool(added_homes or added_doors or removed or dropped_homes)
    if changed:
        changelog = {
            'added_homes': [{'name': n, 'doors': d, 'pod': p, 'km': k,
                             'source': s, 'why': w}
                            for n, d, p, k, s, w in added_homes],
            'removed': removed, 'dropped_homes': dropped_homes,
            'added_doors': len(added_doors),
            'from_source': os.path.basename(report), 'on': asof,
            'applied': datetime.date.today().isoformat()}
    else:
        changelog = prev_audit.get('changelog') or {
            'added_homes': [], 'removed': [], 'dropped_homes': [],
            'added_doors': 0, 'from_source': os.path.basename(report),
            'on': asof, 'applied': datetime.date.today().isoformat()}

    audit = {
        'kind': 'rentroll', 'asof': asof, 'source': os.path.basename(report),
        'changelog': changelog,
        'lease_rows': lease_rows, 'all_doors': all_doors,
        'excluded': excluded,
        'duplicate_records': dupes,
        'not_a_door': [
            {'code': c, 'unit': u} for c, u, s in R['notdoors']],
        # Codes the roll carries but deliberately excludes, so a later pass
        # (the ILS listing check) can tell "off-boarded" from "never heard of".
        'offboard_codes': sorted({d['code'] for d in doors_all
                                  if d['code'] and d['offboard']}),
        'internal_codes': sorted({d['code'] for d in doors_all
                                  if d['code'] and d['internal']}),
        'roll_codes': sorted({d['code'] for d in doors_all if d['code']}),
        'doors_raw': len(active), 'doors': doors,
        'matched': matched, 'added_doors': len(added_doors),
        'added_homes': [{'name': n, 'doors': d, 'pod': p, 'km': k,
                         'source': s, 'why': w} for n, d, p, k, s, w in added_homes],
        'unplaced': [{'scope': s, 'units': u, 'why': w} for s, u, w in unplaceable],
        'unplaced_doors': gap, 'unplaced_vacant': unplaced_vac,
        'roll_vacant': roll_vac, 'notdoor_vacant': notdoor_vac,
        'removed': removed, 'dropped_homes': dropped_homes,
        'vacant': after_vac, 'map_doors': after_doors,
        'generated': datetime.date.today().isoformat(),
    }
    blob['audit'] = audit

    pct = 100.0 * (after_doors - after_vac) / after_doors
    print('rent roll %s (as of %s)' % (os.path.basename(report), asof))
    print('  lease rows %d -> %d doors (%d off-boarded/internal excluded)'
          % (lease_rows, all_doors, excluded))
    if dupes:
        print('  duplicate Buildium records set aside: %d' % len(dupes))
        for d in dupes:
            print('      = %-58s %-8s %-7s  (kept %s, %s)'
                  % (d['scope'][:58], d['unit'], d['status'],
                     d['kept'][:44], d['kept_status']))
    print('  BRIDGE  %d active doors - %d non-door = %d' % (len(active), notdoor, doors))
    print('          %d matched on the map + %d added + %d unplaced = %d  OK'
          % (matched, newdoors, gap, doors))
    print('  VACANT  %d in the roll - %d non-door - %d unplaced = %d on the map'
          % (roll_vac, notdoor_vac, unplaced_vac, after_vac))
    print('  doors   %d -> %d      vacant %d -> %d      occupancy %.1f%%'
          % (before_doors, after_doors, before_vac, after_vac, pct))
    print('  status flips: %d newly vacant, %d newly leased'
          % (len(flips['to_vacant']), len(flips['to_rented'])))
    print('  pins stamped with a Buildium code: %d' % stamped)
    print('  doors added to existing pins : %d' % len(added_doors))
    print('  properties added             : %d' % len(added_homes))
    for n, d, p, k, s, w in added_homes:
        print('      + %-30s %d door(s)  pod %-3s %5.1f km  [%s] %s'
              % (n, d, p, k, s, w))
    print('  map doors removed            : %d (pins dropped: %d)'
          % (len(removed), len(dropped_homes)))
    for r in removed:
        print('      - %-34s %-14s was %-7s %s'
              % (r['home'][:34], r['unit'][:14], r['was'], r['why']))
    print('  doors the roll has that stay unplaced: %d (%d of them vacant)'
          % (gap, unplaced_vac))
    for s, u, w in unplaceable:
        print('      ! %-46s %s  — %s' % (s[:46], u, w))
    if check:
        print('\n--check: no files written')
        return
    out = json.dumps(blob, ensure_ascii=False, separators=(',', ':'))
    write_html(raw[:m.start(2)] + out + raw[m.end(2):])
    print('\nwrote %s' % os.path.normpath(HTML))


if __name__ == '__main__':
    main()
