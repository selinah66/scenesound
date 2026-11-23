"""Offline API-contract tests; these do not spend credits."""

import unittest
from unittest.mock import Mock, patch

import requests

from mvp.audio import (
    StableAudioError,
    fetch_audio_result,
    start_audio_generation,
    wait_for_audio,
)


JOB_ID = "a" * 64


def response(status, *, payload=None, content=b"", content_type="application/json"):
    return Mock(
        status_code=status,
        content=content,
        headers={"Content-Type": content_type},
        json=Mock(return_value=payload),
    )


class AudioTests(unittest.TestCase):
    @patch("mvp.audio.requests.post")
    def test_submit_sends_edited_prompt_and_duration_as_multipart(self, post):
        post.return_value = response(202, payload={"id": JOB_ID})
        self.assertEqual(start_audio_generation(" Edited prompt ", 10, "key"), JOB_ID)
        kwargs = post.call_args.kwargs
        self.assertEqual(kwargs["files"]["prompt"], (None, "Edited prompt"))
        self.assertEqual(kwargs["files"]["duration"], (None, "10"))
        self.assertEqual(kwargs["files"]["output_format"], (None, "mp3"))
        self.assertEqual(kwargs["files"]["model"], (None, "stable-audio-3"))
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer key")
        self.assertFalse(kwargs["allow_redirects"])
        self.assertEqual(post.call_count, 1)

    @patch("mvp.audio.requests.post")
    def test_invalid_inputs_never_submit(self, post):
        for prompt, duration, key in [
            (" ", 10, "key"), ("x" * 10001, 10, "key"),
            ("rain", 0, "key"), ("rain", 381, "key"),
            ("rain", float("nan"), "key"), ("rain", True, "key"),
            ("rain", 10, ""),
        ]:
            with self.subTest(duration=duration), self.assertRaises(ValueError):
                start_audio_generation(prompt, duration, key)
        post.assert_not_called()

    @patch("mvp.audio.requests.post")
    def test_post_timeout_is_not_retried(self, post):
        post.side_effect = requests.Timeout("secret-key")
        with self.assertRaises(StableAudioError) as caught:
            start_audio_generation("rain", 10, "key")
        self.assertIn("may have been accepted", str(caught.exception))
        self.assertNotIn("secret-key", str(caught.exception))
        self.assertEqual(post.call_count, 1)

    @patch("mvp.audio.requests.post")
    def test_malformed_acceptance_does_not_resubmit(self, post):
        post.return_value = response(202, payload={})
        with self.assertRaises(StableAudioError):
            start_audio_generation("rain", 10, "key")
        self.assertEqual(post.call_count, 1)

    @patch("mvp.audio.requests.post")
    def test_submission_errors_have_safe_status(self, post):
        for status in (400, 401, 402, 403, 429, 500):
            post.return_value = response(status, payload={"errors": ["secret-key"]})
            with self.subTest(status=status), self.assertRaises(StableAudioError) as caught:
                start_audio_generation("rain", 10, "key")
            self.assertEqual(caught.exception.status_code, status)
            self.assertNotIn("secret-key", str(caught.exception))

    @patch("mvp.audio.requests.post")
    @patch("mvp.audio.requests.get")
    def test_pending_check_never_submits(self, get, post):
        get.return_value = response(202)
        self.assertIsNone(fetch_audio_result(JOB_ID, "key"))
        self.assertTrue(get.call_args.args[0].endswith(JOB_ID))
        post.assert_not_called()

    @patch("mvp.audio.requests.get")
    def test_completed_check_returns_bytes(self, get):
        get.return_value = response(200, content=b"ID3-audio", content_type="audio/mpeg")
        self.assertEqual(fetch_audio_result(JOB_ID, "key"), b"ID3-audio")

    @patch("mvp.audio.requests.get")
    def test_empty_or_non_audio_success_is_rejected(self, get):
        for content, content_type in [(b"", "audio/mpeg"), (b"{}", "application/json")]:
            get.return_value = response(200, content=content, content_type=content_type)
            with self.assertRaises(StableAudioError):
                fetch_audio_result(JOB_ID, "key")

    @patch("mvp.audio.requests.get")
    def test_invalid_job_id_never_makes_request(self, get):
        with self.assertRaises(ValueError):
            fetch_audio_result("../other-endpoint", "key")
        get.assert_not_called()

    @patch("mvp.audio.requests.get")
    def test_expired_and_rate_limited_checks_preserve_error_status(self, get):
        for status in (404, 429, 500):
            get.return_value = response(status)
            with self.assertRaises(StableAudioError) as caught:
                fetch_audio_result(JOB_ID, "key")
            self.assertEqual(caught.exception.status_code, status)

    @patch("mvp.audio.requests.get", side_effect=requests.Timeout)
    def test_get_timeout_can_be_checked_again(self, get):
        with self.assertRaisesRegex(StableAudioError, "Keep the generation ID"):
            fetch_audio_result(JOB_ID, "key")

    @patch("mvp.audio.time.sleep")
    @patch("mvp.audio.fetch_audio_result", side_effect=[None, b"audio"])
    def test_optional_polling_waits_then_returns(self, fetch, sleep):
        self.assertEqual(wait_for_audio(JOB_ID, "key"), b"audio")
        self.assertEqual(fetch.call_count, 2)
        sleep.assert_called_once()

    @patch("mvp.audio.time.sleep")
    @patch("mvp.audio.time.monotonic", side_effect=[0, 0, 0, 11])
    @patch("mvp.audio.fetch_audio_result", return_value=None)
    def test_wait_timeout_never_submits_new_job(self, fetch, clock, sleep):
        with self.assertRaisesRegex(TimeoutError, "same generation ID"):
            wait_for_audio(JOB_ID, "key", timeout_seconds=10)
        self.assertEqual(fetch.call_count, 1)

    def test_invalid_wait_settings(self):
        for value in (0, -1, float("inf"), True):
            with self.assertRaises(ValueError):
                wait_for_audio(JOB_ID, "key", timeout_seconds=value)


if __name__ == "__main__":
    unittest.main()
