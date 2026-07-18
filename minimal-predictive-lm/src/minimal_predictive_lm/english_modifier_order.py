from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ModifierOrderPrediction:
    output: str | None
    operations: int
    candidates: int


class EnglishModifierOrderResolver:
    """Score English prenominal modifiers by semantic distance from the noun.

    The resolver does not receive a benchmark or axis name.  It recognizes two or
    more candidate noun phrases and prefers the phrase whose modifier classes follow
    the ordinary English ordering tendency:

    evaluation, size, age, shape, colour, origin, material, purpose.
    """

    _OPINION = frozenset(
        "good nice lovely wonderful terrible awful repulsive ridiculous silly "
        "mysterious obnoxious beautiful ugly attractive strange excellent normal"
        .split()
    )
    _SIZE = frozenset(
        "big large huge enormous massive small tiny little midsize medium-size "
        "medium-sized normal-size normal-sized gigantic miniature vast".split()
    )
    _AGE = frozenset(
        "new brand-new old ancient archaic antique old-fashioned modern young "
        "recent aged".split()
    )
    _SHAPE = frozenset(
        "round circular square rectangular triangular spherical pyramidal "
        "prismlike oval flat curved straight cylindrical conical".split()
    )
    _COLOUR = frozenset(
        "black white red blue green yellow orange purple pink tan brown grey gray "
        "violet turquoise beige crimson".split()
    )
    _ORIGIN = frozenset(
        "american brazilian mexican indian egyptian pakistani filipino german "
        "congolese japanese nigerian indonesian vietnamese russian turkish iranian "
        "chinese thai israeli italian french british english spanish korean canadian "
        "australian african asian european".split()
    )
    _MATERIAL = frozenset(
        "rubber iron cloth glass wool steel cardboard lead leather wood wooden paper "
        "silver gold fiberglass fibreglass plastic cotton silk metal metallic stone "
        "ceramic bronze copper aluminum aluminium".split()
    )

    _OPTION = re.compile(r"^\s*(?:\(([A-Z])\)|([A-Z])[.)])\s+(.+?)\s*$")

    @property
    def description_bits(self) -> int:
        words = (
            self._OPINION
            | self._SIZE
            | self._AGE
            | self._SHAPE
            | self._COLOUR
            | self._ORIGIN
            | self._MATERIAL
        )
        return 8 * (320 + sum(len(word) + 1 for word in words))

    @staticmethod
    def _clean(token: str) -> str:
        return token.lower().strip(" ,.;:!?\"'()[]{}")

    def _class(self, token: str) -> int:
        word = self._clean(token)
        if word in self._OPINION:
            return 0
        if word in self._SIZE:
            return 1
        if word in self._AGE:
            return 2
        if word in self._SHAPE:
            return 3
        if word in self._COLOUR:
            return 4
        if word in self._ORIGIN or (word[:1].isalpha() and token[:1].isupper()):
            return 5
        if word in self._MATERIAL:
            return 6
        if word.endswith("ing") or word in {"exercise", "typing", "walking"}:
            return 7
        return 8

    def _score(self, phrase: str) -> tuple[int, int, tuple[int, ...]]:
        tokens = phrase.split()
        if len(tokens) < 2:
            return 10_000, 0, ()
        classes = tuple(self._class(token) for token in tokens[:-1])
        inversions = sum(
            1
            for left in range(len(classes))
            for right in range(left + 1, len(classes))
            if classes[left] > classes[right]
        )
        unknown = sum(value == 8 for value in classes)
        # Unknown modifiers are not automatically wrong, but a phrase whose known
        # modifiers are correctly ordered is preferred over one that scrambles them.
        return inversions, unknown, classes

    def answer(self, prompt: str) -> ModifierOrderPrediction:
        options: list[tuple[str, str]] = []
        for line in prompt.splitlines():
            match = self._OPTION.match(line)
            if match:
                options.append((match.group(1) or match.group(2), match.group(3)))
        if len(options) < 2:
            return ModifierOrderPrediction(None, len(prompt), len(options))
        scored = [(self._score(phrase), label) for label, phrase in options]
        scored.sort(key=lambda row: row[0])
        if len(scored) > 1 and scored[0][0][:2] == scored[1][0][:2]:
            return ModifierOrderPrediction(None, len(prompt) + len(options), len(options))
        return ModifierOrderPrediction(
            f"({scored[0][1]})",
            len(prompt) + sum(len(item[0][2]) for item in scored),
            len(options),
        )
