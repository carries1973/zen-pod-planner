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
