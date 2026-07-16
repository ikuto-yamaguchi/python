# SPARC-HS9: Sparse Discourse Graph

HS9 adds local claim, evidence, example, counterargument, concession and conclusion structure to the shared HS8 model.

## Compute contract

- document routing uses rare literal anchors and a bounded inverted-index read budget;
- only the selected document's main claim is activated;
- evidence retrieval follows a per-target reverse edge index;
- counterargument retrieval uses the selected document's local role list;
- comparison activates at most two main claims;
- no operation scans every document, node or discourse edge;
- no Transformer, softmax attention or growing KV cache is used.

## Representation

Each sentence becomes a typed local node. Edges such as `supports`, `exemplifies`, `opposes`, `qualifies`, `elaborates` and `develops` are constructed inside one document. Every target node stores the IDs of its incoming edges, so asking for a conclusion's reasons reads only those edges rather than filtering the complete graph.

## Claim boundary

The initial discourse-role classifier uses Japanese surface markers such as `なぜなら`, `例えば`, `しかし` and `したがって`. It is a bootstrap operator, not unrestricted discourse understanding. HS9 therefore tests the graph and routing architecture, while later stages must learn discourse roles from weak supervision and real varied prose.
