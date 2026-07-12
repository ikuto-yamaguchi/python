from __future__ import annotations

from collections import defaultdict, deque

from .signed_claim_graph import ClaimPrediction, SignedClaimProgram, SignedClaimRuntime


class QueueSignedClaimRuntime(SignedClaimRuntime):
    """Linear work-list evaluator for signed reliability constraints.

    The semantic relation is unchanged: a speaker is truthful exactly when the
    target truth value matches the polarity asserted by the speaker.  Unlike a
    repeated full-graph fixed-point scan, each newly discovered signed value is
    propagated through its outgoing edges once.  Conflicts deliberately
    propagate both polarities and therefore remain observable at the query.
    """

    def execute(self, program: SignedClaimProgram) -> ClaimPrediction:
        adjacency: dict[str, list[tuple[str, bool]]] = defaultdict(list)
        values: dict[str, set[bool]] = {}
        queue: deque[tuple[str, bool]] = deque()
        operations = reads = writes = 0

        entities = {program.query_entity}
        for claim in program.claims:
            adjacency[claim.target].append((claim.speaker, claim.asserted_truth))
            entities.add(claim.target)
            entities.add(claim.speaker)
            operations += 1
            writes += 1

        for entity, truth in program.base_assignments:
            entities.add(entity)
            bucket = values.setdefault(entity, set())
            reads += 1
            if bool(truth) not in bucket:
                bucket.add(bool(truth))
                queue.append((entity, bool(truth)))
                writes += 2

        while queue:
            target, target_truth = queue.popleft()
            operations += 1
            reads += 1
            for speaker, asserted_truth in adjacency.get(target, ()):
                operations += 1
                reads += 1
                speaker_truth = target_truth == asserted_truth
                bucket = values.setdefault(speaker, set())
                reads += 1
                if speaker_truth in bucket:
                    continue
                bucket.add(speaker_truth)
                queue.append((speaker, speaker_truth))
                writes += 2

        query_values = values.get(program.query_entity, set())
        reads += 1
        conflicts = tuple(sorted(entity for entity, rows in values.items() if len(rows) > 1))
        unresolved = tuple(sorted(entity for entity in entities if not values.get(entity)))
        known = sum(len(rows) == 1 for rows in values.values())
        if len(query_values) != 1:
            return ClaimPrediction(
                None,
                operations,
                reads,
                writes,
                known,
                conflicts,
                unresolved,
            )
        actual = next(iter(query_values))
        return ClaimPrediction(
            "Yes" if actual == program.query_polarity else "No",
            operations,
            reads,
            writes,
            known,
            conflicts,
            unresolved,
        )
