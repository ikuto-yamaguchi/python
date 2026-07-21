from __future__ import annotations
import argparse, io, json, random, resource, statistics, time
from dataclasses import dataclass, asdict
from pathlib import Path
import torch
from torch import nn
import torch.nn.functional as F

torch.set_num_threads(1)
TOKENS=['<pad>','<bos>','<eos>','記録','更新','質問','回答','は','の','色','数','規則','。','？','+','=','葵','蓮','凛','空','海','森','赤','青','緑','白','黒','黄','0','1','2','3','4','5','6','7','8','9','雑音','静か','速い','丸い']
T={x:i for i,x in enumerate(TOKENS)}; PAD=T['<pad>']
NAMES=['葵','蓮','凛','空','海','森']; COLORS=['赤','青','緑','白','黒','黄']; NOISE=['静か','速い','丸い']

def enc(xs): return [T[x] for x in xs]

def make_example(rng, task, depth, held_out):
    xs=['<bos>']
    if task=='overwrite':
        names=rng.sample(NAMES,4); vals=rng.sample(COLORS,4); st=dict(zip(names,vals))
        for n in names: xs += ['記録',n,'は',st[n],'。']
        for _ in range(depth):
            if rng.random()<.8:
                n=rng.choice(names); v=rng.choice(COLORS); st[n]=v; xs += ['更新',n,'は',v,'。']
            else: xs += ['雑音',rng.choice(NOISE),'。']
        q=rng.choice(names); xs += ['質問',q,'の','色','は','？','回答',st[q],'<eos>']
    elif task=='multiquery':
        names=rng.sample(NAMES,4); vals=rng.sample(COLORS,4); st=dict(zip(names,vals))
        for n in names: xs += ['記録',n,'は',st[n],'。']
        for _ in range(depth):
            n=rng.choice(names); v=rng.choice(COLORS); st[n]=v; xs += ['更新',n,'は',v,'。']
        q1,q2=rng.sample(names,2); xs += ['質問',q1,'の','色','は','？','回答',st[q1],'。','質問',q2,'の','色','は','？','回答',st[q2],'<eos>']
    else:
        a=rng.randrange(10); c=a
        xs += ['記録','数',str(a),'。']
        for _ in range(depth):
            d=rng.randrange(10); c=(c+d)%10; xs += ['更新','+',str(d),'。']
        xs += ['質問','数','は','？','回答',str(c),'<eos>']
    ids=enc(xs); answer_positions=[i for i,x in enumerate(xs) if x=='回答']
    return ids, answer_positions

class DS(torch.utils.data.Dataset):
    def __init__(self,n,seed,task,depth,held=False):
        r=random.Random(seed); self.x=[make_example(r,task,depth,held) for _ in range(n)]
    def __len__(self): return len(self.x)
    def __getitem__(self,i): return self.x[i]

def collate(batch):
    L=max(len(x) for x,_ in batch); inp=torch.full((len(batch),L-1),PAD,dtype=torch.long); tgt=torch.full_like(inp,-100); ans=[]
    for i,(x,apos) in enumerate(batch):
        z=torch.tensor(x); inp[i,:len(x)-1]=z[:-1]; tgt[i,:len(x)-1]=z[1:]; ans.append(apos)
    return inp,tgt,ans

class GRULM(nn.Module):
    def __init__(self,v,d=32):
        super().__init__(); self.e=nn.Embedding(v,d); self.r=nn.GRU(d,d,batch_first=True); self.h=nn.Linear(d,v,bias=False); self.h.weight=self.e.weight
    def forward(self,x): y,_=self.r(self.e(x)); return self.h(y)
    def state_elems(self): return self.r.hidden_size

class TransformerLM(nn.Module):
    def __init__(self,v,d=32):
        super().__init__(); self.e=nn.Embedding(v,d); self.p=nn.Embedding(256,d); layer=nn.TransformerEncoderLayer(d,4,64,batch_first=True); self.m=nn.TransformerEncoder(layer,1); self.h=nn.Linear(d,v,bias=False); self.h.weight=self.e.weight
    def forward(self,x):
        L=x.size(1); z=self.e(x)+self.p(torch.arange(L,device=x.device)); mask=torch.triu(torch.ones(L,L,device=x.device,dtype=torch.bool),1); return self.h(self.m(z,mask=mask))
    def state_elems(self): return 0

class SimpleSSM(nn.Module):
    def __init__(self,v,d=32):
        super().__init__(); self.e=nn.Embedding(v,d); self.A=nn.Parameter(torch.linspace(-3,-.1,d)); self.B=nn.Linear(d,d); self.C=nn.Linear(d,d); self.g=nn.Linear(d,d); self.h=nn.Linear(d,v,bias=False); self.h.weight=self.e.weight
    def forward(self,x):
        e=self.e(x); s=torch.zeros(x.size(0),e.size(-1),device=x.device); ys=[]
        for t in range(x.size(1)):
            u=e[:,t]; a=torch.exp(self.A).clamp(max=.999); s=a*s+torch.sigmoid(self.g(u))*self.B(u); ys.append(self.C(s)+u)
        return self.h(torch.stack(ys,1))
    def state_elems(self): return self.A.numel()

class DeltaNet(nn.Module):
    def __init__(self,v,d=32,h=4):
        super().__init__(); self.e=nn.Embedding(v,d); self.hn=h; self.n=d//h; self.q=nn.Linear(d,d); self.k=nn.Linear(d,d); self.v=nn.Linear(d,d); self.beta=nn.Linear(d,h); self.o=nn.Linear(d,d); self.head=nn.Linear(d,v,bias=False); self.head.weight=self.e.weight
    def forward(self,x):
        e=self.e(x); B=e.size(0); S=torch.zeros(B,self.hn,self.n,self.n,device=x.device); ys=[]
        for t in range(x.size(1)):
            u=e[:,t]; q=self.q(u).view(B,self.hn,self.n); k=F.normalize(self.k(u).view(B,self.hn,self.n),dim=-1); v=self.v(u).view(B,self.hn,self.n); b=torch.sigmoid(self.beta(u)).view(B,self.hn,1)
            pred=(S@k.unsqueeze(-1)).squeeze(-1); err=v-pred; S=S+b.unsqueeze(-1)*err.unsqueeze(-1)*k.unsqueeze(-2); y=(S@q.unsqueeze(-1)).squeeze(-1).reshape(B,-1); ys.append(self.o(y)+u)
        return self.head(torch.stack(ys,1))
    def state_elems(self): return self.hn*self.n*self.n

class RWKVLite(nn.Module):
    def __init__(self,v,d=32,h=4):
        super().__init__(); self.e=nn.Embedding(v,d); self.hn=h; self.n=d//h; self.r=nn.Linear(d,d); self.k=nn.Linear(d,d); self.v=nn.Linear(d,d); self.w=nn.Linear(d,d); self.a=nn.Linear(d,d); self.o=nn.Linear(d,d); self.head=nn.Linear(d,v,bias=False); self.head.weight=self.e.weight
    def forward(self,x):
        e=self.e(x); B=e.size(0); S=torch.zeros(B,self.hn,self.n,self.n,device=x.device); ys=[]
        for t in range(x.size(1)):
            u=e[:,t]; r=self.r(u).view(B,self.hn,self.n); k=self.k(u).view(B,self.hn,self.n); v=self.v(u).view(B,self.hn,self.n); kk=F.normalize(k,dim=-1); a=torch.sigmoid(self.a(u)).view(B,self.hn,self.n); w=torch.exp(-F.softplus(self.w(u))).view(B,self.hn,1,self.n)
            ab=(-kk).unsqueeze(-1)@(kk*a).unsqueeze(-2); S=S*w+S@ab+v.unsqueeze(-1)*k.unsqueeze(-2); y=(S@r.unsqueeze(-1)).squeeze(-1).reshape(B,-1); ys.append(self.o(y)+u)
        return self.head(torch.stack(ys,1))
    def state_elems(self): return self.hn*self.n*self.n

MODELS={'gru':GRULM,'transformer':TransformerLM,'ssm':SimpleSSM,'deltanet':DeltaNet,'rwkv7':RWKVLite}
@dataclass
class M: arch:str; seed:int; train_n:int; params:int; bytes:int; rss:int; train_s:float; acc:float; long_acc:float; nll:float; latency_ms:float; candidates:int; reads:int

def size(m): b=io.BytesIO(); torch.save(m.state_dict(),b); return b.tell()
def evaluate(m,dl):
    m.eval(); c=n=tok=0; loss=0
    with torch.no_grad():
        for x,y,ans in dl:
            z=m(x); loss+=float(F.cross_entropy(z.reshape(-1,z.size(-1)),y.reshape(-1),ignore_index=-100,reduction='sum')); tok+=int(y.ne(-100).sum())
            for i,apos in enumerate(ans):
                for a in apos:
                    if a<z.size(1): c+=int(z[i,a].argmax()==y[i,a]); n+=1
    return c/max(1,n),loss/max(1,tok)
def latency(m,L=64):
    x=torch.randint(1,len(TOKENS),(1,L)); m.eval()
    with torch.no_grad():
        for _ in range(2): m(x)
        t=time.perf_counter()
        for _ in range(10): m(x)
    return (time.perf_counter()-t)*1000/(10*L)

def train(arch,seed,n,task):
    torch.manual_seed(seed); random.seed(seed); m=MODELS[arch](len(TOKENS),32)
    tr=DS(n,seed*1009+n,task,5); va=DS(128,900000+seed,task,5,True); lo=DS(128,910000+seed,task,20,True)
    dl=torch.utils.data.DataLoader(tr,batch_size=32,shuffle=True,collate_fn=collate,generator=torch.Generator().manual_seed(seed)); vdl=torch.utils.data.DataLoader(va,batch_size=64,collate_fn=collate); ldl=torch.utils.data.DataLoader(lo,batch_size=64,collate_fn=collate)
    opt=torch.optim.AdamW(m.parameters(),lr=3e-3); t=time.perf_counter()
    m.train()
    for x,y,_ in dl:
        opt.zero_grad(); z=m(x); loss=F.cross_entropy(z.reshape(-1,z.size(-1)),y.reshape(-1),ignore_index=-100); loss.backward(); nn.utils.clip_grad_norm_(m.parameters(),1); opt.step()
    ts=time.perf_counter()-t; acc,nll=evaluate(m,vdl); la,_=evaluate(m,ldl)
    return M(arch,seed,n,sum(p.numel() for p in m.parameters()),size(m),resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,ts,acc,la,nll,latency(m),len(TOKENS),m.state_elems())

def run(out):
    rows=[]
    for task in ['overwrite','multiquery','arithmetic']:
        for n in [128,512]:
            for arch in MODELS:
                for seed in [1,7]: rows.append(dict(task=task,**asdict(train(arch,seed,n,task))))
    agg={}
    for task in ['overwrite','multiquery','arithmetic']:
        agg[task]={}
        for arch in MODELS:
            agg[task][arch]={}
            for n in [128,512]:
                xs=[r for r in rows if r['task']==task and r['arch']==arch and r['train_n']==n]
                agg[task][arch][str(n)]={k:statistics.mean(r[k] for r in xs) for k in ['acc','long_acc','nll','train_s','latency_ms']}
                agg[task][arch][str(n)].update(params=max(r['params'] for r in xs),model_bytes=max(r['bytes'] for r in xs),peak_rss_kib=max(r['rss'] for r in xs),candidates=max(r['candidates'] for r in xs),reads=max(r['reads'] for r in xs))
    rep={'claim_scope':{'completion':False,'highschool_level_passed':False,'native_japanese_communication_passed':False},'aggregate':agg,'runs':rows}
    Path(out).parent.mkdir(parents=True,exist_ok=True); Path(out).write_text(json.dumps(rep,ensure_ascii=False,indent=2)); return rep
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output',default='artifacts/broad_architecture_report.json'); a=p.parse_args(); r=run(a.output); print(json.dumps(r['aggregate'],ensure_ascii=False))
