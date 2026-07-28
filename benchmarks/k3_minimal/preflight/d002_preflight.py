import argparse, hashlib, json, math, os, platform, resource, sys, tempfile, time
from dataclasses import asdict, dataclass
from pathlib import Path
import torch
import torch.nn as nn
import torch.nn.functional as F

@dataclass(frozen=True)
class Config:
    vocab_size:int=151936; hidden_size:int=512; num_layers:int=12; num_heads:int=8; num_kv_heads:int=4
    intermediate_size:int=1536; num_blocks:int=4; rms_eps:float=1e-6; recency_bias:float=3.0

class RMSNorm(nn.Module):
    def __init__(self,d,eps=1e-6): super().__init__(); self.weight=nn.Parameter(torch.ones(d)); self.eps=eps
    def forward(self,x): return x * torch.rsqrt(x.float().pow(2).mean(-1,keepdim=True)+self.eps).to(x.dtype) * self.weight

class Attention(nn.Module):
    def __init__(self,c):
        super().__init__(); d=c.hidden_size; self.h=c.num_heads; self.kv=c.num_kv_heads; self.hd=d//self.h
        self.q_proj=nn.Linear(d,d,bias=False); self.k_proj=nn.Linear(d,self.kv*self.hd,bias=False); self.v_proj=nn.Linear(d,self.kv*self.hd,bias=False); self.o_proj=nn.Linear(d,d,bias=False)
        self.q_norm=RMSNorm(self.hd,c.rms_eps); self.k_norm=RMSNorm(self.hd,c.rms_eps)
    def forward(self,x):
        b,t,d=x.shape; q=self.q_proj(x).view(b,t,self.h,self.hd).transpose(1,2); k=self.k_proj(x).view(b,t,self.kv,self.hd).transpose(1,2); v=self.v_proj(x).view(b,t,self.kv,self.hd).transpose(1,2)
        q=self.q_norm(q); k=self.k_norm(k)
        if self.kv != self.h:
            r=self.h//self.kv; k=k.repeat_interleave(r,1); v=v.repeat_interleave(r,1)
        y=F.scaled_dot_product_attention(q,k,v,is_causal=True); return self.o_proj(y.transpose(1,2).contiguous().view(b,t,d))

class MLP(nn.Module):
    def __init__(self,c): super().__init__(); d=c.hidden_size;i=c.intermediate_size; self.gate_proj=nn.Linear(d,i,bias=False); self.up_proj=nn.Linear(d,i,bias=False); self.down_proj=nn.Linear(i,d,bias=False)
    def forward(self,x): return self.down_proj(F.silu(self.gate_proj(x))*self.up_proj(x))

def route(blocks, partial, proj, norm, bias, trace=None):
    t0=time.perf_counter_ns(); V=torch.stack(blocks+[partial],0); t1=time.perf_counter_ns(); K=norm(V); q=proj.weight.view(-1); logits=torch.einsum('d,nbtd->nbt',q,K); logits[-1]=logits[-1]+bias; t2=time.perf_counter_ns(); w=logits.softmax(0); t3=time.perf_counter_ns(); h=torch.einsum('nbt,nbtd->btd',w,V); t4=time.perf_counter_ns()
    if trace is not None:
        trace.append({'sources':len(blocks)+1,'shape':list(V.shape),'stride':list(V.stride()),'contiguous':V.is_contiguous(),'dtype':str(V.dtype),'layout_ns':t1-t0,'norm_score_ns':t2-t1,'softmax_ns':t3-t2,'mix_ns':t4-t3,'full_ns':t4-t0,'temporary_bytes':V.numel()*V.element_size()+K.numel()*K.element_size()+logits.numel()*logits.element_size()+w.numel()*w.element_size()})
    return h

class Layer(nn.Module):
    def __init__(self,c,idx,attnres):
        super().__init__(); self.idx=idx; self.lpb=max(1,(c.num_layers+c.num_blocks-1)//c.num_blocks); self.attn=Attention(c); self.mlp=MLP(c); self.in_norm=RMSNorm(c.hidden_size,c.rms_eps); self.post_norm=RMSNorm(c.hidden_size,c.rms_eps); self.attnres=attnres
        if attnres:
            self.attn_res_proj=nn.Linear(c.hidden_size,1,bias=False); self.attn_res_norm=RMSNorm(c.hidden_size,c.rms_eps); self.attn_res_bias=nn.Parameter(torch.tensor(c.recency_bias)); self.mlp_res_proj=nn.Linear(c.hidden_size,1,bias=False); self.mlp_res_norm=RMSNorm(c.hidden_size,c.rms_eps); self.mlp_res_bias=nn.Parameter(torch.tensor(c.recency_bias))
    @property
    def new_block(self): return self.idx>0 and self.idx%self.lpb==0
    def forward(self,blocks,partial,trace):
        if self.attnres:
            h=route(blocks,partial,self.attn_res_proj,self.attn_res_norm,self.attn_res_bias,trace)
            if self.new_block: blocks=blocks+[partial]; partial=torch.zeros_like(partial)
            partial=partial+self.attn(self.in_norm(h)); h=route(blocks,partial,self.mlp_res_proj,self.mlp_res_norm,self.mlp_res_bias,trace); partial=partial+self.mlp(self.post_norm(h)); return blocks,partial
        x=partial; x=x+self.attn(self.in_norm(x)); x=x+self.mlp(self.post_norm(x)); return blocks,x

class Model(nn.Module):
    def __init__(self,c,attnres):
        super().__init__(); self.c=c; self.attnres=attnres; self.embed=nn.Embedding(c.vocab_size,c.hidden_size); self.layers=nn.ModuleList([Layer(c,i,attnres) for i in range(c.num_layers)]); self.norm=RMSNorm(c.hidden_size,c.rms_eps)
        if attnres: self.final_res_proj=nn.Linear(c.hidden_size,1,bias=False); self.final_res_norm=RMSNorm(c.hidden_size,c.rms_eps); self.final_res_bias=nn.Parameter(torch.tensor(c.recency_bias))
        self.lm_head=nn.Linear(c.hidden_size,c.vocab_size,bias=False); self.lm_head.weight=self.embed.weight
    def forward(self,ids,trace=None):
        x=self.embed(ids); blocks=[x]; partial=x
        for l in self.layers: blocks,partial=l(blocks,partial,trace)
        if self.attnres: partial=route(blocks,partial,self.final_res_proj,self.final_res_norm,self.final_res_bias,trace)
        return self.lm_head(self.norm(partial))

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def tensor_sha(t): return sha_bytes(t.detach().cpu().contiguous().numpy().tobytes())
def pcount(m): return sum(p.numel() for p in m.parameters())
def model_bytes(m): return sum(p.numel()*p.element_size() for p in m.parameters())
def routing_names(m): return [n for n,_ in m.named_parameters() if any(s in n for s in ['attn_res_','mlp_res_','final_res_'])]

def run_one(c,attnres,outdir,ids):
    torch.manual_seed(17); trace=[]; t0=time.perf_counter(); m=Model(c,attnres); inst=time.perf_counter()-t0
    names={n:list(p.shape) for n,p in m.named_parameters()}; before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    m.train(); t1=time.perf_counter(); logits=m(ids,trace); loss=logits.float().pow(2).mean(); loss.backward(); wall=time.perf_counter()-t1
    grads={n:{'finite':bool(torch.isfinite(p.grad).all()) if p.grad is not None else False,'nonzero':bool((p.grad!=0).any()) if p.grad is not None else False,'norm':float(p.grad.float().norm()) if p.grad is not None else None} for n,p in m.named_parameters() if n in routing_names(m)}
    outsha=tensor_sha(logits); ck=outdir/('a1.pt' if attnres else 'b0.pt'); torch.save(m.state_dict(),ck); file_sha=sha_bytes(ck.read_bytes()); ref=logits.detach().clone(); del logits; del loss
    m2=Model(c,attnres); m2.load_state_dict(torch.load(ck,map_location='cpu',weights_only=True)); m2.eval();
    with torch.no_grad(): post=m2(ids)
    maxdiff=float((ref-post).abs().max()); postsha=tensor_sha(post)
    return {'condition':'A1' if attnres else 'B0','params':pcount(m),'model_bytes_fp32':model_bytes(m),'instantiate_s':inst,'forward_backward_s':wall,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'peak_rss_delta_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss-before,'loss':float((ref.float().pow(2).mean())),'output_sha256':outsha,'postload_output_sha256':postsha,'checkpoint_sha256':file_sha,'save_load_max_abs_diff':maxdiff,'routing_gradients':grads,'routing_trace':trace,'parameter_shapes':names}

def bench_route(c):
    rows=[]; torch.manual_seed(17); proj=nn.Linear(c.hidden_size,1,bias=False); norm=RMSNorm(c.hidden_size); bias=nn.Parameter(torch.tensor(3.0))
    for seq in [1,128,512,2048]:
        blocks=[torch.randn(1,seq,c.hidden_size) for _ in range(4)]; partial=torch.randn(1,seq,c.hidden_size)
        for _ in range(2): route(blocks,partial,proj,norm,bias)
        ts=[]
        for _ in range(5): t=time.perf_counter_ns(); route(blocks,partial,proj,norm,bias); ts.append(time.perf_counter_ns()-t)
        rows.append({'batch':1,'seq':seq,'sources':5,'median_ns':sorted(ts)[len(ts)//2],'all_ns':ts})
    return rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    torch.set_num_threads(1); c=Config(); g=torch.Generator().manual_seed(17); ids=torch.randint(0,c.vocab_size,(1,4),generator=g); input_sha=tensor_sha(ids)
    result={'schema':'D002-v1','environment':{'python':sys.version,'torch':torch.__version__,'platform':platform.platform(),'threads':torch.get_num_threads(),'cuda_available':torch.cuda.is_available()},'config':asdict(c),'input_shape':list(ids.shape),'input_sha256':input_sha,'candidate_source_sha256':'649aa0067e5b9d0fc2a3cc68784a6794090a26a4','runs':[]}
    for ar in [False,True]: result['runs'].append(run_one(c,ar,out,ids))
    b0,a1=result['runs']; bn=set(b0['parameter_shapes']); an=set(a1['parameter_shapes']); result['parameter_name_diff']={'only_a1':sorted(an-bn),'only_b0':sorted(bn-an)}; result['param_delta']=a1['params']-b0['params']; result['routing_microbench']=bench_route(c)
    expected_b0=115554304; expected_old_a1=115578904; expected_candidate_a1=115579929
    allgr=all(v['finite'] and v['nonzero'] for v in a1['routing_gradients'].values()); only_declared=all(any(x in n for x in ['attn_res_','mlp_res_','final_res_']) for n in result['parameter_name_diff']['only_a1']) and not result['parameter_name_diff']['only_b0']
    status='PASS' if b0['params']==expected_b0 and a1['params']==expected_candidate_a1 and allgr and a1['save_load_max_abs_diff']<=1e-6 and only_declared else 'STOP'
    result['decision']={'path_status':status,'expected_b0':expected_b0,'previous_static_a1':expected_old_a1,'corrected_candidate_a1':expected_candidate_a1,'all_routing_gradients_finite_nonzero':allgr,'residual_only_parameter_diff':only_declared,'note':'D001 omitted final_res_proj/final_res_norm/final_res_bias (1025 params).'}
    raw=json.dumps(result,indent=2,sort_keys=True); (out/'D002_result.json').write_text(raw); (out/'D002_result.sha256').write_text(sha_bytes(raw.encode())+'  D002_result.json\n'); print(json.dumps({'decision':result['decision'],'b0_params':b0['params'],'a1_params':a1['params'],'param_delta':result['param_delta'],'b0_wall':b0['forward_backward_s'],'a1_wall':a1['forward_backward_s'],'result_sha':sha_bytes(raw.encode())},indent=2))
if __name__=='__main__': main()
