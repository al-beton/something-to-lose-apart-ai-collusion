<!-- Implements: reports/submission-pack -->
# Final essay-writing sprint

Al's ordered list for finishing the paper and releasing it. Work top to bottom, and the last step is the release. Tick an item only when it's true of the paper on `main` (or the built PDF). Sub-points are a starting set: Al adds or cuts them after checking a few reference papers. The repo, results and form items stay in [`checklist.md`](checklist.md).

Due **Monday 26 October 2026, 19:59 HKT**; submit once.

## 1. Format and layout
- [ ] Apart template order: Introduction (with numbered contributions), Related Work, Methods, Results, Discussion and Limitations, Conclusion, Code and Data, References, Appendix.
- [ ] Title page: title, author and affiliation, the sprint footnote, the repository URL ([#335](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/335)).
- [ ] At most 8 body pages before the references (the current draft builds to 9).
- [ ] Results sections headed as questions, in a light voice.

## 2. Title
- [ ] *Something to Lose*, with or without a subtitle, decided.
- [ ] The cover subtitle matches the evidence: a personal cost can *improve* alignment, not keep agents aligned ([#329](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/329)).
- [ ] The same title on the paper, the form and the project image.

## 3. Abstract infographic
- [ ] Hero or project image chosen: the two robots in Firm A / Firm B caps ([#329](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/329)).
- [ ] Placed under the abstract or on the title page, and legible at thumbnail size.

## 4. Abstract
- [ ] 150–250 words, checked by `paper/check.py`: the problem, the approach, the key numbers, the takeaway.
- [ ] No single Gemma percentage, and no "honest", "agents value leisure" or "holds generally".
- [ ] Says innocent agents stop coming forward under the verified review, and that frontier models behave differently, not that they show nothing.

## 5. Introduction
- [ ] Why naming each bad act doesn't scale, and why law and personal penalties might (Salib & Goldstein; quote checked against the PDF).
- [ ] The question and the numbered contributions.
- [ ] Lee 2026 as the main prior work: what we take, change and extend.

## 6. Overall structure
- [ ] The escalating arc: set-up and collusion → confessing as plain game theory → a stake of its own → truth or self-protection → how models differ → what it would take.
- [ ] The writers' sections merged into one voice ([#336](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/336), [#337](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/337), [#338](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/338), then the editor pass).

## 7. Graphics
- [ ] Main-body figures chosen (about 6): the set-up, price traces, owning up by penalty, coming forward by stake, the verified review (guilty vs innocent), and the model × stake grid.
- [ ] No placeholders left: the price traces (still `figA4`) and the verified-review figure.
- [ ] Every figure numbered, with a caption that stands alone, legible text, and placed near its first mention.
- [ ] Each figure has its replay and regenerate commands ([#324](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/324)).

## 8. Content
- [ ] Every number traces to a committed file, with a source comment.
- [ ] Variance, seeds, baselines and the positive control (record-ceiling: 78/96 guilty vs 2/36 innocent).
- [ ] Robustness: Gemma given as a range across wordings; temperature; full conversation memory ([#315](https://github.com/al-beton/something-to-lose-apart-ai-collusion/pull/315)).
- [ ] "Loves Sudoku" on Gemma, plus the other-model follow-up if it lands in time.
- [ ] Every `[CHECK]`, `[CITE]` and `AL:` marker resolved or deliberately left out.

## 9. Conclusion
- [ ] Two short paragraphs: what we found, and what it would take (a stake the firm can't protect, likely detection, a review that checks evidence).
- [ ] Future work: applied rather than stated stakes, richer scenarios, frontier models.

## 10. Mandatory parts
- [ ] Appendix titled exactly "Limitations and Dual-Use / Ethical Considerations", including that the verified rule tells agents collusion without messages is safe.
- [ ] LLM usage statement: built and run by Claude Code agents under Al's direction; Al takes responsibility for every claim.
- [ ] Prior-work disclosure: all code written during the sprint (first commit 24 October 2026), with the libraries named.
- [ ] Code and Data: the repository, `make reproduce`, and what replays exactly.
- [ ] References: every entry real and checked (arXiv ID, URL, authors), and Wagner "Anchored" added or cut.
- [ ] Every link works.

## 11. Release
- [ ] Final PDF from `make paper-pdf` on `main`, at most 25 MB.
- [ ] The submission form filled from [`form-fields.md`](form-fields.md): title, abstract, PDF, tracks 1 and 3, project image, code URL.
- [ ] Submit **once** before 19:59 HKT, and check that the confirmation email arrives.
