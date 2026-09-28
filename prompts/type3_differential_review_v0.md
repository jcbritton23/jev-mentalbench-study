# Type 3 differential review after five all-23 exploration calls

Status: **development analysis and proposed next wording; no holdout case was read or sent.**
The first draft guide and question were kept fixed for the two additional
Type 3 requests. Complete 23-score vectors and timing are in the ignored local
[first pilot result](../results/first_draft_23way_3case_v0.json) and
[Type 3 follow-up result](../results/type3_psychosis_followup_2case_v0.json).
This note paraphrases exploration cases and does not copy their source text.

## Observed results

| Exploration case | Benchmark-keyed diagnoses and Jev scores | Highest all-23 score |
| --- | --- | --- |
| Type 3, D006/D010 | Schizoaffective bipolar 0.50 (rank 3); bipolar I with psychotic features 0.53 (rank 2) | Schizophrenia 0.81 |
| Type 3, D007/D015 | Schizoaffective depressive 0.47 (rank 4); MDD with psychotic features 0.77 (rank 1) | MDD with psychotic features 0.77 |
| Type 3, D004/D015 | Delusional disorder 0.39 (rank 4); MDD with psychotic features 0.33 (rank 5) | Plain MDD 0.83 |

These three cases were selected for development, with the two follow-up pairs
chosen for psychosis/mood differential coverage after seeing the first case.
They are not an unbiased estimate of Type 3 accuracy. The key adjudicates
the four supplied options; an all-23 top score outside them is an important
disagreement, not automatically a clinical error.

## What the bipolar-versus-schizophrenia case actually leaves open

The D006/D010 Type 3 narrative describes roughly ten months of irritability,
being driven to start many projects, sleeping less while working, and erratic
follow-through. It also describes about eight months of tactile/perceptual
experiences, a surveillance belief, unusual invented words, withdrawal, and
functional decline. This is substantial evidence for a sustained psychotic
syndrome. It suggests a manic mood shift, but it does not clearly establish
reduced *need* for sleep rather than curtailed sleep, a bounded manic episode,
or the complete set of mania features. The relationship between psychosis and
qualifying mood episodes is not resolved. Those facts can make schizophrenia
a plausible outside-choice hypothesis under the all-23 task.

The source profile's two **exploration-only** Type 4 variants clarify the
benchmark's intended switch. One says the psychotic experiences faded when
the elevated/irritable state ended, supporting bipolar I with psychotic
features. The other says psychosis continued for at least two weeks during
relatively normal mood between high and low periods, supporting
schizoaffective bipolar type. The Type 3 case omits that interval information.
Our guides already state the distinction. Lowering schizophrenia just to
force one of the two supplied answers would undermine the all-23 experiment.

## What the two follow-up cases add

In D007/D015, a year of depression and about eight months of possible
hallucinations/somatic delusion overlap, while psychosis without a major mood
episode is not described. D015 therefore has more direct support; D007's
0.47 is uncertainty around the missing independent-psychosis interval.
The plain MDD label also scored 0.72 despite the possible psychotic features,
which exposes a question-wording issue for the benchmark's plain-versus-
specifier convention.

In D004/D015, there is a strongly held belief that an executive is signaling
romantic interest through ambiguous cues, alongside a depressive syndrome;
the onset order is unclear. Whether the belief is a fixed delusion rather than
an overinterpretation is itself uncertain. Jev's low D004/D015 scores and
high plain MDD score may reflect that uncertainty. It is worth reviewing,
not automatically relabeling as a model failure.

## Proposed first revision for discussion

1. **Align the Noul with independent plausibility.** In the current runner,
   the generic `false` criterion ends with “or supports a better-fitting
   alternative.” That can lower a live differential merely because another
   diagnosis scores higher. Proposed wording: *False when the described
   syndrome fits poorly or explicit evidence contradicts a defining feature
   or resolves the differential against this diagnosis.* Keep the `true`
   criterion focused on meaningful positive evidence plus unresolved missing
   information. This keeps Type 4 discriminators effective without forcing a
   single winner in Type 3.
2. **Use specific criteria for the plain mood labels.** The full-23 runner used
   one generic Noul template for D013 and D008 even though the D013 sample
   document has a more specific question. In the next version, D013 should
   explicitly mean the *plain benchmark label* when a major depressive
   episode is supported and episode-linked psychotic features are not clearly
   described; D008 should use the parallel rule for bipolar I. When the
   evidence for psychosis is genuinely uncertain, the plain and specifier
   labels may both retain some probability. This corrects a prompt mismatch
   rather than tailoring a guide to a particular answer key.
3. **Keep the current psychosis/mood guides.** They already identify the
   clinically important two-week mood-free psychosis interval, proportion of
   illness spent in major mood episodes, and episode-linked psychosis. More
   Type 3 development cases can test whether wording changes improve
   differential retention without making unrelated labels uniformly high.

The proposed revision was implemented as a separate v1 question builder in
`scripts/compare_type3_prompts_v0_v1.py`; v0 guides and questions remain
unchanged. It was evaluated on three previously untested, source-group-disjoint
Type 3 exploration cases. The result is recorded in
`results/type3_v0_v1_fresh_3case.json` (ignored; no case text). Do not choose
v1 solely because it raises scores on these three cases.

| New Type 3 pair | v0 keyed probabilities | v1 keyed probabilities | Both keyed at 0.50? |
| --- | --- | --- | --- |
| D003/D008 | 0.83 / 0.22 | 0.84 / 0.28 | Neither version |
| D005/D018 | 0.60 / 0.47 | 0.63 / 0.52 | v1 only |
| D019/D020 | 0.25 / 0.59 | 0.26 / 0.62 | Neither version |

The v1 wording raised each keyed score slightly but did not change the top
all-23 label or either keyed label's rank in any case. The number of all-23
labels at or above 0.50 rose from 2 to 3 for D005/D018 and was unchanged in
the other two. This is an exploratory n=3 paired check, not evidence that v1
generalizes or that the benchmark's two labels must both be true clinically.
It also shows why a prompt wording change alone may not solve omitted
discriminator information. The four-option condition remains untested.

Six additional Jev requests used 77,501 input tokens and cost an estimated
**$0.003255042** at the documented input-token rate. Their individual request
latencies were 0.3978, 0.2744, 0.4081, 0.4080, 0.2292, and 0.2429 seconds.

## Four-option comparison on the same three cases

The v0 four-option questions were run on those same rows. Only the four
supplied candidates, their guides, and the case text were sent; benchmark keys
stayed local. This keeps the question version fixed and changes the available
diagnoses, though it also reduces the guide/state size.

| Type 3 pair | All-23 top diagnosis | Four-option top diagnosis | Keyed scores, all-23 → four | Both keys ≥0.50 in four-option? |
| --- | --- | --- | --- | --- |
| D003/D008 | D003 (keyed) | D003 (keyed) | D003 .83→.85; D008 .22→.22 | No |
| D005/D018 | D004 (outside options) | D005 (keyed) | D005 .60→.64; D018 .47→.48 | No |
| D019/D020 | D011 (outside options) | D020 (keyed) | D019 .25→.34; D020 .59→.61 | No |

The top-ranked diagnosis moved to a keyed answer in all three four-option
cases, compared with one of three all-23 cases. At the 0.50 differential
cutoff, each four-option case still retained only one of its two keyed
diagnoses. Thus restricting the list changed ranks substantially where an
outside diagnosis had led, but did little to the keyed probability values.
With three selected development cases this is descriptive only; it does not
establish a reliable accuracy gain. The three four-option requests used 9,645
input tokens, cost an estimated **$0.00040509**, and took 0.2196, 0.1829, and
0.1447 seconds. Detailed scores are in the ignored
`results/type3_four_option_same_cases_v0.json`.

Guide-file SHA-256 values for these five v0 calls (the files were unchanged
across the calls):

- `d013_mdd_sample_v0.md`: `05e544044be56b27dda230b1c7d3dda8c0c953dc7163ea52ce10df836d17ec76`
- `basic_diagnosis_guides_v0.md`: `bda02731aa97e161e3205d8ddc61211afe72da291ecaca6a286b70b7ff7a7a9e`
- `complex_diagnosis_guides_v0.md`: `22c866d818924173436550bc9f5132721c2b9a1e4e72a7d36f498efba0013a63`

Clinical basis: [APA schizophrenia and schizoaffective overview](https://www.psychiatry.org/patients-families/schizophrenia/what-is-schizophrenia),
[APA bipolar overview](https://www.psychiatry.org/patients-families/bipolar-disorders/what-are-bipolar-disorders),
and [APA DSM-5-TR clarification of bipolar psychotic-feature specifiers](https://www.psychiatry.org/getmedia/98fd2c17-93f0-42cd-9f41-755d77b862a5/APA-DSM5TR-BipolarIandBipolarIIDisorders.pdf).
TypeSafe's [Noul guidance](https://docs.typesafe.ai/primitives/noul)
describes independent yes probabilities; its [Jev 1.13 limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13)
warn that literal criteria wording and irrelevant state can change results.
