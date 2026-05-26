"""Speaker verification — is this Rudhran speaking?

Uses Resemblyzer (a lightweight neural voice-encoder, ~150 MB model). The
profile lives at ~/.harry/voiceprint.npy as a single 256-d float vector.
Verification computes cosine similarity to the stored vector.

This module gracefully degrades when resemblyzer or its torch dep are not
installed — verify() returns True in that mode so the rest of the system
keeps working. The Settings UI surfaces enrolment status so you know.
"""
from __future__ import annotations

import os
from pathlib import Path

PROFILE_PATH = Path.home() / ".harry" / "voiceprint.npy"
DEFAULT_THRESHOLD = float(os.getenv("HARRY_SPEAKER_THRESHOLD", "0.78"))


def _try_import():
    try:
        import numpy as np
        from resemblyzer import VoiceEncoder, preprocess_wav
        return np, VoiceEncoder, preprocess_wav
    except Exception:
        return None, None, None


class SpeakerID:
    def __init__(self, threshold: float = DEFAULT_THRESHOLD) -> None:
        self.threshold = threshold
        self._np, self._VoiceEncoder, self._preprocess = _try_import()
        self._encoder = None
        self._profile = None
        if self._VoiceEncoder and PROFILE_PATH.exists():
            self._encoder = self._VoiceEncoder(verbose=False)
            self._profile = self._np.load(PROFILE_PATH)

    @property
    def enabled(self) -> bool:
        return self._VoiceEncoder is not None

    @property
    def enrolled(self) -> bool:
        return self._profile is not None

    def verify_wav(self, wav_path: str | Path) -> tuple[bool, float]:
        """Returns (accept, similarity). Accepts when disabled or unenrolled
        — security is opt-in, not default-on."""
        if not self.enabled or not self.enrolled:
            return True, 1.0
        wav = self._preprocess(str(wav_path))
        emb = self._encoder.embed_utterance(wav)
        sim = float(self._np.dot(emb, self._profile) /
                    (self._np.linalg.norm(emb) * self._np.linalg.norm(self._profile)))
        return sim >= self.threshold, sim

    def enrol_from_wavs(self, wav_paths: list[str | Path]) -> float:
        if not self.enabled:
            raise RuntimeError(
                "resemblyzer not installed. Add it to requirements and reinstall.")
        encoder = self._VoiceEncoder(verbose=False)
        embeddings = []
        for p in wav_paths:
            wav = self._preprocess(str(p))
            embeddings.append(encoder.embed_utterance(wav))
        profile = self._np.mean(self._np.stack(embeddings), axis=0)
        PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._np.save(PROFILE_PATH, profile)
        self._encoder = encoder
        self._profile = profile
        return float(self._np.linalg.norm(profile))
