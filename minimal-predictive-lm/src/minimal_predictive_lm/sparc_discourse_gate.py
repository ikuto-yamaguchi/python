from __future__ import annotations
import argparse,json,resource,time
from pathlib import Path
from .sparc_discourse_learner import DiscourseTextbookLearner
from .sparc_open_textbook_gate import RELATIONS,QUERIES,base_training,train_queries,jpnum,name

def run_gate(output_dir:Path):
    started=time.perf_counter(); model=DiscourseTextbookLearner()
    records,_,chains=base_training(); model.learn_paragraphs(records); model.induce_rules(min_support=6); train_queries(model,chains)
    old_probes=[]
    for rel in ("tax","loc","part","need","cause"):
        s,o=name(rel,0,0),name(rel,1,0); old_probes.append((QUERIES[rel]["direct"][0].format(a=s),o))
    before_bytes=len(model.to_bytes()); accepted=resolved=correct=0; max_candidates=max_reads=0
    for rel in ("tax","loc"):
        marker="分類群" if rel=="tax" else "地域"
        for i in range(50):
            x=jpnum(i); a=f"単発始点{rel}{x}"; b=f"単発中間甲{rel}{x}"; c=f"単発中間乙{rel}{x}"; d=f"単発終点{rel}{x}"
            text=RELATIONS[rel][3].format(a=a,b=b)+f"この{marker}は{c}"+("の一種である。" if rel=="tax" else "に位置する。")+f"この{marker}は{d}"+("の一種である。" if rel=="tax" else "に位置する。")
            read=model.read_document(text,f"doc-{rel}-{i:02d}"); accepted+=read.accepted; resolved+=read.resolved_anaphors
            q=QUERIES[rel]["closure"][0].format(a=a); ans=model.ask(q)
            expected=tuple(f"doc-{rel}-{i:02d}#s{j}" for j in (1,2,3))
            correct+=int(ans.value==d and ans.sources==expected and len(ans.proof)==3)
            max_candidates=max(max_candidates,model.last_candidates); max_reads=max(max_reads,model.last_feature_reads)
    old_retained=sum(model.ask(q).value==v for q,v in old_probes)
    facts_before=len(model.facts); unknown=model.read_document("未知概念は不可思議に共鳴する。この現象は無限へ跳躍する。","unknown")
    unknown_preserved=(facts_before==len(model.facts) and unknown.accepted==0)
    blob=model.to_bytes(); restored=DiscourseTextbookLearner.from_bytes(blob)
    restore_correct=0
    for rel in ("tax","loc"):
        for i in range(5):
            x=jpnum(i); a=f"単発始点{rel}{x}"; d=f"単発終点{rel}{x}"
            restore_correct+=int(restored.ask(QUERIES[rel]["closure"][0].format(a=a)).value==d)
    elapsed=time.perf_counter()-started; peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    checks={"single_exposure_sentences":accepted==300,"anaphor_resolution":resolved==200,"three_hop_questions":correct==100,"old_knowledge_retained":old_retained==5,"unknown_abstention_non_mutating":unknown_preserved,"save_restore":restore_correct==10,"bounded_discourse_state":model.max_focus_slots==1,"serialized_bytes":len(blob)<=30000,"peak_memory":peak<=64*1024*1024,"wall_time":elapsed<=3.0,"candidate_bound":max_candidates<=12,"feature_read_bound":max_reads<=1200}
    report={"passed":all(checks.values()),"checks":checks,"metrics":{"accepted_single_exposure":accepted,"resolved_anaphors":resolved,"three_hop_correct":correct,"old_probes_retained":old_retained,"restore_correct":restore_correct,"seed_serialized_bytes":before_bytes,"serialized_bytes":len(blob),"peak_rss_bytes":peak,"wall_seconds":elapsed,"max_candidates":max_candidates,"max_feature_reads":max_reads},"model":model.report(),"claim_boundary":"Relation templates still require redundant seed prose. New facts and discourse chains are each presented once; this is not unrestricted textbook understanding or high-school-level intelligence."}
    output_dir.mkdir(parents=True,exist_ok=True); (output_dir/"SPARC-discourse-textbook-002.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)); (output_dir/"SPARC-discourse-textbook-002.model.zlib").write_bytes(blob)
    return report

def main():
    p=argparse.ArgumentParser(); p.add_argument("--output-dir",type=Path,required=True); a=p.parse_args(); r=run_gate(a.output_dir); print(json.dumps(r,ensure_ascii=False,indent=2)); raise SystemExit(0 if r["passed"] else 1)
if __name__=="__main__":main()
