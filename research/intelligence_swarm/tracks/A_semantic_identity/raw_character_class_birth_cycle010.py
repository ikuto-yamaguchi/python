from __future__ import annotations
import itertools,json,math,pickle,random,resource,statistics,time
SEEDS=(1,7,19)
OPS=("noop","mark","swap"); ARITY={"noop":0,"mark":1,"swap":2}; OBJECTS=("A","B","C")
CHARS=("ラ","ミ","ソ","ギ","プ","ワ","ト","カ"); FORMS=("prefix","suffix","interleave","reverse","paragraph")

def apply_op(world,op,args):
 w=list(world)
 if op=="noop": return tuple(w)
 if op=="mark": w[args[0]]=(w[args[0]]+1)%3
 else: w[args[0]],w[args[1]]=w[args[1]],w[args[0]]
 return tuple(w)

def encode(obj_tokens,op_tokens,op,args,rng,form):
 ot=op_tokens[OPS.index(op)]; ats=[obj_tokens[i] for i in args]
 nuisance=[c for c in CHARS if c not in obj_tokens and c not in op_tokens]; f1,f2=rng.sample(nuisance,2)
 if form=="prefix": p=[f1,ot]+ats+[f2]
 elif form=="suffix": p=[f1]+ats+[ot,f2]
 elif form=="interleave": p=([ats[0],f1,ot]+ats[1:]+[f2]) if ats else [f1,ot,f2]
 elif form=="reverse": p=[f1]+list(reversed(ats))+[f2,ot]
 else:
  p=[f1,ot]+ats+[f2]
  return "".join(p[:2])+"\n"+"".join(p[2:])
 return "".join(p)

def rows(seed):
 r=random.Random(seed); chars=list(CHARS); r.shuffle(chars)
 obj_tokens=tuple(chars[:3]); op_tokens=tuple(chars[3:6]); out=[]
 for _ in range(84):
  before=tuple(r.randrange(3) for _ in OBJECTS); op=r.choice(OPS)
  args=tuple(r.sample(range(3),ARITY[op])); form=r.choice(FORMS)
  out.append({"before":before,"command":encode(obj_tokens,op_tokens,op,args,r,form),
              "after":apply_op(before,op,args),"op":op,"args":args,"form":form})
 return out,obj_tokens,op_tokens

def hypotheses():
 out=[]
 for op_set in itertools.combinations(CHARS,3):
  rem=[c for c in CHARS if c not in op_set]
  for obj_set in itertools.combinations(rem,3):
   for op_order in itertools.permutations(op_set):
    for obj_order in itertools.permutations(obj_set): out.append((op_order,obj_order))
 return out
HS=hypotheses()

def parses(h,cmd):
 op_order,obj_order=h; chars=[c for c in cmd if c in CHARS]
 op_chars=[c for c in chars if c in op_order]
 if len(op_chars)!=1: return []
 op=OPS[op_order.index(op_chars[0])]
 obj_chars=[c for c in chars if c in obj_order]
 if len(obj_chars)!=ARITY[op]: return []
 args=[obj_order.index(c) for c in obj_chars]; opts={tuple(args)}
 if len(args)==2: opts.add(tuple(reversed(args)))
 return [(op,a) for a in opts]

def predictions(h,row): return {apply_op(row["before"],op,args) for op,args in parses(h,row["command"])}

def entropy(surv,row):
 groups={}
 for idx in surv:
  key=tuple(sorted(predictions(HS[idx],row))); groups[key]=groups.get(key,0)+1
 n=max(1,len(surv))
 return -sum((v/n)*math.log2(v/n) for v in groups.values())

def select(pool,budget,method,seed,shuffle=False):
 surv=list(range(len(HS))); rng=random.Random(seed); pool=list(pool)
 for _ in range(budget):
  if not surv or not pool: break
  row=max(pool,key=lambda x:entropy(surv,x)) if method=="active" else rng.choice(pool)
  pool.remove(row); outcome=row["after"]
  if shuffle:
   alternatives=[x["after"] for x in pool if x["after"]!=outcome]
   if alternatives: outcome=rng.choice(alternatives)
  surv=[idx for idx in surv if outcome in predictions(HS[idx],row)]
 return surv

def vote(surv,row):
 v={}
 for idx in surv:
  for p in predictions(HS[idx],row): v[p]=v.get(p,0)+1
 return max(v,key=v.get) if v else None

def inverse_vote(surv,row):
 v={}
 for idx in surv:
  for op,_ in parses(HS[idx],row["command"]): v[op]=v.get(op,0)+1
 return max(v,key=v.get) if v else None

def evaluate(surv,data):
 m={k:0 for k in ("prospective","inverse","unknown_order","paragraph","counterfactual")}
 d={k:0 for k in m}
 for r in data:
  pred=vote(surv,r)
  m["prospective"]+=pred==r["after"]; d["prospective"]+=1
  m["inverse"]+=inverse_vote(surv,r)==r["op"]; d["inverse"]+=1
  if r["form"] in ("interleave","reverse"): m["unknown_order"]+=pred==r["after"]; d["unknown_order"]+=1
  if r["form"]=="paragraph": m["paragraph"]+=pred==r["after"]; d["paragraph"]+=1
  alt=tuple((x+1)%3 for x in r["before"]); rr=dict(r); rr["before"]=alt
  m["counterfactual"]+=vote(surv,rr)==apply_op(alt,r["op"],r["args"]); d["counterfactual"]+=1
 return {k:m[k]/max(1,d[k]) for k in m}

def run_seed(seed):
 data,obj_tokens,op_tokens=rows(seed); true=(op_tokens,obj_tokens); true_idx=HS.index(true)
 p1,p2,test=data[:28],data[28:56],data[56:]; out={}
 for method in ("active","random"):
  s1=select(p1,5,method,seed+100); s2=select(p2,5,method,seed+200); inter=list(set(s1)&set(s2))
  out[method]={"survivors_1":len(s1),"survivors_2":len(s2),"intersection":len(inter),
               "true_support_1":true_idx in s1,"true_support_2":true_idx in s2,
               "same_unique":len(s1)==len(s2)==1 and s1[0]==s2[0],**evaluate(inter,test),
               "model_bytes":len(pickle.dumps(inter))}
 sh1=select(p1,5,"active",seed+300,True); sh2=select(p2,5,"active",seed+400,True)
 inter=list(set(sh1)&set(sh2)); out["outcome_shuffle"]={"survivors_1":len(sh1),"survivors_2":len(sh2),"intersection":len(inter),**evaluate(inter,test)}
 nuisance=[c for c in CHARS if c not in obj_tokens and c not in op_tokens]; bad_obj=list(obj_tokens); bad_obj[0]=nuisance[0]
 bad=(op_tokens,tuple(bad_obj)); bad_surv=[HS.index(bad)] if bad in HS else []
 out["factor_shuffle"]={"survivors_1":len(bad_surv),"survivors_2":len(bad_surv),"intersection":len(bad_surv),**evaluate(bad_surv,test)}
 return out

def main():
 start=time.perf_counter(); raw={str(s):run_seed(s) for s in SEEDS}
 def avg(m,k): return statistics.mean(float(raw[str(s)][m][k]) for s in SEEDS)
 summary={m:{k:avg(m,k) for k in raw["1"][m]} for m in raw["1"]}
 print(json.dumps({"cycle":10,"hypothesis":"Independent-Witness Raw Character-Class Birth under Episode-Local Syntax",
  "seeds":SEEDS,"summary":summary,"strict_progress_seeds":0,"semantic_identity_gate":False,
  "failure_classification":"oracle_operation_family_and_cardinality_upper_bound",
  "candidate_count":len(HS),"model_bytes_mean":summary["active"]["model_bytes"],
  "peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
  "runtime_seconds":time.perf_counter()-start,
  "estimated_ops":"O(2*B*H*Q), H=20160, B=5, plus held-out voting",
  "answer_leakage":False,"character_class_oracle":False,"operation_family_oracle":True,
  "fixed_ontology":False,"rag":False,"external_llm":False,"weak_smartphone_verified":False,
  "highschool_level_passed":False,"completion":False,"raw":raw},ensure_ascii=False,indent=2))
if __name__=="__main__": main()
