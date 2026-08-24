"""Resolve EVERY active door in a Buildium Rent Roll onto the SFH map, and
report coverage in both directions.

The Vacant-Units pipeline could only ever answer "is this door vacant?"; a door
missing from the report was indistinguishable from a leased door, so a parse
failure looked like a lease. The rent roll states both sides, so the control
here is coverage-vs-source: every roll door must land on a map door or be named,
and every map door must be claimed by the roll or be named.

Matching is property-first — a scope narrows to candidate homes, then doors are
matched inside those homes — because 1,465 doors searched globally produces
plausible-looking cross-property matches.
"""
import re
from collections import defaultdict
import vaclib
import addr
from resolve import (nz, unit_tokens, street_sig, unit_match, build_index,
                     OVERRIDE, NOT_A_DOOR, ALCES_RE)

# Buildium scope labels that name several street addresses at once
# ('11207, 11209 51 Street NW - Barry1'). Doors route by house-number prefix.
ANNOT_STRIP = re.compile(r'\s*[-(]\s*(?:New\s+PMA|Returning)\b.*$', re.I)


def home_addr(h):
    """Parse a map home's own address, falling back to its display name."""
    a = addr.parse(h['addr'])
    if not a['street'] or not a['houses']:
        b = addr.parse(h['name'])
        if b['street'] and b['houses']:
            return b
    return a


def scope_candidates(code, label, idx, extra_houses=(), unit_ids=(),
                     addr_owned=frozenset()):
    """Homes this scope could refer to, best first, with how it was decided.

    The signals are UNIONED, not raced. A Buildium scope routinely spans
    several map pins — SF175 is one scope for '61 - 83 Fenwyck Boulevard'
    while the map carries a pin per house number, and SF46 covers both 8405
    and 8409 108 Street — so stopping at the first signal that fires strands
    every door that belongs to a sibling pin.

    A shared house number alone never matches: Edmonton's numbered grid would
    make every '#21' collide.
    """
    ranked = {}

    def add(x, tier):
        if x['i'] not in ranked or ranked[x['i']][0] < tier:
            ranked[x['i']] = (tier, x)

    how = []
    if code:
        for x in idx:
            if x['raw'].get('code') == code:
                add(x, 3)
        if ranked:
            how.append('code')
    if code and code in OVERRIDE:
        key = nz(OVERRIDE[code])
        for x in idx:
            if key in x['txt']:
                add(x, 2)
                if 'override' not in how:
                    how.append('override')
    pa = addr.parse(ANNOT_STRIP.sub('', label))
    # A scope's own unit ids name the house numbers it spans: SF337 is labelled
    # '10314 147 Street NW' but its doors are '10314/10316/10318 Main|Bsmt', and
    # the map carries a pin per house. Without this the sibling pins are not
    # even candidates and their doors strand.
    if extra_houses:
        pa = dict(pa, houses=pa['houses'] | set(extra_houses))
    hint = pa['hint'].lstrip('#').lower()
    for x in idx:
        if addr.same_place(pa, x['addr']):
            add(x, 1)
            if 'address' not in how:
                how.append('address')
    # Same street, and the pin's own door ids are this scope's door ids. The map
    # sometimes splits one Buildium scope across neighbouring house numbers
    # (SF46 is labelled '8405 108 Street' but the map also pins 8409 with
    # SF46's '2F-A2'/'BSM-C1' ids), which no address rule can reach.
    # Only pins that NO scope reaches by address may be borrowed this way.
    # Apartment ids repeat across buildings — '202' exists at both 3607 and
    # 3611 118 Ave — so without that guard SF232's doors walk into SF237's pin.
    if unit_ids and pa['street']:
        skey = addr.street_key(pa['street'], True)
        for x in idx:
            if x['i'] in ranked or x['i'] in addr_owned or not x['addr']['street']:
                continue
            if addr.street_key(x['addr']['street'], True) != skey:
                continue
            if {nz(u['unit']) for u in x['raw']['units']} & unit_ids:
                add(x, 1)
                if 'unit-ids' not in how:
                    how.append('unit-ids')
    if not ranked:
        return [], 'none'
    out = sorted(ranked.values(), key=lambda t: (
        t[0],
        len(pa['houses'] & t[1]['addr']['houses']),
        1 if hint and hint == t[1]['addr']['hint'].lstrip('#').lower() else 0,
    ), reverse=True)
    return [x for _, x in out], '+'.join(how)


def drop_duplicate_records(active):
    """Set aside doors that are the SAME physical door recorded twice.

    Buildium can carry two property records for one address — Rivers Edge has
    both 'RP158 ... 170 North Railway St B26' (leased to 2027) and 'RP158 ...
    170 North Railway Street' with the same door B26 sitting VACANT since its
    last lease ended in 2025. Buildium's own summary block counts both, so the
    parse reconciles perfectly while the door count and the vacancy count are
    each one too high.

    The live record wins: a lease covering today proves the door is occupied.
    The loser is RETURNED, never dropped quietly — it is named in the bridge so
    the duplicate can be cleaned up at the source.
    """
    groups = {}
    for d in active:
        a = addr.parse(d['scope'])
        if not a['street']:
            groups[('', id(d))] = [d]
            continue
        key = (a['street'], tuple(sorted(a['houses'])),
               re.sub(r'[^a-z0-9]', '', d['unit'].lower()))
        groups.setdefault(key, []).append(d)
    keep, dupes = [], []
    for key, ds in groups.items():
        if len(ds) == 1 or len({d['scope'] for d in ds}) == 1:
            keep.extend(ds)
            continue
        ranked = sorted(ds, key=lambda d: (d['status'] == 'Rented',
                                           d['lease_end'] or ''), reverse=True)
        keep.append(ranked[0])
        for d in ranked[1:]:
            dupes.append({'scope': d['scope'], 'unit': d['unit'],
                          'status': d['status'],
                          'kept': ranked[0]['scope'],
                          'kept_status': ranked[0]['status']})
    return keep, dupes


def resolve_all(blob, report_path):
    homes = blob['homes']
    idx = build_index(homes)
    for x in idx:
        x['addr'] = home_addr(x['raw'])
    recs, meta = vaclib.load(report_path)
    if meta.get('kind') != 'rentroll':
        raise SystemExit('REFUSE: cover.py needs a Rent Roll, got %r'
                         % meta.get('kind'))
    import rrlib
    doors = rrlib.to_doors(recs, meta['asof'])
    active = [d for d in doors if not d['offboard'] and not d['internal']]
    active, dupes = drop_duplicate_records(active)

    byscope = defaultdict(list)
    for r in active:
        byscope[r['scope']].append(r)

    # Pass one: which pins does some scope reach by its own address? Those are
    # spoken for, and the unit-id fallback below must not poach them.
    addr_owned = set()
    for scope, rs in byscope.items():
        pa = addr.parse(ANNOT_STRIP.sub('', scope))
        prefixes = {p for p in (unit_tokens(r['unit'], rs[0]['code'])[0]
                                for r in rs) if p}
        if prefixes:
            pa = dict(pa, houses=pa['houses'] | prefixes)
        for x in idx:
            if addr.same_place(pa, x['addr']):
                addr_owned.add(x['i'])

    hits, misses, notdoors = [], [], []
    claimed = {}
    for scope, rs in sorted(byscope.items()):
        code = rs[0]['code']
        prefixes = {p for p in (unit_tokens(r['unit'], code)[0] for r in rs) if p}
        unit_ids = {nz(r['unit']) for r in rs}
        cands, how = scope_candidates(code, scope, idx, prefixes, unit_ids,
                                      addr_owned)
        for r in rs:
            if NOT_A_DOOR.search(r['unit']):
                notdoors.append((code, r['unit'], scope))
                continue
            if not cands:
                misses.append({'code': code, 'unit': r['unit'], 'scope': scope,
                               'why': 'no home on map', 'home': None, 'door': r})
                continue
            pref, suf = unit_tokens(r['unit'], code)
            # Multi-address scopes: a door's own house-number prefix decides
            # which of the scope's homes it belongs to.
            pool = cands
            if pref:
                narrowed = [c for c in cands if pref in c['anums']]
                if narrowed:
                    pool = narrowed
            found = None
            for c in pool:
                for ui, u in enumerate(c['raw']['units']):
                    if (c['i'], ui) in claimed:
                        continue
                    if unit_match(u['unit'], pref, suf):
                        found = (c['i'], ui)
                        break
                if found:
                    break
            # A single-door scope against a single-door home is unambiguous
            # even when the ids disagree ('Full' vs '1' vs the house number).
            # A single-door scope against a single-door home is unambiguous
            # even when the ids disagree ('Full House' vs '1' vs '#41'), as
            # long as the ranking has already settled which home it is.
            if not found and len(rs) == 1:
                singles = [c for c in pool
                           if len(c['raw']['units']) == 1
                           and (c['i'], 0) not in claimed]
                if singles and (len(singles) == 1 or singles[0] is pool[0]):
                    found = (singles[0]['i'], 0)
            if found:
                claimed[found] = (code, r['unit'], scope)
                hits.append((code, r['unit'], found, scope, r['status']))
            else:
                # The property is on the map, this door is not. Name the pin it
                # belongs to so the door can be added there rather than lost.
                misses.append({'code': code, 'unit': r['unit'], 'scope': scope,
                               'why': 'door absent from ' + homes[pool[0]['i']]['name'],
                               'home': pool[0]['i'], 'door': r})

    unclaimed = [(i, ui) for i, h in enumerate(homes)
                 for ui in range(len(h['units'])) if (i, ui) not in claimed]
    return {'meta': meta, 'recs': recs, 'doors': doors, 'active': active,
            'dupes': dupes, 'hits': hits,
            'misses': misses, 'notdoors': notdoors, 'claimed': claimed,
            'unclaimed': unclaimed, 'byscope': byscope}
