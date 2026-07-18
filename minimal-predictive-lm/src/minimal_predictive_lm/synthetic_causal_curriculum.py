from __future__ import annotations

from dataclasses import dataclass
import random

from .cic_choice_data import ChoiceExample


@dataclass(frozen=True)
class SyntheticCausalCurriculum:
    train: tuple[ChoiceExample, ...]
    holdout: tuple[ChoiceExample, ...]


def _row(story: str, question: str, yes: bool) -> ChoiceExample:
    stem = (story.strip() + " " + question.strip()).strip()
    raw = stem + "\nOptions:\n- Yes\n- No"
    return ChoiceExample(raw, stem, ("Yes", "No"), 0 if yes else 1)


def build_synthetic_causal_curriculum(seed: int = 41) -> SyntheticCausalCurriculum:
    """Create labelled event worlds without benchmark prompts or target labels.

    Train and holdout use different names, objects, outcomes, and surface templates while
    sharing causal structures. This tests whether the compact semantic learner composes
    rules instead of memorizing a fixed sentence.
    """

    rng = random.Random(seed)
    train_names = ["Ari", "Bela", "Cato", "Dina", "Eli", "Fara", "Gio", "Hana"]
    test_names = ["Ivo", "Juna", "Kian", "Lumi"]
    devices = ["alarm", "beacon", "gate", "pump", "signal", "heater"]
    outcomes = ["starts", "fails", "rings", "opens", "stops", "overheats"]
    harms = ["river", "forest", "patient", "village", "wetland"]
    benefits = ["park", "school", "clinic", "garden", "library"]

    def make(names: list[str], holdout: bool) -> list[ChoiceExample]:
        rows: list[ChoiceExample] = []
        for index in range(72 if not holdout else 28):
            a, b = rng.sample(names, 2)
            device = rng.choice(devices)
            outcome = rng.choice(outcomes)
            variant = index % 12
            if variant == 0:
                story = (
                    f"The {device} {outcome} if both switch A and switch B are active. "
                    f"{a} is permitted to activate A. {b} is not supposed to activate B. "
                    f"They activate both and the {device} {outcome}."
                )
                rows += [
                    _row(story, f"Did {b} cause the {device} to {outcome.rstrip('s')}?", True),
                    _row(story, f"Did {a} cause the {device} to {outcome.rstrip('s')}?", False),
                ]
            elif variant == 1:
                story = (
                    f"Either key is sufficient for the {device} to {outcome.rstrip('s')}. "
                    f"{a} already used one key. {b} also used the other key, although both "
                    f"were allowed. The {device} {outcome}."
                )
                rows.append(_row(story, f"Did {b}'s key cause the {device} to {outcome.rstrip('s')}?", False))
            elif variant == 2:
                story = (
                    f"The {device} {outcome} when two users are connected. {a} connected "
                    f"first. Later, while {a} was already connected, {b} connected and the "
                    f"{device} {outcome} immediately."
                )
                rows.append(_row(story, f"Did {b} cause the {device} to {outcome.rstrip('s')}?", True))
            elif variant == 3:
                story = (
                    f"Maintaining the machine requires oil every week. It was {a}'s "
                    f"responsibility to add oil. {a} forgot to add it, and the machine failed."
                )
                rows.append(_row(story, f"Did {a}'s failure to add oil cause the machine failure?", True))
            elif variant == 4:
                story = (
                    f"Maintaining the machine requires oil. It was {a}'s responsibility, "
                    f"not {b}'s. {b} noticed nothing and did not add oil. The machine failed."
                )
                rows.append(_row(story, f"Did {b}'s not adding oil cause the machine failure?", False))
            elif variant == 5:
                harm = rng.choice(harms)
                story = (
                    f"{a} knows the project will definitely harm the {harm}. {a} does not "
                    f"care and decides to start the project for profit. The {harm} is harmed."
                )
                rows.append(_row(story, f"Did {a} intentionally harm the {harm}?", True))
            elif variant == 6:
                benefit = rng.choice(benefits)
                story = (
                    f"{a} knows the project will also help the {benefit}, but does not care "
                    f"about helping it and starts the project for another purpose."
                )
                rows.append(_row(story, f"Did {a} intentionally help the {benefit}?", False))
            elif variant == 7:
                harm = rng.choice(harms)
                story = (
                    f"{a} knows the decision may harm the {harm}, personally opposes that "
                    f"harm, and tries to prevent it, but continues for an unrelated reason."
                )
                rows.append(_row(story, f"Did {a} intentionally harm the {harm}?", False))
            elif variant == 8:
                story = (
                    f"{a} aimed at the wall, but by accident the ball struck the bell. "
                    f"The bell rang immediately."
                )
                rows += [
                    _row(story, f"Did {a} intentionally strike the bell?", False),
                    _row(story, "Did the ball cause the bell to ring?", True),
                ]
            elif variant == 9:
                likelihood = "unlikely" if index % 2 else "very likely"
                expected = likelihood == "unlikely"
                story = (
                    f"Winning requires both a green token and a blue token. It is {likelihood} "
                    f"that {a} selects green first. {a} selects green and then blue and wins."
                )
                rows.append(_row(story, f"Did {a}'s first choice cause the win?", expected))
            elif variant == 10:
                story = (
                    f"Long ago {a} chose a career that placed {a} in the city. Years later a "
                    f"drunk driver struck {a} on the way home, causing death immediately."
                )
                rows += [
                    _row(story, f"Did {a}'s career choice cause the death?", False),
                    _row(story, "Did the drunk driver cause the death?", True),
                ]
            else:
                story = (
                    f"A paired set is completed only when both pieces are present. {a} placed "
                    f"the first piece. {b} then placed the matching piece, so the set was "
                    f"completed immediately."
                )
                rows.append(_row(story, f"Did {b} cause the paired set to be completed?", True))
        rng.shuffle(rows)
        return rows

    return SyntheticCausalCurriculum(tuple(make(train_names, False)), tuple(make(test_names, True)))
