# automation — Lion Shorts (Bengali)

একই recurring লায়ন (**Lion**) চরিত্রের original ৭–৮ part গল্প, YouTube Shorts প্রথমে; পরে Instagram Reels।

## এখন কী আছে (Phase 0)

- `stories/lion/` — Character Bible, ৮-part arc, Part 1 (Hook, script, scene prompts, JSON)
- `scripts/pipeline.py` — episode validate + quota plan (কোনো network call নেই)
- `tests/` — unit tests
- `docs/manual-install/dry-run.yml` — manual dry-run workflow (GitHub App-এর `workflows` permission না থাকায় এটি `.github/workflows/`-এ যুক্ত হয়নি; নিচের নির্দেশ দেখুন)
- `docs/architecture.md` — service যাচাই, API count, quota guardrails
- `docs/setup.md` — secret names ও ফোন থেকে review-এর ধাপ

## দ্রুত চালানো

```bash
python3 -m unittest discover -s tests -v
python3 scripts/pipeline.py plan --episode stories/lion/part-01.json
```

## Free-first নীতি

- Gemini ও Cloudflare Workers AI free allowance-এর মধ্যে; quota শেষ হলে workflow থামবে, paid fallback নেই।
- Real API call, schedule ও public upload এখনো চালু নয়; প্রথমে private/unlisted test।
- কোনো API key repository-তে নেই; secret names ও setup `docs/setup.md`-তে।

Status ও পরিকল্পনা: `docs/architecture.md`।
