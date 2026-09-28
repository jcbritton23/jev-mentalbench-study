# MentalBench diagnosis guides: ADHD, psychosis, and bipolar labels

Status: **frozen for the v1.1 holdout request after full exploration review**. This completes
draft coverage of the benchmark's 23 labels alongside the [first guide batch](basic_diagnosis_guides_v0.md)
and [D013 MDD example](d013_mdd_sample_v0.md). These are paraphrased,
decision-relevant outlines, not a diagnostic instrument. Each label receives
one independent Noul judgment under the shared question: *Does the description
support retaining this named benchmark label as a credible candidate, given
the best available evidence and the other available candidates?* Missing
information lowers certainty; it does not prove absence. Explicit contrary
evidence matters. A Type 3 case can retain two alternatives because the
discriminator is missing; that is not a claim of simultaneous comorbidity.

## Shared benchmark-label convention

Where the benchmark has both a broad mood label and a “with psychotic
features” label, prefer the more specific label when hallucinations or
delusions are described as concurrent with a qualifying mood episode. Do not
infer psychosis merely because it is unreported. Do not infer a mood-episode
relationship merely because psychosis and mood symptoms occur somewhere in
the same history. This is a *label-scoring convention*, not a rule that a
person with a psychotic specifier no longer has the underlying mood disorder.
The depressed episode in John's D015 rule must reach at least two weeks and
the psychotic symptoms must overlap that episode and mood shift. Mood
congruence can inform the pattern but is not required for the specifier.

## ADHD symptom-domain reference (shared by D001–D003)

The formal current-presentation threshold is **at least six of nine symptoms
in a domain through age 16, or at least five of nine from age 17 onward**,
persisting for at least six months. Combined presentation reaches the
age-appropriate threshold in *both* domains; predominantly inattentive or
hyperactive/impulsive presentation reaches it in only the named domain.
Several symptoms began before age 12, symptoms occur in two or more settings,
and there is functional interference. A case may report only selected
symptoms: distinguish *not reported* from *explicitly absent* and do not
force a literal count from a selective narrative.

Inattention domains (nine distinct patterns):

1. Frequent careless errors or missed details.
2. Difficulty sustaining attention in tasks or activities.
3. Appearing not to listen when directly addressed.
4. Failing to finish tasks or follow instructions despite understanding them.
5. Difficulty organizing tasks, activities, time, or materials.
6. Avoiding or disliking tasks demanding sustained mental effort.
7. Frequently losing needed items.
8. Being easily distracted by unrelated stimuli or thoughts.
9. Forgetfulness in ordinary daily activities.

Hyperactivity/impulsivity domains (nine distinct patterns):

1. Fidgeting or squirming.
2. Leaving one's seat when expected to remain seated.
3. Inappropriate running/climbing, or subjective restlessness in older people.
4. Difficulty playing or engaging in leisure quietly.
5. Being persistently on the go or unable to remain still.
6. Excessive talking.
7. Blurting out responses or completing others' sentences prematurely.
8. Difficulty waiting one's turn.
9. Interrupting or intruding on others.

These are paraphrased from [NIMH's ADHD symptom and diagnosis guide](https://www.nimh.nih.gov/health/publications/attention-deficit-hyperactivity-disorder-what-you-need-to-know)
and the [APA's ADHD overview](https://www.psychiatry.org/patients-families/adhd/what-is-adhd).
The shared reference should appear **once** in request state for all three ADHD
questions; repeating it in each question would waste tokens and may obscure
the case-specific judgment.

## D001 — ADHD, Combined Presentation

- **Pattern:** A persistent developmental pattern of both inattention
  (sustaining attention, organization, follow-through, distractibility,
  forgetfulness) and hyperactivity/impulsivity (restlessness, excessive
  activity or talking, interrupting, difficulty waiting) beyond what is
  developmentally expected.
- **Course:** Several symptoms began before age 12, occur in at least two
  settings, and interfere with functioning. The current presentation requires
  the age-appropriate threshold in **both** shared symptom domains above.
- **Distinctions:** The combined label needs credible evidence for *both*
  domains **in the current presentation**, not a single prominent trait from
  the second domain. ADHD presentations can shift across development, so a
  prior combined pattern does not prove a current combined pattern. Chronic
  developmental symptoms differ from concentration or agitation arising only
  during a depressive, anxious, manic, or psychotic episode. If only one
  domain is reported and supported, favor D002 or D003 rather than inferring
  combined presentation; the unreported domain remains unknown.

## D002 — ADHD, Predominantly Inattentive Presentation

- **Pattern:** Persistent difficulty sustaining attention, following through,
  organizing, tracking details or belongings, and resisting distraction or
  forgetfulness, beyond developmental expectations.
- **Course:** The ADHD onset, cross-setting, impairment, and six-month pattern
  above apply. In the current presentation, the inattention domain reaches
  its age-appropriate threshold; hyperactivity/impulsivity does not reach its
  full threshold when sufficient evidence is available to judge both.
- **Distinctions:** When only inattention is reported and supported, favor
  D002 over D001 without claiming that unreported hyperactivity/impulsivity
  is definitively below threshold. Prior or future presentations may differ.
  Concentration problems confined to a mood, anxiety, sleep, or psychotic
  episode do not by themselves establish developmental ADHD.

## D003 — ADHD, Predominantly Hyperactive/Impulsive Presentation

- **Pattern:** Persistent excessive movement or internal restlessness,
  difficulty remaining seated or quiet, excessive talking, impatience,
  interrupting, or acting before considering consequences, relative to
  developmental level.
- **Course:** The ADHD onset, cross-setting, impairment, and six-month pattern
  apply. In the current presentation, hyperactivity/impulsivity reaches its
  age-appropriate threshold; inattention does not reach its full threshold
  when sufficient evidence is available to judge both.
- **Distinctions:** Adult hyperactivity may appear as inner restlessness rather
  than conspicuous running. When only hyperactivity/impulsivity is reported
  and supported, favor D003 over D001 without claiming that unreported
  inattention is definitively below threshold; presentations may change over
  time. Episodic increased energy, reduced need for sleep, and
  elevated/irritable mood point toward mania or hypomania rather than ADHD
  alone.

## D004 — Delusional Disorder

- **Pattern:** One or more persistent delusions are the central disturbance.
  Outside the delusion's impact, behavior and functioning are not markedly
  disorganized, and prominent hallucinations, disorganization, or negative
  symptoms do not dominate.
- **Course:** Delusions persist at least one month in the formal pattern.
- **Distinctions:** Broad schizophrenia-spectrum symptoms and substantial
  decline favor D005. Psychotic symptoms occurring only within a major mood
  episode favor a mood disorder with psychotic features. Fixed, strongly held
  beliefs are not automatically delusions; assess reality testing and context.
  If mood episodes occur, their total duration is brief relative to delusional
  periods for this label.

## D005 — Schizophrenia

- **Pattern:** A sustained psychotic syndrome involving multiple characteristic
  domains: delusions, hallucinations, disorganized speech, markedly
  disorganized/catatonic behavior, or negative symptoms. The formal active
  phase includes at least two domains, with at least one being delusions,
  hallucinations, or disorganized speech. Functional decline supports the
  pattern.
- **Course:** Roughly one month of active symptoms (less if successfully
  treated) within at least six months of continuous disturbance is the formal
  course. A shorter syndrome may belong to another psychosis label outside
  this benchmark.
- **Distinctions:** If major mood episodes occupy the majority of the active
  and residual psychotic illness and there is also psychosis for two weeks
  without a major mood episode, consider D006/D007. Mood episodes brief
  relative to the total psychotic course favor schizophrenia. Isolated
  delusions with relatively preserved functioning favor D004. A psychotic
  symptom confined to a mood episode does not establish schizophrenia.

## D006 — Schizoaffective Disorder, Bipolar Type

- **Pattern:** A schizophrenia-level psychotic syndrome overlaps a major mood
  episode; the illness includes a manic episode (possibly with major
  depression). Delusions or hallucinations also persist for at least two weeks
  in the absence of a major mood episode.
- **Course:** Major mood episodes occupy the majority of the total active and
  residual illness duration, not merely a brief segment of a long psychotic
  illness.
- **Distinctions:** Psychosis *only* during mania/depression favors bipolar I
  with psychotic features. Mood episodes brief relative to psychotic illness
  favor schizophrenia. The bipolar subtype is defined by mania, not simply
  alternating mood symptoms. Missing psychosis-without-mood timeline details
  lower confidence in this differential; do not invent the two-week interval.

## D007 — Schizoaffective Disorder, Depressive Type

- **Pattern:** A schizophrenia-level psychotic syndrome overlaps a major
  depressive episode, and delusions or hallucinations also persist for at
  least two weeks without a major mood episode. No manic episode is supported
  in the depressive subtype.
- **Course:** Major mood episodes occupy the majority of the total active and
  residual psychotic illness duration.
- **Distinctions:** Psychosis confined to a depressive episode favors D015.
  Mood episodes brief relative to a long psychotic course favor D005. A true
  manic episode changes the schizoaffective subtype to D006. Do not infer
  independent psychosis from an unclear chronology; lower confidence when the
  timeline is incomplete.

## D008 — Bipolar I Disorder (plain benchmark label)

- **Pattern:** At least one manic episode: a distinct, sustained increase in
  mood/irritability and energy/activity with changes such as reduced need for
  sleep, grandiosity, pressured speech, racing thoughts, distractibility,
  increased goal-directed activity, or risky behavior. Depression can occur
  but is not required for bipolar I.
- **Course:** Mania generally lasts at least a week, or any duration if
  hospitalization is necessary, and markedly impairs function. Hypomania
  without any mania does not establish bipolar I. The formal manic pattern
  includes at least three of the accompanying changes (four if mood is only
  irritable): inflated self-esteem/grandiosity, reduced need for sleep,
  unusually increased talking, racing thoughts, distractibility, increased
  goal-directed activity or agitation, and risky/impulsive activities.
- **Distinctions:** For this benchmark, use D008 when manic illness is
  supported without clearly episode-linked psychotic features; use D010 when
  they are described during either a manic or a major depressive episode in
  the bipolar I course. Psychosis outside mood episodes raises the
  schizoaffective/schizophrenia differential.

## D009 — Bipolar II Disorder

- **Pattern:** At least one major depressive episode and at least one
  hypomanic episode, with no history of a full manic episode. Hypomania is a
  clear change in mood and energy/activity with observable change in function,
  but not the marked impairment or hospitalization of mania.
- **Course:** Hypomania lasts at least four consecutive days in the formal
  pattern and draws on the same seven accompanying change domains as mania
  (at least three, or four if mood is only irritable); major depression lasts
  at least two weeks. Both episode histories matter, even if the vignette
  focuses on current depression.
- **Distinctions:** A full manic episode shifts to bipolar I. Psychosis during
  an elevated episode makes it manic, not hypomanic. Depression without
  credible hypomania may favor D013/D014; chronic baseline activity or ADHD
  should not be mistaken for an episodic hypomanic change.

## D010 — Bipolar I Disorder with Psychotic Features

- **Pattern:** A bipolar I course with a manic episode, plus delusions or
  hallucinations concurrent with a qualifying mood episode (manic or major
  depressive). They may be mood-congruent or mood-incongruent.
- **Course:** The mania threshold/course of D008 applies. Establish the
  psychosis–mood timeline; simultaneity somewhere in the case history alone
  is not enough.
- **Distinctions:** If psychosis persists for at least two weeks outside any
  major mood episode, consider D006 when mood episodes occupy the majority of
  the illness. If psychosis has no clear episode link, retain uncertainty
  rather than forcing D010. With no described psychosis, use the plain D008
  benchmark label. Psychosis during an elevated episode rules out labeling
  that episode merely hypomanic.

## D015 — Major Depressive Disorder with Psychotic Features

- **Pattern:** A major depressive episode with depressed mood or loss of
  interest and a broader depressive syndrome, accompanied by delusions or
  hallucinations that occur **during the mood shift and overlap the depressive
  episode**. The psychosis may or may not match depressive themes.
- **Course:** The major depressive episode lasts at least two weeks and causes
  significant distress/impairment; use D013's symptom-domain outline as
  context. Do not require that psychosis last the entire episode, but require
  credible episode overlap rather than merely a remote psychosis history.
- **Distinctions:** Psychosis continuing for at least two weeks in the absence
  of a major mood episode raises D007 if major mood episodes dominate the
  illness, or D005 if they do not. Mania shifts the mood-disorder family.
  An unreported psychosis history is unknown, not affirmative evidence for
  D015; when the case describes no psychotic features, favor D013's plain
  benchmark label. If psychosis is present but the timing is not established,
  lower certainty and leave D013/D015 or a psychosis-spectrum alternative
  unresolved rather than silently assuming concurrency.

## Clinical-source and decision notes

Official/primary sources used for these paraphrases: [NIMH ADHD](https://www.nimh.nih.gov/health/publications/attention-deficit-hyperactivity-disorder-what-you-need-to-know),
[APA ADHD DSM-5 changes](https://www.psychiatry.org/File%20Library/Psychiatrists/Practice/DSM/APA_DSM-5-ADHD.pdf),
[APA schizophrenia and schizoaffective overview](https://www.psychiatry.org/patients-families/schizophrenia/what-is-schizophrenia),
[NIMH schizophrenia](https://www.nimh.nih.gov/health/publications/schizophrenia),
[APA bipolar overview](https://www.psychiatry.org/patients-families/bipolar-disorders/what-are-bipolar-disorders),
[APA bipolar I/II DSM-5-TR clarification](https://www.psychiatry.org/getmedia/98fd2c17-93f0-42cd-9f41-755d77b862a5/APA-DSM5TR-BipolarIandBipolarIIDisorders.pdf),
and [NIMH bipolar overview](https://www.nimh.nih.gov/health/publications/bipolar-disorder).

The shared Noul shape follows [TypeSafe's Noul guidance](https://docs.typesafe.ai/primitives/noul)
and [structured-question guidance](https://docs.typesafe.ai/primitives/advanced).
The following decisions were confirmed with John on 2026-09-27:

1. D010 applies when psychotic features occur during a qualifying manic **or**
   major depressive episode within a bipolar I course. This follows the
   episode-based specifier logic rather than requiring mania-linked psychosis.
2. ADHD is developmental, and presentations may shift over time. Score the
   *current* presentation supported by the case. If only one domain is
   reported, prefer that presentation rather than inferring combined type;
   an unreported second domain remains unknown.
3. Keep both schizoaffective distinctions: at least two weeks of delusions or
   hallucinations without a major mood episode and major mood episodes over
   the majority of the active/residual illness. An incomplete chronology
   lowers confidence; it does not justify inventing or assuming either fact.

These choices fix the guide's intended meaning, not its empirical performance
or the benchmark's answer-key validity. The development pilot still needs to
check whether Jev handles missing evidence and discriminating evidence as
intended before the guide is frozen.
