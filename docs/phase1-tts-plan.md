# Phase 1 — Bangla TTS Plan (dry-run ভিত্তিক)

> Status: **Planning only.** কোনো real API call করা হয়নি। Real call-এর আগে মালিকের স্পষ্ট অনুমতি লাগবে।
> যাচাইয়ের তারিখ: 2026-10-10

## 1. যাচাই করা তথ্য

| বিষয় | ফলাফল | Source |
|---|---|---|
| Bangla ভাষা সমর্থন | ✅ `Gemini 3.8 Flash TTS` ও `Gemini 3.8 Flash-Lite TTS` দুটিতেই "Bangla" তালিকায় আছে | https://ai.google.dev/gemini-api/docs/speech-generation (Supported languages) |
| Gemini 3.8 Flash TTS free tier | ✅ Official pricing-এ Free Tier: input ও output "Free of charge" | https://ai.google.dev/gemini-api/docs/pricing (Gemini 3.8 Flash TTS) |
| Gemini 3.8 Flash-Lite TTS free tier | ❌ Free Tier "Not available" | একই pricing page |
| Free tier-এর data ব্যবহার | ⚠️ "Used to improve our products: Yes" | একই pricing page |
| Output format (unary) | WAV, 24 kHz, mono, 16-bit PCM | speech-generation docs |
| Pricing তারিখ-সংবেদনশীল | ⚠️ Paid tier price 2026-12-31 পর্যন্ত আলাদা; Free tier-এর quota project অনুযায়ী বদলাতে পারে | pricing page |

**যা এখনো যাচাই হয়নি:** Bangla উচ্চারণ ও স্বাভাবিকতার মান। Docs ভাষাটি তালিকায় রেখেছে, কিন্তু গুণমান যাচাই হয়নি। এটি AI Studio-তে শুনে যাচাই করতে হবে।

## 2. Model ও voice নির্বাচন

- **Primary:** `gemini-3.8-flash-tts` (Free tier আছে, Bangla সমর্থিত)।
- **Fallback নয়:** `gemini-3.8-flash-lite-tts` — free tier নেই, তাই ব্যবহার করা হবে না।
- Voice: prebuilt voice (উদাহরণ `Kore` docs-এ আছে)। Bangla-এর জন্য কোন voice ভালো লাগে তা AI Studio-তে নিজে শুনে বাছতে হবে। Voice নাম এখনো নির্ধারিত নয়।

## 3. Test ধাপ (real API call-এর আগে বা অনুমতি পাওয়ার পরে)

1. **Manual test (AI Studio, মালিক নিজে):** [aistudio.google.com/generate-speech](https://aistudio.google.com/generate-speech)-এ `part-01.json`-এর scene 1–2 বাংলা text দিয়ে ৩–৪টি voice শুনুন।
2. **Quality check:** উচ্চারণ, বাক্য শেষের intonation, নাম (লায়ন, দিদা, টিক) ঠিক আছে কি না।
3. **Automated test (অনুমতির পরে):** একটি scene-এর WAV তৈরি, duration মাপা, ফাইল `.gitignore`-এ থাকা `out/`-এ যাবে।

## 4. Dry-run ধাপ (বর্তমান কোডে সম্ভব)

- `scripts/pipeline.py plan` ইতিমধ্যে `network_calls: 0` দেখায়।
- পরবর্তী ধাপ: `tts-plan` কমান্ড যোগ করা, যা প্রতিটি scene-এর narration-এর character count ও আনুমানিক token সংখ্যা হিসাব করবে। কোনো API call হবে না।
- Free tier quota-র জন্য প্রতি episode-এর টেক্সট দৈর্ঘ্যের হিসাব রাখা হবে, এবং quota-র কাছাকাছি গেলে run থামবে।

## 5. Guardrail

- Quota শেষ বা rate-limit error হলে clean stop ও log; paid fallback নয়।
- Real call-এর আগে মালিকের স্পষ্ট অনুমতি।
- API key শুধু GitHub Actions Secrets `GEMINI_API_KEY`-এ; chat বা repo-তে নয়।
- Public upload-এর আগে সবসময় private/unlisted test।

## 6. পরের ধাপ (অনুমতির পর)

1. মালিক AI Studio-তে Bangla voice শুনে একটি voice বাছবে।
2. আমি `tts-plan` dry-run যোগ করব।
3. মালিক অনুমতি দিলে একটি scene-এর real TTS test হবে।
4. Real test সফল হলে পরের ধাপ: image generation (আলাদা অনুমতি)।
