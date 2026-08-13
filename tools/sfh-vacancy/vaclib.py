import openpyxl, re, sys
from difflib import SequenceMatcher

# Buildium scope labels are hand-typed and contain real typos in the wild
# (OFFBAORDED, OFRFBOARDED). Match the WORD fuzzily instead of enumerating
# misspellings, so the next typo classifies correctly with no code change.
_OFF_WORDS = ('offboard', 'offboarded', 'offboarding')
_HARD_OFF = re.compile(r'do not use|terminat|\binactive\b', re.I)
INTERNAL_PAT = re.compile(r'ZEN\s*INTERNAL', re.I)

def offboard_hit(label):
    """Return the matched token if this label marks the scope/unit as
    offboarding, else None. Verified zero false positives against the
    full address vocabulary of the Aug-13 report."""
    if _HARD_OFF.search(label):
        return _HARD_OFF.search(label).group(0)
    for tok in re.findall(r"[A-Za-z']+", label.lower()):
        if len(tok) < 6:
            continue
        for t in _OFF_WORDS:
            if SequenceMatcher(None, tok, t).ratio() >= 0.82:
                return tok
    return None

def _s(c):
    return '' if c is None else str(c).strip()

def parse(path):
    """Parse a Buildium 'Vacant Units' export -> (records, meta).
    Header rows are detected by ROW SHAPE (col A populated, all others empty),
    never by name, so new/renamed properties parse without code changes."""
    ws = openpyxl.load_workbook(path, data_only=True)['Vacant Units']
    rows = [[_s(c) for c in r] for r in ws.iter_rows(values_only=True)]
    recs, cur, asof, stop = [], None, None, None
    for i, r in enumerate(rows, 1):
        a, rest = r[0], [x for x in r[1:] if x]
        low = a.lower()
        if i <= 2:
            for c in r:
                m = re.search(r'As of (\d{4}-\d{2}-\d{2})', c)
                if m: asof = m.group(1)
            continue
        if low.startswith('grand total'):
            stop = i; break
        if low.startswith('total for') or not a: continue
        if a == 'Unit' and r[1] == 'Vacated': continue
        if not rest:                      # scope header, by shape
            cur = a; continue
        if cur is None:
            print('WARN orphan row %d' % i, file=sys.stderr); continue
        recs.append({'row': i, 'scope': cur, 'unit': a,
                     'vacated': r[1][:10], 'available': r[2][:10],
                     'nextlease': r[3][:10], 'bedbath': r[4],
                     'sqft': r[5], 'rent': r[6]})
    if stop is None:
        raise SystemExit('REFUSE: no "Grand total" row found in %s' % path)

    # independent reconciliation against the report's own summary block
    declared = None
    for r in rows[stop:]:
        if r[0].startswith('Totals & Averages'):
            declared = int(r[1]); break
    for r in recs:
        m = re.match(r'^((?:SF|RP|MF)\s*\d+)\b', r['scope'])
        r['code'] = re.sub(r'\s+', '', m.group(1)) if m else None
        r['offboard'] = offboard_hit(r['scope']) is not None
        r['internal'] = bool(INTERNAL_PAT.search(r['scope']))
        r['key'] = (r['code'], norm_unit(r['unit']))
    return recs, {'asof': asof, 'stop': stop, 'declared': declared}

def norm_unit(u):
    """Unit ids carry house-number prefixes ('11204 - Bsmt') and annotations
    ('- OFF MARKET FIRE'). Reduce to a comparable token."""
    u = re.sub(r'\s*-\s*(OFF MARKET|DO NOT|FIRE|RENO).*$', '', u, flags=re.I)
    u = u.strip().lstrip('#').strip()
    m = re.match(r'^\d{4,6}\s*-\s*(.+)$', u)   # '11204 - Bsmt' -> 'Bsmt'
    if m: u = m.group(1).strip()
    return u.lower()
