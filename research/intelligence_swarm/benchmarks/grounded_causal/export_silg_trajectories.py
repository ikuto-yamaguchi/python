from __future__ import annotations
import argparse, json, random
from pathlib import Path
from typing import Any

def flatten_obs(x: Any) -> list[float]:
    if isinstance(x, dict):
        out=[]
        for k in sorted(x):
            if k in {'instruction','text','wiki','message','task'}: continue
            out.extend(flatten_obs(x[k]))
        return out
    if hasattr(x,'tolist'): return flatten_obs(x.tolist())
    if isinstance(x,(list,tuple)):
        out=[]
        for v in x: out.extend(flatten_obs(v))
        return out
    if isinstance(x,(bool,int,float)): return [float(x)]
    return []

def extract_text(obs: Any) -> str:
    if not isinstance(obs,dict): return ''
    vals=[]
    for k in ('instruction','text','wiki','message','task'):
        if k in obs:
            v=obs[k]
            vals.append(v if isinstance(v,str) else ' '.join(map(str,v)) if isinstance(v,(list,tuple)) else str(v))
    return '\n'.join(vals)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--env',default='silg:rtfm_train_s1-v0'); ap.add_argument('--episodes',type=int,default=100); ap.add_argument('--seed',type=int,default=1); ap.add_argument('--split',choices=['train','test'],default='train'); ap.add_argument('--out',required=True); args=ap.parse_args()
    try:
        import gym
        import silg  # noqa:F401
    except Exception as e:
        raise SystemExit(f'SILG_IMPORT_FAILURE: {type(e).__name__}: {e}')
    rng=random.Random(args.seed); env=gym.make(args.env); rows=[]
    try:
        if hasattr(env,'seed'): env.seed(args.seed)
        for ep in range(args.episodes):
            reset=env.reset(); obs=reset[0] if isinstance(reset,tuple) else reset; done=False; t=0
            while not done:
                action=rng.randrange(env.action_space.n); step=env.step(action)
                if len(step)==5: nxt,reward,terminated,truncated,info=step; done=terminated or truncated
                else: nxt,reward,done,info=step
                before=flatten_obs(obs); after=flatten_obs(nxt)
                if not before or len(before)!=len(after): raise RuntimeError(f'nonfixed numeric state at episode={ep} step={t}: {len(before)}->{len(after)}')
                rows.append({'instance_id':f'{args.split}-{args.seed}-{ep}-{t}','domain':args.env,'seed':args.seed,'split':args.split,'utterance':extract_text(obs),'state_before':before,'state_after':after,'action':int(action),'reward':float(reward),'done':bool(done),'entity_holdout':False,'dynamics_holdout':False,'language_holdout':False})
                obs=nxt; t+=1
    finally: env.close()
    Path(args.out).write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in rows)+'\n')
    print(json.dumps({'rows':len(rows),'env':args.env,'seed':args.seed,'split':args.split,'out':args.out}))
if __name__=='__main__': main()
