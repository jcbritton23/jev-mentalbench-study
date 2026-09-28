# MentalBench Jev question, draft 0

Status: **draft 0 was tested in small exploration pilots; not frozen for holdout.**

This is the first question design for both study conditions. It uses TypeSafe's
`noul` question type: one independent yes-probability judgment for each available
diagnosis, with all questions for one case batched in one API request. The 23-way
condition asks 23 questions; the four-option condition asks four. Each condition
has its own request for the same case.

## What the question asks

> Given the clinical description and the diagnostic guide, is **[diagnosis]** a
> plausible explanation of the presentation based on the best available
> evidence? Consider the defining clinical pattern, course, functional impact,
> and features that distinguish it from the other available diagnoses. Missing
> information lowers certainty but is not evidence that a symptom is absent.
> Explicit evidence against a diagnosis lowers its support. More than one
> diagnosis may remain plausible when the description does not resolve the
> differential.

This asks about *diagnostic plausibility*, not whether a vignette documents
every requirement for a formal diagnosis. A Type 3 case can give high support
to two alternatives without asserting that both disorders are present.

## Request shape

The local runner will construct this JSON for each case. Names in brackets are
placeholders, not literal API fields or case data:

The [D013 Major Depressive Disorder example](d013_mdd_sample_v0.md) shows one
complete guide entry and its Noul question for clinical review. Draft entries
for the [11 other anxiety, trauma, and eating labels](basic_diagnosis_guides_v0.md)
and [11 ADHD, psychosis, and bipolar labels](complex_diagnosis_guides_v0.md)
now cover the full 23-label inventory, pending clinical and benchmark-label
review. They have not been converted into a final request or tested on cases.

```jsonc
{
  "model": "jev-1.13.0",
  "state": {
    "case_text": "[one synthetic case description]",
    "candidate_diagnoses": ["[available diagnosis names]"],
    "diagnostic_guide": {
      "[diagnosis name]": {
        "defining_pattern": "[clinically useful paraphrase]",
        "course_and_thresholds": "[duration, episode, onset, or impairment details that matter]",
        "key_distinctions": "[how this differs from close candidates]"
      }
    }
  },
  "questions": {
    "[stable diagnosis code]": {
      "type": "noul",
      "instructions": "Using `case_text`, `candidate_diagnoses`, and the `diagnostic_guide` entry for [full diagnosis name], is [full diagnosis name] a plausible explanation of this presentation based on the best available evidence? Consider defining features, course, impairment, and distinctions from the other candidates. Treat unreported details as unknown, not absent; weigh explicit contrary evidence against the diagnosis. More than one candidate may remain plausible.",
      "criteria": {
        "true": "The described pattern is meaningfully consistent with this diagnosis; any missing discriminating information leaves it a live possibility.",
        "false": "The observed pattern fits poorly or explicit contrary or distinguishing evidence makes this diagnosis unlikely."
      }
    }
  }
}
```

The runner fills `questions` for every available candidate. Diagnosis codes
serve as response keys, but the full diagnosis name must appear in each question:
TypeSafe says question IDs are not sent to the model. In the all-23 condition,
`candidate_diagnoses` and `diagnostic_guide` contain all 23 entries, with the
benchmark's four offered options and answer omitted. In the four-option
condition, these fields contain only that case's four offered diagnoses, with
the answer omitted. The question wording and guide entry for each diagnosis
stay the same across conditions.

## Guide detail

Begin each diagnosis entry with its clinical pattern and the few details that
change a differential judgment. Include specific subfeatures when they define
the syndrome or distinguish similar labels, such as the time relationship of
psychosis and mood episodes. Do not reduce the guide to only diagnosis names or
force Jev to count an exhaustive checklist of symptoms. We ask one Noul per
diagnosis, not a separate Noul for every DSM criterion. The development pilot
will show where the guide needs more detail or where wording creates confusion.
Paraphrase and record the source for each entry; John reviews the clinical
meaning before the guide is frozen.

## Benchmark diagnosis inventory

The published list and the local CSV's single-diagnosis answer mapping agree:

| Code | Diagnosis |
| --- | --- |
| D001 | Attention-Deficit/Hyperactivity Disorder (Combined Presentation) |
| D002 | Attention-Deficit/Hyperactivity Disorder (Predominantly Inattentive Presentation) |
| D003 | Attention-Deficit/Hyperactivity Disorder (Predominantly Hyperactive/Impulsive Presentation) |
| D004 | Delusional Disorder |
| D005 | Schizophrenia |
| D006 | Schizoaffective Disorder (Bipolar Type) |
| D007 | Schizoaffective Disorder (Depressive Type) |
| D008 | Bipolar I Disorder |
| D009 | Bipolar II Disorder |
| D010 | Bipolar I Disorder with Psychotic Features |
| D011 | Generalized Anxiety Disorder |
| D012 | Specific Phobia |
| D013 | Major Depressive Disorder |
| D014 | Persistent Depressive Disorder |
| D015 | Major Depressive Disorder with Psychotic Features |
| D016 | Obsessive-Compulsive Disorder |
| D017 | Body Dysmorphic Disorder |
| D018 | Posttraumatic Stress Disorder |
| D019 | Acute Stress Disorder |
| D020 | Adjustment Disorder |
| D021 | Anorexia Nervosa |
| D022 | Bulimia Nervosa |
| D023 | Binge-Eating Disorder |

Source: [MentalBench paper, Appendix B, Table 4](https://arxiv.org/html/2602.12871).
The local check read only `code`, `option`, and `answer` fields, not case text.

## Proposed bounded development pilot

1. Select **12 exploration cases**, three from each of Types 1–4, from distinct
   reconstructed seed groups. Use these to check the request, output shape,
   interpretation, and actual tokens, cost, and latency. This is a prompt check,
   not an estimate of accuracy across 23 diagnoses.
2. If the question works, use a **70-case exploration set** including those
   12: one Type 1 and one Type 2 case for each of the 23 diagnosis codes
   (46), plus one Type 3 and one Type 4 case for each of the 12 diagnosis-pair
   codes selected to cover all 23 diagnoses (24). This yields 70 cases from
   58 independent reconstructed seed groups. Select by metadata and seed
   group; keep case text out of chat and logs.
3. Limit prompt/guide development to the initial version and at most two
   substantive revisions. Freeze the final guide, question, model ID, sampling
   rule, and scoring code before any holdout request. Make a measured full-run
   cost projection after the first 12 and remain within the project's $20 goal.

This pilot size is a design choice for broad coverage and manageable review,
not a sample-size calculation for precise per-diagnosis accuracy.

TypeSafe references: [API](https://docs.typesafe.ai/api),
[Noul](https://docs.typesafe.ai/primitives/noul),
[State](https://docs.typesafe.ai/concepts/state),
[Jev 1.13 limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13).
