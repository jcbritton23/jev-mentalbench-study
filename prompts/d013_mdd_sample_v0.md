# One complete diagnosis guide example: D013 Major Depressive Disorder

Status: **frozen as the D013 guide for the v1.1 holdout request; three
synthetic-only Jev micro-test requests were run on 2026-09-27. No MentalBench
case was sent in that micro-test.**
This illustrates the amount and kind of information proposed for **one of 23
diagnosis judgments**, not a two-diagnosis classifier or a complete request.
The full all-23 request evaluates the same case with 23 diagnosis guides and
23 parallel Noul questions. It paraphrases source material; it is not a
diagnostic instrument for real patients.

## Clinical guide entry

```json
{
  "name": "Major Depressive Disorder",
  "code": "D013",
  "benchmark_label_scope": "Use D013 for a major depressive presentation without episode-linked psychotic features. The benchmark has a separate D015 label for MDD with Psychotic Features. If psychosis is unreported, treat it as unknown; do not infer its presence.",
  "defining_pattern": "A sustained depressive episode marked by depressed mood or marked loss of interest or pleasure, with a meaningful change from usual functioning. Consider the overall cluster and severity, not sadness alone.",
  "episode_requirements": "A major depressive episode ordinarily lasts at least two weeks, with symptoms present most of the day on nearly every day. The formal DSM pattern involves at least five of the nine symptom domains during the same period, including depressed mood or loss of interest/pleasure, and clinically significant distress or impairment.",
  "symptom_domains": [
    "Depressed mood",
    "Markedly reduced interest or pleasure",
    "Meaningful appetite or weight change",
    "Too little or too much sleep",
    "Observable slowing or agitation",
    "Fatigue or low energy",
    "Worthlessness or excessive guilt",
    "Difficulty thinking, concentrating, or deciding",
    "Thoughts of death, suicidal thoughts, or suicidal behavior"
  ],
  "key_distinctions": [
    "A history of a genuine manic or hypomanic episode raises a bipolar diagnosis rather than unipolar MDD.",
    "A chronic depressed mood across years suggests persistent depressive disorder; a full major depressive episode can also occur during that chronic course.",
    "If delusions or hallucinations occur during the major depressive episode, consider the benchmark's separate D015 MDD with Psychotic Features label. Psychosis continuing outside depressive episodes points toward a different psychosis/mood differential rather than that specifier. The episode timeline matters.",
    "Consider medication, substance, or medical causes when the vignette supplies evidence for them. A stressor does not by itself exclude MDD when a full depressive syndrome is present."
  ],
  "evidence_handling": "Unreported symptoms or episode history are unknown. Their absence from a selective self-report reduces certainty but does not prove they are absent. Explicit, reliable information that a required feature is absent or that a competing condition better accounts for the presentation weighs more strongly against MDD."
}
```

This contains the complete *decision-relevant outline* for the sample, including
the nine symptom domains as reference context. Jev is not asked nine additional
questions or made to mechanically tally them. We will see on exploration cases
whether the symptom-domain list helps or becomes distracting.

## One Noul question that uses this entry

```json
{
  "type": "noul",
  "instructions": {
    "question": "Considering all diagnoses in `candidate_diagnoses`, does `case_text` support retaining the benchmark's plain Major Depressive Disorder label (D013) as a credible diagnostic candidate?",
    "focus": "Use the overall depressive pattern and D013 guide, then compare with all available candidates on episode course, functional impact, and distinguishing evidence. D015 is one relevant distinction when episode-linked psychotic features are clearly described. Treat unreported details as unknown; more than one candidate can remain credible."
  },
  "criteria": {
    "true": {
      "what": "The available evidence meaningfully supports a major depressive episode under the plain D013 label, without clearly described psychotic features tied to that episode. A selective narrative may leave some details unreported."
    },
    "false": {
      "what": "The depressive pattern is weak or absent, stated evidence materially favors a different explanation, or psychotic features tied to the depressive episode make the more specific D015 label appropriate."
    }
  }
}
```

The actual request also supplies `case_text`, `candidate_diagnoses`, and the
guide entries for the available labels in shared `state`, then batches this
question with 22 other candidate questions in the all-23 test or three others
in the four-option test. The D013 guide mentions its closest lookalikes, but
the full candidate list is not limited to those examples. It never supplies
the answer key.

## Label convention for this draft

The benchmark includes both D013 (MDD) and D015 (MDD with Psychotic Features).
Clinically, psychotic features specify a form of MDD; they are not an unrelated
disorder. For this benchmark, John chose the plain D013 label when a major
depressive presentation has no described psychotic features, and the specific
D015 label when psychotic features occur with the depressive episode. An
unreported psychosis history remains unknown. Evidence that psychosis persists
outside depressive episodes should prompt consideration of schizoaffective or
another psychotic disorder; co-occurrence alone does not settle that
differential. The same principle applies to D008 (Bipolar I) versus D010
(Bipolar I with Psychotic Features), with psychotic features linked to a mood
episode. Apply the convention in both study conditions and describe it as a
benchmark label convention, not a claim that the broad disorder ceases to exist.

Sources for the clinical outline: [SAMHSA's DSM-5 MDD criteria exhibit,
reproduced with APA permission](https://www.ncbi.nlm.nih.gov/books/NBK571021/box/ch4.b4/),
[NIMH depression overview](https://www.nimh.nih.gov/health/publications/depression),
[NIMH bipolar overview](https://www.nimh.nih.gov/health/publications/bipolar-disorder),
and [APA's DSM-5-TR clarification for MDD](https://www.psychiatry.org/File%20Library/Psychiatrists/Practice/DSM/DSM-5-TR/APA-DSM5TR-MajorDepressiveDisorder.pdf).
For the episode-timing distinction, see the [American Psychiatric Association's
schizoaffective overview](https://www.psychiatry.org/patients-families/schizophrenia/what-is-schizophrenia)
and [NIH-hosted clinical review of psychosis](https://pmc.ncbi.nlm.nih.gov/articles/PMC4455840/).
TypeSafe guidance: [structured questions](https://docs.typesafe.ai/primitives/advanced),
[Jev model limits](https://docs.typesafe.ai/models), and
[known Jev 1.13 limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13).

## First live micro-test (synthetic cases only)

Run with [`scripts/test_mdd_guide.py`](../scripts/test_mdd_guide.py) using
`jev-1.13.0`; one D013 Noul per request and only the D013 guide in state:

| Invented case | D013 yes probability | Input tokens | Estimated cost | Latency |
| --- | ---: | ---: | ---: | ---: |
| Clear nonpsychotic depressive episode | 0.97 | 1,139 | $0.00004784 | 0.269 s |
| Brief sadness without a depressive syndrome | 0.10 | 1,111 | $0.00004666 | 0.230 s |
| Depressive episode with episode-linked psychosis | 0.12 | 1,133 | $0.00004759 | 0.186 s |

Total estimated cost: **$0.00014209** for three calls. These results check the
question's basic behavior and the D013/D015 label convention on deliberately
clear examples. They do not measure MentalBench accuracy, calibration, or
performance and cost when all 23 guides and questions are present.
