import importlib.util
import io
import json
import math
from pathlib import Path
import shutil
import struct
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import wave

SPEC = importlib.util.spec_from_file_location(
    "lecture", Path(__file__).parents[1] / "scripts/transcribe_lecture.py"
)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def result(text="The debt is twenty million, not thirty."):
    return {
        "response": {"text": text, "usage": {"cost": 0.001}},
        "generation_id": "test",
    }


def reconciliation(text="The debt is twenty million, not thirty.", finish="stop"):
    return {
        "response": {
            "choices": [
                {
                    "finish_reason": finish,
                    "message": {
                        "content": json.dumps({"text": text, "uncertainties": []})
                    },
                }
            ]
        }
    }


class Planning(unittest.TestCase):
    def test_mode_defaults(self):
        standard = m.apply_mode_defaults(m.parser().parse_args(["lecture.wav"]))
        self.assertEqual(standard.mode, "standard")
        self.assertEqual(standard.chunk_seconds, 300)
        self.assertEqual(standard.jobs, 4)
        self.assertEqual(standard.model, "microsoft/mai-transcribe-2")

        dual = m.apply_mode_defaults(
            m.parser().parse_args(["lecture.wav", "--mode", "dual-pass"])
        )
        self.assertEqual(dual.chunk_seconds, 120)
        self.assertEqual(dual.jobs, 1)

    def test_three_hour_coverage_and_bounded_chunks(self):
        spans = [(x + 5, x + 6) for x in range(0, 10800, 117)]
        plan = m.plan_chunks(0, 10800, 120, 20, spans)
        self.assertEqual(plan[0]["start"], 0)
        self.assertEqual(plan[-1]["end"], 10800)
        for a, b in zip(plan, plan[1:]):
            self.assertEqual(a["end"], b["start"])
        self.assertTrue(all(0 < c["end"] - c["start"] <= 120.000001 for c in plan))

    def test_silence_boundary_and_forced_boundary(self):
        p = m.plan_chunks(300, 560, 120, 20, [(410, 412)])
        self.assertEqual(p[0]["end"], 411)
        self.assertFalse(p[0]["forced_boundary"])
        self.assertTrue(p[1]["forced_boundary"])
        self.assertFalse(p[-1]["forced_boundary"])

    def test_invalid_responses_are_not_successes(self):
        for value in ({"response": {}}, {"response": {"text": None}}):
            with self.assertRaises(RuntimeError):
                m.validate_stt(value)
        with self.assertRaises(RuntimeError):
            m.parse_reconciliation(reconciliation(finish="length"), 30)
        r = reconciliation()
        r["response"]["choices"][0]["message"]["content"] = (
            '{"text":"x","uncertainties":[{"offset_seconds":99,"reason":"unclear"}]}'
        )
        with self.assertRaises(RuntimeError):
            m.parse_reconciliation(r, 30)

    def test_boundary_overlap_is_flagged_not_deleted(self):
        chunks = [
            {"final": {"text": "So A"}, "flags": []},
            {"final": {"text": "A versus B."}, "flags": []},
        ]
        m.audit_boundaries(chunks)
        self.assertEqual(chunks[1]["final"]["text"], "A versus B.")
        self.assertEqual(len(chunks[1]["flags"]), 1)
        m.audit_boundaries(chunks)
        self.assertEqual(len(chunks[1]["flags"]), 1)

    def test_language_and_provider_specific_options(self):
        p = m.stt_payload(
            "custom/model",
            {},
            None,
            {"custom/model": {"provider": {"prompt": "EBITDA"}}},
        )
        self.assertNotIn("language", p)
        self.assertNotIn("prompt", p)
        self.assertEqual(p["provider"]["options"]["provider"]["prompt"], "EBITDA")

    def test_preflight_requires_audio_and_structured_output(self):
        stt = {
            "data": [
                {"id": "a", "architecture": {"input_modalities": ["audio"]}},
                {"id": "b", "architecture": {"input_modalities": ["audio"]}},
            ]
        }
        calls = iter(
            [
                {"response": stt},
                {
                    "response": {
                        "data": [
                            {
                                "id": "review",
                                "architecture": {"input_modalities": ["audio"]},
                                "supported_parameters": ["response_format"],
                            }
                        ]
                    }
                },
            ]
        )
        self.assertEqual(
            len(m.preflight("key", ["a", "b"], "review", lambda *args: next(calls))), 3
        )

    def test_standard_preflight_skips_chat_catalog(self):
        calls = []

        def call(route, *args):
            calls.append(route)
            return {"response": {"data": [{"id": "primary"}]}}

        self.assertEqual(
            m.preflight("key", ["primary"], None, call)[0]["id"], "primary"
        )
        self.assertEqual(calls, ["models?output_modalities=transcription"])

    def test_http_error_body_never_printed_and_no_auth_retry(self):
        error = urllib.error.HTTPError(
            "https://example.invalid",
            401,
            "no",
            {},
            io.BytesIO(b"PRIVATE_AUDIO_OR_KEY"),
        )
        with patch.object(m.urllib.request, "urlopen", side_effect=error) as call:
            with self.assertRaises(RuntimeError) as raised:
                m.api_request("audio/transcriptions", "dummy-test-key", {})
        self.assertNotIn("PRIVATE", str(raised.exception))
        self.assertEqual(call.call_count, 1)

    def test_retry_limit_includes_initial_attempt(self):
        with (
            patch.object(m.urllib.request, "urlopen", side_effect=TimeoutError),
            patch.object(m.time, "sleep"),
        ):
            with self.assertRaises(RuntimeError):
                m.api_request("audio/transcriptions", "dummy-test-key", {}, retries=2)
            self.assertEqual(m.urllib.request.urlopen.call_count, 3)


@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe required"
)
class Pipeline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "lecture.wav"
        with wave.open(str(self.source), "wb") as w:
            w.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
            w.writeframes(
                b"".join(
                    struct.pack(
                        "<h", round(4000 * math.sin(2 * math.pi * 440 * i / 16000))
                    )
                    for i in range(16000 * 23)
                )
            )
        self.key = self.root / "key"
        self.key.write_text("dummy-test-key")
        self.out = self.root / "out"
        self.args = [
            str(self.source),
            "--output-dir",
            str(self.out),
            "--chunk-seconds",
            "10",
            "--boundary-window",
            "2",
            "--confirm-external-upload",
        ]
        self.calls = []

    def tearDown(self):
        self.tmp.cleanup()

    def fake_api(self, route, key, payload=None, *args):
        self.calls.append((route, payload))
        if route == "audio/transcriptions":
            self.assertNotIn("messages", payload)
            self.assertTrue(payload["input_audio"]["data"])
            return result()
        return reconciliation()

    def run_pipeline(self, extra=None, api=None):
        with (
            patch.object(m, "KEY_FILE", self.key),
            patch.object(m, "preflight", return_value=[]),
            patch.object(m, "api_request", side_effect=api or self.fake_api),
        ):
            return m.main(self.args + (extra or []))

    def checkpoint(self):
        return json.loads((self.out / "lecture.transcript.json").read_text())

    def test_complete_standard_pipeline_and_resume(self):
        self.assertEqual(self.run_pipeline(), 0)
        state = self.checkpoint()
        self.assertEqual(len(self.calls), 3)
        self.assertEqual(state["status"], "complete_needs_review")
        self.assertEqual(state["chunks"][1]["audio_start"], 10)
        self.assertEqual(state["chunks"][-1]["end"], 23)
        for chunk in state["chunks"]:
            self.assertEqual(len(chunk["drafts"]), 1)
            self.assertIn("twenty million", chunk["final"]["text"])
        self.calls.clear()
        self.run_pipeline(["--resume", "--jobs", "1"])
        self.assertEqual(self.calls, [])

    def test_dual_pass_rejects_parallel_jobs(self):
        with self.assertRaisesRegex(RuntimeError, "requires --jobs 1"):
            self.run_pipeline(["--mode", "dual-pass", "--jobs", "2"])

    def test_dual_pass_pipeline_keeps_both_drafts_and_reconciliation(self):
        self.run_pipeline(["--mode", "dual-pass"])
        state = self.checkpoint()
        self.assertEqual(len(self.calls), 9)
        for chunk in state["chunks"]:
            self.assertEqual(len(chunk["drafts"]), 2)
            self.assertIn("reconciliation", chunk)
        payloads = [p for route, p in self.calls if route == "chat/completions"]
        self.assertTrue(payloads)
        self.assertEqual(payloads[0]["max_tokens"], 4000)
        self.assertEqual(payloads[0]["reasoning"]["effort"], "none")

    def test_failure_checkpoints_first_draft_then_resumes(self):
        attempts = 0

        def fail_second(route, key, payload=None, *args):
            nonlocal attempts
            attempts += 1
            if attempts == 2:
                raise RuntimeError("temporary failure")
            return self.fake_api(route, key, payload)

        with self.assertRaises(RuntimeError):
            self.run_pipeline(["--mode", "dual-pass"], api=fail_second)
        self.assertEqual(len(self.checkpoint()["chunks"][0]["drafts"]), 1)
        self.calls.clear()
        self.run_pipeline(["--mode", "dual-pass", "--resume"])
        self.assertEqual(len(self.calls), 8)

    def test_invalid_reconciliation_is_checkpointed_and_retried(self):
        invalid = reconciliation()
        invalid["response"]["choices"][0]["message"]["content"] = (
            '{"text": "missing uncertainties"}'
        )
        attempts = 0

        def invalid_once(route, key, payload=None, *args):
            nonlocal attempts
            if route == "audio/transcriptions":
                return result()
            attempts += 1
            return invalid if attempts == 1 else reconciliation()

        self.run_pipeline(["--mode", "dual-pass"], api=invalid_once)
        state = self.checkpoint()
        self.assertEqual(len(state["chunks"][0]["reconciliation_attempts"]), 2)
        self.assertNotIn("reconciliation_error", state["chunks"][0])

    def test_dry_run_cannot_clobber_transcripts_or_read_key(self):
        self.run_pipeline()
        original = (self.out / "lecture.transcript.json").read_bytes()
        self.key.unlink()
        self.calls.clear()
        self.run_pipeline(["--dry-run"])
        self.assertEqual(original, (self.out / "lecture.transcript.json").read_bytes())
        self.assertEqual(self.calls, [])
        self.assertTrue((self.out / "lecture.plan.json").exists())

    def test_resume_rejects_changed_source_and_settings(self):
        self.run_pipeline()
        for extra in (
            ["--language", "en"],
            ["--model", "other/model"],
            ["--mode", "dual-pass"],
        ):
            with self.assertRaisesRegex(RuntimeError, "Resume mismatch"):
                self.run_pipeline(["--resume", *extra])
        with self.source.open("ab") as f:
            f.write(b"changed")
        with self.assertRaisesRegex(RuntimeError, "Resume mismatch"):
            self.run_pipeline(["--resume"])

    def test_refuses_overwrite_and_parallel_run(self):
        self.run_pipeline()
        with self.assertRaisesRegex(RuntimeError, "Output exists"):
            self.run_pipeline()
        (self.out / ".lecture.lock").touch()
        with self.assertRaisesRegex(RuntimeError, "Run lock exists"):
            self.run_pipeline(["--resume"])


if __name__ == "__main__":
    unittest.main()
