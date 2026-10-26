<!-- Implements: reports/submission-pack, specs-and-docs/folder-guides -->
# Submitting to the sprint

Everything for submitting "Something to Lose" to the [Apart AI Collusion Research Sprint](https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25).

**Deadline: Monday 26 October 2026, 19:59 HKT** (Sunday 25 October, 23:59 AoE). **Submit once:** resubmitting updates the form's details but never replaces the PDF.

## What's here

- [`checklist.md`](checklist.md) (a draft proposal for Al to go through): one checklist for the repo, the results, the paper and the form. Each item has an owner and a link, and is ticked only when it's true on `main`.
- [`form-fields.md`](form-fields.md): every field of the submission form, with a value ready to paste, and what only Al can fill in.
- The project image (optional): [`project-image.png`](../reports/paper/figures/project-image.png) and [`.svg`](../reports/paper/figures/project-image.svg). It's built with the paper's figures by `make paper-figures` (`reports/paper/project_image.py`).

## The order

1. **Merge the results.** Merge the open pull requests in checklist section 2, then check that `make reproduce` passes on `main`.
2. **Finish the paper.** Do checklist section 3, writing the abstract last. The form's summary is that abstract, word for word.
3. **Build the final PDF** from `main` with `make paper-pdf`. Check it's at most 8 pages before the appendices and at most 25 MB.
4. **Check the repo.** It's public, its README marks anything written before the sprint (nothing is), and every link in the paper works.
5. **Fill in the form** from `form-fields.md`, then submit once before 19:59 HKT.
6. **Confirm** that the confirmation email arrives. The project page can take up to 12 hours to appear, so check it then.
7. **Optional, the recording:** record it after submitting if there's time. Then resubmit the form **with the exact same title** before the deadline to add the link. That updates the details and leaves the PDF as it is.

## How the site shows a submission

From the sprint page and from submitted projects:

- **The entries grid** shows text cards only: the title, the team, and the first four lines of the summary. So the summary's first sentence carries the project.
- **The project page** shows the title, then the authors and team, then the summary in full. Each line break becomes a paragraph, and Markdown isn't rendered. The project image comes next, below the summary, about 600 px wide and at most 448 px tall, uncropped. The sidebar has buttons for "Read the report", "Recording", "Code", and a link for additional material.
- **Judges score the PDF** on three criteria: impact and innovation, execution quality, and presentation and clarity. Tracks don't affect the score.
