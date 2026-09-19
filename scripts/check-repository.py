#!/usr/bin/env python3
"""Check local consistency and immutable evidence; no live infrastructure access."""
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
errors = []
def require(ok, message):
    if not ok: errors.append(message)

stories = json.loads((ROOT/'scripts/backlog.json').read_text())
require(len(stories) == 39, 'Expected 39 backlog stories')
require(len({s['id'] for s in stories}) == len(stories), 'Duplicate story IDs')
require(sum(s['points'] for s in stories) == 113, 'Backlog total must be 113 SP')
expected = {1:(17,40), 2:(9,35), 3:(13,38)}
main = (ROOT/'docs/dokumentation.md').read_text()
for sprint, (count, points) in expected.items():
    group = [s for s in stories if s['sprint'] == sprint]
    require((len(group),sum(s['points'] for s in group)) == (count,points), f'Sprint {sprint} mismatch')
for story in stories:
    row = f'| {story["id"]} | {story["title"].split(": ",1)[1]} | {story["epic"]} | {story["points"]} | {story["priority"].capitalize()} |'
    require(row in main, f'Main document backlog differs: {story["id"]}')
    require(f'| Story Points | {story["points"]} |' in story['body'], f'Issue points differ: {story["id"]}')
    require(f'| Sprint | {story["sprint"]} |' in story['body'], f'Issue sprint differs: {story["id"]}')
for line in (ROOT/'docs/nachweise/SHA256SUMS').read_text().splitlines():
    digest, name = line.split('  ',1)
    path = ROOT/name
    require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == digest, f'Historical evidence changed: {name}')
for path in [ROOT/'README.md', *ROOT.joinpath('docs').rglob('*.md')]:
    content = path.read_text()
    # Inline local links, excluding fenced code and external URLs; anchors checked by MkDocs.
    content = re.sub(r'```.*?```', '', content, flags=re.S)
    for target in re.findall(r'\]\(([^)]+)\)', content):
        target = target.split(' "',1)[0]
        parsed = urlsplit(target)
        if parsed.scheme or target.startswith(('#','/')): continue
        if parsed.path:
            require((path.parent/unquote(parsed.path)).is_file(), f'Broken link in {path.relative_to(ROOT)}: {target}')
require('Platzhalter Abbildung' not in main, 'Obsolete figure placeholder')
require(not re.search(r'(?m)^- \[[ xX]\]',main), 'Main document contains checkboxes')
require(not re.search('[ß–—]',main), 'Main document contains excluded typography')
mermaids = re.findall(r'^```mermaid\n(.+?)^```', main, re.M | re.S)
require(len(mermaids) >= 2, 'Mermaid diagrams missing')
require('<svg' not in main, 'Inline SVG diagram found')
require(not list(ROOT.joinpath('docs').rglob('*.svg')), 'Separate SVG diagram found')
require((ROOT/'.github/pull_request_template.md').is_file(), 'PR template missing')
if errors:
    print('\n'.join(errors),file=sys.stderr);sys.exit(1)
print(f'OK: {len(stories)} stories, 113 SP, local links, Mermaid blocks and immutable evidence verified.')
