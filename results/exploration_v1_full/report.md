# MentalBench v1 full exploration results

This is the frozen **exploration** partition: 1,965 synthetic cases in 107 reconstructed source groups. The 22,785-case holdout has not been scored. Each case received one all-23 and one four-option Jev request. The question version and clinical guides were fixed for this run. All measures below concern benchmark labels, not clinical diagnostic accuracy.

## Required top diagnosis

| Case type | Cases | All 23: top diagnosis in key | Four options: top diagnosis in key |
| --- | ---: | ---: | ---: |
| all | 1965 | 83.3% | 94.2% |
| type1 | 735 | 95.5% | 97.3% |
| type2 | 690 | 74.6% | 89.7% |
| type3 | 180 | 65.6% | 96.7% |
| type4 | 360 | 83.9% | 95.6% |

For Type 3, a top diagnosis counts as a hit when it matches either of the two keyed labels; it does not demonstrate that both were retained. An all-23 label outside the supplied choices led in 228 of 1,965 cases; those are unadjudicated disagreements.

## Differential: all diagnoses at or above each cutoff

Exact set and precision below are scored **within the four supplied options**. The all-23 run may also list diagnoses outside those options; the benchmark does not label those as negatives.

| Arm | Cutoff | All types: exact offered set | Type 3: both keyed included | Type 3: exact offered set | Mean full set size |
| --- | ---: | ---: | ---: | ---: | ---: |
| all23 | 0.50 | 75.6% | 42.2% | 38.3% | 1.68 |
| all23 | 0.70 | 77.9% | 3.9% | 3.9% | 1.18 |
| all23 | 0.80 | 71.9% | 0.0% | 0.0% | 0.90 |
| all23 | 0.90 | 50.4% | 0.0% | 0.0% | 0.54 |
| four | 0.50 | 77.1% | 39.4% | 36.1% | 1.20 |
| four | 0.70 | 82.1% | 8.3% | 8.3% | 0.99 |
| four | 0.80 | 77.2% | 0.0% | 0.0% | 0.86 |
| four | 0.90 | 56.9% | 0.0% | 0.0% | 0.59 |

## Exploratory lower cutoff review

These additional cutoffs were examined only after the exploration scores were saved. They are candidates for a decision rule to freeze before holdout.

| Arm | Cutoff | Type 3: both keyed included | Type 3: exact offered set | Type 4: exact offered set | Overall exact offered set | Mean full set size |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all23 | 0.20 | 77.8% | 41.1% | 28.3% | 45.0% | 3.45 |
| all23 | 0.30 | 62.2% | 44.4% | 52.2% | 61.4% | 2.40 |
| all23 | 0.40 | 57.8% | 48.9% | 62.2% | 69.9% | 1.95 |
| all23 | 0.50 | 42.2% | 38.3% | 74.4% | 75.6% | 1.68 |
| all23 | 0.60 | 22.2% | 21.1% | 84.2% | 78.3% | 1.43 |
| all23 | 0.70 | 3.9% | 3.9% | 85.0% | 77.9% | 1.18 |
| four | 0.20 | 75.0% | 42.8% | 32.8% | 50.4% | 1.72 |
| four | 0.30 | 62.8% | 44.4% | 55.0% | 64.8% | 1.45 |
| four | 0.40 | 52.2% | 41.1% | 69.4% | 72.3% | 1.31 |
| four | 0.50 | 39.4% | 36.1% | 79.7% | 77.1% | 1.20 |
| four | 0.60 | 20.6% | 18.9% | 86.7% | 80.7% | 1.10 |
| four | 0.70 | 8.3% | 8.3% | 88.6% | 82.1% | 0.99 |

## Paper-style four-option exact-match estimate

The paper asks for one answer on Types 1 and 2, and an exact answer set on Types 3 and 4. This development estimate therefore uses Jev's top diagnosis for Types 1/2 and the thresholded four-option set for Types 3/4, then applies the paper's type weights (1,725 / 3,450 / 6,525 / 13,050 cases). It remains a development estimate from only 107 source groups.

| Cutoff for Type 3/4 sets | Type 3 exact set | Type 4 exact set | Weighted overall exact match |
| ---: | ---: | ---: | ---: |
| 0.05 | 9.4% | 0.0% | 21.8% |
| 0.10 | 31.7% | 5.3% | 30.4% |
| 0.15 | 38.3% | 17.8% | 38.8% |
| 0.20 | 42.8% | 32.8% | 47.8% |
| 0.25 | 46.7% | 46.4% | 56.0% |
| 0.30 | 44.4% | 55.0% | 60.0% |
| 0.35 | 43.9% | 61.7% | 63.4% |
| 0.40 | 41.1% | 69.4% | 66.7% |
| 0.45 | 39.4% | 74.7% | 69.1% |
| 0.50 | 36.1% | 79.7% | 70.8% |
| 0.55 | 27.8% | 83.3% | 70.5% |
| 0.60 | 18.9% | 86.7% | 70.0% |
| 0.65 | 15.6% | 88.1% | 69.8% |
| 0.70 | 8.3% | 88.6% | 68.2% |
| 0.75 | 1.7% | 85.6% | 64.8% |
| 0.80 | 0.0% | 77.5% | 60.1% |
| 0.85 | 0.0% | 63.9% | 53.0% |
| 0.90 | 0.0% | 45.0% | 43.0% |
| 0.95 | 0.0% | 14.2% | 26.8% |

On the actual exploration split, the same paper-shaped scoring rule gives 1,686/1,965 = 85.8% at 0.50. This raw split rate is not representative of the paper's case mix because exploration contains relatively more Type 1/2 rows; the paper-weighted estimate above is the appropriate summary for comparison, and both remain development results.

For Type 3, the paper reports exact-set accuracy of 9.01% for GPT-5-mini, 22.48% for GPT-5.1, 14.99% for Claude Sonnet 4.5, 40.25% for GPT-4o, and 54.19% for Qwen 3 235B. Jev's four-option exploration exact-set rates are 41.1% at 0.40 and 36.1% at 0.50. These are not head-to-head results: Jev's figures cover 180 related exploration variants from 12 Type 3 source groups, whereas the paper reports the full benchmark. [MentalBench paper](https://arxiv.org/html/2602.12871).

## Type 3 pair coverage at the exploratory 0.40 cutoff

Each diagnosis pair contributes one reconstructed source group and 15 related narrative cases. Counts below show cases where both benchmark keys cleared 0.40; the group is the independent unit.

| Diagnosis pair | All 23: both keys / 15 | Four options: both keys / 15 |
| --- | ---: | ---: |
| D001_D013 | 12/15 | 11/15 |
| D002_D011 | 12/15 | 11/15 |
| D003_D008 | 6/15 | 4/15 |
| D004_D015 | 12/15 | 11/15 |
| D005_D018 | 7/15 | 6/15 |
| D006_D010 | 15/15 | 14/15 |
| D007_D015 | 11/15 | 10/15 |
| D012_D016 | 0/15 | 0/15 |
| D014_D009 | 13/15 | 13/15 |
| D017_D021 | 2/15 | 1/15 |
| D019_D020 | 4/15 | 5/15 |
| D023_D022 | 10/15 | 8/15 |

## Cost and timing

| Arm | Requests | Input tokens | Cost | Median request | 90th percentile request | Retries |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all23 | 1,965 | 25,611,391 | $1.0757 | 0.317s | 0.355s | 0 |
| four | 1,965 | 5,517,766 | $0.2317 | 0.218s | 0.255s | 0 |

Total exploration API cost: **$1.3074**. Run wall time: **6.0 minutes** with three concurrent workers. The input-token cost is calculated from TypeSafe's documented Jev 1.13 rate; output tokens are free. The actual account charge should be checked independently.

## Limits and next decision

This exploration set contains related narrative variants; the 107 source groups are the relevant independent units. The results can guide a cutoff choice but are development estimates. The four supplied options adjudicate only those four labels. After choosing and recording a cutoff, the protected holdout can provide an independent assessment. MentalBench has no cases whose correct answer is 'no diagnosis.'
