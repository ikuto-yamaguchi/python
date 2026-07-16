from __future__ import annotations

import json
import zlib
from dataclasses import asdict

from .sparc_language import ReplyResult
from .sparc_perspective_types import (
    _AGENT, _normalise, _template_regex, CauseProgram, CauseSchema, EventProgram,
    EventRecord, EventSchema, QueryProgram, QuerySchema, StateFact,
)


class PerspectiveRuntimeMixin:
    def _solve_state(self, text: str) -> ReplyResult | None:
        candidate_ids, reads = self._candidate_schemas(
            text,
            self.query_schemas,
            self.query_postings,
            self.max_candidates,
        )
        self.last_schema_reads = reads
        self.last_query_candidates = len(candidate_ids)
        self.last_state_reads = 0
        self.last_focus_reads = 0
        for schema_id in candidate_ids:
            schema = self.query_schemas[schema_id]
            regex = self._query_regex_cache.get(schema_id)
            if regex is None:
                regex_template = schema.template.replace(_AGENT, "<AGENT0>")
                regex = _template_regex(regex_template)
                self._query_regex_cache[schema_id] = regex
            match = regex.match(text)
            if match is None:
                continue
            program = self.query_programs[schema.program_id]
            groups = match.groupdict()
            object_name = groups.get("object")
            agent = groups.get("agent0")
            if program.object_from_focus:
                object_name = self._focus_entity("object")
            if program.agent_from_focus:
                agent = self._focus_entity("agent")
            if not object_name:
                continue
            fact: StateFact | None
            if program.mode == "world":
                self.last_state_reads += 1
                fact = self.world.get((object_name, program.attribute))
                perspective = "実際"
            else:
                if not agent:
                    continue
                self.last_state_reads += 1
                fact = self.beliefs.get((agent, object_name, program.attribute))
                perspective = f"{agent}の認識"
            if fact is None:
                return ReplyResult(
                    text=f"{perspective}では、{object_name}の{program.attribute}は未確定です。",
                    confidence=0.35,
                    mechanism="calibrated-perspective-unknown",
                    candidates_inspected=self.last_query_candidates,
                    active_bits=1,
                    estimated_sparse_operations=reads + self.last_focus_reads + 1,
                )
            self._remember(object_name, "object")
            if agent:
                self._remember(agent, "agent")
            operations = reads + self.last_focus_reads + self.last_state_reads + 2
            self.last_estimated_operations = operations
            return ReplyResult(
                text=(
                    f"{fact.value}です。{perspective}における"
                    f"{object_name}の{program.attribute}を参照しました。"
                    f"出典: ［{fact.source_id}］"
                ),
                confidence=0.91,
                mechanism="learned-perspective-state-query",
                candidates_inspected=self.last_query_candidates,
                active_bits=2,
                estimated_sparse_operations=operations,
            )
        return None

    def _solve_cause(self, text: str) -> ReplyResult | None:
        candidate_ids, reads = self._candidate_schemas(
            text,
            self.cause_schemas,
            self.cause_postings,
            self.max_candidates,
        )
        for schema_id in candidate_ids:
            schema = self.cause_schemas[schema_id]
            regex = self._cause_regex_cache.get(schema_id)
            if regex is None:
                regex = _template_regex(schema.template)
                self._cause_regex_cache[schema_id] = regex
            match = regex.match(text)
            if match is None:
                continue
            program = self.cause_programs[schema.program_id]
            object_name = match.groupdict().get("object")
            self.last_focus_reads = 0
            if program.object_from_focus:
                object_name = self._focus_entity("object")
            if not object_name:
                continue
            self.last_state_reads = 1
            event_id = self.last_writer.get((object_name, program.attribute))
            if event_id is None:
                return ReplyResult(
                    text=f"{object_name}の{program.attribute}を直接変えた出来事は記録されていません。",
                    confidence=0.35,
                    mechanism="calibrated-causal-unknown",
                    candidates_inspected=len(candidate_ids),
                    active_bits=1,
                    estimated_sparse_operations=reads + self.last_focus_reads + 1,
                )
            event = self.events[event_id]
            self._remember(object_name, "object")
            operations = reads + self.last_focus_reads + 2
            self.last_estimated_operations = operations
            return ReplyResult(
                text=(
                    f"直接の原因は「{event.text}」です。"
                    f"この出来事が{object_name}の{program.attribute}を"
                    f"{event.previous_value}から{event.new_value}へ更新しました。"
                    f"出典: ［{event.source_id}］"
                ),
                confidence=0.90,
                mechanism="local-counterfactual-writer-cause",
                candidates_inspected=len(candidate_ids),
                active_bits=2,
                estimated_sparse_operations=operations,
            )
        return None

    def answer(self, text: str) -> ReplyResult | None:
        normalised = _normalise(text)
        cause = self._solve_cause(normalised)
        if cause is not None:
            return cause
        return self._solve_state(normalised)

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-perspective-state-hs15",
            "limits": {
                "max_event_programs": self.max_event_programs,
                "max_query_programs": self.max_query_programs,
                "max_schemas": self.max_schemas,
                "max_candidates": self.max_candidates,
                "focus_size": self.focus.maxlen or 16,
            },
            "world": [
                [obj, attr, fact.value, fact.source_id, fact.event_id]
                for (obj, attr), fact in self.world.items()
            ],
            "beliefs": [
                [agent, obj, attr, fact.value, fact.source_id, fact.event_id]
                for (agent, obj, attr), fact in self.beliefs.items()
            ],
            "entity_kinds": self.entity_kinds,
            "events": [asdict(event) for event in self.events],
            "last_writer": [[obj, attr, event_id] for (obj, attr), event_id in self.last_writer.items()],
            "focus": list(self.focus),
            "event_programs": [asdict(item) for item in self.event_programs],
            "event_schemas": [asdict(item) for item in self.event_schemas],
            "query_programs": [asdict(item) for item in self.query_programs],
            "query_schemas": [asdict(item) for item in self.query_schemas],
            "cause_programs": [asdict(item) for item in self.cause_programs],
            "cause_schemas": [asdict(item) for item in self.cause_schemas],
        }
        return zlib.compress(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8"),
            9,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "SparsePerspectiveWorkspace":
        payload = json.loads(zlib.decompress(data))
        limits = payload["limits"]
        model = cls(
            max_event_programs=int(limits["max_event_programs"]),
            max_query_programs=int(limits["max_query_programs"]),
            max_schemas=int(limits["max_schemas"]),
            max_candidates=int(limits["max_candidates"]),
            focus_size=int(limits["focus_size"]),
        )
        for name, kind in payload["entity_kinds"].items():
            model.register_entity(str(name), str(kind))
        for obj, attr, value, source, event_id in payload["world"]:
            model.world[(str(obj), str(attr))] = StateFact(str(value), str(source), None if event_id is None else int(event_id))
        for agent, obj, attr, value, source, event_id in payload["beliefs"]:
            model.beliefs[(str(agent), str(obj), str(attr))] = StateFact(str(value), str(source), None if event_id is None else int(event_id))
        model.events = [
            EventRecord(
                str(row["text"]),
                str(row["source_id"]),
                str(row["object_name"]),
                str(row["attribute"]),
                None if row["previous_value"] is None else str(row["previous_value"]),
                str(row["new_value"]),
                tuple(str(item) for item in row["updated_agents"]),
            )
            for row in payload["events"]
        ]
        for obj, attr, event_id in payload["last_writer"]:
            model.last_writer[(str(obj), str(attr))] = int(event_id)
        model.focus.extend((str(name), str(kind)) for name, kind in payload["focus"])
        for row in payload["event_programs"]:
            model._intern_event_program(
                EventProgram(
                    str(row["attribute"]),
                    tuple(int(item) for item in row["update_agent_slots"]),
                    bool(row["object_from_focus"]),
                    int(row["support"]),
                )
            )
        for row in payload["event_schemas"]:
            schema_id = len(model.event_schemas)
            schema = EventSchema(str(row["template"]), int(row["program_id"]), int(row["support"]))
            model.event_schemas.append(schema)
            model.event_schema_ids[schema.template] = schema_id
            model._index_schema(schema.template, schema_id, model.event_postings)
        for row in payload["query_programs"]:
            model._intern_query_program(
                QueryProgram(
                    str(row["mode"]),
                    str(row["attribute"]),
                    bool(row["agent_from_focus"]),
                    bool(row["object_from_focus"]),
                )
            )
        for row in payload["query_schemas"]:
            schema_id = len(model.query_schemas)
            schema = QuerySchema(str(row["template"]), int(row["program_id"]), int(row["support"]))
            model.query_schemas.append(schema)
            model.query_schema_ids[schema.template] = schema_id
            model._index_schema(schema.template, schema_id, model.query_postings)
        for row in payload["cause_programs"]:
            program = CauseProgram(str(row["attribute"]), bool(row["object_from_focus"]))
            key = (program.attribute, program.object_from_focus)
            model.cause_program_ids[key] = len(model.cause_programs)
            model.cause_programs.append(program)
        for row in payload["cause_schemas"]:
            schema_id = len(model.cause_schemas)
            schema = CauseSchema(str(row["template"]), int(row["program_id"]), int(row["support"]))
            model.cause_schemas.append(schema)
            model.cause_schema_ids[schema.template] = schema_id
            model._index_schema(schema.template, schema_id, model.cause_postings)
        return model

    def report(self) -> dict[str, int | bool]:
        return {
            "world_slots": len(self.world),
            "belief_slots": len(self.beliefs),
            "entities": len(self.entity_kinds),
            "events": len(self.events),
            "event_programs": len(self.event_programs),
            "event_schemas": len(self.event_schemas),
            "query_programs": len(self.query_programs),
            "query_schemas": len(self.query_schemas),
            "cause_programs": len(self.cause_programs),
            "cause_schemas": len(self.cause_schemas),
            "serialized_bytes": len(self.to_bytes()),
            "last_event_candidates": self.last_event_candidates,
            "last_query_candidates": self.last_query_candidates,
            "last_schema_reads": self.last_schema_reads,
            "last_state_reads": self.last_state_reads,
            "last_focus_reads": self.last_focus_reads,
            "last_entity_substring_checks": self.last_entity_substring_checks,
            "last_estimated_operations": self.last_estimated_operations,
            "global_world_scan_used": False,
            "global_belief_scan_used": False,
            "full_history_scan_used": False,
        }
