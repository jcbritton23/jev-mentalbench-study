"""Run three blinded, exploration-only all-23 Jev pilot requests.

Reads benchmark text locally and sends only three selected exploration rows to
TypeSafe. Supplied options and answer keys are used locally for scoring and are
never included in the API state. Neither input text nor raw API payloads are
written to the results artifact or printed.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import time

from typesafe_sdk import Noul, NoulCriteria, TypeSafeClient

try:
    from .smoke_test import PRICE_PER_INPUT_TOKEN_USD, load_local_key
except ImportError:
    from smoke_test import PRICE_PER_INPUT_TOKEN_USD, load_local_key


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/raw/mentalbench.csv"
ROW_SPLIT = ROOT / "data/processed/mentalbench_row_split_v1.csv"
INVENTORY = ROOT / "prompts/mentalbench_v0.md"
GUIDE_FILES = (
    ROOT / "prompts/basic_diagnosis_guides_v0.md",
    ROOT / "prompts/complex_diagnosis_guides_v0.md",
)
MDD_GUIDE = ROOT / "prompts/d013_mdd_sample_v0.md"
OUTPUT = ROOT / "results/first_draft_23way_3case_v0.json"
MODEL = "jev-1.13.0"
PILOT_TYPES = ("type1", "type2", "type3")
THRESHOLDS = (0.50, 0.70, 0.80, 0.90)


def parse_option_labels(value: str) -> list[str]:
    return [m.group(2).strip() for m in re.finditer(r"(?m)^\s*([A-D])\.\s+(.+?)\s*$", value)]


def parse_answer_labels(value: str, option_text: str) -> list[str]:
    option_map = {
        match.group(1): match.group(2).strip()
        for match in re.finditer(r"(?m)^\s*([A-D])\.\s+(.+?)\s*$", option_text)
    }
    prefix = re.match(r"^\s*([A-D](?:\s*&\s*[A-D])*)\.", value)
    if prefix:
        letters = re.findall(r"[A-D]", prefix.group(1))
        return [option_map[letter] for letter in letters if letter in option_map]
    return parse_option_labels(value)


def parse_diagnosis_inventory() -> dict[str, str]:
    inventory: dict[str, str] = {}
    for code, name in re.findall(r"(?m)^\| (D\d{3}) \| (.+?) \|$", INVENTORY.read_text(encoding="utf-8")):
        inventory[code] = name
    if len(inventory) != 23:
        raise RuntimeError("Expected the current 23-label inventory")
    return inventory


def parse_markdown_guides() -> tuple[dict[str, str], str]:
    guides: dict[str, str] = {}
    shared_adhd = ""
    for path in GUIDE_FILES:
        text = path.read_text(encoding="utf-8")
        headings = list(re.finditer(r"(?m)^## (D\d{3}) — (.+)$", text))
        for index, heading in enumerate(headings):
            end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            guides[heading.group(1)] = text[heading.start():end].strip()
        if path.name == "complex_diagnosis_guides_v0.md":
            match = re.search(
                r"(?ms)^## ADHD symptom-domain reference.*?(?=^## D001)", text
            )
            if match:
                shared_adhd = match.group(0).strip()

    blocks = re.findall(r"```json\n(.*?)\n```", MDD_GUIDE.read_text(encoding="utf-8"), re.S)
    if not blocks:
        raise RuntimeError("Could not read the D013 clinical guide entry")
    d013 = json.loads(blocks[0])
    guides[d013["code"]] = json.dumps(d013, ensure_ascii=False, separators=(",", ":"))

    if set(guides) != {f"D{i:03d}" for i in range(1, 24)}:
        raise RuntimeError("Guide entries do not cover exactly the 23 benchmark labels")
    if not shared_adhd:
        raise RuntimeError("Could not read the shared ADHD symptom reference")
    return guides, shared_adhd


def select_exploration_rows() -> list[dict]:
    with ROW_SPLIT.open(encoding="utf-8", newline="") as stream:
        assignments = {int(row["row_index"]): row for row in csv.DictReader(stream)}

    candidates: dict[str, list[tuple[str, dict]]] = {case_type: [] for case_type in PILOT_TYPES}
    with SOURCE.open(encoding="utf-8-sig", newline="") as stream:
        for row_index, row in enumerate(csv.DictReader(stream)):
            assignment = assignments.get(row_index)
            if assignment and assignment["split"] == "exploration" and row["type"] in candidates:
                group_id = assignment["group_id"]
                order = hashlib.sha256(f"jev-first-draft-pilot-v0|{row['type']}|{group_id}".encode()).hexdigest()
                candidates[row["type"]].append((order, {**row, "_row_index": row_index, "_group_id": group_id}))

    selected = []
    seen_groups = set()
    for case_type in PILOT_TYPES:
        ordered = sorted(candidates[case_type], key=lambda item: item[0])
        row = next((candidate for _, candidate in ordered if candidate["_group_id"] not in seen_groups), None)
        if row is None:
            raise RuntimeError(f"No independent exploration case available for {case_type}")
        selected.append(row)
        seen_groups.add(row["_group_id"])
    return selected


def parse_noul_answer(answer) -> float:
    value = getattr(answer, "noul", None)
    if value is None:
        raise RuntimeError("Jev response did not contain a Noul probability")
    return float(value)


def build_questions(names: dict[str, str]) -> dict[str, Noul]:
    questions = {}
    for code, name in sorted(names.items()):
        guide_ref = f"`diagnostic_guides.{code}`"
        extra = (
            " Also use `shared_references.ADHD_symptom_domains` for the current-presentation symptom domains and age thresholds."
            if code in {"D001", "D002", "D003"}
            else ""
        )
        if code == "D015":
            extra += " Apply the D013 guide's depressive-episode symptom domains, and require psychotic symptoms to overlap that qualifying episode and mood shift."
        instructions = (
            f"Based on `case_text`, the full set in `candidate_diagnoses`, and {guide_ref}{extra} "
            f"does the description meaningfully support retaining {name} ({code}) as a plausible diagnostic candidate? "
            "Consider the overall clinical pattern, course, impairment, and distinguishing evidence. "
            "Treat unreported details as unknown rather than absent; weigh explicit contrary evidence. "
            "More than one candidate may remain plausible when the case does not resolve the differential."
        )
        questions[code] = Noul(
            instructions=instructions,
            criteria=NoulCriteria(
                true=(
                    f"The best available evidence meaningfully supports {name} ({code}) as a plausible candidate, "
                    "even if a selective description leaves some details unknown."
                ),
                false=(
                    f"The described pattern fits {name} ({code}) poorly, or explicit evidence materially weighs "
                    "against it or supports a better-fitting alternative."
                ),
            ),
        )
    return questions


def main() -> int:
    load_local_key()
    if not __import__("os").environ.get("TYPESAFE_API_KEY"):
        print("TYPESAFE_API_KEY is not configured locally; no request was sent.", file=sys.stderr)
        return 2
    if not SOURCE.exists() or not ROW_SPLIT.exists():
        print("The local MentalBench file or frozen split manifest is missing; no request was sent.", file=sys.stderr)
        return 2

    names = parse_diagnosis_inventory()
    guides, shared_adhd = parse_markdown_guides()
    rows = select_exploration_rows()
    all_candidates = [{"code": code, "name": names[code]} for code in sorted(names)]
    output_cases = []
    failures = []
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost = 0.0

    with TypeSafeClient() as client:
        for case_number, row in enumerate(rows, start=1):
            options = parse_option_labels(row["option"])
            keys = parse_answer_labels(row["answer"], row["option"])
            if not options or not keys or not set(keys) <= set(options):
                raise RuntimeError("Could not resolve the local option/answer labels for a selected row")

            state = {
                "case_text": row["question"],
                "candidate_diagnoses": all_candidates,
                "diagnostic_guides": guides,
                "shared_references": {"ADHD_symptom_domains": shared_adhd},
            }

            questions = build_questions(names)

            started_at = datetime.now(timezone.utc).isoformat()
            started = time.perf_counter()
            try:
                response = client.system_one(model=MODEL, state=state, questions=questions)
                elapsed = time.perf_counter() - started
                if len(response.answers) != 23:
                    raise RuntimeError(f"Expected 23 answers, received {len(response.answers)}")
                probabilities = {code: parse_noul_answer(response.answers[code]) for code in names}
                ranked = sorted(probabilities.items(), key=lambda item: (-item[1], item[0]))
                top_code, top_probability = ranked[0]
                option_names = {name: code for code, name in names.items()}
                option_codes = [option_names[label] for label in options if label in option_names]
                key_codes = [option_names[label] for label in keys if label in option_names]
                case_cost = response.usage.input_tokens * PRICE_PER_INPUT_TOKEN_USD

                case_result = {
                    "case_label": f"pilot_{case_number}_{row['type']}",
                    "source_row_index": row["_row_index"],
                    "source_group_id": row["_group_id"],
                    "case_type": row["type"],
                    "model": response.model,
                    "elapsed_seconds": round(elapsed, 4),
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "estimated_cost_usd": round(case_cost, 10),
                    "benchmark_key_codes": key_codes,
                    "offered_option_codes": option_codes,
                    "top1_code": top_code,
                    "top1_probability": round(top_probability, 6),
                    "top1_in_benchmark_key": top_code in key_codes,
                    "key_probabilities_and_ranks": {
                        code: {
                            "diagnosis": names[code],
                            "probability": round(probabilities[code], 6),
                            "rank": next(i for i, (ranked_code, _) in enumerate(ranked, start=1) if ranked_code == code),
                        }
                        for code in key_codes
                    },
                    "top_5": [
                        {"code": code, "diagnosis": names[code], "probability": round(probability, 6)}
                        for code, probability in ranked[:5]
                    ],
                    "all_23_probabilities": {
                        code: round(probabilities[code], 6)
                        for code in sorted(probabilities)
                    },
                    "key_recall_at_3": sum(code in {c for c, _ in ranked[:3]} for code in key_codes) / len(key_codes),
                    "known_key_recall_by_threshold": {
                        f"{threshold:.2f}": sum(probabilities[code] >= threshold for code in key_codes) / len(key_codes)
                        for threshold in THRESHOLDS
                    },
                }
                output_cases.append(case_result)
                total_input_tokens += response.usage.input_tokens
                total_output_tokens += response.usage.output_tokens
                total_cost += case_cost
                write_result(output_cases, failures, total_input_tokens, total_output_tokens, total_cost)
            except Exception as exc:  # save only safe error class, never provider text/input
                elapsed = time.perf_counter() - started
                failures.append({
                    "case_label": f"pilot_{case_number}_{row['type']}",
                    "case_type": row["type"],
                    "elapsed_seconds": round(elapsed, 4),
                    "error_type": type(exc).__name__,
                })
                write_result(output_cases, failures, total_input_tokens, total_output_tokens, total_cost)
                print(json.dumps({"partial_results_saved": True, "failed_case_type": row["type"], "error_type": type(exc).__name__}), file=sys.stderr)
                return 1

    summary = make_summary(output_cases, failures, total_input_tokens, total_output_tokens, total_cost)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    write_result(output_cases, failures, total_input_tokens, total_output_tokens, total_cost)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def make_summary(cases, failures, input_tokens, output_tokens, cost):
    matches = sum(case["top1_in_benchmark_key"] for case in cases)
    return {
        "model": cases[0]["model"] if cases else MODEL,
        "study_arm": "all_23_candidates; supplied options and answers hidden from Jev",
        "case_types_selected": [case["case_type"] for case in cases],
        "successful_requests": len(cases),
        "failed_requests": len(failures),
        "questions_per_request": 23,
        "top1_benchmark_key_hits": matches,
        "top1_benchmark_key_rate": (matches / len(cases)) if cases else None,
        "case_summaries": [
            {
                "case_label": case["case_label"],
                "case_type": case["case_type"],
                "benchmark_key": case["benchmark_key_codes"],
                "top1": {"code": case["top1_code"], "probability": case["top1_probability"]},
                "top1_in_key": case["top1_in_benchmark_key"],
                "key_probabilities_and_ranks": case["key_probabilities_and_ranks"],
                "top_5": case["top_5"],
                "key_recall_at_3": case["key_recall_at_3"],
            }
            for case in cases
        ],
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
        "estimated_cost_usd": round(cost, 10),
        "elapsed_seconds_total_sequential": round(sum(case["elapsed_seconds"] for case in cases) + sum(f["elapsed_seconds"] for f in failures), 4),
        "elapsed_seconds_by_case": {case["case_label"]: case["elapsed_seconds"] for case in cases},
        "limitations": [
            "Three exploration cases are a prompt smoke test, not an accuracy estimate.",
            "Only supplied benchmark labels are adjudicated; diagnoses outside the supplied options are unverified by this key.",
            "Jev probabilities are per-diagnosis yes probabilities, not probabilities that a diagnosis is the top of 23.",
        ],
    }


def write_result(cases, failures, input_tokens, output_tokens, cost):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "pilot_version": "first_draft_23way_3case_v0",
        "started_or_updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": cases[0]["model"] if cases else MODEL,
        "cases": cases,
        "failures": failures,
        "aggregate_usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost_usd": round(cost, 10),
        },
        "contains_case_text": False,
        "contains_raw_api_payload": False,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
