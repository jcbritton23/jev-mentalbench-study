# MentalBench holdout freeze v1.1

Frozen 2026-09-27, before any held-out Jev request. The machine-readable
freeze is [`mentalbench_holdout_freeze_v1_1.json`](mentalbench_holdout_freeze_v1_1.json).
Its checksums pin the source dataset, group and row assignments, all 23
diagnosis guides, question builder, model, runner, and scoring code. The
runner refuses changed files or a mixed-version response journal.

## Request and answer rule

- Use `jev-1.13.0`. Ask one Noul plausibility question per available
  diagnosis, with all questions for a case in one request.
- For each held-out case, send the all-23 arm with all 23 guides and candidate
  labels. The case's supplied four options and answer key are absent from its
  API state. Separately send the four-option arm with only those four labels
  and guides. The answer key is absent from both arms.
- Use the v1 question wording tested in exploration. The only guide change
  since the full exploration run is the more complete D012 Specific Phobia
  and D016 OCD descriptions. A three-case, one-family development check did
  not show a measurable classification gain. No further wording changes are
  planned for this evaluation.
- Always take the highest-scored diagnosis for a required single answer.
  For differential sets, include every available diagnosis with score at
  least **0.50** as the primary rule. **0.40** is the prespecified more
  inclusive Type 3 sensitivity point. The full cutoff curve will also be
  reported without reselecting a threshold from held-out outcomes.
- The main comparison to the paper uses the four-option arm: top answer for
  Types 1 and 2, exact offered-label set at 0.50 for Types 3 and 4, then the
  paper's case-type weights 1,725 / 3,450 / 6,525 / 13,050. Also report the
  raw holdout score. The all-23 arm is a harder extension with unadjudicated
  labels outside the supplied four.
- Estimate uncertainty by resampling the 673 reconstructed source groups,
  with Type 1, Type 2, and linked Type 3/4 families as strata. The analysis
  uses 2,000 bootstrap replicates with a fixed seed. Report case-type
  results, group counts, paired arm differences, offered-label calibration,
  cost, retries, request latency, and total active run time.

## Data and budget gate

The frozen holdout has **22,785 cases / 673 source groups**: 990 Type 1,
2,760 Type 2, 6,345 Type 3, and 12,690 Type 4. Each case requires two
requests, **45,570** in total. The full exploration run projects **$15.2584**
for the holdout. The runner's holdout cap is **$17.50**, reserving up to the
documented 64k input-token request maximum for every in-flight attempt and
up to three attempts per request. It stops before scheduling a request that
could exceed the cap under the frozen $0.042 per million input-token rate.
Prior recorded project calls total approximately $1.32, leaving some room
under the project's $20 target. Actual account charges and available
credits must be checked separately.

The default command is a metadata-only preflight. It hashes the raw source
as bytes, validates the split and request shape using synthetic text, checks
any existing journal, and sends no API request:

```bash
.venv/bin/python scripts/run_holdout_v1_1.py
```

The explicit `--run` flag starts or resumes the held-out API evaluation.
The ignored journal stores codes, probabilities, usage, status, and timing,
without case descriptions or raw provider payloads. The post-run scorer
refuses a partial result:

```bash
.venv/bin/python scripts/run_holdout_v1_1.py --run
.venv/bin/python scripts/summarize_holdout_v1_1.py
```

The present preparation did **not** use `--run`. No held-out request or
scoring result exists yet.
