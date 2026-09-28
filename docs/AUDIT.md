# MentalBench metadata audit — 2026-09-27

This audit used the local, Git-ignored source CSV and printed only counts, identifiers, schema, and hashes. It did not print or send case descriptions, options, or answer text. Reproduce with `python3 scripts/audit_mentalbench_metadata.py`; aggregate JSON is in ignored `data/interim/mentalbench_metadata_audit.json`.

Source: <https://huggingface.co/datasets/hysong/MentalBench>, revision `1b1d88771ab92744a77bd9e05ce762a654b9551d`, CC BY 4.0 dataset declaration. Local CSV SHA-256: `92b8d1c835a1aad22161e2b4bc1444823ed22d91275df99463b3b5e488bec957`. The single published split is named `train`; there is no published development/test partition.

## Observed structure

| Check | Result |
| --- | ---: |
| Rows | 24,750 |
| Type 1 / 2 / 3 / 4 | 1,725 / 3,450 / 6,525 / 13,050 |
| Narrative generators | 3, each contributing 8,250 rows |
| Single-diagnosis codes / diagnosis-pair codes | 23 / 87 |
| Unique `code + id` profiles | 3,900 |
| Profiles represented by 3 / 9 rows | 1,725 / 2,175 |
| Distinct case-text hashes | 24,750; no exact duplicate text |
| Missing values in the seven CSV fields | 0 |
| Type 3 keys with two option letters | 6,525 of 6,525 |
| Types 1, 2, and 4 keys with one option letter | All 18,225 |

The seven fields are `type`, `code`, `model`, `id`, `question`, `option`, and `answer`. The 87 pair codes have the same `code + id` in Type 3 and Type 4; the three generators and both clear-case variants make **nine rows per profile**. Thus row-level, generator-level, and type-level splitting would leak related cases. Exact text deduplication would miss all of these relationships.

The paper states that five patient profiles are generated per underlying seed. IDs are shaped `l001`–`l025`, `m001`–`m050`, and `h001`–`h025` within a code. Grouping consecutive blocks of five IDs within each code yields **780 candidate seed groups**: 345 groups of 15 rows and 435 groups of 45 rows. Every candidate group has exactly one identical option set across its rows. In the reverse check, within each code, **zero option sets split a five-ID block**: every block represented in an option set contributes all five IDs. The grouping also keeps the Type 3 and Type 4 versions of each high-difficulty profile together. These checks agree with the paper's five-profile generation process. The released CSV still has no explicit seed identifier and the authors' profile-generation code is not present in the public repository, so describe this as a strongly supported reconstructed seed key rather than a source-provided key.

The first 100 published rows were exposed through an earlier public data preview. They map to seven candidate seed groups; those groups and any verified relatives must be assigned to development or excluded from holdout. No held-out row contents were viewed in this audit.

## Frozen exploration/holdout assignment, version 1

The earlier estimate of 300 families as roughly 900 rows was wrong at the underlying-seed level. Three hundred of 780 seed groups would reserve about 38% of groups for development, before accounting for unequal group sizes. The actual split uses a smaller, deterministic selection made by `scripts/make_mentalbench_split.py` against the fixed source SHA-256 above.

| Partition | Seed groups | Rows | Share |
| --- | ---: | ---: | ---: |
| Exploration | 107 | 1,965 | 7.94% |
| Holdout | 673 | 22,785 | 92.06% |

Exploration includes two source seeds for each diagnosis in Type 1, two in Type 2, and one seed from each of 12 selected pair codes covering all 23 diagnoses in Types 3–4. Seven preview-exposed groups are forced into exploration. All 23 diagnosis codes occur in the holdout overall, and each of the four case types occurs in both partitions. Development coverage is 5–8 reconstructed seed groups per diagnosis. Each narrative generator contributes exactly 655 exploration and 7,595 holdout rows.

The preview exclusion has a visible cost: all five Type 1 seed groups for code `D001` were in the conservatively quarantined first 100 rows, so the holdout has **no Type 1 `D001` cases**. It still contains `D001` in other case types. Report this coverage exception; do not claim diagnosis-by-type completeness or quietly move an exposed group into holdout.

The local, Git-ignored manifests are `data/processed/mentalbench_group_split_v1.csv` (one row per seed group) and `data/processed/mentalbench_row_split_v1.csv` (one row per source CSV row), with aggregate summary `data/processed/mentalbench_split_summary_v1.json`. They contain no case text, option text, or answer text. Manifest SHA-256 values are recorded in the summary. Rerunning the script checks for byte-identical output and fails if an existing version-1 artifact would change. The source CSV is unchanged. The split is fixed before any Jev benchmark calls or exploration of held-out text.

This would protect against shared seed/profile/generator leakage. It cannot exclude common DSM criteria or the shared knowledge graph across development and holdout, nor can it prove what Jev encountered before this project. These are generalization limits to disclose.

## Remaining research checks before benchmark calls

1. If a public feature artifact or author clarification reveals a different seed mapping, update the reconstructed key and regenerate the split. The current five-ID key has passed the internal structural checks above.
2. Verify the mapping from 23 diagnosis codes to displayed DSM diagnoses and how each `code` pair relates to its answer key, without exposing holdout case text.
3. Confirm the option/answer parser against the authors' evaluation code. The split manifest now exists; downstream readers must honor it and keep holdout text out of notebooks, chat, and diagnostic logs during development.
