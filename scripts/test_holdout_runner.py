"""Synthetic-only checks of holdout cost reservation and split enforcement."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import csv
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

try:
    from . import run_holdout_v1_1 as runner
    from . import summarize_holdout_v1_1 as scorer
except ImportError:
    import run_holdout_v1_1 as runner
    import summarize_holdout_v1_1 as scorer


class HoldoutRunnerChecks(unittest.TestCase):
    @staticmethod
    def cases() -> list[dict]:
        return [{"row_index": row_index, "group_id": f"SYNTH:{row_index}",
                 "case_type": "type1", "generator": "synthetic",
                 "case_text": "Fictional test input", "option_codes": ["D001", "D002", "D003", "D004"],
                 "key_codes": ["D001"]} for row_index in range(3)]

    @staticmethod
    def fake_run_one(case: dict, arm: str, *_args) -> dict:
        return {"row_index": case["row_index"], "arm": arm, "status": "ok",
                "model": runner.MODEL, "prompt_version": "v1_1_frozen",
                "estimated_cost_usd": 0.0005, "failed_attempt_cost_upper_usd": 0.0,
                "input_tokens": 1000, "output_tokens": 10, "retry_count": 0,
                "elapsed_seconds_total": 0.01, "attempts": [{"attempt": 1, "status": "ok"}]}

    def run_synthetic(self, cap: float) -> tuple[int, list[dict], dict]:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            freeze = json.loads(runner.FREEZE.read_text(encoding="utf-8"))
            freeze["holdout_cost_cap_usd"] = cap
            freeze["expected_requests"] = 6
            names = {code: code for code in ("D001", "D002", "D003", "D004")}
            with patch.multiple(runner, JOURNAL=root / "responses.jsonl",
                                SESSIONS=root / "sessions.jsonl",
                                SUMMARY=root / "summary.json",
                                run_one=self.fake_run_one):
                with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                    exit_code = runner.run_holdout(self.cases(), set(), 0.0,
                                                   names, {}, "", freeze)
                records = [json.loads(line) for line in (root / "responses.jsonl").read_text().splitlines()]
                summary = json.loads((root / "summary.json").read_text())
            return exit_code, records, summary

    def test_temporary_inflight_reservation_does_not_stop_run(self) -> None:
        exit_code, records, summary = self.run_synthetic(0.016128)
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(records), 6)
        self.assertEqual(summary["successful_requests"], 6)
        self.assertLessEqual(summary["conservative_cost_upper_usd"], 0.016128)

    def test_cost_cap_stops_before_next_request(self) -> None:
        exit_code, records, summary = self.run_synthetic(0.009)
        self.assertEqual(exit_code, 1)
        self.assertEqual(len(records), 2)
        self.assertEqual(summary["stop_reason"], "cost_cap")
        self.assertLessEqual(summary["conservative_cost_upper_usd"], 0.009)

    def test_resume_journal_rejects_non_holdout_row(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "responses.jsonl"
            path.write_text(json.dumps({"row_index": 99, "arm": "all23", "status": "error",
                                        "max_possible_cost_usd": 0.008064}) + "\n")
            freeze = json.loads(runner.FREEZE.read_text(encoding="utf-8"))
            with patch.object(runner, "JOURNAL", path):
                with self.assertRaisesRegex(RuntimeError, "non-holdout"):
                    runner.read_journal({1}, freeze)

    def test_resume_journal_reserves_possible_retry_cost(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "responses.jsonl"
            path.write_text(json.dumps({
                "row_index": 1, "arm": "all23", "status": "ok",
                "model": runner.MODEL, "prompt_version": "v1_1_frozen",
                "estimated_cost_usd": 0.0005,
                "failed_attempt_cost_upper_usd": 0.002688,
            }) + "\n")
            freeze = json.loads(runner.FREEZE.read_text(encoding="utf-8"))
            with patch.object(runner, "JOURNAL", path):
                completed, success, failed_upper = runner.read_journal({1}, freeze)
            self.assertEqual(completed, {(1, "all23")})
            self.assertAlmostEqual(success, 0.0005)
            self.assertAlmostEqual(failed_upper, 0.002688)

    def test_family_bootstrap_uses_all_frozen_group_strata(self) -> None:
        records = []
        with runner.GROUP_SPLIT.open(encoding="utf-8", newline="") as stream:
            for group in csv.DictReader(stream):
                if group["split"] != "holdout":
                    continue
                types = (["type3", "type4"] if group["case_types"] == "type3+type4"
                         else [group["case_types"]])
                for case_type in types:
                    keys = ["D001", "D002"] if case_type == "type3" else ["D001"]
                    records.append({
                        "group_id": group["group_id"], "arm": "four",
                        "case_type": case_type, "option_codes": ["D001", "D002", "D003", "D004"],
                        "key_codes": keys, "top1_code": "D001",
                        "probabilities": {"D001": .9, "D002": .9 if case_type == "type3" else .1,
                                          "D003": .1, "D004": .1},
                    })
        result = scorer.family_bootstrap_four(records, .5)
        self.assertEqual(sum(result["group_counts_by_stratum"].values()), 673)
        self.assertEqual(result["paper_weighted_four_option_exact_95pct_interval"], [1.0, 1.0])


if __name__ == "__main__":
    unittest.main()
