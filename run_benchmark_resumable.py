"""Resumable APSP benchmark using the six original CPLEX formulations.

Copy beside solver_worker.py, models/, and benchmark/ in your project root.
Uses one subprocess per (graph, model); results are persisted after each run.
No mathematical formulation is modified.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

from solver_worker import MODELS

ROOT = Path(__file__).resolve().parent
RESULT_DIR = ROOT / 'results' / 'benchmark_120'
FIELDS = ['graph', 'model', 'status', 'period', 'raw_objective',
          'solver_time_seconds', 'wall_time_seconds', 'iterations', 'error', 'log']


def save_csv(rows: list[dict], filename: Path) -> None:
    temp = filename.with_suffix('.csv.tmp')
    with temp.open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temp, filename)


def read_result(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        obj = json.loads(path.read_text(encoding='utf-8'))
        return obj if isinstance(obj, dict) and obj.get('status') not in (None, 'not_run') else None
    except (OSError, ValueError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description='Run all 120 APSP instances with 6 CPLEX solvers; resume safely')
    parser.add_argument('--timeout', type=float, default=120, help='Per solver time limit in seconds')
    parser.add_argument('--iterations', type=int, default=10000, help='Max Benders iterations')
    parser.add_argument('--limit-graphs', type=int, default=0, help='0 means all 120 graphs')
    parser.add_argument('--model', choices=['all', *MODELS.keys()], default='all')
    parser.add_argument('--retry-failed', action='store_true', help='Rerun errors and timeouts')
    args = parser.parse_args()
    if args.timeout <= 0 or args.limit_graphs < 0 or args.iterations <= 0:
        parser.error('Timeout and iterations must be positive; limit-graphs must be nonnegative')

    graphs = sorted((ROOT / 'benchmark' / 'graphs').glob('*.xml'))
    if not graphs:
        parser.error('No XML files found in benchmark/graphs; put script in the project root')
    if args.limit_graphs:
        graphs = graphs[:args.limit_graphs]
    names = list(MODELS) if args.model == 'all' else [args.model]
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    print(f'Found {len(graphs)} XML graphs, {len(names)} models, {len(graphs)*len(names)} total runs', flush=True)
    print(f'Output: {RESULT_DIR}', flush=True)
    rows = []
    for graph in graphs:
        for name in names:
            stem = f'{graph.stem}__{name}'
            json_path = RESULT_DIR / (stem + '.json')
            log_path = RESULT_DIR / (stem + '.log')
            previous = read_result(json_path)
            if previous and not (args.retry_failed and str(previous.get('status', '')).lower() in
                    {'error', 'process_error', 'hard_timeout', 'no_result', 'bad_result_json'}):
                row = dict(previous)
                row['log'] = str(log_path)
                rows.append(row)
                save_csv(rows, RESULT_DIR / 'comparison.csv')
                print(f'[SKIP] {graph.name} | {name} | {row.get("status")}', flush=True)
                continue

            cmd = [sys.executable, str(ROOT / 'solver_worker.py'), '--model', name,
                   '--graph', graph.name, '--time-limit', str(args.timeout),
                   '--iterations', str(args.iterations), '--output', str(json_path)]
            print(f'[RUN ] {graph.name} | {name} | limit {args.timeout:g}s', flush=True)
            start = time.perf_counter()
            # Remove a stale result before starting so an interrupted process is not mistaken for a completed one.
            json_path.unlink(missing_ok=True)
            try:
                p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                                   errors='replace', timeout=args.timeout + 15)
                output = (p.stdout or '') + '\n' + (p.stderr or '')
                fallback = 'PROCESS_ERROR' if p.returncode else 'NO_RESULT'
            except subprocess.TimeoutExpired as exc:
                stdout = exc.stdout or b''
                stderr = exc.stderr or b''
                output = (stdout.decode(errors='replace') if isinstance(stdout, bytes) else stdout) + '\n' + \
                         (stderr.decode(errors='replace') if isinstance(stderr, bytes) else stderr)
                fallback = 'HARD_TIMEOUT'
            log_path.write_text(output, encoding='utf-8')
            row = read_result(json_path) or {
                'graph': graph.name, 'model': name, 'status': fallback,
                'period': None, 'raw_objective': None, 'solver_time_seconds': None,
                'iterations': None, 'error': f'Worker exited without a usable JSON result ({fallback}).'
            }
            row['wall_time_seconds'] = round(time.perf_counter() - start, 3)
            row['log'] = str(log_path)
            # Make the result persistent even if the process did not finish normally.
            tmp = json_path.with_suffix('.json.tmp')
            tmp.write_text(json.dumps(row, indent=2, default=str), encoding='utf-8')
            os.replace(tmp, json_path)
            rows.append(row)
            save_csv(rows, RESULT_DIR / 'comparison.csv')
            print(f'[DONE] {name}: {row.get("status")}; period={row.get("period")}', flush=True)

    counts = Counter(str(row.get('status')) for row in rows)
    print('\nFinished / recorded:', len(rows), '\nStatus counts:', dict(counts), flush=True)
    print('CSV:', RESULT_DIR / 'comparison.csv', flush=True)
    print('Important: time-limit feasible incumbents are NOT proven optimal. Validate schedules separately.')


if __name__ == '__main__':
    main()
