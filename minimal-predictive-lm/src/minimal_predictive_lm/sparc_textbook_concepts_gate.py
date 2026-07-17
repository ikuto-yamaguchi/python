from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import sys
import time

from .sparc_textbook_learner import SparseTextbookLearner

S = {
    "class": (
        "「{a}」は「{b}」の一種である。", "分類上、「{a}」は「{b}」に含まれる。",
        "「{a}」が属する分類は「{b}」だ。",
        "教科書の記述によると、「{a}」は分類上「{b}」の仲間とされる。",
        "要点を言えば、「{a}」は「{b}」に属するものだ。",
    ),
    "located": (
        "「{a}」は「{b}」に位置する。", "「{a}」の所在地は「{b}」である。",
        "地理的に、「{a}」は「{b}」の中にある。",
        "地図上では「{a}」が存在する地域は「{b}」だ。",
        "資料では「{a}」を「{b}」の内部に位置づけている。",
    ),
    "part": (
        "「{a}」は「{b}」の一部である。", "「{b}」を構成する要素の一つが「{a}」だ。",
        "構造上、「{a}」は「{b}」に組み込まれている。",
        "全体との関係では、「{a}」は「{b}」を構成する部分だ。",
        "「{b}」の構成要素として「{a}」が含まれる。",
    ),
    "causes": (
        "「{a}」は「{b}」を引き起こす。", "「{b}」の原因の一つは「{a}」である。",
        "「{a}」の結果として「{b}」が生じる。",
        "因果関係をたどると、「{a}」から「{b}」が発生する。",
        "資料は「{a}」が「{b}」の発生要因だと説明する。",
    ),
    "requires": (
        "「{a}」には「{b}」が必要である。", "「{a}」を行うには「{b}」を要する。",
        "「{b}」は「{a}」の成立条件だ。",
        "成立条件を考えると、「{a}」には「{b}」が欠かせない。",
        "「{a}」を実現する前提として「{b}」が求められる。",
    ),
    "produces": (
        "「{a}」は「{b}」を生成する。", "「{a}」から「{b}」が作られる。",
        "「{b}」は「{a}」の生成物である。",
        "生成過程では「{a}」から「{b}」が得られる。",
        "「{a}」が生み出す物質は「{b}」だ。",
    ),
    "property": (
        "「{a}」は「{b}」という性質を持つ。", "「{a}」の性質の一つは「{b}」である。",
        "「{b}」は「{a}」に見られる特徴だ。",
        "性質に注目すると、「{a}」には「{b}」が備わっている。",
        "資料は「{a}」の特徴として「{b}」を挙げている。",
    ),
}
Q = {
    "class": (
        "「{a}」は何の一種ですか。", "分類上、「{a}」は何に含まれますか。",
        "「{a}」が属する分類を答えてください。",
        "教科書上、「{a}」はどの分類の仲間ですか。", "「{a}」の上位分類は何でしょうか。",
    ),
    "located": (
        "「{a}」はどこに位置しますか。", "「{a}」の所在地を答えてください。",
        "地理的に「{a}」はどこにありますか。",
        "地図上で「{a}」が存在する地域はどこですか。", "「{a}」を含む場所はどこでしょうか。",
    ),
    "part": (
        "「{a}」は何の一部ですか。", "「{a}」が構成する全体を答えてください。",
        "構造上「{a}」は何に組み込まれていますか。",
        "「{a}」を構成要素として含む全体は何ですか。", "全体との関係で「{a}」は何の部分でしょうか。",
    ),
    "causes": (
        "「{a}」は何を引き起こしますか。", "「{a}」の結果として何が生じますか。",
        "「{a}」が原因となる現象を答えてください。",
        "因果関係上、「{a}」から何が発生しますか。", "「{a}」によって起きる結果は何でしょうか。",
    ),
    "requires": (
        "「{a}」には何が必要ですか。", "「{a}」の成立条件を答えてください。",
        "「{a}」を行うには何を要しますか。",
        "「{a}」を実現する前提は何ですか。", "成立条件として「{a}」に欠かせないものは何でしょうか。",
    ),
    "produces": (
        "「{a}」は何を生成しますか。", "「{a}」から何が作られますか。",
        "「{a}」の生成物を答えてください。",
        "生成過程で「{a}」から得られるものは何ですか。", "「{a}」が生み出す物質は何でしょうか。",
    ),
    "property": (
        "「{a}」はどのような性質を持ちますか。", "「{a}」の性質を答えてください。",
        "「{a}」に見られる特徴は何ですか。",
        "性質に注目すると「{a}」には何が備わっていますか。", "資料が挙げる「{a}」の特徴は何でしょうか。",
    ),
}
RQ = {
    "class": ("「{a}」の最上位分類は何ですか。", "関係をたどったとき「{a}」が最終的に属する分類は何ですか。"),
    "located": ("「{a}」を最終的に含む地域はどこですか。", "位置関係をたどると「{a}」は最終的にどこに含まれますか。"),
    "requires": ("関係をたどると「{a}」に最終的に必要なものは何ですか。", "分類を考慮したとき「{a}」の成立条件は何ですか。"),
    "property": ("分類関係を考慮すると「{a}」が受け継ぐ性質は何ですか。", "上位分類から「{a}」に継承される特徴は何でしょうか。"),
}
BASE = ("class", "located", "part", "causes", "requires")
NEW = ("produces", "property")
RULES = (
    ("class", "class", "class", "分類"),
    ("located", "located", "located", "地理"),
    ("part", "located", "located", "構造地理"),
    ("class", "requires", "requires", "条件"),
)


def paragraph(rel, a, b, surfaces=None):
    return "".join(t.format(a=a, b=b) for t in (surfaces or S[rel]))


def ingest(model, rel, a, b, source, index, prefix):
    return model.read_sentence(prefix + S[rel][3 + index % 2].format(a=a, b=b), source)


def build_base():
    model = SparseTextbookLearner()
    ids = {}
    for rel in BASE:
        for i in range(12):
            rid = model.learn_fact_paragraph(
                paragraph(rel, f"学習{rel}項目{i}", f"学習{rel}概念{i}"),
                f"TRAIN-{rel}-{i}",
            )
            ids.setdefault(rel, rid)
        for i, question in enumerate(Q[rel]):
            if not model.learn_question(
                question.format(a=f"学習{rel}項目{i}"),
                f"学習{rel}概念{i}",
            ):
                raise RuntimeError("direct question induction failed")
    return model, ids


def train_rules(model):
    for left, right, head, name in RULES:
        for i in range(10):
            a, b, c = f"{name}A{i}", f"{name}B{i}", f"{name}C{i}"
            model.learn_fact_paragraph(paragraph(left, a, b, S[left][:2]), f"RULE-{name}-{i}-1")
            model.learn_fact_paragraph(paragraph(right, b, c, S[right][:2]), f"RULE-{name}-{i}-2")
            model.learn_fact_paragraph(paragraph(head, a, c, S[head][:2]), f"RULE-{name}-{i}-3")
    learned = model.induce_rules(min_support=5, min_precision=0.95)
    for left, right, head, name in RULES:
        for qi, question in enumerate(RQ[head]):
            a, b, c = f"推論例{name}A{qi}", f"推論例{name}B{qi}", f"推論例{name}C{qi}"
            if not ingest(model, left, a, b, f"DEMO-{name}-{qi}-1", qi, "第一資料では、")[0]:
                raise RuntimeError("reasoning demo read failed")
            if not ingest(model, right, b, c, f"DEMO-{name}-{qi}-2", qi + 1, "第二資料では、")[0]:
                raise RuntimeError("reasoning demo read failed")
            if not model.learn_question(question.format(a=a), c, mode="closure"):
                raise RuntimeError("reasoning question induction failed")
    return learned


def eval_direct(model, rels, count, phase):
    cases, correct, evidence, mc, mr = [], 0, 0, 0, 0
    for rel in rels:
        for i in range(count):
            a, b, source = f"{phase}{rel}対象{i}", f"{phase}{rel}答{i}", f"{phase}-SRC-{rel}-{i}"
            accepted, _ = ingest(model, rel, a, b, source, i, "別の教科書では、")
            question = "本文と資料を踏まえると、" + Q[rel][3 + i % 2].format(a=a)
            answer = model.ask(question)
            good = accepted and answer.value == b
            correct += good
            evidence += good and answer.sources == (source,)
            mc, mr = max(mc, model.last_candidates), max(mr, model.last_feature_reads)
            cases.append((question, b, source))
    return {"correct": correct, "total": len(cases), "evidence": evidence, "cases": cases, "max_candidates": mc, "max_reads": mr}


def eval_two(model, count, phase):
    cases, correct, evidence, mc, mr = [], 0, 0, 0, 0
    for ci, (left, right, head, name) in enumerate(RULES):
        for i in range(count):
            a, b, c = f"{phase}{name}A{i}", f"{phase}{name}B{i}", f"{phase}{name}C{i}"
            s1, s2 = f"{phase}-{name}-{i}-1", f"{phase}-{name}-{i}-2"
            ok1 = ingest(model, left, a, b, s1, i, "第一資料では、")[0]
            ok2 = ingest(model, right, b, c, s2, i + 1, "第二資料では、")[0]
            question = "二つの資料を統合すると、" + RQ[head][ci % 2].format(a=a)
            answer = model.ask(question)
            good = ok1 and ok2 and answer.value == c
            correct += good
            evidence += good and set(answer.sources) == {s1, s2}
            mc, mr = max(mc, model.last_candidates), max(mr, model.last_feature_reads)
            cases.append((question, c, {s1, s2}))
    return {"correct": correct, "total": len(cases), "evidence": evidence, "cases": cases, "max_candidates": mc, "max_reads": mr}


def eval_three(model, count, phase):
    cases, correct, evidence, mc, mr = [], 0, 0, 0, 0
    for rel, name in (("class", "三段分類"), ("located", "三段地理")):
        for i in range(count):
            a, b, c, d = (f"{phase}{name}A{i}", f"{phase}{name}B{i}", f"{phase}{name}C{i}", f"{phase}{name}D{i}")
            sources, accepted = [], True
            for hop, (left, right) in enumerate(((a, b), (b, c), (c, d))):
                source = f"{phase}-{name}-{i}-{hop + 1}"
                sources.append(source)
                accepted &= ingest(model, rel, left, right, source, i + hop, f"第{hop + 1}資料では、")[0]
            question = "三つの資料を順にたどると、" + RQ[rel][i % 2].format(a=a)
            answer = model.ask(question)
            good = accepted and answer.value == d
            correct += good
            evidence += good and set(answer.sources) == set(sources)
            mc, mr = max(mc, model.last_candidates), max(mr, model.last_feature_reads)
            cases.append((question, d, set(sources)))
    return {"correct": correct, "total": len(cases), "evidence": evidence, "cases": cases, "max_candidates": mc, "max_reads": mr}


def add_new(model):
    ids = {}
    for rel in NEW:
        for i in range(10):
            rid = model.learn_fact_paragraph(paragraph(rel, f"追加{rel}項目{i}", f"追加{rel}概念{i}"), f"NEWTRAIN-{rel}-{i}")
            ids.setdefault(rel, rid)
        for i, question in enumerate(Q[rel]):
            if not model.learn_question(question.format(a=f"追加{rel}項目{i}"), f"追加{rel}概念{i}"):
                raise RuntimeError("new question induction failed")
    for i in range(10):
        a, b, c = f"継承A{i}", f"継承B{i}", f"継承C{i}"
        model.learn_fact_paragraph(paragraph("class", a, b, S["class"][:2]), f"NEWRULE-{i}-1")
        model.learn_fact_paragraph(paragraph("property", b, c, S["property"][:2]), f"NEWRULE-{i}-2")
        model.learn_fact_paragraph(paragraph("property", a, c, S["property"][:2]), f"NEWRULE-{i}-3")
    model.induce_rules(min_support=5, min_precision=0.95, preserve_existing=True)
    for i, question in enumerate(RQ["property"]):
        a, b, c = f"継承推論A{i}", f"継承推論B{i}", f"継承推論C{i}"
        if not ingest(model, "class", a, b, f"NEWDEMO-{i}-1", i, "分類資料では、")[0]:
            raise RuntimeError("new rule demo failed")
        if not ingest(model, "property", b, c, f"NEWDEMO-{i}-2", i + 1, "性質資料では、")[0]:
            raise RuntimeError("new rule demo failed")
        if not model.learn_question(question.format(a=a), c, mode="closure"):
            raise RuntimeError("new reasoning question failed")
    return ids


def eval_new_rule(model, count, phase):
    cases, correct, evidence, mc, mr = [], 0, 0, 0, 0
    for i in range(count):
        a, b, c = f"{phase}A{i}", f"{phase}B{i}", f"{phase}C{i}"
        s1, s2 = f"{phase}-{i}-1", f"{phase}-{i}-2"
        ok1 = ingest(model, "class", a, b, s1, i, "分類資料では、")[0]
        ok2 = ingest(model, "property", b, c, s2, i + 1, "性質資料では、")[0]
        question = "複数の資料を統合して考えると、" + RQ["property"][i % 2].format(a=a)
        answer = model.ask(question)
        good = ok1 and ok2 and answer.value == c
        correct += good
        evidence += good and set(answer.sources) == {s1, s2}
        mc, mr = max(mc, model.last_candidates), max(mr, model.last_feature_reads)
        cases.append((question, c, {s1, s2}))
    return {"correct": correct, "total": len(cases), "evidence": evidence, "cases": cases, "max_candidates": mc, "max_reads": mr}


def recheck(model, direct, reasoning):
    dc = de = rc = revidence = 0
    for question, expected, source in direct:
        answer = model.ask(question)
        dc += answer.value == expected
        de += answer.value == expected and answer.sources == (source,)
    for question, expected, sources in reasoning:
        answer = model.ask(question)
        rc += answer.value == expected
        revidence += answer.value == expected and set(answer.sources) == sources
    return {"direct_correct": dc, "direct_evidence": de, "reasoning_correct": rc, "reasoning_evidence": revidence}


def run_gate():
    started = time.perf_counter()
    model, base_ids = build_base()
    base_rules = train_rules(model)
    direct = eval_direct(model, BASE, 20, "BASE")
    two = eval_two(model, 20, "BASE-RULE")
    three = eval_three(model, 20, "BASE-THREE")
    initial_relations, initial_rules = len(model.relation_patterns), len(model.rules)
    new_ids = add_new(model)
    new_direct = eval_direct(model, NEW, 20, "NEW")
    new_rule = eval_new_rule(model, 30, "NEW-RULE")
    expanded_relations, expanded_rules = len(model.relation_patterns), len(model.rules)
    old_reasoning = two["cases"] + three["cases"]
    nonregression = recheck(model, direct["cases"], old_reasoning)

    before = len(model.facts)
    unknown_rel = sum(
        not model.read_sentence(text, f"UNKNOWN-{i}")[0]
        for i, text in enumerate((
            "「未知対象」は「未知概念」と強く共鳴する。",
            "「未知対象」は「未知概念」を祝福する。",
            "「未知対象」は「未知概念」に反対票を投じる。",
        ))
    )
    state_preserved = len(model.facts) == before
    unknown_q = sum(
        model.ask(question).value is None
        for question in (
            "「未知対象」はなぜ人気なのですか。",
            "「未知対象」に反対したのは誰ですか。",
            "「未知対象」の色を説明してください。",
        )
    )

    payload = model.to_bytes()
    restored = SparseTextbookLearner.from_bytes(payload)
    restored_result = recheck(restored, direct["cases"][:20], old_reasoning[:20])
    max_candidates = max(x["max_candidates"] for x in (direct, two, three, new_direct, new_rule))
    max_reads = max(x["max_reads"] for x in (direct, two, three, new_direct, new_rule))
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_bytes = int(peak if sys.platform == "darwin" else peak * 1024)

    checks = {
        "five_base_relations_induced_without_names": initial_relations == 5,
        "four_base_rules_induced": initial_rules == 4,
        "base_direct_and_evidence_exact": direct["correct"] == direct["evidence"] == direct["total"] == 100,
        "two_source_reasoning_and_evidence_exact": two["correct"] == two["evidence"] == two["total"] == 80,
        "three_source_reasoning_and_evidence_exact": three["correct"] == three["evidence"] == three["total"] == 40,
        "continual_relations_grow_to_seven": expanded_relations == 7,
        "continual_rules_grow_to_five": expanded_rules == 5,
        "new_direct_and_evidence_exact": new_direct["correct"] == new_direct["evidence"] == new_direct["total"] == 40,
        "new_cross_rule_and_evidence_exact": new_rule["correct"] == new_rule["evidence"] == new_rule["total"] == 30,
        "old_direct_nonregressing": nonregression["direct_correct"] == nonregression["direct_evidence"] == 100,
        "old_reasoning_nonregressing": nonregression["reasoning_correct"] == nonregression["reasoning_evidence"] == 120,
        "unknown_relations_abstain_without_mutation": unknown_rel == 3 and state_preserved,
        "unknown_questions_abstain": unknown_q == 3,
        "save_restore_preserves_direct_and_reasoning": all(value == 20 for value in restored_result.values()),
        "candidate_budget_at_most_16": max_candidates <= 16,
        "feature_reads_at_most_5000": max_reads <= 5000,
        "model_at_most_256_kib": len(payload) <= 256 * 1024,
    }
    report = {
        "capability_id": "SPARC-TEXTBOOK-CONCEPTS-001",
        "initial_relations": initial_relations, "expanded_relations": expanded_relations,
        "initial_rules": initial_rules, "expanded_rules": expanded_rules,
        "base_relation_ids": base_ids, "new_relation_ids": new_ids,
        "base_rules": {"|".join(body): head for body, head in base_rules.items()},
        "base_direct": {k: v for k, v in direct.items() if k != "cases"},
        "base_two_hop": {k: v for k, v in two.items() if k != "cases"},
        "base_three_hop": {k: v for k, v in three.items() if k != "cases"},
        "new_direct": {k: v for k, v in new_direct.items() if k != "cases"},
        "new_rule": {k: v for k, v in new_rule.items() if k != "cases"},
        "nonregression": nonregression,
        "unknown_relation_abstentions": unknown_rel, "unknown_question_abstentions": unknown_q,
        "unknown_state_preserved": state_preserved,
        "resources": {
            "serialized_model_bytes": len(payload), "peak_rss_bytes": peak_bytes,
            "wall_seconds": time.perf_counter() - started,
            "maximum_candidates": max_candidates, "maximum_feature_reads": max_reads,
        },
        "model": model.report(), "checks": checks, "passed": all(checks.values()),
        "claim_boundary": (
            "The documents and questions are generated, and entity discovery is bootstrapped by Japanese "
            "quotation marks. This establishes latent relation clustering, source-grounded multi-document "
            "reasoning, rule induction, continual relation growth, and calibrated abstention. It does not "
            "establish unrestricted Japanese reading or Japanese high-school-level intelligence."
        ),
    }
    return report, model


def render(report):
    r = report["resources"]
    return "\n".join((
        "# SPARC textbook concepts 001", "", f"Passed: **{report['passed']}**",
        f"- Latent relations: **{report['initial_relations']} -> {report['expanded_relations']}**",
        f"- Learned rules: **{report['initial_rules']} -> {report['expanded_rules']}**",
        f"- Direct: **{report['base_direct']['correct']}/{report['base_direct']['total']}**",
        f"- Two-hop: **{report['base_two_hop']['correct']}/{report['base_two_hop']['total']}**",
        f"- Three-hop: **{report['base_three_hop']['correct']}/{report['base_three_hop']['total']}**",
        f"- New direct: **{report['new_direct']['correct']}/{report['new_direct']['total']}**",
        f"- New rule: **{report['new_rule']['correct']}/{report['new_rule']['total']}**",
        f"- Model: **{r['serialized_model_bytes']} bytes**", f"- Wall: **{r['wall_seconds']:.3f} s**",
        "", "## Claim boundary", report["claim_boundary"],
    ))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report, model = run_gate()
    (args.output_dir / "SPARC-textbook-concepts-001.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    (args.output_dir / "SPARC-textbook-concepts-001.md").write_text(render(report), encoding="utf-8")
    (args.output_dir / "SPARC-textbook-concepts-001.model.zlib").write_bytes(model.to_bytes())
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if not report["passed"]:
        raise SystemExit("SPARC-TEXTBOOK-CONCEPTS-001 gate failed")


if __name__ == "__main__":
    main()
