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
    forward and backward. No task label, domain label, or phrase exception is used.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.latent_graphs_solved = 0
        self.latent_graph_abstentions = 0
        self.latent_state_nodes_recovered = 0
        self.latent_constraint_reads = 0
        self.latent_forward_checks = 0
        self.latent_verification_failures = 0

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

        keys = {key for _i, key, _v in observations} | {key for _i, _s, key, _a, _b, _p in transitions}
        if not keys:
            self.latent_graph_abstentions += 1
            return LatentStateGraphResult(False, World(), World(), (), (), "", False, "abstain-empty-latent-state-graph")

        solved_by_key: dict[tuple[str, str], list[int]] = {}
        action_rows: list[tuple[int, str]] = []
        observed_nodes: set[tuple[tuple[str, str], int]] = set()
        for key in sorted(keys):
            edges = [row for row in transitions if row[2] == key]
            edges.sort(key=lambda row: row[0])
            if not edges:
                continue
            values: list[int | None] = [None] * (len(edges) + 1)
            for observation_index, observation_key, observed_value in observations:
                if observation_key != key:
                    continue
                node = sum(1 for edge in edges if edge[0] < observation_index)
                current = values[node]
                if current is not None and current != observed_value:
                    self.latent_graph_abstentions += 1
                    return LatentStateGraphResult(False, World(), World(), (), (), "", False, "abstain-conflicting-latent-observations")
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
                            self.latent_graph_abstentions += 1
                            return LatentStateGraphResult(False, World(), World(), (), (), "", False, "abstain-inconsistent-latent-transition")
                    elif right is not None:
                        candidate = self._backward(right, scale, offset)
                        if candidate is None:
                            self.latent_graph_abstentions += 1
                            return LatentStateGraphResult(False, World(), World(), (), (), "", False, "abstain-nonintegral-latent-transition")
                        values[edge_index] = candidate
                        changed = True

            if any(value is None for value in values):
                self.latent_graph_abstentions += 1
                return LatentStateGraphResult(False, World(), World(), (), (), "", False, "abstain-underconstrained-latent-state-graph")
            solved_by_key[key] = [int(value) for value in values]
            action_rows.extend((row[0], row[1]) for row in edges)

        if not solved_by_key:
            self.latent_graph_abstentions += 1
            return LatentStateGraphResult(False, World(), World(), (), (), "", False, "abstain-no-solved-latent-chain")

        initial = World.from_parts(numbers={key: values[0] for key, values in solved_by_key.items()})
        world = initial
        edge_cursor = {key: 0 for key in solved_by_key}
        ordered_actions: list[str] = []
        observation_map: dict[int, list[tuple[tuple[str, str], int]]] = {}
        for index, key, value in observations:
            observation_map.setdefault(index, []).append((key, value))
        transition_map = {index: (sentence, key) for index, sentence, key, _a, _b, _p in transitions if key in solved_by_key}

        for index, sentence in enumerate(sentences):
            if index in transition_map:
                action, key = transition_map[index]
                applied = self.apply(action, world)
                if not applied.accepted:
                    self.latent_graph_abstentions += 1
                    return LatentStateGraphResult(False, initial, world, tuple(ordered_actions), (), "", False, "abstain-latent-forward-application")
                world = applied.world
                ordered_actions.append(action)
                edge_cursor[key] += 1
                expected = solved_by_key[key][edge_cursor[key]]
                self.latent_forward_checks += 1
                if world.number_map().get(key) != expected:
                    self.latent_verification_failures += 1
                    return LatentStateGraphResult(False, initial, world, tuple(ordered_actions), (), "", False, "abstain-latent-node-verification")
            for key, value in observation_map.get(index, ()):
                self.latent_forward_checks += 1
                if world.number_map().get(key) != value:
                    self.latent_verification_failures += 1
                    return LatentStateGraphResult(False, initial, world, tuple(ordered_actions), (), "", False, "abstain-latent-observation-verification")

        recovered: list[tuple[str, str, int, int]] = []
        for (subject, relation), values in sorted(solved_by_key.items()):
            for node, value in enumerate(values):
                if ((subject, relation), node) not in observed_nodes:
                    recovered.append((subject, relation, node, value))
        if not recovered:
            self.latent_graph_abstentions += 1
            return LatentStateGraphResult(False, initial, world, tuple(ordered_actions), (), "", False, "abstain-no-latent-state-recovered")

        self.latent_graphs_solved += 1
        self.latent_state_nodes_recovered += len(recovered)
        summary = "、".join(f"{subject}の時点{node}は{value}" for subject, _relation, node, value in recovered)
        answer = f"同じ世界遷移を前後から照合すると、{summary}です。全ての観測位置まで順方向に再実行し、矛盾がないことを検算しました。"
        return LatentStateGraphResult(True, initial, world, tuple(ordered_actions), tuple(recovered), answer, True, "shared-bidirectional-latent-state-graph")

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
        })
        return result
