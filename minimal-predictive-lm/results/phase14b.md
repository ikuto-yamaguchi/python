# Phase 14b results: provenance document overlay

Raw evidence sentences are compiled into provenance-bearing concept edges and composed with the pinned Open English WordNet graph. WordNet `no-hypernym-path` is treated as open-world absence; explicit cross-source contradictions cause abstention.

## Adaptation disclosure

- evidence selected after failure analysis: **true**
- strict zero-shot claim: **false**
- failed surface identified first: **garlic**
- public item surface overlap in the selected evidence: **garlic, onion**
- benchmark examples / targets used for training: **0 / 0**
- benchmark-specific handler / solver / item dictionary: **0 / false / false**
- external evidence source: `https://arxiv.org/abs/2409.11187`

The external paper describes garlic and onion as allium vegetables. The experiment stores a paraphrased two-edge proof: `garlic → allium vegetable → vegetable`.

## Shared mechanism checks

The same raw-document graph handles independent controlled evidence in other domains:

- `cloudberry → berry → fruit`
- `router → network device → artifact`
- `whale → mammal`
- explicit `whale ↛ fish`
- unknown terms remain unknown

All six cross-domain checks passed. A separate graph containing both `whale → fish` and `whale ↛ fish` returns unknown and abstains.

## Knowledge and compiled cost

- document sources / edges: **4 / 9**
- document graph: **1,891 bytes**
- overlay proof cache: **14,663 bytes**
- graph + overlay cache: **16,554 bytes**
- compiled graph+cache / full WordNet: **0.1721%**
- full reported model bytes: **9,642,678**
- public document-evidence uses: **8**

## Public result

| axis | Phase 14a | Phase 14b |
|---|---:|---:|
| boolean expressions | 100% | 100% |
| direct arithmetic | 100% | 100% |
| multistep arithmetic | 100% | 100% |
| object counting | 90% | 100% |
| word sorting | 100% | 100% |

Overall: **98% → 100%**. All **200/200** public examples were answered correctly.

## Claim boundary

This is an explicitly disclosed post-failure adaptation result. It demonstrates evidence reuse, transitive concept composition, provenance, and contradiction-aware abstention. It is not a zero-shot result, not autonomous discovery of the evidence source, and not an open-model or general-LLM parity result.
