"""Buildium REST API pull -> the same door records rrlib.to_doors emits.

A THIRD source shape, after the Vacant Units xlsx (vaclib) and the Rent Roll
xlsx (rrlib). It arrives as CSV written by zen-l2l's pipeline/buildium_pull.py
(build/buildium/<date>/reports/), not as a spreadsheet download.

This is deliberately an ADAPTER, not a second pipeline. It produces door dicts
in exactly rrlib's shape, so cover.py's resolution, apply_rentroll.py's
both-directions coverage control, the bridge, the pod assignment and both
refusals all run unchanged. Adding a source should cost one loader, not a
parallel copy of everything downstream.

WHY unit_state.csv AND NOT vacant_extracted.csv. Carrie sent the vacancy
extract, which is the richer file -- asking rents, listing copy, open work
orders. But it lists only VACANT doors, and a door missing from a vacancy-only
file is indistinguishable from a leased one: a parse failure looks exactly like
a lease. That is the trap the rent-roll migration was built to escape. So
unit_state.csv (both sides of all 798 doors) is the SPINE, and
vacant_extracted.csv is layered on top as ENRICHMENT for the doors it covers.

WHAT THIS SOURCE IS BETTER AT than the rent roll: it is already at door grain
(no lease-grain collapse, no historical rows), it carries sqft and a real
asking rent for vacant doors -- the long-standing gap where 152 of 205 vacant
doors showed no rent, because a rent roll's Rent column is contract rent and a
vacant door has no contract -- and it carries make-ready state (open work
orders) that no previous source had.
"""
import csv
import os
import re

import rrlib
import vaclib

# The pull already applies a scope filter, but it misses the typo'd markers:
# the 2026-09-11 pull carried "SF100 - ... - OFFBAORDED COMPLETED" and
# "SF242- ... - OFRFBOARDED" as stabilised, in-scope doors. vaclib.offboard_hit
# matches the WORD fuzzily (difflib >= 0.82) precisely so the next typo needs no
# code change, so offboarding is re-decided here from the label rather than
# trusted from upstream. Three doors, but they are three doors of fake vacancy.
INTERNAL_PAT = vaclib.INTERNAL_PAT


def _f(s):
    """'1450.0' -> '1450'; '' -> ''. The map renders rents as strings."""
    s = (s or '').strip()
    if not s:
        return ''
    try:
        v = float(s)
    except ValueError:
        return s
    return str(int(v)) if v == int(v) else str(v)


def _bedbath(beds, baths):
    beds, baths = (beds or '').strip(), (baths or '').strip()
    if not beds and not baths:
        return ''
    return '%s Bed/%s Bath' % (beds, baths)


def load_unit_state(path, asof):
    """unit_state.csv -> door records in rrlib.to_doors' shape.

    Status comes from Buildium's own Occupied/Vacant, which this export states
    for every door -- unlike the rent roll, where status had to be derived from
    lease dates against the as-of.
    """
    doors = []
    with open(path, newline='', encoding='utf-8-sig') as fh:
        for i, r in enumerate(csv.DictReader(fh), 2):
            scope = (r.get('property') or '').strip()
            unit = (r.get('unit') or '').strip()
            if not scope or not unit:
                continue
            status = 'Rented' if (r.get('status') or '').strip() == 'Occupied' \
                else 'Vacant'
            lease_end = (r.get('lease_to') or '').strip()
            pre = (r.get('next_lease_from') or '').strip()

            # Availability is a WINDOW, not a boolean -- identical rules to
            # rrlib, deliberately, so the two sources cannot disagree about
            # what "expiring" means.
            if status == 'Vacant':
                state = 'preleased' if pre else 'vacant'
                avail = (r.get('available_date') or '').strip() or (asof if not pre else '')
            elif pre:
                state, avail = 'preleased', ''
            elif lease_end and rrlib._within(lease_end, asof,
                                             rrlib.MARKETING_WINDOW_DAYS):
                state, avail = 'expiring', rrlib._plus(lease_end)
            else:
                state, avail = 'leased', (rrlib._plus(lease_end) if lease_end else '')

            # A vacant door's asking rent is listed_rent or market_rent; a
            # leased door's is what it actually collects. Never blend the two.
            rent = _f(r.get('listed_rent')) or _f(r.get('market_rent')) \
                if status == 'Vacant' else \
                (_f(r.get('lease_rent')) or _f(r.get('market_rent')))

            doors.append({
                'state': state, 'avail': avail,
                'scope': scope, 'unit': unit,
                'code': (r.get('code') or '').strip(),
                'offboard': bool(vaclib.offboard_hit(scope)),
                'internal': bool(INTERNAL_PAT.search(scope)),
                'status': status, 'preleased': pre,
                'bedbath': _bedbath(r.get('beds'), r.get('baths')),
                'beds': (r.get('beds') or '').strip(),
                'bath': (r.get('baths') or '').strip(),
                'rent': rent,
                'lease_end': lease_end, 'leases': 1, 'row': i,
                'sqft': (r.get('sqft') or '').strip(),
                # carried for enrichment / the page, not used by resolution
                'listed': (r.get('listed') or '').strip() == 'Y',
                'days_vacant': (r.get('days_vacant') or '').strip(),
                'addr_full': (r.get('address') or '').strip(),
                'city': (r.get('city') or '').strip(),
                'postal': (r.get('postal') or '').strip(),
            })
    return doors


def load_vacant_extract(path):
    """vacant_extracted.csv -> {(scope, unit): enrichment}.

    Vacancy-only by construction, so it is never the spine -- only a layer over
    doors unit_state already proved exist. Carries the two things no earlier
    source had: a real asking rent for a vacant door, and whether the door is
    physically ready to show (open work orders).
    """
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, newline='', encoding='utf-8-sig') as fh:
        for r in csv.DictReader(fh):
            scope = (r.get('property') or '').strip()
            unit = (r.get('unit') or '').strip()
            if not scope or not unit:
                continue
            ready = (r.get('move_in_ready') or '').strip()
            out[(scope, unit)] = {
                'ask': _f(r.get('listing_rent')) or _f(r.get('desc_rent'))
                       or _f(r.get('market_rent')),
                'deposit': (r.get('listing_deposit') or '').strip(),
                'listed': (r.get('is_listed') or '').strip() == 'Y',
                'sqft': (r.get('sqft') or '').strip(),
                'pets': (r.get('pets') or '').strip(),
                'parking': (r.get('parking') or '').strip(),
                'term': (r.get('lease_term') or '').strip(),
                'incentive': (r.get('incentive') or '').strip(),
                'utilities': (r.get('utilities') or '').strip(),
                'agent': (r.get('agent') or '').strip(),
                'email': (r.get('agent_email') or '').strip(),
                'desc': (r.get('description') or '').strip(),
                'ready': ready,
                'blocker': (r.get('move_in_blocker') or '').strip(),
                'open_items': (r.get('open_work_items') or '').strip(),
                'application': (r.get('application_status') or '').strip(),
                'applicants': (r.get('applicants_live') or '').strip(),
                'available': (r.get('desc_available') or '').strip()
                             or (r.get('listing_available') or '').strip(),
            }
    return out


def asof_from_path(path):
    """The pull writes build/buildium/<YYYY-MM-DD>/reports/unit_state.csv, so
    the as-of is the folder, never the file's mtime -- a copied file keeps its
    date this way."""
    m = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.abspath(path))
    if not m:
        raise SystemExit('REFUSE: cannot read an as-of date from %r. This '
                         'source is dated by its pull folder; a file mtime is '
                         'not a report date.' % path)
    return m.group(1)


# ---------------------------------------------------------------- pod mapping
# A FOURTH shape: the consolidated per-door export Carrie produces from the Buildium
# pull ("all_units_pod_mapping.csv"). The richest source this map has had --
# authoritative rent WITH its provenance, the resolved ILS crosswalk, make-ready state,
# live applications, and Buildium-vs-ILS conflicts already computed.
#
# IT IS THE STABILISED BUCKET ONLY, and that is the whole reason it cannot be the spine.
# The 2026-09-11 file holds 677 doors and NONE of the 112 lease-up doors (RP27, Alces,
# SF348/352/353/354). Read as "the door count" it would drop every lease-up door -- the
# most actively-leasable inventory in the portfolio -- off the map. Carrie confirmed
# 2026-09-11 that the map keeps the full in-scope count and this file supplies detail:
#
#   677 stabilised + 112 lease-up - 1 duplicate door - 1 non-door = 787 on the map.
#
# Doors it does not cover keep what the spine gave them and are COUNTED as uncovered, so
# the gap is a figure on the page rather than a silent blank.

_ILS_RESOLVED = ('exact', 'code-only')      # crosswalk strong enough to act on


def load_pod_mapping(path):
    """-> ({(scope, unit): enrichment}, meta)."""
    out = {}
    codes, scopes = set(), set()
    with open(path, newline='', encoding='utf-8-sig') as fh:
        rdr = csv.DictReader(fh)
        need = {'property', 'unit', 'status', 'rent_authoritative', 'ils_status'}
        missing = need - set(rdr.fieldnames or ())
        if missing:
            raise SystemExit('REFUSE: %s is not a pod-mapping export (missing %s)'
                             % (os.path.basename(path), ', '.join(sorted(missing))))
        for r in rdr:
            scope = (r.get('property') or '').strip()
            unit = (r.get('unit') or '').strip()
            if not scope or not unit:
                continue
            codes.add((r.get('code') or '').strip())
            scopes.add(scope)
            ils_match = (r.get('ils_match') or '').strip()
            out[(scope, unit)] = {
                # Rent WITH its provenance. Two doors can both say $1,750 and mean
                # different things -- one read off a live listing description, one the
                # Buildium MarketRent field with no listing at all.
                'ask': _f(r.get('rent_authoritative')),
                'rent_source': (r.get('rent_source') or '').strip(),
                'deposit': (r.get('listing_deposit') or '').strip()
                           or (r.get('desc_deposit') or '').strip(),
                'sqft': (r.get('sqft') or '').strip(),
                'pets': (r.get('pets') or '').strip(),
                'parking': (r.get('parking') or '').strip(),
                'term': (r.get('lease_term') or '').strip(),
                'incentive': (r.get('incentive') or '').strip(),
                'utilities': (r.get('utilities') or '').strip(),
                'agent': (r.get('agent') or '').strip(),
                'email': (r.get('agent_email') or '').strip(),
                'desc': (r.get('description') or '').strip(),
                'amen': (r.get('unit_amenities') or '').strip(),
                # Make-ready: whether the door can actually be shown.
                'ready': (r.get('move_in_ready') or '').strip(),
                'blocker': (r.get('move_in_blocker') or '').strip(),
                'ready_date': (r.get('move_in_ready_date') or '').strip(),
                'open_items': (r.get('open_work_detail') or '').strip(),
                # Availability date AND how it was decided -- a date off a listing and a
                # date derived from a lease end are not the same claim.
                'avail_date': (r.get('available_date') or '').strip(),
                'avail_source': (r.get('available_date_source') or '').strip(),
                # Applications in the last 30 days.
                'application': (r.get('application_status_30d') or '').strip(),
                'has_application': (r.get('has_live_application') or '').strip() == 'Y',
                'applicants': (r.get('applicants_30d') or '').strip(),
                # The ILS crosswalk, already resolved upstream.
                'ils_match': ils_match,
                'ils_resolved': ils_match in _ILS_RESOLVED,
                'ils_status': (r.get('ils_status') or '').strip(),
                'ils_live': (r.get('ils_live') or '').strip() == 'Y',
                'ils_unit_id': (r.get('ils_unit_id') or '').strip(),
                'ils_conflicts': (r.get('ils_conflicts') or '').strip(),
                'filled_from': (r.get('filled_from') or '').strip(),
                'lease_to': (r.get('lease_to') or '').strip(),
                'next_lease_from': (r.get('next_lease_from') or '').strip(),
                'status': (r.get('status') or '').strip(),
            }
    return out, {'rows': len(out), 'codes': len(codes - {''}), 'scopes': len(scopes),
                 'source': os.path.basename(path)}


def ads_from_pod_mapping(enrich, asof, window=None):
    """Derive the advertising worklist from the resolved ILS crosswalk.

    Replaces the ILS-feed join apply_listings.py had to do by hand, because this export
    already carries ils_unit_id / ils_status per door.

    THE RULE THAT MATTERS: "leased" does NOT mean "pull the ad". A lease ending inside the
    marketing window with no replacement is live demand, and switching that ad off tells
    staff to stop working a door that is about to be empty. Five doors in the 2026-09-11
    file are exactly that -- one of them a lease ending the next day. Availability is a
    window, not a flag.

    A door whose crosswalk is unresolved ('none'/'ambiguous') never produces a turn-off
    call: killing an ad for a genuinely vacant door costs real money, so ambiguity goes to
    a human. Every ILS-enabled door in the 2026-09-11 file happened to be resolved, but
    the guard is the point, not the luck.
    """
    window = rrlib.MARKETING_WINDOW_DAYS if window is None else window
    turn_off, keep_live, advertised_vacant, check = [], [], [], []
    for (scope, unit), e in sorted(enrich.items()):
        if e['ils_status'] != 'enabled':
            continue                                   # not advertised; nothing to do
        row = {'scope': scope, 'unit': unit, 'ils_unit_id': e['ils_unit_id'],
               'match': e['ils_match'], 'ask': e['ask']}
        if not e['ils_resolved']:
            check.append(dict(row, why='ILS crosswalk is %r -- which door this ad points '
                                       'at is not settled' % (e['ils_match'] or 'unknown')))
        elif e['status'] != 'Occupied':
            advertised_vacant.append(dict(row, why='vacant and advertised — correct'))
        elif e['next_lease_from']:
            turn_off.append(dict(row, why='pre-leased, next lease starts %s'
                                          % e['next_lease_from']))
        elif e['lease_to'] and rrlib._within(e['lease_to'], asof, window):
            keep_live.append(dict(row, why='lease ends %s, inside the %d-day window and no '
                                           'replacement — live demand'
                                           % (e['lease_to'], window)))
        elif e['lease_to']:
            turn_off.append(dict(row, why='leased to %s, beyond the %d-day window'
                                          % (e['lease_to'], window)))
        else:
            check.append(dict(row, why='occupied but no lease end on file'))
    enabled = len(turn_off) + len(keep_live) + len(advertised_vacant) + len(check)
    no_ad = sorted((s, u) for (s, u), e in enrich.items()
                   if e['status'] != 'Occupied' and e['ils_status'] != 'enabled')
    return {'turn_off': turn_off, 'keep_live': keep_live,
            'advertised_vacant': advertised_vacant, 'check': check,
            'enabled': enabled, 'no_ad': [{'scope': s, 'unit': u} for s, u in no_ad],
            'window': window, 'asof': asof}
