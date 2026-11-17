"""Synthetic fixtures only; no labels or video from the provided game."""
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from possession import PossessionState, observation, validate, tag_evidence

CFG = json.loads((Path(__file__).resolve().parents[1] / 'config.json').read_text())


class PipelineTests(unittest.TestCase):
    def test_control_and_deflection(self):
        state = PossessionState(CFG)
        for _ in range(state.confirm):
            label, _ = state.step('H', 'control_candidate', 0)
        self.assertEqual(label, 'H')
        self.assertEqual(state.step('A', 'control_candidate', 0)[0], 'H')
        self.assertEqual(state.step(None, 'loose_or_contested', 0)[0], 'H')
        for _ in range(state.confirm):
            label, _ = state.step('A', 'control_candidate', 0)
        self.assertEqual(label, 'A')

    def test_missing_is_not_dead(self):
        state = PossessionState(CFG)
        for _ in range(state.confirm):
            state.step('H', 'control_candidate', 0)
        for _ in range(state.hold):
            self.assertEqual(state.step(None, 'missing_ball', 0)[0], 'H')
        self.assertEqual(state.step(None, 'missing_ball', 0)[0], 'X')

    def test_dead_and_restart(self):
        state = PossessionState(CFG)
        for _ in range(state.out_confirm):
            label, _ = state.step(None, 'outside', 0)
        self.assertEqual(label, 'D')
        self.assertEqual(state.step('H', 'control_candidate', 0)[0], 'D')
        for _ in range(state.confirm):
            label, _ = state.step('H', 'control_candidate', 0)
        self.assertEqual(label, 'H')
        state.reset()
        self.assertEqual(state.state, 'X')

    def test_tag_conflict_and_no_double_vote(self):
        state = PossessionState(CFG)
        for _ in range(state.confirm + 1):
            self.assertEqual(state.step('H', 'control_candidate', 2)[0], 'X')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'tags.xml'
            instance = '<instance><start>0</start><end>1</end><code>BUILD UP</code><label><group>Team</group><text>home</text></label></instance>'
            path.write_text('<root>'+instance*2+'</root>')
            support = tag_evidence(path, {'home': 'H'}, {**CFG, 'expected_frames': 26})
            self.assertEqual(list(support[:25]), [1]*25)
            self.assertEqual(support[25], 0)

    def test_geometry_nan_and_coverage(self):
        args = (['H', 'A'], (105, 68), CFG)
        self.assertEqual(observation([(0.5, 0.5), (0.8, 0.8)], (0.5, 0.5), *args)[0], 'H')
        self.assertEqual(observation([(0.5, 0.5), (0.5, 0.5)], (0.5, 0.5), *args)[0], None)
        self.assertEqual(observation([(0.5, 0.5), (float('nan'), 0)], (0.5, 0.5), *args)[1], 'team_coverage_missing')
        self.assertEqual(observation([], (float('nan'), 0), [], (105,68), CFG)[1], 'missing_ball')
        self.assertEqual(observation([], (1.1, 0), [], (105,68), CFG)[1], 'outside')

    def test_csv_contract(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'test.csv'
            path.write_text('frame,label\n0,H\n1,X\n')
            validate(path, 2)
            with self.assertRaises(ValueError):
                validate(path, 3)
            path.write_text('frame,label\n1,H\n2,X\n')
            with self.assertRaises(ValueError):
                validate(path, 2)


if __name__ == '__main__':
    unittest.main()
