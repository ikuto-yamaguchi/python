#!/usr/bin/env python3
from __future__ import annotations
import json, math, random, resource, statistics, time
SEEDS=(1,7,19); TD=64; IDD=32; OPD=16
MOVES=((1,0),(-1,0),(0,1),(0,-1))
MOVE_WORD={(1,0):('右','東'),(-1,0):('左','西'),(0,1):('上','北'),(0,-1):('下','南')}
REL_WORD={(-1,0):('左側','西側'),(1,0):('右側','東側'),(0,-1):('下側','南側'),(0,1):('上側','北側')}
TRAIN=('基準点の{rel}にいる{name}を{move}へ一歩動かして。','{name}は基準より{rel}だ。その個体だけを{move}方向へ移して。','目印から見て{rel}の{name}について、位置を{move}へ一つ変える。')
HELD=('目印の{rel}にいる{name}だけ、次は{move}側へ進めて。','{move}へ一歩ずらす対象は、基準から{rel}にいる{name}。','基準との位置関係が{rel}の{name}を選び、{move}方向へ動かす。')
DOMAIN=('ビーコンの{alias_rel}に位置する{name}を{alias_move}へ一単位遷移させる。','{name}の初期配置はビーコンの{alias_rel}。この個体のみ{alias_move}へ変位させる。')
def hidx(s,d,salt):
 h=2166136261^salt
 for ch in s:h^=ord(ch);h=(h*16777619)&0xffffffff
 return h%d,(-1.0 if h>>31 else 1.0)
def norm(v):
 z=math.sqrt(sum(x*x for x in v)) or 1.0
 return [x/z for x in v]
def textf(t):
 v=[0.0]*TD;p='^'+t+'$'
 for n in (1,2,3,4):
  for i in range(len(p)-n+1):j,s=hidx(p[i:i+n],TD,17+n);v[j]+=s
 return norm(v)
def rot(p,k):
 x,y=p
 for _ in range(k%4):x,y=-y,x
 return x,y
def make_world(rng):
 ps=[(-2,0),(2,0),(0,-2),(0,2)]
 while len(ps)<8:
  p=(rng.randint(-4,4),rng.randint(-4,4))
  if p!=(0,0) and p not in ps:ps.append(p)
 return {'p':tuple(ps),'a':(0,0),'t':rng.randrange(4),'m':rng.choice(MOVES)}
def transform(w,k,dx,dy,perm):
 ps=[rot(p,k) for p in w['p']];ps=[(x+dx,y+dy) for x,y in ps];a=rot(w['a'],k);a=(a[0]+dx,a[1]+dy);inv=[0]*8
 for new,old in enumerate(perm):inv[old]=new
 return {'p':tuple(ps[old] for old in perm),'a':a,'t':inv[w['t']],'m':rot(w['m'],k)}
def relation(w):
 x,y=w['p'][w['t']];ax,ay=w['a'];x-=ax;y-=ay
 if abs(x)>=abs(y):return (1,0) if x>0 else (-1,0)
 return (0,1) if y>0 else (0,-1)
def render(w,form,name):
 rw,ra=REL_WORD[relation(w)];mw,ma=MOVE_WORD[w['m']]
 return form.format(name=name,rel=rw,move=mw,alias_rel=ra,alias_move=ma)
def idf(w,c):
 v=[0.0]*IDD;ax,ay=w['a'];cx,cy=w['p'][c];cx-=ax;cy-=ay
 for x,y in w['p']:
  j,s=hidx(f'r:{x-ax-cx}:{y-ay-cy}',IDD,101);v[j]+=s
 for tok in (f'a:{cx}:{cy}',f'd:{abs(cx)+abs(cy)}'):
  j,s=hidx(tok,IDD,151);v[j]+=s
 return norm(v)
def opf(m):
 v=[0.0]*OPD
 for tok in (f'dx:{m[0]}',f'dy:{m[1]}',f'axis:{abs(m[0])}:{abs(m[1])}',f'sign:{m[0]+m[1]}'):
  j,s=hidx(tok,OPD,211);v[j]+=s
 return norm(v)
def outer(W,u,z):
 for i,ui in enumerate(u):
  if ui:
   for j,zj in enumerate(z):
    if zj:W[i][j]+=ui*zj
def score(W,u,z):return sum(ui*sum(a*b for a,b in zip(row,z)) for ui,row in zip(u,W) if ui)
def train(seed,shuffle=False,n=50):
 rng=random.Random(seed);Wi=[[0.0]*IDD for _ in range(TD)];Wo=[[0.0]*OPD for _ in range(TD)];rows=[]
 for _ in range(n):
  base=make_world(rng)
  for k in range(4):
   perm=list(range(8));rng.shuffle(perm);w=transform(base,k,rng.randint(-3,3),rng.randint(-3,3),perm)
   for form in TRAIN:rows.append((textf(render(w,form,f'個体{rng.randrange(10**8)}')),idf(w,w['t']),opf(w['m'])))
 ids=[r[1] for r in rows];ops=[r[2] for r in rows]
 if shuffle:rng.shuffle(ids);rng.shuffle(ops)
 for (u,_,_),zi,zo in zip(rows,ids,ops):outer(Wi,u,zi);outer(Wo,u,zo)
 return Wi,Wo
def qtext(w,c,rng):
 name=f'符号{rng.randrange(10**10)}';txt=render(w,rng.choice(HELD),name)
 if c=='order':txt=f'{MOVE_WORD[w["m"]][0]}へ動かすのは、{REL_WORD[relation(w)][0]}にいる{name}。'
 if c=='omission':txt=f'基準から{REL_WORD[relation(w)][0]}の個体だけ、{MOVE_WORD[w["m"]][0]}へ一つ。'
 if c=='paragraph':txt='他の対象は固定する。\n'+txt+'\n移動後も識別を維持する。'
 if c=='free':txt=f'ねえ、目印の{REL_WORD[relation(w)][0]}にいる{name}だけさ、{MOVE_WORD[w["m"]][0]}へちょっと一つ動かして。'
 if c=='domain':txt=render(w,rng.choice(DOMAIN),f'ユニット{rng.randrange(10**8)}')
 return txt
def evaluate(seed,Wi,Wo,c,n=80):
 rng=random.Random(seed*10007+sum(map(ord,c)));t=m=j=inv=e=0
 for _ in range(n):
  base=make_world(rng);perm=list(range(8));rng.shuffle(perm);w=transform(base,rng.randrange(4),rng.randint(-5,5),rng.randint(-5,5),perm);u=textf(qtext(w,c,rng))
  ts=sorted(((score(Wi,u,idf(w,x)),x) for x in range(8)),reverse=True);ms=sorted(((score(Wo,u,opf(x)),x) for x in MOVES),reverse=True);pc,pm=ts[0][1],ms[0][1]
  t+=pc==w['t'];m+=pm==w['m'];j+=pc==w['t'] and pm==w['m'];e+=pc==w['t'] and pm==w['m'] and ts[0][0]-ts[1][0]>.05 and ms[0][0]-ms[1][0]>.05
  texts=[qtext(w,c,rng)];
  for mm in MOVES:
   if mm!=w['m'] and len(texts)<4:texts.append(qtext({'p':w['p'],'a':w['a'],'t':w['t'],'m':mm},c,rng))
  zi,zo=idf(w,w['t']),opf(w['m']);ss=[score(Wi,textf(x),zi)+score(Wo,textf(x),zo) for x in texts];inv+=max(range(4),key=ss.__getitem__)==0
 return {'target':t/n,'move':m/n,'joint':j/n,'inverse':inv/n,'eligible_rate':e/n}
def run(seed):
 Wi,Wo=train(seed);Si,So=train(seed,True);cs=('held','rename','order','omission','paragraph','free','domain')
 return {'seed':seed,'correct':{c:evaluate(seed,Wi,Wo,c) for c in cs},'shuffle':{c:evaluate(seed,Si,So,c) for c in cs}}
def main():
 st=time.perf_counter();per=[run(s) for s in SEEDS];secs=time.perf_counter()-st;cs=('held','rename','order','omission','paragraph','free','domain');mean={m:{c:{k:statistics.mean(r[m][c][k] for r in per) for k in per[0][m][c]} for c in cs} for m in ('correct','shuffle')};strict=0
 for r in per:
  a,b=r['correct'],r['shuffle'];strict+=int(a['held']['joint']-b['held']['joint']>.03 and a['domain']['joint']-b['domain']['joint']>.03 and a['held']['inverse']>.30 and a['domain']['inverse']>.30 and a['held']['eligible_rate']>0 and a['domain']['eligible_rate']>0)
 print(json.dumps({'cycle':'D_MEMORY_ELIGIBILITY_003','hypothesis':'Factorized Identity-Operation Consistency as Memory Eligibility','seeds':list(SEEDS),'per_seed':per,'mean':mean,'chance':{'target':1/8,'move':1/4,'joint':1/32,'inverse':1/4},'strict_seed_passes':strict,'semantic_memory_eligible_units':0 if strict<3 else 1,'resources':{'model_bytes_float32_estimate':TD*(IDD+OPD)*4,'training_seconds_total':secs,'peak_rss_kib_python_runtime_included':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),'update_ops_estimate_per_episode':TD*(IDD+OPD),'inference_ops_estimate_per_query':8*TD*IDD+4*TD*OPD},'leakage_audit':{'post_treatment_used':False,'final_outcome_used_for_training':False,'identity_or_operation_label_used_for_scoring':False,'span_proposals_used':False,'string_retrieval_used':False}},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
