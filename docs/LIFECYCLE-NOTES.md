# Life-cycle footprint of an AI query: research notes (agent-compiled, 2026-10-25)

Research notes compiled 2026-10-25 for the AI grading benchmark's public environmental-footprint section. Every figure below comes from a primary document that was opened (an HTML page, or a PDF downloaded and text-extracted), except where it is marked **unverified**. "Derived" means I computed it from the sourced inputs shown; it is not printed in the source. Figures already in hand (Elsworth et al. 2025, Jegham et al. 2025, Oviedo et al. 2025, Mistral per-response, Li et al. 2023, IEA/Kamiya 2020 streaming, Poore & Nemecek 2018) are re-quoted only where a boundary detail matters.

Conventions: Wh = watt-hour; gCO2e = grams CO2-equivalent; MB = market-based emissions accounting (counts renewable purchases); LB = location-based (grid average). Water "consumption" = water evaporated or otherwise not returned; "withdrawal" = water taken, most of it returned. These two are not interchangeable.

---

## Boundary check on the operational figures already in hand

| Figure | Value | Unit | Boundary | Year | Source URL |
|---|---|---|---|---|---|
| Google median Gemini Apps text prompt, energy | 0.24 | Wh/prompt | Active accelerator, host CPU and DRAM, idle provisioned machines, data-centre overhead (fleet PUE 1.09). Excludes training, external networking, end-user devices. | May 2025 | https://arxiv.org/html/2508.15734 |
| Same, emissions | 0.03 (0.023 Scope 2 MB + 0.010 Scope 1+3) | gCO2e/prompt | **Does include embodied hardware.** The paper's Table 2 splits it into 0.023 g Scope 2 (MB) and 0.010 g Scope 1+3; the Scope 3 part is manufacturing of accelerators, host CPU and DRAM. MB factor 94 gCO2e/kWh (2024). The paper does not mention data-centre building construction, so it appears to be left out (check before quoting). | 2025 | https://arxiv.org/html/2508.15734 |
| Same, water | 0.26 | mL/prompt | On-site cooling only, at fleet WUE 1.15 L/kWh. Excludes water used to generate the electricity and water used to make the chips. | 2025 | https://arxiv.org/html/2508.15734 |
| Same, narrow "existing approach" | 0.10 Wh, 0.02 g, 0.12 mL | per prompt | Active accelerator only. The paper's own text gives 0.01 g and 0.15 mL, which disagrees with its Table 2 | 2025 | https://arxiv.org/html/2508.15734 |
| Mistral Large 2, per 400-token Le Chat response | 1.14 gCO2e, 45 mL, 0.16 mg Sb eq | per response | Described as "the marginal impacts of inference", excluding users' devices. LCA under the GHG Protocol and ISO 14040/44 that includes server manufacturing. The page does not say whether a share of training is allocated to it. Peer reviewed by Resilio and Hubblo. | published 22 Jul 2025 | https://mistral.ai/news/our-contribution-to-a-global-environmental-standard-for-ai |
| Epoch AI, GPT-4o typical query | ~0.3 | Wh/query | 500 output tokens, H100 at about 10% utilisation, 1,500 W per GPU including server and 10–20% facility overhead. Excludes training and embodied energy. | 7 Feb 2025 | https://epoch.ai/gradient-updates/how-much-energy-does-chatgpt-use |
| Epoch, long inputs | ~2.5 (10k-token input); ~40 (100k-token input) | Wh/query | Same model of the hardware | 2025 | same |
| OpenAI CEO, average ChatGPT query | 0.34 Wh; 0.000085 gal (~0.32 mL) water | per query | Methodology not given. The date is not shown on the page; it was reported as June 2025 (**unverified date**). | 2025 | https://blog.samaltman.com/the-gentle-singularity |

---

## A. Training, amortised

| Figure | Value | Unit | Boundary | Year | Source URL |
|---|---|---|---|---|---|
| Llama 3.1 8B / 70B / 405B training | 1.46M / 7.0M / 30.84M GPU-h; 420 / 2,040 / 8,930 t LB; 0 t MB | GPU-hours; tCO2e | H100-80GB at 700 W (TDP), "peak power capacity per GPU device used, adjusted for power usage efficiency". So energy is an upper-bound estimate, not a meter reading. The card does not say whether development, fine-tuning or embodied emissions are included. MB = 0 because of 100% renewable matching. | 2024 | https://huggingface.co/meta-llama/Llama-3.1-8B |
| Llama 3.1 405B energy (derived) | ≈21.6 | GWh | 30.84M GPU-h × 0.7 kW. Implied LB grid intensity ≈414 gCO2e/kWh (derived) | 2024 | derived from the above |
| Llama 3.1 family total | 39.3M GPU-h; 11,390 t LB | GPU-h; tCO2e | as above | 2024 | same |
| Llama 3.3 70B | 7.0M GPU-h; 2,040 t LB; 0 MB | | as above | 2024 | https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct |
| Llama 4 Scout / Maverick | 5.0M / 2.38M GPU-h; 1,354 / 645 t LB; 0 MB | | as above | 2025 | https://huggingface.co/meta-llama/Llama-4-Scout-17B-16E |
| Ai2 OLMo series (Morrison et al.), final training runs | 913 MWh; 312 tCO2e; 1,921 kL water | | GPU power measured. PUE 1.2; 0.332 kgCO2/kWh; off-site WUE 1.29 L/kWh, on-site 0 (Jupiter cluster). Excludes data-centre construction, transport, end-of-life. | 2025 (ICLR 2025) | https://arxiv.org/html/2503.05804 |
| Same, development (ablations, failed runs, etc.) | 459 MWh; 159 tCO2e; 843 kL | | Development is about 50% of training's impact. About 70% of the development impact came from the 7B and 13B work. | 2025 | same |
| Same, embodied (manufacturing) | 22 tCO2e; 4.8 kL | | 463 kgCO2e per GPU (3,700 kg per 8-GPU node, taken from Luccioni 2023); about 100.4 L water per H100 (an estimate based on TSMC); 4-year life; 0.013 kgCO2e and 0.003 L per GPU-hour | 2025 | same |
| Same, total | ≥493 tCO2e; 2,769 kL water | | Sum of the three rows above. The embodied share is ≈4.5% (derived). | 2025 | same |
| Same, inference break-even | "hundreds of millions to tens of billions" of inferences to equal training CO2e. OLMo 2 7B: 20.9 bn (batched), 1.05 bn (1 req/s) | inferences | Simulated on one H100 with SGLang and 2,400 ShareGPT prompts, GPU only (a lower bound) | 2025 | same |
| BLOOM 176B, final training | 433,196 kWh; 24.69 t (dynamic power only) | kWh; tCO2e | French grid, 57 gCO2e/kWh | 2023 (JMLR) | https://arxiv.org/abs/2211.02001 (text from PDF) |
| BLOOM embodied | 11.2 t (7.57 servers + 3.64 GPUs) | tCO2e | HPE server ~2,500 kg plus ~150 kg per A100 (a lower bound), 6-year life, 85% use. Excludes network, cooling and other infrastructure. | 2023 | same |
| BLOOM idle | 256,646 kWh; 14.6 t | | Only ~54% of cluster power went to the training job itself | 2023 | same |
| BLOOM total | 50.5 | tCO2e | dynamic + idle + embodied. Embodied ≈22% (derived). | 2023 | same |
| BLOOM deployment (18 days, 16×A100, no batching) | 914 kWh for 230,768 requests; ≈19 kgCO2e/day | kWh | About 75% of energy went to keeping the model in memory between requests. ≈3.96 Wh/request (derived). | 2023 | same |
| Mistral Large 2 training (to Jan 2025, after 18 months of use) | 20.4 ktCO2e; 281,000 m³ water; 660 kg Sb eq | | Full LCA including hardware manufacturing. **No per-response amortisation is published** and no split between training and inference is given on the page. A press report that training plus inference make up 85.5% of emissions is **unverified** (secondary only, Next.ink). Critics note that R&D and fine-tuning appear to be excluded. | 2025 | https://mistral.ai/news/our-contribution-to-a-global-environmental-standard-for-ai |
| GPT-4 training (IEA estimate) | ≈42.4 | GWh | 25,000 GPUs for about 14 weeks at an 84% load factor. An estimate, not a disclosure. | 2025 | https://iea.blob.core.windows.net/assets/dd7c2387-2f60-4b60-8c5f-6563b6aa1e4c/EnergyandAI.pdf (p. 40–41) |
| GPT-4 training (Morand, Névéol, Ligozat) | 32.8 GWh; 15 ktCO2e (10.2 use, 2.0 infrastructure, 3.3 embodied) | | Uses Epoch's 57M A100 GPU-hours, PUE 1.2 and the US average grid. Embodied ≈20% of carbon. No water figure. | arXiv v2, 17 Sep 2026 | https://arxiv.org/html/2510.09022 |
| GPT-4 training, AI Index | 5,184 | tCO2e | **unverified**: seen only in secondary coverage | 2025 | (not opened) |
| Largest model in the Epoch dataset (IEA) | ~154 MW peak; ~310 GWh | | IEA estimate | 2025 | IEA Energy and AI p. 41 |
| All large AI models (>10^23 FLOP) trained since 2020 | ~1.7 TWh | | ≈0.1% of data-centre electricity over the period (IEA) | 2025 | same |
| Google ML energy split | "about ⅗ of ML energy use is for inference and ⅖ for training" | share | All Google ML use (research, development, testing, production), one week each April in 2019–2021. ML was 10–15% of Google's total energy. | 2022 | https://arxiv.org/abs/2204.05149 (PDF text) |
| Meta AI infrastructure split | 10:20:70 (experimentation : training : inference) | power capacity | Meta (then Facebook) AI fleet. For one recommendation model, end-to-end energy split 31:29:40 (data : experimentation/training : inference). | 2022 (MLSys) | https://arxiv.org/abs/2111.00364 (PDF text) |

**What can and cannot be compared.** Open-model training figures are now fairly solid: Meta's model cards, Ai2 and BLOOM. Closed frontier models have only estimates (IEA's ~42 GWh, and Morand's 32.8 GWh / 15 kt for GPT-4), and those come from guessed GPU counts. Meta's figures are a GPU-TDP upper bound. They do not separate development, which Ai2 found adds about 50% on top of the final run. Meta's market-based zero is an accounting choice, not a physical one. Per-query amortisation is mostly limited by the denominator: no lab publishes lifetime query counts per model.

**How to amortise.** Training share per query = (final training + development + training-hardware embodied) ÷ (lifetime queries served by that model and its distilled descendants). Inputs needed: the training total (above); a development multiplier (≈1.5× from Ai2, the only measured value); deployment life (months until the model is replaced); and queries per day. The only volume disclosure found is 2.5 billion ChatGPT prompts per day (OpenAI to Axios, via TechCrunch, 21 Jul 2025: https://techcrunch.com/2025/07/21/chatgpt-users-send-2-5-billion-prompts-a-day/), and that is not per model. As an illustration (derived): 42.4 GWh spread over one year at 2.5 bn prompts/day is ≈0.046 Wh per prompt, or ≈0.07 Wh with development added. That is about 20–30% of a 0.24–0.34 Wh query. A 310 GWh model at the same volume gives ≈0.34 Wh, about 1× to 1.4×. Mistral would need about 17.9 bn responses (derived: 20.4 kt ÷ 1.14 g) before training per response fell to the size of the marginal inference figure. A top-down alternative is to scale the operational figure by a fleet ratio: Google's ⅖ : ⅗ split implies training adds ≈0.67× of inference energy, and Meta's 10:20:70 implies ≈0.43×.

---

## B. Embodied hardware and buildings

| Figure | Value | Unit | Boundary | Year | Source URL |
|---|---|---|---|---|---|
| NVIDIA HGX H100 baseboard (8× H100 SXM, 640 GB HBM3) | 1,312 | kgCO2e per baseboard (≈164 per GPU, derived) | Cradle-to-gate: materials, components, assembly, transport. Excludes use and end-of-life, and the host server (CPUs, DRAM, chassis, NICs, storage). Memory 546 kg (42%), ICs 332 (25%), thermal 230 (18%); assembly 8.6%, transport 0.4%. ISO 14067, reviewed by WSP. Typical power 5,600 W. | Jul 2025 | https://images.nvidia.com/aem-dam/Solutions/documents/HGX-H100-PCF-Summary.pdf |
| Google TPU LCA (Schneider et al.), embodied per chip over 6 years | v4i 386; v5e 402; v6e 692; v4 693; v5p 1,101 | kgCO2e/chip | Includes chip and CPU manufacturing plus transport **and data-centre construction** (v6e: 109 kg, ≈16% of embodied, derived). Excludes racks, network, auxiliary compute and storage. | Feb 2025 | https://arxiv.org/html/2502.01671v1 |
| Same, embodied vs operational share | embodied ≈10% (LB, no clean-energy purchasing); operational ≈70% (MB); ≈90% (LB); operational ≈40% at a hypothetical 90% carbon-free energy | share of lifetime CO2e | per TPU generation | 2025 | same |
| Same, compute carbon intensity v6e | embodied 38; operational 118 (MB) / 316 (LB) | gCO2e/ExaFLOP | The embodied share is 11% (LB) to 24% (MB) (derived) | 2025 | same |
| IEA, high-performance server | >10 MWh to manufacture vs >80 MWh of operation over 5 years; manufacturing "<20%" of life-cycle energy | MWh | Energy, not carbon. 3 nm wafer ≈2.3 MWh. | 2025 | IEA Energy and AI p. 38–39 |
| Gupta et al., "Chasing Carbon" | Facebook 2019: capex and supply-chain emissions were 23× opex-related | ratio | Opex is market-based, after renewable purchasing. The paper says "most emissions related to modern mobile and data-center equipment come from hardware manufacturing and infrastructure". | 2020 (HPCA 2021) | https://arxiv.org/abs/2011.02839 (PDF text) |
| Wu et al. (Meta), "Sustainable AI" | manufacturing ≈50% of the location-based operational footprint of large ML tasks | ratio | Meta fleet, PUE 1.1 | 2022 | https://arxiv.org/abs/2111.00364 |
| Microsoft FY24 | Scope 2: 9,955,368 t (LB) vs 259,090 t (MB). Scope 3 Category 2, capital goods (incl. server equipment and other long-term assets): 6,066,000 t, up from 3,105,000 in FY20 | tCO2e | Capital goods are ≈23× market-based Scope 2, but ≈0.6× location-based (derived). Building construction is not broken out separately. | FY24 (Jul 2023–Jun 2024) | https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/microsoft/msc/documents/presentations/CSR/2025-Microsoft-Environmental-Data-Fact-Sheet-PDF.pdf |
| Embodied share in the training studies above | Ai2 ≈4.5%; BLOOM ≈22%; GPT-4 (Morand) ≈20% | share | derived from section A | | |

**What can and cannot be compared.** Google's 0.03 g per prompt already includes hardware manufacturing: 0.010 g, about 30% (derived). Google gives no sign that it includes data-centre construction. Mistral's figure includes server manufacturing. Epoch's 0.3 Wh, OpenAI's 0.34 Wh and most per-query energy figures exclude both. The embodied share depends mostly on the accounting: about 10% when operational electricity is counted at grid average, and 25–50% or more when renewable purchases are netted off. A single "embodied share" should therefore always state LB or MB. Per-GPU values vary about 3× (150 kg BLOOM lower bound, 164 kg NVIDIA baseboard-only, 463 kg Ai2, about 600–1,100 kg for a whole TPU system per chip) because the boundaries differ: GPU only, baseboard, or whole server plus building.

---

## C. Water, fully

| Figure | Value | Unit | Boundary | Year | Source URL |
|---|---|---|---|---|---|
| IEA global data-centre water consumption | ~560 bn L/yr (2023) → ~1,200 bn L/yr (2030, Base Case) | litres/yr | About ⅔ electricity and primary energy supply, about ¼ on-site cooling, the remainder (about 1/12, derived) chip manufacturing | 2025 | IEA Energy and AI p. 241–242 |
| IEA, 100 MW US hyperscale | ~2 million L/day in total; "equivalent to about 6500 households"; >60% indirect | L/day | includes the electricity's water | 2025 | same |
| IEA, chip manufacturing water for data centres | ~70 bn L in 2030 (up >50% from 2023); ~90% for ultra-pure water | L/yr | | 2025 | same |
| US data centres, direct (on-site) water 2023 | 17 bn gal (64 bn L) | gal/yr | **unverified**: secondary reports of LBNL 2024. The LBNL PDF returned 403 and could not be opened. | 2024 | (LBNL report: https://escholarship.org/uc/item/32d6m0d1) |
| US data centres, indirect (electricity) water 2023 | 211 bn gal (800 bn L) | gal/yr | **unverified**, as above | 2024 | same |
| Li et al., on-site WUE range | ~1 (Google annual) to ~9 (Arizona, summer) | L/kWh | on-site evaporation | v5, Mar 2025 | https://arxiv.org/abs/2304.03271 (PDF v5) |
| Li et al., US electricity water intensity (EWIF) | consumption 3.14 L/kWh; withdrawal 43.83 L/kWh. Alternatives: 4.35 L/kWh; Meta's own 3.70 L/kWh | L/kWh | Their EWIF counts hydropower reservoir evaporation, which raises it a lot | 2025 | same |
| Li et al., GPT-3 training water | 5.4 million L total, of which 700,000 L on-site | L | Microsoft US data centres | 2025 | same |
| Ai2 off-site WUE; on-site | 1.29 L/kWh off-site; 0 on-site (Jupiter); 3.10 L/kWh (Augusta) | L/kWh | | 2025 | https://arxiv.org/html/2503.05804 |
| Water to make one H100 | ≈100.4 | L/GPU | estimate based on TSMC data; plus ~2.2 L for rare-earth mining | 2025 | same |
| Google fleet WUE | 1.15 | L/kWh | on-site, 2023–2024 | 2025 | https://arxiv.org/html/2508.15734 |
| Google fleet PUE vs industry | 1.09 vs 1.56 | – | The industry figure is Uptime Institute's 2024 survey as cited by Google (Uptime itself not opened) | 2024 | https://www.gstatic.com/gumdrop/sustainability/google-2025-environmental-report.pdf |
| Google total water consumption | ~8.1 bn gal (31 bn L) | gal/yr | Data centres it operates plus offices. Google equates this to irrigating 54 golf courses in the US south-west (at 150 Mgal per course per year, USGA 2012). | 2024 | same |
| Google Council Bluffs, Iowa (its largest site) | withdrawal 1,410.3; discharge 400.1; consumption 1,010.2 Mgal; "6.7 golf course equivalents" | Mgal/yr | on-site only | 2024 | same (water-by-location table) |
| Council Bluffs, per day (derived) | ≈2.77 Mgal/day ≈ 10.5 million L/day consumed | | derived from the above | 2024 | derived |
| Other Google sites | Mayes County, OK: 833.2 Mgal consumed; Berkeley County, SC: 776.5; The Dalles, OR: 361.4 | Mgal/yr | on-site | 2024 | same |
| Microsoft total water consumption | 5,807 ML (FY24); 7,844 ML (FY23). 42% of FY24 consumption in water-stressed areas. | ML/yr | company-wide | FY24 | Microsoft fact sheet (URL in B) |
| US domestic use, public supply | 82 | gal/person/day | **withdrawal-type deliveries, not consumption**; the self-supplied average is 77 | 2015 | https://pubs.usgs.gov/circ/1441/circ1441.pdf |
| US irrigation | 118 Bgal/d withdrawn; 73.2 Bgal/d consumed | Bgal/day | | 2015 | https://pubs.usgs.gov/publication/cir1441 |
| US thermoelectric power | 133 Bgal/d withdrawn; 4.31 Bgal/d consumed | Bgal/day | | 2015 | same |

**What can and cannot be compared.** On-site figures such as Google's 0.26 mL and its golf-course comparisons are about a quarter of the full picture. By IEA's global split, the full total is roughly 4× the on-site figure, and the electricity's water is the largest part. That part depends heavily on whether hydropower evaporation is counted. Comparisons with towns are only fair consumption-to-consumption. USGS per-capita figures are deliveries (withdrawals), so dividing Council Bluffs' 2.77 Mgal/day by 82 gal/day (≈34,000 people, derived) overstates the equivalence: much of a household's water returns to the sewer, while evaporated cooling water does not. US data centres' direct use (17 bn gal/yr, unverified) is ≈0.06% of US irrigation consumption (derived; the years differ, 2023 vs 2015). Nationally it is small. Locally it is not, because a single site can draw millions of gallons a day from one aquifer or utility.

---

## D. Local vs data centre

| Figure | Value | Unit | Boundary | Year | Source URL |
|---|---|---|---|---|---|
| Ai2, Llama 3.1 8B on one H100, batched (all requests at once) | 0.011 kWh / 2,400 prompts ≈ 0.0046 Wh/request (derived) | Wh/request | GPU energy only (a lower bound); ShareGPT prompts | 2025 | https://arxiv.org/html/2503.05804 (Table 3) |
| Same at 8 req/s; at 1 req/s | ≈0.021; ≈0.139 Wh/request (derived) | Wh/request | Low load leaves the GPU mostly idle, so energy per request is ~30× the batched figure | 2025 | same |
| Husom et al. (MELODI), Llama3-8B on Laptop 2 (Intel i7 10th gen + Quadro RTX 4000 8 GB) | 1.34e-4 kWh/response (0.134 Wh) at 255 tokens average (≈1.9 J/token, derived) | kWh/response | Process-level CPU (RAPL via Scaphandre) plus nvidia-smi GPU. No screen, no rest of the system, no wall power. Alpaca prompts. | v2, Mar 2026 | https://arxiv.org/html/2407.16893v2 |
| Same paper, workstation (Xeon + RTX A2000) | gemma-7b 8.05e-5 vs laptop 9.81e-5 kWh/response | | "Energy consumption is noticeably higher for the laptops than the workstation" | 2026 | same |
| GreenBench, Apple M4 Pro (48 GB), 3–9B models | 4.4–11.6 mJ/token package; 0.09–0.25 J/token "system-level", using an **assumed** ~10 W system power | J/token | Preprint. The 0.47 W package reading is implausibly low, and system power is assumed, not metered. The paper claims "30–40× better energy efficiency per token than datacenter GPUs in single-user deployment". **Treat as unverified.** | 2026 | https://arxiv.org/pdf/2608.28667 |
| ML.ENERGY (Chung et al.), effect of batching | Raising the batch size "can unlock a 3–5× reduction in energy per token". Qwen3-32B on B200: 0.209 J/token at batch 128, 0.151 at batch 512 | J/token | GPU only. The authors note GPUs are 50–70% of data-centre power. | arXiv Jan 2026 | https://arxiv.org/html/2601.22076v1 |
| AI Energy Score | batch size 1 on H100; GPU energy only; Wh per 1,000 queries | method | Its own notes say total energy needs CPU, RAM, network and storage added, then PUE | current | https://huggingface.github.io/AIEnergyScore/ |
| BLOOM API, unbatched | ≈3.96 Wh/request (derived); 75% of energy spent idle in memory | | 16×A100, real traffic | 2023 | https://arxiv.org/abs/2211.02001 |
| Data-centre overhead | PUE 1.09 (Google), 1.2 (Ai2), 1.56 (industry average per Uptime, via Google) | – | | 2024–25 | see C |

**What can and cannot be compared.** No study runs the same model and prompts on a laptop and in a batched data centre. The comparison below is assembled from different sources and is order-of-magnitude only. For an 8B model: batched H100 GPU-only ≈0.005 Wh/request. Adding non-GPU server power (GPU ≈50–70% of the total) and PUE 1.1–1.56 gives ≈0.01–0.015 Wh (derived). An older laptop with a discrete GPU measured ≈0.13 Wh for a similar-length response. So **at high load a data centre is roughly 10× more efficient per response for the same small model.** At low load (one request per second on one GPU) the advantage disappears: about 0.14 Wh GPU-only, the same as the laptop. Apple-silicon figures (≈0.006–0.018 Wh per 255 tokens, derived, unverified) suggest a modern unified-memory laptop may come within about 1–2× of batched serving. The larger lever is model choice. A local 8B model uses tens of times less energy than the 0.24–0.34 Wh frontier-model figures, while a data centre serving a frontier model uses far more per response than either.

---

## E. Comparators, life-cycle where available

| Figure | Value | Unit | Boundary | Year | Source URL |
|---|---|---|---|---|---|
| Video streaming, Europe, one hour (Carbon Trust/DIMPACT) | ≈55 gCO2e; 188 Wh | per hour | **Operational electricity only**: data centres and CDN <1 g / ~1 Wh (≈1%), network 6 g / 20 Wh (10%), home router 21 g / 71 Wh (38%), viewing device plus peripherals 28 g / 96 Wh (51%). **Excludes embodied emissions of devices and equipment, and content production.** Grid-average factors. On-demand only, not live. Netflix funded it. | 2021 (2020 data) | https://www.carbontrust.com/sites/default/files/documents/resource/public/Carbon-impact-of-video-streaming.pdf |
| IEA/Kamiya streaming | 0.077 kWh/h | | in hand; check its device and network boundary against Carbon Trust's | 2020 | (in hand) |
| Petrol car, Europe, lower-medium, life cycle (ICCT) | 245–246 (petrol and diesel similar); small 226–227; SUV 266–288 | gCO2e per **vehicle**-km | Vehicle production, maintenance, recycling, fuel production and real-world use. Life-cycle values are "more than twice as high" as the official test tailpipe values (109–122 gCO2/km NEDC, lower-medium). | Jul 2021 | https://theicct.org/wp-content/uploads/2021/12/Global-LCA-passenger-cars-jul2021_0.pdf |
| Petrol car, US, life cycle (ICCT) | 254 (car); 312 (SUV) | gCO2e/vehicle-km | as above; real-world 7.8 L/100 km | 2021 | same |
| Battery EV, Europe, life cycle (ICCT) | 76–83 (lower-medium); 77–84 (small); 82–90 (SUV) | gCO2e/vehicle-km | Includes battery manufacturing; the range depends on IEA grid scenarios. Country examples: Germany 104, UK 67, France 49. | 2021 | same |
| Battery EV, US, life cycle (ICCT) | 83–103 (car); 105–133 (SUV) | gCO2e/vehicle-km | | 2021 | same |
| Petrol car, use phase per passenger-km (OWID, from UK DESNZ 2022) | 170 | gCO2e/passenger-km | **Excludes vehicle manufacturing** | 2022 factors | https://ourworldindata.org/travel-carbon-footprint |
| Short-haul flight | 154 | gCO2e/passenger-km | **Includes non-CO2 effects** through a 1.9 multiplier (contrails etc.). Without it, roughly 81 (derived, approximate) | 2022 factors | same |
| Domestic flight | 246 | gCO2e/passenger-km | includes the 1.9 multiplier | 2022 | same |
| National rail; Eurostar | ~35; ~4 | gCO2e/passenger-km | | 2022 | same |
| Beef (beef herd), Poore & Nemecek | 99.48 kgCO2e/kg; 1,451.2 L/kg freshwater withdrawals | per kg of product | Global mean across studies, as processed by OWID | 2018 (2010 data) | https://ourworldindata.org/grapher/ghg-per-kg-poore ; https://ourworldindata.org/grapher/water-withdrawals-per-kg-poore |
| Beef (dairy herd) | 33.3 kgCO2e/kg; 2,714.3 L/kg | | | | same |
| Quarter-pound (113 g) beef-herd patty (derived) | ≈11.2 kgCO2e; ≈164 L withdrawals | per patty | 113 g is an assumed serving size (it matches the Beyond Burger LCA functional unit), raw-weight basis | | derived |
| Plant alternatives, per 113 g (derived) | tofu ≈0.36 kgCO2e (3.16/kg); peas ≈0.11 kg (0.98/kg) | | Poore & Nemecek via OWID | | same |
| Beyond Burger vs US beef | "90% fewer" GHG emissions per quarter-pound | relative | Cradle to distribution; commissioned by Beyond Meat. **Unverified**: the report PDF and U-M pages returned 403/404; this comes from the search summary only. | 2018 | (CSS18-10, University of Michigan, not opened) |
| Cheese | 23.88 kgCO2e/kg; 5,605.2 L/kg | | Poore & Nemecek via OWID | | same |
| Coffee | 28.53 kgCO2e/kg; 25.9 L/kg | per kg of product | Per cup depends on the grounds mass, which the source does not give | | same |
| Sandwich (UK, Espinoza-Orias & Azapagic) | range up to 1,441 g ("all-day breakfast", ready-made). UK average ≈826 g per sandwich (derived from 9.5 Mt ÷ 11.5 bn sandwiches). Home-made ham and cheese is the lowest; making at home cuts emissions by about half. | gCO2e/sandwich | Whole life cycle: ingredients, packaging, waste. The ham-and-cheese home-made range of 399–843 g is **unverified** (secondary). | 2018 | https://www.manchester.ac.uk/about/news/what-is-the-environmental-impact-of-your-lunch-time-sandwich/ |
| Google web search | 0.0003 kWh (1 kJ); ~0.2 gCO2 | per search | Includes index building. Google's own figure from 2009; now 17 years old and not updated. | 11 Jan 2009 | https://googleblog.blogspot.com/2009/01/powering-google-search.html |
| TV for comparison | Google uses ~100 W, so 0.24 Wh ≈ 9 s of TV | | | 2025 | https://arxiv.org/html/2508.15734 |

**What can and cannot be compared.** Car and EV figures from ICCT are true life-cycle figures (manufacture, fuel and electricity production, use) and are per vehicle-km. OWID's 170 g is per passenger-km and excludes manufacture. Streaming at 55 g/h is operational only, so it matches an operational per-query figure, not a life-cycle one. Food figures are farm-to-retail life-cycle means with very wide spreads. Illustrative ratios using the reported figures (derived; check the boundaries before publishing): one quarter-pound beef-herd patty ≈ 340,000 Google median prompts at 0.033 g (MB), or ≈ 9,900 Mistral responses at 1.14 g. One hour of streaming ≈ 1,700 Google prompts, or ≈ 48 Mistral responses. One km in an average European petrol car (life cycle) ≈ 7,400 Google prompts. The fair version uses the full per-query estimate below (≈0.04–0.25 g), which shrinks these ratios by up to about 8×. For an education audience, the right unit is a whole grading session or a semester, not a single prompt.

---

## F. Scale of the whole

| Figure | Value | Unit | Boundary | Year | Source URL |
|---|---|---|---|---|---|
| Global data-centre electricity | ~415 TWh (~1.5% of global) in 2024 → ~945 TWh (just under 3%) in 2030, Base Case. Sensitivity cases 670–1,260 TWh. ~12%/yr growth since 2017. | TWh | All data centres. US 45%, China 25%, Europe 15% (2024). | Apr 2025 | https://iea.blob.core.windows.net/assets/dd7c2387-2f60-4b60-8c5f-6563b6aa1e4c/EnergyandAI.pdf |
| IEA update | 485 TWh in 2025 (+17%); AI-focused data centres +50% in 2025; ~950 TWh by 2030 (~3%); AI-focused triples | TWh | | Apr 2026 | https://iea.blob.core.windows.net/assets/3179f7f8-01f6-4dd6-bffa-c9f7b73f1dc9/KeyQuestionsonEnergyandAI.pdf |
| IEA thought experiment | 10 bn queries/day at 1 Wh ≈ 3.6 TWh/yr, "<1% of the 485 TWh" | TWh/yr | IEA's illustration, which covers chat queries only | 2026 | same |
| Data-centre share of electricity-demand growth to 2030 | <10% of global growth; less than industry, electric transport, appliances or space cooling; "nearly half" of US growth | share | | 2025 | IEA 2025 p. 63–65 |
| Data-centre CO2 | 180 Mt today → ~300 Mt by 2035 (Base), up to 500 Mt (Lift-Off); "below 1.5% of total energy sector emissions"; peak ~320 Mt around 2030 | MtCO2 | Electricity supply only. No embodied emissions. | 2025 | IEA 2025 p. 14, 49 |
| Transport, for comparison | ">20% of CO₂ emissions in the energy sector"; road 75% of transport energy, aviation >10% | share | | 2025 | IEA 2025 p. ~150 |
| Other ICT, for comparison | crypto ~125 TWh (0.5% of global electricity); TVs, peripherals and cable networks ~500 TWh (2%) | TWh, 2023 | | 2025 | IEA 2025 p. 71 |
| US data centres | 176 TWh (4.4% of US) in 2023, from 58 TWh in 2014 → 325–580 TWh (6.7–12%) in 2028 | TWh | LBNL 2024, as reported by DOE (the LBNL PDF itself was not reachable) | Dec 2024 | https://www.energy.gov/articles/doe-releases-new-report-evaluating-increase-electricity-demand-data-centers |
| Size of one site | a 100 MW data centre ≈ electricity of 100,000 households; largest under construction ≈ 2 million households | | IEA | 2025 | IEA 2025 p. 14, 37 |
| Ireland | data centres 22% of metered electricity (2024), up from 21% (2023) and 5% (2015); urban dwellings 18% | share | | released 10 Jun 2025 | https://www.cso.ie/en/releasesandpublications/ep/p-dcmec/datacentresmeteredelectricityconsumption2024/ |
| US states | 6 states above 10% of electricity supply; Virginia 25% | share | IEA | 2025 | IEA 2025 p. 37 |
| Clustering | "Nearly half of data centre capacity in the United States is in five regional clusters" | | | 2025 | IEA 2025 p. 13 |

**What can and cannot be compared.** Globally, data centres (all of them, not only AI) use about 1.5% of electricity, rising to about 3% by 2030. They account for under 10% of electricity-demand growth and under 1.5% of energy-sector CO2. That is smaller than transport (>20%), but it is growing fast and is concentrated in a few places. The community concern is local, and in those places it is well founded: in Ireland data centres now use more metered electricity than all urban homes (22% vs 18%), and in Virginia the share is 25%. Water is the same story: nationally small next to irrigation, but a single site can take millions of gallons a day. There is no source here for the AI-only share of total water. The IEA's 560 bn L is for all data centres.

---

## Building a full per-query estimate

Start from an operational figure whose boundary you know. Below, Google's median text prompt is the base: 0.24 Wh, 0.033 gCO2e (MB, including hardware), 0.26 mL on-site. All results are derived. Low, central and high are ranges the literature supports, not confidence intervals.

**Step 1 — Fix the operational boundary.** Use a figure that includes idle capacity, host CPU and DRAM, and PUE (Google 0.24 Wh). A GPU-only or batch-1 benchmark (AI Energy Score, ML.ENERGY) is too narrow on overhead and does not represent real load. Google's own narrow method gave 0.10 Wh, a 2.4× understatement. Long inputs, reasoning modes and images can raise operational energy 10–100× (Epoch: 2.5 Wh at 10k tokens, 40 Wh at 100k). A grading prompt that carries a rubric and a long student answer needs its own token count.

**Step 2 — Add training and development.** Multiplier m on operational energy:
- low m ≈ 0.1: a 20–40 GWh frontier run (Llama 3.1 405B ≈21.6 GWh; GPT-4 ≈33–42 GWh) amortised over about a year at ChatGPT-scale volume (2.5 bn/day). This gives ≈0.02–0.05 Wh, roughly 0.1–0.2×.
- central m ≈ 0.4–0.67: fleet ratios from Meta (10:20:70) and Google (⅖ : ⅗). These include research and development.
- high m ≈ 1.4: a 310 GWh run (IEA's largest) at the same volume, or a model with far fewer users or a short deployment life. Add Ai2's ≈1.5× for development if the training figure covers only the final run.
- Inputs that are still missing: per-model lifetime query counts, and the deployment life before replacement.

**Step 3 — Add manufacturing and buildings.** Energy: IEA's server figure (>10 MWh manufacturing vs >80 MWh operation over 5 years) adds about 12.5% of operational energy. Carbon: Google's 0.010 g already includes accelerator, CPU and DRAM manufacturing. Data-centre construction adds about 16% on top of hardware embodied (Schneider v6e: 109 of 692 kg). For a figure that excludes embodied altogether (e.g. Epoch's or OpenAI's), add about 10% of total under LB accounting, or about 25–30% under MB (Schneider; Google Table 2).

**Step 4 — Choose the carbon accounting and state it.** MB (Google's 94 g/kWh) vs LB (≈414 g/kWh, as implied by Meta's Llama card). On 0.24 Wh that is 0.023 g vs 0.099 g of operational carbon, a 4.3× swing that outweighs most other choices.

**Step 5 — Complete the water.** Total = (on-site + electricity water) × (1 + m) + manufacturing.
- On-site: 0.26 mL (WUE 1.15 L/kWh).
- Electricity: 0.24 Wh × EWIF → 0.31 mL (1.29 L/kWh, Ai2), 0.75 mL (3.14 L/kWh, Li US average, including hydro), 1.04 mL (4.35 L/kWh).
- Chip manufacturing: ≈0.001 mL using Ai2's 0.003 L per GPU-hour and about one GPU-second per query (Epoch's assumption). Using IEA's global share (about 1/12 of total data-centre water), it is ≈0.1 mL. The two methods disagree by about 100×; this is the least well-sourced input.

**Result (derived, per median text prompt):**

| | Low | Central | High |
|---|---|---|---|
| Energy (Wh) | 0.26 (m 0.1, no manufacturing) | 0.39 (m 0.5, +12.5% manufacturing) | 0.61 (m 1.4, +12.5%) |
| Carbon (gCO2e) | 0.04 (MB) | 0.16 (LB) | 0.25 (LB) |
| Water consumed (mL) | 0.6 (EWIF 1.29) | 1.6 (EWIF 3.14) | 3.3 (EWIF 4.35) |

So, with every left-out component added, a typical text prompt is about 1–2.5× the operational energy figure, 1–8× the headline carbon figure (mostly because of the accounting choice), and 2–13× the on-site water figure. It still sits in the range of a fraction of a gram of CO2 and a few millilitres of water. Mistral's 1.14 g and 45 mL per response are above even the high case. Its page does not explain why (model size, French-grid LCA factors, the water metric, or allocation choices). Present it as a separate, independently built data point rather than averaging it in.

**Honest uncertainty.**
- (1) The training denominator (lifetime queries) is undisclosed.
- (2) Closed-model training energy is an estimate built on guessed GPU counts.
- (3) No AI vendor publishes an LB-and-MB pair per query.
- (4) Chip-manufacturing water rests on one TSMC-based estimate.
- (5) Per-query figures describe short text prompts; grading prompts with long rubrics and student work need their own token counts (Epoch's input-length scaling).
- (6) Rebound effects (the extra use that efficiency invites) are outside any per-query figure. The IEA projections are where they show up.

---

## Sources (all opened unless marked)

- Elsworth et al. 2025, Google, Measuring the environmental impact of delivering AI at Google scale. https://arxiv.org/html/2508.15734
- Mistral AI 2025, Our contribution to a global environmental standard for AI. https://mistral.ai/news/our-contribution-to-a-global-environmental-standard-for-ai
- Meta Llama 3.1 model card. https://huggingface.co/meta-llama/Llama-3.1-8B ; Llama 3.3: https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct ; Llama 4: https://huggingface.co/meta-llama/Llama-4-Scout-17B-16E
- Morrison et al. 2025, Holistically Evaluating the Environmental Impact of Creating Language Models (Ai2). https://arxiv.org/html/2503.05804
- Luccioni, Viguier, Ligozat 2023, Estimating the Carbon Footprint of BLOOM. https://arxiv.org/abs/2211.02001
- Patterson et al. 2022, The Carbon Footprint of Machine Learning Training Will Plateau, Then Shrink. https://arxiv.org/abs/2204.05149
- Wu et al. 2022, Sustainable AI: Environmental Implications, Challenges and Opportunities (Meta). https://arxiv.org/abs/2111.00364
- Gupta et al. 2020, Chasing Carbon. https://arxiv.org/abs/2011.02839
- Schneider et al. 2025, Life-Cycle Emissions of AI Hardware (Google TPU). https://arxiv.org/html/2502.01671v1
- NVIDIA 2025, PCF Summary for NVIDIA HGX H100. https://images.nvidia.com/aem-dam/Solutions/documents/HGX-H100-PCF-Summary.pdf
- Morand, Névéol, Ligozat 2026 (v2), The Environmental Impacts of Language Model Training Keep Rising. https://arxiv.org/html/2510.09022
- IEA 2025, Energy and AI. https://iea.blob.core.windows.net/assets/dd7c2387-2f60-4b60-8c5f-6563b6aa1e4c/EnergyandAI.pdf
- IEA 2026, Key Questions on Energy and AI. https://iea.blob.core.windows.net/assets/3179f7f8-01f6-4dd6-bffa-c9f7b73f1dc9/KeyQuestionsonEnergyandAI.pdf
- US DOE 2024, release on the LBNL 2024 US Data Center Energy Usage Report. https://www.energy.gov/articles/doe-releases-new-report-evaluating-increase-electricity-demand-data-centers (the LBNL report at https://escholarship.org/uc/item/32d6m0d1 was **not reachable**: 403)
- Li, Yang, Islam, Ren 2025 (v5), Making AI Less "Thirsty". https://arxiv.org/abs/2304.03271
- Google 2025 Environmental Report. https://www.gstatic.com/gumdrop/sustainability/google-2025-environmental-report.pdf
- Microsoft 2025 Environmental Data Fact Sheet (FY24). https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/microsoft/msc/documents/presentations/CSR/2025-Microsoft-Environmental-Data-Fact-Sheet-PDF.pdf
- Dieter et al. 2018, Estimated Use of Water in the United States in 2015 (USGS Circular 1441). https://pubs.usgs.gov/circ/1441/circ1441.pdf
- CSO Ireland 2025, Data Centres Metered Electricity Consumption 2024. https://www.cso.ie/en/releasesandpublications/ep/p-dcmec/datacentresmeteredelectricityconsumption2024/
- Husom et al. 2026 (v2), The Price of Prompting. https://arxiv.org/html/2407.16893v2
- Kannan et al. 2026, GreenBench (preprint; figures unverified). https://arxiv.org/pdf/2608.28667
- Chung et al. 2026, Where Do the Joules Go? https://arxiv.org/html/2601.22076v1 ; ML.ENERGY Benchmark: https://arxiv.org/html/2505.06371
- AI Energy Score methodology. https://huggingface.github.io/AIEnergyScore/
- You 2025, How much energy does ChatGPT use? (Epoch AI). https://epoch.ai/gradient-updates/how-much-energy-does-chatgpt-use
- Altman, The Gentle Singularity. https://blog.samaltman.com/the-gentle-singularity
- TechCrunch 2025, ChatGPT users send 2.5 billion prompts a day. https://techcrunch.com/2025/07/21/chatgpt-users-send-2-5-billion-prompts-a-day/
- Carbon Trust 2021, Carbon impact of video streaming. https://www.carbontrust.com/sites/default/files/documents/resource/public/Carbon-impact-of-video-streaming.pdf
- Bieker 2021, ICCT, A global comparison of the life-cycle greenhouse gas emissions of combustion engine and electric passenger cars. https://theicct.org/wp-content/uploads/2021/12/Global-LCA-passenger-cars-jul2021_0.pdf
- Our World in Data, Which form of transport has the smallest carbon footprint? https://ourworldindata.org/travel-carbon-footprint
- Poore & Nemecek 2018 via OWID: https://ourworldindata.org/grapher/ghg-per-kg-poore ; https://ourworldindata.org/grapher/water-withdrawals-per-kg-poore
- University of Manchester 2018, release on Espinoza-Orias & Azapagic, Carbon footprint of sandwiches (doi 10.1016/j.spc.2017.12.002). https://www.manchester.ac.uk/about/news/what-is-the-environmental-impact-of-your-lunch-time-sandwich/
- Google 2009, Powering a Google search. https://googleblog.blogspot.com/2009/01/powering-google-search.html
- **Not opened / unverified:** LBNL 2024 report PDF (water figures 17 bn and 211 bn gal); Beyond Meat LCA, Heller & Keoleian 2018 (CSS18-10); AI Index 2025 GPT-4 figure of 5,184 t; Next.ink's 85.5% Mistral breakdown; Uptime Institute 2024 PUE survey (cited via Google); IEA/Kamiya 2020 (in hand, boundary not re-checked here).
