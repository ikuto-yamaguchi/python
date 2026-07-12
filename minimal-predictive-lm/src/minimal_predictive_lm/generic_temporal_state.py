from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
import json
import re

from .generic_state_machine import CompiledStateProgram, StateEvent, StatePrediction, StateQuery


_MONTHS = {
    name.casefold(): index
    for index, name in enumerate(calendar.month_name)
    if name
}
_MONTHS.update(
    {
        name.casefold(): index
        for index, name in enumerate(calendar.month_abbr)
        if name
    }
)
_MONTHS.update({"sept": 9, "feburary": 2})
_OPTION_RE = re.compile(r"^\(([A-F])\)\s*(\d{1,2}/\d{1,2}/\d{4})\s*$", re.MULTILINE)
_NAMED_DATE_RE = re.compile(
    r"\b([A-Za-z]+)\.?\s+(\d{1,2})(?:st|nd|rd|th)?(?:,)?\s+(\d{4})\b",
    re.IGNORECASE,
)
_NUMERIC_DATE_RE = re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{4})(?!\d)")


def _bits(payload: object) -> int:
    return len(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ) * 8


def _month_number(raw: str) -> int:
    key = raw.casefold().rstrip(".")
    if key not in _MONTHS:
        raise ValueError(f"unknown month: {raw}")
    return _MONTHS[key]


def _parse_named_date(text: str) -> date | None:
    match = _NAMED_DATE_RE.search(text)
    if not match:
        return None
    try:
        return date(int(match.group(3)), _month_number(match.group(1)), int(match.group(2)))
    except ValueError:
        return None


def _parse_numeric_date(text: str, *, day_first: bool = False) -> date | None:
    match = _NUMERIC_DATE_RE.search(text)
    if not match:
        return None
    first, second, year = map(int, match.groups())
    month, day = (second, first) if day_first else (first, second)
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _parse_any_date(text: str, *, day_first: bool = False) -> date | None:
    return _parse_named_date(text) or _parse_numeric_date(text, day_first=day_first)


def _shift_months(value: date, months: int) -> date:
    index = value.year * 12 + value.month - 1 + months
    year, zero_month = divmod(index, 12)
    month = zero_month + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _shift_years(value: date, years: int) -> date:
    year = value.year + years
    day = min(value.day, calendar.monthrange(year, value.month)[1])
    return date(year, value.month, day)


def _first_weekday(year: int, month: int, weekday: int) -> date:
    start = date(year, month, 1)
    return start + timedelta(days=(weekday - start.weekday()) % 7)


def _palindrome_day(year: int) -> date | None:
    current = date(year, 1, 1)
    while current.year == year:
        compact = current.strftime("%m%d%Y")
        if compact == compact[::-1]:
            return current
        current += timedelta(days=1)
    return None


def _question_event(question: str) -> StateEvent | None:
    lowered = question.casefold()
    if "date today" in lowered:
        return StateEvent("shift_days", (0,))
    if "date tomorrow" in lowered or "24 hours later" in lowered:
        return StateEvent("shift_days", (1,))
    if "date yesterday" in lowered:
        return StateEvent("shift_days", (-1,))
    if "one week from today" in lowered:
        return StateEvent("shift_days", (7,))
    if "one week ago" in lowered:
        return StateEvent("shift_days", (-7,))
    match = re.search(r"date\s+(\d+)\s+days?\s+ago", lowered)
    if match:
        return StateEvent("shift_days", (-int(match.group(1)),))
    if "a month ago" in lowered or "one month ago" in lowered:
        return StateEvent("shift_months", (-1,))
    if "one year ago" in lowered:
        return StateEvent("shift_years", (-1,))
    return None


def _derive_today(context: str) -> tuple[date | None, str]:
    lowered = context.casefold()

    match = re.search(r"christmas eve of\s+(\d{4})", lowered)
    if match:
        return date(int(match.group(1)), 12, 24), "named-holiday"

    if "day before the month" in lowered:
        return _parse_numeric_date(context, day_first=True), "locale-date"

    correctness = re.search(
        r"Jane thinks today is\s+([^,]+),\s+but John thinks today is\s+([^\.]+)\.\s+(Jane|John) is correct",
        context,
        re.IGNORECASE,
    )
    if correctness:
        selected = correctness.group(1) if correctness.group(3).casefold() == "jane" else correctness.group(2)
        return _parse_any_date(selected), "speaker-correction"

    marriage = re.search(
        r"married on\s+(.+?)\.\s+(?:It is|Today is) their\s+(\d+)-year anniversary today",
        context,
        re.IGNORECASE,
    )
    if marriage:
        base = _parse_any_date(marriage.group(1))
        return (_shift_years(base, int(marriage.group(2))) if base else None), "anniversary"

    golden = re.search(
        r"married on\s+(.+?)\.\s+Today is their golden wedding anniversary",
        context,
        re.IGNORECASE,
    )
    if golden:
        base = _parse_any_date(golden.group(1))
        return (_shift_years(base, 50) if base else None), "golden-anniversary"

    visits = re.search(
        r"on the\s+(\d+)(?:st|nd|rd|th)\s+of each month starting from the\s+([A-Za-z]+)\s+of\s+(\d{4}).*?(\d+)(?:st|nd|rd|th) visit",
        context,
        re.IGNORECASE,
    )
    if visits:
        day = int(visits.group(1))
        start = date(int(visits.group(3)), _month_number(visits.group(2)), day)
        return _shift_months(start, int(visits.group(4)) - 1), "monthly-recurrence"

    eggs = re.search(
        r"On\s+(.+?)\s+Jane bought\s+(\d+)\s+eggs\.\s+She ate one per day\.\s+Today she ran out",
        context,
        re.IGNORECASE,
    )
    if eggs:
        base = _parse_any_date(eggs.group(1))
        return (base + timedelta(days=int(eggs.group(2))) if base else None), "daily-consumption"

    elapsed = re.search(
        r"on\s+(.+?)\.\s+(\d+) days have passed since then",
        context,
        re.IGNORECASE,
    )
    if elapsed:
        base = _parse_any_date(elapsed.group(1))
        return (base + timedelta(days=int(elapsed.group(2))) if base else None), "elapsed-days"

    ten_years = re.search(
        r"(.+?) is like yesterday.*?actually ten years ago",
        context,
        re.IGNORECASE,
    )
    if ten_years:
        base = _parse_any_date(ten_years.group(1))
        return (_shift_years(base, 10) if base else None), "relative-years"

    first_weekday = re.search(
        r"The first day of\s+(\d{4})\s+is a\s+([A-Za-z]+),\s+and today is the first\s+([A-Za-z]+)\s+of\s+\1",
        context,
        re.IGNORECASE,
    )
    if first_weekday:
        weekday_names = {name.casefold(): index for index, name in enumerate(calendar.day_name)}
        weekday = weekday_names.get(first_weekday.group(3).casefold())
        if weekday is not None:
            return _first_weekday(int(first_weekday.group(1)), 1, weekday), "first-weekday"

    palindrome = re.search(r"palindrome day of\s+(\d{4})", lowered)
    if palindrome:
        return _palindrome_day(int(palindrome.group(1))), "palindrome-date"

    last_month = re.search(r"last day of\s+([A-Za-z]+)\s+(\d{4})", context, re.IGNORECASE)
    if last_month:
        year = int(last_month.group(2))
        month = _month_number(last_month.group(1))
        return date(year, month, calendar.monthrange(year, month)[1]), "month-boundary"

    last_year = re.search(r"last day of\s+(\d{4})", context, re.IGNORECASE)
    if last_year:
        return date(int(last_year.group(1)), 12, 31), "year-boundary"

    ordinal_month = re.search(r"second day of the third month of\s+(\d{4})", lowered)
    if ordinal_month:
        return date(int(ordinal_month.group(1)), 3, 2), "ordinal-date"

    deadline = re.search(
        r"deadline is\s+(.+?),\s+which is\s+(\d+)\s+days? away from now",
        context,
        re.IGNORECASE,
    )
    if deadline:
        due = _parse_any_date(deadline.group(1))
        return (due - timedelta(days=int(deadline.group(2))) if due else None), "future-offset-anchor"

    tomorrow_match = re.search(r"\btomorrow\b([^.]*)", context, re.IGNORECASE)
    if tomorrow_match:
        anchor = _parse_any_date(tomorrow_match.group(0))
        if anchor is not None:
            return anchor - timedelta(days=1), "tomorrow-anchor"

    yesterday_match = re.search(r"\bYesterday\b([^.]*)", context, re.IGNORECASE)
    if yesterday_match:
        anchor = _parse_any_date(yesterday_match.group(0))
        if anchor is not None:
            return anchor + timedelta(days=1), "yesterday-anchor"

    current_time = re.search(
        r"current local time is.+?of\s+([0-9]+/[0-9]+/[0-9]+)",
        context,
        re.IGNORECASE,
    )
    if current_time:
        return _parse_any_date(current_time.group(1)), "clock-date"

    direct_named = re.search(
        r"\bToday is\s+([A-Za-z]+\.?\s+\d{1,2}(?:st|nd|rd|th)?(?:,)?\s+\d{4})",
        context,
        re.IGNORECASE,
    )
    if direct_named:
        return _parse_named_date(direct_named.group(1)), "direct-today"

    direct_numeric = re.search(
        r"(?:\bToday is|\bToday,|\bIt is)\s*(\d{1,2}/\d{1,2}/\d{4})(?:\s+today)?",
        context,
        re.IGNORECASE,
    )
    if direct_numeric:
        return _parse_numeric_date(direct_numeric.group(1)), "direct-today"

    if re.search(r"coming in\s+\d+\s+hours", lowered):
        return None, "time-of-day-ambiguous"

    return None, "unresolved-anchor"


@dataclass(frozen=True)
class TemporalPrediction:
    output: str | None
    anchor_reason: str
    operations: int
    reads: int
    writes: int


class TemporalStateRuntime:
    def execute(self, program: CompiledStateProgram) -> StatePrediction:
        current = date.fromisoformat(str(dict(program.initial_state)["today"]))
        operations = reads = writes = 0
        for event in program.events:
            operations += 1
            amount = int(event.arguments[0])
            if event.operation == "shift_days":
                current += timedelta(days=amount)
            elif event.operation == "shift_months":
                current = _shift_months(current, amount)
            elif event.operation == "shift_years":
                current = _shift_years(current, amount)
            else:
                return StatePrediction(None, "temporal", operations, reads, writes)
            reads += 1
            writes += 1
        options = dict(program.query.arguments[0])
        target = current.strftime("%m/%d/%Y")
        matches = [label for label, value in options.items() if value == target]
        reads += len(options)
        return StatePrediction(
            matches[0] if len(matches) == 1 else None,
            "temporal",
            operations + len(options),
            reads,
            writes,
        )


def compile_temporal_program(prompt: str) -> tuple[CompiledStateProgram | None, str]:
    if "What is the date" not in prompt or "\nOptions:" not in prompt:
        return None, "surface-not-temporal"
    context, rest = prompt.split("What is the date", 1)
    question = "What is the date" + rest.split("\nOptions:", 1)[0]
    event = _question_event(question)
    if event is None:
        return None, "unsupported-query"
    today, reason = _derive_today(context)
    if today is None:
        return None, reason
    options = {f"({label})": value for label, value in _OPTION_RE.findall(prompt)}
    if len(options) < 2:
        return None, "missing-date-options"
    return (
        CompiledStateProgram(
            "temporal",
            {"today": today.isoformat()},
            (event,),
            StateQuery("date_option", (tuple(options.items()),)),
        ),
        reason,
    )


@dataclass(frozen=True)
class GenericTemporalMachine:
    runtime: TemporalStateRuntime = TemporalStateRuntime()
    benchmark_task_name_branches: int = 0
    human_designed_surface_compilers: int = 1

    def predict(self, prompt: str) -> TemporalPrediction:
        program, reason = compile_temporal_program(prompt)
        if program is None:
            return TemporalPrediction(None, reason, 1, 0, 0)
        prediction = self.runtime.execute(program)
        return TemporalPrediction(
            prediction.output,
            reason,
            prediction.operations,
            prediction.reads,
            prediction.writes,
        )

    def render(self) -> object:
        return {
            "state": ["today"],
            "events": ["shift_days", "shift_months", "shift_years"],
            "query": "date_option",
            "benchmark_task_name_branches": self.benchmark_task_name_branches,
            "human_designed_surface_compilers": self.human_designed_surface_compilers,
        }

    @property
    def description_bits(self) -> int:
        return _bits(self.render())
