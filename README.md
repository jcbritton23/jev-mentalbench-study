# Jev on MentalBench

A small independent evaluation of TypeSafe's Jev classifier on MentalBench, a benchmark of synthetic mental-health case descriptions. The repository contains the protocol, prompts, analysis code, split manifests, and human-readable reports. The complete machine-readable result bundle is linked below. The MentalBench dataset itself is not included.

## Main result

The frozen holdout contained 22,785 cases from 673 reconstructed source groups, or 92.06% of the 24,750-case dataset. The development/exploration partition contained 1,965 cases from 107 groups, or 7.94%. Related variants were assigned together by reconstructed source group. The split is documented in [the audit](docs/AUDIT.md) and [the manifests](data/processed/).

The primary four-option, paper-style exact-match score was **62.8%** on the holdout, with a reconstructed-family bootstrap 95% interval of **61.4%–64.2%**. The primary rule takes Jev's top diagnosis for Types 1 and 2, and the exact set of offered diagnoses scoring at least 0.50 for Types 3 and 4. A prespecified 0.40 Type 3 sensitivity result is reported separately. These are benchmark-label results on synthetic cases, not clinical diagnostic accuracy.

Jev 1.13.0 completed 45,570 successful requests across the two holdout arms. Estimated input-token cost was **$15.4127**, and recorded active run time was **70.6 minutes** using three concurrent workers. Median per-request latency was 0.319 seconds for the all-23 arm and 0.222 seconds for the four-option arm. Account billing may differ from the token-based estimate.

| Case type | Holdout cases | All-23 top diagnosis hit | Four-option top diagnosis hit | Four-option exact-set score at 0.50 |
| --- | ---: | ---: | ---: | ---: |
| Type 1 | 990 | 91.9% | 94.6% | 89.0% |
| Type 2 | 2,760 | 74.1% | 88.9% | 71.2% |
| Type 3 | 6,345 | 74.9% | 95.5% | 32.4% |
| Type 4 | 12,690 | 77.5% | 88.0% | 66.9% |

The full curves, case-level probability outputs, cost/latency records, paired analyses, calibration measures, and family-bootstrap details are in the [complete results bundle](https://github.com/jcbritton23/jev-mentalbench-study/releases/latest/download/mentalbench-results-bundle.zip). The separate reports are available for [exploration](results/exploration_v1_full/report.md) and [holdout](results/holdout_v1_1_full/report.md).

## Study design

Each case was evaluated in two paired conditions. The all-23 condition offered all diagnoses without showing the case's supplied options. The four-option condition offered only the four diagnoses supplied for that case. The same frozen DSM-informed guides and question meaning were used in both conditions. The paper-style weighted score uses the benchmark's Type 1–4 case-count weights; it is a score on this grouped held-out subset, not a direct head-to-head rerun of the paper's models.

The holdout split was frozen before its Jev calls. The dataset does not provide explicit seed IDs, so source groups were reconstructed from the documented five-profile generation structure and checked against repeated option sets and cross-type variants. This grouping is an evidence-supported reconstruction, not a source-provided identifier. Seven previously preview-exposed groups were kept in exploration. Consequently, the holdout has no Type 1 cases for diagnosis code D001, although all 23 diagnoses occur in the holdout overall.

## What's here

- `PROTOCOL.md` records the study questions, development decisions, frozen analysis plan, and interpretation limits.
- `prompts/` contains the diagnosis guides, question wording, development notes, and the pre-run v1.1 freeze record.
- `scripts/` contains the audit, split, API runners, scorers, and tests.
- `data/processed/` contains the group split assignment and aggregate counts. The complete bundle also contains the row-level split manifest. These contain identifiers and split labels only, not case text, options, or answers.
- `docs/AUDIT.md` records dataset structure, related-case reconstruction, exclusion rules, and license information.
- `results/` contains the concise reports and run summaries. The linked ZIP release asset contains the full case-level response journals and machine-readable metrics.

The result journals contain anonymous row/group identifiers, benchmark codes, Jev probabilities, usage, status, and latency. They do not contain the synthetic case descriptions or raw provider payloads. No raw dataset, API key, `.env` file, EmpatheticDialogues data, or participant-level data is included.

## Data and references

MentalBench is hosted at [Hugging Face](https://huggingface.co/datasets/hysong/MentalBench). Its repository declares the dataset under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The source provides one `train` split and no development/holdout partition; this project created and documents its own grouped split. Download the dataset from its source and review the source terms before reuse. The dataset is linked, not redistributed here.

The benchmark task and published comparison are described in the [MentalBench paper](https://arxiv.org/html/2602.12871). Jev API behavior and pricing used for the run are documented by [TypeSafe](https://api.typesafe.ai/docs).

## Reproducing the analysis

Python 3.10 or newer is required. Install dependencies with `python -m pip install -e .`. Download the MentalBench CSV separately into `data/raw/mentalbench.csv`; it is intentionally ignored by Git. The metadata audit and split checks do not call Jev. Re-running either API runner with its explicit `--run` flag makes paid requests, so review the frozen protocol and cost first.

The scripts expect `TYPESAFE_API_KEY` in the environment or a local, ignored `.env` file. Never commit or paste an API key into source or output.

## Interpretation

This is a synthetic benchmark evaluation. It does not establish clinical diagnostic accuracy, clinical utility, or performance on real patient records. The four-option labels do not adjudicate diagnoses outside those supplied options in the all-23 condition. Type 3 results are especially sensitive to whether both keyed labels are recovered. The bootstrap interval reflects sampling uncertainty under the reconstructed family grouping; it does not resolve label ambiguity or establish clinical validity.

The repository does not assign an open-source license to the project code. The dataset's stated CC BY 4.0 license applies to the upstream dataset, not automatically to this repository's code or result files.
