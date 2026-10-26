# Data roadmap: studies by what they need, and what the field could provide

Written 2026-10-26, after the media fairness review (`LITERATURE-MEDIA-FAIRNESS.md`). Every access link was checked
on that day. **Read each licence in full before any study.** In particular, read whether it allows:
- sending the data to third-party or commercial AI models through an API;
- publishing results;
- the zero retention this benchmark requires (`METHODOLOGY.md` 6.2, 6.3).

Accounts and licence acceptance belong to the maintainers, not an agent.

## 0. Open now (no sign-up): started or ready

| study | dataset | access | status |
|---|---|---|---|
| Language coverage: does a grader recognise a correct spoken answer as well in less common languages? | FLEURS (102 languages, the same sentences read aloud; CC BY 4.0) | [huggingface.co/datasets/google/fleurs](https://huggingface.co/datasets/google/fleurs) | being pre-registered |
| Accent: perception and transcription of accented English in video calls, by L1 | EdAcc (~40 h, many L1 and L2 accents; CC BY-SA) | [groups.inf.ed.ac.uk/edacc](https://groups.inf.ed.ac.uk/edacc/) | ready |
| Pronunciation scoring, children against adults | speechocean762 (5,000 utterances, Mandarin L1, five expert raters; CC BY 4.0) | [openslr.org/101](https://www.openslr.org/101/) | already held (speech task) |
| Written work in languages other than English, against CEFR ratings | MERLIN (2,286 German, Italian and Czech learner texts; CC BY-SA 4.0) | [merlin-platform.eu](https://merlin-platform.eu/) | ready |
| One paragraph read across many L1s: accent effect on a content judgement | Speech Accent Archive (CC BY-NC-SA 4.0; non-commercial) | [accent.gmu.edu](https://accent.gmu.edu/) | ready (site under renovation) |

## 1. Studies that need consent or access to a dataset

| # | study | dataset | how to get access | terms to check |
|---|---|---|---|---|
| 1 | **Perception audit.** How often each video model says it cannot see the person, refuses, or misdescribes them, by skin tone crossed with lighting. Your "I can't see you" incident, measured. | **Casual Conversations v2**: 26,467 consented videos, 5,567 people in seven countries. Labels: Fitzpatrick and Monk skin tone, self-reported language, disability, recording setup | Request on Meta's page: [ai.meta.com/datasets/casual-conversations-v2-dataset](https://ai.meta.com/datasets/casual-conversations-v2-dataset/) | "Limited" licence: evaluation allowed. Commercial use, and whether data may be sent to third-party APIs, are not stated on the page. |
| 2 | Perception audit, US only, with a low-light flag (a smaller first run) | **Casual Conversations v1** (45,186 videos, 3,011 people) | [ai.meta.com/datasets/casual-conversations-dataset](https://ai.meta.com/datasets/casual-conversations-dataset/) | as above |
| 3 | Lighting challenge across all ten Monk tones | **MST-E** (Google; 1,515 images, 31 videos, expert labels) | [skintone.google/mste-dataset](https://skintone.google/mste-dataset) | licence not confirmed |
| 4 | Image-model descriptions by perceived skin tone (for handwritten and photographed work) | **FACET** (~32k images; evaluation only) | [facet.metademolab.com](https://facet.metademolab.com/) | evaluation only, no training |
| 5 | **Accent and scoring.** Do audio models score speakers of different L1s differently at the same human score? This is the gap the literature names. | **Speak & Improve Corpus 2025** (~315 h of learner English, A2-C1, proficiency scores, many L1s) | Sign-up on ELiT's page: [englishlanguageitutoring.com/datasets/speak-and-improve-corpus-2025](https://www.englishlanguageitutoring.com/datasets/speak-and-improve-corpus-2025) | non-commercial use |
| 6 | Pronunciation error detection across six L1s (Hindi, Korean, Mandarin, Spanish, Arabic, Vietnamese) | **L2-ARCTIC** v5.0 (24 speakers, hand-annotated phone errors; Zhao et al. 2018, doi:10.21437/Interspeech.2018-1110) | Requested 2026-10-26: TAMU emails Google Drive links. Drive refuses scripted downloads ("only the owner and editors can download"), so the maintainer downloads in a browser; the links are not to be shared or committed (TAMU asks that others request their own copy at [psi.engr.tamu.edu/l2-arctic-corpus](https://psi.engr.tamu.edu/l2-arctic-corpus/)) | CC BY-NC 4.0; commercial use needs TAMU |
| 7 | African-accented English (120 accents) | **AfriSpeech-200** (200 h, 2,463 speakers) | Accept the terms on Hugging Face: [huggingface.co/datasets/intronhealth/afrispeech-200](https://huggingface.co/datasets/intronhealth/afrispeech-200) | CC BY-NC-SA, research only |
| 8 | Native vs non-native English, with self-reported ethnicity and region | **Fair-Speech** (Meta; 26.5k utterances, 593 speakers) | [ai.meta.com/datasets/speech-fairness-dataset](https://ai.meta.com/datasets/speech-fairness-dataset/) | licence not confirmed |
| 9 | Many languages and self-reported accents, at scale | **Common Voice** (100+ languages; CC0) | Account on the Mozilla Data Collective (the only route since Oct 2025): [datacollective.mozillafoundation.org](https://datacollective.mozillafoundation.org/) | its terms of service (not yet read) |
| 10 | **Student oral presentations with human evaluations:** the first real presentation-grading study | **SOPHIAS** (50 presentations, 65 students at Universidad Autónoma de Madrid; teacher, peer and self rubric scores; webcams, audio, slides, sensors; over 380 GB; Becerra, Cobos & Daza 2026, doi:10.1038/s41597-026-08240-w) | [github.com/dataGHIA/SOPHIAS](https://github.com/dataGHIA/SOPHIAS): sign the license agreement (`License/SOPHIAS_License_Agreement.pdf`) and email it to the group, with the requester's details and purpose; they reply with a download link | Research use, 2 years; every user named and registered with the licensor; **no redistribution to any other party**; identifiable faces; no images in publications without written permission; destroy at expiry. Sending recordings to a hosted AI model is a disclosure to a third party, so ask the licensor in writing before doing so, or use only models we run ourselves |
| 11 | Children's L2 English and German speaking, scored by experts | **TLT-school** (Italian pupils aged 9-16) | via FBK (details unverified) | part free to researchers |

**Suggested order:**
1. **1 and 5.** These are the two the literature calls gaps: perception by skin tone and lighting, and scoring by L1
   at the same human score.
2. **10.** It is the only consented, scored presentation set found.
3. **6 and 7**, for accent breadth.

## 2. Studies that need an IRB and new data collection

Each would use consented participants, zero retention, and nothing identifiable committed. Self-reported
demographics would be collected under a protocol that names AI processing.

| # | study | why it needs new data | design in one line |
|---|---|---|---|
| A | **Graded student presentations, by skin tone, accent and language** | No public set pairs real student presentations with several raters' scores and consented demographics | Students record a short presentation. At least two trained raters score each; self-reported L1 and ethnicity are collected, with Monk skin tone annotated. Gaps are measured at the same human score. |
| B | **The same student, two recordings** (good and poor lighting; laptop and phone microphone) | Separates perception from judgement: the person and the content are fixed, only the recording changes | Each student records twice; the paired difference in grade is the effect of the recording. |
| C | **The same script, many presenters** | Content fixed, presenter varies: the cleanest test of appearance and voice bias | Students deliver a common script; any grade difference across presenters is not about content. |
| D | **Answering in one's first language against in English** | Language coverage on real student content, not read sentences | Bilingual students answer the same oral questions in both languages; the same raters score both. |
| E | **Screen-share and code walkthroughs** | A new modality with no scored public set | Students explain their code on screen; raters score explanation and correctness. Text on screen gives an injection probe. |
| F | **Assistive formats and disability** (captions, sign language, AAC, stuttering, low vision) | Not in any dataset found | Recruit with disability organisations; compare grades with human raters'; count "cannot see or hear" replies. |
| G | **Teacher in the loop** | Whether AI suggestions shift teachers' marks differently by student group (automation bias) | Teachers mark with and without an AI suggestion, randomised. |
| H | **Feedback uptake for media work** (extends the planned feedback study) | Whether feedback on a presentation changes the next one | A delayed second presentation, as in the existing protocol. |
| I | **Student-reported harm** | "I can't see you" happens to real students; its frequency and effect are unknown | A short survey after AI-assessed tasks, reported by group. |

**Shared requirements:**
- a protocol that names each AI vendor and its retention;
- consent that covers AI processing, with withdrawal;
- recordings kept off the repository and deleted on schedule;
- the raters' scores as the reference;
- a pre-registered subgroup minimum before any gap is read.

## 3. Recommendations to the field: what would make better benchmarks possible

1. **Release every rater's score, not only the adjudicated one.** Without two independent scores per item there is
   no human ceiling, and an AI that beats one rater's agreement cannot be read. ASAP 2.0 publishes one adjudicated
   score.
2. **Write licences that say whether the data may be used to evaluate third-party AI models, and published.** Most
   dataset terms predate API models. "Evaluation only, no training, results publishable, through zero-retention
   endpoints" would let a benchmark use them without doubt.
3. **Collect consented, self-reported demographics, and standard skin-tone labels.** Use the Monk scale alongside
   Fitzpatrick, plus L1, dialect and disability. Set a subgroup minimum, so fairness can be measured rather than
   guessed.
4. **Record the conditions, don't filter them.** Lighting, camera, microphone, noise, connection: real classrooms
   are not studios, and quality effects need the variation.
5. **Use content-fixed designs where possible:** the same script read by many people, and the same sentences in
   many languages (as FLEURS does). They separate who is speaking from what is said.
6. **Release transcripts aligned with the audio or video.** That separates transcription error from judgement, and
   lets errors be traced through the pipeline.
7. **Release analytic, per-trait scores and the rubric the raters used,** with stable item identifiers and checksums.
8. **Keep a private held-out test set, publish its hashes, and seed canary strings.** Public corpora end up in
   training data; the board found 2-8% of its cases in one model's training set.
9. **Collect real student work across ages, subjects and languages.** Crowdsourced and read-aloud speech is not
   classroom work, and almost every scored set is English.
10. **Keep access stable and versioned,** with a DOI per version. Moving a corpus to a new platform emptied the
    mirrors that studies depended on (Common Voice, 2025).
11. **Publish datasheets that state the consent scope,** including AI processing and retention, so later users know
    what the participants agreed to.
12. **Include, or permit, adversarial and null variants:** blank and off-task answers, and instructions embedded in
    the work. Graders are now gamed through these, and a benchmark should not have to invent them.
