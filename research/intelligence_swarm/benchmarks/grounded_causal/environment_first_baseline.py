from __future__ import annotations
import argparse, json, os, random, resource, statistics, time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

@dataclass
class Config:
    state_dim: int
    num_actions: int
    vocab_size: int
    hidden_dim: int = 64
    action_dim: int = 24
    text_dim: int = 48
    batch_size: int = 64
    env_epochs: int = 20
    lang_epochs: int = 20
    lr: float = 3e-3
    freeze_decoder: bool = True

class Rows(Dataset):
    def __init__(self, rows: list[dict[str, Any]], vocab: dict[str,int], max_len: int=40):
        self.rows=rows; self.vocab=vocab; self.max_len=max_len
    def __len__(self): return len(self.rows)
    def __getitem__(self,i):
        r=self.rows[i]
        ids=[self.vocab.get(ch,1) for ch in r.get('utterance','')[:self.max_len]]
        ids += [0]*(self.max_len-len(ids))
        return {'before':torch.tensor(r['state_before'],dtype=torch.float32),'after':torch.tensor(r['state_after'],dtype=torch.float32),'action':torch.tensor(r['action'],dtype=torch.long),'text':torch.tensor(ids,dtype=torch.long),'mask':torch.tensor([1.0 if x else 0.0 for x in ids],dtype=torch.float32),'entity_holdout':bool(r.get('entity_holdout',False)),'dynamics_holdout':bool(r.get('dynamics_holdout',False)),'language_holdout':bool(r.get('language_holdout',False))}

class TransitionEncoder(nn.Module):
    def __init__(self,c): super().__init__(); self.net=nn.Sequential(nn.Linear(c.state_dim*2,c.hidden_dim),nn.Tanh(),nn.Linear(c.hidden_dim,c.action_dim))
    def forward(self,s,sp): return self.net(torch.cat([s,sp],-1))
class Decoder(nn.Module):
    def __init__(self,c): super().__init__(); self.state=nn.Sequential(nn.Linear(c.state_dim+c.action_dim,c.hidden_dim),nn.ReLU(),nn.Linear(c.hidden_dim,c.state_dim)); self.action=nn.Linear(c.action_dim,c.num_actions)
    def forward(self,s,z): return self.state(torch.cat([s,z],-1)),self.action(z)
class LanguageEncoder(nn.Module):
    def __init__(self,c): super().__init__(); self.emb=nn.Embedding(c.vocab_size,c.text_dim,padding_idx=0); self.gru=nn.GRU(c.text_dim,c.hidden_dim,batch_first=True); self.out=nn.Linear(c.hidden_dim,c.action_dim)
    def forward(self,x,mask): _,h=self.gru(self.emb(x)); return self.out(h[-1])
class E2E(nn.Module):
    def __init__(self,c): super().__init__(); self.lang=LanguageEncoder(c); self.dec=Decoder(c)
    def forward(self,s,x,m): return self.dec(s,self.lang(x,m))

def build_vocab(rows):
    chars=sorted({ch for r in rows if r.get('split')=='train' for ch in r.get('utterance','')}); return {'<pad>':0,'<unk>':1,**{c:i+2 for i,c in enumerate(chars)}}
def seed_all(s): random.seed(s); torch.manual_seed(s); torch.set_num_threads(1)
def loss_fn(sp_hat,a_hat,b): return nn.functional.mse_loss(sp_hat,b['after'])+nn.functional.cross_entropy(a_hat,b['action'])
def train_env(enc,dec,loader,c):
    opt=torch.optim.Adam(list(enc.parameters())+list(dec.parameters()),lr=c.lr); t=time.perf_counter()
    for _ in range(c.env_epochs):
        for b in loader:
            sh,ah=dec(b['before'],enc(b['before'],b['after'])); loss=loss_fn(sh,ah,b); opt.zero_grad(); loss.backward(); opt.step()
    return time.perf_counter()-t
def train_language(lang,dec,loader,c):
    if c.freeze_decoder:
        for p in dec.parameters(): p.requires_grad=False
    opt=torch.optim.Adam([p for p in list(lang.parameters())+list(dec.parameters()) if p.requires_grad],lr=c.lr); t=time.perf_counter()
    for _ in range(c.lang_epochs):
        for b in loader:
            sh,ah=dec(b['before'],lang(b['text'],b['mask'])); loss=loss_fn(sh,ah,b); opt.zero_grad(); loss.backward(); opt.step()
    return time.perf_counter()-t
def train_e2e(model,loader,c):
    opt=torch.optim.Adam(model.parameters(),lr=c.lr); t=time.perf_counter()
    for _ in range(c.lang_epochs):
        for b in loader:
            sh,ah=model(b['before'],b['text'],b['mask']); loss=loss_fn(sh,ah,b); opt.zero_grad(); loss.backward(); opt.step()
    return time.perf_counter()-t

def evaluate(method,model,loader,condition='correct'):
    if method=='e2e': model.eval()
    else: model[0].eval(); model[1].eval()
    n=act=success=0; mse=0.; buckets={k:[0,0] for k in ('entity','dynamics','language')}; lat=[]
    with torch.no_grad():
        for b in loader:
            text=b['text'].clone()
            if condition=='language_blind': text.zero_()
            elif condition=='language_shuffle': text=text[torch.randperm(text.shape[0])]
            st=time.perf_counter_ns()
            if method=='e2e': sh,ah=model(b['before'],text,b['mask'])
            else: lang,dec=model; sh,ah=dec(b['before'],lang(text,b['mask']))
            lat.append((time.perf_counter_ns()-st)/1e6/len(text)); pred=ah.argmax(-1); ok=pred.eq(b['action']); act+=ok.sum().item(); n+=len(text); mse+=nn.functional.mse_loss(sh,b['after'],reduction='sum').item(); success+=((sh-b['after']).abs().mean(-1)<0.25).logical_and(ok).sum().item()
            for key,field in [('entity','entity_holdout'),('dynamics','dynamics_holdout'),('language','language_holdout')]:
                mask=b[field].bool(); buckets[key][0]+=ok[mask].sum().item(); buckets[key][1]+=mask.sum().item()
    dim=len(loader.dataset.rows[0]['state_after'])
    return {'task_success':success/n,'action_accuracy':act/n,'next_state_mse':mse/(n*dim),'cpu_inference_ms_per_item':statistics.mean(lat),'heldout':{k:(a/b if b else None) for k,(a,b) in buckets.items()}}
def bytes_model(m): return sum(p.numel()*p.element_size() for p in m.parameters())
def load_rows(p): return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--out',required=True); ap.add_argument('--seed',type=int,default=1); ap.add_argument('--hidden-dim',type=int,default=64); ap.add_argument('--action-dim',type=int,default=24); ap.add_argument('--env-epochs',type=int,default=20); ap.add_argument('--lang-epochs',type=int,default=20); args=ap.parse_args(); seed_all(args.seed)
    rows=load_rows(args.data); train=[r for r in rows if r['split']=='train']; test=[r for r in rows if r['split']=='test']; vocab=build_vocab(rows)
    c=Config(state_dim=len(train[0]['state_before']),num_actions=max(r['action'] for r in rows)+1,vocab_size=len(vocab),hidden_dim=args.hidden_dim,action_dim=args.action_dim,env_epochs=args.env_epochs,lang_epochs=args.lang_epochs)
    tr=DataLoader(Rows(train,vocab),batch_size=c.batch_size,shuffle=True); te=DataLoader(Rows(test,vocab),batch_size=c.batch_size)
    enc,dec,lang=TransitionEncoder(c),Decoder(c),LanguageEncoder(c); env_t=train_env(enc,dec,tr,c); lang_t=train_language(lang,dec,tr,c)
    ef={x:evaluate('ef',(lang,dec),te,x) for x in ('correct','language_blind','language_shuffle')}
    seed_all(args.seed); e2e=E2E(c); e2e_t=train_e2e(e2e,tr,c); ee={x:evaluate('e2e',e2e,te,x) for x in ('correct','language_blind','language_shuffle')}
    result={'status':'smoke_test_not_public_silg_reproduction','seed':args.seed,'config':asdict(c),'n_train':len(train),'n_test':len(test),'vocab_size':len(vocab),'environment_first':{'env_pretrain_seconds':env_t,'language_train_seconds':lang_t,'model_bytes':bytes_model(enc)+bytes_model(dec)+bytes_model(lang),'metrics':ef},'end_to_end':{'train_seconds':e2e_t,'model_bytes':bytes_model(e2e),'metrics':ee},'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'torch_version':torch.__version__,'python':os.sys.version}
    Path(args.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)); print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
