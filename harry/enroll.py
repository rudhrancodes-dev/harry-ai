"""Voice enrollment CLI.

Usage:
    python -m harry.enroll                # records 10 fresh samples
    python -m harry.enroll --samples 6    # fewer if you're in a hurry
    python -m harry.enroll --status       # check current enrolment

Run once. You'll be prompted to read a short prompt 10 times. Each sample
is ~4 seconds. The averaged voiceprint is saved to ~/.harry/voiceprint.npy
and Harry will from then on verify that the speaker is you before acting
on a request.
"""
from __future__ import annotations

import argparse
import sys
import tempfile
import time
import wave
from pathlib import Path

PROMPTS = [
    "Harry, what does the day look like?",
    "Harry, summarise the engineering sync from yesterday.",
    "Harry, dim the studio lights to forty percent.",
    "Hey Harry, book a 30 minute slot with Priya tomorrow.",
    "Harry, play something calm.",
    "Harry, take a screenshot and put it in my notes.",
    "Harry, what is on my agenda today?",
    "Harry, draft a status update for the team.",
    "Harry, send Priya the rollout document.",
    "Harry, set a 25 minute focus timer.",
]


def _record_one(seconds: int = 4) -> Path:
    import sounddevice as sd  # type: ignore
    import soundfile as sf    # type: ignore
    fs = 16000
    print(f"   recording {seconds} s... ", end="", flush=True)
    audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype="float32")
    sd.wait()
    print("done.")
    tmp = Path(tempfile.mkstemp(suffix=".wav")[1])
    sf.write(str(tmp), audio, fs)
    return tmp


def _record_one_fallback(seconds: int = 4) -> Path:
    """Falls back to system `rec`/`sox` if sounddevice isn't installed."""
    import shutil
    import subprocess
    tool = shutil.which("rec") or shutil.which("sox")
    if not tool:
        raise SystemExit(
            "Install one of:  pip install sounddevice soundfile  or  brew install sox")
    tmp = Path(tempfile.mkstemp(suffix=".wav")[1])
    cmd = [tool, "-q", "-d", "-r", "16000", "-c", "1", str(tmp),
           "trim", "0", str(seconds)]
    print(f"   recording {seconds} s via sox... ", end="", flush=True)
    subprocess.run(cmd, check=True)
    print("done.")
    return tmp


def _record_one_any(seconds: int) -> Path:
    try:
        return _record_one(seconds)
    except ImportError:
        return _record_one_fallback(seconds)


def main() -> int:
    parser = argparse.ArgumentParser(prog="harry-enroll")
    parser.add_argument("--samples", type=int, default=10)
    parser.add_argument("--seconds", type=int, default=4)
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()

    from harry.voice.speaker_id import PROFILE_PATH, SpeakerID
    sid = SpeakerID()

    if args.status:
        print(f"resemblyzer available: {sid.enabled}")
        print(f"enrolled: {sid.enrolled}")
        print(f"profile path: {PROFILE_PATH}")
        return 0

    if not sid.enabled:
        print("resemblyzer is not installed.\n"
              "Install it with:  pip install resemblyzer\n"
              "(this also pulls torch ~150 MB)", file=sys.stderr)
        return 1

    print("\nVoice enrollment — speak each prompt in your natural voice.")
    print(f"Recording {args.samples} samples of {args.seconds} s each.\n")

    paths: list[Path] = []
    for i in range(args.samples):
        prompt = PROMPTS[i % len(PROMPTS)]
        print(f"[{i + 1:2d}/{args.samples}]  >  {prompt}")
        time.sleep(0.4)
        paths.append(_record_one_any(args.seconds))

    print("\nComputing voiceprint...")
    norm = sid.enrol_from_wavs(paths)
    for p in paths:
        try: p.unlink()
        except OSError: pass

    print(f"\n✓ Voiceprint saved to {PROFILE_PATH}")
    print(f"  embedding norm: {norm:.3f}")
    print(f"  threshold:      {sid.threshold}")
    print("\nDone. Harry will now verify it is you before acting on requests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
