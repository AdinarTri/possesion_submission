"""Local, deterministic possession inference; no training, video or ground-truth access."""
import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
ATTACK_CODES = {'BUILD UP', 'PROGRESSION', 'ATTACKING TRANSITION',
                'CREATING CHANCES', 'LONG BALL', 'BALL IN FINAL THIRD', 'BALL IN THE BOX'}
DEFEND_CODES = {'DEFENDING IN MIDDLE THIRD', 'DEFENDING IN ATTACKING THIRD',
                'DEFENDING IN DEFENSIVE THIRD', 'DEFENSIVE TRANSITION'}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def one(folder, pattern):
    paths = list(folder.glob(pattern))
    if len(paths) != 1:
        raise ValueError(f'Expected exactly one {pattern} in {folder}')
    return paths[0]


def metadata(path):
    root = ET.parse(path).getroot()
    score = root.find('.//Score')
    home, away = score.get('idLocalTeam'), score.get('idVisitingTeam')
    sides = {home: 'H', away: 'A'}
    if home is None or away is None or home == away:
        raise ValueError('Missing distinct home/away team IDs')
    names = {t.findtext('Name').strip().casefold(): sides[t.get('id')]
             for t in root.findall('.//Teams/Team')}
    players = {p.get('id'): sides[p.get('teamId')] for p in root.findall('.//Players/Player')}
    channels = {c.get('id'): c.get('playerId') for c in root.findall('.//PlayerChannels/PlayerChannel')}
    refs = root.findall('.//DataFormatSpecification//PlayerChannelRef')
    if len(refs) % 3:
        raise ValueError('Expected x,y,speed triplets')
    slots = []
    for i in range(0, len(refs), 3):
        ids = [channels[r.get('playerChannelId')] for r in refs[i:i+3]]
        if len(set(ids)) != 1:
            raise ValueError('Mixed player IDs in one triplet')
        slots.append(players[ids[0]])
    size = root.find('.//FieldSize')
    pitch = float(size.findtext('Width')), float(size.findtext('Height'))
    if not slots or not all(math.isfinite(x) and x > 0 for x in pitch):
        raise ValueError('Invalid slots or pitch dimensions')
    return slots, names, pitch, float(root.findtext('.//FrameRate'))


def tag_evidence(path, names, config):
    """Boolean support by team: overlapping nested tags do not multiply evidence."""
    n, fps = config['expected_frames'], config['fps']
    diffs = {s: [0] * (n + 1) for s in 'HA'}
    for event in ET.parse(path).iter('instance'):
        code = (event.findtext('code') or '').strip().upper()
        tags = {t.findtext('group'): t.findtext('text') for t in event.findall('label')}
        side = names.get((tags.get('Team') or '').strip().casefold())
        if side is None or code not in ATTACK_CODES | DEFEND_CODES:
            continue
        if code in DEFEND_CODES:
            side = 'A' if side == 'H' else 'H'
        start, end = float(event.findtext('start')), float(event.findtext('end'))
        if not math.isfinite(start + end) or end < start:
            raise ValueError('Invalid tag interval')
        lo, hi = max(0, min(n, round(start * fps))), max(0, min(n, round(end * fps)))
        diffs[side][lo] += 1
        diffs[side][hi] -= 1
    support = bytearray(n)
    h = a = 0
    for i in range(n):
        h += diffs['H'][i]
        a += diffs['A'][i]
        support[i] = (1 if h > 0 else 0) | (2 if a > 0 else 0)
    return support


def xy(group):
    values = group.split(',')
    if len(values) != 3:
        raise ValueError('Expected x,y,speed')
    # Parse speed for structural validation only; no speed-unit assumption.
    values = tuple(float(v) for v in values)
    return values[:2]


def finite(point):
    return all(math.isfinite(v) for v in point)


def observation(players, ball, sides, pitch, cfg):
    if not finite(ball):
        return None, 'missing_ball'
    if not all(0 <= v <= 1 for v in ball):
        return None, 'outside'
    distances = {'H': math.inf, 'A': math.inf}
    for point, side in zip(players, sides):
        if finite(point) and all(0 <= v <= 1 for v in point):
            dist = math.hypot((point[0]-ball[0])*pitch[0], (point[1]-ball[1])*pitch[1])
            distances[side] = min(distances[side], dist)
    if not all(math.isfinite(d) for d in distances.values()):
        return None, 'team_coverage_missing'
    side = 'H' if distances['H'] < distances['A'] else 'A'
    other = 'A' if side == 'H' else 'H'
    if distances[side] <= cfg['control_radius_m'] and distances[other]-distances[side] >= cfg['opponent_margin_m']:
        return side, 'control_candidate'
    return None, 'loose_or_contested'


class PossessionState:
    def __init__(self, cfg):
        self.confirm = math.ceil(cfg['control_confirmation_seconds'] * cfg['fps'])
        self.out_confirm = math.ceil(cfg['outside_confirmation_seconds'] * cfg['fps'])
        self.hold = math.ceil(cfg['missing_hold_seconds'] * cfg['fps'])
        self.reset()

    def reset(self):
        self.state = 'X'
        self.pending = None
        self.count = self.out_count = self.missing_count = 0

    def step(self, candidate, reason, support):
        if reason == 'outside':
            self.out_count += 1
            self.pending, self.count = None, 0
            self.missing_count = 0
            if self.out_count >= self.out_confirm:
                self.state = 'D'
            return self.state, 'outside_confirmed' if self.state == 'D' else 'outside_pending'
        self.out_count = 0
        missing = reason in ('missing_ball', 'team_coverage_missing')
        self.missing_count = self.missing_count + 1 if missing else 0
        # Tags corroborate a proximity candidate; never turn an entire tagged interval
        # into a possession or a set-piece interval into a dead-ball stretch.
        prior = {1: 'H', 2: 'A'}.get(support)
        if prior is not None and candidate is not None and prior != candidate:
            candidate = None
        if candidate is None:
            self.pending, self.count = None, 0
        else:
            self.count = self.count + 1 if candidate == self.pending else 1
            self.pending = candidate
            if self.count >= self.confirm:
                self.state = candidate
        if missing and self.missing_count > self.hold:
            return 'X', 'abstain_missing'
        return self.state, 'confirmed_control' if candidate and self.count >= self.confirm else 'retain_state'


def validate(path, expected):
    with path.open(newline='', encoding='utf-8') as handle:
        reader = csv.reader(handle)
        if next(reader, None) != ['frame', 'label']:
            raise ValueError('Invalid CSV header')
        count = 0
        for frame, row in enumerate(reader):
            if len(row) != 2 or row[0] != str(frame) or row[1] not in ('H', 'A', 'D', 'X'):
                raise ValueError(f'Invalid CSV row {frame}')
            count += 1
    if count != expected:
        raise ValueError(f'Expected {expected} rows, found {count}')


def run(data, output, config_path):
    cfg = json.loads(config_path.read_text(encoding='utf-8'))
    n = cfg['expected_frames']
    folder = data / 'tactical'
    paths = {k: one(folder, pattern) for k, pattern in
             [('metadata', '*atd.xml'), ('tracking', '*atd.txt'), ('tags', '*smart_tagging.xml')]}
    hashes = {k: digest(p) for k, p in paths.items()}
    sides, names, pitch, fps = metadata(paths['metadata'])
    if fps != cfg['fps']:
        raise ValueError('Unexpected frame rate')
    support = tag_evidence(paths['tags'], names, cfg)
    output.mkdir(parents=True, exist_ok=True)
    csv_path = output / 'possession.csv'
    temp = output / 'possession.csv.tmp'
    labels, reasons, states = Counter(), Counter(), Counter()
    machine = PossessionState(cfg)
    active_half = None
    count = 0
    with paths['tracking'].open(encoding='utf-8') as raw, temp.open('w', encoding='utf-8', newline='') as out:
        writer = csv.writer(out, lineterminator='\n')
        writer.writerow(['frame', 'label'])
        for i, line in enumerate(raw):
            parts = line.strip().split(':')
            if len(parts) != 3 or int(parts[0]) != i+1 or i >= n:
                raise ValueError(f'Invalid tracking frame at row {i}')
            players = [xy(g) for g in parts[1].split(';')]
            ball = xy(parts[2])
            if len(players) != len(sides):
                raise ValueError(f'Invalid slot count at row {i}')
            half = next((j for j, (lo, hi) in enumerate(cfg['half_blocks_inclusive']) if lo <= i <= hi), None)
            if half != active_half:
                machine.reset()
                active_half = half
            if half is None:
                label, why, reason = 'X', 'outside_published_halves', 'not_evaluated'
            else:
                candidate, reason = observation(players, ball, sides, pitch, cfg)
                label, why = machine.step(candidate, reason, support[i])
            writer.writerow([i, label])
            labels[label] += 1
            reasons[reason] += 1
            states[why] += 1
            count += 1
    validate(temp, n)
    if hashes != {k: digest(p) for k, p in paths.items()}:
        raise RuntimeError('Input changed during inference')
    temp.replace(csv_path)
    manifest = {'algorithm': 'causal_control_state_v1', 'config': cfg,
                'input_sha256': hashes, 'config_sha256': digest(config_path),
                'source_sha256': digest(Path(__file__)), 'output_sha256': digest(csv_path),
                'rows': count, 'label_counts': dict(labels), 'observation_counts': dict(reasons),
                'decision_counts': dict(states), 'input_unchanged': True,
                'video_opened': False, 'ground_truth_opened': False,
                'training': None, 'parameter_search': None}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print('PASS: generated and structurally validated possession.csv; inputs unchanged.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True, help='Dataset root containing tactical/')
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts')
    parser.add_argument('--config', type=Path, default=ROOT / 'config.json')
    args = parser.parse_args()
    run(args.data, args.output, args.config)
