# Setup Guide

## 1. Local dry-run (কোনো key লাগে না)

```bash
python3 -m unittest discover -s tests -v
python3 scripts/pipeline.py validate --episode stories/lion/part-01.json
python3 scripts/pipeline.py plan --episode stories/lion/part-01.json
```

`plan` কোনো network call করে না; শুধু episode validate করে এবং quota estimate দেখায়।

## 2. GitHub Actions — secret names (values কখনো commit বা chat-এ দেবেন না)

Repository → **Settings → Secrets and variables → Actions**

| নাম | ধরন | কখন লাগবে |
|---|---|---|
| `GEMINI_API_KEY` | Secret | Phase 1: script/TTS |
| `CLOUDFLARE_ACCOUNT_ID` | Secret | Phase 1: image |
| `CLOUDFLARE_API_TOKEN` | Secret | Phase 1: image (Workers AI permission সীমিত রাখুন) |
| `NEURONS_PER_IMAGE` | **Variable** (secret নয়) | Docs/dashboard থেকে যাচাই করে সেট করার পর real run-এর জন্য |

Phase 2-এ YouTube-এর জন্য আলাদা OAuth client secrets লাগবে; তখন নতুন নাম যোগ হবে।

## 3. Workflow চালানো

- **Actions → dry-run → Run workflow**: এখন শুধু test + plan চলে; কোনো secret লাগে না।
- Phase 1-এর real generation workflow শুধু `workflow_dispatch`-এ চলবে, schedule থাকবে না, প্রথমে quota guard ও আপনার confirmation লাগবে।

## 4. ফোন থেকে review

1. GitHub app/browser → repo → **Actions** → run খুলুন।
2. Summary/log-এ validate ও plan output দেখুন।
3. Phase 1-এর পরে MP4 **artifact** নামানো যাবে (retention ছোট রাখা হবে, ৭ দিন)। ফোনে download করে YouTube Studio-তে **private/unlisted** হিসেবে upload করুন।

## 5. Public repo সতর্কতা

এই repository public। কোনো `.env`, key, token, বা generated MP4 commit করবেন না। `.gitignore` এগুলো ignore করে, তবুও commit-এর আগে `git status` দেখুন।
