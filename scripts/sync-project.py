#!/usr/bin/env python3
"""Issues und Project Board abgleichen. Ohne --apply werden nur Vorschläge erstellt."""
import argparse
from datetime import date, timedelta
import difflib
import json
from pathlib import Path
import re
import subprocess
import sys

import issues

ROOT = Path(__file__).resolve().parents[1]
SPRINTS = {1: ('2026-09-14', '2026-10-18'), 2: ('2026-10-19', '2026-11-15'),
           3: ('2026-11-16', '2026-12-18')}
DONE = {
    'US01': 'ordner', 'US07': '32-ist-analyse-der-heutigen-bereitstellung',
    'US09': '34-messkonzept', 'US12': '313-vorgefundener-zustand-auf-dl380-01',
    'US13': '316-architekturentscheide-aus-der-erhebung',
}
FIELD_PART = '''... on ProjectV2Field {id name dataType}
... on ProjectV2SingleSelectField {id name dataType options {id name color description}}
... on ProjectV2IterationField {id name dataType configuration {
iterations {id title startDate duration} completedIterations {id title startDate duration}}}'''


def api(path, method='GET', payload=None):
    command = ['gh', 'api', path, '--method', method]
    if payload is not None:
        command += ['--input', '-']
    result = subprocess.run(command, input=json.dumps(payload, ensure_ascii=False) if payload is not None else None,
                            text=True, encoding='utf-8', capture_output=True)
    if result.returncode:
        raise RuntimeError(f'GitHub {method} {path}: {result.stderr.strip()}')
    return json.loads(result.stdout) if result.stdout.strip() else {}


def gql(query, **variables):
    response = api('graphql', 'POST', dict(query=query, variables=variables))
    if response.get('errors'):
        raise RuntimeError('; '.join(e['message'] for e in response['errors']))
    return response['data']


def mutation(name, typename, value, result):
    return gql('mutation($input:'+typename+'!){'+name+'(input:$input){'+result+'}}', input=value)[name]


def rest_rows(path):
    return [row for page in json.loads(issues.gh('api', '--paginate', '--slurp', path)) for row in page]


def connection(project_id, name, fragment):
    rows, cursor = [], None
    while True:
        data = gql('query($id:ID!,$cursor:String){node(id:$id){... on ProjectV2 {'
                   + name + '(first:100,after:$cursor){nodes{' + fragment + '}'
                   + 'pageInfo{hasNextPage endCursor}}}}}', id=project_id, cursor=cursor)['node'][name]
        rows.extend(x for x in data['nodes'] if x)
        if not data['pageInfo']['hasNextPage']:
            return rows
        cursor = data['pageInfo']['endCursor']


def choose_project(repo, number):
    owner = api(f'repos/{repo}')['owner']
    kind = 'organization' if owner['type'] == 'Organization' else 'user'
    rows, cursor = [], None
    while True:
        data = gql('query($login:String!,$cursor:String){' + kind + '(login:$login){'
                   'projectsV2(first:100,after:$cursor){nodes{id number title public closed url}'
                   'pageInfo{hasNextPage endCursor}}}}', login=owner['login'], cursor=cursor)[kind]['projectsV2']
        rows.extend(data['nodes'])
        if not data['pageInfo']['hasNextPage']:
            break
        cursor = data['pageInfo']['endCursor']
    matches = [p for p in rows if p['number'] == number] if number else [
        p for p in rows if p['title'] == 'Project Board Diplomarbeit Efekan' and not p['closed']]
    if len(matches) != 1:
        choices = ', '.join(f'{p["number"]}: {p["title"]}' for p in rows)
        raise ValueError(f'Project nicht eindeutig. --project NUMMER angeben. Verfügbar: {choices}')
    return matches[0]


def option_match(options, desired):
    exact = [o for o in options if o['name'].casefold() == desired.casefold()]
    if len(exact) == 1:
        return exact[0]
    prefixed = [o for o in options if o['name'].casefold().startswith(desired.casefold() + ' ')]
    if len(prefixed) == 1:
        return prefixed[0]
    if len(exact) > 1 or len(prefixed) > 1:
        raise ValueError(f'Mehrdeutige Auswahloption: {desired}')
    return None


def field_value(field, desired):
    dtype = field['dataType']
    if dtype == 'SINGLE_SELECT':
        option = option_match(field['options'], str(desired))
        if not option:
            raise ValueError(f'{field["name"]}: Option {desired} fehlt')
        return {'singleSelectOptionId': option['id']}
    if dtype == 'ITERATION':
        config = field['configuration']
        matches = [v for v in config['iterations'] + config['completedIterations'] if v['title'] == desired]
        if len(matches) != 1:
            raise ValueError(f'Sprint-Iteration {desired} fehlt oder ist doppelt')
        sprint = int(desired.split()[-1])
        iteration = matches[0]
        end = date.fromisoformat(iteration['startDate']) + timedelta(days=iteration['duration'] - 1)
        if (iteration['startDate'], end.isoformat()) != SPRINTS[sprint]:
            raise ValueError(f'{desired}: Iteration stimmt nicht mit den dokumentierten Sprintdaten überein')
        return {'iterationId': iteration['id']}
    return {dict(NUMBER='number', DATE='date', TEXT='text')[dtype]: desired}


def ensure_fields(pid, fields, apply, log):
    specs = [('Story Points', 'NUMBER', []), ('Start date', 'DATE', []), ('Target date', 'DATE', []),
             ('Sprint', 'SINGLE_SELECT', ['Sprint 1', 'Sprint 2', 'Sprint 3']),
             ('Epic', 'SINGLE_SELECT', [f'E{i}' for i in range(1, 12)]),
             ('Priority', 'SINGLE_SELECT', ['must', 'should', 'could', 'wont']),
             ('Status', 'SINGLE_SELECT', ['Backlog', 'Ready', 'In Progress', 'Done'])]
    aliases = {'Start date': ['Startdatum'], 'Target date': ['End date', 'Enddatum', 'Zieldatum'],
               'Story Points': ['Story points', 'SP']}
    result = {}
    for name, dtype, options in specs:
        names = {n.casefold() for n in [name] + aliases.get(name, [])}
        matches = [f for f in fields if f['name'].casefold() in names]
        if len(matches) > 1:
            raise ValueError(f'Mehrere passende Felder für {name}; bitte zuerst zusammenführen')
        field = matches[0] if matches else None
        if field is None:
            log.append(f'Feld anlegen: {name} ({dtype})')
            payload = dict(projectId=pid, name=name, dataType=dtype)
            if options:
                payload['singleSelectOptions'] = [dict(name=o, color='BLUE', description='') for o in options]
            if apply:
                field = mutation('createProjectV2Field', 'CreateProjectV2FieldInput', payload,
                                 'projectV2Field{' + FIELD_PART + '}')['projectV2Field']
            else:
                field = dict(id='preview-'+name, name=name, dataType=dtype,
                             options=[dict(id='preview-'+o, name=o) for o in options])
        allowed = {dtype}
        if name in ('Sprint', 'Epic', 'Priority'):
            allowed.add('TEXT')
        if name == 'Sprint':
            allowed.add('ITERATION')
        if field['dataType'] not in allowed:
            raise ValueError(f'{name}: Typ {field["dataType"]} passt nicht zu {dtype}; keine Feldlöschung')
        if field['dataType'] == 'SINGLE_SELECT':
            missing = [o for o in options if not option_match(field['options'], o)]
            if missing:
                log.append(f'{name}: Optionen ergänzen: {", ".join(missing)}')
                old = [{k: o[k] for k in ('id', 'name', 'color', 'description')} for o in field['options']]
                added = [dict(name=o, color='BLUE', description='') for o in missing]
                if apply:
                    mutation('updateProjectV2Field', 'UpdateProjectV2FieldInput',
                             dict(fieldId=field['id'], singleSelectOptions=old+added), 'projectV2Field{' + FIELD_PART + '}')
                    field = next(f for f in connection(pid, 'fields', FIELD_PART) if f['id'] == field['id'])
                else:
                    field = dict(field, options=field['options']+[dict(o, id='preview-'+o['name']) for o in added])
        if name == 'Sprint' and field['dataType'] == 'ITERATION':
            for sprint in SPRINTS:
                field_value(field, f'Sprint {sprint}')
        result[name] = field
    return result


def plan_dates(story):
    return (SPRINTS[1][0], SPRINTS[3][1]) if story['id'] == 'US05' else SPRINTS[story['sprint']]


def complete_body(body):
    prefix, managed = body.split(issues.BEGIN, 1)
    managed, suffix = managed.split(issues.END, 1)
    managed = re.sub(r'(?m)^- \[[ xX]\] ', '- [x] ', managed)
    return prefix + issues.BEGIN + managed + issues.END + suffix


def prepare(stories, rows, folder, complete, repo='Cancani/diplomarbeit'):
    plans = []
    for story in stories:
        issue = issues.select_issue(rows, story['id'])
        body = issues.migrate_body(issue.get('body') or '', story) if issue else issues.marked(story['body'])
        done = complete and story['id'] in DONE
        if done and issue is None:
            raise ValueError(f'{story["id"]}: Fertige Story fehlt auf GitHub; zuerst Zuordnung klären')
        if done and issue.get('state_reason') == 'not_planned':
            raise ValueError(f'{story["id"]}: Als nicht geplant geschlossen; Abschluss bitte prüfen')
        if done:
            body = complete_body(body)
            proof = f'[Nachweis in dokumentation.md](https://github.com/{repo}/blob/main/docs/dokumentation.md#{DONE[story["id"]]})'
            if proof not in body:
                body = body.rstrip() + '\n\n' + proof + '\n'
        path = folder / (story['id'] + '.md')
        path.write_text(body, encoding='utf-8')
        old = (issue.get('body') or '') if issue else ''
        (folder / (story['id'] + '.diff')).write_text(''.join(difflib.unified_diff(
            old.splitlines(True), body.splitlines(True), fromfile='GitHub', tofile='Vorschlag')), encoding='utf-8')
        plans.append(dict(story=story, issue=issue, body=body, done=done))
    return plans


def sync_milestones_labels(repo, apply, log, stories):
    milestones = rest_rows(f'repos/{repo}/milestones?state=all&per_page=100')
    result = {}
    for sprint, (start, end) in SPRINTS.items():
        title = f'Sprint {sprint}'
        matches = [m for m in milestones if m['title'] == title]
        if len(matches) > 1:
            raise ValueError(f'Doppelter Milestone {title}')
        current = matches[0] if matches else None
        payload = dict(title=title, due_on=end+'T23:59:59Z')
        if not current or (current.get('due_on') or '')[:10] != end:
            log.append(f'Milestone {title}: Fälligkeit {end}')
            if apply:
                current = api(f'repos/{repo}/milestones' + (f'/{current["number"]}' if current else ''),
                              'PATCH' if current else 'POST', payload)
        result[sprint] = current['number'] if current else 0
    labels = rest_rows(f'repos/{repo}/labels?per_page=100')
    required = {'story'} | {s['epic'] for s in stories} | {s['priority'] for s in stories}
    for name in sorted(required - {l['name'] for l in labels}):
        log.append(f'Label anlegen: {name}')
        if apply:
            api(f'repos/{repo}/labels', 'POST', dict(name=name, color='1d76db'))
    log.append(f'Labels vorhanden: {len(labels)}; erwartete Projektkonvention: 19 (zusätzliche Labels bleiben erhalten)')
    return result


def item_values(item):
    values = {}
    for v in item.get('fieldValues', {}).get('nodes', []):
        field = v.get('field', {})
        if not field.get('id'):
            continue
        for key in ('number', 'date', 'text', 'optionId', 'iterationId'):
            if key in v:
                values[field['id']] = {('singleSelectOptionId' if key == 'optionId' else key): v[key]}
    return values


def sync_item(pid, fields, item, issue, story, done, apply):
    if not item:
        if not apply:
            return
        item = mutation('addProjectV2ItemById', 'AddProjectV2ItemByIdInput',
                        dict(projectId=pid, contentId=issue['node_id']), 'item{id}')['item']
    if item.get('isArchived'):
        raise ValueError(f'{story["id"]}: Project-Eintrag ist archiviert; bitte gezielt wiederherstellen')
    start, end = plan_dates(story)
    desired = {'Story Points': story['points'], 'Sprint': f'Sprint {story["sprint"]}',
               'Epic': story['epic'], 'Priority': story['priority'], 'Start date': start, 'Target date': end}
    current = item_values(item)
    if done or (issue['state'] == 'closed' and issue.get('state_reason') == 'completed'):
        desired['Status'] = 'Done'
    elif issue['state'] == 'open' and fields['Status']['id'] not in current:
        desired['Status'] = 'Backlog'
    for name, value in desired.items():
        field = fields[name]
        target = field_value(field, value)
        if current.get(field['id']) != target and apply:
            mutation('updateProjectV2ItemFieldValue', 'UpdateProjectV2ItemFieldValueInput',
                     dict(projectId=pid, itemId=item['id'], fieldId=field['id'], value=target), 'projectV2Item{id}')


def sync_views(pid, fields, apply, log):
    views = connection(pid, 'views', 'id name layout filter fields(first:100){nodes{' + FIELD_PART + '}}')
    support = gql('{__type(name:"Mutation"){fields{name}}}')['__type']['fields']
    supported = {v['name'] for v in support}
    names = ['Title', 'Status', 'Sprint', 'Story Points', 'Priority', 'Epic', 'Start date', 'Target date']
    all_fields = connection(pid, 'fields', FIELD_PART) if apply else list(fields.values())
    visible = [f['id'] for name in names for f in all_fields if f['name'] == name or
               (name in fields and f['id'] == fields[name]['id'])]
    for name, layout, old_name in [('Arbeitsboard', 'BOARD_LAYOUT', 'View 1'),
                                   ('Zeitplan', 'ROADMAP_LAYOUT', 'View 2'),
                                   ('Sprintplanung', 'TABLE_LAYOUT', None)]:
        matches = [v for v in views if v['name'] == name]
        if not matches and old_name:
            matches = [v for v in views if v['name'] == old_name and v['layout'] == layout]
        if len(matches) > 1:
            raise ValueError(f'Mehrere Ansichten namens {name}')
        current = matches[0] if matches else None
        log.append(f'Ansicht: {name} ({layout})')
        if not {'createProjectV2View', 'updateProjectV2View'} <= supported:
            log.append('Ansichten-API nicht verfügbar: Namen und sichtbare Felder im Browser einstellen')
            continue
        if not apply:
            continue
        configuration = dict(visibleFieldIds=list(dict.fromkeys(visible)))
        if current:
            current_fields = [f['id'] for f in current['fields']['nodes']]
            if current['name'] != name or current['layout'] != layout or current_fields != configuration['visibleFieldIds']:
                mutation('updateProjectV2View', 'UpdateProjectV2ViewInput',
                         dict(viewId=current['id'], name=name, layout=layout, configuration=configuration), 'projectV2View{id}')
        else:
            mutation('createProjectV2View', 'CreateProjectV2ViewInput',
                     dict(projectId=pid, name=name, layout=layout, configuration=configuration), 'projectV2View{id}')
    log.append('Im Browser: Zeitplan > Date fields > Start date / Target date (bzw. vorhandene Datumsfelder).')
    log.append('Arbeitsboard nach Status gruppieren; Sprintplanung nach Sprint gruppieren und Story Points summieren.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', nargs='?', default='Cancani/diplomarbeit')
    parser.add_argument('--project', type=int, help='Project-Nummer aus der URL, falls der Name abweicht')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--complete-reviewed', action='store_true', help='US01, US07, US09, US12, US13 abhaken und schliessen')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repo):
        parser.error('Repository muss OWNER/REPO sein')
    stories = json.loads((ROOT/'scripts/backlog.json').read_text(encoding='utf-8-sig'))
    if len(stories) != 39 or len({s['id'] for s in stories}) != 39 or sum(s['points'] for s in stories) != 113:
        raise ValueError('Backlog weicht vom geprüften Stand mit 39 Stories und 113 SP ab')
    folder = ROOT/'issue-preview'/args.repo.replace('/', '_')/'sync'
    folder.mkdir(parents=True, exist_ok=True)
    rows = issues.list_issues(args.repo)
    plans = prepare(stories, rows, folder, args.complete_reviewed, args.repo)
    project = choose_project(args.repo, args.project)
    print(f'Project: {project["title"]} ({project["url"]})', flush=True)
    fields = connection(project['id'], 'fields', FIELD_PART)
    fragments = ['... on ProjectV2ItemField'+typ+'Value {'+value+' field{' + FIELD_PART + '}}'
                 for typ, value in [('Number', 'number'), ('Date', 'date'), ('Text', 'text'),
                                    ('SingleSelect', 'optionId'), ('Iteration', 'iterationId')]]
    items = connection(project['id'], 'items', 'id isArchived content{... on Issue{id number repository{nameWithOwner}}}'
                       'fieldValues(first:100){nodes{' + ' '.join(fragments) + '}}')
    item_map = {}
    for item in items:
        content = item.get('content') or {}
        if content.get('repository', {}).get('nameWithOwner', '').casefold() == args.repo.casefold():
            if content['number'] in item_map:
                raise ValueError('Doppelter Project-Eintrag für Issue '+str(content['number']))
            item_map[content['number']] = item
    log = [f'Project: {project["title"]}; öffentlich: {project["public"]}',
           '39 Stories, 113 SP: Sprint 1 = 40, Sprint 2 = 35, Sprint 3 = 38.',
           'Zeiträume sind Plantermine. US05 läuft bis 18.12.2026.']
    # Validate field compatibility and every issue before the first write.
    preview_fields = ensure_fields(project['id'], fields, False, log)
    for plan in plans:
        story, issue = plan['story'], plan['issue']
        item = item_map.get(issue['number']) if issue else None
        if item and item.get('isArchived'):
            raise ValueError(f'{story["id"]}: archivierter Project-Eintrag; keine automatische Änderung')
        if issue:
            sync_item(project['id'], preview_fields, item, issue, story, plan['done'], False)
    milestones = sync_milestones_labels(args.repo, False, log, stories)
    if args.apply:
        fields = ensure_fields(project['id'], fields, True, [])
        milestones = sync_milestones_labels(args.repo, True, [], stories)
    else:
        fields = preview_fields
    for plan in plans:
        story, issue, body, done = (plan[k] for k in ('story', 'issue', 'body', 'done'))
        sid = story['id']
        action = 'abhaken + Done + schliessen' if done else ('abgleichen' if issue else 'anlegen')
        start, end = plan_dates(story)
        line = f'{sid}: {action}; Sprint {story["sprint"]}; {story["points"]} SP; {start} bis {end}'
        print(line, flush=True)
        log.append(line)
        if not args.apply:
            continue
        endpoint = f'repos/{args.repo}/issues'
        if issue:
            fresh = api(endpoint+f'/{issue["number"]}')
            if any(fresh.get(k) != issue.get(k) for k in ('body', 'title', 'state', 'updated_at')):
                raise ValueError(f'{sid}: Zwischenzeitliche Änderung; erneut starten')
            labels = {l['name'] for l in issue.get('labels', [])}
            labels -= {'must', 'should', 'could', 'wont'} - {story['priority']}
            labels -= {f'E{i}' for i in range(1, 12)} - {story['epic']}
        else:
            labels = set()
        labels |= {'story', story['epic'], story['priority']}
        payload = dict(title=story['title'], body=body, labels=sorted(labels), milestone=milestones[story['sprint']])
        changed = not issue or any([issue['title'] != payload['title'], (issue.get('body') or '') != body,
                     {l['name'] for l in issue.get('labels', [])} != labels,
                     (issue.get('milestone') or {}).get('number') != payload['milestone']])
        if changed:
            # Mark the board criterion only after the board update succeeds.
            first_body = body.replace('- [x] Issue im Board auf Done', '- [ ] Issue im Board auf Done') if done else body
            payload['body'] = first_body
            issue = api(endpoint+(f'/{issue["number"]}' if issue else ''), 'PATCH' if issue else 'POST', payload)
        sync_item(project['id'], fields, item_map.get(issue['number']), issue, story, done, True)
        if done and ((issue.get('body') or '') != body or issue['state'] != 'closed'):
            fresh = api(endpoint+f'/{issue["number"]}')
            if any(fresh.get(k) != issue.get(k) for k in ('body', 'title', 'state', 'updated_at')):
                raise ValueError(f'{sid}: Zwischenzeitliche Änderung vor Abschluss; erneut starten')
            api(endpoint+f'/{issue["number"]}', 'PATCH', dict(body=body, state='closed', state_reason='completed'))
    sync_views(project['id'], fields, args.apply, log)
    workflows = connection(project['id'], 'workflows', 'name enabled')
    log += [f'Workflow: {w["name"]}; aktiv: {w["enabled"]}' for w in workflows]
    log.append('Workflow-Bedingungen sowie Gruppierung, Summen und Roadmap-Datumszuordnung im Browser prüfen.')
    log.append('Abschlussliste: US01, US07, US09, US12, US13. US04/US11 und alle weiteren offenen Stories bleiben offen.')
    (folder/'pruefung.txt').write_text('\n'.join(log)+'\n', encoding='utf-8')
    print('\n'.join(log[:3] + log[-9:]))
    print(f'{"Angewendet" if args.apply else "Vorschau, keine GitHub-Änderungen"}. Details: {folder/"pruefung.txt"}')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (RuntimeError, ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print(f'Abgebrochen: {error}', file=sys.stderr)
        print('Bei fehlenden Project-Rechten: gh auth refresh -s project', file=sys.stderr)
        sys.exit(1)
