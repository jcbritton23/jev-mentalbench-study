"""Run both Jev v1 arms on the frozen MentalBench exploration partition.

The protected holdout is never sent to TypeSafe. The ignored result journal
contains identifiers, gold/option codes, probabilities, usage, and timing, but
no case text, option text, answer text, or raw API payloads. Re-running resumes
from successful case/arm records and refuses changed input or prompt hashes.
"""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

from typesafe_sdk import (
    TypeSafeAPIConnectionError,
    TypeSafeAPIError,
    TypeSafeAPITimeoutError,
    TypeSafeClient,
)
from typesafe_sdk._core.retry import RetryPolicy

try:
    from .compare_type3_prompts_v0_v1 import build_v1_questions
    from .pilot_23way import (MODEL, ROOT, ROW_SPLIT, SOURCE,
        parse_answer_labels, parse_diagnosis_inventory, parse_markdown_guides,
        parse_noul_answer, parse_option_labels)
    from .smoke_test import PRICE_PER_INPUT_TOKEN_USD, load_local_key
except ImportError:
    from compare_type3_prompts_v0_v1 import build_v1_questions
    from pilot_23way import (MODEL, ROOT, ROW_SPLIT, SOURCE,
        parse_answer_labels, parse_diagnosis_inventory, parse_markdown_guides,
        parse_noul_answer, parse_option_labels)
    from smoke_test import PRICE_PER_INPUT_TOKEN_USD, load_local_key


RUN_DIR = ROOT / "results/exploration_v1_full"
MANIFEST = RUN_DIR / "manifest.json"
JOURNAL = RUN_DIR / "responses.jsonl"
SUMMARY = RUN_DIR / "summary.json"
EXPECTED_SOURCE_SHA256 = "92b8d1c835a1aad22161e2b4bc1444823ed22d91275df99463b3b5e488bec957"
EXPECTED_CASES = 1965
EXPECTED_GROUPS = 107
ARMS = ("all23", "four")
THRESHOLDS = (0.50, 0.70, 0.80, 0.90)
MAX_RUN_COST_USD = 2.50
WORKERS = 3
MAX_ATTEMPTS = 3


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_cases(names: dict[str, str]) -> tuple[list[dict], dict[str, int]]:
    with ROW_SPLIT.open(encoding="utf-8", newline="") as stream:
        assignments = {int(row["row_index"]): row for row in csv.DictReader(stream)}
    name_to_code = {name: code for code, name in names.items()}
    if len(name_to_code) != 23:
        raise RuntimeError("Diagnosis names are not unique")

    selected: list[dict] = []
    total_rows = 0
    with SOURCE.open(encoding="utf-8-sig", newline="") as stream:
        for row_index, row in enumerate(csv.DictReader(stream)):
            total_rows += 1
            assignment = assignments.get(row_index)
            if assignment is None:
                raise RuntimeError("A source row has no frozen split assignment")
            if assignment["split"] != "exploration":
                continue
            option_names = parse_option_labels(row["option"])
            key_names = parse_answer_labels(row["answer"], row["option"])
            if (len(option_names) != 4 or len(set(option_names)) != 4
                    or len(key_names) != (2 if row["type"] == "type3" else 1)
                    or not set(key_names) <= set(option_names)
                    or any(name not in name_to_code for name in option_names)):
                raise RuntimeError("An exploration row has invalid option/key metadata")
            selected.append({
                "row_index": row_index,
                "group_id": assignment["group_id"],
                "case_type": row["type"],
                "generator": row["model"],
                "case_text": row["question"],
                "option_codes": [name_to_code[name] for name in option_names],
                "key_codes": [name_to_code[name] for name in key_names],
            })
    if total_rows != len(assignments) or total_rows != 24750:
        raise RuntimeError("Source rows do not match the frozen split manifest")
    if len(selected) != EXPECTED_CASES or len({r["group_id"] for r in selected}) != EXPECTED_GROUPS:
        raise RuntimeError("Exploration partition size or group count changed")
    if len({r["row_index"] for r in selected}) != EXPECTED_CASES:
        raise RuntimeError("Duplicate exploration row index")
    return selected, dict(Counter(r["case_type"] for r in selected))


def expected_manifest(type_counts: dict[str, int]) -> dict:
    guide_paths = (
        ROOT / "prompts/basic_diagnosis_guides_v0.md",
        ROOT / "prompts/complex_diagnosis_guides_v0.md",
        ROOT / "prompts/d013_mdd_sample_v0.md",
    )
    return {
        "run_id": "mentalbench_exploration_v1_both_arms",
        "model": MODEL,
        "prompt_version": "v1_candidate",
        "question_builder_sha256": file_sha256(ROOT / "scripts/compare_type3_prompts_v0_v1.py"),
        "prompt_description_sha256": file_sha256(ROOT / "prompts/mentalbench_v1_question_candidate.md"),
        "guide_sha256": {p.name: file_sha256(p) for p in guide_paths},
        "source_sha256": file_sha256(SOURCE),
        "row_split_sha256": file_sha256(ROW_SPLIT),
        "expected_cases": EXPECTED_CASES,
        "expected_requests": EXPECTED_CASES * len(ARMS),
        "expected_groups": EXPECTED_GROUPS,
        "type_counts": type_counts,
        "arms": list(ARMS),
        "price_per_input_token_usd": PRICE_PER_INPUT_TOKEN_USD,
        "max_run_cost_usd": MAX_RUN_COST_USD,
        "contains_case_text": False,
    }


def ensure_manifest(expected: dict) -> None:
    if expected["source_sha256"] != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("Source CSV hash differs from audited MentalBench revision")
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    if MANIFEST.exists():
        existing = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if existing != expected:
            raise RuntimeError("Run manifest differs; refusing to mix versions")
    else:
        if JOURNAL.exists():
            raise RuntimeError("Response journal exists without a manifest")
        MANIFEST.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_journal() -> tuple[set[tuple[int, str]], float, int, int]:
    completed: set[tuple[int, str]] = set()
    cost = 0.0
    input_tokens = 0
    output_tokens = 0
    if not JOURNAL.exists():
        return completed, cost, input_tokens, output_tokens
    with JOURNAL.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            if record["status"] != "ok":
                continue
            key = (record["row_index"], record["arm"])
            if key in completed:
                raise RuntimeError("Duplicate successful case/arm result in journal")
            completed.add(key)
            cost += record["estimated_cost_usd"]
            input_tokens += record["input_tokens"]
            output_tokens += record["output_tokens"]
    return completed, cost, input_tokens, output_tokens


def backoff_seconds(exc: Exception, retry_number: int) -> float:
    headers = getattr(exc, "headers", None)
    if headers is not None:
        try:
            retry_after = float(headers.get("retry-after", ""))
            if math.isfinite(retry_after) and retry_after >= 0:
                return min(retry_after, 30.0)
        except (ValueError, TypeError):
            pass
    return min(2.0 ** retry_number, 8.0)


def is_retryable(exc: Exception) -> bool:
    if isinstance(exc, TypeSafeAPIError):
        return exc.status in {408, 429, 529} or 500 <= exc.status < 600
    return isinstance(exc, (TypeSafeAPIConnectionError, TypeSafeAPITimeoutError))


def run_one(case: dict, arm: str, names: dict[str, str], guides: dict[str, str],
            shared_adhd: str, all_candidates: list[dict], all_questions: dict,
            four_question_cache: dict[tuple[str, ...], dict]) -> dict:
    option_codes = case["option_codes"]
    if arm == "all23":
        candidates = all_candidates
        relevant_guides = guides
        questions = all_questions
        references = {"ADHD_symptom_domains": shared_adhd}
    else:
        candidates = [{"code": code, "name": names[code]} for code in option_codes]
        relevant_guides = {code: guides[code] for code in option_codes}
        questions = four_question_cache[tuple(option_codes)]
        references = ({"ADHD_symptom_domains": shared_adhd}
                      if any(code in {"D001", "D002", "D003"} for code in option_codes)
                      else {})
    state = {
        "case_text": case["case_text"],
        "candidate_diagnoses": candidates,
        "diagnostic_guides": relevant_guides,
        "shared_references": references,
    }
    base = {
        "row_index": case["row_index"], "group_id": case["group_id"],
        "case_type": case["case_type"], "generator": case["generator"],
        "arm": arm, "option_codes": option_codes, "key_codes": case["key_codes"],
        "prompt_version": "v1_candidate", "requested_model": MODEL,
    }
    started_at = utc_now()
    started = time.perf_counter()
    attempts: list[dict] = []
    for attempt_number in range(1, MAX_ATTEMPTS + 1):
        attempt_started = time.perf_counter()
        try:
            with TypeSafeClient(retry=RetryPolicy(max_retries=0)) as client:
                response = client.system_one(model=MODEL, state=state, questions=questions)
            attempts.append({"attempt": attempt_number,
                             "elapsed_seconds": round(time.perf_counter() - attempt_started, 4),
                             "status": "ok"})
            expected_codes = set(names) if arm == "all23" else set(option_codes)
            if set(response.answers) != expected_codes:
                raise RuntimeError("Jev answer codes did not match requested diagnoses")
            probs = {code: parse_noul_answer(response.answers[code]) for code in sorted(expected_codes)}
            if any(not math.isfinite(p) or not 0 <= p <= 1 for p in probs.values()):
                raise RuntimeError("Jev returned an invalid Noul probability")
            ranked = sorted(probs, key=lambda code: (-probs[code], code))
            tokens = response.usage.input_tokens
            return {**base, "status": "ok", "started_at_utc": started_at,
                "ended_at_utc": utc_now(),
                "elapsed_seconds_total": round(time.perf_counter() - started, 4),
                "attempts": attempts, "retry_count": attempt_number - 1,
                "model": response.model, "input_tokens": tokens,
                "output_tokens": response.usage.output_tokens,
                "estimated_cost_usd": round(tokens * PRICE_PER_INPUT_TOKEN_USD, 10),
                "probabilities": probs, "top1_code": ranked[0],
                "top1_probability": probs[ranked[0]],
            }
        except Exception as exc:
            retryable = is_retryable(exc)
            attempt_record = {"attempt": attempt_number,
                              "elapsed_seconds": round(time.perf_counter() - attempt_started, 4),
                              "status": "error", "error_type": type(exc).__name__}
            if isinstance(exc, TypeSafeAPIError):
                attempt_record["http_status"] = exc.status
            attempts.append(attempt_record)
            if retryable and attempt_number < MAX_ATTEMPTS:
                time.sleep(backoff_seconds(exc, attempt_number))
                continue
            return {**base, "status": "error", "started_at_utc": started_at,
                    "ended_at_utc": utc_now(),
                    "elapsed_seconds_total": round(time.perf_counter() - started, 4),
                    "attempts": attempts, "retry_count": attempt_number - 1,
                    "error_type": type(exc).__name__}
    raise AssertionError("Unreachable retry state")


def write_summary(expected: dict, started_at: str, elapsed: float) -> dict:
    counts = Counter()
    cost = 0.0
    input_tokens = 0
    output_tokens = 0
    latency_by_arm: dict[str, list[float]] = {arm: [] for arm in ARMS}
    retries = 0
    with JOURNAL.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            counts[record["status"]] += 1
            if record["status"] == "ok":
                counts[record["arm"]] += 1
                input_tokens += record["input_tokens"]
                output_tokens += record["output_tokens"]
                cost += record["estimated_cost_usd"]
                latency_by_arm[record["arm"]].append(record["elapsed_seconds_total"])
                retries += record["retry_count"]
    summary = {
        "run_id": expected["run_id"], "model": MODEL,
        "started_or_resumed_at_utc": started_at, "updated_at_utc": utc_now(),
        "current_session_wall_seconds": round(elapsed, 3),
        "expected_requests": expected["expected_requests"],
        "successful_requests": counts["ok"], "recorded_failure_events": counts["error"],
        "successful_by_arm": {arm: counts[arm] for arm in ARMS},
        "input_tokens": input_tokens, "output_tokens": output_tokens,
        "estimated_cost_usd": round(cost, 10), "retry_count_total": retries,
        "latency_seconds_by_arm": {
            arm: {"count": len(values),
                  "mean": round(sum(values) / len(values), 4) if values else None,
                  "median": round(sorted(values)[len(values) // 2], 4) if values else None,
                  "p90": round(sorted(values)[math.ceil(len(values) * 0.9) - 1], 4) if values else None}
            for arm, values in latency_by_arm.items()
        },
        "contains_case_text": False,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true", help="Validate the frozen exploration selection without API calls")
    args = parser.parse_args()

    names = parse_diagnosis_inventory()
    guides, shared_adhd = parse_markdown_guides()
    cases, type_counts = load_cases(names)
    expected = expected_manifest(type_counts)
    ensure_manifest(expected)
    completed, spent, _, _ = read_journal()
    pending = [(case, arm) for case in cases for arm in ARMS
               if (case["row_index"], arm) not in completed]
    print(json.dumps({"preflight": True, "exploration_cases": len(cases),
        "source_groups": len({c["group_id"] for c in cases}),
        "type_counts": type_counts, "requests_completed": len(completed),
        "requests_pending": len(pending), "estimated_prior_cost_usd": round(spent, 8),
        "run_cost_cap_usd": MAX_RUN_COST_USD}, sort_keys=True), flush=True)
    if args.preflight or not pending:
        return 0

    load_local_key()
    if not os.environ.get("TYPESAFE_API_KEY"):
        print("TYPESAFE_API_KEY is not configured; no request was sent.", file=sys.stderr)
        return 2
    if spent >= MAX_RUN_COST_USD:
        print("Exploration cost cap already reached; no request was sent.", file=sys.stderr)
        return 2

    all_candidates = [{"code": code, "name": names[code]} for code in sorted(names)]
    all_questions = build_v1_questions(names)
    option_sets = {tuple(case["option_codes"]) for case in cases}
    four_question_cache = {
        codes: build_v1_questions({code: names[code] for code in codes})
        for codes in option_sets
    }
    started_at = utc_now()
    started = time.perf_counter()
    pending_iter = iter(pending)
    completed_this_session = 0
    stop_reason = None
    with JOURNAL.open("a", encoding="utf-8") as journal, ThreadPoolExecutor(max_workers=WORKERS) as pool:
        inflight = {}

        def submit_next() -> bool:
            if spent >= MAX_RUN_COST_USD or stop_reason is not None:
                return False
            try:
                case, arm = next(pending_iter)
            except StopIteration:
                return False
            future = pool.submit(run_one, case, arm, names, guides, shared_adhd,
                                 all_candidates, all_questions, four_question_cache)
            inflight[future] = (case["row_index"], arm)
            return True

        for _ in range(WORKERS):
            submit_next()
        while inflight:
            done, _ = wait(inflight, return_when=FIRST_COMPLETED)
            for future in done:
                row_index, arm = inflight.pop(future)
                try:
                    record = future.result()
                except Exception as exc:
                    record = {"row_index": row_index, "arm": arm, "status": "error",
                              "error_type": type(exc).__name__, "ended_at_utc": utc_now(),
                              "attempts": []}
                journal.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
                journal.flush()
                os.fsync(journal.fileno())
                if record["status"] == "ok":
                    spent += record["estimated_cost_usd"]
                    completed_this_session += 1
                else:
                    stop_reason = "request_error"
                if spent >= MAX_RUN_COST_USD:
                    stop_reason = "cost_cap"
                if completed_this_session and completed_this_session % 100 == 0:
                    print(json.dumps({"completed_this_session": completed_this_session,
                        "requests_total": len(completed) + completed_this_session,
                        "expected_requests": expected["expected_requests"],
                        "estimated_cost_usd": round(spent, 6),
                        "elapsed_seconds": round(time.perf_counter() - started, 1)}), flush=True)
            while len(inflight) < WORKERS and submit_next():
                pass

    summary = write_summary(expected, started_at, time.perf_counter() - started)
    print(json.dumps(summary, sort_keys=True), flush=True)
    if stop_reason:
        print(json.dumps({"stopped": stop_reason, "can_resume": True}), file=sys.stderr)
        return 1
    if summary["successful_requests"] != expected["expected_requests"]:
        print("Run is incomplete; journal can be resumed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
