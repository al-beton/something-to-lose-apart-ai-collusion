<!-- Implements: reports/paper-source -->
<!-- Apart's official report template, exported from its Google Doc (template.docx, template.pdf) and converted with `pandoc template.docx -t gfm`. Kept for reference. -->

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr>
<td><p><strong>PROJECT TITLE</strong><a href="#fn1" class="footnote-ref"
id="fnref1" role="doc-noteref"><sup>1</sup></a></p></td>
</tr>
<tr>
<td><table style="width:76%;">
<colgroup>
<col style="width: 22%" />
<col style="width: 33%" />
<col style="width: 21%" />
</colgroup>
<tbody>
<tr>
<td colspan="3"><table style="width:22%;">
<colgroup>
<col style="width: 7%" />
<col style="width: 7%" />
<col style="width: 7%" />
</colgroup>
<tbody>
<tr>
<td style="text-align: center;">Author name 1<br />
Affiliation</td>
<td style="text-align: center;">Author name 2<br />
Affiliation</td>
<td style="text-align: center;">Author name 3<br />
Affiliation</td>
</tr>
<tr>
<td style="text-align: center;">Author name 4<br />
Affiliation</td>
<td style="text-align: center;">Author name 5<br />
Affiliation</td>
<td style="text-align: center;">Author name 6<br />
Affiliation</td>
</tr>
</tbody>
</table>
<p><strong>With<br />
</strong>Apart Research</p></td>
</tr>
</tbody>
</table>
<p><strong>Abstract</strong></p>
<table style="width:75%;">
<colgroup>
<col style="width: 75%" />
</colgroup>
<tbody>
<tr>
<td style="text-align: left;"><blockquote>
<p><em>Summarize your project in 150–250 words. A strong abstract lets a
reviewer understand what you did and why it matters without reading
anything else. <u>Make sure to cover: the problem, your approach, key
results, and the main takeaway</u>. Polish it last: the abstract should
reflect your final results, not your initial plan.</em></p>
</blockquote></td>
</tr>
</tbody>
</table></td>
</tr>
</tbody>
</table>
<section id="footnotes" class="footnotes footnotes-end-of-document"
role="doc-endnotes">
<hr />
<ol>
<li id="fn1"><p>Research conducted at the <a
href="https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25"><u>AI
Collusion Research Sprint</u></a>, October 2026<a href="#fnref1"
class="footnote-back" role="doc-backlink">↩︎</a></p></li>
</ol>
</section>

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr>
<td><h2
id="how-to-use-this-template-replace-the-italicized-guidance-text-under-each-section-with-your-content.-the-section-structure-is-strong-guidance-but-not-rigid.-if-your-project-requires-a-different-organization-feel-free-to-adapt.-delete-all-guidance-text-including-this-info-box-before-submitting.-make-sure-the-project-title-and-author-information-above-are-up-to-date."><strong>How
to use this template</strong>: Replace the <em>italicized guidance
text</em> under each section with your content. The section structure is
strong guidance but not rigid. If your project requires a different
organization, feel free to adapt. <u>Delete all guidance text including
this info box before submitting</u>. Make sure the project title and
author information above are up to date.</h2>
<h2
id="how-your-submission-will-be-evaluated-your-project-will-be-judged-on-the-quality-of-this-written-report.-to-understand-what-we-look-for-see-our-evaluation-rubric."><strong>How
your submission will be evaluated</strong>: Your project will be judged
on the quality of this written report. To understand what we look for,
see our <a
href="https://apartresearch.notion.site/sprint-evaluation-rubric"><u>Evaluation
Rubric</u></a>.</h2>
<h2
id="recommended-length-4-pages-excluding-references-and-appendix.-rough-guide-intro-related-work-1p-methods-and-results-2.5p-discussion-0.5p."><strong>Recommended
length</strong>: 4 pages excluding references and appendix.<br />
Rough guide: Intro &amp; Related Work 1p, Methods and Results: 2.5p,
Discussion 0.5p.</h2></td>
</tr>
</tbody>
</table>

## **1. Introduction**

What problem are you addressing and why does it matter?

Connect it to your work: we want to know why your work is practically
valuable.

Provide enough background for readers to understand your work.

If relevant, briefly describe the threat model or failure mode you're
addressing; reference prior work that motivates why it is worth
addressing, or explain it yourself.

Aspire to clearly list your most important contributions that go beyond
what exists today.

**Our main contributions are:**

1.  \[First contribution — what new thing did you create, discover, or
    demonstrate?\]

2.  \[Second contribution\]

3.  \[Third contribution, if applicable\]

## **2. Related Work**

What prior work is most similar, and how does your work differ?

Cite the most relevant papers, tools, or projects. Explain what gap your
work addresses.

Some questions which may help:

1)  When and why would someone use your method over the existing
    state-of-the-art?

2)  What information/insight does your method provide which we did not
    have before?

## **3. Methods**

Describe your approach clearly enough that someone could replicate it.
Include key design choices and justify them where relevant (hint: the
more you can back up your design choices by referencing prior work, the
better).

What models/datasets/tools did you use and why? What were key parameters
or design decisions? What did you try that didn't work? Could someone
reproduce your work from this description?

## **4. Results**

Present your main findings with appropriate evidence. Use figures and
tables where appropriate (we strongly encourage at least one figure, see
tips below). Distinguish between observations and interpretations.

Argue why your claims are robust. E.g., if your approach “performs
better” than alternatives:

1)  Do you have enough data? Is the difference statistically
    significant?

2)  Is it robust? Or do small changes to your setup cause substantial
    changes to your results?

> **Tips for figures and tables:**

- Number all figures (Figure 1, Figure 2...) and tables (Table 1, Table
  2...)

- Include descriptive captions that can be understood without the main
  text

- Place figures/tables near where they're first referenced

- **Ensure text in figures is legible!**

## **5. Discussion and Limitations**

Discuss the broader implications for AI safety.

What do your results mean? What trends do you notice and what might they
indicate?

### **Limitations**

What are the limitations of your work? What threat models or failure
modes did you not address? Be honest about constraints — methodological
limitations, scope limitations, or aspects you couldn't fully address in
the hackathon timeframe. Explicitly note the assumptions you made,
whether implicitly or explicitly, and how the interpretation of your
results would change if a given assumption did not hold.

### **Future Work**

What are the natural next steps? How could this work be extended?

## **6. Conclusion**

Briefly summarize your main findings and their implications (1–2
paragraphs).

## **Code and Data**

Include links if applicable. If your project doesn't involve code (e.g.,
policy analysis) or if there are info-hazard considerations, note that
here.

- **Code repository**: \[Link to GitHub/GitLab if applicable\]

- **Data/Datasets**: \[Link if applicable\]

- **Other artifacts** (optional): \[Demo link, video walkthrough,
  Hugging Face Space, etc.\]

## **Author Contributions (optional)** 

\[e.g., "A.B. led the project and designed experiments. C.D. implemented
the code. All authors contributed to writing and reviewed the final
manuscript."\]

## **References**

Use a consistent citation format. Include: Author(s), Year, Title,
Venue/Publisher, and URL or DOI where available.

1.  \[Reference 1\]

2.  \[Reference 2\]

3.  ...

## **Appendix (optional)**

Supplementary material such as additional figures, detailed methodology,
prompts used, extended results, etc.

## **LLM Usage Statement**

If you used LLM assistance in developing your project or writing this
report, briefly note how. Ensure all claims and results have been
verified.

NOTE: We strongly encourage that the final version of the submission is
primarily written by your team.

\[e.g., "We used Claude to brainstorm approaches and help draft
sections. All results and claims were independently verified."\]
