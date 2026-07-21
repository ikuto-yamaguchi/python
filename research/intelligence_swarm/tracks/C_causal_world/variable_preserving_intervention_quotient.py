from pathlib import Path

import difflib,json,random,resource,time,statistics,re,sys
from dataclasses import dataclass,asdict
ENT=["アルファ","ベータ","ガンマ","デルタ","未知甲","未知乙"]; LOC=["棚A","棚B","棚C","棚D","箱1","箱2"]
FR=[("{e}は{o}にある。","{e}を{n}へ移す。","{e}は{n}にある。"),("現在、{e}の場所は{o}。","{e}の置き場を{n}に変更。","現在、{e}の場所は{n}。"),("{o}に{e}が置かれている。","{e}を{n}に置き直す。","{n}に{e}が置かれている。")]
PAR=[("{e}は{o}にある。","{n}へ{e}を運んで。","{e}は{n}にある。"),("現在、{e}の場所は{o}。","{e}を{n}の方へ動かして。","現在、{e}の場所は{n}。")]
def mk(seed,n,frames=FR,conf=False,ents=None,locs=None):
 r=random.Random(seed); out=[]; ents=ents or ENT[:4]; locs=locs or LOC[:4]
 for _ in range(n):
  e=r.choice(ents); o,nw=r.sample(locs,2); f=r.choice(frames); out.append(tuple(x.format(e=e,o=o,n=nw) for x in f))
 if conf:
  for _ in range(max(2,n//8)):
   e=r.choice(ents); o,nw=r.sample(locs,2); out.append((f"{e}は{o}にある。",f"{e}を{nw}へ移す。",f"{e}は{o}にある。"))
 return out
def diff(a,b):
 ds=[];ins=[];eq=[]
 for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,a,b).get_opcodes():
  if t=="equal": eq.append(a[i1:i2])
  elif t=="replace": ds.append(a[i1:i2]);ins.append(b[j1:j2])
  elif t=="delete": ds.append(a[i1:i2])
  elif t=="insert": ins.append(b[j1:j2])
 return ds,ins,eq
def induce(b,c,a):
 ds,ins,eq=diff(b,a); old=[x for x in ds if x]; new=[x for x in ins if x and x in c]; anc=[b[i:i+n] for i,j,n in difflib.SequenceMatcher(None,b,c).get_matching_blocks() if n>=2]
 if len(old)!=1 or len(new)!=1:return None
 o,n=old[0],new[0]
 bsk=b.replace(o,"<OLD>"); csk=c.replace(n,"<NEW>")
 for x in sorted(anc,key=len,reverse=True):
  bsk=bsk.replace(x,"<ID>"); csk=csk.replace(x,"<ID>")
 return bsk+"|||"+csk
def match_one(sk,s):
 p=re.escape(sk)
 for m in ("ID","OLD","NEW"): p=p.replace(re.escape(f"<{m}>"),f"(?P<{m}>.+?)")
 m=re.fullmatch(p,s); return m.groupdict() if m else None
def match(sk,b,c):
 bsk,csk=sk.split("|||",1); gb=match_one(bsk,b); gc=match_one(csk,c)
 if not gb or not gc:return None
 if gb.get("ID") and gc.get("ID") and gb["ID"]!=gc["ID"]:return None
 return {**gb,**gc}
class Surface:
 def fit(self,x):self.x=list(x)
 def pred(self,b,c):
  z=max(self.x,key=lambda r:difflib.SequenceMatcher(None,c,r[1]).ratio());return z[2],len(self.x)
 def size(self):return len(json.dumps(self.x,ensure_ascii=False).encode())
class Quot:
 def fit(self,x):
  self.rules={};self.conf=set()
  for b,c,a in x:
   sk=induce(b,c,a)
   if not sk:continue
   nochange=(b==a)
   if sk in self.rules and self.rules[sk]!=nochange:self.conf.add(sk)
   self.rules[sk]=nochange
 def pred(self,b,c):
  outs=[]
  for sk in self.rules:
   g=match(sk,b,c)
   if g and sk not in self.conf and not self.rules[sk] and g.get("OLD") in b: outs.append(b.replace(g["OLD"],g["NEW"],1))
  return (outs[0] if len(set(outs))==1 else None),len(self.rules)
 def size(self):return len(json.dumps({"r":self.rules,"c":list(self.conf)},ensure_ascii=False).encode())
def ev(m,data):
 ok=ab=0;ts=[];rd=[]
 for b,c,a in data:
  t=time.perf_counter();p,r=m.pred(b,c);ts.append((time.perf_counter()-t)*1000);rd.append(r);ok+=p==a;ab+=p is None
 return ok/len(data),ab/len(data),statistics.mean(ts),statistics.mean(rd)
def comp(m,seed,n=60):
 r=random.Random(seed);ok=0
 for _ in range(n):
  e=r.choice(ENT[4:]);a,b,c=r.sample(LOC[:4],3);cur=f"{e}は{a}にある。"
  for cmd in (f"{e}を{b}へ移す。",f"{e}を{c}へ移す。"):
   cur,_=m.pred(cur,cmd)
   if cur is None:break
  ok+=cur==f"{e}は{c}にある。"
 return ok/n
@dataclass
class Row:
 method:str;seed:int;examples:int;normal:float;rename:float;paraphrase:float;confound_abstain:float;composition:float;model_bytes:int;peak_rss_kib:int;train_s:float;infer_ms:float;candidate_reads:float;rules:int
def one(method,seed,n):
 m=Surface() if method=="surface" else Quot(); t=time.perf_counter();m.fit(mk(seed,n));tr=time.perf_counter()-t
 normal=ev(m,mk(seed+10,80)); ren=ev(m,mk(seed+20,80,[FR[0]],ents=ENT[4:],locs=LOC[:4])); para=ev(m,mk(seed+30,80,PAR))
 cm=Surface() if method=="surface" else Quot();cm.fit(mk(seed,n,conf=True)); conf=ev(cm,mk(seed+40,80,[FR[0]]))
 rules=len(m.x) if method=="surface" else len(m.rules)
 return Row(method,seed,n,normal[0],ren[0],para[0],conf[1],comp(m,seed+50),m.size(),resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,tr,normal[2],normal[3],rules)
def run(path):
 rows=[one(m,s,n) for n in (32,128,512) for s in (1,7,19) for m in ("surface","quotient")]
 agg={}
 for m in ("surface","quotient"):
  agg[m]={}
  for n in (32,128,512):
   rr=[x for x in rows if x.method==m and x.examples==n]
   agg[m][str(n)]={k:statistics.mean(getattr(x,k) for x in rr) for k in ("normal","rename","paraphrase","confound_abstain","composition","model_bytes","peak_rss_kib","train_s","infer_ms","candidate_reads","rules")}
 out={"hypothesis":"Variable-preserving intervention quotient","claim":{"completion":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False},"aggregate":agg,"runs":[asdict(x) for x in rows]}
 Path(path).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8");return out
if __name__=="__main__":print(json.dumps(run(sys.argv[1])["aggregate"],ensure_ascii=False,indent=2))
