<!-- Implements: reports/paper-source, specs-and-docs/folder-guides -->
# Paper

The paper, written once in Markdown and built three ways: HTML for writing, LaTeX for Overleaf, and the PDF that gets submitted.

- **The text:** `body.md` (the abstract, in its front matter, then every section up to the LLM usage statement) and `appendix.md`. This is what you edit.
- **The skeleton:** `paper.md` holds the title-page fields and the plumbing: where the text goes, the page-count label, the references and the appendix switch. `include.lua` pulls `body.md` and `appendix.md` in where its include blocks name them.
- **The references:** `references.bib`.
- **The look:** `apart.latex` (the PDF's template: title page, caution box, running header), and `apart.html` with `style.css` (the HTML at the PDF's proportions).
- **The rules:** `check.py` warns when the abstract falls outside 150–250 words or the body runs past 8 pages.
- **For reference:** `template/` holds the sprint's official template.
- **Figures** come from `reports/paper/figures/` (`make paper-figures` rebuilds them).

## Build

```sh
make paper-watch   # the writing loop: rebuilds on every save; preview at http://127.0.0.1:8765/preview.html
make paper-html    # paper/build/paper.html
make paper-tex     # paper/build/paper.tex, with references.bib and figures/ beside it, ready for Overleaf
make paper-pdf     # paper/build/paper.pdf (tectonic)
```

`make paper-watch` (`watch.sh`, `preview.html`) needs `fswatch`, `pandoc`, `tectonic` and `pdftoppm` (`brew install fswatch pandoc tectonic poppler`). The preview shows the HTML beside the PDF's pages, so page breaks show as you type. Output goes to `paper/build/`, which isn't committed.

## Published preview

Every push to a pull request that touches the paper builds it in CI (`.github/workflows/paper-preview.yml`). The HTML and PDF go to GitHub Pages under `pr-<number>/`, and one comment on the pull request links them. `main`'s build is the published report: <https://al-beton.github.io/something-to-lose-apart-ai-collusion/>.
