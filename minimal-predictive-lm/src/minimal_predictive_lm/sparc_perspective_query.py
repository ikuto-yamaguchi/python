from __future__ import annotations

from typing import Iterable

from .sparc_perspective_types import (
    _AGENT, _OBJECT, _VALUE, _answer_value, _normalise, _replace_all,
    CauseProgram, CauseSchema, FocusedQueryExample, QueryProgram, QuerySchema,
)


class PerspectiveQueryMixin:
    def _entities_in_text(self, text: str) -> tuple[str, ...]:
        self.last_entity_substring_checks = 0
        matches: list[str] = []
        maximum = min(self.max_entity_chars, len(text))
        for size in range(maximum, 0, -1):
            for start in range(len(text) - size + 1):
                self.last_entity_substring_checks += 1
                piece = text[start : start + size]
                if piece in self.entity_kinds:
                    matches.append(piece)
        unique = sorted(set(matches), key=lambda name: (-len(name), text.index(name), name))
        selected: list[str] = []
        for name in unique:
            span = (text.index(name), text.index(name) + len(name))
            if any(
                text.index(other) <= span[0]
                and span[1] <= text.index(other) + len(other)
                for other in selected
            ):
                continue
            selected.append(name)
        return tuple(sorted(selected, key=lambda name: (text.index(name), -len(name))))

    def _query_candidates_for_row(
        self,
        question: str,
        answer: str,
    ) -> set[tuple[str, str, str]]:
        answer = _answer_value(answer)
        entities = self._entities_in_text(question)
        objects = [name for name in entities if self.entity_kinds.get(name) == "object"]
        agents = [name for name in entities if self.entity_kinds.get(name) == "agent"]
        candidates: set[tuple[str, str, str]] = set()
        for object_name in objects:
            for (obj, attribute), fact in self.world.items():
                if obj == object_name and fact.value == answer:
                    template = _normalise(question).replace(object_name, _OBJECT, 1)
                    candidates.add(("world", attribute, template))
            for agent in agents:
                for (owner, obj, attribute), fact in self.beliefs.items():
                    if owner == agent and obj == object_name and fact.value == answer:
                        template = _replace_all(
                            _normalise(question),
                            {agent: _AGENT, object_name: _OBJECT},
                        )
                        candidates.add(("belief", attribute, template))
        return candidates

    def _focused_query_candidates(
        self,
        example: FocusedQueryExample,
    ) -> set[tuple[str, str, str, bool, bool]]:
        answer = _answer_value(example.answer)
        original_focus = tuple(self.focus)
        self.focus.clear()
        self.focus.extend(example.focus)
        try:
            entities = self._entities_in_text(example.question)
            explicit_objects = [
                name for name in entities if self.entity_kinds.get(name) == "object"
            ]
            explicit_agents = [
                name for name in entities if self.entity_kinds.get(name) == "agent"
            ]
            focused_object = self._focus_entity("object")
            focused_agent = self._focus_entity("agent")
            objects = explicit_objects or ([focused_object] if focused_object else [])
            agents = explicit_agents or ([focused_agent] if focused_agent else [])
            object_from_focus = not explicit_objects
            candidates: set[tuple[str, str, str, bool, bool]] = set()
            for object_name in objects:
                if object_name is None:
                    continue
                for (obj, attribute), fact in self.world.items():
                    if obj == object_name and fact.value == answer:
                        replacements = (
                            {object_name: _OBJECT} if not object_from_focus else {}
                        )
                        template = _replace_all(_normalise(example.question), replacements)
                        candidates.add(
                            ("world", attribute, template, False, object_from_focus)
                        )
                for agent in agents:
                    if agent is None:
                        continue
                    agent_from_focus = not explicit_agents
                    for (owner, obj, attribute), fact in self.beliefs.items():
                        if (
                            owner == agent
                            and obj == object_name
                            and fact.value == answer
                        ):
                            replacements: dict[str, str] = {}
                            if not agent_from_focus:
                                replacements[agent] = _AGENT
                            if not object_from_focus:
                                replacements[object_name] = _OBJECT
                            template = _replace_all(
                                _normalise(example.question), replacements
                            )
                            candidates.add(
                                (
                                    "belief",
                                    attribute,
                                    template,
                                    agent_from_focus,
                                    object_from_focus,
                                )
                            )
            return candidates
        finally:
            self.focus.clear()
            self.focus.extend(original_focus)

    def teach_focused_query(
        self, examples: Iterable[FocusedQueryExample]
    ) -> QueryProgram:
        rows = list(examples)
        if len(rows) < 2:
            raise ValueError("at least two focused query demonstrations are required")
        common: set[tuple[str, str, str, bool, bool]] | None = None
        for example in rows:
            candidates = self._focused_query_candidates(example)
            common = candidates if common is None else common & candidates
        if not common:
            raise ValueError("focused demonstrations share no grounded query program")
        mode, attribute, template, agent_from_focus, object_from_focus = min(
            common, key=lambda item: (item[0] != "belief", item)
        )
        program = QueryProgram(
            mode,
            attribute,
            agent_from_focus=agent_from_focus,
            object_from_focus=object_from_focus,
        )
        program_id = self._intern_query_program(program)
        if template not in self.query_schema_ids:
            schema_id = len(self.query_schemas)
            self.query_schemas.append(QuerySchema(template, program_id, len(rows)))
            self.query_schema_ids[template] = schema_id
            self._index_schema(template, schema_id, self.query_postings)
        return self.query_programs[program_id]

    def _intern_query_program(self, program: QueryProgram) -> int:
        key = (
            program.mode,
            program.attribute,
            program.agent_from_focus,
            program.object_from_focus,
        )
        existing = self.query_program_ids.get(key)
        if existing is not None:
            return existing
        if len(self.query_programs) >= self.max_query_programs:
            raise MemoryError("query-program capacity reached")
        program_id = len(self.query_programs)
        self.query_programs.append(program)
        self.query_program_ids[key] = program_id
        return program_id

    def teach_query(self, examples: Iterable[tuple[str, str]]) -> QueryProgram:
        rows = list(examples)
        if len(rows) < 2:
            raise ValueError("at least two query demonstrations are required")
        common: set[tuple[str, str, str]] | None = None
        for question, answer in rows:
            candidates = self._query_candidates_for_row(question, answer)
            common = candidates if common is None else common & candidates
        if not common:
            raise ValueError("query demonstrations share no grounded state program")
        mode, attribute, template = min(common, key=lambda item: (item[0] != "belief", item))
        program = QueryProgram(mode, attribute)
        program_id = self._intern_query_program(program)
        if template not in self.query_schema_ids:
            schema_id = len(self.query_schemas)
            self.query_schemas.append(QuerySchema(template, program_id, len(rows)))
            self.query_schema_ids[template] = schema_id
            self._index_schema(template, schema_id, self.query_postings)
        return self.query_programs[program_id]

    def link_query_surface(
        self,
        template: str,
        program: QueryProgram,
        *,
        agent_from_focus: bool = False,
        object_from_focus: bool = False,
    ) -> int:
        linked = QueryProgram(
            program.mode,
            program.attribute,
            agent_from_focus=agent_from_focus,
            object_from_focus=object_from_focus,
        )
        program_id = self._intern_query_program(linked)
        normalised = _normalise(template)
        existing = self.query_schema_ids.get(normalised)
        if existing is not None:
            return existing
        schema_id = len(self.query_schemas)
        self.query_schemas.append(QuerySchema(normalised, program_id, program.support if hasattr(program, "support") else 1))
        self.query_schema_ids[normalised] = schema_id
        self._index_schema(normalised, schema_id, self.query_postings)
        return schema_id

    def teach_cause_query(
        self,
        examples: Iterable[tuple[str, str]],
        *,
        attribute: str,
    ) -> CauseProgram:
        rows = list(examples)
        if len(rows) < 2:
            raise ValueError("at least two cause demonstrations are required")
        templates: set[str] = set()
        for question, answer in rows:
            entities = self._entities_in_text(question)
            objects = [name for name in entities if self.entity_kinds.get(name) == "object"]
            matched = False
            for object_name in objects:
                event_id = self.last_writer.get((object_name, attribute))
                if event_id is not None and self.events[event_id].text == answer.strip():
                    fact = self.world.get((object_name, attribute))
                    replacements = {object_name: _OBJECT}
                    if fact is not None and fact.value in question:
                        replacements[fact.value] = _VALUE
                    templates.add(_replace_all(_normalise(question), replacements))
                    matched = True
                    break
            if not matched:
                raise ValueError("cause answer is not the direct local writer event")
        if len(templates) != 1:
            raise ValueError("cause demonstrations do not share one surface")
        template = next(iter(templates))
        key = (attribute, False)
        program_id = self.cause_program_ids.get(key)
        if program_id is None:
            program_id = len(self.cause_programs)
            self.cause_programs.append(CauseProgram(attribute, False))
            self.cause_program_ids[key] = program_id
        if template not in self.cause_schema_ids:
            schema_id = len(self.cause_schemas)
            self.cause_schemas.append(CauseSchema(template, program_id, len(rows)))
            self.cause_schema_ids[template] = schema_id
            self._index_schema(template, schema_id, self.cause_postings)
        return self.cause_programs[program_id]

    def link_cause_surface(
        self,
        template: str,
        program: CauseProgram,
        *,
        object_from_focus: bool = False,
    ) -> int:
        linked = CauseProgram(program.attribute, object_from_focus)
        key = (linked.attribute, linked.object_from_focus)
        program_id = self.cause_program_ids.get(key)
        if program_id is None:
            program_id = len(self.cause_programs)
            self.cause_programs.append(linked)
            self.cause_program_ids[key] = program_id
        normalised = _normalise(template)
        schema_id = len(self.cause_schemas)
        self.cause_schemas.append(CauseSchema(normalised, program_id, 1))
        self.cause_schema_ids[normalised] = schema_id
        self._index_schema(normalised, schema_id, self.cause_postings)
        return schema_id
