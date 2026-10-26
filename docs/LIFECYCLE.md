# The full footprint of a grading, and how it compares

Per-query energy figures count only running the model. This page adds what they leave out: training,
building the chips and data centres, and the water used to make the electricity. It sets the result beside
everyday choices on the same footing wherever the sources allow, and states where they do not. The aim is an
objective sense of scale for people deciding how to use AI, or weighing a data centre near them. It is not
an argument for or against either.

The research notes behind every figure, with boundaries and links, are in `LIFECYCLE-NOTES.md`; it was
compiled by an agent from primary sources and spot-checked. The parameters are in `energy.json`
(`lifecycle`).

## What the usual figures leave out

| figure | includes | leaves out |
|---|---|---|
| Google, 0.24 Wh and 0.03 g CO2e per prompt | the accelerator, host CPU and memory, idle machines, data-centre overhead; **manufacturing of the hardware** (0.010 of the 0.03 g); carbon after Google's clean-energy purchases | training, data-centre buildings, networks, users' devices; water used to make the electricity |
| Google, 0.26 mL water per prompt | cooling water evaporated on site | the electricity's water (the largest part), chip manufacturing |
| Mistral, 1.14 g and 45 mL per response | inference and server manufacturing (a full life-cycle method) | how training is shared out per response is not published |
| Jegham et al., Epoch AI, OpenAI's 0.34 Wh | running the model | manufacturing, training, buildings |

## Adding it all up

Three steps on top of a task's running energy (mid-size model, `ENERGY.md`):
1. **Training and development.** Training energy, shared over the queries a model serves, adds a fraction m
   of the running energy. No company publishes how many queries a model serves, so m is a range:
   - low (0.1): a frontier-scale run spread over a year of very heavy use;
   - central (0.5): the fleet-wide split companies report, Meta 10:20:70 for experiments : training : use,
     and Google about two-fifths training;
   - high (1.4): the largest run, or a model with few users.
2. **Manufacturing and buildings.**
   - Energy: making the servers adds about 12.5% of their running energy (IEA).
   - Carbon: Google's figure already includes the hardware. Data-centre construction adds about 16% to the
     hardware's footprint (Schneider et al.).
3. **Accounting and water.**
   - Carbon: counting the grid average (about 414 g CO2e per kWh) instead of renewable purchases (Google's
     94 g) multiplies the carbon by about 4. The central and high cases use the grid average.
   - Water: add the water used to generate the electricity (1.3-4.4 L per kWh) and to make the chips.

| grading | energy, low / central / high | carbon | water |
|---|---|---|---|
| short answer | 0.21 / 0.32 / 0.51 Wh | 0.03 / 0.13 / 0.21 g | 0.5 / 1.3 / 2.6 mL |
| essay | 0.51 / 0.78 / 1.25 Wh | 0.07 / 0.32 / 0.52 g | 1.3 / 3.2 / 6.3 mL |
| code | 0.59 / 0.90 / 1.44 Wh | 0.08 / 0.37 / 0.60 g | 1.4 / 3.7 / 7.3 mL |
| code, reasoning-heavy model | 4.3 / 6.5 / 10.5 Wh | 0.56 / 2.7 / 4.3 g | 10 / 27 / 53 mL |
| 30-minute video | 18 / 28 / 44 Wh | 2.4 / 11 / 18 g | 44 / 112 / 223 mL |

**In short:** with everything added, a grading is about 1.1-2.7 times its running energy, up to about 9 times
the usually quoted carbon (mostly because of the accounting choice), and about 2.5-13 times the usually quoted
on-site water. It is
still a fraction of a gram of CO2 and a few millilitres of water for typical written work.

## Against everyday choices

Central case, short-answer gradings (0.13 g CO2e each):

| choice | carbon | boundary | equals, in short-answer gradings |
|---|---|---|---|
| a teacher's term: 150 students × 10 assignments | 0.2 kg | as above | 1,500 |
| driving 1 km, petrol car | 245 g | life cycle: car, fuel, driving (ICCT) | about 1,900 |
| driving 1 km, battery electric car | 80 g | life cycle including the battery (ICCT) | about 600 |
| streaming video for an hour | 55 g | electricity only, mostly the home router and screen; making the devices excluded (Carbon Trust) | about 400 |
| a quarter-pound beef patty | 11.2 kg | life cycle, global mean (Poore and Nemecek) | about 86,000 |
| a quarter-pound tofu patty | 0.36 kg | life cycle, global mean | about 2,700 |
| a 250 mL glass of almond milk | 176 g | life cycle, global mean (Poore and Nemecek) | about 1,300 |
| a 250 mL glass of oat milk | 226 g | as above | about 1,700 |
| a 250 mL glass of dairy milk | 788 g | as above | about 6,000 |
| a 1,000 km return flight | 308 kg | per passenger, including non-CO2 effects | about 2.4 million |

So a term of AI-graded short answers is roughly a kilometre of driving or four hours of streaming. Grading a
30-minute video is closer to 50 m of driving. For one person's choices, a meal or a trip matters far more than
grading.

**Water.** Central case, short-answer gradings (1.3 mL each, counting water evaporated on site, used to make the
electricity, and used to make the chips):

| choice | water | equals, in short-answer gradings |
|---|---|---|
| a teacher's term: 150 students × 10 assignments | 1.9 L | 1,500 |
| a 250 mL glass of oat milk | 12 L | about 9,400 |
| a 250 mL glass of almond milk | 93 L | about 72,000 |
| a 250 mL glass of dairy milk | 157 L | about 122,000 |
| a quarter-pound beef patty | 164 L | about 128,000 |

The food figures are freshwater withdrawn over the whole life cycle, mostly to irrigate crops and feed (Poore
and Nemecek 2018, global means via Our World in Data; farms vary widely). The grading's water is mostly water
consumed (evaporated), which is not the same measure: withdrawn water can partly return to rivers, so the
comparison overstates the food's share somewhat. Even so, one glass of almond milk is about 48 terms of a
teacher's AI-graded short answers. Almond milk is thirsty beside oat milk, but still uses less water than dairy
milk. Where the water is drawn matters as much as how much: almonds are mostly grown in drought-prone
California, and data centres are often sited where water is short.

## Where the concern is real: the total, and the place

- **Globally, small but growing fast.**
  - Data centres used about 415 TWh in 2024, about 1.5% of the world's electricity. That is projected to
    reach about 945 TWh, just under 3%, by 2030 (IEA).
  - Their CO2 is under 1.5% of energy-sector emissions, against over 20% for transport.
- **Locally, large.**
  - In Ireland, data centres used 22% of metered electricity in 2024, more than all urban homes (18%). In
    Virginia the share is about 25%.
  - One 100 MW data centre uses the electricity of about 100,000 households.
  - One of Google's largest sites, in Iowa, consumed about 2.8 million gallons of water a day in 2024.
- **The per-query figure and the total answer different questions.** Each grading is small, but the use is
  multiplied by billions and concentrated in a few places. A community weighing a new campus is right to look
  at its grid and water. A person deciding whether to use AI to mark a class's work is choosing something
  smaller than a short drive.

## Your own computer or a data centre?

No study runs the same model on a laptop and in a data centre, so this is pieced together, to an order of
magnitude:
- **For a small model under heavy use, a data centre is about 10 times more efficient per response.** It
  batches many requests on one GPU and cools efficiently.
- **At low use the advantage disappears.** One request a second on one GPU costs about the same as a laptop.
- **The bigger lever is the model.** A small model run locally uses tens of times less energy per response than
  a large model in a data centre.

## What remains uncertain

- No company publishes how many queries a model serves, so the training share is a range.
- Closed models' training energy is estimated by outsiders.
- Chip-manufacturing water rests on one estimate.
- Food figures are global means across farms that differ widely.
- Streaming's 55 g excludes making the devices, unlike the life-cycle figures.
- Efficiency invites more use, which no per-query figure shows (rebound effects). The national projections are
  where that appears.
