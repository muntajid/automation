#!/usr/bin/env python3
"""Lion shorts pipeline — dry-run-first planner.

Phase 0 scope: validate an episode JSON and estimate Workers AI quota.
This script makes NO network calls and needs NO API keys.

Usage:
  python3 scripts/pipeline.py validate --episode stories/lion/part-01.json
  python3 scripts/pipeline.py plan     --episode stories/lion/part-01.json

Env:
  NEURONS_PER_IMAGE  Verified Workers AI neuron cost per image (not yet verified -> real run blocked).
  NEURON_SAFETY      Fraction of the 10,000/day allowance to use (default 0.8).
"""
import argparse
import json
import os
import sys
from pathlib import Path

DAILY_NEURONS = 10_000          # Workers Free allowance, resets 00:00 UTC (Cloudflare pricing docs)
DEFAULT_SAFETY = 0.8
MAX_SCENES = 12
MAX_TOTAL_SECONDS = 60          # YouTube Shorts length target
REQUIRED_TOP = ("series", "episode", "title", "hook", "scenes", "cliffhanger")
REQUIRED_SCENE = ("id", "seconds", "narration_bn", "image_prompt")


def load_episode(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate(ep: dict) -> list:
    errors = []
    for key in REQUIRED_TOP:
        if key not in ep:
            errors.append(f"missing top-level key: {key}")
    if errors:
        return errors

    if not isinstance(ep["episode"], int) or not 1 <= ep["episode"] <= 8:
        errors.append("episode must be an integer 1..8")

    hook = ep["hook"]
    if not hook.get("text"):
        errors.append("hook.text is required")
    if not isinstance(hook.get("seconds"), (int, float)) or hook["seconds"] > 2:
        errors.append("hook.seconds must be <= 2 (Hook must land in first 1-2 seconds)")

    scenes = ep["scenes"]
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= MAX_SCENES:
        errors.append(f"scenes must be a list of 1..{MAX_SCENES} items")
        return errors

    total = 0.0
    for scene in scenes:
        sid = scene.get("id", "?")
        for key in REQUIRED_SCENE:
            if key not in scene:
                errors.append(f"scene {sid} missing key: {key}")
        total += float(scene.get("seconds", 0) or 0)
    if total > MAX_TOTAL_SECONDS:
        errors.append(f"total duration {total}s exceeds {MAX_TOTAL_SECONDS}s")

    if not ep["cliffhanger"].get("text"):
        errors.append("cliffhanger.text is required")
    return errors


def quota_plan(ep: dict, neurons_per_image, safety: float = DEFAULT_SAFETY) -> dict:
    images = sum(1 for s in ep["scenes"] if s.get("image_prompt"))
    budget = DAILY_NEURONS * safety
    result = {"images": images, "daily_allowance": DAILY_NEURONS, "safety_fraction": safety,
              "budget_neurons": budget}
    if neurons_per_image is None:
        result.update(status="blocked",
                      reason="NEURONS_PER_IMAGE not verified; real image generation stays blocked")
        return result
    estimate = images * neurons_per_image
    result.update(neurons_per_image=neurons_per_image, estimated_neurons=estimate,
                  status="ok" if estimate <= budget else "over_budget")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["validate", "plan"])
    parser.add_argument("--episode", required=True)
    args = parser.parse_args(argv)

    ep = load_episode(args.episode)
    errors = validate(ep)
    if args.command == "validate":
        print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
        return 1 if errors else 0

    if errors:
        print(json.dumps({"valid": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1

    raw = os.environ.get("NEURONS_PER_IMAGE", "").strip()
    try:
        neurons = float(raw) if raw else None
    except ValueError:
        print(json.dumps({"valid": True, "errors": [], "error": "NEURONS_PER_IMAGE is not a number"}))
        return 1
    safety = float(os.environ.get("NEURON_SAFETY", DEFAULT_SAFETY))
    plan = {"valid": True, "series": ep["series"], "episode": ep["episode"], "title": ep["title"],
            "scenes": len(ep["scenes"]), "quota": quota_plan(ep, neurons, safety),
            "network_calls": 0}
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
