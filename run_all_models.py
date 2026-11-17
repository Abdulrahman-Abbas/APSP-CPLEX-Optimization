"""Run six APSP formulations independently and write comparable CSV results.

Each solver runs in its own Python process. The parent imposes a hard timeout
and saves console output; one solver error cannot abort the whole experiment.
"""
import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path
from solver_worker import MODELS

ROOT=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser(description='APSP six-model CPLEX comparison')
    p.add_argument('--graph',default='graph__10-1000-0.10-02_0.xml')
    p.add_argument('--all-graphs',action='store_true')
    p.add_argument('--limit-graphs',type=int,default=0,help='0 means all')
    p.add_argument('--model',choices=['all']+list(MODELS),default='all')
    p.add_argument('--timeout',type=float,default=60,help='seconds allowed per solver')
    p.add_argument('--iterations',type=int,default=10000)
    a=p.parse_args()
    folder=ROOT/'benchmark'/'graphs'
    graphs=sorted(f.name for f in folder.glob('*.xml')) if a.all_graphs else [a.graph]
    if a.limit_graphs>0: graphs=graphs[:a.limit_graphs]
    selected=MODELS.keys() if a.model=='all' else [a.model]
    output=ROOT/'results'; output.mkdir(exist_ok=True)
    rows=[]
    for graph in graphs:
        if not (folder/graph).is_file():
            p.error(f'Graph not found: {folder/graph}')
        for model in selected:
            prefix=output/(Path(graph).stem+'__'+model)
            result_path=Path(str(prefix)+'.json')
            if result_path.exists(): result_path.unlink()  # avoid stale result on crash
            cmd=[sys.executable,str(ROOT/'solver_worker.py'),'--model',model,'--graph',graph,
                 '--time-limit',str(a.timeout),'--iterations',str(a.iterations),
                 '--output',str(result_path)]
            print(f'\nRunning {model} on {graph} ({a.timeout:g}s) ...',flush=True)
            start=time.perf_counter()
            try:
                proc=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,
                                    timeout=a.timeout+12,errors='replace')
                text=(proc.stdout or '')+'\n'+(proc.stderr or '')
                status='PROCESS_ERROR' if proc.returncode else 'UNKNOWN'
            except subprocess.TimeoutExpired as exc:
                text=(exc.stdout or b'')+(exc.stderr or b'')
                if isinstance(text,bytes): text=text.decode(errors='replace')
                status='HARD_TIMEOUT'
            Path(str(prefix)+'.log').write_text(text,encoding='utf-8')
            row={'model':model,'graph':graph,'status':status,'period':None,
                 'raw_objective':None,'solver_time_seconds':None,'iterations':None,
                 'wall_time_seconds':round(time.perf_counter()-start,3),'log':str(Path(str(prefix)+'.log'))}
            if result_path.is_file():
                try: row.update(json.loads(result_path.read_text(encoding='utf-8')))
                except (json.JSONDecodeError,OSError) as exc: row['status']='BAD_RESULT_JSON'; row['error']=str(exc)
            if row['status'] in {'UNKNOWN','not_run'}: row['status']='NO_RESULT'
            rows.append(row)
            with (output/'comparison.csv').open('w',newline='',encoding='utf-8') as f:
                cols=['graph','model','status','period','raw_objective','solver_time_seconds',
                      'wall_time_seconds','iterations','error','log']
                writer=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore')
                writer.writeheader();writer.writerows(rows)
            print(f"  Status: {row['status']} | Period: {row['period']} | Log: {row['log']}",flush=True)
    print('\nResults saved to:',output/'comparison.csv')

if __name__=='__main__': main()
