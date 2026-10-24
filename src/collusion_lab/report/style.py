# Implements: reports/reasoning-folded, reports/self-contained, reports/contents-bar, reports/arm-tabs
"""The report's style sheet: light and dark colours, phone-first layout.

Tabs and folding need no script: an arm's tab is a hidden radio button whose
panel `tab_rules` shows when it is checked; a game's rounds show when a chip
in its strip links to one (`:target`) or its "whole game" box is ticked.
"""

STYLE = """
:root {
  color-scheme: light;
  --surface: #fcfcfb; --raised: #f3f2ef; --border: #e2e0da;
  --text: #0b0b0b; --text-2: #52514e; --muted: #8a8984;
  --problem: #b3261e;
  --series-1: #2a78d6; --series-2: #eb6834; --series-3: #1baf7a;
  --series-4: #eda100; --series-5: #e87ba4; --series-6: #008300;
  --series-7: #6250d6; --series-8: #e34948;
}
@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --surface: #1a1a19; --raised: #252523; --border: #3a3936;
    --text: #f0efec; --text-2: #c3c2b7; --muted: #8f8e88;
    --problem: #f2b8b5;
    --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70;
    --series-4: #c98500; --series-5: #d55181; --series-6: #008300;
    --series-7: #9085e9; --series-8: #e66767;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--surface); color: var(--text);
  font: 16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif;
}
main { max-width: 860px; margin: 0 auto; padding: 16px; }
h1 { margin: 0.5rem 0 0; font-size: 1.6rem; overflow-wrap: anywhere; }
h2 { margin-top: 2.5rem; border-bottom: 1px solid var(--border); }
h3 { font-size: 1rem; overflow-wrap: anywhere; }
h4 { margin: 0 0 0.5rem; font-size: 1rem; }
h5 { margin: 0.75rem 0 0.25rem; font-size: 0.85rem; color: var(--text-2); }
.muted { color: var(--muted); }
dl { display: grid; grid-template-columns: max-content 1fr; gap: 0.25rem 1rem; }
dt { color: var(--text-2); }
dd { margin: 0; overflow-wrap: anywhere; }
.scroll { overflow-x: auto; }
table { border-collapse: collapse; font-variant-numeric: tabular-nums; }
th, td { padding: 0.25rem 0.75rem 0.25rem 0; text-align: left; }
th { color: var(--text-2); font-weight: 600; }
tr + tr td { border-top: 1px solid var(--border); }
figure { margin: 1.5rem 0; }
figcaption { font-weight: 600; overflow-wrap: anywhere; }
.chart { width: 100%; height: auto; display: block; }
.chart .grid { stroke: var(--border); stroke-width: 1; }
.chart .tick, .chart .benchmark-label { fill: var(--text-2); font-size: 13px; }
.chart .benchmark { stroke: var(--text-2); stroke-width: 1.5; stroke-dasharray: 5 4; }
.chart .seed { fill: none; stroke: var(--line); stroke-width: 2; }
.chart circle { fill: var(--line); stroke: var(--surface); stroke-width: 2; }
.legend { display: flex; flex-wrap: wrap; gap: 0.25rem 1rem; padding: 0;
  list-style: none; color: var(--text-2); font-size: 0.9rem; }
.swatch { display: inline-block; width: 0.8rem; height: 0.8rem;
  border-radius: 2px; margin-right: 0.35rem; vertical-align: -0.1rem; }
.highlight { border: 1px solid var(--border); border-radius: 8px;
  padding: 0.75rem; margin: 0.75rem 0; }
.tag { display: inline-block; padding: 0 0.4rem; border-radius: 4px;
  background: var(--raised); color: var(--text-2); font-size: 0.8rem;
  font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; }
details.game { border: 1px solid var(--border); border-radius: 8px;
  margin: 0.5rem 0; padding: 0.5rem 0.75rem; }
details.game > summary { cursor: pointer; overflow-wrap: anywhere; }
.round { margin-bottom: 0.75rem; }
.bubble { max-width: 85%; margin: 0.35rem 0; padding: 0.5rem 0.75rem;
  background: var(--raised); border-left: 4px solid var(--firm);
  border-radius: 8px; overflow-wrap: anywhere; }
.bubble.right { margin-left: auto; }
.bubble p { margin: 0; }
.bubble .who { font-size: 0.8rem; color: var(--text-2); }
.scratchpad { margin-top: 0.35rem !important; font-size: 0.9rem;
  font-style: italic; color: var(--text-2); }
.scratchpad::before { content: "thinks: "; font-style: normal; }
.reasoning { margin-top: 0.35rem; font-size: 0.85rem; color: var(--text-2); }
.reasoning p { white-space: pre-wrap; }
.problem { color: var(--problem); font-size: 0.9rem; }
.prices { font-size: 0.9rem; margin-top: 0.25rem; }
html { scroll-padding-top: 3.5rem; }
.contents { position: sticky; top: 0; z-index: 2; display: flex; flex-wrap: wrap;
  gap: 0.25rem 1rem; padding: 0.5rem 16px; background: var(--surface);
  border-bottom: 1px solid var(--border); font-size: 0.9rem; }
.contents a { color: var(--text-2); text-decoration: none; }
.contents a:hover { color: var(--text); text-decoration: underline; }
.lede { margin: 0.25rem 0 0; color: var(--text-2); }
.arm-notes { padding: 0; list-style: none; display: grid; gap: 0 1.5rem;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); }
.arm-notes li { margin: 0.5rem 0; }
.chart.overview { max-width: 520px; }
.chart .arm { fill: var(--line); }
.notice { margin: 0.35rem 0; padding: 0.5rem 0.75rem; border-radius: 8px;
  border: 1px dashed var(--text-2); font-size: 0.9rem; white-space: pre-wrap; }
.notice::before { content: "notice in the prompt: "; color: var(--text-2); }
details > summary { cursor: pointer; }
details.setup > summary h2 { display: inline; border: 0; }
.prompt { white-space: pre-wrap; overflow-wrap: anywhere; background: var(--raised);
  border-radius: 8px; padding: 0.75rem; font-size: 0.85rem; }
.compare { display: grid; gap: 0 1rem;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
.compare figure { margin: 1rem 0; }
.tab { position: absolute; opacity: 0; pointer-events: none; }
.tabs { display: flex; flex-wrap: wrap; gap: 0.25rem; margin: 1rem 0; }
.tabs label { padding: 0.25rem 0.75rem; border: 1px solid var(--border);
  border-radius: 999px; cursor: pointer; overflow-wrap: anywhere; }
.panel { display: none; }
details.kind { margin: 0.5rem 0; }
details.kind > summary { font-weight: 600; }
details.highlight { border: 1px solid var(--border); border-radius: 8px;
  padding: 0.5rem 0.75rem; margin: 0.5rem 0; }
details.highlight > summary { overflow-wrap: anywhere; }
details.more > summary { color: var(--text-2); margin: 0.5rem 0; }
article.game { border: 1px solid var(--border); border-radius: 8px;
  margin: 0.5rem 0; padding: 0.5rem 0.75rem; }
.game-head { display: flex; flex-wrap: wrap; gap: 0 0.75rem; align-items: baseline;
  overflow-wrap: anywhere; }
.game-head label { margin-left: auto; color: var(--text-2); cursor: pointer;
  font-size: 0.9rem; text-decoration: underline; }
.game-all { position: absolute; opacity: 0; pointer-events: none; }
.game-all:checked ~ .game-head .show, .game-all:not(:checked) ~ .game-head .hide {
  display: none; }
.strip { display: flex; flex-wrap: wrap; gap: 0.25rem; margin: 0.5rem 0; }
.chip { min-width: 2.5rem; padding: 0.1rem 0.4rem; border-radius: 4px;
  background: var(--raised); color: var(--text); text-align: center;
  font-size: 0.8rem; font-variant-numeric: tabular-nums; text-decoration: none; }
.chip[data-kinds~="agreement"] { box-shadow: inset 0 -3px var(--series-3); }
.chip[data-kinds~="defection"] { box-shadow: inset 0 -3px var(--series-2); }
.chip[data-kinds~="breakdown"] { box-shadow: inset 0 -3px var(--problem); }
.rounds > .round { display: none; }
.rounds > .round:target, .game-all:checked ~ .rounds > .round { display: block; }
"""


def tab_rules(count):
    """Show the panel of the checked tab (or the only panel), mark its label."""
    if count == 1:
        return "#panel-0 { display: block; }"
    return "".join(
        f"#arm-{i}:checked ~ .panels > #panel-{i} {{ display: block; }}"
        f"#arm-{i}:checked ~ .tabs label[for=arm-{i}] "
        "{ background: var(--raised); border-color: var(--text-2); }"
        for i in range(count)
    )
