"""Score the complete frozen MentalBench holdout from the no-text journal.

This refuses partial runs. It reads no source case text and selects no new
thresholds: .50 is primary, .40 is the prespecified Type 3 sensitivity point.
"""

from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import random

try:
    from .pilot_23way import ROOT
    from .run_holdout_v1_1 import read_freeze, read_holdout_assignment
    from .summarize_exploration_v1 import (
        PAPER_TOTAL, THRESHOLDS, TOTAL_BY_TYPE, calibration, paired,
        paper_style_weighted_exact, score_subset, type3_pair_breakdown, usage,
    )
except ImportError:
    from pilot_23way import ROOT
    from run_holdout_v1_1 import read_freeze, read_holdout_assignment
    from summarize_exploration_v1 import (
        PAPER_TOTAL, THRESHOLDS, TOTAL_BY_TYPE, calibration, paired,
        paper_style_weighted_exact, score_subset, type3_pair_breakdown, usage,
    )


FREEZE = ROOT / "prompts/mentalbench_holdout_freeze_v1_1.json"
RUN_DIR = ROOT / "results/holdout_v1_1_full"
MANIFEST = RUN_DIR / "manifest.json"
JOURNAL = RUN_DIR / "responses.jsonl"
RUN_SUMMARY = RUN_DIR / "summary.json"
OUT_JSON = RUN_DIR / "metrics.json"
OUT_MD = RUN_DIR / "report.md"
BOOTSTRAP_SEED = 20260927
BOOTSTRAP_REPLICATES = 2000
CASE_TYPES = ("type1", "type2", "type3", "type4")


def read_complete() -> tuple[list[dict], dict, dict]:
    freeze = read_freeze()
    holdout = read_holdout_assignment(freeze)
    if json.loads(MANIFEST.read_text(encoding="utf-8")) != freeze:
        raise RuntimeError("Holdout run manifest differs from the frozen protocol")
    summary = json.loads(RUN_SUMMARY.read_text(encoding="utf-8"))
    if (summary["successful_requests"] != freeze["expected_requests"]
            or summary["model"] != freeze["model"]):
        raise RuntimeError("The holdout is incomplete or used an unexpected model")
    records = []
    with JOURNAL.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            if record["status"] == "ok":
                records.append(record)
    if len(records) != freeze["expected_requests"]:
        raise RuntimeError("Holdout journal has the wrong number of successful requests")
    by_row: dict[int, dict[str, dict]] = defaultdict(dict)
    for record in records:
        row_index, arm = record["row_index"], record["arm"]
        if (arm not in freeze["arms"] or arm in by_row[row_index]
                or record["model"] != freeze["model"]
                or record["prompt_version"] != freeze["prompt_version"]):
            raise RuntimeError("Holdout journal has a duplicate, model change, or prompt change")
        by_row[row_index][arm] = record
    if len(by_row) != freeze["expected_cases"]:
        raise RuntimeError("Holdout journal does not contain every paired case")
    if set(by_row) != set(holdout):
        raise RuntimeError("Holdout journal row indices differ from the frozen split")
    for row_index, arms in by_row.items():
        if set(arms) != set(freeze["arms"]):
            raise RuntimeError("A holdout case lacks one of its two arms")
        left, right = arms["all23"], arms["four"]
        if (left["group_id"] != right["group_id"]
                or left["group_id"] != holdout[row_index]
                or left["case_type"] != right["case_type"]
                or left["option_codes"] != right["option_codes"]
                or left["key_codes"] != right["key_codes"]):
            raise RuntimeError("Paired holdout metadata disagree")
    groups = {record["group_id"] for record in records}
    if len(groups) != freeze["expected_groups"]:
        raise RuntimeError("Holdout result group count differs from the freeze")
    counts = {case_type: sum(arms["four"]["case_type"] == case_type
                             for arms in by_row.values()) for case_type in CASE_TYPES}
    if counts != freeze["expected_type_counts"]:
        raise RuntimeError("Holdout result type counts differ from the freeze")
    return records, summary, freeze


def paper_style_hit(record: dict, cutoff: float) -> int:
    if record["case_type"] in {"type1", "type2"}:
        return int(record["top1_code"] in record["key_codes"])
    selected = {code for code in record["option_codes"]
                if record["probabilities"][code] >= cutoff}
    return int(selected == set(record["key_codes"]))


def family_bootstrap_four(records: list[dict], cutoff: float) -> dict:
    """Resample reconstructed groups within Type 1, Type 2, and pair strata."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        if record["arm"] == "four":
            groups[record["group_id"]].append(record)
    strata: dict[str, list[dict[str, tuple[int, int]]]] = defaultdict(list)
    for group_records in groups.values():
        types = {record["case_type"] for record in group_records}
        if types == {"type1"}:
            stratum = "type1"
        elif types == {"type2"}:
            stratum = "type2"
        elif types == {"type3", "type4"}:
            stratum = "paired_type3_type4"
        else:
            raise RuntimeError("Unexpected reconstructed family structure")
        per_type = {}
        for case_type in types:
            subset = [record for record in group_records if record["case_type"] == case_type]
            per_type[case_type] = (sum(paper_style_hit(record, cutoff) for record in subset),
                                   len(subset))
        strata[stratum].append(per_type)
    if sum(len(values) for values in strata.values()) != 673:
        raise RuntimeError("Family bootstrap does not cover 673 independent groups")

    rng = random.Random(BOOTSTRAP_SEED)
    weighted = []
    type3 = []
    for _ in range(BOOTSTRAP_REPLICATES):
        hits = defaultdict(int)
        totals = defaultdict(int)
        for family_pool in strata.values():
            for _ in family_pool:
                sampled = rng.choice(family_pool)
                for case_type, (hit_count, n) in sampled.items():
                    hits[case_type] += hit_count
                    totals[case_type] += n
        score = sum(TOTAL_BY_TYPE[case_type] * hits[case_type] / totals[case_type]
                    for case_type in CASE_TYPES) / PAPER_TOTAL
        weighted.append(score)
        type3.append(hits["type3"] / totals["type3"])

    def interval(values: list[float]) -> list[float]:
        ordered = sorted(values)
        return [ordered[int(.025 * (len(ordered) - 1))],
                ordered[int(.975 * (len(ordered) - 1))]]

    return {
        "method": "Percentile bootstrap of reconstructed source groups, stratified as Type 1, Type 2, and linked Type 3/4 families",
        "seed": BOOTSTRAP_SEED,
        "replicates": BOOTSTRAP_REPLICATES,
        "group_counts_by_stratum": {key: len(value) for key, value in strata.items()},
        "paper_weighted_four_option_exact_95pct_interval": interval(weighted),
        "type3_four_option_exact_95pct_interval": interval(type3),
    }


def build_metrics(records: list[dict], run_summary: dict, freeze: dict) -> dict:
    by_arm = {}
    calibration_by_arm = {}
    usage_by_arm = {}
    for arm in freeze["arms"]:
        arm_records = [record for record in records if record["arm"] == arm]
        by_arm[arm] = {
            case_type: score_subset(arm_records if case_type == "all" else
                                    [record for record in arm_records
                                     if record["case_type"] == case_type])
            for case_type in ("all", *CASE_TYPES)
        }
        calibration_by_arm[arm] = calibration(arm_records)
        usage_by_arm[arm] = usage(arm_records)
    primary_cutoff = freeze["primary_differential_cutoff"]
    secondary_cutoff = freeze["secondary_type3_cutoff"]
    four_records = [record for record in records if record["arm"] == "four"]
    raw_primary_hits = sum(paper_style_hit(record, primary_cutoff)
                           for record in four_records)
    paper_weighted_by_cutoff = {
        f"{threshold:.2f}": paper_style_weighted_exact(by_arm, "four", threshold)
        for threshold in THRESHOLDS
    }
    return {
        "run_id": freeze["run_id"], "model": freeze["model"],
        "prompt_version": freeze["prompt_version"],
        "cases": freeze["expected_cases"], "source_groups": freeze["expected_groups"],
        "requests": len(records),
        "primary_cutoff": primary_cutoff,
        "secondary_type3_cutoff": secondary_cutoff,
        "primary_four_option_paper_style_raw_hits": raw_primary_hits,
        "primary_four_option_paper_style_raw_rate": raw_primary_hits / len(four_records),
        "primary_four_option_paper_weighted_rate": paper_weighted_by_cutoff[f"{primary_cutoff:.2f}"],
        "paper_weighted_four_option_exact_by_cutoff": paper_weighted_by_cutoff,
        "by_arm": by_arm,
        "paired_top1": paired(records),
        "calibration_by_arm": calibration_by_arm,
        "usage_by_arm": usage_by_arm,
        "family_bootstrap_primary": family_bootstrap_four(records, primary_cutoff),
        "type3_pair_breakdown_at_primary": type3_pair_breakdown(records, primary_cutoff),
        "type3_pair_breakdown_at_secondary": type3_pair_breakdown(records, secondary_cutoff),
        "type3_secondary_four_option_exact_rate": by_arm["four"]["type3"]["thresholds"][f"{secondary_cutoff:.2f}"]["offered_exact_set_rate"],
        "recorded_session_wall_seconds": run_summary["recorded_session_wall_seconds"],
        "estimated_success_cost_usd": run_summary["estimated_success_cost_usd"],
        "conservative_cost_upper_usd": run_summary["conservative_cost_upper_usd"],
        "recorded_failure_events": run_summary["recorded_failure_events"],
        "contains_case_text": False,
    }


def make_report(metrics: dict) -> str:
    by_arm = metrics["by_arm"]
    primary = f"{metrics['primary_cutoff']:.2f}"
    secondary = f"{metrics['secondary_type3_cutoff']:.2f}"
    ci = metrics["family_bootstrap_primary"]
    interval = ci["paper_weighted_four_option_exact_95pct_interval"]
    lines = [
        "# MentalBench frozen holdout results",
        "",
        f"Jev {metrics['model']} scored {metrics['cases']:,} synthetic cases from {metrics['source_groups']} reconstructed source groups in both all-23 and four-option conditions. This is benchmark performance, not clinical diagnostic accuracy.",
        "",
        "## Primary paper-style result",
        "",
        f"The prespecified four-option rule takes Jev's top diagnosis for Types 1–2 and the exact set of diagnoses at or above {primary} for Types 3–4. With the paper's full-dataset case-type weights, the holdout estimate is **{metrics['primary_four_option_paper_weighted_rate']:.1%}** (family-bootstrap 95% interval **{interval[0]:.1%}–{interval[1]:.1%}**). The raw holdout agreement is **{metrics['primary_four_option_paper_style_raw_hits']:,}/{metrics['cases']:,} = {metrics['primary_four_option_paper_style_raw_rate']:.1%}**. Weighting adjusts for the holdout's different type mix; it does not turn this subset into a direct paired rerun of published LLMs.",
        "",
        "| Type | Cases | All 23 top key hit | Four top key hit | Four exact offered set at primary cutoff |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for case_type in CASE_TYPES:
        a, b = by_arm["all23"][case_type], by_arm["four"][case_type]
        exact = b["thresholds"][primary]["offered_exact_set_rate"]
        lines.append(f"| {case_type} | {b['n']:,} | {a['top1_key_hit_rate']:.1%} | {b['top1_key_hit_rate']:.1%} | {exact:.1%} |")
    type3 = by_arm["four"]["type3"]
    lines += [
        "",
        "## Differentials and uncertainty",
        "",
        f"At the primary {primary} cutoff, the four-option Type 3 exact-set rate is {type3['thresholds'][primary]['offered_exact_set_rate']:.1%}; the family-bootstrap interval is {ci['type3_four_option_exact_95pct_interval'][0]:.1%}–{ci['type3_four_option_exact_95pct_interval'][1]:.1%}. At the prespecified {secondary} sensitivity cutoff, Type 3 exact-set agreement is {metrics['type3_secondary_four_option_exact_rate']:.1%}. The machine-readable metrics include the complete cutoff curve, Type 3 pair recovery, offered-label calibration and Brier scores, and paired top-answer results.",
        "",
        "Diagnoses outside a case's four supplied options are unadjudicated by the benchmark. The all-23 set measures must be read as benchmark proxies over the offered labels, not proof that extra diagnoses are clinically wrong.",
        "",
        "## Cost and latency",
        "",
        "| Arm | Requests | Input tokens | Estimated cost | Median latency | 90th percentile | Retries |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for arm in ("all23", "four"):
        u = metrics["usage_by_arm"][arm]
        lines.append(f"| {arm} | {u['requests']:,} | {u['input_tokens']:,} | ${u['estimated_cost_usd']:.4f} | {u['median_latency_seconds']:.3f}s | {u['p90_latency_seconds']:.3f}s | {u['retries']} |")
    wall = metrics["recorded_session_wall_seconds"]
    lines += [
        "",
        f"Successful calls cost an estimated **${metrics['estimated_success_cost_usd']:.4f}** at the frozen input-token rate. The conservative upper bound, including possibly billed failed attempts, is **${metrics['conservative_cost_upper_usd']:.4f}**. Recorded active run time is **{wall / 60:.1f} minutes** with three workers; paired cases completed per minute were **{metrics['cases'] / (wall / 60):.1f}**. Verify the account charge separately. There were **{metrics['recorded_failure_events']}** recorded failed request events.",
        "",
        "The 95% intervals resample reconstructed source groups within Type 1, Type 2, and linked Type 3/4 strata. They quantify this split's sampling uncertainty under that grouping assumption; they do not address possible label ambiguity or prove clinical validity.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    records, run_summary, freeze = read_complete()
    metrics = build_metrics(records, run_summary, freeze)
    OUT_JSON.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(make_report(metrics), encoding="utf-8")
    print(json.dumps({
        "cases": metrics["cases"], "source_groups": metrics["source_groups"],
        "primary_four_option_paper_weighted_rate": metrics["primary_four_option_paper_weighted_rate"],
        "primary_family_bootstrap_interval": metrics["family_bootstrap_primary"]["paper_weighted_four_option_exact_95pct_interval"],
        "estimated_success_cost_usd": metrics["estimated_success_cost_usd"],
        "recorded_session_wall_seconds": metrics["recorded_session_wall_seconds"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
