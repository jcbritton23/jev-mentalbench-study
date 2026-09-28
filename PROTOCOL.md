# Jev psychology project — working hypothesis and method

Status: **v1.1 method frozen; holdout evaluation complete** (2026-09-27). This records the approach John and Codex developed together. The exploration/holdout assignments are fixed. The v1 prompt and guides were held fixed for the full exploration run. The primary cutoff is 0.50, and v1.1 expands the D012/D016 entries. The [holdout freeze](prompts/mentalbench_holdout_freeze_v1_1.md) pins the exact request and analysis files; its pre-run status is intentionally preserved as a historical freeze record.

## Why do this?

The end product should be credible resume/portfolio evidence that John can bring psychological judgment and technical thinking to a new kind of AI model. MentalBench provides a large, interesting demonstration: can Jev make useful *fuzzy, probabilistic distinctions* among 23 diagnoses from synthetic case descriptions? A secondary story is that an independent researcher can now try substantial classification experiments at low cost. We hope for strong accuracy, but it is **desired, not required** for an honest and worthwhile project. Results will be reported as benchmark performance on synthetic cases, never clinical diagnostic accuracy.

## Working questions and hypotheses

1. **Test 1 — all 23:** Given only a synthetic case description and a DSM-based diagnostic checklist, how well does Jev rank the benchmark-keyed diagnosis or diagnoses among all 23 available diagnoses? The case's four supplied options are hidden. Hypothesis: Jev will meaningfully discriminate among all 23; the size of that effect is exploratory because the published benchmark did not test this harder framing.
2. **Test 2 — four options:** On those same cases, how does Jev do when **only that case's four supplied diagnoses** are available as choices? Hypothesis: on single-answer cases, top-ranked keyed-answer recovery will be higher than in Test 1, because the candidate set is smaller. A stretch hypothesis is that Jev will meet or exceed the paper's best published overall four-option exact-match result (62.69%, Claude Sonnet-4.5); the comparison must match the paper's scoring and case-type mix, and a different held-out subset is not a direct head-to-head replication. This is the only second classification test—there are **not two separate all-23 tests**.
3. **Feasibility:** What do the calls actually cost, how long do they take, and how much setup is needed? Aim to keep total Jev API spend below **$20**. This may become part of the public story only if measured results support it.

**Cost hypothesis, not yet quantified:** Jev may deliver a useful accuracy–cost tradeoff versus the published LLMs. Do not preclaim one-tenth or one-hundredth of their cost: the paper reports accuracy, while a fair price ratio needs comparable per-case token usage, contemporary model prices, and the same evaluation scope. Measure Jev's actual billed tokens and latency first, then calculate and label any defensible cost comparison.

EmpatheticDialogues is a separate, deferred project, not part of this MentalBench experiment or its $20 Jev budget. Its emotion label describes the speaker's situation, not turn-level empathy or a clinical diagnosis.

## Broad method we are converging on

- First audit MentalBench's labels and relationships among generated variants. Related versions of a case must stay together. Inspect counts by diagnosis before choosing a development subset.
- Use the **frozen exploration partition** to refine the checklist and Jev instructions, then freeze them before holdout testing. The [metadata audit and split record](data/AUDIT.md) found 780 reconstructed source-seed groups of 15 or 45 rows; the five-ID grouping passed whole-dataset option-set checks, although the CSV lacks an explicit seed field. The earlier 300-family / 900-row estimate is withdrawn. Version 1 assigns **107 groups / 1,965 rows (7.94%)** to exploration and **673 groups / 22,785 rows (92.06%)** to holdout. Exploration has 5–8 seed groups per diagnosis and all four case types. Seven previously previewed groups are all in exploration. The resulting holdout has no Type 1 cases for `D001`, though all 23 diagnoses occur in the holdout overall; disclose this limit. Prompt iteration began with bounded examples; the full exploration partition has now been run to characterize performance and select a cutoff before holdout. The 107 reconstructed groups, rather than all 1,965 related rows, are the independent development units.
- Use DSM diagnostic criteria as the default basis for a **clinically useful diagnostic guide**, unless the dataset audit gives us a reason to reconsider. The [draft 0 question and 23-label inventory](prompts/mentalbench_v0.md) records the proposed form. For each diagnosis, write a readable paraphrase of its defining pattern, important duration/impairment conditions, and features that distinguish it from close alternatives; include exclusions or red flags where they materially change the judgment. Give Jev enough information to reason about a realistic vignette, without copying a long DSM checklist or optimizing for the shortest possible prompt. The guide supports a fuzzy judgment; it is not a rigid rule engine.
- Use the paper's published task definition to decide what our question means before testing. Build the checklist from DSM-based criteria and clinical judgment rather than copying the benchmark's generated case features, answer logic, or held-out examples into Jev's instructions. Record the checklist source and any overlap with the authors' knowledge graph.
- Run exactly two classification tests on the frozen holdout: first all 23 diagnoses available with the case's four options hidden; second only that case's four options available. Keep the case set aligned for comparison. **Recommended implementation:** ask one Jev yes/no probability question per available diagnosis, batching the 23 or four questions for a case into one request. This permits the benchmark's ambiguous, multi-answer cases; a single forced-choice question would not. Use the same DSM-based diagnosis descriptions and underlying question meaning in both tests, changing only which candidates Jev sees. Validate this simple design on development cases before freezing it.
- Compare ranked outputs with benchmark answers and look carefully at cases where Jev favors a diagnosis outside the supplied four. Those are disagreements to inspect, not automatically obvious clinical errors. Report the synthetic benchmark's limits and avoid claims about real-patient diagnosis.
- Track model version, requests, tokens, cost, errors, and latency from the first pilot. Estimate the full run before authorizing it; if necessary, use a prespecified smaller holdout sample to stay under budget. **Do not run all 24,750 cases yet.**

**Timing for shareable results:** For each request, save arm (23 or four),
anonymous case/family/type identifiers, start/end timestamps, wall-clock
elapsed seconds, API-reported usage/cost, status, and retry count. Count a
retried case's total elapsed time from first attempt to final response, while
also retaining each attempt's duration; do not quietly exclude failures.
For each arm and case type, report median and 90th-percentile request latency,
mean latency, total requests/retries, and completed cases per minute. Also
report the actual wall-clock duration of the full run and the concurrency
setting, because per-request latency and total runtime are different claims.
Record a local monotonic timer; use server timing separately only if the API
actually supplies it. Report cost and tokens alongside timing. These measures
are part of the frozen analysis plan, not just debugging logs.

**First all-23 exploration pilot (draft 0, 2026-09-27):** Three independent
exploration cases were sent, one each from Types 1, 2, and 3. Each request
batched 23 Noul questions; no supplied options, answer keys, or case text were
written to the result artifact. Jev 1.13.0 returned a top-ranked keyed
diagnosis for 2/3 cases. On Type 3, both keyed diagnoses appeared in Jev's top
three with probabilities 0.53 and 0.50, while D005 ranked first at 0.81; this
is an outside-choice disagreement to inspect, not automatically a clinical
error. Total usage was 38,559 input tokens and 1,323 output tokens, estimated
cost **$0.001619478**, with request latencies 0.3925 s, 0.4654 s, and 0.2191 s
(1.077 s summed request time; no failed requests). The local ignored artifact
[`first_draft_23way_3case_v0.json`](results/first_draft_23way_3case_v0.json)
contains the three complete 23-score distributions and metadata, but no input
text. A mechanical extrapolation of this one arm to 24,750 cases at the
observed mean 12,853 input tokens/request is about **$13.39**; applying that
mean to the actual 22,785-case holdout is about **$12.30**. Actual case length,
usage, retries, and the four-option arm still need measurement, so this does
not yet establish that both full arms fit the $20 target.

**Type 3 follow-up (same draft 0):** Two further all-23 requests from distinct
exploration seed groups targeted D007/D015 and D004/D015. D015 led the first
at 0.77, with D007 at 0.47. In the second, plain D013 led at 0.83 while the
two keyed psychotic diagnoses scored 0.39 and 0.33. These two calls used
25,700 input tokens, cost an estimated **$0.0010794**, and took 0.4172 s and
0.2070 s. The [Type 3 differential review](prompts/type3_differential_review_v0.md)
records the case-level interpretation and a **candidate** question revision;
the first-draft guide and question remain unchanged.
Across the five all-23 pilot calls, mean input use was 12,851.8 tokens per
request. At the current TypeSafe input price, a 22,785-case all-23 holdout
would cost about $12.30. The four-option holdout would need to average below
roughly 8,000 input tokens/request to keep these two holdout arms under $20,
before retries and development spend. Measure it directly before committing
to the full run. This estimate does not require a $40–$50 project budget.

**Fresh paired Type 3 wording check (v0 versus v1):** Three further Type 3
exploration cases from distinct, previously untested source groups were each
sent once with the unchanged v0 question and once with a v1 question that
keeps unresolved alternatives plausible and clarifies the plain mood-label
convention. The guides and all-23 candidate state were identical. V1 raised
all six keyed probabilities slightly; at a 0.50 cutoff it recovered both
keyed diagnoses in one of the three cases versus zero for v0. It did not
change any top all-23 label or keyed rank. One case gained one additional
all-23 label above 0.50. This small, selected development comparison does
not establish superiority. The [Type 3 review](prompts/type3_differential_review_v0.md)
and ignored [paired result](results/type3_v0_v1_fresh_3case.json) have the
scores and timing. Six calls cost an estimated **$0.003255042** total.
No holdout row was read or sent.

**Paired four-option Type 3 pilot (v0):** The same three Type 3 rows were then
run with only their four supplied diagnoses and guides in state. Question
wording stayed at v0. The four-option top diagnosis matched a keyed diagnosis
in 3/3 cases, compared with 1/3 in the paired all-23 results; however, at the
0.50 differential threshold, all three four-option runs retained only one of
the two keyed diagnoses. The two keyed probabilities moved only slightly in
most cases, while rank improved when an outside diagnosis had led all-23.
This is descriptive pilot evidence, not a stable estimate of gain. The
requests used 9,645 input tokens, cost **$0.00040509**, and took 0.2196,
0.1829, and 0.1447 seconds. See the detailed
[Type 3 review](prompts/type3_differential_review_v0.md) and ignored
[four-option result](results/type3_four_option_same_cases_v0.json). No holdout
data were used.

**Second paired Type 3 wording batch (v0 versus v1):** Two new diagnosis-pair
groups (D012/D016 and D014/D009) were each run once per wording version with
all 23 diagnoses available. V1 again used the revised independent-inclusion
wording; the structured diagnosis guides were identical across versions.
For D012/D016 the keyed scores were 0.95/0.08 (v0) and 0.95/0.09 (v1), with
the same ranks (1 and 3). For D014/D009 they were 0.76/0.54 (v0) and
0.77/0.52 (v1), again with the same ranks (1 and 3). At the four-option
0.50 threshold, both keyed labels were included for D014/D009, while only
D012 was included for D012/D016; the same was true for both wording versions.
At 0.70 only the higher-scoring key was included in either case; at 0.80 and
0.90, neither pair was fully recovered. The all-23 thresholded set sizes at
0.50/0.70/0.80/0.90 were 1/1/1/1 for D012/D016 under both versions, and
3/1/0/0 (v0) versus 3/2/0/0 (v1) for D014/D009. Unoffered diagnoses in these
sets are unadjudicated. This second small batch shows little change from v1.
Four requests used 51,848 input tokens, cost **$0.002177616**,
and took 0.3747, 0.2330, 0.2397, and 0.2753 seconds. See the ignored
[second-batch result](results/type3_v0_v1_second_batch_2case.json). No holdout
case was read or sent.

The current v1 wording is preserved as an
[exploration prompt candidate](prompts/mentalbench_v1_question_candidate.md).
It has not replaced v0 in the original pilot runner, and the guide entries are
still draft material; wording and guides need to be reviewed and frozen before
held-out evaluation.

Across the five paired Type 3 cases tested so far, the 0.50 offered-option
cutoff included both keyed diagnoses in 2/5 cases under v1 and 1/5 under v0.
Top-ranked diagnosis matched one of the two keys in 3/5 cases under each
version. These exploratory numbers are too small to establish a prompt effect.

**Full v1 exploration run (both arms, 2026-09-27):** All **1,965 exploration
cases** from 107 reconstructed source groups were scored in both arms, for
3,930 successful requests. The v1 question builder, diagnosis guides, model,
source CSV, and split manifest were pinned by hash in the ignored run manifest.
The all-23 API state omitted the supplied choices and answer. The four-option
state included only the four offered diagnoses and their guides, adding the
shared ADHD reference only when an ADHD diagnosis was among those four; the
answer remained local. No holdout case was sent. The [local exploration report](results/exploration_v1_full/report.md)
and [machine-readable metrics](results/exploration_v1_full/metrics.json) contain
the full analysis; neither contains case text. The required top-ranked answer
matched a benchmark key in **83.3%** of all-23 runs and **94.2%** of four-option
runs. On Type 3, these top-one hit rates were **65.6%** and **96.7%**, but
top-one success only requires matching *one* of the two keyed diagnoses.
At a 0.50 differential cutoff, both Type 3 keys were retained in **76/180
(42.2%)** all-23 runs and **71/180 (39.4%)** four-option runs. The 180 Type 3
rows come from only 12 reconstructed source groups. The four-option condition
therefore improved the forced top answer far more than it improved recovery of
both alternatives. The run used 31,129,157 input tokens, cost an estimated
**$1.3074**, and took **361.1 seconds** wall time with three concurrent
workers; there were no failed requests or retries. Median request latency was
0.317 s for all-23 and 0.218 s for four-option. A type-stratified extrapolation
from these development costs projects about **$15.26** for both arms over the
22,785-case holdout, leaving budget room under $20 but not guaranteeing the
actual charge. Keep the holdout sealed until the prompt and cutoff are frozen.

**Cutoff decision from exploration:** We select **0.50** as the primary
paper-style operating cutoff because it produced the strongest paper-weighted
exact-match estimate among cutoffs on the 0.05 grid. We will still report the
full curve and highlight **0.40** as a more inclusive secondary Type 3 point.
At 0.40, both Type 3 keys were
retained in **57.8%** (all-23) and **52.2%** (four-option) of cases, while
four-option Type 4 exact-set agreement was **69.4%**. At 0.50, Type 3 pair
recovery fell to **42.2% / 39.4%**, while Type 4 four-option exact-set
agreement rose to **79.7%**. For the paper-style weighted exact-match score,
Types 1 and 2 use the required top answer, while Types 3 and 4 use an exact
four-option answer set at the selected cutoff. With the paper's case-type
weights, the exploration estimate is **66.7% at 0.40** versus **70.8% at
0.50**. Thus 0.40 improves Type 3 pair recovery; it does not increase the
paper-style overall exact-match estimate. Type 4 matters to that metric
because the paper expects its discriminating evidence to narrow the answer
set to one diagnosis, and Type 4 carries 52.7% of the headline weight. The
full curve should be reported, with the selected 0.50 cutoff frozen before
holdout.

**Type 3 comparison to published models:** Compare only four-option exact-set
accuracy for Jev and the paper's Type 3 scores. The paper reports a wide range,
including 9.01% (GPT-5-mini), 14.99% (Claude Sonnet 4.5), 22.48% (GPT-5.1),
40.25% (GPT-4o), and 54.19% (Qwen 3 235B). Jev's exploration results are
41.1% at a 0.40 cutoff and 36.1% at 0.50, but these 180 cases come from only
12 source groups and are not directly comparable to the paper's full-set
results. Use the same exact-set metric on the protected holdout and describe
the paper as a reference, not a paired head-to-head trial.

**Other exploration error clusters to review cautiously:** In the four-option
arm, top-one benchmark-key hit rate was 89.7% for Type 2 versus 97.3% for
Type 1; the all-23 Type 2 rate was 74.6%. Within the four-option Type 2 rows,
some weaker target labels were schizoaffective bipolar type (8/30),
schizoaffective depressive type (11/30), and hyperactive/impulsive ADHD
(15/30). Adjustment disorder was also weak in Type 4: top-one recovery was
6/15 in both arms, while exact-set agreement still depended on the cutoff.
These counts are rows from very few source
groups, not independent case counts. The current guides already state the
relevant timing, episode, and presentation distinctions. Do not expand them
to fit these slices without auditing development examples. Apart from an
explicit phobia/OCD contrast across D012 and D016, no general criteria rewrite
is justified by this exploratory evidence.

**Targeted Type 3 development audit:** Two variants from weak diagnosis-pair
groups were inspected after the full run, without changing the v1 prompt.
Their secondary benchmark labels (OCD in one phobia case, anorexia nervosa in
one body-dysmorphic case) were not clearly supported by the visible syndrome
features. This is a limited, non-clinician inference, not a relabeling of the
benchmark or a judgment on every related variant. The [audit note](prompts/type3_development_audit_v1.md)
records the evidence and clinical sources. We should not tune the guide or
cutoff solely to force a high score for an under-supported second label.

**Targeted guide and recurring-error audit (2026-09-27):** The expanded
Specific Phobia/OCD guides were checked on three hash-selected four-option
exploration variants (one Type 3, one Type 4 keyed D012, one Type 4 keyed
D016), all from one source group. Scores barely changed from baseline and
the .50 exact-set outcomes were unchanged; this is not evidence of a general
prompt effect. Three other exploration-only Type 2 misses (D003, D006, D007)
were inspected qualitatively. The ADHD case gives meaningful evidence for
both current symptom domains, making D001 combined a plausible competing
label. Two schizoaffective misses leave psychosis/mood chronology unclear;
the current guide already includes the key distinctions. No additional guide
rewrite is supported by these small audits. See the full
[targeted development audit](prompts/targeted_development_audit_v1_1.md) and
the ignored [phobia/OCD check results](results/phobia_ocd_guide_v1_1_exploration_check.json).

## Outputs, measures, and cutoff rule

Keep **all raw Jev scores** for all 23 candidates in Test 1 and all four in Test 2. One score can be highest while several diagnoses remain plausible. This is central to the study, not an incidental byproduct.

- **Required single answer:** always return the highest-scored diagnosis, even when its probability is low. This makes the single-answer decision explicit instead of converting a low score into abstention. Types 1, 2, and 4 have one keyed diagnosis, so measure whether the top-ranked diagnosis matches that label. For Type 3, count a top-ranked answer as a hit if it matches either of the two keyed diagnoses; this does not mean it recovered the full differential.
- **Differential set:** include every diagnosis at or above the inclusion cutoff. This set may contain one, several, or no diagnoses; an empty thresholded set does not erase the required top-ranked answer. Report results at cutoffs **0.50, 0.70, 0.80, and 0.90**, including per case whether the set contains **all**, **some**, or **none** of the keyed diagnoses, how many keyed diagnoses it recovered, how many additional diagnoses it listed, and set size. For Type 3, this directly measures whether Jev retained both keyed diagnoses. For the four-option arm, unkeyed offered diagnoses are benchmark negatives; for the all-23 arm, diagnoses outside the supplied options remain unadjudicated.
- **Four-option benchmark comparison:** within the four offered choices, report exact match of the differential set to the complete keyed set, by case type and overall, using the paper's scoring convention. Also compare top-ranked keyed-answer recovery between Tests 1 and 2 on paired single-answer cases. In Test 1, extra diagnoses outside the four are **not verified negatives**; its all-23 differential cannot be declared clinically wrong or right solely from the four-option answer key. Any strict 23-way set-match number must be explicitly labeled a benchmark proxy, not clinical accuracy.
- **Probability calibration:** 0.80 means an estimated **80% chance of yes to that particular diagnosis question**, not the 80th percentile of cases or an 80% chance of being the best of 23. Among supplied-option diagnosis–case pairs scored around 0.80, roughly 80% should be benchmark-positive *if* those probabilities are calibrated. Plot observed positive rates against score bands, including 0.75–0.85, with denominators. Do not claim 23-way calibration from a key that only adjudicates the supplied options.
- **Uncertainty and comparison:** retain results by case family and question type. Report per-diagnosis results and uncertainty using families, not near-duplicate rows, as the independent units. Only compare the published 62.69% figure using the same exact-match definition; disclose subset or prompt differences.

**Threshold approach, revised after discussion:** the primary answer is always the highest-scored diagnosis; there is no primary-answer abstention cutoff. The primary secondary-differential cutoff is **0.50**, selected from exploration to maximize the paper-style weighted exact-set estimate on the evaluated 0.05 grid. Use **0.40** as a secondary Type 3 sensitivity point, and report the full curve, including the illustrative 0.50/0.70/0.80/0.90 points with denominators. These are score cutoffs, not promises of corresponding accuracy. Do not choose the best-looking held-out cutoff and call it independently validated. Changes suggested by holdout findings become hypotheses for a future dataset or fresh validation.

The planned curves are:

1. **Primary calls: accuracy versus coverage.** As the minimum top score increases, show keyed-answer agreement among retained primary calls and the fraction of cases retained. Test whether higher scores actually identify more reliable calls; do not assume monotonic improvement.
2. **Differentials: recovery versus list size.** For all 23 candidates, show the proportion of keyed diagnoses recovered, the proportion of cases recovering the entire keyed set, and the size of the differential across inclusion thresholds. For the four offered candidates, additionally report precision–recall and average precision (a summary over thresholds), plus exact-set agreement. ROC AUC can supplement these when both positives and negatives are defined; it does not measure probability calibration. Do not assign negative labels to all unoffered diagnoses merely to calculate an all-23 AUC.
3. **Calibration: stated probability versus observed keyed inclusion.** Use the offered diagnosis–case pairs for which the answer key supplies a benchmark target. Report reliability plots, counts, and Brier score, separately for each test's scores on those offered diagnoses and by question type where sample sizes permit. This measures agreement with the benchmark's inclusion rule, not real-patient disease probability. Calibration of a top prediction is a separate selection-conditioned question from calibration of all diagnosis scores.

These analyses reuse saved scores and require no additional Jev calls. Higher probability scores predicting higher benchmark inclusion is a directional hypothesis; the extent of calibration, useful operating cutoffs, and the all-23 recovery/list-size tradeoff remain exploratory outcomes. Report all prespecified curves rather than selecting favorable ones after results.

## Whole-project method review

The study has a coherent scope: paired all-23 and four-option experiments, DSM criteria, a protected holdout, graded multi-diagnosis outputs, calibration, and measured cost/latency. The following issues deserve attention before implementation:

- **Define what a positive diagnosis score means.** The paper's Type 3 seeds omit discriminating evidence, leaving two diagnoses consistent with a case. This differs from demonstrating simultaneous comorbid diagnoses. Ask whether each diagnosis remains a plausible explanation given the *best available evidence* and the DSM-based criteria. Missing information should introduce uncertainty, while explicit contradictory evidence can rule a candidate down. Do not quietly substitute a demand for fully documented criteria. Verify that this wording aligns with the benchmark's inclusion rule on development cases. A primary call means the leading model hypothesis, not a proven principal diagnosis.
- **Handle base labels and psychotic-feature labels consistently.** When the case supports MDD without episode-linked psychosis, use the plain MDD benchmark label; when psychotic features occur with the depressive episode, favor MDD with Psychotic Features. Apply the parallel distinction to Bipolar I and Bipolar I with Psychotic Features, tying psychosis to a mood episode. Psychosis outside mood episodes raises schizoaffective or another psychotic differential. Missing timeline information creates uncertainty. The [D013 sample](prompts/d013_mdd_sample_v0.md) records this as a benchmark label convention, since psychotic features clinically specify a form of a mood disorder rather than an unrelated diagnosis.
- **Confirmed guide decisions (2026-09-27):** In bipolar I, psychotic features linked to either a manic or a major depressive episode support D010 rather than the plain D008 benchmark label. For ADHD, use a developmental history but score the *currently supported* presentation; presentations may change over time, and one reported domain does not justify inferring combined presentation. For schizoaffective disorder, retain both the psychosis-without-major-mood-episode interval and the majority-of-illness mood rule; missing chronology lowers certainty rather than being filled in. These decisions are recorded in the [complex guide draft](prompts/complex_diagnosis_guides_v0.md).
- **Tune guide detail for usefulness, not minimum length.** Start with enough DSM-based context to convey the syndrome and meaningful differential distinctions for all 23 labels. Use exploration cases to find omissions, excess detail, or confusing wording, then make at most the planned revisions before freezing. Record token cost and performance, but do not remove clinically important information solely to save tokens. The study can explore potential clinical utility while reporting measured performance only on synthetic benchmark cases.
- **Symptom-reference audit (2026-09-27):** The draft now lists all nine MDD symptom domains and both nine-item ADHD presentation domains, plus the formal thresholds. It also states the decisive domain/threshold structure for mania/hypomania, GAD, persistent depressive disorder, PTSD, acute stress disorder, and binge-eating disorder. These references support a syndrome judgment; they do not make Jev a reliable counter of listed items. TypeSafe explicitly warns that Jev 1.13 does not count reliably. In the 12-case development pilot, inspect whether the prompt handles clearly above-threshold, explicitly below-threshold, and selectively reported patterns. If literal feature counts become essential to a claim, use a separately validated extraction/scoring procedure rather than treating a Noul probability as proof of arithmetic compliance.
- **Request-size check:** The three current Markdown guide files, including commentary and source lists that will *not* be sent, total about 4,700 words / 36 kB. This is a rough source-size check, **not an API token count**. TypeSafe currently documents 64k input tokens per request and 32k for shared state plus the longest question. The final runner should serialize one case, the applicable guide entries, and 23 or four questions, then check the actual API-reported tokens on the first synthetic/development request. Feasibility under the token limit does not guarantee good accuracy: TypeSafe also warns that large irrelevant state can distract Jev. Keep the ADHD domain reference once in shared state, omit manuscript commentary and citations, and preserve all clinically relevant distinctions. Project the full-run cost from measured tokens before authorizing it.
- **Make the two input conditions real.** Batched Jev questions are evaluated independently. Merely dropping 19 questions may leave the four remaining answers unchanged. Put the applicable candidate list and its criteria explicitly in shared state, so each diagnosis judgment receives the intended 23- or four-candidate context. Then test on development cases whether changing the list actually changes scores, ranking, or selected differentials. This is an empirical question, not a promised improvement. Keep diagnosis wording and scoring meaning consistent. This remains exactly two experiments.
- **Audit independent groups before selecting sample size.** Keep descendants of the same seed together, including profile variants, narrative generators, and linked task versions where identifiable. Check label and question-type representation using metadata. Report independent-group counts alongside row counts. Public paper examples and previously previewed rows, plus identifiable relatives, belong outside holdout.
- **Keep comparison claims proportional to the design.** The all-23 extension has incomplete differential labels outside the four supplied candidates. The published LLM score is a historical reference with potentially different inputs and prompts; our DSM-supplied workflow could have an information advantage. It cannot by itself isolate a Jev-versus-LLM model effect. Include cheap uniform-random and development-frequency ranking baselines and disclose baseline prompts, case mix, and scoring differences. A direct LLM rerun is optional and requires a budget check.
- **Bound development and preserve the audit trail.** Recommend an initial checklist plus at most two substantive revisions, each logged with development performance and cost. Save the final criteria, model version, split identifiers, scoring code, and date before holdout. Use family-level uncertainty, show results by question type and diagnosis, and account for failed calls rather than silently dropping them. A short, timestamped methods snapshot is sufficient for this informal study; a formal preregistration is optional.

Sources reviewed for this revision: [MentalBench, sections 4.2 and 5](https://arxiv.org/html/2602.12871), [TypeSafe agent guidance](https://docs.typesafe.ai/llms.txt), [probability calibration](https://scikit-learn.org/stable/modules/calibration.html), and [precision–recall analysis](https://scikit-learn.org/stable/auto_examples/model_selection/plot_precision_recall.html).

## Information boundaries

Dataset files, if downloaded, belong in ignored `data/raw/`, not Git or chat. Local code can read them, but held-out case text, answer keys, and individual Jev responses should stay out of Codex's context while we develop the method. The all-23 API call must omit the supplied options and answer. The four-option call must omit the answer. Earlier exploration exposed a few MentalBench preview rows; their related families should not enter the final holdout. These controls reduce *project-level* leakage; they cannot establish whether Jev previously encountered benchmark material in training.

## Holdout preparation complete

The v1.1 wording, pinned Jev 1.13.0 model, primary 0.50 cutoff, secondary
Type 3 0.40 point, paper-style scoring rule, family-bootstrap method, split
hashes, and budget cap are recorded in the [holdout freeze](prompts/mentalbench_holdout_freeze_v1_1.md).
The [holdout runner](scripts/run_holdout_v1_1.py) was resumable and required
an explicit `--run` flag. Its pre-run metadata check covered 22,785 cases,
673 groups, and 45,570 requests. Five synthetic-only checks of the cap,
resume boundary, and group-bootstrap structure passed. The run is now
complete; see the [frozen holdout report](results/holdout_v1_1_full/report.md)
and the dated interpretation below. Published-model comparisons remain
references, not a paired head-to-head trial. A portfolio/resume summary
should be developed later in John's own voice.

## Completed holdout results and interpretation (2026-09-27)

The frozen Jev 1.13.0 run scored the same 22,785 synthetic cases in both
conditions: all 23 diagnoses available, and only each case's four supplied
diagnoses available. It made 45,570 successful requests across 673
reconstructed source groups, with no recorded failed request events or
retries. The complete aggregate report and machine-readable metrics are in
the ignored [holdout results directory](results/holdout_v1_1_full/); the
frozen prompt, script, and scoring artifacts remain unchanged.

**Four-option paper-style headline.** Following the paper's “one or more”
answer convention, the frozen rule uses the top-ranked diagnosis for Types 1
and 2 and all diagnoses scoring at least 0.50 for Types 3 and 4. Exact-set
agreement under the paper's full-dataset type weights is **62.8%** (family
bootstrap 95% interval **61.4%–64.2%**); unweighted agreement on this held-out
subset is **61.2% (13,937/22,785)**. This is a weighted estimate from our
grouped holdout, not a direct paired replication of the paper's evaluation.

| Case type | Holdout cases | Four-option top-key hit | Four-option exact-set at 0.50 |
| --- | ---: | ---: | ---: |
| Type 1 | 990 | 94.6% | 89.0% |
| Type 2 | 2,760 | 88.9% | 71.2% |
| Type 3 | 6,345 | 95.5% hit on either keyed diagnosis | 32.4% |
| Type 4 | 12,690 | 88.0% | 66.9% |

The pattern is informative: Types 1 and 2 show strong recovery of a single
benchmark label, especially Type 1. Type 3 shows Jev often ranks at least one
member of the intended pair highly, while recovering the *exact pair* is much
harder. At 0.50 it included both keyed diagnoses in about 35% of Type 3 cases
and produced the exact set in 32.4%; lowering the threshold to the
prespecified 0.40 sensitivity point raises Type 3 exact-set agreement to
40.2%. That is a real recall-versus-extra-diagnoses tradeoff, not a reason to
select a new headline cutoff after seeing holdout results. Type 4 is important
to the weighted score because it is over half of the benchmark; its 66.9%
exact-set result is useful context alongside Type 1/2 strength and Type 3
difficulty.

**All-23 condition.** Top-ranked benchmark-key recovery was 91.9%, 74.1%,
74.9%, and 77.5% for Types 1–4, respectively. A derived paper-weighted
all-23 proxy is **58.4%** when Types 1/2 use top-one recovery and Types 3/4
use the exact set among the benchmark's supplied labels at 0.50. This is not
the primary paper-style four-option comparison: the benchmark does not
adjudicate Jev's diagnoses outside each case's four options. Those additional
all-23 suggestions are unadjudicated, not automatically clinical errors.

The four-option condition had higher top-one recovery than all-23 by 13.5
percentage points overall (90.5% versus 77.0%). On paired cases, the
four-option top answer improved on 3,196 cases, was unchanged on 19,471, and
was worse on 118. This supports the practical observation that narrowing the
candidate set can materially change ranking; it does not establish that the
extra all-23 suggestions are wrong. A post-hoc “at least one answer”
sensitivity for Types 3/4 yields 63.1% weighted, but the frozen 62.8% rule
remains primary and the post-hoc version must stay labeled exploratory.

**How this relates to published LLMs.** The closest conceptual comparison is
with fast/no-reasoning model settings because Jev is a System One model and
does not generate a deliberative rationale. The MentalBench paper's reported
four-option top model was Claude Sonnet 4.5 at 62.69%; its Type 3 score was
14.99%. GPT-5.1 was 62.17% overall and 22.48% on Type 3; Gemini Pro was
59.65% overall and 35.16% on Type 3. Jev's 62.8% weighted estimate is
numerically close to the paper's best overall result, and Jev's Type 3 exact
set of 32.4% is higher than those Claude/GPT-5.1 figures but below Gemini
Pro's. These are contextual numerical comparisons only: our split, prompts,
DSM criteria supplied, protocol, and uncertainty differ, and no direct
paired significance claim is justified. The paper's released model code
explicitly sets no-reasoning for some providers/local models, but does not
specify a reasoning-effort setting for every GPT-series call; therefore do
not describe the entire paper comparison as uniformly “no reasoning.” See
the [paper](https://arxiv.org/html/2602.12871) and its
[released model code](https://github.com/HoyunS/MentalBench/blob/main/scripts/models.py).

This supports a useful *system-level* question: can clear DSM-based criteria,
candidate framing, and a typed probability interface let a fast classifier
express meaningful distinctions without a generated chain of thought? The
results are encouraging for structured classification, especially Types 1
and 2, and interesting for Type 3 differential recovery. They do **not** show
that Jev has the same internal reasoning as a thinking model, or that it is
ready to diagnose real patients. The study evaluates synthetic benchmark
vignettes, not real intake reports or clinical diagnostic accuracy. A
responsible future utility example would be candidate-diagnosis flagging or
discrepancy review for a clinician, with human judgment retained.

**Scale, speed, and cost.** The two holdout arms together used an estimated
**$15.4127** in input-token charges: $12.6977 for all-23 and $2.7149 for
four-option. Across 45,570 successful calls they used 366,968,661 input and
11,870,985 output tokens. With three workers, elapsed run time was **70.6
minutes** (322.9 paired cases/minute); per-call median latency was 0.319 s
all-23 and 0.222 s four-option. Adding the recorded $1.3074 exploration run
puts the known major-run estimate at about **$16.72**, within the intended $20
API budget before any separately recorded small pilot/smoke charges; verify
the actual account ledger before stating a final billed total. This is a
concrete scale/cost result, not a claim that the per-case rate applies to
every dataset or prompt.

**Probability and evaluation limits.** The offered-label Brier score is
0.08945 across 91,140 diagnosis/case pairs. For offered-label pairs in the
0.80–0.90 bin, the mean score was 0.848 and benchmark-positive fraction
0.845; in the 0.90–1.00 bin these were 0.937 and 0.951. This is encouraging
benchmark calibration evidence, but is not calibration to real-patient
disease probabilities. All-23 probabilities outside the four adjudicated
labels cannot be clinically calibrated from this answer key. The paper's
labels and synthetic generation process also do not establish that each
individual vignette is a clinician-validated real-world diagnosis.

These findings make a strong portfolio story when framed accurately: a
psychology-informed, technically reproducible application of a fast typed
model; a grouped development/holdout design; DSM-oriented structured
prompting; paired candidate-set conditions; measured accuracy, uncertainty,
latency, and cost; and transparent limits. They do not establish superiority
to LLMs, clinical validity, or an autonomous diagnostic product. No additional
API calls are needed for the planned cutoff curves and calibration analyses;
they can be computed from saved scores. A next useful step is a careful
write-up of the already-frozen report, with the distinctions above retained.
