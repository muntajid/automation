# Architecture ও Free-Quota Guardrails

> Project: Bengali short-form video (Lion series), 7–8 part, YouTube Shorts প্রথমে; Instagram Reels পরে।
> Status: **Phase 0 — planning + dry-run scaffold।** কোনো real API call, public upload বা paid service এখনো যুক্ত হয়নি।

## 1. Service যাচাই (যাচাইয়ের তারিখ: 2026-10-09)

| Service | কাজ | Free অবস্থা | যাচাই | Status |
|---|---|---|---|---|
| Gemini Developer API — text (script/outline) | Story bible, outline, Hook, script | Flash/Flash-Lite text-এর free tier আছে; quota project অনুযায়ী ও পরিবর্তনশীল | Google official pricing: https://ai.google.dev/gemini-api/docs/pricing | ✅ free আছে, quota AI Studio-তে যাচাই করতে হবে |
| Gemini 3.8 Flash TTS | Bangla voiceover (candidate) | Official pricing table-এ Free Tier "Free of charge" লেখা | https://ai.google.dev/gemini-api/docs/pricing (Gemini 3.8 Flash TTS section) | ✅ free tier listed; Bangla quality ও language support test করতে হবে |
| Gemini 3.8 Flash-Lite TTS | TTS বিকল্প | Free Tier "Not available" | একই page | ❌ free নয় — ব্যবহার করা যাবে না |
| Cloudflare Workers AI | Scene image | ১০,০০০ Neurons/দিন (Workers Free), reset 00:00 UTC; বেশি হলে request ব্যর্থ, billing হয় না | https://developers.cloudflare.com/workers-ai/platform/pricing/ | ✅ free allocation আছে |
| FLUX.2 dev (`@cf/black-forest-labs/flux-2-dev`) | Multi-reference lion image | Model page আছে, partner model; **per-image neuron cost ও free eligibility এখনো যাচাই বাকি** | https://developers.cloudflare.com/workers-ai/models/flux-2-dev/ | ⚠️ uncertain |
| FFmpeg | Still image → pan/zoom, audio, caption, 9:16 render | API নয়, open source | — | ✅ (local/Actions-এ চালানো) |
| GitHub Actions | Cloud run, manual dispatch, artifact | Repo public হলে standard GitHub-hosted runner minutes free; artifact storage-এর নিয়ম যাচাই বাকি | https://docs.github.com/billing/managing-billing-for-github-actions/about-billing-for-github-actions | ✅ public repo-তে free (standard runner) |
| YouTube Data API v3 + OAuth | Auto-upload | Phase 2-এ যাচাই | — | ⏸ এখন নয় |
| Instagram/Meta publishing | Auto-publish | Phase 3-এ যাচাই | — | ⏸ এখন নয় |
| Tavily | Real-world research | Fiction-এর জন্য দরকার নেই (optional) | — | ⏸ optional |
| Pexels | Stock footage | Recurring lion-এর প্রধান visual হিসেবে ব্যবহার করা হবে না | — | ❌ primary নয় |

**সতর্কতা:** Gemini free tier-এ ব্যবহৃত data Google product উন্নয়নে ব্যবহৃত হতে পারে (pricing table-এ "Used to improve our products: Yes")। Story draft-এ personal/sensitive তথ্য দেবেন না।

## 2. API Integration count

- Fictional story + manual YouTube upload: Gemini + Cloudflare = **২টি core API**
- YouTube auto-upload যোগ হলে: **৩টি** (YouTube Data API v3 + OAuth)
- YouTube + Instagram auto-publish: **৪টি**
- Real-world research যোগ হলে Tavily optional **+১টি**
- FFmpeg ও GitHub Actions API count-এ নেই।

## 3. Pipeline (planned)

```
episode JSON ──► validate ──► quota guard ──► [Phase 1] TTS ─► image gen ─► FFmpeg render ─► MP4 artifact
                                                     │
                                  dry-run: শুধু validate + plan, কোনো API call নয়
```

বর্তমান কোডে আছে: `validate` ও `plan` (dry-run)। TTS, image generation, FFmpeg render ও upload Phase 1–2-এ যোগ হবে।

## 4. Quota guardrails

- Cloudflare daily budget: `10,000` Neurons। Code-এর default safety margin `80%` → কার্যকর budget `8,000`।
- `NEURONS_PER_IMAGE` **verify না হওয়া পর্যন্ত real run blocked থাকবে** (`status: blocked`)। এটি official docs/dashboard থেকে যাচাই করে Repository Variable হিসেবে সেট করুন।
- Quota শেষ হলে workflow clean stop করবে; paid fallback, auto-upgrade বা billing নেই।
- Gemini quota বা rate-limit error এলে retry সীমিত রাখবে এবং log করে থামবে।
- Public upload সবসময় **private/unlisted** দিয়ে শুরু; public শুধু আপনার লিখিত confirmation-এর পরে।

## 5. Cost-safety ও content নীতি

- Recurring lion-এর appearance **শতভাগ এক থাকবে** — এই নিশ্চয়তা নেই; reference/seed ব্যবহার করার আগে ছোট test করতে হবে।
- প্রতিটি part-এ নতুন original plot ও progression থাকবে; একই template-এ শুধু শব্দ বদলে mass-produce করা হবে না।
- Fiction হলে factual lesson জোর করে ঢোকানো হবে না।
- Reference Reel-এর plot, dialogue, visuals বা scene sequence ব্যবহার করা হয়নি; এটি শুধু episodic cliffhanger style-এর ধারণা।
