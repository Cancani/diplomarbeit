import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
spec = importlib.util.spec_from_file_location('project_sync', ROOT/'scripts/sync-project.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)
issues = sync.issues


class ProjectTests(unittest.TestCase):
    def test_old_section_restores_matching_checks_only(self):
        body = '## Ready\n\n- [ ] Nutzen und Ziel sind formuliert\n- [ ] Akzeptanzkriterien sind prüfbar\n- [ ] Neues Kriterium'
        current = issues.marked(body+'\n\n'+issues.HISTORY+'\n\n- [x] Nutzen und Ziel sind formuliert\n- [x] Akzeptanzkriterien sind prÃ¼fbar\n- [x] Weggefallenes Kriterium')
        result = issues.migrate_body(current, {'body': body})
        self.assertNotIn(issues.HISTORY, result)
        self.assertIn('- [x] Akzeptanzkriterien sind prüfbar', result)
        self.assertIn('- [ ] Neues Kriterium', result)
        self.assertNotIn('Weggefallenes', result)
        self.assertEqual(issues.migrate_body(result, {'body': body}), result)

    def test_unknown_note_in_old_section_is_not_discarded(self):
        with self.assertRaises(ValueError):
            issues.remove_old_section(issues.HISTORY+'\nEigene Notiz')

    def test_dates_and_weekly_report(self):
        for n, dates in sync.SPRINTS.items():
            self.assertEqual(sync.plan_dates({'id': 'US17', 'sprint': n}), dates)
        self.assertEqual(sync.plan_dates({'id': 'US05', 'sprint': 1}), ('2026-09-14', '2026-12-18'))

    def test_complete_only_reviewed_stories_and_keep_notes(self):
        body = '## Kriterien\n\n- [ ] erledigt'
        stories = [dict(id=sid, body=body) for sid in ['US01', 'US04', 'US11']]
        rows = [dict(number=i, title=s['id']+': Test', body=issues.marked(body)+'\nNotiz: - [ ] separat',
                     state='open') for i, s in enumerate(stories, 1)]
        with tempfile.TemporaryDirectory() as temp:
            plans = sync.prepare(stories, rows, Path(temp), True)
        self.assertEqual([p['done'] for p in plans], [True, False, False])
        self.assertIn('- [x] erledigt', plans[0]['body'])
        self.assertIn('Notiz: - [ ] separat', plans[0]['body'])
        self.assertIn('- [ ] erledigt', plans[1]['body'])

    def test_preview_cannot_write_and_live_is_idempotent(self):
        fields = {}
        for name, typ, choices in [('Story Points','NUMBER',[]), ('Start date','DATE',[]),
                                   ('Target date','DATE',[]), ('Sprint','TEXT',[]), ('Epic','TEXT',[]),
                                   ('Priority','TEXT',[]), ('Status','SINGLE_SELECT',['Backlog','In Progress','Done'])]:
            fields[name] = dict(id=name, name=name, dataType=typ, options=[dict(id=o,name=o) for o in choices])
        story = dict(id='US01', sprint=1, points=2, epic='E1', priority='must')
        issue = dict(node_id='issue', state='open')
        item = dict(id='item', fieldValues={'nodes': []})
        with patch.object(sync, 'mutation') as write:
            sync.sync_item('project', fields, item, issue, story, True, False)
            write.assert_not_called()
            sync.sync_item('project', fields, item, issue, story, True, True)
            self.assertEqual(write.call_count, 7)
            nodes = []
            for call in write.call_args_list:
                payload = call.args[2]
                value = dict(payload['value'])
                if 'singleSelectOptionId' in value:
                    value['optionId'] = value.pop('singleSelectOptionId')
                nodes.append(dict(value, field={'id': payload['fieldId']}))
            write.reset_mock()
            sync.sync_item('project', fields, dict(item, fieldValues={'nodes':nodes}), issue, story, True, True)
            write.assert_not_called()

    def test_closed_as_not_planned_is_not_completed(self):
        story = dict(id='US01', body='- [ ] a')
        row = dict(title='US01: Test', body='- [ ] a', state='closed', state_reason='not_planned')
        with tempfile.TemporaryDirectory() as temp, self.assertRaises(ValueError):
            sync.prepare([story], [row], Path(temp), True)

    def test_partial_or_changed_backlog_is_rejected(self):
        story = dict(body='- [ ] a', previous_body='- [ ] old')
        with self.assertRaises(ValueError):
            issues.migrate_body(issues.marked('- [ ] a\n- [ ] Eigene Ergänzung'), story)

    def test_iteration_dates_must_match_plan(self):
        field = dict(name='Sprint', dataType='ITERATION', configuration=dict(
            iterations=[dict(id='s1', title='Sprint 1', startDate='2026-09-14', duration=35)], completedIterations=[]))
        self.assertEqual(sync.field_value(field, 'Sprint 1'), {'iterationId':'s1'})
        field['configuration']['iterations'][0]['duration'] = 14
        with self.assertRaises(ValueError):
            sync.field_value(field, 'Sprint 1')

    def test_single_select_matching_does_not_confuse_epics(self):
        options = [dict(id='e10', name='E10 Betrieb'), dict(id='e1', name='E1 Initialisierung')]
        self.assertEqual(sync.option_match(options, 'E1')['id'], 'e1')

    def test_existing_option_ids_are_preserved(self):
        field = dict(id='epic', name='Epic', dataType='SINGLE_SELECT',
                     options=[dict(id='old-e1', name='E1', color='BLUE', description='Bestehend')])
        calls = []
        def fake_mutation(name, typename, payload, result):
            calls.append((name, payload))
            if name == 'createProjectV2Field':
                return {'projectV2Field': dict(id=payload['name'], name=payload['name'],
                        dataType=payload['dataType'], options=[dict(o, id=o['name']) for o in payload.get('singleSelectOptions',[])])}
            return {}
        updated = dict(field, options=field['options']+[dict(id=f'e{i}',name=f'E{i}') for i in range(2,12)])
        with patch.object(sync, 'mutation', side_effect=fake_mutation), patch.object(sync, 'connection', return_value=[updated]):
            sync.ensure_fields('project', [field], True, [])
        updates = [p for n,p in calls if n == 'updateProjectV2Field']
        self.assertEqual(updates[0]['singleSelectOptions'][0]['id'], 'old-e1')

    def test_connection_reads_all_pages(self):
        pages = [{'node':{'items':{'nodes':[{'id':'1'}], 'pageInfo':{'hasNextPage':True,'endCursor':'next'}}}},
                 {'node':{'items':{'nodes':[{'id':'2'}], 'pageInfo':{'hasNextPage':False,'endCursor':'end'}}}}]
        with patch.object(sync, 'gql', side_effect=pages) as read:
            self.assertEqual(sync.connection('p','items','id'), [{'id':'1'},{'id':'2'}])
            self.assertEqual(read.call_args.kwargs['cursor'], 'next')

class EndToEndTests(unittest.TestCase):
    def test_full_preview_apply_repeat_and_concurrent_edit(self):
        from copy import deepcopy
        import io
        stories = json.loads((ROOT/'scripts/backlog.json').read_text(encoding='utf-8'))
        rows = {i: dict(number=i, node_id='node'+str(i), title=s['title'],
                       body=issues.marked(s['body']), state='open', state_reason=None,
                       updated_at='v0', labels=[], milestone=None) for i,s in enumerate(stories, 1)}
        rows[99] = dict(number=99,node_id='node99',title='US06: Kickoff mit den Experten',body=issues.marked(sync.CANCELLED['body']),state='open',state_reason=None,updated_at='v0',labels=[],milestone=None)
        pid = 'project'
        fields = []
        sync.ensure_fields(pid, fields, False, [])
        specs = [('Story Points','NUMBER',[]),('Start date','DATE',[]),('Target date','DATE',[]),
                 ('Sprint','SINGLE_SELECT',[f'Sprint {i}' for i in range(1,4)]),
                 ('Epic','SINGLE_SELECT',[f'E{i}' for i in range(1,12)]),
                 ('Priority','SINGLE_SELECT',['must','should','could','wont']),
                 ('Status','SINGLE_SELECT',['Backlog','Ready','In Progress','Done'])]
        fields = [dict(id=n,name=n,dataType=t,options=[dict(id=o,name=o,color='BLUE',description='') for o in opts])
                  for n,t,opts in specs]
        milestones = [dict(number=i,title=f'Sprint {i}',due_on=sync.SPRINTS[i][1]+'T23:59:59Z') for i in range(1,4)]
        labels = [dict(name=n) for n in {'story','must','should','could','wont'} | {f'E{i}' for i in range(1,12)}]
        items, writes = {'99':dict(id='99',isArchived=False,content=dict(number=99,repository={'nameWithOwner':'test/repo'}),fieldValues={'nodes':[]})}, []
        def fake_api(path, method='GET', payload=None):
            n = int(path.rsplit('/',1)[1])
            if method == 'GET':
                return deepcopy(rows[n])
            writes.append((path,payload))
            update = deepcopy(payload)
            if 'labels' in update:
                update['labels'] = [dict(name=x) for x in update['labels']]
            if 'milestone' in update:
                update['milestone'] = dict(number=update['milestone']) if update['milestone'] is not None else None
            rows[n].update(update)
            rows[n]['updated_at'] += 'x'
            return deepcopy(rows[n])
        def fake_connection(project, name, fragment):
            if name == 'fields': return deepcopy(fields)
            if name == 'views' or name == 'workflows': return []
            return deepcopy(list(items.values()))
        def fake_mutation(name, typename, payload, result):
            writes.append((name,deepcopy(payload)))
            if name == 'deleteProjectV2Item':
                items.pop(payload['itemId'])
                return {'deletedItemId':payload['itemId']}
            if name == 'addProjectV2ItemById':
                n = int(payload['contentId'][4:])
                item = dict(id=str(n),isArchived=False,content=dict(number=n,repository={'nameWithOwner':'test/repo'}),
                            fieldValues={'nodes':[]})
                items[str(n)] = item
                return {'item':deepcopy(item)}
            if name == 'updateProjectV2ItemFieldValue':
                item = items[payload['itemId']]
                nodes = item['fieldValues']['nodes']
                nodes[:] = [v for v in nodes if v['field']['id'] != payload['fieldId']]
                value = dict(payload['value'])
                if 'singleSelectOptionId' in value: value['optionId'] = value.pop('singleSelectOptionId')
                nodes.append(dict(value,field={'id':payload['fieldId']}))
                return {'projectV2Item':{'id':item['id']}}
            self.fail('Unexpected mutation '+name)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'scripts').mkdir()
            (root/'scripts/backlog.json').write_text(json.dumps(stories),encoding='utf-8')
            with patch.object(sync,'ROOT',root), patch.object(sync,'choose_project',return_value=dict(id=pid,title='Board',url='url',public=True)), \
                 patch.object(issues,'list_issues',side_effect=lambda r:deepcopy(list(rows.values()))), \
                 patch.object(sync,'connection',side_effect=fake_connection), patch.object(sync,'api',side_effect=fake_api), \
                 patch.object(sync,'rest_rows',side_effect=lambda p:deepcopy(milestones if '/milestones?' in p else labels)), \
                 patch.object(sync,'mutation',side_effect=fake_mutation), patch.object(sync,'gql',return_value={'__type':{'fields':[]}}), \
                 patch('sys.stdout',new=io.StringIO()):
                with patch.object(sys,'argv',['sync-project.py','test/repo','--complete-reviewed']):
                    self.assertEqual(sync.main(),0)
                    self.assertEqual(writes,[])
                with patch.object(sys,'argv',['sync-project.py','test/repo','--complete-reviewed','--apply']):
                    self.assertEqual(sync.main(),0)
                    self.assertEqual(len(items),38)
                    closed = {r['title'].split(':')[0] for r in rows.values() if r['state']=='closed' and r['state_reason']=='completed'}
                    self.assertEqual(closed,set(sync.DONE))
                    self.assertEqual(rows[99]['state_reason'],'not_planned')
                    self.assertNotIn('99',items)
                    for r in rows.values():
                        if r['state']=='closed': self.assertNotIn('- [ ]',r['body'])
                    writes.clear()
                    self.assertEqual(sync.main(),0)
                    self.assertEqual(writes,[])
                    base = fake_api
                    def edited(path, method='GET', payload=None):
                        r = base(path, method, payload)
                        if method=='GET': r['updated_at'] += 'concurrent'
                        return r
                    with patch.object(sync,'api',side_effect=edited), self.assertRaises(ValueError):
                        sync.main()
                    self.assertEqual(writes,[])


class ConflictTests(unittest.TestCase):
    def test_all_conflicts_are_identified_and_exported(self):
        stories = [dict(id=sid, body='- [ ] Vorgabe') for sid in ['US01','US04']]
        rows = [dict(number=n,title=s['id']+': Test',body='Eigene Ergänzung') for n,s in enumerate(stories,1)]
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'2 Issue-Konflikte'):
                sync.prepare(stories,rows,Path(tmp),False)
            exported = json.loads((Path(tmp)/'konflikte.json').read_text(encoding='utf-8'))
            self.assertEqual([v['issue'] for v in exported],[1,2])
            self.assertEqual(exported[0]['current_body'],'Eigene Ergänzung')


if __name__ == '__main__':
    unittest.main()
