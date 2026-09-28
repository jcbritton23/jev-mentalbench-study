"""Make a seed-grouped MentalBench exploration/holdout split.

Reads case text locally to verify the source file, but writes only identifiers,
split assignments, and aggregate counts. It makes no API requests.
"""

from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/raw/mentalbench.csv"
OUTPUT = ROOT / "data/processed"
SOURCE_SHA256 = "92b8d1c835a1aad22161e2b4bc1444823ed22d91275df99463b3b5e488bec957"
SPLIT_VERSION = "mentalbench-seed-groups-v1"
SALT = "jev-psych-2026-09-27-split-v1"


def priority(value):
    return hashlib.sha256(f"{SALT}|{value}".encode()).hexdigest()


def save_if_new_or_identical(path, contents):
    payload = contents.encode("utf-8")
    if path.exists():
        if path.read_bytes() != payload:
            raise RuntimeError(f"Existing split artifact differs: {path}")
        return
    path.write_bytes(payload)


def csv_text(fieldnames, records):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return stream.getvalue()


def main():
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if source_hash != SOURCE_SHA256:
        raise RuntimeError("MentalBench source hash changed; audit the new source before splitting")

    groups = defaultdict(lambda: {"rows": [], "types": set(), "models": Counter(), "option_hashes": set()})
    row_groups = []
    preview_groups = set()
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as stream:
        for row_index, row in enumerate(csv.DictReader(stream)):
            code, profile_id = row["code"].strip(), row["id"].strip()
            match = re.fullmatch(r"([lmh])(\d{3})", profile_id)
            if not match:
                raise RuntimeError(f"Unexpected profile ID at row {row_index}")
            family, profile_number = match.group(1), int(match.group(2))
            if family != {"type1": "l", "type2": "m", "type3": "h", "type4": "h"}[row["type"]]:
                raise RuntimeError(f"Unexpected type/profile combination at row {row_index}")
            if ("_" in code) != (family == "h"):
                raise RuntimeError(f"Unexpected code/profile combination at row {row_index}")
            block = (profile_number - 1) // 5
            group_id = f"{code}:{family}:{block:02d}"
            group = groups[group_id]
            group["rows"].append(row_index)
            group["types"].add(row["type"])
            group["models"][row["model"]] += 1
            group["option_hashes"].add(hashlib.sha256(row["option"].encode()).hexdigest())
            row_groups.append(group_id)
            if row_index < 100:
                preview_groups.add(group_id)

    if len(row_groups) != 24750 or len(groups) != 780 or len(preview_groups) != 7:
        raise RuntimeError("Source structure differs from the audited dataset")
    for group_id, group in groups.items():
        code, family, _ = group_id.split(":")
        expected_rows = 45 if family == "h" else 15
        expected_types = {"h": {"type3", "type4"}, "l": {"type1"}, "m": {"type2"}}[family]
        if len(group["rows"]) != expected_rows or group["types"] != expected_types:
            raise RuntimeError(f"Incomplete reconstructed seed group: {group_id}")
        if len(group["option_hashes"]) != 1:
            raise RuntimeError(f"Mixed option sets in reconstructed seed group: {group_id}")
        if set(group["models"].values()) != {expected_rows // 3}:
            raise RuntimeError(f"Generator imbalance in reconstructed seed group: {group_id}")

    dev = set(preview_groups)
    single_codes = sorted({g.split(":")[0] for g in groups if "_" not in g})
    pair_codes = sorted({g.split(":")[0] for g in groups if "_" in g})
    if len(single_codes) != 23 or len(pair_codes) != 87:
        raise RuntimeError("Diagnosis code coverage changed")

    # Two independent seeds for both chart and patient-report presentation of
    # each diagnosis. Exposed groups are retained and counted toward the two.
    for code in single_codes:
        for family in ("l", "m"):
            candidates = sorted(
                (g for g in groups if g.startswith(f"{code}:{family}:")),
                key=priority,
            )
            existing = {g for g in dev if g.startswith(f"{code}:{family}:")}
            dev.update(candidates[: max(0, 2 - len(existing))])

    # Select a deterministic cover of the 23 disorders from published pair
    # codes. A pair is selected for development only once, then one seed of it.
    uncovered = set(single_codes)
    selected_pairs = []
    while uncovered:
        candidates = sorted(
            pair_codes,
            key=lambda c: (-len(set(c.split("_")) & uncovered), priority(c)),
        )
        chosen = candidates[0]
        newly_covered = set(chosen.split("_")) & uncovered
        if not newly_covered:
            raise RuntimeError("No diagnosis-pair cover exists")
        selected_pairs.append(chosen)
        uncovered -= newly_covered
    for code in selected_pairs:
        candidates = sorted((g for g in groups if g.startswith(f"{code}:h:")), key=priority)
        dev.add(candidates[0])

    holdout = set(groups) - dev
    if dev & holdout or dev | holdout != set(groups):
        raise RuntimeError("Group assignment overlap or omission")
    if not preview_groups <= dev:
        raise RuntimeError("A preview-exposed group entered holdout")

    counts_by_split = Counter()
    type_counts = defaultdict(Counter)
    model_counts = defaultdict(Counter)
    development_seed_coverage = Counter()
    group_records = []
    for group_id in sorted(groups):
        code, family, _ = group_id.split(":")
        group = groups[group_id]
        split = "exploration" if group_id in dev else "holdout"
        counts_by_split[split] += len(group["rows"])
        for t in group["types"]:
            type_counts[split][t] += 15 if family == "h" and t == "type3" else (30 if family == "h" else 15)
        model_counts[split].update(group["models"])
        if split == "exploration":
            for diagnosis_code in code.split("_"):
                development_seed_coverage[diagnosis_code] += 1
        group_records.append({
            "group_id": group_id,
            "split": split,
            "row_count": len(group["rows"]),
            "case_types": "+".join(sorted(group["types"])),
            "preview_exposed": int(group_id in preview_groups),
        })
    if min(development_seed_coverage.values()) < 5 or len(development_seed_coverage) != 23:
        raise RuntimeError("Development seed coverage below five for a diagnosis")
    if counts_by_split["exploration"] / len(row_groups) > 0.10:
        raise RuntimeError("Exploration partition exceeds 10% of rows")
    if any(type_counts[split][t] == 0 for split in ("exploration", "holdout") for t in ("type1", "type2", "type3", "type4")):
        raise RuntimeError("A partition lacks a case type")

    group_csv = csv_text(
        ["group_id", "split", "row_count", "case_types", "preview_exposed"],
        group_records,
    )
    row_csv = csv_text(
        ["row_index", "group_id", "split"],
        (dict(row_index=i, group_id=g, split="exploration" if g in dev else "holdout")
         for i, g in enumerate(row_groups)),
    )
    summary = {
        "version": SPLIT_VERSION,
        "source_sha256": SOURCE_SHA256,
        "selection_salt": SALT,
        "row_counts": dict(counts_by_split),
        "group_counts": {"exploration": len(dev), "holdout": len(holdout)},
        "type_counts": {s: dict(sorted(c.items())) for s, c in type_counts.items()},
        "generator_counts": {s: dict(sorted(c.items())) for s, c in model_counts.items()},
        "development_seed_coverage_min_max": [min(development_seed_coverage.values()), max(development_seed_coverage.values())],
        "selected_pair_code_count": len(selected_pairs),
        "preview_groups_in_exploration": len(preview_groups),
        "group_manifest_sha256": hashlib.sha256(group_csv.encode()).hexdigest(),
        "row_manifest_sha256": hashlib.sha256(row_csv.encode()).hexdigest(),
        "raw_text_in_manifests": False,
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    save_if_new_or_identical(OUTPUT / "mentalbench_group_split_v1.csv", group_csv)
    save_if_new_or_identical(OUTPUT / "mentalbench_row_split_v1.csv", row_csv)
    save_if_new_or_identical(
        OUTPUT / "mentalbench_split_summary_v1.json",
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
