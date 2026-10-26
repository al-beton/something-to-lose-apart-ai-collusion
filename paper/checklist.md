<!-- Implements: reports/paper-rules -->
# Report checklist: "Something to Lose"

Tick an item only when it's true of the built PDF, not of the plan. Due Monday 26 October 2026, 19:59 HKT.

## A. Template and readability

- [x] Title page: title, author and affiliation (Alistair Wakelin, Independent Researcher), the Apart Research and sprint line, the hackathon caution box, the repository URL.
- [ ] Sections follow the official template's order: Introduction (with numbered contributions), Related Work, Methods, Results, Discussion and Limitations, Conclusion, Code and Data, References, Appendix. *The order is right; only the Results headings are questions so far.*
- [ ] At most 8 pages of body, excluding references and appendices. *The build warns past 8; the skeleton is about 6 pages of placeholder text.*
- [ ] Every figure and table is numbered, with a caption that stands alone and legible text, and sits near its first mention. *Placeholder figures for now.*
- [x] The PDF and HTML both build from one source (`paper/paper.md`), and every push publishes a preview (`paper-preview` CI, linked from the pull request).

## B. The sprint's requirements

- [ ] An abstract of 150–250 words: the problem, the approach, the key numbers, the takeaway. *Lorem ipsum for now.*
- [x] Author name and affiliation.
- [ ] An appendix titled exactly "Limitations and Dual-Use / Ethical Considerations": what the results do and don't establish, and whether the setup could make real collusion easier to carry out or harder to detect. *The heading is in place; no text yet.*
- [ ] Results report variance, seeds and baselines, and the positive control: the record-ceiling arm, 78/96 guilty against 2/36 innocent (`reports/e9/findings.md`, the record-ceiling row).
- [ ] Prior-work disclosure: all code was written during the sprint (first commit 24 October 2026), with nothing pre-existing; name the libraries and any starter code reused. *The sprint line is in Code and Data; the libraries aren't named yet.*
- [ ] A statement on AI tools: the lab was built and run by a team of Claude Code agents under Al's direction, and Al takes responsibility for every claim.
- [ ] References: every citation resolves in `references.bib`, and every entry is real and checked against its source (arXiv ID, URL, authors). Made-up references can disqualify a project.
- [ ] Every link works: the repository is public, and the Pages site and the figures load.
- [ ] Submission form: title, summary, a PDF of at most 25 MB, tracks, publishing yes or no, team details, a project image (draft: `paper/submission.md`, from the submission-pack session). Submit once, because the PDF can't be replaced.

## C. Reproducibility and extensibility

- [ ] A short section in the paper, before Code and Data: archived replies and `make reproduce`, exact reruns only on Modal (with the caveat that none of the paper's runs used that setting), one config per run, how to extend, built spec-first. *Skeleton bullets are in `paper/paper.md` for Al to edit.*
- [ ] The MIT licence is merged (it's on the `claude/mit-license` branch).

## D. Narrative and abstract

- [ ] The thesis and spine, from Al's private storylines notes (read locally, never committed).
- [ ] The abstract drafted.
- [ ] Three claims to avoid, checked against the text: "stakes make agents honest", "they value leisure or ownership", "it holds generally".

## E. Which results to show and how

- [ ] About 4 figures or tables chosen for the main body, from Figures 1–10 and the E9 and E4 tables; everything else goes to the appendix.
- [ ] Every claim that needs a rerun or a new test before it can be made, listed. Al decides whether to run it.

## F. Final pass

- [ ] Every number traces to a committed file (a comment in the source), and `make reproduce` passes.
- [ ] Spelling, the page count and the PDF's filename.
