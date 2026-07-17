from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

from .sparc_open_textbook_learner import OpenTextbookLearner

DIGITS = "〇一二三四五六七八九"
RELATIONS = {
    "tax": ["{a}は{b}の一種である。", "分類上、{a}は{b}に含まれる。", "{b}に属するものとして{a}が知られる。", "{a}の分類先は{b}である。"],
    "loc": ["{a}は{b}に位置する。", "{a}が置かれている場所は{b}である。", "{b}の中に{a}がある。", "{a}の所在地は{b}である。"],
    "part": ["{a}は{b}を構成する部分である。", "{b}の一部として{a}が存在する。", "{a}が属する全体は{b}である。", "{a}は{b}の構成要素である。"],
    "need": ["{a}には{b}が必要である。", "{a}を成立させるには{b}を要する。", "{b}は{a}の必要条件である。", "{a}が必要とするものは{b}である。"],
    "cause": ["{a}は{b}を引き起こす。", "{a}の結果として{b}が生じる。", "{b}の原因の一つは{a}である。", "{a}によって{b}が発生する。"],
    "use": ["{a}は{b}を利用する。", "{a}が使用するものは{b}である。", "{b}は{a}によって使われる。", "{a}の利用対象は{b}である。"],
    "produce": ["{a}は{b}を生成する。", "{a}から{b}が作られる。", "{b}の生成元は{a}である。", "{a}が生み出すものは{b}である。"],
}
QUERIES = {
    "tax": {"direct": ["{a}の分類は何ですか。", "{a}は何に属しますか。"], "closure": ["{a}の最上位分類は何ですか。", "{a}をたどった最終分類は何ですか。"]},
    "loc": {"direct": ["{a}の所在地はどこですか。", "{a}はどこにありますか。"], "closure": ["{a}を最終的に含む場所はどこですか。", "{a}の上位所在地はどこですか。"]},
    "part": {"direct": ["{a}が属する全体は何ですか。", "{a}は何の部分ですか。"], "closure": ["{a}を含む最上位の全体は何ですか。"]},
    "need": {"direct": ["{a}に必要なものは何ですか。", "{a}の必要条件は何ですか。"], "closure": ["{a}が間接的に必要とするものは何ですか。"]},
    "cause": {"direct": ["{a}が引き起こすものは何ですか。", "{a}の結果は何ですか。"], "closure": ["{a}が最終的に生じさせるものは何ですか。"]},
    "use": {"direct": ["{a}が利用するものは何ですか。", "{a}の利用対象は何ですか。"], "closure": ["{a}が分類を通じて利用するものは何ですか。"]},
    "produce": {"direct": ["{a}が生成するものは何ですか。", "{a}の生成物は何ですか。"], "closure": ["{a}が分類を通じて生成するものは何ですか。"]},
}
PREFIXES = {
    "tax": ("分類対象", "分類群"), "loc": ("施設対象", "所在地"),
    "part": ("部品対象", "全体構造"), "need": ("工程対象", "必要資源"),
    "cause": ("現象対象", "発生結果"), "use": ("装置対象", "利用資源"),
    "produce": ("生産対象", "生成物"),
}
BRIDGE = {"tax": (0,3,2), "loc": (0,3,2), "part": (0,3,1), "need": (0,3,2), "cause": (0,3,2), "use": (0,3,2), "produce": (0,3,2)}


def jpnum(value: int) -> str:
    return "".join(DIGITS[int(char)] for char in f"{value:03d}")


def name(relation: str, side: int, value: int) -> str:
    return PREFIXES[relation][side] + jpnum(value)


def paragraph(relation: str, first: str, second: str, forms=(0,1,2)) -> str:
    return "".join(RELATIONS[relation][index].format(a=first, b=second) for index in forms)


def plain(text: str) -> None:
    assert "「" not in text and "」" not in text and " " not in text and "\t" not in text


def base_training():
    records = []
    expected = []
    for relation in ("tax", "loc", "part", "need", "cause"):
        for index in range(12):
            first, second = name(relation,0,index), name(relation,1,index)
            text, source = paragraph(relation,first,second), f"{relation}-direct-{index:02d}"
            plain(text); records.append((text,source)); expected.append((first,second,source))
    rule_specs = (("tax","tax","tax"),("loc","loc","loc"),("part","loc","loc"),("tax","need","need"))
    chains = []
    for rule_index,(left,right,head) in enumerate(rule_specs):
        for index in range(8):
            suffix = jpnum(rule_index*20+index)
            first,middle,last = "連鎖始点"+suffix,"連鎖中間"+suffix,"連鎖終点"+suffix
            for relation,subject,obj,source in ((left,first,middle,f"規則{rule_index}-{index}-左"),(right,middle,last,f"規則{rule_index}-{index}-右"),(head,first,last,f"規則{rule_index}-{index}-頭")):
                text=paragraph(relation,subject,obj); plain(text); records.append((text,source)); expected.append((subject,obj,source))
            chains.append((left,right,head,first,middle,last))
    for relation in ("tax","loc","part","need","cause"):
        first,second=PREFIXES[relation][0]+"橋渡し",PREFIXES[relation][1]+"橋値"
        text=paragraph(relation,first,second,BRIDGE[relation]); plain(text)
        source=f"{relation}-surface-bridge"; records.append((text,source)); expected.append((first,second,source))
    return records,expected,chains


def train_queries(model, chains) -> None:
    for relation in ("tax","loc","part","need","cause"):
        first,second=name(relation,0,0),name(relation,1,0)
        for surface in QUERIES[relation]["direct"]:
            question=surface.format(a=first); plain(question); assert model.learn_question(question,second,"direct")
    for relation in ("tax","loc","need"):
        _,_,_,first,_,last=next(row for row in chains if row[2]==relation)
        for surface in QUERIES[relation]["closure"]:
            question=surface.format(a=first); plain(question); assert model.learn_question(question,last,"closure")


def evaluate(model, question, value, sources, proof_length) -> bool:
    answer=model.ask(question)
    return answer.value==value and answer.sources==tuple(sorted(sources)) and len(answer.proof)==proof_length


def run_gate(output_dir: Path) -> dict[str,object]:
    started=time.perf_counter(); model=OpenTextbookLearner()
    records,expected,chains=base_training(); model.learn_paragraphs(records)
    boundary_exact=sum(any(s==first and o==second and source in sources for (s,_,o),sources in model.facts.items()) for first,second,source in expected)
    base_relations=len(model.relation_patterns); model.induce_rules(min_support=6); base_rules=len(model.rules); train_queries(model,chains)

    direct_cases=[]; direct_correct=0
    for relation in ("tax","loc","part","need","cause"):
        for index in range(20):
            suffix=jpnum(index); first="評価"+PREFIXES[relation][0]+suffix; second="評価"+PREFIXES[relation][1]+suffix; source=f"直接-{relation}-{index:02d}"
            sentence=RELATIONS[relation][3].format(a=first,b=second); question=QUERIES[relation]["direct"][1].format(a=first); plain(sentence); plain(question)
            accepted,_=model.read_sentence(sentence,source); passed=accepted and evaluate(model,question,second,(source,),1); direct_correct+=int(passed); direct_cases.append((question,second,(source,),1))

    two_cases=[]; two_correct=0
    for rule_index,(left,right,head) in enumerate((("tax","tax","tax"),("loc","loc","loc"),("part","loc","loc"),("tax","need","need"))):
        for index in range(20):
            suffix=jpnum(rule_index*30+index); first,middle,last="二資料始点"+suffix,"二資料中間"+suffix,"二資料終点"+suffix; sources=(f"二資料-{rule_index}-{index}-左",f"二資料-{rule_index}-{index}-右")
            assert model.read_sentence(RELATIONS[left][3].format(a=first,b=middle),sources[0])[0]; assert model.read_sentence(RELATIONS[right][3].format(a=middle,b=last),sources[1])[0]
            question=QUERIES[head]["closure"][0].format(a=first); passed=evaluate(model,question,last,sources,2); two_correct+=int(passed); two_cases.append((question,last,tuple(sorted(sources)),2))

    three_cases=[]; three_correct=0
    for relation in ("tax","loc"):
        for index in range(20):
            suffix=jpnum(index); first="三資料始点"+relation+suffix; middle1="三資料中間甲"+relation+suffix; middle2="三資料中間乙"+relation+suffix; last="三資料終点"+relation+suffix; sources=tuple(f"三資料-{relation}-{index}-{part}" for part in range(3))
            for subject,obj,source in ((first,middle1,sources[0]),(middle1,middle2,sources[1]),(middle2,last,sources[2])): assert model.read_sentence(RELATIONS[relation][3].format(a=subject,b=obj),source)[0]
            question=QUERIES[relation]["closure"][1].format(a=first); passed=evaluate(model,question,last,sources,3); three_correct+=int(passed); three_cases.append((question,last,tuple(sorted(sources)),3))

    base_bytes=len(model.to_bytes()); additional=[]
    for relation in ("use","produce"):
        for index in range(10): additional.append((paragraph(relation,name(relation,0,index),name(relation,1,index)),f"追加-{relation}-{index:02d}"))
        additional.append((paragraph(relation,PREFIXES[relation][0]+"橋渡し",PREFIXES[relation][1]+"橋値",BRIDGE[relation]),f"追加-{relation}-橋"))
    new_chains=[]
    for index in range(8):
        suffix=jpnum(index); first,middle,last="追加規則始点"+suffix,"追加規則中間"+suffix,"追加規則終点"+suffix
        additional.extend(((paragraph("tax",first,middle),f"追加規則-{index}-左"),(paragraph("use",middle,last),f"追加規則-{index}-右"),(paragraph("use",first,last),f"追加規則-{index}-頭"))); new_chains.append((first,middle,last))
    for text,_ in additional: plain(text)
    model.learn_paragraphs(additional); model.induce_rules(min_support=6,preserve_existing=True); expanded_relations=len(model.relation_patterns); expanded_rules=len(model.rules)
    for relation in ("use","produce"):
        first,second=name(relation,0,0),name(relation,1,0)
        for surface in QUERIES[relation]["direct"]: assert model.learn_question(surface.format(a=first),second,"direct")
    first,_,last=new_chains[0]; assert model.learn_question(QUERIES["use"]["closure"][0].format(a=first),last,"closure")

    new_direct=0
    for relation in ("use","produce"):
        for index in range(20):
            suffix=jpnum(index); first="新評価"+PREFIXES[relation][0]+suffix; second="新評価"+PREFIXES[relation][1]+suffix; source=f"新直接-{relation}-{index:02d}"
            accepted,_=model.read_sentence(RELATIONS[relation][3].format(a=first,b=second),source); new_direct+=int(accepted and evaluate(model,QUERIES[relation]["direct"][1].format(a=first),second,(source,),1))
    new_rule=0
    for index in range(30):
        suffix=jpnum(index); first,middle,last="新規則評価始点"+suffix,"新規則評価中間"+suffix,"新規則評価終点"+suffix; sources=(f"新規則評価-{index}-左",f"新規則評価-{index}-右")
        assert model.read_sentence(RELATIONS["tax"][3].format(a=first,b=middle),sources[0])[0]; assert model.read_sentence(RELATIONS["use"][3].format(a=middle,b=last),sources[1])[0]
        new_rule+=int(evaluate(model,QUERIES["use"]["closure"][0].format(a=first),last,sources,2))

    old_direct=sum(evaluate(model,*case) for case in direct_cases); old_reasoning=sum(evaluate(model,*case) for case in two_cases+three_cases)
    before=(len(model.facts),len(model.entities),len(model.relation_patterns)); unknown_relations=sum(not model.read_sentence(f"未知主体{jpnum(index)}は未知値{jpnum(index)}を祝福する。",f"未知資料-{index}")[0] for index in range(3)); after=(len(model.facts),len(model.entities),len(model.relation_patterns))
    unknown_questions=sum(model.ask(f"評価分類対象〇〇〇の色彩的な印象を説明してください{jpnum(index)}。").value is None for index in range(3))
    restored=OpenTextbookLearner.from_bytes(model.to_bytes()); restore_cases=direct_cases[:10]+two_cases[:10]; restore_exact=sum(evaluate(restored,*case) for case in restore_cases)
    wall=time.perf_counter()-started; peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024; learner=model.report()
    checks={
        "plain_japanese_without_quotes":True,"base_boundary_exact":boundary_exact==len(expected),"base_relations":base_relations==5,"base_rules":base_rules==4,
        "direct_questions":direct_correct==100,"two_source_questions":two_correct==80,"three_source_questions":three_correct==40,
        "expanded_relations":expanded_relations==7,"expanded_rules":expanded_rules==5,"new_direct_questions":new_direct==40,"new_cross_rule_questions":new_rule==30,
        "old_direct_nonregression":old_direct==100,"old_reasoning_nonregression":old_reasoning==120,"unknown_relations_abstain":unknown_relations==3,
        "unknown_relation_preserves_graph":before==after,"unknown_questions_abstain":unknown_questions==3,"restore_exact":restore_exact==20,
        "model_under_128_kib":learner["serialized_bytes"]<=131072,"bounded_wall_time":wall<=10.0,"bounded_peak_memory":peak<=536870912,
        "no_quote_bootstrap":learner["quoted_entity_bootstrap_used"] is False,"no_supplied_boundaries":learner["entity_boundaries_supplied"] is False,
        "no_relation_names":learner["relation_names_supplied"] is False,"no_fixed_inventory":learner["fixed_relation_inventory_supplied"] is False,
        "no_word_tokenizer":learner["whitespace_tokenizer_used"] is False,"no_morphological_dictionary":learner["morphological_dictionary_used"] is False,
    }
    report={"experiment":"SPARC-open-textbook-001","passed":all(checks.values()),"checks":checks,
        "base":{"training_paragraphs":len(records),"boundary_exact":boundary_exact,"boundary_total":len(expected),"latent_relations":base_relations,"rules":base_rules,"direct_correct":direct_correct,"two_source_correct":two_correct,"three_source_correct":three_correct,"serialized_bytes":base_bytes},
        "continual":{"additional_paragraphs":len(additional),"latent_relations":expanded_relations,"rules":expanded_rules,"new_direct_correct":new_direct,"new_rule_correct":new_rule,"old_direct_after":old_direct,"old_reasoning_after":old_reasoning},
        "safety":{"unknown_relation_abstentions":unknown_relations,"unknown_question_abstentions":unknown_questions,"graph_preserved":before==after,"restore_exact":restore_exact},
        "resources":{"serialized_bytes":learner["serialized_bytes"],"peak_rss_bytes":peak,"wall_seconds":wall,"max_candidates":model.last_candidates,"last_feature_reads":model.last_feature_reads},
        "learner":learner,"claim_boundary":"Generated Japanese paragraphs still repeat one fact in several sentences. This is not unrestricted textbook reading or high-school-level intelligence."}
    output_dir.mkdir(parents=True,exist_ok=True); (output_dir/"SPARC-open-textbook-001.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8"); (output_dir/"SPARC-open-textbook-001.model.zlib").write_bytes(model.to_bytes())
    (output_dir/"SPARC-open-textbook-001.md").write_text("\n".join(["# SPARC open textbook 001","",f"- passed: {report['passed']}",f"- entity boundaries: {boundary_exact}/{len(expected)}",f"- latent relations: {base_relations} -> {expanded_relations}",f"- learned rules: {base_rules} -> {expanded_rules}",f"- direct: {direct_correct}/100",f"- two-source: {two_correct}/80",f"- three-source: {three_correct}/40",f"- new direct: {new_direct}/40",f"- new cross-rule: {new_rule}/30",f"- model bytes: {learner['serialized_bytes']}",f"- peak RSS: {peak}",f"- wall seconds: {wall:.3f}","","No quotation-mark entity bootstrap, word tokenizer, morphology dictionary, relation labels, supplied entity spans, or fixed relation inventory were used."])+"\n",encoding="utf-8")
    return report


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--output-dir",type=Path,required=True); args=parser.parse_args(); report=run_gate(args.output_dir); print(json.dumps(report,ensure_ascii=False,indent=2))
    if not report["passed"]: raise SystemExit(1)


if __name__=="__main__": main()
