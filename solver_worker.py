"""One solver, one subprocess. Original mathematical models are in models/."""
import argparse
import json
import math
import traceback
from pathlib import Path

# Import inside main so import failures are saved as structured errors.
MODELS = {
    'bounded_monolithic': ('models.bounded.bounded_monolithic', 'BoundedMonolithic', False, False),
    'bounded_benders': ('models.bounded.bounded_Benders', 'BoundedMagnantiWongBenders', True, False),
    'quinton_monolithic': ('models.Quinton.Quinton_monolithic', 'QuintonMonolithic', False, True),
    'quinton_benders': ('models.Quinton.Quinton_Benders', 'QuintonMagnantiWongBenders', True, True),
    'bounded_quinton_monolithic': ('models.bounded.bounded_Quinton_monolithic', 'BoundedQuintonMonolithic', False, True),
    'bounded_quinton_benders': ('models.bounded.bounded_Quinton_Benders', 'BoundedQuintonMagnantiWongBenders', True, True),
}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',required=True,choices=MODELS)
    parser.add_argument('--graph',required=True)
    parser.add_argument('--time-limit',type=float,default=120)
    parser.add_argument('--iterations',type=int,default=10000)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    path=Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    info={'model': args.model,'graph':args.graph,'status':'not_run', 'period':None,
          'raw_objective':None,'solver_time_seconds':None,'iterations':None,'error':None}
    try:
        import importlib
        from models.utilities import APSPModelData
        graph_folder=Path(__file__).resolve().parent/'benchmark'/'graphs'
        data=APSPModelData(str(graph_folder)+ '/', args.graph)
        module_name,class_name,benders,inverse=MODELS[args.model]
        cls=getattr(importlib.import_module(module_name),class_name)
        solver=cls(args.model,data)
        if benders:
            solver.set_iterations(args.iterations)
            solver.solve(False,log_verbosity=0,time_out=args.time_limit)
            info['iterations']=getattr(solver,'iteration',None)
        else:
            solver.setup_model('')
            # No conflict refiner on ordinary time-out (it adds up to 180 seconds).
            solver.conflict_ref_time_limit=1
            solver.solve(False,time_limit=args.time_limit)
        info['status']=str(solver.get_status())
        info['solver_time_seconds']=solver.get_solve_time()
        raw=solver.get_objective()
        if raw is not None and raw != '':
            raw=float(raw)
            if math.isfinite(raw) and (not inverse or raw>0):
                info['raw_objective']=raw
                info['period']=(1.0/raw) if inverse else raw
            else:
                info['error']='Invalid or nonpositive objective returned.'
        if not benders:
            # Export the full, inspectable CPLEX formulation for this instance.
            lp=path.with_suffix('.lp')
            solver.model.export_as_lp(str(lp))
            info['lp_file']=str(lp)
        else:
            # Benders has multiple LPs: master, primal, dual and auxiliary.
            for title,attr in [('master','master_problem'),('primal','primal_sub_problem'),
                               ('dual','dual_sub_problem'),('auxiliary','auxiliary_sub_problem')]:
                obj=getattr(solver,attr,None)
                mdl=getattr(obj,'model',None)
                if mdl is not None:
                    lp=path.with_name(path.stem+'_'+title+'.lp')
                    mdl.export_as_lp(str(lp))
                    info[title+'_lp_file']=str(lp)
    except BaseException:
        info['status']='ERROR'
        info['error']=traceback.format_exc()
        print(info['error'],flush=True)
    finally:
        path.write_text(json.dumps(info,indent=2,default=str),encoding='utf-8')
        print('RESULT:',json.dumps(info,default=str),flush=True)

if __name__=='__main__':
    main()
