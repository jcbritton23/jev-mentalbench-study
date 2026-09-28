"""Test the revised D012/D016 guides on three exploration-only four-option cases.

The script sends no option-answer keys and writes no case text or raw API data.
It requires the frozen row-split assignment and compares against the original
v1 exploration responses for the same row indices.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from typesafe_sdk import TypeSafeClient

try:
    from .compare_type3_prompts_v0_v1 import build_v1_questions
    from .pilot_23way import (MODEL, ROW_SPLIT, SOURCE, parse_answer_labels,
        parse_diagnosis_inventory, parse_markdown_guides, parse_noul_answer,
        parse_option_labels)
    from .smoke_test import PRICE_PER_INPUT_TOKEN_USD, load_local_key
except ImportError:
    from compare_type3_prompts_v0_v1 import build_v1_questions
    from pilot_23way import (MODEL, ROW_SPLIT, SOURCE, parse_answer_labels,
        parse_diagnosis_inventory, parse_markdown_guides, parse_noul_answer,
        parse_option_labels)
    from smoke_test import PRICE_PER_INPUT_TOKEN_USD, load_local_key


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "results/exploration_v1_full/responses.jsonl"
OUTPUT = ROOT / "results/phobia_ocd_guide_v1_1_exploration_check.json"
PAIR_CODES = {"D012", "D016"}
THRESHOLDS = (0.40, 0.50)


def select_rows(names: dict[str, str]) -> list[dict]:
    assignments = {
        int(r["row_index"]): r
        for r in csv.DictReader(ROW_SPLIT.open(encoding="utf-8", newline=""))
    }
    name_to_code = {name: code for code, name in names.items()}
    buckets: dict[str, list[dict]] = {"type3": [], "type4_D012": [], "type4_D016": []}
    with SOURCE.open(encoding="utf-8-sig", newline="") as stream:
        for row_index, row in enumerate(csv.DictReader(stream)):
            assignment = assignments.get(row_index)
            # Check the frozen partition before accessing narrative text.
            if assignment is None or assignment["split"] != "exploration":
                continue
            if row["type"] not in {"type3", "type4"} or row["code"] != "D012_D016":
                continue
            options = parse_option_labels(row["option"])
            option_codes = [name_to_code.get(name) for name in options]
            if len(option_codes) != 4 or not PAIR_CODES <= set(option_codes):
                continue
            keys = parse_answer_labels(row["answer"], row["option"])
            key_codes = [name_to_code.get(name) for name in keys]
            if row["type"] == "type3" and set(key_codes) == PAIR_CODES:
                buckets["type3"].append({**row, "_row_index": row_index,
                                          "_group_id": assignment["group_id"],
                                          "_option_codes": option_codes,
                                          "_key_codes": key_codes})
            elif row["type"] == "type4" and len(key_codes) == 1 and key_codes[0] in PAIR_CODES:
                buckets[f"type4_{key_codes[0]}"] .append({
                    **row, "_row_index": row_index,
                    "_group_id": assignment["group_id"],
                    "_option_codes": option_codes, "_key_codes": key_codes,
                })
    selected = []
    for bucket, values in buckets.items():
        if not values:
            raise RuntimeError(f"No exploration candidates for {bucket}")
        # Stable hash selection avoids picking a row based on its observed score.
        selected.append(min(values, key=lambda row: hashlib.sha256(
            f"jev-d012-d016-guide-v1.1|{bucket}|{row['_row_index']}".encode()
        ).hexdigest()))
    return selected


def main() -> int:
    load_local_key()
    if not os.environ.get("TYPESAFE_API_KEY"):
        print("TYPESAFE_API_KEY is not configured; no request was sent.", file=sys.stderr)
        return 2
    if OUTPUT.exists():
        print("Result exists; refusing duplicate requests.", file=sys.stderr)
        return 2
    if not BASELINE.exists():
        print("Baseline response journal missing; no request was sent.", file=sys.stderr)
        return 2

    names = parse_diagnosis_inventory()
    guides, _ = parse_markdown_guides()
    selected = select_rows(names)
    baseline = {}
    with BASELINE.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("status") == "ok" and record.get("arm") == "four":
                baseline[record["row_index"]] = record
    if any(row["_row_index"] not in baseline for row in selected):
        raise RuntimeError("A selected exploration row lacks a successful four-option baseline")

    output_cases = []
    with TypeSafeClient() as client:
        for row in selected:
            codes = row["_option_codes"]
            candidates = [{"code": code, "name": names[code]} for code in codes]
            state = {
                "case_text": row["question"],
                "candidate_diagnoses": candidates,
                "diagnostic_guides": {code: guides[code] for code in codes},
                "shared_references": {},
            }
            questions = build_v1_questions({code: names[code] for code in codes})
            started = time.perf_counter()
            response = client.system_one(model=MODEL, state=state, questions=questions)
            elapsed = time.perf_counter() - started
            if set(response.answers) != set(codes):
                raise RuntimeError("Jev answer codes did not match the four supplied diagnoses")
            probabilities = {code: parse_noul_answer(response.answers[code]) for code in codes}
            keys = row["_key_codes"]
            old = baseline[row["_row_index"]]
            old_probs = old["probabilities"]
            old_set = [code for code in codes if old_probs[code] >= 0.50]
            new_set = [code for code in codes if probabilities[code] >= 0.50]
            output_cases.append({
                "row_index": row["_row_index"],
                "source_group_id": row["_group_id"],
                "case_type": row["type"],
                "key_codes_local_only": keys,
                "option_codes": codes,
                "baseline_v1_probabilities": old_probs,
                "v1_1_probabilities": probabilities,
                "baseline_top1": old["top1_code"],
                "v1_1_top1": max(probabilities, key=lambda code: (probabilities[code], code)),
                "threshold_sets": {
                    f"{threshold:.2f}": {
                        "baseline": [code for code in codes if old_probs[code] >= threshold],
                        "v1_1": [code for code in codes if probabilities[code] >= threshold],
                    } for threshold in THRESHOLDS
                },
                "exact_set_at_0_50": {
                    "baseline": set(old_set) == set(keys),
                    "v1_1": set(new_set) == set(keys),
                },
                "model": response.model,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "estimated_cost_usd": round(response.usage.input_tokens * PRICE_PER_INPUT_TOKEN_USD, 10),
                "elapsed_seconds": round(elapsed, 4),
            })

    result = {
        "version": "phobia_ocd_guide_v1_1_exploration_check",
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": MODEL,
        "selection": "One hash-selected Type 3 and one Type 4 case keyed D012 and D016, all from exploration; Type 4 cases share the single available D012/D016 source group.",
        "contains_case_text": False,
        "contains_raw_api_payload": False,
        "cases": output_cases,
        "usage": {
            "requests": len(output_cases),
            "input_tokens": sum(case["input_tokens"] for case in output_cases),
            "output_tokens": sum(case["output_tokens"] for case in output_cases),
            "estimated_cost_usd": round(sum(case["estimated_cost_usd"] for case in output_cases), 10),
            "elapsed_seconds_sum": round(sum(case["elapsed_seconds"] for case in output_cases), 4),
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "model": MODEL,
        "cases": [{key: case[key] for key in ("row_index", "case_type", "key_codes_local_only", "baseline_v1_probabilities", "v1_1_probabilities", "exact_set_at_0_50", "input_tokens", "estimated_cost_usd", "elapsed_seconds")} for case in output_cases],
        "usage": result["usage"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
