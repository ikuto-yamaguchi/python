from __future__ import annotations

import itertools
import unittest

from sparc_hs16.brain_loop import CorticoHippocampalLoop


class CorticoHippocampalLoopTests(unittest.TestCase):
    def test_one_shot_episodic_recall(self) -> None:
        loop = CorticoHippocampalLoop(["A", "B"], alpha=0.1)
        loop.learn({"cue": "x"}, "A", 1.0, {"done": 1}, terminal=True)
        loop.learn({"cue": "x"}, "B", -1.0, {"done": 1}, terminal=True)
        self.assertEqual(loop.act({"cue": "x"}), "A")

    def test_compositional_hidden_combinations(self) -> None:
        actions = ["LEFT", "RIGHT", "STAY"]
        colors = ["red", "blue", "green"]
        shapes = ["circle", "square", "triangle"]
        rules = ["color", "shape"]
        loop = CorticoHippocampalLoop(actions, buckets=65536, alpha=0.08)

        color_action = dict(zip(colors, actions))
        shape_action = dict(zip(shapes, actions))
        held_keys = {
            ("color", "red", "square"),
            ("color", "blue", "triangle"),
            ("color", "green", "circle"),
            ("shape", "blue", "circle"),
            ("shape", "green", "square"),
            ("shape", "red", "triangle"),
        }
        train: list[tuple[dict[str, str], str]] = []
        hidden: list[tuple[dict[str, str], str]] = []
        for rule, color, shape in itertools.product(rules, colors, shapes):
            state = {"rule": rule, "color": color, "shape": shape}
            answer = color_action[color] if rule == "color" else shape_action[shape]
            (hidden if (rule, color, shape) in held_keys else train).append((state, answer))

        for _ in range(100):
            for state, answer in train:
                for action in actions:
                    loop.learn(state, action, 1.0 if action == answer else -1.0, state, terminal=True)
        loop.replay(4)

        self.assertTrue(all(loop.act(state) == answer for state, answer in hidden))

    def test_reverse_replay_propagates_delayed_reward(self) -> None:
        loop = CorticoHippocampalLoop(["GO", "WAIT"], alpha=0.4, gamma=0.9)
        loop.learn({"position": 0}, "GO", 0.0, {"position": 1})
        loop.learn({"position": 0}, "WAIT", -0.2, {"position": 0}, terminal=True)
        loop.learn({"position": 1}, "GO", 0.0, {"position": 2})
        loop.learn({"position": 1}, "WAIT", -0.2, {"position": 1}, terminal=True)
        loop.learn({"position": 2}, "GO", 1.0, {"done": 1}, terminal=True)
        loop.learn({"position": 2}, "WAIT", -0.2, {"position": 2}, terminal=True)
        loop.replay(10)
        self.assertEqual([loop.act({"position": index}) for index in range(3)], ["GO"] * 3)

    def test_round_trip(self) -> None:
        loop = CorticoHippocampalLoop(["A", "B"])
        loop.learn({"cue": "save"}, "A", 1.0, {"done": 1}, terminal=True)
        restored = CorticoHippocampalLoop.from_dict(loop.to_dict())
        self.assertEqual(restored.act({"cue": "save"}), "A")
        self.assertLess(restored.serialized_bytes(), 1_000_000_000)


if __name__ == "__main__":
    unittest.main()
