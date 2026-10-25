# Energy, carbon and water per grading

No vendor reports the energy of a grading, and no one has measured it for closed models. This page puts
the published figures side by side, with who produced each and what it counts, and converts them into
everyday comparisons. Every figure is an estimate. Where vendor and independent figures disagree, both are
shown.

## What a grading uses

Measured on this benchmark's runs (all models, from the providers' token counts):

| task | input tokens, median | output tokens, median | output, 90th percentile |
|---|---|---|---|
| short answers | 184 | 44 | 278 |
| essays | 2,004 | 59 | 472 |
| code | 2,210 | 112 | 1,212 |

Output tokens drive most of the energy. A grading's output is short, so its energy is closer to a short
chat query than to a long one. Reasoning models also spend hidden reasoning tokens, which the 90th
percentile partly reflects. One model's full leaderboard run is about 3,250 gradings.

## Published figures per query

| source | who | what it counts | energy per query | carbon | water |
|---|---|---|---|---|---|
| Elsworth et al. 2025, *Measuring the environmental impact of delivering AI at Google scale* (arXiv 2508.15734) | Google, about its own service | median Gemini text prompt, May 2025; full serving stack including idle capacity and cooling | 0.24 Wh | 0.03 g CO2e (market-based, counting Google's clean-energy purchases) | 0.26 mL (on site) |
| Altman 2025 (blog post) | OpenAI, about its own service | average ChatGPT query; no method given | 0.34 Wh | — | about 0.32 mL |
| Mistral 2025 life-cycle analysis | Mistral, about its own model | a 400-token response of Mistral Large 2, including hardware manufacture | — | 1.14 g CO2e | 45 mL |
| Jegham et al. 2025, *How Hungry is AI?* (arXiv 2505.09598, v6) | University of Rhode Island, independent | 30 commercial models, inferred from API speed and assumed hardware, with company-specific multipliers | 0.42 Wh for a short query (GPT-4o); the most energy-intensive models exceed 29 Wh per long prompt, over 65 times the most efficient | per model, on their dashboard | per model, on their dashboard |
| Oviedo et al. 2025, *Energy Use of AI Inference* (arXiv 2509.20241, v2, 2026) | Microsoft researchers, a vendor, about frontier models in general | frontier-scale models (>200B) on H100 nodes, bottom-up from throughput and node power | 0.31 Wh median (IQR 0.16-0.60); 3.91 Wh for reasoning queries 15 times longer | — | — |
| ML.ENERGY Benchmark (Chung et al., arXiv 2505.06371) | University of Michigan, independent | open models only, measured on GPUs under realistic serving; GPU energy only, so a lower bound | per model and task, on their leaderboard | — | — |
| AI Energy Score (Hugging Face, Salesforce, Cohere, Carnegie Mellon) | independent, with vendor participation | open models measured one request at a time, which overstates energy per request; closed models only if the vendor submits | star ratings per model | — | — |
| Li et al. 2023, *Making AI Less "Thirsty"* (arXiv 2304.03271) | independent | GPT-3-era model, including water used to generate the electricity | — | — | 500 mL per 10-50 medium-length responses |

None is audited. Only one independent source covers closed models (Jegham et al.), and its figures are
modelled, not measured. Only open models
have been measured directly, which is one advantage of open models the board can show.

## In everyday terms

Two cases: an ordinary model at 0.24-0.42 Wh per grading (Google's median to Jegham's short query), and a
reasoning model at 3.9 Wh (Oviedo et al.). Carbon at a grid intensity of 0.4 kg CO2 per kWh, near the US
average (an assumption: market-based figures such as Google's are lower). Comparisons:
- video streaming, about 0.077 kWh per hour (IEA, Kamiya 2020, 2019 data);
- a petrol car, 170 g CO2 per km;
- a domestic flight, 246 g per passenger-km (UK government factors for 2022, via Our World in Data).

| | energy | as streaming video | carbon | as driving a petrol car |
|---|---|---|---|---|
| one grading, ordinary model | 0.24-0.42 Wh | 11-20 seconds | 0.1-0.17 g | about 1 m |
| one grading, reasoning model | 3.9 Wh | 3 minutes | 1.6 g | 9 m |
| a teacher's term: 150 students × 10 assignments, ordinary model | 0.36-0.63 kWh | 5-8 hours | 0.14-0.25 kg | 0.8-1.5 km |
| the same, reasoning model | 5.9 kWh | 76 hours | 2.3 kg | 14 km |
| one model's full leaderboard run (3,250 gradings), ordinary model | 0.8-1.4 kWh | 10-18 hours | 0.3-0.55 kg | 2-3 km |

**A conference trip** of 1,000 km each way by air is about 2,000 km × 246 g ≈ 490 kg CO2. At 0.4 kg per kWh
that equals 1,200 kWh: about 3-5 million gradings by an ordinary model, or about 300,000 by a reasoning
model.

**Water** ranges from 0.26 mL per query (Google, on site only) to 10-50 mL (Li et al., counting the water used
to make the electricity, for an older model). A teacher's term of 1,500 gradings is about 0.4 L at the low
figure and 15-75 L at the high one.

## What we could add

- **Measured energy for open models.** Running the open models on the board on our own GPU with the same
  battery would give measured Wh per grading, which no one has for grading tasks.
- **A column per model** citing the vendor's own disclosure, or its absence, beside the independent figure.
