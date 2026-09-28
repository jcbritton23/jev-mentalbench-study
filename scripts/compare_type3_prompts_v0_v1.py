"""Small paired, exploration-only Type 3 comparison; never prints case text."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
import os
import sys
import time

from typesafe_sdk import Noul, NoulCriteria, TypeSafeClient

try:
    from .pilot_23way import (MODEL, ROOT, ROW_SPLIT, SOURCE, build_questions,
        parse_answer_labels, parse_diagnosis_inventory, parse_markdown_guides,
        parse_noul_answer, parse_option_labels)
    from .smoke_test import PRICE_PER_INPUT_TOKEN_USD, load_local_key
except ImportError:
    from pilot_23way import (MODEL, ROOT, ROW_SPLIT, SOURCE, build_questions,
        parse_answer_labels, parse_diagnosis_inventory, parse_markdown_guides,
        parse_noul_answer, parse_option_labels)
    from smoke_test import PRICE_PER_INPUT_TOKEN_USD, load_local_key


PAIRS = ("D003_D008", "D005_D018", "D019_D020")
OUTPUT = ROOT / "results/type3_v0_v1_fresh_3case.json"


def build_v1_questions(names: dict[str, str]) -> dict[str, Noul]:
    questions = {}
    for code, name in sorted(names.items()):
        extra = ""
        if code in {"D001", "D002", "D003"}:
            extra += " Use `shared_references.ADHD_symptom_domains` for symptom domains and age thresholds."
        if code == "D015":
            extra += " Apply D013 depressive-episode domains; psychotic symptoms must overlap a qualifying episode and mood shift."
        if code == "D013":
            extra += " For this plain MDD benchmark label, favor it when a major depressive episode is supported and episode-linked psychotic features are not clearly described. If psychosis is uncertain, both plain and psychotic-feature labels may remain plausible."
        if code == "D008":
            extra += " For this plain bipolar I benchmark label, favor it when a manic episode is supported and episode-linked psychotic features are not clearly described. If psychosis is uncertain, both plain and psychotic-feature labels may remain plausible."
        instructions = (
            f"Based on `case_text`, the full set in `candidate_diagnoses`, and `diagnostic_guides.{code}`{extra} "
            f"does the description meaningfully support retaining {name} ({code}) as a plausible diagnostic candidate? "
            "Consider the overall clinical pattern, course, impairment, and distinguishing evidence. "
            "Treat unreported details as unknown rather than absent; weigh explicit contrary evidence. "
            "More than one candidate may remain plausible when the case does not resolve the differential."
        )
        questions[code] = Noul(
            instructions=instructions,
            criteria=NoulCriteria(
                true=(f"The best available evidence meaningfully supports {name} ({code}) as a plausible candidate, "
                      "even if a selective description leaves some details unknown or another candidate also fits."),
                false=(f"The described syndrome fits {name} ({code}) poorly, or explicit evidence contradicts "
                       "a defining feature or resolves the differential against this diagnosis."),
            ),
        )
    return questions


def select_rows() -> list[dict]:
    with ROW_SPLIT.open(encoding="utf-8", newline="") as stream:
        assignments = {int(r["row_index"]): r for r in csv.DictReader(stream)}
    candidates = {pair: [] for pair in PAIRS}
    with SOURCE.open(encoding="utf-8-sig", newline="") as stream:
        for row_index, row in enumerate(csv.DictReader(stream)):
            assignment = assignments.get(row_index)
            if (assignment and assignment["split"] == "exploration"
                    and row["type"] == "type3" and row["code"] in candidates):
                order = hashlib.sha256(f"jev-type3-paired-fresh-v1|{row['code']}|{row_index}".encode()).hexdigest()
                candidates[row["code"]].append((order, {**row, "_row_index": row_index,
                                                       "_group_id": assignment["group_id"]}))
    rows = []
    for pair in PAIRS:
        if not candidates[pair]:
            raise RuntimeError(f"No exploration row for {pair}")
        rows.append(sorted(candidates[pair], key=lambda item: item[0])[0][1])
    if len({r["_group_id"] for r in rows}) != len(rows):
        raise RuntimeError("Selected rows share a source group")
    return rows


def save(cases: list[dict], failures: list[dict]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({
        "version": "type3_v0_v1_fresh_3case", "model": MODEL,
        "selection": "Hash-selected exploration-only Type 3 rows from three independent, previously untested pair groups",
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "contains_case_text": False, "contains_raw_api_payload": False,
        "cases": cases, "failures": failures,
        "aggregate_usage": {
            "input_tokens": sum(x["input_tokens"] for c in cases for x in c["arms"].values()),
            "output_tokens": sum(x["output_tokens"] for c in cases for x in c["arms"].values()),
            "estimated_cost_usd": round(sum(x["estimated_cost_usd"] for c in cases for x in c["arms"].values()), 10),
        },
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    load_local_key()
    if not os.environ.get("TYPESAFE_API_KEY"):
        print("TYPESAFE_API_KEY is not configured; no request was sent.", file=sys.stderr)
        return 2
    if OUTPUT.exists():
        print("Result exists; no duplicate request sent.", file=sys.stderr)
        return 2
    names = parse_diagnosis_inventory()
    guides, shared_adhd = parse_markdown_guides()
    rows = select_rows()
    candidates = [{"code": code, "name": names[code]} for code in sorted(names)]
    question_sets = {"v0": build_questions(names), "v1": build_v1_questions(names)}
    name_to_code = {name: code for code, name in names.items()}
    cases, failures = [], []
    with TypeSafeClient() as client:
        for row in rows:
            options = parse_option_labels(row["option"])
            keys = parse_answer_labels(row["answer"], row["option"])
            if len(options) != 4 or len(keys) != 2 or not set(keys) <= set(options):
                raise RuntimeError("Could not parse local Type 3 options/key")
            key_codes = [name_to_code[name] for name in keys]
            option_codes = [name_to_code[name] for name in options]
            state = {"case_text": row["question"], "candidate_diagnoses": candidates,
                     "diagnostic_guides": guides,
                     "shared_references": {"ADHD_symptom_domains": shared_adhd}}
            case = {"pair_code": row["code"], "source_row_index": row["_row_index"],
                    "source_group_id": row["_group_id"], "case_type": "type3",
                    "benchmark_key_codes": key_codes, "offered_option_codes": option_codes,
                    "arms": {}}
            cases.append(case)
            for version, questions in question_sets.items():
                started = time.perf_counter()
                try:
                    response = client.system_one(model=MODEL, state=state, questions=questions)
                    elapsed = time.perf_counter() - started
                    if len(response.answers) != 23:
                        raise RuntimeError("Expected 23 answers")
                    probabilities = {code: parse_noul_answer(response.answers[code]) for code in names}
                    ranked = sorted(probabilities, key=lambda code: (-probabilities[code], code))
                    case["arms"][version] = {
                        "model": response.model, "elapsed_seconds": round(elapsed, 4),
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                        "estimated_cost_usd": round(response.usage.input_tokens * PRICE_PER_INPUT_TOKEN_USD, 10),
                        "probabilities": probabilities,
                        "key_probabilities": {code: probabilities[code] for code in key_codes},
                        "key_ranks": {code: ranked.index(code) + 1 for code in key_codes},
                        "top1_code": ranked[0], "top1_probability": probabilities[ranked[0]],
                        "n_all23_at_0_5": sum(p >= 0.5 for p in probabilities.values()),
                        "offered_set_at_0_5": [code for code in option_codes if probabilities[code] >= 0.5],
                    }
                    save(cases, failures)
                except Exception as exc:
                    failures.append({"pair_code": row["code"], "version": version,
                                     "error_type": type(exc).__name__,
                                     "elapsed_seconds": round(time.perf_counter() - started, 4)})
                    save(cases, failures)
                    print(json.dumps({"error_type": type(exc).__name__, "partial_results_saved": True}), file=sys.stderr)
                    return 1
    print(json.dumps({"cases": [
        {"pair_code": c["pair_code"], "key_codes": c["benchmark_key_codes"],
         "arms": {v: {k: a[k] for k in ("key_probabilities", "key_ranks", "top1_code", "n_all23_at_0_5", "offered_set_at_0_5", "elapsed_seconds", "input_tokens", "estimated_cost_usd")}
                  for v, a in c["arms"].items()}}
        for c in cases],
        "total_cost_usd": round(sum(a["estimated_cost_usd"] for c in cases for a in c["arms"].values()), 10)},
        indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
