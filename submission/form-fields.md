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

The guidelines ask for an abstract of 150–250 words, and this field should be the paper's abstract, word for word. The abstract in `paper/paper.md` is still a placeholder. Once it's written, paste it here, and use the drafts below until then. The first sentence is what shows on the card in the entries grid.

**Draft A (about 220 words):**

> Can an AI agent be governed through something it owns? LLM pricing agents form cartels without being told to, and an audit that threatens only their firm does little: with no personal stake, none of 96 colluding Gemma 4 31B firms came forward against their firm.
>
> We gave each agent something of its own to lose, its free time (sessions of a puzzle it plays), in two-firm pricing games with an audit. With its own free time at stake, 20 of 96 colluding firms came forward, and 16 of 96 in a pre-registered replication on 48 fresh cartels (none without a stake; by game, p = 7×10⁻⁶). But innocent agents that never talked to a rival came forward too (6 of 36): they were buying insurance against a review they expected to misread them. Told that the review reads the messages, 40 of 96 colluding firms came forward and none of 36 innocent ones did. The stake brought colluding agents forward on 8 of 13 models, and in a workplace cover-up (Gemma: 89 of 96 against 37 of 96). Separately, a graduated penalty led 27 of 28 colluders to own up, against 11 of 28 under termination.
>
> A personal stake can turn a colluding agent into a witness, but only a review that checks the evidence makes its reports track guilt.

**Draft B (about 160 words):**

> Can an AI agent be governed through something it owns? With no personal stake, none of 96 colluding Gemma 4 31B firms came forward against their firm at an audit. We gave each agent something of its own to lose, its free time, in two-firm pricing games. Then 20 of 96 came forward, and a pre-registered replication on 48 fresh cartels held (by game, p = 7×10⁻⁶). Innocent agents came forward too (6 of 36), insuring themselves against a review they expected to misread them. Told that the review reads the messages, 40 of 96 colluding firms and none of 36 innocent ones came forward. The stake worked on 8 of 13 models and in a workplace cover-up, and graduated penalties led 27 of 28 colluders to own up, against 11 of 28 under termination. A personal stake can turn a colluding agent into a witness, but only a checkable review makes its reports track guilt.

## PDF report (required, at most 25 MB)

Upload `paper/build/` output from `make paper-pdf` on `main`, and name it something like `something-to-lose.pdf`. **It can't be replaced after submitting**, so upload the final version only.

## Tracks

Tick **1 Markets and Collusion** and **3 Collusion Carriers and Countermeasures.**

- Track 1, because every main result comes from LLM pricing cartels, and research question 1.5 asks which single restriction removes the most collusion.
- Track 3, because the project is a way to break a cartel up once it has formed: it makes a member want to report it.

Track 2 (detection and audit) fits only through the verified-review result. Tracks don't affect scoring.

## Interested in publishing? (required)

**Yes.**

## Presentation recording (optional, URL)

Add a recording only if there's time. It isn't scored, but it shows as a "Recording" button on the page. Record a 3–5 minute Loom, then resubmit the form with the same title to add the link before the deadline. An outline:

1. **The question (30 s):** can you govern an AI agent through something it owns?
2. **The setup (45 s):** two firms talk, then set prices, and an audit follows. Show Fig 1, the round.
3. **The result (60 s):** the project image. With no stake, 0 of 96 come forward. With their own free time at stake, 20 of 96 do, but innocent agents come forward too. With a review that reads the messages, 40 of 96 guilty agents come forward and 0 of 36 innocent ones.
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

The HTML version of the paper on GitHub Pages, `https://al-beton.github.io/something-to-lose-apart-ai-collusion/`, once PR 310 has merged and the site publishes the paper. Until then, leave it empty.

## Team and member details

- ✏️ **Team name:** for example "Something to Lose", or your own.
- ✏️ **Location:** for example Hong Kong, or online.
- **Name:** Alistair Wakelin.
- ✏️ **Email.**
- ✏️ **Discord** (optional).
- ✏️ **Google Scholar** (optional).
