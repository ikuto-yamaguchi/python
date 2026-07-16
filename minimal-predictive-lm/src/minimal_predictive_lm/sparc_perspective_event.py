from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

from .sparc_programs import _literal_anchors
from .sparc_perspective_types import (
    _AGENT_PREFIX, _OBJECT, _VALUE, _normalise, _replace_all, _template_regex,
    EventProgram, EventRecord, EventSchema, StateFact, TransitionExample,
)


class PerspectiveEventMixin:
    def register_entity(self, name: str, kind: str) -> None:
        self.entity_kinds[str(name)] = str(kind)
        self.max_entity_chars = max(self.max_entity_chars, len(str(name)))

    def _remember(self, name: str, kind: str) -> None:
        self.register_entity(name, kind)
        try:
            self.focus.remove((name, kind))
        except ValueError:
            pass
        self.focus.append((name, kind))

    def reset_focus(self) -> None:
        self.focus.clear()

    def set_initial_fact(
        self,
        object_name: str,
        attribute: str,
        value: str,
        *,
        source_id: str,
        known_by: Iterable[str] = (),
    ) -> None:
        self.register_entity(object_name, "object")
        self.register_entity(value, "value")
        fact = StateFact(str(value), str(source_id), None)
        self.world[(str(object_name), str(attribute))] = fact
        for agent in known_by:
            self.register_entity(agent, "agent")
            self.beliefs[(str(agent), str(object_name), str(attribute))] = fact

    @staticmethod
    def _changed_world(example: TransitionExample) -> tuple[str, str, str | None, str]:
        keys = set(example.before_world) | set(example.after_world)
        changed = [
            key
            for key in keys
            if example.before_world.get(key) != example.after_world.get(key)
        ]
        if len(changed) != 1:
            raise ValueError("transition demonstration must change exactly one world slot")
        object_name, attribute = changed[0]
        after = example.after_world.get(changed[0])
        if after is None:
            raise ValueError("transition demonstration may not delete a world slot")
        return object_name, attribute, example.before_world.get(changed[0]), after

    @staticmethod
    def _changed_belief_agents(
        example: TransitionExample,
        object_name: str,
        attribute: str,
        new_value: str,
    ) -> tuple[str, ...]:
        agents: list[str] = []
        keys = set(example.before_beliefs) | set(example.after_beliefs)
        for agent, obj, attr in sorted(keys):
            if obj != object_name or attr != attribute:
                continue
            before = example.before_beliefs.get((agent, obj, attr))
            after = example.after_beliefs.get((agent, obj, attr))
            if before != after and after == new_value:
                agents.append(agent)
        return tuple(agents)

    def _event_candidate(self, example: TransitionExample) -> tuple[str, EventProgram]:
        object_name, attribute, _previous, new_value = self._changed_world(example)
        changed_agents = self._changed_belief_agents(
            example, object_name, attribute, new_value
        )
        agents_in_text = [
            name
            for name, kind in example.entity_kinds.items()
            if kind == "agent" and name in example.text
        ]
        agents_in_text.sort(key=lambda name: example.text.index(name))
        replacements: dict[str, str] = {}
        for index, agent in enumerate(agents_in_text):
            replacements[agent] = f"<AGENT{index}>"
        object_from_focus = object_name not in example.text
        if not object_from_focus:
            replacements[object_name] = _OBJECT
        if new_value not in example.text:
            raise ValueError("new world value must appear in event demonstration")
        replacements[new_value] = _VALUE
        update_slots: list[int] = []
        for agent in changed_agents:
            if agent not in agents_in_text:
                raise ValueError("changed belief agent must appear in event text")
            update_slots.append(agents_in_text.index(agent))
        template = _replace_all(_normalise(example.text), replacements)
        program = EventProgram(
            attribute=str(attribute),
            update_agent_slots=tuple(update_slots),
            object_from_focus=object_from_focus,
            support=1,
        )
        return template, program

    def _intern_event_program(self, program: EventProgram) -> int:
        key = (program.attribute, program.update_agent_slots, program.object_from_focus)
        existing = self.event_program_ids.get(key)
        if existing is not None:
            return existing
        if len(self.event_programs) >= self.max_event_programs:
            raise MemoryError("event-program capacity reached")
        program_id = len(self.event_programs)
        self.event_programs.append(program)
        self.event_program_ids[key] = program_id
        return program_id

    @staticmethod
    def _index_schema(template: str, schema_id: int, postings: dict[str, set[int]]) -> None:
        literal = re.sub(r"<(?:AGENT\d+|OBJECT|VALUE)>", "", template)
        for anchor in _literal_anchors(literal) or {literal}:
            if anchor:
                postings[anchor].add(schema_id)

    def teach_event_program(self, examples: Iterable[TransitionExample]) -> EventProgram:
        rows = list(examples)
        if len(rows) < 2:
            raise ValueError("at least two transition demonstrations are required")
        candidates = [self._event_candidate(row) for row in rows]
        templates = {template for template, _program in candidates}
        signatures = {
            (program.attribute, program.update_agent_slots, program.object_from_focus)
            for _template, program in candidates
        }
        if len(templates) != 1 or len(signatures) != 1:
            raise ValueError("transition demonstrations do not share one event program")
        template = candidates[0][0]
        first = candidates[0][1]
        learned = EventProgram(
            first.attribute,
            first.update_agent_slots,
            first.object_from_focus,
            len(rows),
        )
        program_id = self._intern_event_program(learned)
        if template not in self.event_schema_ids:
            if len(self.event_schemas) >= self.max_schemas:
                raise MemoryError("event-schema capacity reached")
            schema_id = len(self.event_schemas)
            self.event_schemas.append(EventSchema(template, program_id, len(rows)))
            self.event_schema_ids[template] = schema_id
            self._index_schema(template, schema_id, self.event_postings)
        return self.event_programs[program_id]

    def link_event_surface(
        self,
        template: str,
        program: EventProgram,
    ) -> int:
        program_id = self._intern_event_program(program)
        normalised = _normalise(template)
        existing = self.event_schema_ids.get(normalised)
        if existing is not None:
            return existing
        schema_id = len(self.event_schemas)
        self.event_schemas.append(EventSchema(normalised, program_id, program.support))
        self.event_schema_ids[normalised] = schema_id
        self._index_schema(normalised, schema_id, self.event_postings)
        return schema_id

    @staticmethod
    def _candidate_schemas(
        text: str,
        schemas: list[object],
        postings: dict[str, set[int]],
        max_candidates: int,
    ) -> tuple[list[int], int]:
        routes = sorted(
            (
                len(postings.get(anchor, ())),
                -len(anchor),
                anchor,
            )
            for anchor in _literal_anchors(text)
            if postings.get(anchor)
        )
        votes: Counter[int] = Counter()
        reads = 0
        for posting_size, negative_length, anchor in routes[:8]:
            weight = (-negative_length) ** 2 / max(1, posting_size)
            for schema_id in postings[anchor]:
                if schema_id < len(schemas):
                    votes[schema_id] += weight
                    reads += 1
            if len(votes) >= max_candidates:
                break
        return [item for item, _score in votes.most_common(max_candidates)], reads

    def _focus_entity(self, kind: str) -> str | None:
        for name, entity_kind in reversed(self.focus):
            self.last_focus_reads += 1
            if entity_kind == kind:
                return name
        return None

    def apply_event(self, text: str, *, source_id: str) -> EventRecord | None:
        normalised = _normalise(text)
        candidate_ids, reads = self._candidate_schemas(
            normalised,
            self.event_schemas,
            self.event_postings,
            self.max_candidates,
        )
        self.last_schema_reads = reads
        self.last_event_candidates = len(candidate_ids)
        self.last_focus_reads = 0
        for schema_id in candidate_ids:
            schema = self.event_schemas[schema_id]
            regex = self._event_regex_cache.get(schema_id)
            if regex is None:
                regex = _template_regex(schema.template)
                self._event_regex_cache[schema_id] = regex
            match = regex.match(normalised)
            if match is None:
                continue
            program = self.event_programs[schema.program_id]
            groups = match.groupdict()
            object_name = groups.get("object")
            if program.object_from_focus:
                object_name = self._focus_entity("object")
            new_value = groups.get("value")
            if not object_name or not new_value:
                continue
            agents = [
                groups.get(f"agent{index}")
                for index in range(16)
                if groups.get(f"agent{index}") is not None
            ]
            previous = self.world.get((object_name, program.attribute))
            event_id = len(self.events)
            updated_agents: list[str] = []
            fact = StateFact(new_value, str(source_id), event_id)
            self.world[(object_name, program.attribute)] = fact
            for slot in program.update_agent_slots:
                if slot >= len(agents):
                    continue
                agent = str(agents[slot])
                self.register_entity(agent, "agent")
                self.beliefs[(agent, object_name, program.attribute)] = fact
                updated_agents.append(agent)
            record = EventRecord(
                text=str(text),
                source_id=str(source_id),
                object_name=object_name,
                attribute=program.attribute,
                previous_value=previous.value if previous else None,
                new_value=new_value,
                updated_agents=tuple(updated_agents),
            )
            self.events.append(record)
            self.last_writer[(object_name, program.attribute)] = event_id
            self._remember(object_name, "object")
            self._remember(new_value, "value")
            for agent in agents:
                self._remember(str(agent), "agent")
            self.last_estimated_operations = (
                self.last_schema_reads + self.last_focus_reads + 2 + len(updated_agents)
            )
            return record
        return None
