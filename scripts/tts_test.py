#!/usr/bin/env python3
"""Single-scene Bangla TTS test for the Lion series.

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


def load_scene(episode_path, scene_id):
    ep = json.loads(Path(episode_path).read_text(encoding="utf-8"))
    for scene in ep["scenes"]:
        if scene["id"] == scene_id:
            return scene
    raise SystemExit(f"scene {scene_id} not found in {episode_path}")


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

    plan = {"model": MODEL, "scene": args.scene, "chars": len(text),
            "voice": args.voice, "output": args.out, "network_calls": 0, "mode": "dry-run"}

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
        # Print structure only, so the next run shows where audio really is.
        print(json.dumps({**plan, "mode": "execute", "error": "no audio found",
                          "response_shape": shape(data)}, ensure_ascii=False, indent=2))
        return 3

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(audio_b64))
    print(json.dumps({**plan, "mode": "execute", "bytes": out.stat().st_size},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
