from __future__ import annotations

from dataclasses import dataclass

from .sparc_highschool_general import World
from .sparc_highschool_implicit_world import ImplicitWorldLearner


@dataclass(frozen=True)
class LatentStateGraphResult:
    accepted: bool
    initial_world: World
    final_world: World
    actions: tuple[str, ...]
    recovered_states: tuple[tuple[str, str, int, int], ...]
    answer: str
    verified: bool
    mechanism: str


class LatentStateGraphLearner(ImplicitWorldLearner):
    """Solve omitted states anywhere in one shared reversible transition graph.

    Each learned numeric event is the same sparse affine edge used by forward
    execution. Observations may anchor any node, and exact values propagate both
    forward and backward. Disconnected transition components without observations
    are ignored, while observation-only components remain fixed world context.
    No task label, domain label, or phrase exception is used.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.latent_graphs_solved = 0
        self.latent_graph_abstentions = 0
        self.latent_state_nodes_recovered = 0
        self.latent_constraint_reads = 0
        self.latent_forward_checks = 0
        self.latent_verification_failures = 0
        self.latent_anchored_components = 0
        self.latent_unanchored_components_skipped = 0
        self.latent_fixed_observation_components = 0

    @staticmethod
    def _forward(value: int, scale: int, offset: int) -> int:
        return scale * value + offset

    @staticmethod
    def _backward(value: int, scale: int, offset: int) -> int | None:
        if scale == 0:
            return None
        numerator = value - offset
        if numerator % scale:
            return None
        return numerator // scale

    def _abstain(self, mechanism: str, initial: World | None = None, world: World | None = None,
                 actions: tuple[str, ...] = ()) -> LatentStateGraphResult:
        self.latent_graph_abstentions += 1
        return LatentStateGraphResult(
            False,
            initial or World(),
            world or World(),
            actions,
            (),
            "",
            False,
            mechanism,
        )

    def infer_latent_state_graph(self, text: str) -> LatentStateGraphResult:
        sentences = tuple(self._sentences(text))
        observations: list[tuple[int, tuple[str, str], int]] = []
        transitions: list[tuple[int, str, tuple[str, str], int, int, str]] = []
        for index, sentence in enumerate(sentences):
            observed = self.observe_world([sentence])
            if observed.accepted == 1 and not observed.abstained:
                row = self._single_number(observed.world)
                if row is not None:
                    key, value = row
                    observations.append((index, key, value))
            transition = self._affine_transition(sentence)
            if transition is not None:
                key, scale, offset, program_id = transition
                transitions.append((index, sentence, key, scale, offset, program_id))
        self.latent_constraint_reads += len(sentences) + len(transitions) + len(observations)

        keys = {key for _i, key, _v in observations} | {
            key for _i, _s, key, _a, _b, _p in transitions
        }
        if not keys:
            return self._abstain("abstain-empty-latent-state-graph")

        observations_by_key: dict[tuple[str, str], list[tuple[int, int]]] = {}
        for index, key, value in observations:
            observations_by_key.setdefault(key, []).append((index, value))

        solved_by_key: dict[tuple[str, str], list[int]] = {}
        observed_nodes: set[tuple[tuple[str, str], int]] = set()
        active_transition_keys: set[tuple[str, str]] = set()

        for key in sorted(keys):
            edges = sorted(
                (row for row in transitions if row[2] == key),
                key=lambda row: row[0],
            )
            anchors = observations_by_key.get(key, [])

            # A transition component with no observation has no evidential anchor.
            # It is irrelevant to a separately anchored chain and must not force
            # whole-document abstention.
            if edges and not anchors:
                self.latent_unanchored_components_skipped += 1
                continue

            # Numeric context without a transition is a fixed world component.
            # Preserve it during replay, but do not claim it as a recovered state.
            if not edges:
                if not anchors:
                    continue
                distinct = {value for _index, value in anchors}
                if len(distinct) != 1:
                    return self._abstain("abstain-conflicting-fixed-observations")
                value = next(iter(distinct))
                solved_by_key[key] = [value]
                observed_nodes.add((key, 0))
                self.latent_fixed_observation_components += 1
                continue

            self.latent_anchored_components += 1
            active_transition_keys.add(key)
            values: list[int | None] = [None] * (len(edges) + 1)
            for observation_index, observed_value in anchors:
                node = sum(1 for edge in edges if edge[0] < observation_index)
                current = values[node]
                if current is not None and current != observed_value:
                    return self._abstain("abstain-conflicting-latent-observations")
                values[node] = observed_value
                observed_nodes.add((key, node))

            changed = True
            while changed:
                changed = False
                for edge_index, (_position, _sentence, _key, scale, offset, _pid) in enumerate(edges):
                    left, right = values[edge_index], values[edge_index + 1]
                    if left is not None:
                        candidate = self._forward(left, scale, offset)
                        if right is None:
                            values[edge_index + 1] = candidate
                            changed = True
                        elif right != candidate:
                            return self._abstain("abstain-inconsistent-latent-transition")
                    elif right is not None:
                        candidate = self._backward(right, scale, offset)
                        if candidate is None:
                            return self._abstain("abstain-nonintegral-latent-transition")
                        values[edge_index] = candidate
                        changed = True

            if any(value is None for value in values):
                return self._abstain("abstain-underconstrained-anchored-latent-state-graph")
            solved_by_key[key] = [int(value) for value in values]

        if not active_transition_keys:
            return self._abstain("abstain-no-solved-latent-chain")

        initial = World.from_parts(
            numbers={key: values[0] for key, values in solved_by_key.items()}
        )
        world = initial
        edge_cursor = {key: 0 for key in active_transition_keys}
        ordered_actions: list[str] = []
        observation_map: dict[int, list[tuple[tuple[str, str], int]]] = {}
        for index, key, value in observations:
            if key in solved_by_key:
                observation_map.setdefault(index, []).append((key, value))
        transition_map = {
            index: (sentence, key)
            for index, sentence, key, _a, _b, _p in transitions
            if key in active_transition_keys
        }

        for index, _sentence in enumerate(sentences):
            if index in transition_map:
                action, key = transition_map[index]
                applied = self.apply(action, world)
                if not applied.accepted:
                    return self._abstain(
                        "abstain-latent-forward-application",
                        initial,
                        world,
                        tuple(ordered_actions),
                    )
                world = applied.world
                ordered_actions.append(action)
                edge_cursor[key] += 1
                expected = solved_by_key[key][edge_cursor[key]]
                self.latent_forward_checks += 1
                if world.number_map().get(key) != expected:
                    self.latent_verification_failures += 1
                    return self._abstain(
                        "abstain-latent-node-verification",
                        initial,
                        world,
                        tuple(ordered_actions),
                    )
            for key, value in observation_map.get(index, ()):
                self.latent_forward_checks += 1
                if world.number_map().get(key) != value:
                    self.latent_verification_failures += 1
                    return self._abstain(
                        "abstain-latent-observation-verification",
                        initial,
                        world,
                        tuple(ordered_actions),
                    )

        recovered: list[tuple[str, str, int, int]] = []
        for (subject, relation), values in sorted(solved_by_key.items()):
            if (subject, relation) not in active_transition_keys:
                continue
            for node, value in enumerate(values):
                if ((subject, relation), node) not in observed_nodes:
                    recovered.append((subject, relation, node, value))
        if not recovered:
            return self._abstain(
                "abstain-no-latent-state-recovered",
                initial,
                world,
                tuple(ordered_actions),
            )

        self.latent_graphs_solved += 1
        self.latent_state_nodes_recovered += len(recovered)
        summary = "、".join(
            f"{subject}の時点{node}は{value}"
            for subject, _relation, node, value in recovered
        )
        answer = (
            f"同じ世界遷移を前後から照合すると、{summary}です。"
            "全ての観測位置まで順方向に再実行し、矛盾がないことを検算しました。"
        )
        return LatentStateGraphResult(
            True,
            initial,
            world,
            tuple(ordered_actions),
            tuple(recovered),
            answer,
            True,
            "shared-bidirectional-latent-state-graph",
        )

    def report(self):
        result = super().report()
        result.update({
            "shared_bidirectional_latent_state_graph": True,
            "latent_graphs_solved": self.latent_graphs_solved,
            "latent_graph_abstentions": self.latent_graph_abstentions,
            "latent_state_nodes_recovered": self.latent_state_nodes_recovered,
            "latent_constraint_reads": self.latent_constraint_reads,
            "latent_forward_checks": self.latent_forward_checks,
            "latent_verification_failures": self.latent_verification_failures,
            "latent_anchored_components": self.latent_anchored_components,
            "latent_unanchored_components_skipped": self.latent_unanchored_components_skipped,
            "latent_fixed_observation_components": self.latent_fixed_observation_components,
        })
        return result
