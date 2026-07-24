from __future__ import annotations
import itertools,json,math,pickle,random,resource,statistics,time
SEEDS=(1,7,19); OPS=("noop","mark","swap","copy"); ARITY={"noop":0,"mark":1,"swap":2,"copy":2}
OBJECTS=("A","B","C","D"); OOBJ=("ラ","ミ","ソ","ネ"); OOP=("ギ","プ","ワ","ゾ"); FILL=("ト","カ")

def apply_op(world,op,args):
 w=list(world)
 if op=="noop": return tuple(w)
 if op=="mark": w[args[0]]=(w[args[0]]+1)%4
 elif op=="swap": w[args[0]],w[args[1]]=w[args[1]],w[args[0]]
 elif op=="copy": w[args[1]]=w[args[0]]
 return tuple(w)

def encode(objm,opm,op,args,rng,form):
 ot=OOP[opm.index(op)]; ats=[OOBJ[objm.index(OBJECTS[i])] for i in args]; f=rng.choice(FILL)
 if form=="prefix": p=[f,ot]+ats
 elif form=="suffix": p=ats+[ot,f]
 elif form=="interleave": p=([ats[0],f,ot]+ats[1:]) if ats else [f,ot]
 else: p=list(reversed(ats))+[f,ot]
 return "".join(p)

def rows(seed):
 r=random.Random(seed); obj=list(OBJECTS); op=list(OPS); r.shuffle(obj); r.shuffle(op); out=[]
 for _ in range(192):
  before=tuple(r.randrange(4) for _ in OBJECTS); action=r.choice(OPS); args=tuple(r.sample(range(4),ARITY[action])); form=r.choice(("prefix","suffix","interleave","reverse"))
  out.append({"before":before,"command":encode(obj,op,action,args,r,form),"after":apply_op(before,action,args),"op":action,"args":args,"form":form})
 return out,tuple(obj),tuple(op)

ARITY_PERMS=sorted(set(itertools.permutations((0,1,2,2))))
def hypotheses(): return [(opm,objm,arm) for opm in itertools.permutations(OPS) for objm in itertools.permutations(OBJECTS) for arm in ARITY_PERMS]
def parses(h,cmd):
 opm,objm,arm=h; chars=list(cmd); oi=[i for i,c in enumerate(chars) if c in OOP]; ob=[i for i,c in enumerate(chars) if c in OOBJ]
 if len(oi)!=1: return []
 ix=OOP.index(chars[oi[0]]); op=opm[ix]
 if ARITY[op]!=arm[ix]: return []
 filtered=[c for c in chars if c not in FILL]; out=[]
 for form in ("prefix","suffix","interleave","reverse"):
  ok=(form=="prefix" and filtered[0] in OOP) or (form in ("suffix","reverse") and filtered[-1] in OOP) or (form=="interleave" and len(filtered)>1 and filtered[1] in OOP)
  if not ok: continue
  args=[OBJECTS.index(objm[OOBJ.index(chars[p])]) for p in ob]
  if form=="reverse": args=list(reversed(args))
  if len(args)==ARITY[op]: out.append((op,tuple(args),form))
 return out
def predictions(h,row): return {apply_op(row["before"],op,args) for op,args,_ in parses(h,row["command"])}
def entropy(surv,row):
 groups={}
 for h in surv:
  key=tuple(sorted(predictions(h,row))); groups[key]=groups.get(key,0)+1
 n=max(1,len(surv)); return -sum((v/n)*math.log2(v/n) for v in groups.values())
def select(pool,budget,method,seed,conflict=False):
 surv=hypotheses(); rng=random.Random(seed); chosen=[]; pool=list(pool)
 for i in range(budget):
  if not pool or not surv: break
  row=max(pool,key=lambda x:entropy(surv,x)) if method=="active" else rng.choice(pool); pool.remove(row); chosen.append(row)
  outcome=row["after"]
  if conflict and i==budget//2:
   alternatives=[x["after"] for x in pool if x["after"]!=outcome]
   if alternatives: outcome=rng.choice(alternatives)
  surv=[h for h in surv if outcome in predictions(h,row)]
 return surv,chosen
def vote(surv,row):
 v={}
 for h in surv:
  for p in predictions(h,row): v[p]=v.get(p,0)+1
 return max(v,key=v.get) if v else None
def evaluate(surv,data):
 m={k:0 for k in ("prospective","inverse","repair","mixed_order","counterfactual")}
 for r in data:
  pred=vote(surv,r); m["prospective"]+=pred==r["after"]
  ov={}
  for h in surv:
   for op,_,_ in parses(h,r["command"]): ov[op]=ov.get(op,0)+1
  m["inverse"]+=(max(ov,key=ov.get)==r["op"]) if ov else False
  b=list(r["before"]); b[0]=(b[0]+1)%4; rr=dict(r); rr["before"]=tuple(b); m["repair"]+=vote(surv,rr)==apply_op(rr["before"],r["op"],r["args"])
  if r["form"] in ("interleave","reverse"): m["mixed_order"]+=pred==r["after"]
  alt=tuple((x+1)%4 for x in r["before"]); cr=dict(r); cr["before"]=alt; m["counterfactual"]+=vote(surv,cr)==apply_op(alt,r["op"],r["args"])
 n=len(data); mixed=max(1,sum(x["form"] in ("interleave","reverse") for x in data)); return {k:(v/mixed if k=="mixed_order" else v/n) for k,v in m.items()}
def run_seed(seed):
 data,objm,opm=rows(seed); true=(opm,objm,tuple(ARITY[x] for x in opm)); set1=data[:64]; set2=data[64:128]; test=data[128:]
 out={}
 for method in ("active","random"):
  s1,_=select(set1,5,method,seed+100); s2,_=select(set2,5,method,seed+200)
  inter=set(s1)&set(s2); consensus=[h for h in s1 if h in set(s2)]
  out[method]={"survivors_1":len(s1),"survivors_2":len(s2),"intersection":len(inter),"true_support_1":true in s1,"true_support_2":true in s2,"same_unique":len(s1)==len(s2)==1 and s1[0]==s2[0],"intersection_true":true in inter,**{f"closed_{k}":v for k,v in evaluate(consensus,test).items()},"model_bytes":len(pickle.dumps(consensus))}
 sc,_=select(set1,5,"active",seed+300,conflict=True); s2,_=select(set2,5,"active",seed+400); conflict_inter=set(sc)&set(s2)
 out["conflict"]={"survivors_conflict":len(sc),"normal_second":len(s2),"intersection":len(conflict_inter),"conflict_detected":len(conflict_inter)==0}
 s1,_=select(set1,5,"active",seed+500); s2,_=select(set2,5,"active",seed+600); consensus=list(set(s1)&set(s2)); shuffled=[]
 for opm_,objm_,arm in consensus:
  q=list(arm); q[0],q[1]=q[1],q[0]; shuffled.append((opm_,objm_,tuple(q)))
 out["arity_shuffle"]={**evaluate(shuffled,test),"survivors":len(shuffled)}
 return out

def main():
 raw={}; t=time.perf_counter()
 for s in SEEDS: raw[str(s)]=run_seed(s)
 def avg(method,key): return statistics.mean(float(raw[str(s)][method][key]) for s in SEEDS)
 summary={m:{k:avg(m,k) for k in raw["1"][m]} for m in raw["1"]}
 upper=sum(raw[str(s)]["active"]["same_unique"] and raw[str(s)]["active"]["intersection_true"] and all(raw[str(s)]["active"][f"closed_{k}"]>=0.8 for k in ("prospective","inverse","repair","mixed_order","counterfactual")) for s in SEEDS)
 print(json.dumps({"cycle":9,"hypothesis":"Independent-Witness Reconvergence under Episode-Local Syntax and Unknown Arity Support","seeds":SEEDS,"summary":summary,"upper_bound_reconvergence_seeds":upper,"formal_memory_eligible_seeds":0,"formal_memory_eligible_units":0,"failure_classification":"oracle_to_raw_grounding_gap","peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"runtime_seconds":time.perf_counter()-t,"candidate_count":6912,"estimated_ops":"selector O(2*B*H*Q), H=6912, B=5","answer_leakage":False,"memory_optimization_enabled":False,"weak_smartphone_verified":False,"highschool_level_passed":False,"completion":False,"raw":raw},ensure_ascii=False,indent=2))
if __name__=="__main__": main()
