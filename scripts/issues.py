#!/usr/bin/env python3
"""Preview/create/update issues from backlog.json; never silently discard edits."""
import argparse
import difflib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BEGIN = '<!-- diplomarbeit:backlog:start -->'
END = '<!-- diplomarbeit:backlog:end -->'
HISTORY = '## Früher abgehakte Kriterien (historisch)'


def normalise(body):
    return re.sub(r'(?m)^- \[[xX ]\]', '- [ ]', body.replace('\r\n', '\n')).strip()


def marked(body):
    return f'{BEGIN}\n{body.strip()}\n{END}'


def text_key(text):
    for _ in range(2):
        try:
            decoded = text.encode('cp1252').decode('utf-8')
        except (UnicodeError, LookupError):
            break
        if decoded == text:
            break
        text = decoded
    return text.strip()


def remove_old_section(body):
    lines = body.replace('\r\n', '\n').splitlines(keepends=True)
    kept, checks = [], []
    skipping = False
    for line in lines:
        if text_key(line) == HISTORY:
            skipping = True
            continue
        if skipping and (line.startswith('## ') or line.strip() == END):
            skipping = False
        if skipping:
            if not line.strip():
                continue
            match = re.fullmatch(r'- \[[xX]\] (.+)', line.rstrip('\n'))
            if not match:
                raise ValueError('Zusätzlicher Text im zu entfernenden Kriterienabschnitt; bitte manuell prüfen')
            checks.append(match.group(1))
        else:
            kept.append(line)
    return ''.join(kept), checks


def migrate_body(current, story):
    """Only replace known template text; preserve notes outside managed section."""
    current, saved_checks = remove_old_section(current)
    if BEGIN in current or END in current:
        if current.count(BEGIN) != 1 or current.count(END) != 1 or current.index(BEGIN) > current.index(END):
            raise ValueError('Ungültige Verwaltungsmarkierungen')
        prefix, rest = current.split(BEGIN, 1)
        active, suffix = rest.split(END, 1)
    else:
        prefix, active, suffix = '', current, ''
    known = [story['body'], story.get('previous_body')]
    if text_key(normalise(active)) not in [text_key(normalise(x)) for x in known if x]:
        raise ValueError('Beschreibung enthält eigene oder unbekannte Änderungen; Vorschlag manuell zusammenführen')
    checked = re.findall(r'(?m)^- \[[xX]\] (.+)$', active) + saved_checks
    checked = {text_key(line) for line in checked}
    target = story['body'].strip()
    target = '\n'.join('- [x] '+line[6:] if line.startswith('- [ ] ') and text_key(line[6:]) in checked
                       else line for line in target.splitlines())
    return prefix+marked(target)+suffix


def gh(*args):
    result = subprocess.run(['gh', *args], check=True, text=True, encoding='utf-8', capture_output=True)
    return result.stdout


def list_issues(repo):
    # Pagination avoids confusing a missing page with a missing issue.
    pages = json.loads(gh('api', '--paginate', '--slurp', f'repos/{repo}/issues?state=all&per_page=100'))
    return [row for page in pages for row in page if 'pull_request' not in row]


def select_issue(rows, story_id):
    matches = [r for r in rows if re.match(r'^'+re.escape(story_id)+r':(?:\s|$)', r['title'])]
    if len(matches) > 1:
        raise ValueError(f'{story_id}: Mehrere passende Issues; keine automatische Zuordnung')
    return matches[0] if matches else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['create', 'update'])
    parser.add_argument('repo', nargs='?', default='Cancani/diplomarbeit')
    parser.add_argument('--apply', action='store_true', help='Vorschläge auf GitHub anwenden')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repo):
        parser.error('Repository muss OWNER/REPO sein')
    stories = json.loads((ROOT/'scripts/backlog.json').read_text(encoding='utf-8-sig'))
    rows = list_issues(args.repo)
    folder = ROOT/'issue-preview'/args.repo.replace('/', '_')/args.mode
    folder.mkdir(parents=True, exist_ok=True)
    unresolved = 0
    changes = 0
    for story in stories:
        sid = story['id']
        try:
            issue = select_issue(rows, sid)
        except ValueError as error:
            print(error); unresolved += 1; continue
        if args.mode == 'create':
            if issue:
                print(f'{sid}: vorhanden #{issue["number"]}'); continue
            body = marked(story['body'])
        else:
            if issue is None:
                print(f'{sid}: fehlt, mit create anlegen'); continue
            try:
                body = migrate_body(issue.get('body') or '', story)
            except ValueError as error:
                (folder/f'{sid}-vorschlag.md').write_text(marked(story['body'])+'\n', encoding='utf-8')
                print(f'{sid}: {error}'); unresolved += 1; continue
        path = folder/f'{sid}.md'
        path.write_text(body+'\n', encoding='utf-8')
        before = issue.get('body') or '' if issue else ''
        diff = ''.join(difflib.unified_diff(before.splitlines(True), body.splitlines(True), fromfile='GitHub', tofile='Vorschlag'))
        (folder/f'{sid}.diff').write_text(diff, encoding='utf-8')
        print(f'{sid}: {"anlegen" if not issue else "prüfen"}, Sprint {story["sprint"]}, {story["points"]} SP, {path.relative_to(ROOT)}')
        if not args.apply:
            continue
        if issue and issue['state'] == 'closed':
            print(f'{sid}: geschlossen, keine automatische Änderung'); continue
        if issue:
            # Read again immediately before writing; refuse observed concurrent edits.
            fresh = json.loads(gh('api', f'repos/{args.repo}/issues/{issue["number"]}'))
            fields = ('body', 'title', 'state', 'updated_at')
            if any(fresh.get(k) != issue.get(k) for k in fields):
                print(f'{sid}: zwischenzeitlich geändert, übersprungen'); unresolved += 1; continue
            command = ['issue', 'edit', str(issue['number']), '--repo', args.repo]
        else:
            command = ['issue', 'create', '--repo', args.repo]
        command += ['--title', story['title'], '--body-file', str(path), '--milestone', f'Sprint {story["sprint"]}']
        labels = ','.join(['story', story['epic'], story['priority']])
        command += ['--add-label' if issue else '--label', labels]
        if issue:
            current_labels = {x['name'] for x in issue.get('labels', [])}
            remove = sorted(current_labels & {'must','should','could','wont'} - {story['priority']})
            if remove: command += ['--remove-label', ','.join(remove)]
        gh(*command)
        changes += 1
    print(f'{changes} GitHub-Änderungen, {unresolved} manuell zu prüfende Konflikte. Project-Felder separat pflegen.')
    return 2 if unresolved else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as error:
        # Avoid echoing server responses that may include private issue text.
        print(f'GitHub-Abfrage oder lokaler Aufruf fehlgeschlagen: {type(error).__name__}', file=sys.stderr)
        sys.exit(1)
