"""Summarize the complete, paired exploration run without reading case text."""

from __future__ import annotations

from collections import defaultdict
import json
import math
from pathlib import Path
from statistics import mean, median

try:
    from .pilot_23way import ROOT
except ImportError:
    from pilot_23way import ROOT


RUN_DIR = ROOT / "results/exploration_v1_full"
JOURNAL = RUN_DIR / "responses.jsonl"
RUN_SUMMARY = RUN_DIR / "summary.json"
OUT_JSON = RUN_DIR / "metrics.json"
OUT_MD = RUN_DIR / "report.md"
THRESHOLDS = tuple(index / 20 for index in range(1, 20))
REPORT_THRESHOLDS = (0.50, 0.70, 0.80, 0.90)
LOW_CUTOFF_REVIEW = (0.20, 0.30, 0.40, 0.50, 0.60, 0.70)
TOTAL_BY_TYPE = {"type1": 1725, "type2": 3450, "type3": 6525, "type4": 13050}
PAPER_TOTAL = sum(TOTAL_BY_TYPE.values())


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    return ordered[math.ceil(len(ordered) * fraction) - 1]


def rate(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def read_complete() -> tuple[list[dict], dict]:
    run_summary = json.loads(RUN_SUMMARY.read_text(encoding="utf-8"))
    records = []
    with JOURNAL.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            if record["status"] == "ok":
                records.append(record)
    expected = run_summary["expected_requests"]
    if len(records) != expected or expected != 3930:
        raise RuntimeError("Exploration run is incomplete; refusing final metrics")
    keys = {(r["row_index"], r["arm"]) for r in records}
    if len(keys) != expected or len({r["row_index"] for r in records}) != 1965:
        raise RuntimeError("Expected exactly one successful result per case and arm")
    if {r["model"] for r in records} != {"jev-1.13.0"}:
        raise RuntimeError("Unexpected model version in exploration results")
    return records, run_summary


def score_subset(records: list[dict]) -> dict:
    n = len(records)
    if not n:
        return {"n": 0}
    top_hits = []
    outside_top = []
    group_top: dict[str, list[int]] = defaultdict(list)
    for record in records:
        hit = int(record["top1_code"] in record["key_codes"])
        top_hits.append(hit)
        outside_top.append(int(record["top1_code"] not in record["option_codes"]))
        group_top[record["group_id"]].append(hit)
    result = {
        "n": n,
        "source_groups": len(group_top),
        "top1_key_hit_count": sum(top_hits),
        "top1_key_hit_rate": mean(top_hits),
        "top1_key_hit_group_mean": mean(mean(values) for values in group_top.values()),
        "top1_outside_options_count": sum(outside_top),
        "top1_outside_options_rate": mean(outside_top),
        "thresholds": {},
    }
    for threshold in THRESHOLDS:
        true_positives = false_positives = false_negatives = 0
        exact = both = some = none = 0
        key_recall_sum = 0.0
        offered_list_size_sum = all_list_size_sum = 0
        group_exact: dict[str, list[int]] = defaultdict(list)
        group_all_keys: dict[str, list[int]] = defaultdict(list)
        for record in records:
            probabilities = record["probabilities"]
            keys = set(record["key_codes"])
            offered = set(record["option_codes"])
            selected = {code for code, p in probabilities.items() if p >= threshold}
            selected_offered = selected & offered
            tp = len(selected_offered & keys)
            fp = len(selected_offered - keys)
            fn = len(keys - selected_offered)
            true_positives += tp
            false_positives += fp
            false_negatives += fn
            match = int(selected_offered == keys)
            exact += match
            group_exact[record["group_id"]].append(match)
            both += int(tp == len(keys))
            group_all_keys[record["group_id"]].append(int(tp == len(keys)))
            some += int(0 < tp < len(keys))
            none += int(tp == 0)
            key_recall_sum += tp / len(keys)
            offered_list_size_sum += len(selected_offered)
            all_list_size_sum += len(selected)
        precision = rate(true_positives, true_positives + false_positives)
        recall = rate(true_positives, true_positives + false_negatives)
        f1 = (2 * precision * recall / (precision + recall)
              if precision is not None and recall is not None and precision + recall else None)
        result["thresholds"][f"{threshold:.2f}"] = {
            "offered_exact_set_count": exact,
            "offered_exact_set_rate": exact / n,
            "offered_exact_set_group_mean": mean(mean(v) for v in group_exact.values()),
            "all_keys_included_count": both,
            "all_keys_included_group_mean": mean(mean(v) for v in group_all_keys.values()),
            "some_but_not_all_keys_count": some,
            "no_keys_included_count": none,
            "mean_key_recall": key_recall_sum / n,
            "mean_offered_set_size": offered_list_size_sum / n,
            "mean_full_set_size": all_list_size_sum / n,
            "offered_micro_precision": precision,
            "offered_micro_recall": recall,
            "offered_micro_f1": f1,
            "offered_tp": true_positives,
            "offered_fp": false_positives,
            "offered_fn": false_negatives,
        }
    return result


def calibration(records: list[dict]) -> dict:
    pairs = []
    for record in records:
        key_set = set(record["key_codes"])
        for code in record["option_codes"]:
            pairs.append((record["probabilities"][code], int(code in key_set)))
    bins = []
    for index in range(10):
        lo = index / 10
        hi = (index + 1) / 10
        selected = [(p, y) for p, y in pairs if lo <= p < hi or (index == 9 and p == 1)]
        bins.append({"range": f"[{lo:.1f},{hi:.1f}{']' if index == 9 else ')'}",
                     "n": len(selected),
                     "mean_probability": mean(p for p, _ in selected) if selected else None,
                     "benchmark_positive_rate": mean(y for _, y in selected) if selected else None})
    return {"n_offered_diagnosis_case_pairs": len(pairs),
            "brier_score": mean((p - y) ** 2 for p, y in pairs),
            "bins": bins}


def usage(records: list[dict]) -> dict:
    latencies = [r["elapsed_seconds_total"] for r in records]
    inputs = [r["input_tokens"] for r in records]
    return {"requests": len(records),
            "input_tokens": sum(inputs),
            "output_tokens": sum(r["output_tokens"] for r in records),
            "estimated_cost_usd": round(sum(r["estimated_cost_usd"] for r in records), 8),
            "mean_input_tokens_per_request": mean(inputs),
            "mean_latency_seconds": mean(latencies),
            "median_latency_seconds": median(latencies),
            "p90_latency_seconds": percentile(latencies, .90),
            "retries": sum(r["retry_count"] for r in records)}


def paired(records: list[dict]) -> dict:
    by_row: dict[int, dict[str, dict]] = defaultdict(dict)
    for record in records:
        by_row[record["row_index"]][record["arm"]] = record
    result = {}
    for case_type in ("all", "type1", "type2", "type3", "type4"):
        subset = [arms for arms in by_row.values()
                  if case_type == "all" or arms["all23"]["case_type"] == case_type]
        all_hit = [int(a["all23"]["top1_code"] in a["all23"]["key_codes"]) for a in subset]
        four_hit = [int(a["four"]["top1_code"] in a["four"]["key_codes"]) for a in subset]
        result[case_type] = {
            "n": len(subset),
            "all23_top1_key_hit_rate": mean(all_hit),
            "four_top1_key_hit_rate": mean(four_hit),
            "four_minus_all23_top1_hit_rate": mean(four_hit) - mean(all_hit),
            "improved_case_count": sum(not a and b for a, b in zip(all_hit, four_hit)),
            "worsened_case_count": sum(a and not b for a, b in zip(all_hit, four_hit)),
            "unchanged_case_count": sum(a == b for a, b in zip(all_hit, four_hit)),
        }
    return result


def type3_pair_breakdown(records: list[dict], threshold: float = 0.40) -> dict:
    groups: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        if record["case_type"] == "type3":
            pair_code = record["group_id"].split(":", 1)[0]
            groups[pair_code][record["arm"]].append(record)
    result = {}
    for pair_code, arms in sorted(groups.items()):
        result[pair_code] = {}
        for arm in ("all23", "four"):
            subset = arms[arm]
            both = sum(all(r["probabilities"][code] >= threshold for code in r["key_codes"])
                       for r in subset)
            exact = sum({code for code in r["option_codes"] if r["probabilities"][code] >= threshold}
                        == set(r["key_codes"]) for r in subset)
            top = sum(r["top1_code"] in r["key_codes"] for r in subset)
            result[pair_code][arm] = {"cases": len(subset), "both_keys_count": both,
                                     "exact_offered_set_count": exact,
                                     "top1_key_hit_count": top}
    return result


def paper_style_weighted_exact(by_arm: dict, arm: str, threshold: float) -> float:
    """Paper task shape: one answer for Types 1/2, exact sets for Types 3/4."""
    key = f"{threshold:.2f}"
    score = 0.0
    for case_type, count in TOTAL_BY_TYPE.items():
        if case_type in ("type1", "type2"):
            accuracy = by_arm[arm][case_type]["top1_key_hit_rate"]
        else:
            accuracy = by_arm[arm][case_type]["thresholds"][key]["offered_exact_set_rate"]
        score += count * accuracy
    return score / PAPER_TOTAL


def format_pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.1f}%"


def make_report(metrics: dict) -> str:
    by_arm = metrics["by_arm"]
    lines = [
        "# MentalBench v1 full exploration results",
        "",
        "This is the frozen **exploration** partition: 1,965 synthetic cases in 107 reconstructed source groups. The 22,785-case holdout has not been scored. Each case received one all-23 and one four-option Jev request. The question version and clinical guides were fixed for this run. All measures below concern benchmark labels, not clinical diagnostic accuracy.",
        "",
        "## Required top diagnosis",
        "",
        "| Case type | Cases | All 23: top diagnosis in key | Four options: top diagnosis in key |",
        "| --- | ---: | ---: | ---: |",
    ]
    for case_type in ("all", "type1", "type2", "type3", "type4"):
        a = by_arm["all23"][case_type]
        b = by_arm["four"][case_type]
        lines.append(f"| {case_type} | {a['n']} | {format_pct(a['top1_key_hit_rate'])} | {format_pct(b['top1_key_hit_rate'])} |")
    lines += [
        "",
        f"For Type 3, a top diagnosis counts as a hit when it matches either of the two keyed labels; it does not demonstrate that both were retained. An all-23 label outside the supplied choices led in {by_arm['all23']['all']['top1_outside_options_count']} of 1,965 cases; those are unadjudicated disagreements.",
        "",
        "## Differential: all diagnoses at or above each cutoff",
        "",
        "Exact set and precision below are scored **within the four supplied options**. The all-23 run may also list diagnoses outside those options; the benchmark does not label those as negatives.",
        "",
        "| Arm | Cutoff | All types: exact offered set | Type 3: both keyed included | Type 3: exact offered set | Mean full set size |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for arm in ("all23", "four"):
        for threshold in REPORT_THRESHOLDS:
            key = f"{threshold:.2f}"
            all_metrics = by_arm[arm]["all"]["thresholds"][key]
            type3 = by_arm[arm]["type3"]["thresholds"][key]
            lines.append(f"| {arm} | {key} | {format_pct(all_metrics['offered_exact_set_rate'])} | {format_pct(type3['all_keys_included_count'] / 180)} | {format_pct(type3['offered_exact_set_rate'])} | {all_metrics['mean_full_set_size']:.2f} |")
    lines += ["", "## Exploratory lower cutoff review", "",
              "These additional cutoffs were examined only after the exploration scores were saved. They are candidates for a decision rule to freeze before holdout.", "",
              "| Arm | Cutoff | Type 3: both keyed included | Type 3: exact offered set | Type 4: exact offered set | Overall exact offered set | Mean full set size |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for arm in ("all23", "four"):
        for threshold in LOW_CUTOFF_REVIEW:
            key = f"{threshold:.2f}"
            all_metrics = by_arm[arm]["all"]["thresholds"][key]
            type3 = by_arm[arm]["type3"]["thresholds"][key]
            type4 = by_arm[arm]["type4"]["thresholds"][key]
            lines.append(f"| {arm} | {key} | {format_pct(type3['all_keys_included_count'] / 180)} | {format_pct(type3['offered_exact_set_rate'])} | {format_pct(type4['offered_exact_set_rate'])} | {format_pct(all_metrics['offered_exact_set_rate'])} | {all_metrics['mean_full_set_size']:.2f} |")
    lines += ["", "## Paper-style four-option exact-match estimate", "",
              "The paper asks for one answer on Types 1 and 2, and an exact answer set on Types 3 and 4. This development estimate therefore uses Jev's top diagnosis for Types 1/2 and the thresholded four-option set for Types 3/4, then applies the paper's type weights (1,725 / 3,450 / 6,525 / 13,050 cases). It remains a development estimate from only 107 source groups.",
              "",
              "| Cutoff for Type 3/4 sets | Type 3 exact set | Type 4 exact set | Weighted overall exact match |",
              "| ---: | ---: | ---: | ---: |"]
    for threshold in THRESHOLDS:
        key = f"{threshold:.2f}"
        type3 = by_arm["four"]["type3"]["thresholds"][key]
        type4 = by_arm["four"]["type4"]["thresholds"][key]
        weighted = metrics["paper_weighted_four_option_exact_by_cutoff"][key]
        lines.append(f"| {key} | {format_pct(type3['offered_exact_set_rate'])} | {format_pct(type4['offered_exact_set_rate'])} | {format_pct(weighted)} |")
    sample_n = sum(by_arm["four"][t]["n"] for t in ("type1", "type2", "type3", "type4"))
    sample_hits = (
        by_arm["four"]["type1"]["top1_key_hit_count"]
        + by_arm["four"]["type2"]["top1_key_hit_count"]
        + by_arm["four"]["type3"]["thresholds"]["0.50"]["offered_exact_set_count"]
        + by_arm["four"]["type4"]["thresholds"]["0.50"]["offered_exact_set_count"]
    )
    lines += ["",
              f"On the actual exploration split, the same paper-shaped scoring rule gives {sample_hits:,}/{sample_n:,} = {format_pct(sample_hits / sample_n)} at 0.50. This raw split rate is not representative of the paper's case mix because exploration contains relatively more Type 1/2 rows; the paper-weighted estimate above is the appropriate summary for comparison, and both remain development results.",
              "",
              "For Type 3, the paper reports exact-set accuracy of 9.01% for GPT-5-mini, 22.48% for GPT-5.1, 14.99% for Claude Sonnet 4.5, 40.25% for GPT-4o, and 54.19% for Qwen 3 235B. Jev's four-option exploration exact-set rates are 41.1% at 0.40 and 36.1% at 0.50. These are not head-to-head results: Jev's figures cover 180 related exploration variants from 12 Type 3 source groups, whereas the paper reports the full benchmark. [MentalBench paper](https://arxiv.org/html/2602.12871).",
              "",
              "## Type 3 pair coverage at the exploratory 0.40 cutoff", "",
              "Each diagnosis pair contributes one reconstructed source group and 15 related narrative cases. Counts below show cases where both benchmark keys cleared 0.40; the group is the independent unit.", "",
              "| Diagnosis pair | All 23: both keys / 15 | Four options: both keys / 15 |",
              "| --- | ---: | ---: |"]
    for pair_code, arms in metrics["type3_pair_breakdown_at_0_40"].items():
        lines.append(f"| {pair_code} | {arms['all23']['both_keys_count']}/15 | {arms['four']['both_keys_count']}/15 |")
    lines += ["", "## Cost and timing", "",
              "| Arm | Requests | Input tokens | Cost | Median request | 90th percentile request | Retries |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for arm in ("all23", "four"):
        u = metrics["usage_by_arm"][arm]
        lines.append(f"| {arm} | {u['requests']:,} | {u['input_tokens']:,} | ${u['estimated_cost_usd']:.4f} | {u['median_latency_seconds']:.3f}s | {u['p90_latency_seconds']:.3f}s | {u['retries']} |")
    lines += ["",
              f"Total exploration API cost: **${metrics['total_estimated_cost_usd']:.4f}**. Run wall time: **{metrics['run_wall_seconds'] / 60:.1f} minutes** with three concurrent workers. The input-token cost is calculated from TypeSafe's documented Jev 1.13 rate; output tokens are free. The actual account charge should be checked independently.",
              "",
              "## Limits and next decision", "",
              "This exploration set contains related narrative variants; the 107 source groups are the relevant independent units. The results can guide a cutoff choice but are development estimates. The four supplied options adjudicate only those four labels. After choosing and recording a cutoff, the protected holdout can provide an independent assessment. MentalBench has no cases whose correct answer is 'no diagnosis.'", ""]
    return "\n".join(lines)


def main() -> None:
    records, run_summary = read_complete()
    by_arm = {}
    usage_by_arm = {}
    calibration_by_arm = {}
    projection = {}
    for arm in ("all23", "four"):
        arm_records = [r for r in records if r["arm"] == arm]
        by_arm[arm] = {case_type: score_subset(
            arm_records if case_type == "all" else [r for r in arm_records if r["case_type"] == case_type])
            for case_type in ("all", "type1", "type2", "type3", "type4")}
        usage_by_arm[arm] = usage(arm_records)
        calibration_by_arm[arm] = calibration(arm_records)
        projection[arm] = {}
        for case_type, total in TOTAL_BY_TYPE.items():
            subset = [r for r in arm_records if r["case_type"] == case_type]
            holdout_n = total - len(subset)
            projection[arm][case_type] = {
                "holdout_cases": holdout_n,
                "development_mean_cost_usd": mean(r["estimated_cost_usd"] for r in subset),
                "projected_holdout_cost_usd": holdout_n * mean(r["estimated_cost_usd"] for r in subset),
            }
    metrics = {
        "run_id": "mentalbench_exploration_v1_both_arms",
        "model": "jev-1.13.0", "cases": 1965, "source_groups": 107,
        "requests": len(records), "by_arm": by_arm,
        "usage_by_arm": usage_by_arm,
        "calibration_by_arm": calibration_by_arm,
        "paired_top1": paired(records),
        "type3_pair_breakdown_at_0_40": type3_pair_breakdown(records),
        "paper_weighted_four_option_exact_by_cutoff": {
            f"{threshold:.2f}": paper_style_weighted_exact(by_arm, "four", threshold)
            for threshold in THRESHOLDS
        },
        "total_estimated_cost_usd": sum(u["estimated_cost_usd"] for u in usage_by_arm.values()),
        "run_wall_seconds": run_summary["current_session_wall_seconds"],
        "holdout_cost_projection_by_type": projection,
        "holdout_cost_projection_total_usd": sum(v["projected_holdout_cost_usd"]
                                                  for arm in projection.values() for v in arm.values()),
        "contains_case_text": False,
    }
    OUT_JSON.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(make_report(metrics), encoding="utf-8")
    print(json.dumps({
        "cases": metrics["cases"], "requests": metrics["requests"],
        "top1_by_type": {arm: {case_type: by_arm[arm][case_type]["top1_key_hit_rate"]
                              for case_type in ("all", "type1", "type2", "type3", "type4")}
                         for arm in ("all23", "four")},
        "type3_by_cutoff": {arm: {t: by_arm[arm]["type3"]["thresholds"][t]["all_keys_included_count"]
                                  for t in ("0.50", "0.70", "0.80", "0.90")}
                            for arm in ("all23", "four")},
        "usage_by_arm": usage_by_arm,
        "total_estimated_cost_usd": metrics["total_estimated_cost_usd"],
        "holdout_cost_projection_total_usd": metrics["holdout_cost_projection_total_usd"],
        "run_wall_seconds": metrics["run_wall_seconds"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
