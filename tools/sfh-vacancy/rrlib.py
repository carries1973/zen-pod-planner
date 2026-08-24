"""Parse a Buildium 'Rent Roll' export into the same record shape as vaclib.

Why this exists: the Vacant Units report only lists the vacant subset, so the
map could never tell "this door is leased" from "this door is not in the
report" — the exact silent-drop failure mode. The Rent Roll enumerates EVERY
door with its tenant (or VACANT), and carries its own per-property summary
block, so coverage can be reconciled per property in both directions.

Structural facts (all verified against Rent_Roll (11).xlsx, as of 2026-08-20):
  * one detail section, then 'Grand totals', 'Summary by bed/bath', and
    'Summary by property' blocks;
  * property headers are detected by ROW SHAPE (col A populated, every other
    column empty) — never by name, so new properties parse with no code change;
  * the first property header is repeated in the page-header block above the
    column header row, so the detail section starts AFTER 'Unit'/'Tenants';
  * a unit is vacant iff its Tenants cell is exactly 'VACANT'.
"""
import openpyxl, re, sys
from vaclib import offboard_hit, INTERNAL_PAT, norm_unit

SHEET = 'Rent Roll'
_SUMMARY_HEADS = ('grand total', 'summary by', 'totals and averages')


def _s(c):
    return '' if c is None else str(c).strip()


def _split_bedbath(s):
    """\"3 Bed/2 Bath\" -> ('3','2');  \"'- /1 Bath\" -> ('','1')"""
    if not s:
        return '', ''
    m = re.search(r'([\d.]*)\s*Bed', s)
    beds = m.group(1) if m else ''
    m = re.search(r'([\d.]*)\s*Bath', s)
    bath = m.group(1) if m else ''
    return beds, bath


def parse(path):
    """-> (records, meta). Refuses unless the parsed detail rows reconcile with
    the report's own 'Summary by property' block, property by property."""
    ws = openpyxl.load_workbook(path, data_only=True)[SHEET]
    rows = [[_s(c) for c in r] for r in ws.iter_rows(values_only=True)]

    asof = None
    for r in rows[:3]:
        for c in r:
            m = re.search(r'As of (\d{4}-\d{2}-\d{2})', c)
            if m:
                asof = m.group(1)

    # ---- locate the detail section ---------------------------------------
    start = None
    for i, r in enumerate(rows):
        if r[0] == 'Unit' and r[1] == 'Tenants':
            start = i + 1
            break
    if start is None:
        raise SystemExit('REFUSE: no Unit/Tenants header row in %s' % path)
    stop = None
    for i in range(start, len(rows)):
        if rows[i][0].lower().startswith(_SUMMARY_HEADS):
            stop = i
            break
    if stop is None:
        raise SystemExit('REFUSE: no summary block found in %s' % path)

    recs, cur = [], None
    for i in range(start, stop):
        r = rows[i]
        a = r[0]
        rest = [x for x in r[1:] if x]
        if a.lower().startswith('total for'):
            continue
        if not a and not rest:
            continue
        if not rest:                                  # scope header, by shape
            cur = a
            continue
        if cur is None:
            print('WARN orphan row %d: %r' % (i + 1, r[:4]), file=sys.stderr)
            continue
        beds, bath = _split_bedbath(r[4])
        recs.append({'row': i + 1, 'scope': cur, 'unit': a,
                     'tenants': r[1],
                     'status': 'Vacant' if r[1].upper() == 'VACANT' else 'Rented',
                     'bedbath': r[4], 'beds': beds, 'bath': bath,
                     'sqft': '', 'rent': r[7],
                     'lease_start': r[2][:10], 'lease_end': r[3][:10],
                     'vacated': '', 'available': '', 'nextlease': ''})

    # ---- the report's own per-property summary, for reconciliation --------
    summary, in_sum = {}, False
    for i in range(stop, len(rows)):
        r = rows[i]
        if r[0] == 'Property' and r[1].startswith('No. of Unit'):
            in_sum = True
            continue
        if not in_sum or not r[0]:
            continue
        if r[0].lower().startswith('totals and averages'):
            summary['__TOTAL__'] = (int(r[1]), int(r[2]), int(r[3]))
            break
        try:
            summary[r[0]] = (int(r[1]), int(r[2]), int(r[3]))
        except (ValueError, TypeError):
            continue
    if '__TOTAL__' not in summary:
        raise SystemExit('REFUSE: no "Summary by property" totals row in %s' % path)

    # ---- refuse on any divergence, in EITHER direction --------------------
    seen = {}
    for r in recs:
        n, v = seen.get(r['scope'], (0, 0))
        seen[r['scope']] = (n + 1, v + (r['status'] == 'Vacant'))
    bad = []
    for scope, (n, v) in sorted(seen.items()):
        if scope not in summary:
            bad.append('%s: parsed %d doors, absent from summary block' % (scope, n))
            continue
        sn, sv, _ = summary[scope]
        if (n, v) != (sn, sv):
            bad.append('%s: parsed %d doors/%d vacant, summary says %d/%d'
                       % (scope, n, v, sn, sv))
    for scope in summary:
        if scope != '__TOTAL__' and scope not in seen:
            bad.append('%s: in summary block, no detail rows parsed' % scope)
    tn, tv, _ = summary['__TOTAL__']
    if len(recs) != tn or sum(1 for r in recs if r['status'] == 'Vacant') != tv:
        bad.append('grand total: parsed %d doors/%d vacant, report says %d/%d'
                   % (len(recs), sum(1 for r in recs if r['status'] == 'Vacant'),
                      tn, tv))
    if bad:
        raise SystemExit('REFUSE: rent roll does not reconcile with its own '
                         'summary block:\n  ' + '\n  '.join(bad[:25]))

    for r in recs:
        m = re.match(r'^((?:SF|RP|MF)\s*\d+)\b', r['scope'])
        r['code'] = re.sub(r'\s+', '', m.group(1)) if m else None
        r['offboard'] = offboard_hit(r['scope']) is not None
        r['internal'] = bool(INTERNAL_PAT.search(r['scope']))
        r['key'] = (r['code'], norm_unit(r['unit']))

    return recs, {'asof': asof, 'stop': stop, 'declared': tn,
                  'declared_vacant': tv, 'summary': summary,
                  'kind': 'rentroll'}


def to_doors(recs, asof):
    """Collapse lease rows onto DOORS.

    A Buildium rent roll run with 'All leases' emits one row per lease —
    historical, current and future — so its own unit counts are lease counts,
    not door counts. Treating them as doors triples some properties (SF201's
    '11207 - Bsmt' appears three times) and blends a ratio's numerator and
    denominator. Doors are keyed by (scope, unit); status is decided from the
    lease dates against the report's as-of date:

      * a lease covering as-of        -> Rented
      * else an explicit VACANT row   -> Vacant   (Buildium emits one per
                                                   currently-unleased door)
      * else a lease starting later   -> Vacant, pre-leased
      * anything else                 -> refused, never guessed
    """
    from collections import OrderedDict
    grouped = OrderedDict()
    for r in recs:
        grouped.setdefault((r['scope'], r['unit']), []).append(r)

    doors, ambiguous = [], []
    for (scope, unit), rs in grouped.items():
        vac_row = next((r for r in rs if r['status'] == 'Vacant'), None)
        leases = [r for r in rs if r['status'] == 'Rented' and r['lease_start']]
        cur = [r for r in leases if r['lease_start'] <= asof
               and (not r['lease_end'] or r['lease_end'] >= asof)]
        fut = sorted((r for r in leases if r['lease_start'] > asof),
                     key=lambda r: r['lease_start'])
        if cur:
            src = max(cur, key=lambda r: r['lease_start'])
            status, pre = 'Rented', (fut[0]['lease_start'] if fut else '')
        elif vac_row:
            src = vac_row
            status, pre = 'Vacant', (fut[0]['lease_start'] if fut else '')
        elif fut:
            src = fut[0]
            status, pre = 'Vacant', fut[0]['lease_start']
        else:
            ambiguous.append((scope, unit,
                              [(r['tenants'][:24], r['lease_start'],
                                r['lease_end']) for r in rs]))
            continue
        # bed/bath and rent: take them from whichever row actually describes
        # the door today, but never let a blank current row erase a known value
        bedbath = src['bedbath'] or next((r['bedbath'] for r in rs if r['bedbath']), '')
        beds, bath = _split_bedbath(bedbath)
        doors.append({'scope': scope, 'unit': unit, 'code': rs[0]['code'],
                      'offboard': rs[0]['offboard'], 'internal': rs[0]['internal'],
                      'status': status, 'preleased': pre,
                      'bedbath': bedbath, 'beds': beds, 'bath': bath,
                      'rent': src['rent'] or next((r['rent'] for r in rs if r['rent']), ''),
                      'lease_end': src['lease_end'], 'leases': len(rs),
                      'row': rs[0]['row'], 'sqft': ''})
    if ambiguous:
        raise SystemExit(
            'REFUSE: %d door(s) have no lease covering %s and no VACANT row, '
            'so their status cannot be read from this report:\n  %s'
            % (len(ambiguous), asof,
               '\n  '.join('%s / %s %s' % a for a in ambiguous[:10])))
    return doors
