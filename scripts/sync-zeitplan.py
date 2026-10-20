#!/usr/bin/env python3
"""Nur die Datumsfelder des bestehenden Project Boards abgleichen."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('project_sync', ROOT/'scripts/sync-project.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

ITEM_PART = ('id isArchived content{... on Issue{number title repository{nameWithOwner}}}'
             'fieldValues(first:100){nodes{... on ProjectV2ItemFieldDateValue{date '
             'field{... on ProjectV2Field{id name dataType}}}}}')


def date_fields(fields):
    result = {}
    for name, aliases in [('Start date', ['Startdatum']),
                          ('Target date', ['End date', 'Enddatum', 'Zieldatum'])]:
        names = {v.casefold() for v in [name] + aliases}
        matches = [f for f in fields if f['name'].casefold() in names]
        if len(matches) != 1 or matches[0]['dataType'] != 'DATE':
            raise ValueError(f'Datumsfeld {name} fehlt oder ist nicht eindeutig')
        result[name] = matches[0]['id']
    return result


def changes_for(repo, stories, items, fields):
    by_story = {}
    for item in items:
        content = item.get('content') or {}
        if content.get('repository', {}).get('nameWithOwner', '').casefold() != repo.casefold():
            continue
        match = re.match(r'^(US\d+):', content.get('title', ''))
        if not match:
            continue
        sid = match[1]
        if sid in by_story:
            raise ValueError(f'Doppelter Project-Eintrag für {sid}')
        by_story[sid] = item
    changes = []
    for story in stories:
        start, end = sync.plan_dates(story)
        item = by_story.get(story['id'])
        if not item:
            if start is None and end is None:
                continue
            raise ValueError(f'{story["id"]} fehlt im Project Board')
        if item.get('isArchived'):
            raise ValueError(f'{story["id"]} ist archiviert')
        current = sync.item_values(item)
        for name, target in [('Start date', start), ('Target date', end)]:
            field = fields[name]
            old = current.get(field, {}).get('date')
            if old != target:
                changes.append(dict(story=story['id'], itemId=item['id'], fieldId=field,
                                    field=name, before=old, after=target))
    return changes


def apply_changes(project_id, changes):
    fresh = {i['id']: sync.item_values(i) for i in sync.connection(project_id, 'items', ITEM_PART)}
    for change in changes:
        actual = fresh.get(change['itemId'], {}).get(change['fieldId'], {}).get('date')
        if actual != change['before']:
            raise ValueError(f'Zwischenzeitliche Datumsänderung bei {change["story"]}; erneut prüfen')
    for change in changes:
        payload = dict(projectId=project_id, itemId=change['itemId'], fieldId=change['fieldId'])
        if change['after'] is None:
            sync.mutation('clearProjectV2ItemFieldValue', 'ClearProjectV2ItemFieldValueInput',
                          payload, 'projectV2Item{id}')
        else:
            payload['value'] = {'date': change['after']}
            sync.mutation('updateProjectV2ItemFieldValue', 'UpdateProjectV2ItemFieldValueInput',
                          payload, 'projectV2Item{id}')
    checked = {i['id']: sync.item_values(i) for i in sync.connection(project_id, 'items', ITEM_PART)}
    for change in changes:
        actual = checked.get(change['itemId'], {}).get(change['fieldId'], {}).get('date')
        if actual != change['after']:
            raise RuntimeError(f'Datumsänderung bei {change["story"]} nicht bestätigt')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', nargs='?', default='Cancani/diplomarbeit')
    parser.add_argument('--project', type=int, default=7)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repo):
        parser.error('Repository muss OWNER/REPO sein')
    stories = json.loads((ROOT/'scripts/backlog.json').read_text(encoding='utf-8-sig'))
    project = sync.choose_project(args.repo, args.project)
    fields = date_fields(sync.connection(project['id'], 'fields', sync.FIELD_PART))
    items = sync.connection(project['id'], 'items', ITEM_PART)
    changes = changes_for(args.repo, stories, items, fields)
    folder = ROOT/'issue-preview'/args.repo.replace('/', '_')/'zeitplan'
    folder.mkdir(parents=True, exist_ok=True)
    (folder/'aenderungen.json').write_text(json.dumps(changes, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    for c in changes:
        print(f'{c["story"]}: {c["field"]}: {c["before"] or "leer"} -> {c["after"] or "leer"}')
    if args.apply and changes:
        apply_changes(project['id'], changes)
    print(f'{"Angewendet und nachkontrolliert" if args.apply else "Vorschau, keine Änderungen"}: {len(changes)} Datumswerte.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, KeyError, OSError) as error:
        print(f'Abgebrochen: {error}', file=sys.stderr)
        sys.exit(1)
