#!/usr/bin/env python3
"""Bangla TTS for the Lion series.

--scene N : one scene per call.
--all     : whole episode in ONE call (keeps the voice consistent).

Default: DRY RUN, no network call.
Real call only with --execute AND CONFIRM_TTS=yes AND GEMINI_API_KEY set.
"""
import argparse
import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = "gemini-3.8-flash-tts"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
DEFAULT_VOICE = "Kore"
MAX_CHARS_PER_CALL = 1500


def load_episode(episode_path):
    return json.loads(Path(episode_path).read_text(encoding="utf-8"))


def build_body(text, voice, style):
    return {
        "model": MODEL,
        "input": [{
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": text,
                "annotations": [{"type": "speech_metadata", "style": style}],
            }],
        }],
        "response_format": {"type": "audio"},
        "generation_config": {"speech_config": [{"voice": voice}]},
    }


def find_audio(obj):
    """Search the whole response for base64 audio, wherever it sits."""
    if isinstance(obj, dict):
        data = obj.get("data")
        if isinstance(data, str) and (obj.get("type") == "audio"
                                      or "audio" in str(obj.get("mime_type", ""))):
            return data
        oa = obj.get("output_audio")
        if isinstance(oa, dict) and isinstance(oa.get("data"), str):
            return oa["data"]
        for v in obj.values():
            found = find_audio(v)
            if found:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = find_audio(v)
            if found:
                return found
    return None


def shape(obj, depth=0):
    """Structure only: keys and types. Long strings (audio) are never printed."""
    if depth > 5:
        return "..."
    if isinstance(obj, dict):
        return {k: shape(v, depth + 1) for k, v in obj.items()}
    if isinstance(obj, list):
        return [shape(obj[0], depth + 1)] if obj else []
    if isinstance(obj, str):
        return f"str(len={len(obj)})"
    return type(obj).__name__


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--episode", default=str(ROOT / "stories/lion/part-01.json"))
    p.add_argument("--scene", type=int, default=1)
    p.add_argument("--all", action="store_true")
    p.add_argument("--voice", default=DEFAULT_VOICE)
    p.add_argument("--style", default="calm, slightly urgent, storytelling")
    p.add_argument("--execute", action="store_true")
    args = p.parse_args(argv)

    ep = load_episode(args.episode)
    if args.all:
        text = " ".join(s["narration_bn"] for s in ep["scenes"])
        label = "all"
    else:
        matches = [s for s in ep["scenes"] if s["id"] == args.scene]
        if not matches:
            print(json.dumps({"error": f"scene {args.scene} not found"}, ensure_ascii=False))
            return 1
        text = matches[0]["narration_bn"]
        label = f"s{args.scene:02d}"

    if len(text) > MAX_CHARS_PER_CALL:
        print(json.dumps({"error": "text too long for one call", "chars": len(text)},
                         ensure_ascii=False))
        return 1

    out = Path(f"out/lion-p01-{label}.wav")
    plan = {"model": MODEL, "part": label, "chars": len(text),
            "voice": args.voice, "output": str(out), "network_calls": 0, "mode": "dry-run"}

    if not args.execute:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0

    key = os.environ.get("GEMINI_API_KEY", "")
    if os.environ.get("CONFIRM_TTS") != "yes" or not key:
        print(json.dumps({**plan, "error": "refused: CONFIRM_TTS=yes and GEMINI_API_KEY required"},
                         ensure_ascii=False, indent=2))
        return 1

    body = json.dumps(build_body(text, args.voice, args.style)).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=body, method="POST", headers={
        "Content-Type": "application/json", "x-goog-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(json.dumps({**plan, "mode": "execute", "http_status": e.code,
                          "stop": "clean stop; no paid fallback"}, ensure_ascii=False, indent=2))
        return 2

    audio_b64 = find_audio(data)
    if not audio_b64:
        print(json.dumps({**plan, "mode": "execute", "error": "no audio found",
                          "response_shape": shape(data)}, ensure_ascii=False, indent=2))
        return 3

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(audio_b64))
    print(json.dumps({**plan, "mode": "execute", "bytes": out.stat().st_size},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
