<!-- Implements: reports/submission-pack -->
# Submission checklist

> **Draft proposal.** Al decides what goes on this list. He'll go through it section by section, adding, cutting and rewording, before it counts.

Due **Monday 26 October 2026, 19:59 HKT**; submit once. One list for everything, in the order of [`README.md`](README.md); tick an item only when it's true on `main` (or of the built PDF), not when it's planned. *Owner in italics; PR or file linked.*

## 1. Repo

- [x] Public as `al-beton/something-to-lose-apart-ai-collusion`, renamed, with a description and topics. *Repo-public session*
- [x] MIT licence. *Reviewer 1*, [#306](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/306)
- [x] README restructured to follow the paper: key findings, other findings, reproduce, extend, how it was built. *Refactorer*, [#314](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/314), [#316](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/316)
- [x] A short README in each top-level folder, and `reports/README.md` indexing the findings. *Refactorer*
- [x] History audited: no keys or private notes on `main`. *Repo-public*
- [ ] Optional: a GitHub Support purge of the files in the closed PRs [#280](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/280), [#293](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/293) and [#294](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/294). *Al*
- [x] CI green on `main`, and Pages publishes the latest [HTML](https://al-beton.github.io/something-to-lose-apart-ai-collusion/main/paper.html) and [PDF](https://al-beton.github.io/something-to-lose-apart-ai-collusion/main/paper.pdf). *Reviewer 1*

## 2. Results in the repo

- [x] [#296](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/296) exact reruns merged. *Reviewer 1*
- [x] [#305](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/305) paper rules merged. *Reviewer 1*
- [x] [#308](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/308) AI judge for collusion modes merged. *Reviewer 1*
- [x] [#295](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/295) E11 across markets merged. *Reviewer 1*
- [x] [#311](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/311) crux evidence review merged. *Reviewer 1*
- [x] [#310](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/310) paper loop and Pages preview merged. *Reviewer 1*
- [x] `make reproduce` passes on `main` (at `decd67f`). *Reviewer 1*
- [ ] Every number in the paper traces to a committed file. *Paper-draft*
- [ ] Mistral Large 3: Researcher 2 is running it on Modal, with [#319](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/319) (the `lenient_json` flag). It's in only if it finishes in time; otherwise it's dropped. *Researcher 2, Al*
- [ ] [#315](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/315), the conversation-memory spike (a draft): with full memory, the verified review holds on all 5 models, with 0 of 60 innocent agents coming forward. Al decides whether it goes in as a robustness check. *Al*
- [ ] Optional: Al hand-checks the AI judge's 40-game sample (`judge-sample.md`, [#308](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/308)); otherwise the paper says it wasn't done. *Al*

## 3. The paper ([`paper/paper.md`](../paper/paper.md))

*Owner: Al, with the paper-draft session; preview linked from [#310](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/310).*

### A. Template and readability

- [x] Title page: title, author and affiliation (Alistair Wakelin, Independent Researcher), and one first-page footnote naming the sprint (run by Apart Research) and the repository URL.
- [ ] Sections follow the official template's order: Introduction (with numbered contributions), Related Work, Methods, Results, Discussion and Limitations, Conclusion, Code and Data, References, Appendix. *The order is right; only the Results headings are questions so far.*
- [ ] At most 8 pages of body, excluding references and appendices. *The build warns past 8; the skeleton is about 6 pages of placeholder text.*
- [ ] Every figure and table is numbered, with a caption that stands alone and legible text, and sits near its first mention. *Placeholder figures for now.*
- [x] The PDF and HTML both build from one source (`paper/paper.md`).
- [x] Every push publishes a preview (`paper-preview` CI, linked from the pull request).

### B. The sprint's requirements

- [x] An abstract of 150–250 words: the problem, the approach, the key numbers, the takeaway. *Al, with the abstract session*
- [x] Author name and affiliation.
- [ ] An appendix titled exactly "Limitations and Dual-Use / Ethical Considerations": what the results do and don't establish, and whether the setup could make real collusion easier to carry out or harder to detect. *The heading is in place; no text yet.*
- [ ] Results report variance, seeds and baselines, and the positive control: the record-ceiling arm, 78/96 guilty against 2/36 innocent (`reports/e9/findings.md`, the record-ceiling row).
- [ ] Prior-work disclosure: all code was written during the sprint (first commit 24 October 2026), with nothing pre-existing; name the libraries and any starter code reused. *The sprint line is in Code and Data; the libraries aren't named yet.*
- [ ] A statement on AI tools: the lab was built and run by a team of Claude Code agents under Al's direction, and Al takes responsibility for every claim.
- [ ] References: every citation resolves in `references.bib`, and every entry is real and checked against its source (arXiv ID, URL, authors). Made-up references can disqualify a project.
- [ ] Every link works: the repository is public, and the Pages site and the figures load.
- [ ] The submission form: see section 4.

### C. Reproducibility and extensibility

- [ ] A short section in the paper, before Code and Data: archived replies and `make reproduce`, exact reruns only on Modal (with the caveat that none of the paper's runs used that setting), one config per run, how to extend, built spec-first. *Skeleton bullets are in `paper/paper.md` for Al to edit.*

- [ ] Per-figure reproduce commands (a free replay and a paid regeneration), from the verifiability session, applied to the figures Al picks. *Verifiability session, Al*

### D. Narrative and abstract

- [ ] The thesis and spine, from Al's private storylines notes (read locally, never committed).
- [x] The abstract drafted, approved by Al, and pasted into `form-fields.md`.
- [ ] Three claims to avoid, checked against the text: "stakes make agents honest", "they value leisure or ownership", "it holds generally".

### E. Which results to show and how

- [ ] About 4 figures or tables chosen for the main body, from Figures 1–10 and the E9 and E4 tables; everything else goes to the appendix.
- [ ] Every claim that needs a rerun or a new test before it can be made, listed. Al decides whether to run it.

### F. Final pass

- [ ] Every number traces to a committed file (a comment in the source), and `make reproduce` passes.
- [ ] Spelling, the page count and the PDF's filename.

## 4. The submission form

*Owner: Al. Each value is in [`form-fields.md`](form-fields.md), ready to paste.*

- [ ] Title, the same as the paper's title.
- [ ] Summary: the paper's final abstract, 150–250 words.
- [ ] The final PDF from `make paper-pdf` on `main`, at most 25 MB.
- [ ] Tracks: 1 and 3. Track 2 (Detection and Audit) arguably fits the verified-review result too; that's Al's call. *Al*
- [ ] Interested in publishing: yes.
- [ ] Team name, location, name and email. ✏️ *Al*
- [ ] Code URL.
- [ ] Optional: the project image.
- [ ] Optional: additional material, the HTML paper on Pages.
- [ ] Submit **once** before 19:59 HKT on 26 October (resubmitting doesn't replace the PDF), and check that the confirmation email arrives. *Al*
- [ ] The project page shows the submission (it can take up to 12 hours). *Al*
- [ ] Optional: record the Loom, then resubmit with the **same title** before the deadline to add its URL. *Al*
