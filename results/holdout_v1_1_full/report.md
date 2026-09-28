# MentalBench frozen holdout results

Jev jev-1.13.0 scored 22,785 synthetic cases from 673 reconstructed source groups in both all-23 and four-option conditions. This is benchmark performance, not clinical diagnostic accuracy.

## Primary paper-style result

The prespecified four-option rule takes Jev's top diagnosis for Types 1–2 and the exact set of diagnoses at or above 0.50 for Types 3–4. With the paper's full-dataset case-type weights, the holdout estimate is **62.8%** (family-bootstrap 95% interval **61.4%–64.2%**). The raw holdout agreement is **13,937/22,785 = 61.2%**. Weighting adjusts for the holdout's different type mix; it does not turn this subset into a direct paired rerun of published LLMs.

| Type | Cases | All 23 top key hit | Four top key hit | Four exact offered set at primary cutoff |
| --- | ---: | ---: | ---: | ---: |
| type1 | 990 | 91.9% | 94.6% | 89.0% |
| type2 | 2,760 | 74.1% | 88.9% | 71.2% |
| type3 | 6,345 | 74.9% | 95.5% | 32.4% |
| type4 | 12,690 | 77.5% | 88.0% | 66.9% |

## Differentials and uncertainty

At the primary 0.50 cutoff, the four-option Type 3 exact-set rate is 32.4%; the family-bootstrap interval is 29.4%–35.3%. At the prespecified 0.40 sensitivity cutoff, Type 3 exact-set agreement is 40.2%. The machine-readable metrics include the complete cutoff curve, Type 3 pair recovery, offered-label calibration and Brier scores, and paired top-answer results.

Diagnoses outside a case's four supplied options are unadjudicated by the benchmark. The all-23 set measures must be read as benchmark proxies over the offered labels, not proof that extra diagnoses are clinically wrong.

## Cost and latency

| Arm | Requests | Input tokens | Estimated cost | Median latency | 90th percentile | Retries |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all23 | 22,785 | 302,327,118 | $12.6977 | 0.319s | 0.363s | 0 |
| four | 22,785 | 64,641,543 | $2.7149 | 0.222s | 0.262s | 0 |

Successful calls cost an estimated **$15.4127** at the frozen input-token rate. The conservative upper bound, including possibly billed failed attempts, is **$15.4127**. Recorded active run time is **70.6 minutes** with three workers; paired cases completed per minute were **322.9**. Verify the account charge separately. There were **0** recorded failed request events.

The 95% intervals resample reconstructed source groups within Type 1, Type 2, and linked Type 3/4 strata. They quantify this split's sampling uncertainty under that grouping assumption; they do not address possible label ambiguity or prove clinical validity.
