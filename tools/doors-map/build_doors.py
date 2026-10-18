#!/usr/bin/env python3
"""Build doors.html: the root offsite map with NO vacancy/lease/expiry data —
door counts, measured drive times and Google directions instead.

Inputs (both in the repo): index.html (map shell, buildings, pods, SFH pins)
and elise.html (measured drive-minute matrix, 2026-09-23).
Run from the repo root:  python3 tools/doors-map/build_doors.py
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
src = (ROOT / 'index.html').read_text()
eli = (ROOT / 'elise.html').read_text()

D = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', src, re.S).group(1))
E = json.loads(re.search(r'const DATA=(\{.*?\});\n', eli, re.S).group(1))

# Only what the doors map reads. Vacancy, occupancy, rent, turnover, expiries are NOT served.
KEEP_B = ['name', 'addr', 'city', 'lat', 'lng', 'pod', 'sfh', 'seg', 'leaseup', 'code',
          'units', 'dispUnits', 'phaseNote', 'rp', 'rpUnits']
bl = [{k: b[k] for k in KEEP_B if k in b and b[k] is not None} for b in D['buildings']]
pods = [{k: p[k] for k in ('id', 'name', 'metro', 'centroid') if k in p} for p in D['pods']]

codes = {str(b['code']) for b in bl if not b.get('sfh') and 'code' in b}
mins = {c: {o: m for o, m in row.items() if o in codes} for c, row in E['minutes'].items() if c in codes}
office = {b['code']: b['office_min'] for b in E['buildings'] if b['code'] in codes and b.get('office_min') is not None}
missing = sorted(b['name'] for b in bl if not b.get('sfh') and str(b.get('code')) not in mins)

out = {'buildings': bl, 'pods': pods, 'minutes': mins, 'office': office}
payload = json.dumps(out, separators=(',', ':'))
for bad in ('"vacant"', '"occ"', '"rent"', '"expM"', '"turnover"', '"comp"'):
    assert bad not in payload, bad

head_end = src.index('<script id="data" type="application/json">')
shell = src[:head_end]
shell = shell.replace('<title>ZEN Leasing — Offsite Presentation</title>', '<title>ZEN Pod Map — Doors &amp; Drive Times</title>')
shell = shell.replace('Division — Offsite', 'Pod map — doors &amp; drive times')
shell = shell.replace('>Doors &amp; Opportunity<', '>Doors &amp; Drive Times<')
shell = shell.replace('Where the leasable doors are — roving, not fixed seats', 'Every building by pod — door counts, drive times between buildings, directions')
for a, b in (('DOORS TO LEASE', 'TOTAL DOORS'), ('CARDS / REGISTER', 'BUILDINGS'), ('<span>UNITS</span>', '<span>SFH HOMES</span>')):
    assert a in shell, a
    shell = shell.replace(a, b)
# Phone: the root deck pins the sidebar at 344px, leaving the map ~30px wide. Stack instead.
PHONE_CSS = ('<style>@media(max-width:760px){.view.map.on{flex-direction:column}'
             '#map{order:-1;flex:0 0 52vh;height:52vh;min-height:300px}'
             '.mside{width:100%;flex:none;height:auto;border-right:0}.mlist{overflow:visible}}</style>')
assert '</head>' in shell
shell = shell.replace('</head>', PHONE_CSS + '</head>', 1)
shell = shell.replace('click a building for leases + staffing', 'click a building for drive times + directions')
shell = shell.replace('Single-Family (261)', 'Single-Family (%d)' % sum(1 for b in bl if b.get('sfh')))
for bad in ('to lease', 'TO LEASE', 'vacan'):
    assert bad not in shell.split('<script>/* @preserve')[0], bad

JS = (ROOT / 'tools/doors-map/doors_render.js').read_text()
html = shell + '<script id="data" type="application/json">' + payload + '</script>\n<script>\n' + JS + '\n</script></body></html>\n'
(ROOT / 'doors.html').write_text(html)
print('doors.html', len(html), 'bytes ·', sum(1 for b in bl if not b.get('sfh')), 'buildings ·',
      len(mins), 'with drive times · no matrix:', missing)
