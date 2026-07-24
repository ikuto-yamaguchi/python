import hashlib,json,random,resource,statistics,time

SEEDS=[1,7,19]
K=8
PERMUTATIONS=240
BUDGETS=(0,1,2,4,8)

def predict(token,seed):
    h=hashlib.blake2b((token+str(seed)).encode("utf-8"),digest_size=8).digest()
    return int.from_bytes(h,"little")%K

def run(seed):
    rng=random.Random(seed)
    tokens=[f"ゾ{chr(0x30A1+i)}" for i in range(K)]
    fixed={t:predict(t,seed) for t in tokens}
    zero=[]
    curve={b:[] for b in BUDGETS}
    indistinguishable_pairs=0
    for _ in range(PERMUTATIONS):
        pi=list(range(K));rng.shuffle(pi)
        pj=pi[1:]+pi[:1]
        # Hidden-domain outcomeを一切観測しない限り、piとpjは同じraw utterance/
        # pre-treatment interfaceを露出する一方で、全ラベルが異なる。
        indistinguishable_pairs += int(all(pi[i]!=pj[i] for i in range(K)))
        zero.append(sum(fixed[tokens[i]]==pi[i] for i in range(K))/K)
        order=list(range(K));rng.shuffle(order)
        for b in BUDGETS:
            known=set(order[:b])
            ok=0
            for i,t in enumerate(tokens):
                y=pi[i] if i in known else fixed[t]
                ok += int(y==pi[i])
            curve[b].append(ok/K)
    return {
        "zero_shot_mean":statistics.mean(zero),
        "zero_shot_std_over_permutations":statistics.pstdev(zero),
        "zero_shot_min":min(zero),
        "zero_shot_max":max(zero),
        "calibration_curve":{str(b):statistics.mean(curve[b]) for b in BUDGETS},
        "indistinguishable_permutation_pairs":indistinguishable_pairs,
    }

def main():
    st=time.perf_counter()
    raw={str(s):run(s) for s in SEEDS}
    summary={
        "zero_shot_mean":statistics.mean(raw[str(s)]["zero_shot_mean"] for s in SEEDS),
        "zero_shot_std_across_seeds":statistics.pstdev(raw[str(s)]["zero_shot_mean"] for s in SEEDS),
        "chance":1/K,
        "calibration_curve":{
            str(b):statistics.mean(raw[str(s)]["calibration_curve"][str(b)] for s in SEEDS)
            for b in BUDGETS
        },
        "all_indistinguishable_pairs":all(raw[str(s)]["indistinguishable_permutation_pairs"]==PERMUTATIONS for s in SEEDS),
    }
    result={
        "cycle":8,
        "hypothesis":"Permutation-Symmetry Audit for Opaque-Lexicon Semantic Identifiability",
        "seeds":SEEDS,
        "semantic_classes":K,
        "permutations_per_seed":PERMUTATIONS,
        "summary":summary,
        "raw":raw,
        "theoretical_zero_shot_upper_bound_without_bridge":1/K,
        "strict_progress_gate":False,
        "decision":"stage_correction",
        "answer_leakage":False,
        "post_treatment_final_input":False,
        "fixed_ontology":False,
        "model_bytes":0,
        "estimated_ops_per_permutation":K,
        "runtime_seconds":time.perf_counter()-st,
        "peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "highschool_level_passed":False,
        "native_japanese_communication_passed":False,
        "weak_smartphone_verified":False,
        "completion":False,
    }
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
