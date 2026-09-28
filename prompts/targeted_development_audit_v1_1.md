# Targeted development checks: D012/D016 guide and recurring misses

Date: 2026-09-27. These checks used only rows assigned to the frozen
exploration partition. No holdout case text, option, label, or Jev request was
used. This is a limited qualitative review, not clinician adjudication.

## Revised specific-phobia and OCD guides

The expanded D012/D016 entries were checked in the four-option setting on
three hash-selected exploration rows: one Type 3 D012/D016 pair and one Type
4 row keyed to each diagnosis. They come from the **same reconstructed source
group**, so these are three related variants, not independent replications.
The baseline scores are paired with the original full-v1 exploration
journal. Jev saw only the case text and the four candidates/guides;
benchmark options and answer keys stayed local.

| Type / key | Row | Baseline D012 / D016 | Expanded-guide D012 / D016 | Exact set at .50 |
|---|---:|---:|---:|---|
| Type 3 / both | 8268 | .90 / .11 | .91 / .11 | no → no |
| Type 4 / D012 | 17909 | .94 / .07 | .92 / .07 | yes → yes |
| Type 4 / D016 | 17887 | .10 / .95 | .09 / .96 | yes → yes |

Across the three requests, Jev 1.13.0 used 7,567 input tokens and 240 output
tokens; estimated input cost was **$0.000317814** and summed request latency
was **0.7959 seconds** (mean 0.2653 seconds). The clarifications did not
materially move scores or alter the .50 classification on these clear Type 4
cases, nor did they recover the second key on the Type 3 case. This does not
establish that the fuller guides have no value: all three cases came from one
family and this check is far too small to estimate a prompt effect. It does
show no immediate evidence that another round of phobia/OCD wording will fix
the observed Type 3 key-recovery gap. Keep the fuller guides as a candidate
for John's review; do not claim an improvement from this check.

Machine-readable scores and timing (no case text or raw API payload):
[`phobia_ocd_guide_v1_1_exploration_check.json`](../results/phobia_ocd_guide_v1_1_exploration_check.json).
The small runner is [`check_phobia_ocd_v1_1.py`](../scripts/check_phobia_ocd_v1_1.py).

## Qualitative audit of recurring Type 2 errors

Three four-option Type 2 misses were chosen from distinct exploration
families, one each for D003, D006, and D007. Existing exploration scores
showed D003 at .47 versus D001 combined at .89; D006 at .41 versus D008 at
.72 and D010 at .65; and D007 at .34 versus D015 at .79. The broader
exploration rates for these target labels were D003 15/30, D006 8/30, and
D007 11/30. These rows are clustered within very few families, so the rates
are not independent-case estimates.

- **D003 hyperactive/impulsive ADHD:** The inspected narrative includes
  childhood restlessness and blurting, current pacing/leaving the desk, and
  interrupting. It also gives substantial current inattention: losing focus,
  distractibility, unfinished tasks, and missed documents/deadlines. Jev's
  preference for D001 combined over the D003 benchmark key is therefore
  consistent with the described current pattern, although the vignette does
  not supply a complete symptom count or childhood evidence for both domains.
  This looks more like a forced single-label or generated-profile ambiguity
  than missing symptom-domain guidance. Do not weaken the combined-presentation
  threshold to raise D003 recovery.
- **D006 schizoaffective bipolar type:** The example describes psychotic-like
  experiences over roughly 14 months, manic symptoms over about 11 months,
  then a depressive period of about five months. Jev strongly preferred
  bipolar I without psychotic features (D008) and also rated bipolar I with
  psychotic features (D010) relatively high. The vignette does not sharply
  locate the psychotic experiences relative to the mood episodes or establish
  the independent-psychosis interval with precision. The guide already states
  the two-week psychosis-without-mood and mood-majority requirements. The
  remaining issue is vignette chronology and overlap, not an obvious missing
  criterion in the guide.
- **D007 schizoaffective depressive type:** The case describes close to two
  years of things feeling "off" and about a year and a half of depression,
  with delusional-sounding beliefs, disorganization, blunted affect, and
  tactile experiences. Jev preferred D015 MDD with psychotic features. The
  implied timeline might support psychosis outside depression, but the onset
  of the specific psychotic symptoms is not clearly tied to the earlier
  interval. As written, the D007-defining two-week independent-psychosis
  period is uncertain. The guide already covers this distinction; avoid
  adding another prompt reminder on the basis of this one case.

These examples suggest the current ADHD and schizoaffective guides already
cover the critical thresholds. Two of the three errors plausibly reflect
benchmark-label or temporal ambiguity, rather than an instruction that needs
more detail. For the full evaluation, retain the DSM-based guides and score
against the published keys, while separately flagging ambiguous disagreements
for discussion. Do not rewrite instructions simply to maximize benchmark-key
agreement on these examples.

## Decision

No additional guide changes are justified by these small checks. The D012/D016
v1.1 expansions can be kept for review, with no claim of measured gain. If
John approves them and the other guides, freeze the resulting prompt before
any holdout request. The held-out partition remains untouched.
