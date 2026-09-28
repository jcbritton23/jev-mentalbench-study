"""Preflight the frozen MentalBench holdout; send it only with --run.

Default execution checks hashes, split integrity, prompt shape, and the
existing journal without reading held-out case descriptions or calling Jev.
The --run path sends one all-23 and one four-option request per holdout case.
Only identifiers, label codes, probabilities, usage, and timing are journaled.
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
    from .pilot_23way import (
        MODEL, ROOT, ROW_SPLIT, SOURCE, parse_answer_labels,
        parse_diagnosis_inventory, parse_markdown_guides, parse_noul_answer,
        parse_option_labels,
    )
    from .smoke_test import PRICE_PER_INPUT_TOKEN_USD, load_local_key
except ImportError:
    from compare_type3_prompts_v0_v1 import build_v1_questions
    from pilot_23way import (
        MODEL, ROOT, ROW_SPLIT, SOURCE, parse_answer_labels,
        parse_diagnosis_inventory, parse_markdown_guides, parse_noul_answer,
        parse_option_labels,
    )
    from smoke_test import PRICE_PER_INPUT_TOKEN_USD, load_local_key


FREEZE = ROOT / "prompts/mentalbench_holdout_freeze_v1_1.json"
GROUP_SPLIT = ROOT / "data/processed/mentalbench_group_split_v1.csv"
RUN_DIR = ROOT / "results/holdout_v1_1_full"
MANIFEST = RUN_DIR / "manifest.json"
JOURNAL = RUN_DIR / "responses.jsonl"
SESSIONS = RUN_DIR / "sessions.jsonl"
SUMMARY = RUN_DIR / "summary.json"
EXPECTED_RUN_ID = "mentalbench_holdout_v1_1_both_arms"
ARMS = ("all23", "four")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_freeze() -> dict:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if (freeze.get("run_id") != EXPECTED_RUN_ID
            or freeze.get("status") != "frozen_before_holdout"
            or freeze.get("model") != MODEL
            or freeze.get("arms") != list(ARMS)
            or freeze.get("primary_differential_cutoff") != 0.50
            or freeze.get("secondary_type3_cutoff") != 0.40
            or freeze.get("expected_cases") != 22785
            or freeze.get("expected_requests") != 45570
            or freeze.get("expected_groups") != 673
            or freeze.get("holdout_cost_cap_usd") != 17.50
            or not math.isclose(freeze.get("input_price_usd_per_token", 0),
                                PRICE_PER_INPUT_TOKEN_USD, rel_tol=1e-12)
            or freeze.get("max_input_tokens_per_attempt") != 64000
            or freeze.get("max_attempts_per_request") != 3
            or freeze.get("workers") != 3):
        raise RuntimeError("Holdout freeze configuration differs from the reviewed v1.1 protocol")
    for relative_path, expected_sha in {
        **freeze["implementation_sha256"], **freeze["prompt_sha256"]
    }.items():
        if file_sha256(ROOT / relative_path) != expected_sha:
            raise RuntimeError(f"Frozen input changed: {relative_path}")
    for path, key in ((SOURCE, "source_sha256"), (ROW_SPLIT, "row_split_sha256"),
                      (GROUP_SPLIT, "group_split_sha256")):
        if file_sha256(path) != freeze[key]:
            raise RuntimeError(f"Frozen data or split hash changed: {path.name}")
    if len(parse_diagnosis_inventory()) != 23:
        raise RuntimeError("The frozen diagnosis inventory does not have 23 labels")
    if len(parse_markdown_guides()[0]) != 23:
        raise RuntimeError("The frozen guides do not have 23 labels")
    return freeze


def read_holdout_assignment(freeze: dict) -> dict[int, str]:
    all_rows: dict[int, tuple[str, str]] = {}
    with ROW_SPLIT.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            index = int(row["row_index"])
            if index in all_rows or row["split"] not in {"exploration", "holdout"}:
                raise RuntimeError("Frozen row manifest has a duplicate or invalid split")
            all_rows[index] = (row["group_id"], row["split"])
    if len(all_rows) != 24750 or set(all_rows) != set(range(24750)):
        raise RuntimeError("Frozen row manifest does not cover exactly the source row indices")

    groups = {}
    with GROUP_SPLIT.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            group_id = row["group_id"]
            if group_id in groups or row["split"] not in {"exploration", "holdout"}:
                raise RuntimeError("Frozen group manifest has a duplicate or invalid split")
            if row["preview_exposed"] == "1" and row["split"] != "exploration":
                raise RuntimeError("A preview-exposed group entered the holdout")
            groups[group_id] = row
    if len(groups) != 780:
        raise RuntimeError("Frozen group manifest does not have 780 groups")
    group_counts = Counter(group_id for group_id, _ in all_rows.values())
    for group_id, row in groups.items():
        if group_counts[group_id] != int(row["row_count"]):
            raise RuntimeError("Row and group manifests disagree on group size")
    for group_id, split in all_rows.values():
        if group_id not in groups or groups[group_id]["split"] != split:
            raise RuntimeError("A source family crosses the exploration/holdout boundary")

    holdout = {index: group_id for index, (group_id, split) in all_rows.items()
               if split == "holdout"}
    holdout_groups = {group_id for group_id in holdout.values()}
    if len(holdout) != freeze["expected_cases"] or len(holdout_groups) != freeze["expected_groups"]:
        raise RuntimeError("Holdout row or group count differs from the freeze")
    type_counts = Counter()
    for group_id in holdout_groups:
        row = groups[group_id]
        size = int(row["row_count"])
        if row["case_types"] in {"type1", "type2"} and size == 15:
            type_counts[row["case_types"]] += size
        elif row["case_types"] == "type3+type4" and size == 45:
            type_counts["type3"] += 15
            type_counts["type4"] += 30
        else:
            raise RuntimeError("Unexpected holdout family type or size")
    if dict(type_counts) != freeze["expected_type_counts"]:
        raise RuntimeError("Holdout type counts differ from the freeze")
    return holdout


def build_request(case: dict, arm: str, names: dict[str, str], guides: dict[str, str],
                  shared_adhd: str, all_candidates: list[dict], all_questions: dict,
                  four_question_cache: dict[tuple[str, ...], dict]) -> tuple[dict, dict]:
    if arm == "all23":
        candidates = all_candidates
        relevant_guides = guides
        questions = all_questions
        references = {"ADHD_symptom_domains": shared_adhd}
    elif arm == "four":
        codes = case["option_codes"]
        candidates = [{"code": code, "name": names[code]} for code in codes]
        relevant_guides = {code: guides[code] for code in codes}
        questions = four_question_cache[tuple(codes)]
        references = ({"ADHD_symptom_domains": shared_adhd}
                      if any(code in {"D001", "D002", "D003"} for code in codes)
                      else {})
    else:
        raise RuntimeError("Unknown benchmark arm")
    state = {
        "case_text": case["case_text"],
        "candidate_diagnoses": candidates,
        "diagnostic_guides": relevant_guides,
        "shared_references": references,
    }
    return state, questions


def check_request_shape(names: dict[str, str], guides: dict[str, str], shared_adhd: str) -> None:
    all_candidates = [{"code": code, "name": names[code]} for code in sorted(names)]
    all_questions = build_v1_questions(names)
    codes = ("D001", "D002", "D003", "D004")
    four_cache = {codes: build_v1_questions({code: names[code] for code in codes})}
    synthetic = {"case_text": "Fictional preflight text", "option_codes": list(codes),
                 "key_codes": ["D001"]}
    for arm in ARMS:
        state, questions = build_request(synthetic, arm, names, guides, shared_adhd,
                                         all_candidates, all_questions, four_cache)
        expected_codes = set(names) if arm == "all23" else set(codes)
        if (set(state) != {"case_text", "candidate_diagnoses", "diagnostic_guides", "shared_references"}
                or state["case_text"] != synthetic["case_text"]
                or {item["code"] for item in state["candidate_diagnoses"]} != expected_codes
                or set(state["diagnostic_guides"]) != expected_codes
                or set(questions) != expected_codes):
            raise RuntimeError("Synthetic request-shape check failed")
        if "key_codes" in state or "option_codes" in state:
            raise RuntimeError("Benchmark answer or option metadata leaked into API state")


def read_journal(holdout_indices: set[int], freeze: dict) -> tuple[set[tuple[int, str]], float, float]:
    completed: set[tuple[int, str]] = set()
    successful_cost = 0.0
    failed_cost_upper = 0.0
    if not JOURNAL.exists():
        return completed, successful_cost, failed_cost_upper
    max_job_cost = (freeze["max_input_tokens_per_attempt"]
                    * freeze["input_price_usd_per_token"]
                    * freeze["max_attempts_per_request"])
    with JOURNAL.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            row_index, arm = record["row_index"], record["arm"]
            if row_index not in holdout_indices or arm not in ARMS:
                raise RuntimeError("Journal contains a non-holdout row or unknown arm")
            key = (row_index, arm)
            if record["status"] == "ok":
                if key in completed or record["model"] != freeze["model"]:
                    raise RuntimeError("Journal has a duplicate success or unexpected model")
                if record["prompt_version"] != freeze["prompt_version"]:
                    raise RuntimeError("Journal has an unexpected prompt version")
                completed.add(key)
                successful_cost += record["estimated_cost_usd"]
                retry_upper = record["failed_attempt_cost_upper_usd"]
                if (retry_upper < 0 or record["estimated_cost_usd"] + retry_upper
                        > max_job_cost + 1e-9):
                    raise RuntimeError("Journal has an invalid successful-request cost bound")
                failed_cost_upper += retry_upper
            elif record["status"] == "error":
                upper = record["max_possible_cost_usd"]
                if upper < 0 or upper > max_job_cost + 1e-9:
                    raise RuntimeError("Journal has an invalid failed-request cost bound")
                failed_cost_upper += upper
            else:
                raise RuntimeError("Journal has an unknown status")
    if successful_cost + failed_cost_upper > freeze["holdout_cost_cap_usd"] + 1e-9:
        raise RuntimeError("Journal exceeds the frozen holdout cost cap")
    return completed, successful_cost, failed_cost_upper


def load_holdout_cases(holdout: dict[int, str], names: dict[str, str], freeze: dict) -> list[dict]:
    name_to_code = {name: code for code, name in names.items()}
    if len(name_to_code) != 23:
        raise RuntimeError("Diagnosis names are not unique")
    cases = []
    type_counts = Counter()
    with SOURCE.open(encoding="utf-8-sig", newline="") as stream:
        for row_index, row in enumerate(csv.DictReader(stream)):
            group_id = holdout.get(row_index)
            if group_id is None:
                continue
            if not group_id.startswith(row["code"] + ":"):
                raise RuntimeError("Holdout row code conflicts with frozen family")
            option_names = parse_option_labels(row["option"])
            key_names = parse_answer_labels(row["answer"], row["option"])
            if (len(option_names) != 4 or len(set(option_names)) != 4
                    or len(key_names) != (2 if row["type"] == "type3" else 1)
                    or not set(key_names) <= set(option_names)
                    or any(name not in name_to_code for name in option_names)
                    or not row["question"].strip()):
                raise RuntimeError("A selected holdout row has invalid case metadata")
            cases.append({
                "row_index": row_index, "group_id": group_id,
                "case_type": row["type"], "generator": row["model"],
                "case_text": row["question"],
                "option_codes": [name_to_code[name] for name in option_names],
                "key_codes": [name_to_code[name] for name in key_names],
            })
            type_counts[row["type"]] += 1
    if len(cases) != freeze["expected_cases"] or dict(type_counts) != freeze["expected_type_counts"]:
        raise RuntimeError("Selected holdout cases do not match the frozen split")
    return cases


def is_retryable(exc: Exception) -> bool:
    if isinstance(exc, TypeSafeAPIError):
        return exc.status in {408, 429, 529} or 500 <= exc.status < 600
    return isinstance(exc, (TypeSafeAPIConnectionError, TypeSafeAPITimeoutError))


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


def run_one(case: dict, arm: str, names: dict[str, str], guides: dict[str, str],
            shared_adhd: str, all_candidates: list[dict], all_questions: dict,
            four_question_cache: dict[tuple[str, ...], dict], freeze: dict) -> dict:
    state, questions = build_request(case, arm, names, guides, shared_adhd,
                                     all_candidates, all_questions, four_question_cache)
    base = {
        "row_index": case["row_index"], "group_id": case["group_id"],
        "case_type": case["case_type"], "generator": case["generator"],
        "arm": arm, "option_codes": case["option_codes"],
        "key_codes": case["key_codes"], "prompt_version": freeze["prompt_version"],
        "requested_model": MODEL,
    }
    started_at = utc_now()
    started = time.perf_counter()
    attempts = []
    max_job_cost = (freeze["max_input_tokens_per_attempt"]
                    * freeze["input_price_usd_per_token"]
                    * freeze["max_attempts_per_request"])
    for attempt_number in range(1, freeze["max_attempts_per_request"] + 1):
        attempt_started = time.perf_counter()
        try:
            with TypeSafeClient(retry=RetryPolicy(max_retries=0)) as client:
                response = client.system_one(model=MODEL, state=state, questions=questions)
            if response.model != MODEL:
                raise RuntimeError("Jev response used an unexpected model version")
            expected_codes = set(names) if arm == "all23" else set(case["option_codes"])
            if set(response.answers) != expected_codes:
                raise RuntimeError("Jev response codes differ from the request")
            probabilities = {code: parse_noul_answer(response.answers[code])
                             for code in sorted(expected_codes)}
            if any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities.values()):
                raise RuntimeError("Jev returned an invalid Noul probability")
            input_tokens = int(response.usage.input_tokens)
            if not 0 <= input_tokens <= freeze["max_input_tokens_per_attempt"]:
                raise RuntimeError("Jev usage exceeded the reserved request size")
            attempts.append({"attempt": attempt_number, "status": "ok",
                             "elapsed_seconds": round(time.perf_counter() - attempt_started, 4)})
            ranked = sorted(probabilities, key=lambda code: (-probabilities[code], code))
            return {**base, "status": "ok", "started_at_utc": started_at,
                    "ended_at_utc": utc_now(),
                    "elapsed_seconds_total": round(time.perf_counter() - started, 4),
                    "attempts": attempts, "retry_count": attempt_number - 1,
                    "model": response.model, "input_tokens": input_tokens,
                    "output_tokens": int(response.usage.output_tokens),
                    "estimated_cost_usd": round(input_tokens * PRICE_PER_INPUT_TOKEN_USD, 10),
                    "failed_attempt_cost_upper_usd": round(
                        (attempt_number - 1) * freeze["max_input_tokens_per_attempt"]
                        * PRICE_PER_INPUT_TOKEN_USD, 10),
                    "probabilities": probabilities, "top1_code": ranked[0],
                    "top1_probability": probabilities[ranked[0]]}
        except Exception as exc:
            record = {"attempt": attempt_number, "status": "error",
                      "elapsed_seconds": round(time.perf_counter() - attempt_started, 4),
                      "error_type": type(exc).__name__}
            if isinstance(exc, TypeSafeAPIError):
                record["http_status"] = exc.status
            attempts.append(record)
            if is_retryable(exc) and attempt_number < freeze["max_attempts_per_request"]:
                time.sleep(backoff_seconds(exc, attempt_number))
                continue
            return {**base, "status": "error", "started_at_utc": started_at,
                    "ended_at_utc": utc_now(),
                    "elapsed_seconds_total": round(time.perf_counter() - started, 4),
                    "attempts": attempts, "error_type": type(exc).__name__,
                    "max_possible_cost_usd": round(max_job_cost, 10)}
    raise AssertionError("Unreachable retry state")


def write_summary(freeze: dict, stop_reason: str | None) -> dict:
    counts = Counter()
    latencies = {arm: [] for arm in ARMS}
    input_tokens = output_tokens = retries = 0
    successful_cost = failed_cost_upper = 0.0
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
                retries += record["retry_count"]
                successful_cost += record["estimated_cost_usd"]
                failed_cost_upper += record["failed_attempt_cost_upper_usd"]
                latencies[record["arm"]].append(record["elapsed_seconds_total"])
            else:
                failed_cost_upper += record["max_possible_cost_usd"]
    recorded_wall = 0.0
    if SESSIONS.exists():
        with SESSIONS.open(encoding="utf-8") as stream:
            recorded_wall = sum(json.loads(line)["wall_seconds"] for line in stream if line.strip())
    summary = {
        "run_id": freeze["run_id"], "model": MODEL,
        "updated_at_utc": utc_now(), "expected_requests": freeze["expected_requests"],
        "successful_requests": counts["ok"], "recorded_failure_events": counts["error"],
        "successful_by_arm": {arm: counts[arm] for arm in ARMS},
        "input_tokens": input_tokens, "output_tokens": output_tokens,
        "estimated_success_cost_usd": round(successful_cost, 10),
        "failed_request_cost_upper_usd": round(failed_cost_upper, 10),
        "conservative_cost_upper_usd": round(successful_cost + failed_cost_upper, 10),
        "cost_cap_usd": freeze["holdout_cost_cap_usd"],
        "retry_count_total": retries,
        "recorded_session_wall_seconds": round(recorded_wall, 3),
        "latency_seconds_by_arm": {
            arm: {
                "count": len(values),
                "mean": round(sum(values) / len(values), 4) if values else None,
                "median": round(sorted(values)[len(values) // 2], 4) if values else None,
                "p90": round(sorted(values)[math.ceil(len(values) * .9) - 1], 4) if values else None,
            } for arm, values in latencies.items()
        },
        "stop_reason": stop_reason,
        "contains_case_text": False,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def run_holdout(cases: list[dict], completed: set[tuple[int, str]],
                prior_cost_upper: float, names: dict[str, str], guides: dict[str, str],
                shared_adhd: str, freeze: dict) -> int:
    pending = [(case, arm) for case in cases for arm in ARMS
               if (case["row_index"], arm) not in completed]
    if not pending:
        print(json.dumps({"already_complete": True, "requests": freeze["expected_requests"]}))
        return 0
    if prior_cost_upper >= freeze["holdout_cost_cap_usd"]:
        print("Holdout cost cap reached; no request was sent.", file=sys.stderr)
        return 2
    all_candidates = [{"code": code, "name": names[code]} for code in sorted(names)]
    all_questions = build_v1_questions(names)
    option_sets = {tuple(case["option_codes"]) for case in cases}
    four_question_cache = {
        codes: build_v1_questions({code: names[code] for code in codes})
        for codes in option_sets
    }
    max_job_cost = (freeze["max_input_tokens_per_attempt"]
                    * freeze["input_price_usd_per_token"]
                    * freeze["max_attempts_per_request"])
    committed = prior_cost_upper
    reserved = 0.0
    pending_cursor = 0
    completed_this_session = 0
    stop_reason = None
    session_started_at = utc_now()
    session_started = time.perf_counter()
    last_timing_checkpoint_at = session_started_at
    last_timing_checkpoint = session_started

    def record_timing_checkpoint() -> None:
        nonlocal last_timing_checkpoint_at, last_timing_checkpoint
        now = time.perf_counter()
        now_utc = utc_now()
        segment = {
            "started_at_utc": last_timing_checkpoint_at,
            "ended_at_utc": now_utc,
            "wall_seconds": round(now - last_timing_checkpoint, 3),
            "session_started_at_utc": session_started_at,
            "session_successful_requests_so_far": completed_this_session,
        }
        with SESSIONS.open("a", encoding="utf-8") as sessions:
            sessions.write(json.dumps(segment, sort_keys=True) + "\n")
            sessions.flush()
            os.fsync(sessions.fileno())
        last_timing_checkpoint_at = now_utc
        last_timing_checkpoint = now

    with JOURNAL.open("a", encoding="utf-8") as journal, \
            ThreadPoolExecutor(max_workers=freeze["workers"]) as pool:
        inflight = {}

        def submit_next() -> bool:
            nonlocal reserved, stop_reason, pending_cursor
            if stop_reason is not None:
                return False
            if pending_cursor >= len(pending):
                return False
            if committed + reserved + max_job_cost > freeze["holdout_cost_cap_usd"] + 1e-12:
                return False
            case, arm = pending[pending_cursor]
            pending_cursor += 1
            future = pool.submit(run_one, case, arm, names, guides, shared_adhd,
                                 all_candidates, all_questions, four_question_cache, freeze)
            inflight[future] = (case["row_index"], arm)
            reserved += max_job_cost
            return True

        for _ in range(freeze["workers"]):
            submit_next()
        try:
            while inflight:
                done, _ = wait(inflight, return_when=FIRST_COMPLETED)
                for future in done:
                    row_index, arm = inflight.pop(future)
                    reserved -= max_job_cost
                    try:
                        record = future.result()
                    except Exception as exc:
                        record = {"row_index": row_index, "arm": arm, "status": "error",
                                  "error_type": type(exc).__name__, "ended_at_utc": utc_now(),
                                  "attempts": [], "max_possible_cost_usd": round(max_job_cost, 10)}
                    journal.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
                    journal.flush()
                    os.fsync(journal.fileno())
                    if record["status"] == "ok":
                        committed += (record["estimated_cost_usd"]
                                      + record["failed_attempt_cost_upper_usd"])
                        completed_this_session += 1
                    else:
                        committed += record["max_possible_cost_usd"]
                        stop_reason = "request_error"
                    if completed_this_session and completed_this_session % 500 == 0:
                        record_timing_checkpoint()
                        print(json.dumps({
                            "completed_this_session": completed_this_session,
                            "expected_requests": freeze["expected_requests"],
                            "conservative_cost_upper_usd": round(committed + reserved, 6),
                            "elapsed_seconds": round(time.perf_counter() - session_started, 1),
                        }), flush=True)
                while len(inflight) < freeze["workers"] and submit_next():
                    pass
            if pending_cursor < len(pending) and stop_reason is None:
                stop_reason = "cost_cap"
        finally:
            record_timing_checkpoint()

    summary = write_summary(freeze, stop_reason)
    print(json.dumps(summary, sort_keys=True), flush=True)
    if stop_reason:
        print(json.dumps({"stopped": stop_reason, "can_resume": True}), file=sys.stderr)
        return 1
    if summary["successful_requests"] != freeze["expected_requests"]:
        print("Run is incomplete; the journal can be resumed.", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true",
                        help="Send the complete holdout to Jev; default is metadata-only preflight")
    args = parser.parse_args()

    freeze = read_freeze()
    holdout = read_holdout_assignment(freeze)
    names = parse_diagnosis_inventory()
    guides, shared_adhd = parse_markdown_guides()
    check_request_shape(names, guides, shared_adhd)
    if MANIFEST.exists():
        existing = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if existing != freeze:
            raise RuntimeError("Existing run manifest differs from the frozen protocol")
    elif JOURNAL.exists():
        raise RuntimeError("Response journal exists without a run manifest")
    completed, success_cost, failed_upper = read_journal(set(holdout), freeze)
    print(json.dumps({
        "preflight": True,
        "holdout_cases": len(holdout), "source_groups": freeze["expected_groups"],
        "type_counts": freeze["expected_type_counts"],
        "expected_requests": freeze["expected_requests"],
        "completed_requests": len(completed),
        "pending_requests": freeze["expected_requests"] - len(completed),
        "model": MODEL, "primary_cutoff": freeze["primary_differential_cutoff"],
        "secondary_type3_cutoff": freeze["secondary_type3_cutoff"],
        "development_cost_projection_usd": freeze["development_projection_usd"],
        "holdout_cost_cap_usd": freeze["holdout_cost_cap_usd"],
        "conservative_prior_holdout_cost_usd": round(success_cost + failed_upper, 10),
        "holdout_text_loaded": False,
        "api_request_sent": False,
    }, sort_keys=True), flush=True)
    if not args.run:
        return 0
    load_local_key()
    if not os.environ.get("TYPESAFE_API_KEY"):
        print("TYPESAFE_API_KEY is not configured; no request was sent.", file=sys.stderr)
        return 2
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    if not MANIFEST.exists():
        MANIFEST.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    cases = load_holdout_cases(holdout, names, freeze)
    return run_holdout(cases, completed, success_cost + failed_upper,
                       names, guides, shared_adhd, freeze)


if __name__ == "__main__":
    raise SystemExit(main())
