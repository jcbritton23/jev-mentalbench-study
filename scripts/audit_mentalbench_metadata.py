"""Aggregate MentalBench structure without printing or saving case text.

Usage: python scripts/audit_mentalbench_metadata.py
"""

from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/raw/mentalbench.csv"
DEST = ROOT / "data/interim/mentalbench_metadata_audit.json"
REVISION = "1b1d88771ab92744a77bd9e05ce762a654b9551d"


def size_summary(groups):
    sizes = Counter(len(v) for v in groups.values())
    return {"groups": len(groups), "rows_per_group": dict(sorted(sizes.items()))}


def main():
    groups = {name: defaultdict(list) for name in (
        "type_code_id", "code_id", "type_code_id_model", "code", "type_code",
        "type_id", "id", "question_hash", "option_hash", "type_code_id_answer",
        "candidate_seed",
    )}
    types = Counter()
    codes_by_type = defaultdict(set)
    models = Counter()
    empty = Counter()
    type_code_model = Counter()
    answer_letter_count_by_type = defaultdict(Counter)
    id_prefixes = Counter()
    malformed_ids = 0
    question_chars = []
    preview_seed_keys = set()
    option_hashes_by_seed = defaultdict(set)
    ids_by_code_option = defaultdict(set)
    sha = hashlib.sha256()
    with SOURCE.open("rb") as raw:
        for block in iter(lambda: raw.read(1024 * 1024), b""):
            sha.update(block)
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        for index, row in enumerate(reader):
            t, c, m, i = (row[name].strip() for name in ("type", "code", "model", "id"))
            types[t] += 1
            models[m] += 1
            codes_by_type[t].add(c)
            type_code_model[(t, c, m)] += 1
            for name in fields:
                if not row[name] or not row[name].strip():
                    empty[name] += 1
            id_prefixes[i[:1]] += 1
            match = re.fullmatch(r"([lmh])(\d{3})", i)
            if not match:
                malformed_ids += 1
                seed_key = (c, "unparsed", i)
            else:
                seed_key = (c, match.group(1), (int(match.group(2)) - 1) // 5)
            if index < 100:
                preview_seed_keys.add(seed_key)
            option_hash = hashlib.sha256(row["option"].encode()).hexdigest()
            option_hashes_by_seed[seed_key].add(option_hash)
            if match:
                ids_by_code_option[(c, option_hash)].add(int(match.group(2)))
            answer_prefix = re.split(r"[.)]", row["answer"].strip().upper(), maxsplit=1)[0]
            answer_letter_count_by_type[t][len(set(re.findall(r"\b[A-D]\b", answer_prefix)))] += 1
            question_chars.append(len(row["question"]))
            keys = {
                "type_code_id": (t, c, i),
                "code_id": (c, i),
                "type_code_id_model": (t, c, i, m),
                "code": (c,),
                "type_code": (t, c),
                "type_id": (t, i),
                "id": (i,),
                "question_hash": (hashlib.sha256(row["question"].encode()).hexdigest(),),
                "option_hash": (option_hash,),
                "type_code_id_answer": (t, c, i, row["answer"]),
                "candidate_seed": seed_key,
            }
            for name, key in keys.items():
                groups[name][key].append(index)

    code_counter = Counter({key[0]: len(v) for key, v in groups["code"].items()})
    single_codes = {c for c in code_counter if "_" not in c}
    pair_codes = {c for c in code_counter if "_" in c}
    pair_covered_codes = {part for code in pair_codes for part in code.split("_")}
    code_prefixes = Counter(key[0].split("_")[0][:4] for key in groups["code"])
    type_code_id = groups["type_code_id"]
    code_id_types = defaultdict(set)
    for (t, c, i), members in type_code_id.items():
        code_id_types[(c, i)].add(t)
    cross_type = Counter(len(v) for v in code_id_types.values())
    partial_option_seed_blocks = 0
    for (_, _), ids in ids_by_code_option.items():
        block_counts = Counter((id_number - 1) // 5 for id_number in ids)
        partial_option_seed_blocks += sum(count != 5 for count in block_counts.values())
    report = {
        "source": "https://huggingface.co/datasets/hysong/MentalBench",
        "revision": REVISION,
        "sha256": sha.hexdigest(),
        "file_bytes": SOURCE.stat().st_size,
        "rows": len(question_chars),
        "fields": fields,
        "empty_fields": dict(empty),
        "type_counts": dict(sorted(types.items())),
        "model_counts": dict(sorted(models.items())),
        "code_count": len(code_counter),
        "single_diagnosis_code_count": len(single_codes),
        "diagnosis_pair_code_count": len(pair_codes),
        "single_codes_absent_from_pairs": sorted(single_codes - pair_covered_codes),
        "code_size_min_max": [min(code_counter.values()), max(code_counter.values())],
        "code_prefix_count": dict(sorted(code_prefixes.items())),
        "codes_per_type": {t: len(v) for t, v in sorted(codes_by_type.items())},
        "id_prefix_counts": dict(sorted(id_prefixes.items())),
        "malformed_ids": malformed_ids,
        "answer_letter_count_by_type": {
            t: dict(sorted(counts.items())) for t, counts in sorted(answer_letter_count_by_type.items())
        },
        "question_chars_min_median_max": [min(question_chars), sorted(question_chars)[len(question_chars)//2], max(question_chars)],
        "group_summaries": {name: size_summary(group) for name, group in groups.items()},
        "types_per_code_id": dict(sorted(cross_type.items())),
        "candidate_seed_grouping_assumption": "Consecutive blocks of five id numbers correspond to five profiles per source seed; validate against source generation process before a split.",
        "candidate_seed_groups_in_first_100_rows": len(preview_seed_keys),
        "distinct_option_sets_per_candidate_seed": dict(sorted(Counter(map(len, option_hashes_by_seed.values())).items())),
        "partial_five_id_blocks_within_code_option_sets": partial_option_seed_blocks,
        "unique_question_hashes": len(groups["question_hash"]),
        "question_duplicate_groups": sum(len(v) > 1 for v in groups["question_hash"].values()),
        "question_duplicate_rows": sum(len(v) for v in groups["question_hash"].values() if len(v) > 1),
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
