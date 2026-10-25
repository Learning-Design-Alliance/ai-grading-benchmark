# What the vendors document

Each model's licence, size, training cutoff and data, and the evaluations its own card reports, from primary
sources read on 2026-10-25. The machine-readable summary the report uses is `models.json`. A vendor's claim
is printed beside the benchmark's measurement, never in place of it.

**What the cards show, across all 17 models:**
- **No card evaluates education or grading.** Gemma and Olmo list education as an intended use only.
- **Sycophancy** is reported by Anthropic only, qualitatively. Our pushback test measures it directly. Opus
  5.5 holds; Fable 5.1 and Haiku 5.5, whose cards say they improved, still give way by 3.5-3.7% of the scale.
- **Prompt injection** is reported by Anthropic and OpenAI for coding, browsing and tool use, not for
  instructions inside the work being judged. That is the gaming probe here.
- **Energy:** only Meta discloses training energy and carbon (Llama 3.2). No vendor discloses inference
  energy or water.
- **Training data** is described, not released, for every model on the board. Olmo, the candidate, releases
  all of it, so contamination can be checked directly.
- **Transparency** (Stanford's Foundation Model Transparency Index, December 2025): Anthropic 46, Google
  41, OpenAI 35, DeepSeek 32, Meta 31, Alibaba 26, Mistral 18, against a mean of 40.69.

The survey below was compiled by an agent from the primary sources it lists, and spot-checked by the
maintainers' agent (the retention page, the Gemma 4 licence, the FMTI scores). Values marked
**unverified** could not be confirmed.

## Model table

| model | weights | licence (conditions) | params | cutoff | training data | card (URL, date) | sycophancy eval | injection eval | bias eval | education use | energy disclosure | retention options |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| anthropic/claude-opus-5.5 | closed | Proprietary; API under Anthropic Commercial Terms and Usage Policy (https://www.anthropic.com/legal/aup) | not disclosed | June 2026 (card p.11) | description only: "proprietary mix of publicly available information from the internet, public and private datasets, user data … [opt-in], … synthetic data" (p.11) | https://www.anthropic.com/claude-opus-5-5-system-card, 22 Sep 2026 | Reported (automated behavioural audit, figure only, no single number): "strongest tested model or is tied … on most metrics related to honesty" (§6.4.3, p.110–111) | Reported: "Prompt injection probes reduce Claude Opus 5.5's overall attack success rate to 11.13%" (Shade coding, p.88). Most successful attacks came via fallback-model responses | BBQ (p.76): disambiguated accuracy 89.65%, ambiguous 99.99%; bias −0.93% / 0.01% | not reported | none | Default: API inputs/outputs deleted within 30 days (https://privacy.claude.com/en/articles/7996866). ZDR available by arrangement through sales (https://platform.claude.com/docs/en/manage-claude/api-and-data-retention) |
| anthropic/claude-fable-5.1 | closed | Proprietary; as above. Classed as a "Covered Model" | not disclosed | June 2026 (p.11) | description only (p.11) | https://www.anthropic.com/claude-fable-5-1-mythos-5-1-system-card, 1 Sep 2026 (joint card with Mythos 5.1) | Reported, qualitative: Mythos 5.1 [same model] "is less sycophantic to the user overall" (§6.4.4, p.111) | Reported: coding, with probes, "bringing Fable 5.1 to 12.80%" (p.87); computer use, attempt-level ASR 0.07% (Table 5.2.2.2.A, p.87). **Discrepancy:** the Opus 5.5 card (p.88) gives Fable 5.1 8.70% with probes | BBQ (Mythos 5.1, p.73–74): accuracy 89.9% / 100%; bias −0.91% / 0.03% | not reported | none | **ZDR not available:** "require 30-day data retention and are not available under ZDR unless expressly authorized" (platform.claude.com retention page) |
| anthropic/claude-haiku-5.5 | closed | Proprietary; as above | not disclosed | June 2026 (p.8) | description only (p.8) | https://www.anthropic.com/claude-haiku-5-5-system-card, 7 Oct 2026 (condensed card) | Reported, qualitative: "improved on Claude Haiku 4.5 on every honesty-related metric" [includes sycophancy] (§6.2.3, p.65–66) | Reported: coding ASR "0.08% over all attempts without prompt injection probes"; with probes, no attack succeeded (p.52) | BBQ (p.43–44): accuracy 55.56% / 99.65%; bias +1.67% / 0.27%. Low disambiguated accuracy is mostly "cannot be determined" answers | not reported | none | Same as Opus 5.5: 30-day default, ZDR on request |
| openai/gpt-6-astra | closed | Proprietary; OpenAI Services Agreement and Usage Policies (openai.com/policies; 403 to automated fetch, not opened) | not disclosed | 30 Apr 2026 (https://developers.openai.com/api/docs/models/gpt-6-astra) | description only: "trained on diverse datasets and filtered … to reduce personal information" (§2) | https://deploymentsafety.openai.com/gpt-6-astra, published 3 Sep 2026 (changelog to 29 Sep 2026) | not reported | Reported (§5.2): indirect-PI defender success "climbed from 96.23% to 99.79%"; instruction hierarchy 99.99%; Gray Swan IPI ASR 8.5% (vs 27.0% for GPT-5.6 Sol) | not reported (no BBQ or fairness section found) | not reported (has a "Safe Completions for Users Under 18" section, which is not about education) | none | Abuse-monitoring logs kept up to 30 days by default; ZDR / Modified Abuse Monitoring "subject to prior approval" via sales (https://developers.openai.com/api/docs/guides/your-data). Astra-specific eligibility not stated |
| openai/gpt-5-mini | closed | Proprietary; as above | not disclosed | 31 May 2024 (https://developers.openai.com/api/docs/models/gpt-5-mini) | description only: "publicly available on the internet, … third parties …, users or human trainers" (PDF p.6) | GPT-5 System Card, https://cdn.openai.com/gpt-5-system-card.pdf, 13 Aug 2025 (mini = "gpt-5-thinking-mini"; its own results are only in Appendix 1, PDF p.55–56) | not reported for mini. Card reports gpt-5-thinking 0.040 vs GPT-4o 0.145 (Table 4, PDF p.9) | not reported for mini. gpt-5-thinking browsing / tool / coding 0.99 / 0.99 / 0.97 (Table 7, PDF p.12) | not reported for mini. BBQ shown for gpt-5-thinking and gpt-5-main only (Table 12, PDF p.20) | not reported | none | Same as GPT-6 Astra |
| openai/gpt-5.6-luna | closed | Proprietary; as above | not disclosed | 16 Feb 2026 (https://developers.openai.com/api/docs/models/gpt-5.6-luna) | description only (GPT-5.6 card §2) | GPT-5.6 System Card (Sol/Terra/Luna), https://deploymentsafety.openai.com/gpt-5-6, 9 Jul 2026 (updates to Aug 2026) | not reported | Reported (Table 5): Luna Connectors 0.999; Search & Function-Calling 0.897 (higher is better). GPT-Red table did not render in text, **unverified** | Reported: first-person fairness eval, harm_overall metric (§8.1). Value shown only in Figure 21; number **unverified** | not reported | none | Same as GPT-6 Astra |
| openai/gpt-oss-20b | open | Apache 2.0, plus a one-line gpt-oss usage policy ("comply with all applicable law") (https://huggingface.co/openai/gpt-oss-20b) | 20.91B total / 3.61B active, MoE (card PDF p.5) | June 2024 (PDF p.6) | description only: "text-only dataset with trillions of tokens, with a focus on STEM, coding, and general knowledge" (PDF p.6) | gpt-oss-120b & gpt-oss-20b Model Card, https://cdn.openai.com/pdf/419b6906-9da6-406c-a19d-1bb078ac7637/oai_gpt-oss_model_card.pdf, 5 Aug 2025 | not reported | Reported (instruction hierarchy): "Prompt injection hijacking" 0.639 for 20b (vs o4-mini 0.917) (Table 7, PDF p.15) | BBQ (Table 10, PDF p.17): ambiguous 0.79, disambiguated 0.89 | not reported | Compute only: 120b "required 2.1 million H100-hours", 20b "almost 10x fewer" (PDF p.6). No energy or carbon figure | N/A (open weights; OpenAI does not serve it first-party) |
| deepseek/deepseek-v4.1-flash | open | MIT for repository and weights (https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash) | 552B backbone + 196B Engram memory; 8B active (prefill) / 16B (decode) (tech report p.7); HF safetensors total ≈763B | not stated | description only: "multimodal corpus comprising 45T tokens"; web/Common Crawl, PDFs, code (report p.1, p.21) | Model card + tech report, https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/main/DeepSeek_V41_Tech_Report.pdf. Report undated; HF repo created 10 Sep 2026 | not reported | not reported | not reported | not reported | none | No ZDR option found. Privacy policy (last update 10 Feb 2026): inputs kept "for as long as you have an account"; stored in the PRC (https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html). The policy excludes end-user data of apps built on the open platform |
| google/gemini-3.5-flash-lite | closed | Proprietary; Gemini API Additional Terms (https://ai.google.dev/gemini-api/terms) / Google Cloud terms | not disclosed | March 2026; "in others … limited to January 2025" (card, Limitations) | description only, by chain: defers to the 3.1 Flash-Lite card, which defers to the Gemini 3 Pro card ("publicly-available web-documents, text, code, images, audio … and video") | https://deepmind.google/models/model-cards/gemini-3-5-flash-lite/, published 21 Jul 2026 | not reported | not reported | not reported (only automated content-safety deltas, e.g. text-to-text safety improved 8.14 points vs 3.1 Flash-Lite) | not reported | none (generic TPU/sustainability statement in the 3.1 Flash-Lite card) | Gemini API paid tier: logs kept for abuse monitoring, default maximum 55 days (https://ai.google.dev/gemini-api/docs/logs-policy); not used for training. ZDR achievable on Vertex/Gemini Enterprise with specific settings (https://docs.cloud.google.com/vertex-ai/generative-ai/docs/vertex-ai-zero-data-retention) |
| google/gemma-3-27b-it | open (HF gated: accept terms) | Gemma Terms of Use (last modified 1 Apr 2026): Prohibited Use Policy incorporated and must flow down to derivatives; notice/attribution file required; Google may "restrict (remotely or otherwise) usage" (https://ai.google.dev/gemma/terms; https://ai.google.dev/gemma/prohibited_use_policy) | 27B (HF 27.43B), dense | August 2024 | description only: 14T tokens, web docs, code, maths, images, 140+ languages | https://ai.google.dev/gemma/docs/core/model_card_3, last updated 14 Aug 2025 | not reported | not reported | Qualitative only: representational-harms testing ("bias, stereotyping"); "minimal policy violations", no numbers on card | Listed as an intended use ("Language Learning Tools … grammar correction or … writing practice"), not evaluated | none (generic TPU sustainability statement) | N/A (open weights; also on Gemini API under Gemini terms) |
| google/gemma-3-4b-it | open (HF gated) | Gemma Terms of Use, as above | 4B (HF 4.30B), dense | August 2024 | description only: 4T tokens | same Gemma 3 card, last updated 14 Aug 2025 | not reported | not reported | as Gemma 3 27B (qualitative) | as Gemma 3 27B (intended use only) | none | N/A |
| google/gemma-4-26b-a4b-it | open | Apache 2.0, plain text with no added Gemma terms (https://ai.google.dev/gemma/docs/gemma_4_license) | 25.2B total / 3.8B active, MoE (card) | January 2025 | description only | https://ai.google.dev/gemma/docs/core/model_card_4, last updated 30 Jul 2026 | not reported | not reported | Qualitative only: "significantly outperform Gemma 3 and 3n models in improving safety" | Listed under "Research and Education" intended uses, not evaluated | none | N/A |
| google/gemma-4-31b-it | open | Apache 2.0 (as above) | 30.7B dense (card; HF 31.27B) | January 2025 | description only | Gemma 4 card, last updated 30 Jul 2026 | not reported | not reported | Qualitative only (as above) | intended use only | none | N/A |
| meta-llama/llama-3.2-3b-instruct | open (HF gated) | Llama 3.2 Community License: separate licence needed above 700M monthly active users; must display "Built with Llama"; derivative model names must begin "Llama"; Acceptable Use Policy incorporated. The AUP's EU exclusion covers multimodal models only, not this text model (https://github.com/meta-llama/llama-models/blob/main/models/llama3_2/LICENSE; USE_POLICY.md) | 3.21B, dense | December 2023 | description only: "up to 9 trillion tokens … publicly available sources"; logits distilled from Llama 3.1 8B/70B | https://github.com/meta-llama/llama-models/blob/main/models/llama3_2/MODEL_CARD.md; card says "Model Release Date: Oct 24, 2024" (licence version date 25 Sep 2024) | not reported | not reported | not reported | not reported (mentions education only as a grants category) | **Yes:** 3B training 460k H100 GPU-hours at 700 W TDP; 133 tCO2eq location-based, 0 market-based. Llama 3.2 total 916k GPU-hours, 240 tCO2eq (location-based) | N/A (open weights) |
| microsoft/phi-4 | open | MIT (https://huggingface.co/microsoft/phi-4/resolve/main/LICENSE) | 14B dense (HF 14.66B) | June 2024 ("cutoff dates of June 2024 and earlier for publicly available data") | description only: 9.8T tokens; filtered public documents, synthetic "textbook-like" data, acquired academic books, chat SFT | https://huggingface.co/microsoft/phi-4 (release 12 Dec 2024) + Phi-4 Technical Report https://arxiv.org/abs/2412.08905 (Dec 2024) | not reported | not reported as prompt injection; Jailbreak (DR1) defect rate 0.073 (report Table 10, PDF p.19) | No BBQ. Harmful content continuation (incl. hate/fairness) DR3 0.036 (Table 10) | not reported | Compute only: 1920 H100-80G for 21 days (HF card) | Azure Foundry serverless: "Models are stateless, and they don't store any prompts or outputs"; Microsoft does not share them with the provider or train on them (https://learn.microsoft.com/en-us/azure/foundry-classic/how-to/concept-data-privacy) |
| mistralai/ministral-8b-2512 | open | Apache 2.0 (https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512) | 8.4B LM + 0.4B vision encoder (HF FP8 total 8.92B), dense | not stated | description only: distilled from Mistral Small 3.1, "trained for between 1 and 3 trillion tokens" (arXiv 2601.08584, p.1) | HF card (Ministral 3 8B Instruct 2512) + paper https://arxiv.org/abs/2601.08584, 13 Jan 2026 | not reported | not reported | not reported | not reported | none | ZDR "available on paid plans for supported stateless API calls", on request; Mistral reviews and may deny (https://docs.mistral.ai/admin/monitor-comply/zero-data-retention). Default 30-day abuse-monitoring window **unverified** (secondary sources only) |
| qwen/qwen3-235b-a22b-2507 | open | Apache 2.0 (https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507/blob/main/LICENSE) | 235B total / 22B active, MoE (HF card) | not stated | description only: "approximately 36 trillion tokens", 119 languages (Qwen3 Technical Report, p.2–3) | HF card (repo created 21 Jul 2025) + Qwen3 Technical Report https://arxiv.org/abs/2505.09388 (May 2025) | not reported | not reported | not reported | not reported | none | Alibaba Model Studio: prompts and responses "retained for no longer than 30 days". ZDR is enterprise-only, international site, listed model series only; this open Qwen3 model is not listed (https://www.alibabacloud.com/help/en/model-studio/data-retention-policy) |
| *candidate:* allenai/Olmo-3.1-32B-Instruct | open | Apache 2.0; "intended for research and educational use" under Ai2 Responsible Use Guidelines (https://allenai.org/responsible-use) | 32B dense (HF 32.23B) | December 2024 (HF card) | **full data released:** pretraining Dolma 3 mixes and Dolci post-training sets on HF (e.g. https://huggingface.co/datasets/allenai/dolma3_mix-6T); report: "we release both our data mixes" (p.5) | https://huggingface.co/allenai/Olmo-3.1-32B-Instruct (repo created 10 Dec 2025) + Olmo 3 report https://arxiv.org/abs/2512.13961 | not reported | not reported | BBQ reported for Olmo 3 **7B** models only, e.g. 7B Think accuracy 89.2, ambiguous bias 6.5 (report Table 52, PDF p.115). Not found for 32B. HF card gives an aggregate "Safety" score of 89.5 | not reported | Compute only: ≈56 days on 1024 H100s to Olmo 3 Think 32B; "$2.75M" at $2/H100-hour (report p.7). No energy figure | N/A (open weights) |

**Newest Ai2 releases (as at 2026-10-25).** On Hugging Face, the newest Olmo language models are Olmo Hybrid 7B (base Jan 2026; Instruct-DPO 20 Feb 2026; Think-SFT 28 Feb 2026). Their card says Apache 2.0, Dec 2024 cutoff, Dolma 3 / Dolci data. The largest current instruct model is Olmo 3.1 32B Instruct (Dec 2025), so that is the row above. Later "OlmoEarth" repos are Earth-observation models, not LLMs.

## Foundation Model Transparency Index (latest edition)

The latest edition is the **2025 FMTI, December 2025**: https://crfm.stanford.edu/fmti/December-2025 (paper: https://crfm.stanford.edu/fmti/December-2025/paper.pdf). It is scored out of 100 on revised indicators, so scores are not directly comparable with earlier editions. The search found no 2026 edition.

| vendor | 2025 score | flagship model scored | notes |
|---|---|---|---|
| Anthropic | 46 | Claude 4 | −5 vs 2024. The FMTI team prepared Anthropic's report itself (paper p.33–34) |
| Google | 41 | Gemini 2.5 | −6 vs 2024 |
| OpenAI | 35 | o3 | −14 vs 2024 (49 → 35) |
| DeepSeek | 32 | DeepSeek-R1 | first time scored |
| Meta | 31 | Llama 4 | −29 vs 2024 |
| Alibaba (Qwen) | 26 | Qwen 3 | first time scored |
| Mistral | 18 | Medium 3 | −37 vs 2024. Report prepared by FMTI team |
| Microsoft | not scored in 2025 | — | Previous edition (FMTI v1.1, May 2024, https://crfm.stanford.edu/fmti/May-2024/paper.pdf): 62 for Phi-2 |
| Ai2 | not scored | — | Not among the 13 companies in 2025 or the 14 in May 2024 |

Context from the paper: IBM scored 95, Writer 72, AI21 Labs 66, Amazon 39, xAI and Midjourney 14 each. The mean was 40.69 (Figure 7, p.19; abstract).

## Discrepancies and items not verified

- **Fable 5.1 prompt-injection ASR with probes.** Its own card says 12.80% (p.87). The Opus 5.5 card says 8.70% (p.88). The two cards may use different runs or configurations. Cite the card the comparison comes from.
- **Mistral default API retention (30 days).** Only secondary sources give it. The Mistral DPA mentions abuse monitoring but no period.
- **GPT-5.6 Luna.** The first-person-fairness value and the GPT-Red prompt-injection table appear only as a figure or table that did not render in text.
- **Not opened.** openai.com policy pages returned HTTP 403 to automated fetch. The OpenAI licence column rests on the existence of those policies, not on reading them.
- **Pages read from text conversions.** The Anthropic, OpenAI and Google cards were read as PDF/HTML-to-text conversions. Figure-only values were not read.
- **Education/grading evaluations.** None of the 17 cards, nor the Olmo report, reports an evaluation of education or grading use. Gemma 3/4 and Olmo list education only as an intended use.
- **Energy, carbon, water.** Only Meta (Llama 3.2) discloses training energy and carbon. OpenAI (gpt-oss), Microsoft (phi-4) and Ai2 (Olmo 3) disclose training compute only. No vendor discloses water or inference energy in these documents.

## Sources

Anthropic
- System card index: https://www.anthropic.com/system-cards
- Claude Opus 5.5 System Card (22 Sep 2026): https://www.anthropic.com/claude-opus-5-5-system-card (resolves to https://assets.claude.com/fc1b44717c85dc068bc6ba5024219938094694bd.pdf)
- Claude Fable 5.1 & Mythos 5.1 System Card (1 Sep 2026): https://www.anthropic.com/claude-fable-5-1-mythos-5-1-system-card
- Claude Haiku 5.5 System Card (7 Oct 2026): https://www.anthropic.com/claude-haiku-5-5-system-card
- API and data retention: https://platform.claude.com/docs/en/manage-claude/api-and-data-retention
- Commercial data retention: https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data
- Usage Policy: https://www.anthropic.com/legal/aup ; Commercial Terms: https://www.anthropic.com/legal/commercial-terms

OpenAI
- Deployment Safety Hub: https://deploymentsafety.openai.com/
- GPT-6 Astra System Card (3 Sep 2026): https://deploymentsafety.openai.com/gpt-6-astra
- GPT-5.6 System Card (9 Jul 2026): https://deploymentsafety.openai.com/gpt-5-6
- GPT-5 System Card (13 Aug 2025): https://cdn.openai.com/gpt-5-system-card.pdf
- gpt-oss Model Card (5 Aug 2025): https://cdn.openai.com/pdf/419b6906-9da6-406c-a19d-1bb078ac7637/oai_gpt-oss_model_card.pdf
- gpt-oss-20b on HF: https://huggingface.co/openai/gpt-oss-20b
- Model pages (cutoffs): https://developers.openai.com/api/docs/models/gpt-6-astra , https://developers.openai.com/api/docs/models/gpt-5-mini , https://developers.openai.com/api/docs/models/gpt-5.6-luna
- Data controls: https://developers.openai.com/api/docs/guides/your-data

Google
- Gemini 3.5 Flash-Lite model card: https://deepmind.google/models/model-cards/gemini-3-5-flash-lite/
- Gemini 3.1 Flash-Lite model card: https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-1-Flash-Lite-Model-Card.pdf
- Gemini 3 Pro model card: https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-Pro-Model-Card.pdf
- Gemini API terms: https://ai.google.dev/gemini-api/terms ; logs policy: https://ai.google.dev/gemini-api/docs/logs-policy
- Vertex / Gemini Enterprise ZDR: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/vertex-ai-zero-data-retention
- Gemma 3 model card: https://ai.google.dev/gemma/docs/core/model_card_3 ; Gemma 4 model card: https://ai.google.dev/gemma/docs/core/model_card_4
- Gemma Terms of Use: https://ai.google.dev/gemma/terms ; Prohibited Use Policy: https://ai.google.dev/gemma/prohibited_use_policy ; Gemma 4 licence: https://ai.google.dev/gemma/docs/gemma_4_license
- HF: https://huggingface.co/google/gemma-3-27b-it , https://huggingface.co/google/gemma-3-4b-it , https://huggingface.co/google/gemma-4-26B-A4B-it , https://huggingface.co/google/gemma-4-31B-it

Meta
- Llama 3.2 model card: https://github.com/meta-llama/llama-models/blob/main/models/llama3_2/MODEL_CARD.md
- Llama 3.2 licence: https://github.com/meta-llama/llama-models/blob/main/models/llama3_2/LICENSE ; AUP: https://github.com/meta-llama/llama-models/blob/main/models/llama3_2/USE_POLICY.md (the llama.com AUP URL cited in the licence returned 404)
- HF: https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct

Microsoft
- phi-4 HF card: https://huggingface.co/microsoft/phi-4 ; licence: https://huggingface.co/microsoft/phi-4/resolve/main/LICENSE
- Phi-4 Technical Report: https://arxiv.org/abs/2412.08905
- Foundry data privacy: https://learn.microsoft.com/en-us/azure/foundry-classic/how-to/concept-data-privacy

Mistral
- HF card: https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512
- Ministral 3 paper: https://arxiv.org/abs/2601.08584
- ZDR doc: https://docs.mistral.ai/admin/monitor-comply/zero-data-retention ; DPA: https://legal.mistral.ai/terms/data-processing-addendum

DeepSeek
- HF card: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash ; tech report: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/main/DeepSeek_V41_Tech_Report.pdf
- Privacy policy: https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html

Alibaba / Qwen
- HF card: https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507
- Qwen3 Technical Report: https://arxiv.org/abs/2505.09388
- Model Studio data retention: https://www.alibabacloud.com/help/en/model-studio/data-retention-policy

Ai2
- Olmo 3.1 32B Instruct: https://huggingface.co/allenai/Olmo-3.1-32B-Instruct ; Olmo Hybrid: https://huggingface.co/allenai/Olmo-Hybrid-Instruct-DPO-7B
- Olmo 3 report: https://arxiv.org/abs/2512.13961
- Dolma 3 data (example): https://huggingface.co/datasets/allenai/dolma3_mix-6T
- Responsible Use Guidelines: https://allenai.org/responsible-use

FMTI
- 2025 edition (Dec 2025): https://crfm.stanford.edu/fmti/December-2025 ; paper: https://crfm.stanford.edu/fmti/December-2025/paper.pdf
- May 2024 edition paper: https://crfm.stanford.edu/fmti/May-2024/paper.pdf
