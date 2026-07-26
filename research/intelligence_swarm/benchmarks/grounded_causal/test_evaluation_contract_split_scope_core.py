#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('evaluation_contract', HERE / 'evaluation_contract.py')
assert SPEC and SPEC.loader
contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract)

METHODS = sorted(contract.REQUIRED_METHODS)
SEEDS = sorted(contract.CANONICAL_SEEDS)


def dataset(extra_split: str | None = None):
    rows = []
    for seed in SEEDS:
        rows.append({
            'instance_id': f'train-{seed}', 'domain': 'rtfm', 'seed': seed,
            'split': 'train', 'condition': 'in_distribution',
            'utterance': f'train utterance {seed}', 'state_before': {'x': 0},
            'gold_action': 0, 'gold_state_after': {'x': 1},
        })
        rows.append({
            'instance_id': f'test-{seed}', 'domain': 'rtfm', 'seed': seed,
            'split': 'test', 'condition': 'in_distribution',
            'utterance': f'test utterance {seed}', 'state_before': {'x': 2},
            'gold_action': 1, 'gold_state_after': {'x': 3},
        })
    if extra_split:
        rows.append({
            'instance_id': f'{extra_split}-1', 'domain': 'rtfm', 'seed': 1,
            'split': extra_split, 'condition': 'in_distribution',
            'utterance': f'{extra_split} utterance', 'state_before': {'x': 4},
            'gold_action': 1, 'gold_state_after': {'x': 5},
        })
    return rows


def predictions(rows, include_extra=False):
    out = []
    for row in rows:
        if row['split'] not in contract.EVAL_SPLITS and not include_extra:
            continue
        if row['split'] == 'train':
            continue
        for method in METHODS:
            pred = {
                'instance_id': row['instance_id'], 'method': method,
                'instance_fingerprint': contract.instance_fingerprint(contract.adapt_row(row)),
                'pred_action': row['gold_action'], 'pred_state_after': row['gold_state_after'],
            }
            if method in contract.SHUFFLE_METHODS:
                pred['control_source_instance_id'] = row['instance_id']
                pred['control_source_fingerprint'] = pred['instance_fingerprint']
            out.append(pred)
    return out


clean = dataset()
assert contract.validate_dataset(clean)['valid']
assert contract.score(clean, predictions(clean))['valid'] is False  # self-shuffle is independently fail-closed
assert contract.score(clean, predictions(clean))['expected_eval_instances'] == 3

for invalid in ('debug', 'calibration', 'analysis', 'posthoc'):
    rows = dataset(invalid)
    validation = contract.validate_dataset(rows)
    assert not validation['valid'], (invalid, validation)
    assert any('unregistered split' in error for error in validation['errors'])

    scored = contract.score(rows, predictions(rows, include_extra=True))
    assert not scored['valid'], (invalid, scored)
    assert scored['classification'] == 'initial_reproduction_failure'
    assert scored['expected_eval_instances'] == 3
    assert any('unregistered splits' in error for error in scored['errors'])
    assert any('non-evaluation split' in error for error in scored['errors'])

print('R0 core split-scope regression: PASS')
