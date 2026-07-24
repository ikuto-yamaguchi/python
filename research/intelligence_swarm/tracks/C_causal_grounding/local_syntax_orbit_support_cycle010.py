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
 for _ in range(128):
  before=tuple(r.randrange(4) for _ in OBJECTS); action=r.choice(OPS); args=tuple(r.sample(range(4),ARITY[action])); form=r.choice(("prefix","suffix","interleave","reverse"))
  out.append({"before":before,"command":encode(obj,op,action,args,r,form),"after":apply_op(before,action,args),"op":action,"args":args,"form":form})
 return out,tuple(obj),tuple(op)

ARITY_PERMS=sorted(set(itertools.permutations((0,1,2,2))))
def hypotheses(local):
 base=[(opm,objm,arm) for opm in itertools.permutations(OPS) for objm in itertools.permutations(OBJECTS) for arm in ARITY_PERMS]
 return base if local else [(a,b,c,f) for a,b,c in base for f in ("prefix","suffix","interleave","reverse")]

def parses(h,cmd,local):
 if local: opm,objm,arm=h; forms=("prefix","suffix","interleave","reverse")
 else: opm,objm,arm,f=h; forms=(f,)
 chars=list(cmd); oi=[i for i,c in enumerate(chars) if c in OOP]; ob=[i for i,c in enumerate(chars) if c in OOBJ]
 if len(oi)!=1: return []
 ix=OOP.index(chars[oi[0]]); op=opm[ix]
 if ARITY[op]!=arm[ix]: return []
 filtered=[c for c in chars if c not in FILL]; out=[]
 for form in forms:
  ok=(form=="prefix" and filtered[0] in OOP) or (form in ("suffix","reverse") and filtered[-1] in OOP) or (form=="interleave" and len(filtered)>1 and filtered[1] in OOP)
  if not ok: continue
  args=[OBJECTS.index(objm[OOBJ.index(chars[p])]) for p in ob]
  if form=="reverse": args=list(reversed(args))
  if len(args)==ARITY[op]: out.append((op,tuple(args),form))
 return out

def predictions(h,row,local): return {apply_op(row["before"],op,args) for op,args,_ in parses(h,row["command"],local)}
def entropy(surv,row,local):
 groups={}
 for h in surv:
  key=tuple(sorted(predictions(h,row,local))); groups[key]=groups.get(key,0)+1
 n=max(1,len(surv)); return -sum((v/n)*math.log2(v/n) for v in groups.values())

def run(data,method,budget=5):
 local=method!="global_form"; surv=hypotheses(local); rng=random.Random(1000+sum(map(ord,method))); pool=data[:64]
 for _ in range(budget):
  if not pool or not surv: break
  row=max(pool,key=lambda x:entropy(surv,x,local)) if method in ("local_active","global_form") else rng.choice(pool); pool.remove(row); outcome=row["after"]
  if method=="outcome_shuffle": outcome=rng.choice(data[:64])["after"]
  surv=[h for h in surv if outcome in predictions(h,row,local)]
 if method=="argument_shuffle":
  changed=[]
  for opm,objm,arm in surv:
   q=list(objm); q[0],q[1]=q[1],q[0]; changed.append((opm,tuple(q),arm))
  surv=changed
 return surv,local

def vote(surv,row,local):
 v={}
 for h in surv:
  for p in predictions(h,row,local): v[p]=v.get(p,0)+1
 return max(v,key=v.get) if v else None

def evaluate(surv,data,local):
 test=data[64:]; m={k:0 for k in ("prospective","inverse","repair","mixed_order","counterfactual")}
 for r in test:
  pred=vote(surv,r,local); m["prospective"]+=pred==r["after"]
  ov={}
  for h in surv:
   for op,_,_ in parses(h,r["command"],local): ov[op]=ov.get(op,0)+1
  m["inverse"]+=(max(ov,key=ov.get)==r["op"]) if ov else False
  b=list(r["before"]); b[0]=(b[0]+1)%4; rr=dict(r); rr["before"]=tuple(b); m["repair"]+=vote(surv,rr,local)==apply_op(rr["before"],r["op"],r["args"])
  if r["form"] in ("interleave","reverse"): m["mixed_order"]+=pred==r["after"]
  alt=tuple((x+1)%4 for x in r["before"]); cr=dict(r); cr["before"]=alt; m["counterfactual"]+=vote(surv,cr,local)==apply_op(alt,r["op"],r["args"])
 n=len(test); mixed=max(1,sum(x["form"] in ("interleave","reverse") for x in test)); return {k:(v/mixed if k=="mixed_order" else v/n) for k,v in m.items()}

def main():
 methods=("global_form","local_active","local_random","argument_shuffle","outcome_shuffle"); raw={}
 for seed in SEEDS:
  data,objm,opm=rows(seed); raw[str(seed)]={}; true_arm=tuple(ARITY[x] for x in opm)
  for method in methods:
   t=time.perf_counter(); surv,local=run(data,method); triples=surv if local else [(x[0],x[1],x[2]) for x in surv]
   raw[str(seed)][method]={"survivors":len(surv),"true_support":any(x==(opm,objm,true_arm) for x in triples),**evaluate(surv,data,local),"seconds":time.perf_counter()-t,"model_bytes":len(pickle.dumps(surv))}
 summary={m:{k:statistics.mean(float(raw[str(s)][m][k]) for s in SEEDS) for k in raw["1"][m]} for m in methods}
 strict=sum(all(raw[str(s)]["local_active"][k]>=max(raw[str(s)][c][k] for c in methods if c!="local_active")+0.10 for k in ("prospective","inverse","repair","mixed_order","counterfactual")) for s in SEEDS)
 print(json.dumps({"cycle":10,"hypothesis":"Episode-Local Syntax Orbit Restores Causal Candidate Support","seeds":SEEDS,"summary":summary,"strict_gate_seeds":strict,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_ops":"selector O(B*H*Q), H=6912 local / 27648 global","answer_leakage":False,"weak_smartphone_verified":False,"highschool_level_passed":False,"completion":False,"raw":raw},ensure_ascii=False,indent=2))
if __name__=="__main__": main()
