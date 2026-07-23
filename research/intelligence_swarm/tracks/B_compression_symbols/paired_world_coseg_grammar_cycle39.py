import random,time,pickle,resource,json,statistics
OBJECTS=["青い箱","赤い箱","北の鍵","南の鍵","試料甲","試料乙"]
VALUES=["棚A","棚B","棚C","棚D","待機","完了"]
MODES=["seen","word_order","lexeme","rename","alternate","nested","omitted","paragraph"]
def shape(s): return ''.join('J' if ord(c)>127 and c not in '。、\n「」' else c for c in s)
def episode(rng,mode):
    o=rng.choice(OBJECTS); v0=rng.choice(VALUES); v1=rng.choice([x for x in VALUES if x!=v0])
    surf=o.replace("箱","ケース") if mode=="rename" else o
    before=f"{surf}の現在値は{v0}です。補助記録は維持します。"
    if mode=="word_order": cmd=f"{v1}へ変更してください、対象は{surf}です。"
    elif mode=="lexeme": cmd=f"{surf}を次から{v1}扱いにします。"
    elif mode=="alternate": before=f"状態報告：{surf}={v0}。補助記録は維持。"; cmd=f"{surf}を{v1}へ。"
    elif mode=="nested": cmd=f"依頼は「{surf}を{v1}へ変更」です。"
    elif mode=="omitted": cmd=f"それを{v1}へ変更してください。"
    elif mode=="paragraph": cmd=f"前段は維持。\n{surf}を{v1}へ変更してください。\n後段も維持。"
    else: cmd=f"{surf}を{v1}へ変更してください。"
    after=before.replace(v0,v1,1)
    return dict(before=before,command=cmd,after=after,obj=surf,old=v0,new=v1,mode=mode)
def diffrange(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return (l,len(a)-r,l,len(b)-r)
def allspans(s,maxlen=10):
    return [(i,j,s[i:j]) for i in range(len(s)) for j in range(i+1,min(len(s),i+maxlen)+1)]
def paired_world(ep):
    cands=[x for x in allspans(ep["command"],8) if x[2] not in ep["before"]]
    if not cands: return None
    i,j,x=max(cands,key=lambda z:len(z[2]))
    alt="別値候補"
    return dict(before=ep["before"],command=ep["command"][:i]+alt+ep["command"][j:],changed=(i,j),token=x)
def proposals(ep,pair):
    dr=diffrange(ep["before"],ep["after"]); out=[]
    for si,sj,ss in allspans(ep["before"],10):
      for ci,cj,cs in allspans(ep["command"],10):
        if abs(si-dr[0])<=2 and (pair is None or abs(ci-pair["changed"][0])<=3): out.append((si,sj,ci,cj,shape(ss),shape(cs)))
    return out[:64]
def train(seed,method):
    rng=random.Random(seed); eps=[episode(rng,random.choice(MODES[:4])) for _ in range(60)]
    t=time.perf_counter(); prods=[]
    for ep in eps:
      pw=paired_world(ep); ps=proposals(ep,pw)
      if method=="factorized": prods+=ps[:2]
      elif method=="coseg": prods += [p for p in ps if pw and abs(p[2]-pw["changed"][0])<=1][:2]
      elif method=="strict": prods += [p for p in ps if pw and abs(p[2]-pw["changed"][0])==0 and p[1]-p[0]<=8][:2]
      elif method=="shuffle":
        if pw: pw["changed"]=(len(ep["command"])//2,len(ep["command"])//2+1)
        prods += [p for p in ps if pw and abs(p[2]-pw["changed"][0])<=1][:2]
    classes={}
    for p in prods: classes[(p[4],p[5],p[1]-p[0],p[3]-p[2])]=classes.get((p[4],p[5],p[1]-p[0],p[3]-p[2]),0)+1
    grammar=sorted(classes.items(),key=lambda x:x[1],reverse=True)[:32]
    return grammar,time.perf_counter()-t
def infer(ep,grammar):
    vals=[s for _,_,s in allspans(ep["command"],8) if s not in ep["before"]]; cands=[]
    for (stsh,csh,sw,cw),support in grammar:
      for si,sj,ss in allspans(ep["before"],10):
       if sj-si==sw and shape(ss)==stsh:
        for v in vals: cands.append((ep["before"][:si]+v+ep["before"][sj:],support,si,sj,v))
    if not cands:return None,len(cands)
    cands.sort(key=lambda x:x[1],reverse=True)
    if len(cands)>1 and cands[0][1]==cands[1][1]: return None,len(cands)
    return cands[0],len(cands)
def run():
  raw={}
  for seed in (1,7,19):
    raw[str(seed)]={}
    for m in ("factorized","coseg","strict","shuffle"):
      g,tr=train(seed,m); raw[str(seed)][m]={"grammar":len(g),"model_bytes":len(pickle.dumps(g)),"training_seconds":tr}
      for mode in MODES:
       rng=random.Random(seed*100+MODES.index(mode)); rows=[]; t=time.perf_counter()
       for _ in range(30):
        ep=episode(rng,mode); p,n=infer(ep,g); rows.append((p is not None and p[0]==ep["after"],p is not None and p[0]!=ep["after"],p is None,n))
       raw[str(seed)][m][mode]={"accuracy":statistics.mean(x[0] for x in rows),"wrong":statistics.mean(x[1] for x in rows),"null":statistics.mean(x[2] for x in rows),"candidates":statistics.mean(x[3] for x in rows),"inference_ms":(time.perf_counter()-t)*1000/30}
  summary={}
  for m in ("factorized","coseg","strict","shuffle"):
   summary[m]={}
   for mode in MODES: summary[m][mode]={k:statistics.mean(raw[str(s)][m][mode][k] for s in (1,7,19)) for k in ("accuracy","wrong","null","candidates","inference_ms")}
   summary[m]["grammar"]=statistics.mean(raw[str(s)][m]["grammar"] for s in (1,7,19)); summary[m]["model_bytes"]=statistics.mean(raw[str(s)][m]["model_bytes"] for s in (1,7,19)); summary[m]["training_seconds"]=statistics.mean(raw[str(s)][m]["training_seconds"] for s in (1,7,19))
  return {"cycle":39,"hypothesis":"Co-Segmentation Grammar Birth from Paired Disagreement Worlds","summary":summary,"raw":raw,"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"paired segmentation O(NL^2), quotient O(P log P), inference O(GL^2V)","highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
if __name__=="__main__": print(json.dumps(run(),ensure_ascii=False,indent=2))
