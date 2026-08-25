#!/usr/bin/env python3
"""Cross the live ILS listing feed against the map's availability, and build
the "still being advertised" worklist.

    python3 tools/sfh-vacancy/apply_listings.py \\
        "~/Downloads/2026-08-24_unit_list.csv" "~/Downloads/leads_2026-08-24.csv"

Run apply_rentroll.py FIRST — this reads the availability that put on the page,
and refuses if the page has no rent-roll audit.

What it does and does not claim
-------------------------------
The unit list is the live feed: a row with Status 'enabled' is an ad that is
up right now. Whether that ad SHOULD be up is decided against the rent roll.

The listing feed and Buildium do not agree on unit ids — the ILS writes 'G2'
where Buildium writes 'Bsmt - G2', '12228' where Buildium writes
'12228 - Garden', and one ad can cover several doors ('B1 & B2') or several
properties ('SF318, SF313, SF315, ...'). So a door-level match is attempted but
never required, and the verdict is only ever as strong as the evidence:

  turn off  — every property the ad names is fully leased, off-boarded, or gone
              from the roll. No unit-level ambiguity can rescue it.
  check     — the property has vacancy but the advertised unit reads as leased,
              or its unit id could not be resolved. A human decides.
  live      — the advertised door is vacant, or the ad names no unit and the
              property has vacancy.

Leads are attributed by property code (the code appears anywhere in the lead's
Property Name), so a dead ad shows what it is still costing in prospect time.
"""
import csv, json, os, re, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from resolve import nz, unit_tokens

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, '..', '..', 'sfh', 'index.html')
# The canonical listing -> door mapping. One row per (ILS Unit ID, door).
# A listing legitimately covers MORE THAN ONE door ("B1 & B2"), so this is a
# many-to-many table, not a column on either side. Once a pair is confirmed it
# is never guessed again — the ILS Unit ID is stable (225/225 distinct), the
# listing TITLE is not (only 67 of 225 lead titles still match a live listing).
CROSSWALK = os.path.join(HERE, 'listing_crosswalk.csv')
CW_FIELDS = ['ils_unit_id', 'scope', 'unit', 'source', 'confirmed_on', 'note']
BLOB_RE = re.compile(
    r'(<script id="data" type="application/json">)(.*?)(</script>)', re.S)
# Listing titles sometimes sub-designate a code with a trailing letter —
# 'SF204A - 11813 47 Street NW' is Buildium's SF204. Capture the letter so the
# token is consumed, then normalise to the numeric base the roll actually uses.
CODE_RE = re.compile(r'\b((?:SF|RP|MF)\s*\d+)[A-Za-z]?\b', re.I)
LEAD_WINDOW = 30


def codes_in(text):
    return sorted({re.sub(r'\s+', '', c).upper() for c in CODE_RE.findall(text or '')})


def read_crosswalk():
    if not os.path.exists(CROSSWALK):
        return {}
    out = {}
    for r in csv.DictReader(open(CROSSWALK, encoding='utf-8-sig')):
        uid = (r.get('ils_unit_id') or '').strip()
        if not uid:
            continue
        out.setdefault(uid, []).append(r)
    return out


def confirmed_only(cw):
    """Only a row a person has signed off is authoritative. Proposals stay in
    the file so they can be ticked, but they are re-derived every run — a guess
    that silently hardens into evidence is how the door-count dispute started."""
    out = {}
    for uid, rs in cw.items():
        ok = [r for r in rs if (r.get('confirmed_on') or '').strip()]
        if ok:
            out[uid] = ok
    return out


def write_crosswalk(rows):
    tmp = CROSSWALK + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=CW_FIELDS)
        w.writeheader()
        for r in sorted(rows, key=lambda r: (r['scope'], r['unit'], r['ils_unit_id'])):
            w.writerow({k: r.get(k, '') for k in CW_FIELDS})
    os.replace(tmp, CROSSWALK)


def load():
    raw = open(HTML, encoding='utf-8').read()
    m = BLOB_RE.search(raw)
    if not m:
        sys.exit('REFUSE: data blob not found in %s' % HTML)
    blob = json.loads(m.group(2))
    if (blob.get('audit') or {}).get('kind') != 'rentroll':
        sys.exit('REFUSE: run apply_rentroll.py first — the page carries no '
                 'rent-roll availability to check the listings against.')
    return raw, m, blob


def write_html(text):
    if not text or '<script id="data"' not in text:
        sys.exit('REFUSE: refusing to write a page with no data blob')
    tmp = HTML + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        fh.write(text)
    os.replace(tmp, HTML)


def door_index(homes):
    """code -> [(home_index, unit_index)] for every door on the map."""
    idx = {}
    for i, h in enumerate(homes):
        for c in ([h['code']] if h.get('code') else []) + list(h.get('codes') or []):
            idx.setdefault(c, [])
        for ui in range(len(h['units'])):
            for c in ([h['code']] if h.get('code') else []) + list(h.get('codes') or []):
                idx[c].append((i, ui))
    return idx


def unit_hits(homes, doors, want):
    """Doors among `doors` whose id plausibly denotes ILS unit id `want`."""
    w = nz(want)
    if not w:
        return []
    parts = [p.strip() for p in re.split(r'&|,| and ', w) if p.strip()]
    out = []
    for (i, ui) in doors:
        uid = nz(homes[i]['units'][ui]['unit'])
        pref, suf = unit_tokens(homes[i]['units'][ui]['unit'])
        for p in parts:
            if uid == p or suf == p or (pref and pref == p) \
               or (suf and p and suf.endswith(' ' + p)) \
               or (suf and p and p.endswith(' ' + suf)):
                out.append((i, ui))
                break
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    if not args:
        sys.exit(__doc__)
    unit_csv = os.path.expanduser(args[0])
    leads_csv = os.path.expanduser(args[1]) if len(args) > 1 else None
    raw, m, blob = load()
    homes = blob['homes']
    audit = blob['audit']
    offboard = set(audit.get('offboard_codes') or [])
    internal = set(audit.get('internal_codes') or [])
    roll_codes = set(audit.get('roll_codes') or [])
    idx = door_index(homes)

    window = int(audit.get('marketing_window') or 0)
    if not window:
        sys.exit('REFUSE: the page carries no marketing window — re-run '
                 'apply_rentroll.py so door availability states are present.')
    rows = list(csv.DictReader(open(unit_csv, encoding='utf-8-sig')))
    if not rows or 'Status' not in rows[0]:
        sys.exit('REFUSE: %s has no Status column — is this the ILS unit list?'
                 % unit_csv)
    enabled = [r for r in rows if (r.get('Status') or '').strip().lower() == 'enabled']
    disabled = len(rows) - len(enabled)

    # ---- leads, by property code ------------------------------------------
    leads_by_code, last_by_code, leads_total, leads_dated = {}, {}, 0, None
    if leads_csv:
        lrows = list(csv.DictReader(open(leads_csv, encoding='utf-8-sig')))
        leads_total = len(lrows)
        dates = [r['Inquiry Date'][:10] for r in lrows if r.get('Inquiry Date')]
        leads_dated = max(dates) if dates else None
        cutoff = (datetime.date.fromisoformat(leads_dated)
                  - datetime.timedelta(days=LEAD_WINDOW)).isoformat() \
            if leads_dated else None
        for r in lrows:
            d = (r.get('Inquiry Date') or '')[:10]
            for c in codes_in(r.get('Property Name')):
                if cutoff and d >= cutoff:
                    leads_by_code[c] = leads_by_code.get(c, 0) + 1
                if d and d > last_by_code.get(c, ''):
                    last_by_code[c] = d

    cw_all = read_crosswalk()
    cw = confirmed_only(cw_all)
    cw_rows, cw_new, cw_kept = [], 0, 0

    def door_key(i, ui):
        h = homes[i]
        return (h.get('code') or '', homes[i]['units'][ui]['unit'])

    def marketable(d):
        """A door worth advertising: empty now, or empty inside the marketing
        window with nothing lined up. 'Rented' alone is NOT a reason to pull an
        ad — a lease ending in three weeks is exactly what leasing is selling."""
        u = homes[d[0]]['units'][d[1]]
        return u.get('state') in ('vacant', 'expiring')

    turn_off, check_list, live, unmatched = [], [], 0, []
    for r in enabled:
        title = (r.get('Property Name') or '').strip()
        cs = codes_in(title)
        unum = (r.get('Unit #') or '').strip()
        uid = (r.get('Unit ID') or '').strip()
        doors = [d for c in cs for d in idx.get(c, [])]
        known = [c for c in cs if c in idx]
        gone = [c for c in cs if c not in idx]
        avail = [d for d in doors if marketable(d)]
        pins = sorted({homes[i]['name'] for i, _ in doors})
        lead30 = sum(leads_by_code.get(c, 0) for c in cs)
        last = max([last_by_code.get(c, '') for c in cs] or [''])
        item = {'title': title, 'codes': cs, 'unit': unum, 'ils_id': uid,
                'rent': (r.get('Rent') or '').strip(),
                'beds': (r.get('Bedrooms') or '').strip(),
                'pins': pins, 'leads30': lead30, 'last_lead': last}

        if not known:
            off = [c for c in cs if c in offboard or c in internal]
            never = [c for c in cs if c not in roll_codes]
            if off:
                item['why'] = 'off-boarded in Buildium (%s)' % ', '.join(off)
            elif never:
                item['why'] = 'not in the rent roll at all (%s)' % ', '.join(never)
            else:
                item['why'] = 'no pin on the map for %s' % ', '.join(cs)
                unmatched.append(item)
                continue
            turn_off.append(item)
            continue

        # Resolve the ad to specific doors: the crosswalk first, and only then
        # a guess from the unit id.
        mapped = []
        if uid in cw:
            want = {(x['scope'], x['unit']) for x in cw[uid]}
            mapped = [d for d in doors if door_key(*d) in want]
            item['via'] = 'crosswalk (confirmed)'
            for x in cw[uid]:
                cw_rows.append(x)
                cw_kept += 1
        if not mapped and unum:
            mapped = unit_hits(homes, doors, unum)
            item['via'] = 'unit id (proposed)' if mapped else ''
            prev = {(x['scope'], x['unit']): x for x in cw_all.get(uid, [])}
            for d in mapped:
                sc, un = door_key(*d)
                cw_rows.append(prev.get((sc, un)) or {
                    'ils_unit_id': uid, 'scope': sc, 'unit': un,
                    'source': 'proposed: matched on unit id',
                    'confirmed_on': '', 'note': title[:80]})
                cw_new += 1

        if not avail:
            item['why'] = ('every door at %s is leased past the %d-day window'
                           % (', '.join(pins[:2]) or ', '.join(known),
                              window))
            if gone:
                item['why'] += ' (and %s is off-boarded)' % ', '.join(gone)
            turn_off.append(item)
            continue

        if mapped:
            if not any(marketable(d) for d in mapped):
                soon = len(avail)
                item['why'] = ('the advertised door is taken; %d other door(s) '
                               'here are available' % soon)
                check_list.append(item)
                continue
        elif unum:
            item['why'] = ('unit "%s" is not a door id on the map; %d available '
                           'here' % (unum, len(avail)))
            check_list.append(item)
            continue
        live += 1

    # ---- the counterpart: vacancy with no live ad -------------------------
    advertised = {c for r in enabled for c in codes_in(r.get('Property Name'))}
    no_ad = []
    for i, h in enumerate(homes):
        hc = ([h['code']] if h.get('code') else []) + list(h.get('codes') or [])
        if any(c in advertised for c in hc):
            continue
        n = sum(1 for u in h['units'] if u.get('state') in ('vacant', 'expiring'))
        if n:
            no_ad.append({'home': h['name'], 'code': h.get('code') or '',
                          'available': n})
    no_ad.sort(key=lambda x: -x['available'])

    for lst in (turn_off, check_list):
        lst.sort(key=lambda x: (-x['leads30'], x['title']))

    ads = {
        'source': os.path.basename(unit_csv),
        'leads_source': os.path.basename(leads_csv) if leads_csv else '',
        'leads_asof': leads_dated, 'leads_window': LEAD_WINDOW,
        'leads_total': leads_total,
        'listings': len(rows), 'enabled': len(enabled), 'disabled': disabled,
        'window': window,
        'crosswalk_confirmed': cw_kept, 'crosswalk_proposed': cw_new,
        'states': audit.get('states') or {},
        'turn_off': turn_off, 'check': check_list, 'live': live,
        'unmatched': unmatched, 'no_ad': no_ad,
        'no_ad_doors': sum(x['available'] for x in no_ad),
        'generated': datetime.date.today().isoformat(),
    }
    if len(turn_off) + len(check_list) + live + len(unmatched) != len(enabled):
        sys.exit('REFUSE: %d turn-off + %d check + %d live + %d unmatched != %d '
                 'enabled listings' % (len(turn_off), len(check_list), live,
                                       len(unmatched), len(enabled)))
    blob['ads'] = ads
    if not check:
        write_crosswalk(cw_rows)

    print('listings %s — %d rows, %d enabled, %d disabled'
          % (ads['source'], ads['listings'], ads['enabled'], ads['disabled']))
    if leads_csv:
        print('leads %s — %d rows to %s (%d-day window)'
              % (ads['leads_source'], leads_total, leads_dated, LEAD_WINDOW))
    print('  marketing window: %d days   (%s)'
          % (window, ', '.join('%s %d' % kv for kv in sorted(
              (audit.get('states') or {}).items()))))
    print('  TURN OFF : %d  (still pulling %d leads in the last %dd)'
          % (len(turn_off), sum(i['leads30'] for i in turn_off), LEAD_WINDOW))
    print('  crosswalk: %d confirmed + %d proposed = %d rows -> %s'
          % (cw_kept, cw_new, len(cw_rows), os.path.basename(CROSSWALK)))
    print('  check    : %d' % len(check_list))
    print('  live/ok  : %d' % live)
    print('  unmatched: %d' % len(unmatched))
    print('  available doors with no live ad: %d across %d properties'
          % (ads['no_ad_doors'], len(no_ad)))
    print()
    for i in turn_off:
        print('  OFF  %-58s u=%-10s %3d leads  last %s  — %s'
              % (i['title'][:58], i['unit'][:10], i['leads30'],
                 i['last_lead'] or '—', i['why'][:52]))
    for i in check_list:
        print('  CHK  %-58s u=%-10s %3d leads  — %s'
              % (i['title'][:58], i['unit'][:10], i['leads30'], i['why'][:52]))
    for i in unmatched:
        print('  ?    %-58s — %s' % (i['title'][:58], i['why']))

    if check:
        print('\n--check: no files written')
        return
    out = json.dumps(blob, ensure_ascii=False, separators=(',', ':'))
    write_html(raw[:m.start(2)] + out + raw[m.end(2):])
    print('\nwrote %s' % os.path.normpath(HTML))


if __name__ == '__main__':
    main()
