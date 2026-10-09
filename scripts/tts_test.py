#!/usr/bin/env python3
"""Single-scene Bangla TTS test for the Lion series.

Default: DRY RUN. Prints the request plan and makes NO network call.
Real call only when BOTH --execute is passed AND env CONFIRM_TTS=yes is set,
and GEMINI_API_KEY is present in the environment (GitHub Actions Secret).

Model: gemini-3.8-flash-tts (free tier per Google pricing page, checked 2026-10-10).
Bangla is listed in the speech-generation supported languages.
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
DEFAULT_VOICE = "Kore"          # prebuilt docs example; Bangla voice still to be chosen by listening
MAX_CHARS_PER_CALL = 1500       # per-call limit in the tool contract used for this project


def load_scene(episode_path: str, scene_id: int) -> dict:
    ep = json.loads(Path(episode_path).read_text(encoding="utf-8"))
    for scene in ep["scenes"]:
        if scene["id"] == scene_id:
            return scene
    raise SystemExit(f"scene {scene_id} not found in {episode_path}")


def build_body(text: str, voice: str, style: str) -> dict:
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


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--episode", default=str(ROOT / "stories/lion/part-01.json"))
    p.add_argument("--scene", type=int, default=1)
    p.add_argument("--voice", default=DEFAULT_VOICE)
    p.add_argument("--style", default="calm, slightly urgent, storytelling")
    p.add_argument("--out", default="out/lion-p01-s01.wav")
    p.add_argument("--execute", action="store_true")
    args = p.parse_args(argv)

    scene = load_scene(args.episode, args.scene)
    text = scene["narration_bn"]
    if len(text) > MAX_CHARS_PER_CALL:
        print(json.dumps({"error": "text too long for one call"}, ensure_ascii=False))
        return 1

    plan = {
        "model": MODEL,
        "scene": args.scene,
        "chars": len(text),
        "voice": args.voice,
        "output": args.out,
        "network_calls": 0,
        "mode": "dry-run",
    }

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
        # Quota/rate-limit: stop cleanly, no fallback.
        print(json.dumps({**plan, "mode": "execute", "http_status": e.code,
                          "stop": "clean stop; no paid fallback"}, ensure_ascii=False, indent=2))
        return 2

    audio_b64 = (data.get("output_audio") or {}).get("data")
    if not audio_b64:
        print(json.dumps({**plan, "mode": "execute", "error": "no audio in response"}, ensure_ascii=False))
        return 3
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(audio_b64))
    print(json.dumps({**plan, "mode": "execute", "bytes": out.stat().st_size}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
