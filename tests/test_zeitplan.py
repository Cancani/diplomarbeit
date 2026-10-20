import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
spec = importlib.util.spec_from_file_location('dates_only', ROOT/'scripts/sync-zeitplan.py')
dates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dates)


def item(start='2026-09-14', end='2026-10-18'):
    nodes = []
    for field, value in [('start', start), ('end', end)]:
        if value is not None:
            nodes.append(dict(date=value, field=dict(id=field)))
    return dict(id='item', isArchived=False,
                content=dict(title='US19: CLI', repository=dict(nameWithOwner='test/repo')),
                fieldValues=dict(nodes=nodes))


class ScheduleTests(unittest.TestCase):
    def test_schedule_covers_backlog_and_rejects_missing_story(self):
        backlog = json.loads((ROOT/'scripts/backlog.json').read_text(encoding='utf-8'))
        plan = json.loads((ROOT/'scripts/zeitplan.json').read_text(encoding='utf-8'))
        self.assertEqual(set(plan['stories']), {s['id'] for s in backlog})
        with self.assertRaises(ValueError):
            dates.sync.plan_dates({'id': 'US999'})

    def test_only_dates_are_changed_and_repeat_is_empty(self):
        fields = {'Start date': 'start', 'Target date': 'end'}
        story = {'id': 'US19'}
        changes = dates.changes_for('test/repo', [story], [item()], fields)
        self.assertEqual([c['after'] for c in changes], ['2026-10-26', '2026-10-28'])
        self.assertEqual(dates.changes_for('test/repo', [story], [item('2026-10-26', '2026-10-28')], fields), [])
        with patch.object(dates.sync, 'connection', side_effect=[[item()], [item('2026-10-26', '2026-10-28')]]), \
             patch.object(dates.sync, 'mutation') as write:
            dates.apply_changes('p', changes)
        self.assertEqual(write.call_count, 2)
        self.assertTrue(all(c.args[0]=='updateProjectV2ItemFieldValue' for c in write.call_args_list))

    def test_concurrent_date_change_blocks_every_write(self):
        changes = dates.changes_for('test/repo', [{'id': 'US19'}], [item()], {'Start date': 'start', 'Target date': 'end'})
        with patch.object(dates.sync, 'connection', return_value=[item('2026-10-01')]), \
             patch.object(dates.sync, 'mutation') as write, self.assertRaises(ValueError):
            dates.apply_changes('p', changes)
        write.assert_not_called()

    def test_cancelled_story_clears_dates_without_removing_item(self):
        row = item()
        row['content']['title'] = 'US05: Entfallen'
        changes = dates.changes_for('test/repo', [{'id': 'US05'}], [row], {'Start date': 'start', 'Target date': 'end'})
        self.assertEqual([c['after'] for c in changes], [None, None])
        cleared = item(None, None)
        with patch.object(dates.sync, 'connection', side_effect=[[row], [cleared]]), patch.object(dates.sync, 'mutation') as write:
            dates.apply_changes('p', changes)
        self.assertTrue(all(c.args[0]=='clearProjectV2ItemFieldValue' for c in write.call_args_list))
