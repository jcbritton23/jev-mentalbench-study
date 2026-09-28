# MentalBench Jev question, v1 candidate

Status: **question wording frozen for the v1.1 holdout request after the full
exploration run**. This version
retains the v0 DSM guide entries and changes the shared Noul question/criteria.
It was first tested on small paired Type 3 development cases, then used for
both arms of the complete 1,965-case exploration partition. The paired pilot
alone did not establish that v1 is better than v0. See the Type 3 review and
the full exploration report for measured performance.

## Shared question

> Based on `case_text`, the available diagnoses in `candidate_diagnoses`, and
> the guide for **[diagnosis]**, does the description meaningfully support
> retaining **[diagnosis]** as a plausible diagnostic candidate? Consider the
> overall clinical pattern, course, impairment, and distinguishing evidence.
> Treat unreported details as unknown rather than absent, and weigh explicit
> contrary evidence. More than one diagnosis may remain plausible when the case
> does not resolve the differential.

## Noul criteria

- **True:** The best available evidence meaningfully supports this diagnosis
  as a plausible candidate, even if a selective description leaves some details
  unknown or another candidate also fits.
- **False:** The described syndrome fits this diagnosis poorly, or explicit
  evidence contradicts a defining feature or resolves the differential against
  this diagnosis.

## Diagnosis-specific conventions used in the pilot

- For D013 (plain MDD), favor the plain benchmark label when a major depressive
  episode is supported and episode-linked psychotic features are not clearly
  described. If psychosis is uncertain, the plain and psychotic-feature labels
  may both remain plausible.
- For D008 (plain Bipolar I), favor the plain benchmark label when a manic
  episode is supported and episode-linked psychotic features are not clearly
  described. If psychosis is uncertain, the plain and psychotic-feature labels
  may both remain plausible.
- For D015, apply the D013 depressive-episode symptom domains; psychotic
  symptoms must overlap a qualifying depressive episode and mood shift.
- For D001–D003, use the shared ADHD symptom-domain reference for current
  presentation thresholds and developmental evidence.

The answer is a yes probability for each diagnosis independently, not a
probability distribution across diagnoses. The top-scoring diagnosis is the
required single answer; differential cutoffs are applied locally to the saved
scores and do not change the Jev question.
