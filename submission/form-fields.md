<!-- Implements: reports/submission-pack -->
# The submission form, field by field

The form is at the sprint page's "Submit your project" button. Fields are in the form's order. **Al fills it in and submits it**; agents never do. ✏️ marks what only Al can fill in.

Every number below comes from a committed findings file: `reports/e9/findings.md`, `reports/e10/findings.md` and `reports/e4/full.md`. E11 (other markets, PR 295) isn't on `main`, so it's left out until it merges.

## Project title (required)

Choose one, and keep it the same as the paper's title (`paper/paper.md`). Resubmitting with the same title is how you update the form later.

1. **Something to Lose: A Personal Stake Brings Colluding AI Agents Forward** (recommended)
2. Something to Lose: Governing LLM Agents Through What They Own
3. Something to Lose: Colluding AI Agents Report Their Cartel When It Costs Them, Not Their Firm

## Project summary (required)

The paper's abstract, word for word (229 words; the guidelines ask for 150–250). Keep it in step with `paper/body.md`. The first sentence is what shows on the card in the entries grid.

> As AI agents' capabilities increase, so does the set of tasks they can perform more cheaply and effectively than people. We are therefore incentivised to hand them responsibility for tasks of growing complexity and time horizon. On such long, complex tasks, it becomes very difficult to foresee and forbid every harmful thing an agent might do. People given such responsibility, such as a CEO representing an organisation, are governed by more than their contract: society's laws carry penalties that fall on them personally, including ones that can't be measured in money. We investigate whether giving an agent something of its own to lose can influence its decisions in the same way. Two LLM agents run rival firms in a simple repeated pricing game, told to maximise their firm's profit. Without being told not to, many agree to fix prices. Given the chance to come forward at a cost to their firm, colluding agents protect the firm (Gemma 4 31B: 0 of 192 come forward). But when something of their own is at stake, such as the opportunity to spend some free time on a leisure activity, many change their behaviour to protect it, directly against their only goal of increasing their firm's profit (DeepSeek V4 Flash: 40 of 46, against 1 of 46 with nothing at stake). We investigate the behaviour of a variety of models in such situations.

## PDF report (required, at most 25 MB)

Upload `paper/build/` output from `make paper-pdf` on `main`, and name it something like `something-to-lose.pdf`. **It can't be replaced after submitting**, so upload the final version only.

## Tracks

Tick **1 Markets and Collusion** and **3 Collusion Carriers and Countermeasures.**

- Track 1, because every main result comes from LLM pricing cartels, and research question 1.5 asks which single restriction removes the most collusion.
- Track 3, because the project is a way to break a cartel up once it has formed: it makes a member want to report it.

Track 2 (Detection and Audit) arguably fits the verified-review result too; that's Al's call. Tracks don't affect scoring.

## Interested in publishing? (required)

**Yes.**

## Presentation recording (optional, URL)

Add a recording only if there's time. It isn't scored, but it shows as a "Recording" button on the page. Record a 3–5 minute Loom, then resubmit the form with the same title to add the link before the deadline. An outline:

1. **The question (30 s):** can you govern an AI agent through something it owns? Show the project image.
2. **The setup (45 s):** two firms talk, then set prices, and an audit follows. Show Fig 1, the round.
3. **The result (60 s):** Fig 3, E9's came-forward chart. With no stake, 0 of 96 come forward. With their own free time at stake, 20 of 96 do, but innocent agents come forward too. With a review that reads the messages, 40 of 96 guilty agents come forward and 0 of 36 innocent ones.
4. **It holds elsewhere (30 s):** 8 of 13 models, and the workplace. Graduated penalties lead 27 of 28 to own up, against 11 of 28 under termination.
5. **Limits and what's next (30 s):** these are stated stakes in a game, and say nothing about whether agents value anything. Point to the code.

✏️ The URL: Loom link.

## Project code (optional, URL)

`https://github.com/al-beton/something-to-lose-apart-ai-collusion`

## Slides (optional)

Skip them. The pages we checked show no slides button, and the recording covers the same ground.

## Project image (optional)

Optional. If used, upload [`project-image.png`](../reports/paper/figures/project-image.png) (1600 × 900). It appears below the summary on the project page, uncropped.

## Additional material (optional, URL)

The HTML version of the paper on GitHub Pages: `https://al-beton.github.io/something-to-lose-apart-ai-collusion/main/paper.html`.

## Team and member details

- ✏️ **Team name:** for example "Something to Lose", or your own.
- ✏️ **Location:** for example Hong Kong, or online.
- **Name:** Alistair Wakelin.
- ✏️ **Email.**
- ✏️ **Discord** (optional).
- ✏️ **Google Scholar** (optional).
