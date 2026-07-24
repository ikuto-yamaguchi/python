from __future__ import annotations
import json, math, pickle, random, resource, statistics, time
from collections import Counter, defaultdict

OBJECTS=["青い箱","赤い箱","北の鍵","南の鍵","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","北の鍵":"北側キー","南の鍵":"南側キー","試料甲":"サンプル甲","試料乙":"サンプル乙"}
VALUES=["棚A","棚B","棚C","待機","完了","保留"]
FORMS=["canonical","order","lexeme","alternate","nested","paragraph"]
TEST_MODES=FORMS+["rename","omitted"]

def make_ep(rng, form, obj=None, old=None, new=None):
    obj=obj or rng.choice(OBJECTS); old=old or rng.choice(VALUES)
    new=new or rng.choice([v for v in VALUES if v!=old])
    surf=ALIASES[obj] if form=="rename" else obj
    if form=="alternate":
        before=f"状態報告：{surf}={old}。補助欄は維持。"; command=f"{surf}を{new}へ。"
    else:
        before=f"{surf}の現在値は{old}です。補助欄は維持します。"
        if form=="order": command=f"{new}へ変更してください。対象は{surf}です。"
        elif form=="lexeme": command=f"{surf}は次から{new}扱いです。"
        elif form=="nested": command=f"依頼は「{surf}を{new}へ変更」です。"
        elif form=="paragraph": command=f"前段は維持。\n{surf}を{new}へ変更してください。\n後段も維持。"
        elif form=="omitted": command=f"それを{new}へ変更してください。"
        else: command=f"{surf}を{new}へ変更してください。"
    after=before.replace(old,new,1)
    return {"before":before,"command":command,"after":after,"obj":surf,"old":old,"new":new,"form":form}

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,len(a)-r,l,len(b)-r

def changed(a,b):
    return diff(a,b)

def bucket(i,j,n):
    return (min(5,int(6*i/max(1,n))),min(5,int(6*j/max(1,n))),min(7,j-i))

def build_worlds(ep,rng):
    base_obj=next((o for o in OBJECTS if o==ep['obj'] or ALIASES.get(o)==ep['obj']),OBJECTS[0])
    obj2=rng.choice([o for o in OBJECTS if o!=base_obj])
    val2=rng.choice([v for v in VALUES if v not in (ep['old'],ep['new'])])
    return {
      "object":make_ep(rng,ep['form'] if ep['form'] in FORMS else 'canonical',obj2,ep['old'],ep['new']),
      "value":make_ep(rng,ep['form'] if ep['form'] in FORMS else 'canonical',base_obj,ep['old'],val2),
      "order":make_ep(rng,'order' if ep['form']!='order' else 'canonical',base_obj,ep['old'],ep['new'])
    }

def proposal(ep,worlds):
    os=changed(ep['command'],worlds['object']['command'])
    vs=changed(ep['command'],worlds['value']['command'])
    ss=diff(ep['before'],ep['after'])
    if os[0]>=os[1] or vs[0]>=vs[1] or ss[0]>=ss[1]: return None
    payload_o=ep['command'][os[0]:os[1]]; payload_v=ep['command'][vs[0]:vs[1]]
    order_ok=payload_o in worlds['order']['command'] and payload_v in worlds['order']['command']
    return {
      "state":bucket(ss[0],ss[1],len(ep['before'])),
      "r0":bucket(os[0],os[1],len(ep['command'])),
      "r1":bucket(vs[0],vs[1],len(ep['command'])),
      "relative":int(os[0]<vs[0]),"order_ok":order_ok,
      "spans":{"state":(ss[0],ss[1]),"r0":(os[0],os[1]),"r1":(vs[0],vs[1])}
    }

def lesion_vector(ep,p):
    s0,s1=p['spans']['state']; o0,o1=p['spans']['r0']; v0,v1=p['spans']['r1']
    obj=ep['command'][o0:o1]; val=ep['command'][v0:v1]
    full=int(obj in ep['before'] and val in ep['command'] and ep['before'][:s0]+val+ep['before'][s1:]==ep['after'])
    no0=int(val in ep['command'] and ep['before'][:s0]+val+ep['before'][s1:]==ep['after'])
    no1=int(obj in ep['before'])
    no2=int(obj in ep['before'] and val in ep['command'])
    return (full-no0, full-no1, full-no2)

def key(p,method,lesion=None):
    if method=='within': return (p['state'],p['r0'],p['r1'],p['relative'],p['order_ok'])
    if method in ('cross','mdl','shuffle'): return (lesion,p['relative'],p['order_ok'])
    raise ValueError(method)

def train(seed,method):
    rng=random.Random(seed); by_form=defaultdict(list)
    for form in FORMS:
      for _ in range(36):
        ep=make_ep(rng,form); p=proposal(ep,build_worlds(ep,rng))
        if p: by_form[form].append((ep,p,lesion_vector(ep,p)))
    t0=time.perf_counter(); counts=Counter(); held_hits=Counter(); held_total=Counter()
    for held in FORMS:
      profiles=Counter()
      for f in [x for x in FORMS if x!=held]:
        for ep,p,lv in by_form[f]:
          use_lv=(lv[2],lv[1],lv[0]) if method=='shuffle' else lv
          profiles[key(p,'within' if method=='within' else 'cross',use_lv)]+=1
      for ep,p,lv in by_form[held]:
        use_lv=(lv[2],lv[1],lv[0]) if method=='shuffle' else lv
        k=key(p,'within' if method=='within' else 'cross',use_lv)
        held_total[k]+=1
        if k in profiles: held_hits[k]+=1
        counts[k]+=profiles[k]
    grammar=[]
    for k,c in counts.items():
      support=held_hits[k]; total=held_total[k]
      bits=8*len(repr(k))+12*(total-support)+math.log2(1+c)
      gain=20*support-bits
      if method in ('cross','mdl') and support<2: continue
      if method=='mdl' and gain<=0: continue
      grammar.append((k,c,support,bits,gain))
    grammar.sort(key=lambda x:(x[4],x[2],x[1]),reverse=True)
    return grammar[:48],time.perf_counter()-t0

def spans(s,maxlen=12):
    return [(i,j,s[i:j]) for i in range(len(s)) for j in range(i+1,min(len(s),i+maxlen)+1)]

def infer(ep,grammar,method):
    novel=[x for x in spans(ep['command'],8) if x[2] not in ep['before'] and not any(c in x[2] for c in '。、\n「」')][:24]
    common=[x for x in spans(ep['command'],10) if len(x[2])>=2 and x[2] in ep['before'] and not any(c in x[2] for c in '。、\n「」')][:16]
    states=spans(ep['before'],10)[:96]; cand=[]
    for k,c,sup,bits,gain in grammar:
      if method=='within': stateb,r0b,r1b,rel,order_ok=k
      else: lv,rel,order_ok=k; stateb=r0b=r1b=None
      for si,sj,ss in states:
        if stateb and bucket(si,sj,len(ep['before']))!=stateb: continue
        for vi,vj,val in novel:
          if r1b and bucket(vi,vj,len(ep['command']))!=r1b: continue
          if common and not any((oi<vi)==bool(rel) for oi,oj,o in common): continue
          pred=ep['before'][:si]+val+ep['before'][sj:]
          score=gain+4*sup-math.log2(1+len(novel))
          cand.append((pred,score,si,sj,val))
    best={}
    for x in cand:
      if x[0] not in best or x[1]>best[x[0]][1]: best[x[0]]=x
    rank=sorted(best.values(),key=lambda x:x[1],reverse=True)
    if not rank:return None,0,0
    ent=math.log2(len(rank))
    if len(rank)>1 and abs(rank[0][1]-rank[1][1])<1e-9:return None,len(rank),ent
    return rank[0],len(rank),ent

def run():
    methods=['within','cross','mdl','shuffle']; raw={}
    for seed in (1,7,19):
      raw[str(seed)]={}
      for method in methods:
        g,tr=train(seed,method); raw[str(seed)][method]={"grammar":len(g),"model_bytes":len(pickle.dumps(g)),"training_seconds":tr,"description_bits":sum(x[3] for x in g)}
        for mode in TEST_MODES:
          rng=random.Random(seed*100+TEST_MODES.index(mode)); vals=[]; t0=time.perf_counter()
          for _ in range(18):
            ep=make_ep(rng,mode); p,n,e=infer(ep,g,method)
            true_s=ep['before'].find(ep['old'])
            vals.append({"accuracy":p is not None and p[0]==ep['after'],"wrong":p is not None and p[0]!=ep['after'],"null":p is None,"candidates":n,"entropy_bits":e,"exact_state_boundary":p is not None and (p[2],p[3])==(true_s,true_s+len(ep['old'])),"value_recall":p is not None and p[4]==ep['new']})
          raw[str(seed)][method][mode]={k:statistics.mean(float(v[k]) for v in vals) for k in vals[0]}
          raw[str(seed)][method][mode]['inference_ms']=(time.perf_counter()-t0)*1000/len(vals)
    summary={}
    for method in methods:
      summary[method]={}
      for mode in TEST_MODES:
        summary[method][mode]={k:statistics.mean(raw[str(seed)][method][mode][k] for seed in (1,7,19)) for k in raw['1'][method][mode]}
      for k in ('grammar','model_bytes','training_seconds','description_bits'):
        summary[method][k]=statistics.mean(raw[str(seed)][method][k] for seed in (1,7,19))
    return {"cycle":42,"hypothesis":"Cross-Form Deletion-Stable Grammar from Predictive Role Equivalence","seeds":[1,7,19],"summary":summary,"raw":raw,"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"role proposal O(NL), leave-one-form-out profile O(FP), inference O(GL^2V)","final_after_future_used_for_ranking":False,"fixed_ontology_or_handwritten_slots_used_by_model":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}

if __name__=='__main__': print(json.dumps(run(),ensure_ascii=False,indent=2))
