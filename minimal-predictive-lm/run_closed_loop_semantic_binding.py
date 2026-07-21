from __future__ import annotations

import json, random, resource, statistics, time
from pathlib import Path
from minimal_predictive_lm.closed_loop_semantic_binding import ClosedLoopSemanticBinding, Episode, trajectory_signature

OPS={"color":((0,0,0),(1,0,0),(0,1,0)),"owner":((0,0,0),(0,1,0),(0,0,1)),"place":((0,0,0),(0,0,1),(1,0,0)),"cancel":((-1,0,0),(0,-1,0),(0,0,-1))}
FORMS={"color":["色を教えて","色彩はどうですか","何色なの"],"owner":["持ち主は誰","所有者を教えて","誰のものですか"],"place":["場所はどこ","所在地を教えて","どこにありますか"],"cancel":["取り消して","今のをやめて","撤回します"]}

def apply(base,s):
    i=tuple(x+d for x,d in zip(base,s[0]));p=tuple(x+d for x,d in zip(i,s[1]));z=tuple(x+d for x,d in zip(p,s[2]));return i,p,z

def make(op,form,rng,decoy=False):
    b=tuple(rng.randint(-3,3) for _ in range(3));s=((0,0,0),(0,0,1),(1,0,0)) if decoy else OPS[op];i,p,z=apply(b,s);return Episode(form,b,i,p,z)

def one(scale,seed):
    rng=random.Random(seed);m=ClosedLoopSemanticBinding();known=[(o,f) for o,fs in FORMS.items() for f in fs[:2]]
    train=[make(*rng.choice(known),rng) for _ in range(scale)]
    t=time.perf_counter()
    for e in train:m.observe(e)
    fit=(time.perf_counter()-t)*1000
    one_shot=[];transfer=[]
    for op,fs in FORMS.items():
        e=make(op,fs[2],rng);one_shot.append(int(m.infer_from_trajectory(e)==m.operations.get(trajectory_signature(e))));m.observe(e);transfer.append(int(m.infer_known(fs[2])==m.operations.get(trajectory_signature(e))))
    dec=make("color","今日の天気は",rng,True);color=m.operations.get(OPS["color"]);decoy_rejection=int(m.infer_from_trajectory(dec)!=color)
    ts=[];r=m.reads
    for _ in range(1000):
        s=time.perf_counter_ns();m.infer_known("何色なの");ts.append((time.perf_counter_ns()-s)/1e6)
    return {"scale":scale,"seed":seed,"one_shot_grounding":sum(one_shot)/4,"post_ground_transfer":sum(transfer)/4,"decoy_rejection":decoy_rejection,"immediate_only_collision":int(trajectory_signature(dec)[0]==OPS["color"][0]),"operators":len(m.operations),"forms":len(m.forms),"model_bytes":m.serialized_bytes(),"fit_ms":fit,"infer_mean_ms":statistics.mean(ts),"infer_p95_ms":sorted(ts)[949],"candidate_count":len(m.operations),"reads_per_infer":(m.reads-r)/1000}

def main():
    rows=[one(s,z) for s in (8,32,128,512) for z in (1,7,19,31,43)]
    report={"experiment":"closed-loop-semantic-binding-001","rows":rows,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"integrated_gate":{k:False for k in ("free_dialogue","instruction_following","reading","reasoning","planning","causal_counterfactual","free_writing","long_dialogue","continual_learning")},"highschool_level_passed":False,"native_japanese_communication_passed":False,"completion":False}
    Path("closed_loop_semantic_binding_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
if __name__=="__main__":main()
