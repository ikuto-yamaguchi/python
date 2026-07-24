import numpy as np, json, time, resource, pickle
SEEDS=[1,7,19]
DOMAINS={
'd1':{'obj':['青箱','赤箱','緑箱','白箱'],'op':['右へ','左へ','上へ','下へ'],'goal':['近づけ','離せ']},
'd2':{'obj':['甲器','乙器','丙器','丁器'],'op':['東寄せ','西寄せ','北寄せ','南寄せ'],'goal':['接近','分離']},
'd3':{'obj':['ナロ','ミケ','フサ','トネ'],'op':['ルク','セパ','ゴニ','ハル'],'goal':['ヴァ','ネオ']},
}
DIRS=np.array([[1,0],[-1,0],[0,1],[0,-1]],float)

def feat(text,dim=256):
    v=np.zeros(dim); b=text.encode('utf-8')
    for n in (2,3,4):
        for i in range(max(0,len(b)-n+1)):
            h=2166136261
            for x in b[i:i+n]: h=(h^x)*16777619 & 0xffffffff
            v[h%dim]+=1
    return v/(np.linalg.norm(v)+1e-9)

def utter(dom,obj_i,op_i,goal_i,style):
    d=DOMAINS[dom]; o=d['obj'][obj_i%4]; op=d['op'][op_i]; g=d['goal'][goal_i]
    forms=[f'{o}を{op}動かし、基準へ{g}。',f'基準へ{g}ように、{o}は{op}。',f'前段は維持。\n{o}を{op}。目的は{g}。',f'依頼は「{o}を{op}」で、狙いは{g}。']
    return forms[style%4]

def apply(w,target,op):
    z=w.copy(); z[target]+=DIRS[op]; return z

def episode(dom,rng,style=None):
    w=rng.uniform(-2,2,(6,2)); t=int(rng.integers(0,4)); op=int(rng.integers(0,4)); g=int(rng.integers(0,2)); style=int(rng.integers(0,4)) if style is None else style
    return {'dom':dom,'w':w,'target':t,'op':op,'goal':g,'style':style,'u':utter(dom,t,op,g,style),'after':apply(w,t,op)}

def variants(ep,rng):
    out=[]
    for kind in range(4):
        q=dict(ep)
        if kind==0:q['target']=(ep['target']+1)%4
        if kind==1:q['op']=(ep['op']+1)%4
        if kind==2:q['goal']=1-ep['goal']
        if kind==3:q['style']=(ep['style']+1)%4
        q['u']=utter(ep['dom'],q['target'],q['op'],q['goal'],q['style']); q['after']=apply(ep['w'],q['target'],q['op']); out.append(q)
    return out

def joint_delta(ep,q):
    return np.concatenate([feat(q['u'])-feat(ep['u']),(q['after']-ep['after']).reshape(-1)])

def train(seed,language_shuffle=False,global_axis=False):
    rng=np.random.default_rng(seed); pairs=[]
    for dom in ('d1','d2'):
        for _ in range(48):
            ep=episode(dom,rng); vs=variants(ep,rng)
            if language_shuffle:rng.shuffle(vs)
            pairs.extend((ep,q) for q in vs)
    t0=time.perf_counter(); X=[]
    for ep,q in pairs:
        x=joint_delta(ep,q); X.append(x/(np.linalg.norm(x)+1e-9))
    X=np.array(X)
    if global_axis: centers=np.array([X.mean(0)])
    else:
        centers=[X[0]]
        for _ in range(11):
            sims=np.max(np.stack([X@c for c in centers],1),1); centers.append(X[np.argmin(sims)])
        centers=np.array(centers)
        for _ in range(5):
            a=np.argmax(X@centers.T,1)
            for k in range(len(centers)):
                if np.any(a==k):
                    c=X[a==k].mean(0); centers[k]=c/(np.linalg.norm(c)+1e-9)
    U=np.stack([feat(ep['u']) for ep,_ in pairs]); A=np.argmax(X@centers.T,1); W=np.zeros((256,len(centers)))
    for u,a in zip(U,A):W[:,a]+=u
    W/=np.maximum(1,np.bincount(A,minlength=len(centers)))[None,:]
    return {'centers':centers,'W':W},time.perf_counter()-t0

def evaluate(model,seed,dom,style,world_shuffle=False):
    rng=np.random.default_rng(seed+sum(map(ord,dom))+style*37); acc=[]; inv=[]; goal=[]; repair=[]; C=model['centers']; W=model['W']
    for _ in range(24):
        ep=episode(dom,rng,style); sq=feat(ep['u'])@W; vals=[]
        for t in range(4):
            for op in range(4):
                for g in range(2):
                    q=dict(ep,target=t,op=op,goal=g,u=utter(dom,t,op,g,style),after=apply(ep['w'],t,op)); x=joint_delta(ep,q)
                    if world_shuffle:x[256:]=np.roll(x[256:],2)
                    x/=np.linalg.norm(x)+1e-9; vals.append((np.max(sq+x@C.T),t,op,g))
        _,t,op,g=max(vals); acc.append(t==ep['target'] and op==ep['op']); goal.append(g==ep['goal'])
        scores=[]
        for oi in range(4):
            q=dict(ep,op=oi,u=utter(dom,ep['target'],oi,ep['goal'],style),after=apply(ep['w'],ep['target'],oi)); x=joint_delta(ep,q); x/=np.linalg.norm(x)+1e-9; scores.append(np.max(sq+x@C.T))
        inv.append(int(np.argmax(scores))==ep['op']); wrong=(ep['op']+1)%4; repair.append(op=={0:1,1:0,2:3,3:2}[wrong])
    return {k:float(np.mean(v)) for k,v in [('joint',acc),('inverse',inv),('goal',goal),('repair',repair)]}

def main():
    raw={}; sizes=[]; trains=[]; t0=time.perf_counter()
    methods=[('local',False,False),('language_shuffle',True,False),('world_shuffle',False,False),('global_lowrank',False,True)]
    for seed in SEEDS:
        raw[str(seed)]={}
        for name,ls,ga in methods:
            m,tr=train(seed,ls,ga); sizes.append(len(pickle.dumps(m))); trains.append(tr); raw[str(seed)][name]={}
            for dom in ('d1','d2','d3'):
                for style,label in [(0,'held'),(1,'word_order'),(2,'paragraph'),(3,'free')]: raw[str(seed)][name][f'{dom}_{label}']=evaluate(m,seed,dom,style,name=='world_shuffle')
    summary={name:{key:{metric:float(np.mean([raw[str(s)][name][key][metric] for s in SEEDS])) for metric in ('joint','inverse','goal','repair')} for key in raw['1'][name]} for name,_,_ in methods}
    print(json.dumps({'cycle':5,'hypothesis':'Locally Competing Commutator Squares from Single-Factor Surprise Splits','seeds':SEEDS,'summary':summary,'raw':raw,'model_bytes_mean':float(np.mean(sizes)),'train_seconds_mean':float(np.mean(trains)),'runtime_seconds':time.perf_counter()-t0,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'candidate_count':32,'estimated_ops_train_per_pair':3200,'estimated_ops_inference_per_query':122880,'answer_leakage':False,'post_treatment_test_input':False,'fixed_codebook':False,'highschool_level_passed':False,'weak_smartphone_verified':False,'completion':False},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
