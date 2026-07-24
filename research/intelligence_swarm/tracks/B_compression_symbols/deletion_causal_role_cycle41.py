from __future__ import annotations
import json, math, pickle, random, resource, statistics, time
from collections import Counter, defaultdict

OBJECTS=["青い箱","赤い箱","北の鍵","南の鍵","試料甲","試料乙","端末一","端末二"]
VALUES=["棚A","棚B","棚C","棚D","待機","完了","保留","処理中"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","北の鍵":"北側キー","南の鍵":"南側キー","試料甲":"サンプル甲","試料乙":"サンプル乙","端末一":"第一端末","端末二":"第二端末"}
MODES=["seen","word_order","lexeme","rename","alternate","nested","omitted","paragraph"]


def episode(rng,mode,obj=None,old=None,new=None):
    obj=obj or rng.choice(OBJECTS); old=old or rng.choice(VALUES); new=new or rng.choice([v for v in VALUES if v!=old])
    surf=ALIASES[obj] if mode=="rename" else obj
    before=f"{surf}の現在値は{old}です。補助記録は維持します。"
    if mode=="word_order": command=f"{new}へ変更してください。対象は{surf}です。"
    elif mode=="lexeme": command=f"{surf}を次回から{new}扱いにします。"
    elif mode=="alternate": before=f"状態報告：{surf}={old}。補助記録は維持。"; command=f"{surf}を{new}へ。"
    elif mode=="nested": command=f"依頼内容は「{surf}を{new}へ変更」です。"
    elif mode=="omitted": command=f"それを{new}へ変更してください。"
    elif mode=="paragraph": command=f"前段は維持します。\n{surf}を{new}へ変更してください。\n後段も維持します。"
    else: command=f"{surf}を{new}へ変更してください。"
    after=before.replace(old,new,1)
    return dict(before=before,command=command,after=after,obj=surf,old=old,new=new,mode=mode)

def changed_span(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,len(a)-r,l,len(b)-r

def worlds(ep,rng):
    base_obj=next((o for o in OBJECTS if o==ep['obj'] or ALIASES.get(o)==ep['obj']),OBJECTS[0])
    obj2=rng.choice([o for o in OBJECTS if o!=base_obj]); val2=rng.choice([v for v in VALUES if v not in (ep['old'],ep['new'])])
    base_mode=ep['mode'] if ep['mode'] in ('seen','word_order','lexeme') else 'seen'
    return (episode(rng,base_mode,obj=obj2,old=ep['old'],new=ep['new']),
            episode(rng,base_mode,obj=base_obj,old=ep['old'],new=val2),
            episode(rng,'word_order' if base_mode!='word_order' else 'seen',obj=base_obj,old=ep['old'],new=ep['new']))

def proposal(ep,ws,shuffle=False):
    ow,vw,rw=ws
    if shuffle: ow,vw=vw,ow
    os=changed_span(ep['command'],ow['command']); vs=changed_span(ep['command'],vw['command']); ss=changed_span(ep['before'],ep['after'])
    if os[0]>=os[1] or vs[0]>=vs[1] or ss[0]>=ss[1]: return None
    op=ep['command'][os[0]:os[1]]; vp=ep['command'][vs[0]:vs[1]]
    if not op or not vp: return None
    return {'ow':min(8,os[1]-os[0]),'vw':min(8,vs[1]-vs[0]),'sw':min(8,ss[1]-ss[0]),
            'order':int(os[0]<vs[0]),'commute':int(op in rw['command'] and vp in rw['command'])}

def key(p): return (p['ow'],p['vw'],p['sw'],p['order'],p['commute'])

def consequences(p,lesion):
    roles={'r0','r1','r2'}-set(lesion)
    return (int('r0' in roles and p['commute']),int('r1' in roles and p['commute']),int('r2' in roles),int(len(roles)>=2))

def train(seed,method):
    rng=random.Random(seed); rows=[episode(rng,rng.choice(['seen','word_order','lexeme','rename'])) for _ in range(120)]
    t0=time.perf_counter(); stats=defaultdict(lambda:{'support':0,'full':Counter(),'lesions':defaultdict(Counter)})
    for ep in rows:
        p=proposal(ep,worlds(ep,rng),shuffle=(method=='shuffle'))
        if not p: continue
        k=key(p); st=stats[k]; st['support']+=1; st['full'][consequences(p,())]+=1
        for lesion in (('r0',),('r1',),('r2',),('r0','r1'),('r0','r2'),('r1','r2')):
            st['lesions'][lesion][consequences(p,lesion)]+=1
    grammar=[]
    for k,st in stats.items():
        full=st['full'].most_common(1)[0][0]; selective=[]
        for role,expected in [('r0',0),('r1',1),('r2',2)]:
            les=st['lesions'][(role,)].most_common(1)[0][0]
            delta=[full[i]-les[i] for i in range(4)]
            selective.append(int(delta[expected]>0 and sum(max(0,d) for i,d in enumerate(delta) if i!=expected)==0))
        lesion_score=sum(selective)
        bits=8*len(repr(k))+12*(3-lesion_score)+math.log2(1+st['support'])
        gain=18*st['support']+24*lesion_score-bits
        keep=True
        if method in ('deletion','minimal','mdl') and lesion_score<1: keep=False
        if method in ('minimal','mdl') and lesion_score<2: keep=False
        if method=='mdl' and gain<=0: keep=False
        if keep: grammar.append((k,st['support'],tuple(selective),bits,gain))
    grammar.sort(key=lambda x:(x[4],sum(x[2]),x[1]),reverse=True)
    return grammar[:48],time.perf_counter()-t0

def spans(s,maxlen=12): return [(i,j,s[i:j]) for i in range(len(s)) for j in range(i+1,min(len(s),i+maxlen)+1)]
def infer(ep,grammar):
    novel=[x for x in spans(ep['command'],10) if x[2] not in ep['before'] and not any(c in x[2] for c in '。、\n「」')]
    common=[x for x in spans(ep['command'],12) if len(x[2])>=2 and x[2] in ep['before'] and not any(c in x[2] for c in '。、\n「」')]
    states=spans(ep['before'],12); cand=[]
    for k,sup,sel,bits,gain in grammar:
        ow,vw,sw,order,comm=k
        vals=[x for x in novel if min(8,x[1]-x[0])==vw]
        objs=[x for x in common if min(8,x[1]-x[0])==ow]
        if sel[0] and not objs: continue
        for si,sj,_ in states:
            if min(8,sj-si)!=sw: continue
            for vi,vj,val in vals:
                if sel[0] and not any((oi<vi)==bool(order) for oi,oj,o in objs): continue
                pred=ep['before'][:si]+val+ep['before'][sj:]
                score=gain+8*sum(sel)-math.log2(1+len(vals))
                cand.append((pred,score,si,sj,val))
    best={}
    for c in cand:
        if c[0] not in best or c[1]>best[c[0]][1]: best[c[0]]=c
    ranked=sorted(best.values(),key=lambda x:x[1],reverse=True)
    if not ranked:return None,0,0
    if len(ranked)>1 and abs(ranked[0][1]-ranked[1][1])<1e-9:return None,len(ranked),math.log2(len(ranked))
    return ranked[0],len(ranked),math.log2(len(ranked))

def run():
    methods=['quotient','deletion','minimal','mdl','shuffle']; raw={}
    for seed in (1,7,19):
        raw[str(seed)]={}
        for method in methods:
            g,tr=train(seed,method); raw[str(seed)][method]={'grammar':len(g),'model_bytes':len(pickle.dumps(g)),'training_seconds':tr,'description_bits':sum(x[3] for x in g),'selective_roles':sum(sum(x[2]) for x in g)}
            for mode in MODES:
                rng=random.Random(seed*1000+MODES.index(mode)); vals=[]; t0=time.perf_counter()
                for _ in range(36):
                    ep=episode(rng,mode); p,n,e=infer(ep,g); old_i=ep['before'].find(ep['old'])
                    vals.append({'accuracy':p is not None and p[0]==ep['after'],'wrong':p is not None and p[0]!=ep['after'],'null':p is None,'candidates':n,'entropy_bits':e,'exact_state_boundary':p is not None and (p[2],p[3])==(old_i,old_i+len(ep['old'])),'value_recall':p is not None and p[4]==ep['new']})
                raw[str(seed)][method][mode]={k:statistics.mean(float(v[k]) for v in vals) for k in vals[0]}; raw[str(seed)][method][mode]['inference_ms']=(time.perf_counter()-t0)*1000/len(vals)
    summary={}
    for method in methods:
        summary[method]={}
        for mode in MODES: summary[method][mode]={k:statistics.mean(raw[str(seed)][method][mode][k] for seed in (1,7,19)) for k in raw['1'][method][mode]}
        for k in ('grammar','model_bytes','training_seconds','description_bits','selective_roles'):summary[method][k]=statistics.mean(raw[str(seed)][method][k] for seed in (1,7,19))
    return {'cycle':41,'hypothesis':'Deletion-Causal Role Grammar from Minimal Predictive Sufficiency Sets','seeds':[1,7,19],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'co-segmentation O(NL), lesion audit O(P2^R), inference O(GL^2V)','fixed_ontology_or_handwritten_slots_used_by_model':False,'final_after_future_used_for_ranking':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}

if __name__=='__main__': print(json.dumps(run(),ensure_ascii=False,indent=2))
