# Energy, carbon and water per grading

This page covers running the model. Training, making the chips and buildings, full water, and comparisons on a
life-cycle basis are in `LIFECYCLE.md`.

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

## By task

A grading's energy depends mostly on how many tokens it reads and writes. A per-token model was fitted to the
three prompt sizes in Jegham et al. 2025 (Table 4), for a small, a mid-size and a large model, and applied
to the median tokens each task uses on this benchmark (`docs/energy.json`, `public_data.py energy_tasks`).
Carbon and streaming are for the mid-size model.

| task | tokens in / out | small model | mid-size model | large model | as streaming video | carbon | gradings with the carbon of one half-pound beef burger |
|---|---|---|---|---|---|---|---|
| short answer | 166 / 46 | 0.02 Wh | 0.19 Wh | 0.27 Wh | 9 s | 0.07 g | about 300,000 |
| maths working | 450 / 72 | 0.03 Wh | 0.25 Wh | 0.38 Wh | 12 s | 0.10 g | about 230,000 |
| essay | 1,951 / 91 | 0.06 Wh | 0.46 Wh | 0.65 Wh | 22 s | 0.19 g | about 120,000 |
| code | 2,162 / 135 | 0.07 Wh | 0.53 Wh | 0.80 Wh | 25 s | 0.21 g | about 110,000 |
| code, reasoning-heavy model | 2,162 / 3,602 | 0.57 Wh | 3.9 Wh | 10.2 Wh | 3 min | 1.5 g | about 15,000 |
| 3-minute video | 12,357 / 88 | 0.29 Wh | 1.8 Wh | 2.2 Wh | 85 s | 0.73 g | about 31,000 |
| 30-minute video | 123,570 / 88 | 2.7 Wh | 16 Wh | 19 Wh | 13 min | 6.6 g | about 3,400 |

- **Long work costs most.** A 30-minute video costs about 90 times a short answer, because the grader reads
  about 4,000 tokens a minute of footage. This is extrapolated far beyond the 10,000-token prompts the model
  was fitted on, so it is likely an underestimate.
- **Reasoning is the other multiplier.** A model that writes 3,600 reasoning tokens on a code answer uses
  about 7 times the energy of one that writes 135.
- **A model's size** changes the figure about tenfold between the small and the mid-size model.

## Measured on open models (2026-10-25, re-run 2026-10-26)

The estimates above stay as they are. Beside them, the open models on the board were run on a rented GPU and
their energy read off it (`energy/`, pre-registered): one NVIDIA A100 80GB, vLLM, the leaderboard battery, 16
gradings at a time. **Boundary:** the GPU's energy above idle, then × 1.72 for the rest of the server and the
data centre (Google's split of its own figure: accelerators 58% of the total; Elsworth et al. 2025), so that
it compares with the per-token model, which counts them too.

**Status: measured, all nine models.** In the first run (2026-10-25) eight models failed a pre-registered
self-check: the GPU idled 13-26% higher after the runs than before, because it was still cooling. They were re-run
on 2026-10-26 with a cool-down before the second idle reading (CHANGE 3, pre-registered; 63-97 s per model), and
all eight passed. Olmo passed in the first run. The first run's figures are kept in
`energy/out/energy-run1-idle-failed.json`.

| task | measured, full-stack, range over the 9 models | small-model estimate at the same tokens | mid-size estimate |
|---|---|---|---|
| short answer | 1.5-13 mWh (0.0015-0.013 Wh) | 15-46 mWh | 173-381 mWh |
| essay | 3.4-29 mWh | 58-94 mWh | 427-674 mWh |
| code | 6.0-44 mWh | 66-132 mWh | 480-927 mWh |

- **Measured is lower than estimated, for every model and task.** All 27 model-task figures are BELOW THE
  SMALL-MODEL ESTIMATE, by a median factor of 4 (1.4 to 17), and 15 to 128 times below the mid-size estimate. The
  per-token model was fitted to figures inferred for hosted APIs, which carry their own overheads and batch
  sizes. For an open model of up to 32B parameters run in a batch on one modern GPU, it overstates the energy.
- **One request at a time costs 5-15 times as much** as batching. This is the largest lever, bigger than the
  model's size. AI Energy Score measures this way.
- **Per model** (`energy/README.md`): a full leaderboard run of 2,342 gradings used 6-29 Wh of GPU energy. That is
  less than half an hour of video streaming for the heaviest model.
- Closed models cannot be measured. Their estimates above remain the only figures.

## A burger for scale

A half-pound (227 g) beef burger patty from a beef herd carries about 22.6 kg CO2e and 330 litres of
freshwater withdrawn, over its whole life cycle (Poore and Nemecek 2018, *Science*, global means via Our
World in Data; farms vary widely). By carbon, that is about 300,000 short-answer gradings, or 3,400 gradings
of a 30-minute video, by a mid-size model.

The two are not measured the same way, and the comparison should be read with that in mind:
- the burger's figures cover its whole life cycle; the grading figures cover running the model, not
  building the chips or the data centre;
- the burger's water is freshwater withdrawn, mostly for feed; the grading's is water evaporated on site;
- one burger is one meal; gradings run by the billion across all uses of AI, so totals matter as well as
  the unit cost.

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

- **Measured energy at more batch sizes and on other GPUs**, and a node-level meter, so the full-stack factor
  is measured rather than taken from Google.
- **A column per model** citing the vendor's own disclosure, or its absence, beside the independent figure.
