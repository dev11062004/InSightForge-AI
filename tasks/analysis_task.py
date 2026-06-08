import textwrap
from crewai import Task
from agents.data_analyst import data_analyst_agent
from tasks.research_task import research_task
from test_mode import TEST_MODE

# ── TEST_MODE prompt ──────────────────────────────────────────────────────────
_desc_test = textwrap.dedent("""
    Based on the research, list 3 challenges for {company}.
    Format:
    - Challenge 1: [one sentence]
    - Challenge 2: [one sentence]
    - Challenge 3: [one sentence]
    Maximum 60 words. No explanations. No headers.
""")

_expected_test = "3 bullet-point challenges for {company}. Under 60 words."

# ── PRODUCTION prompt ─────────────────────────────────────────────────────────
_desc_prod = textwrap.dedent("""
    Conduct a Business Intelligence analysis on: **{company}**

    Use the research dossier from the previous task. Do NOT repeat research content —
    add analysis and interpretation only.

    ---

    ## PART 1: BUSINESS MODEL (concise)

    ### Revenue Drivers
    Top 3 drivers — one bullet each: Driver | Estimated contribution | Evidence

    ### Customer Segments
    Top 2-3 segments — one bullet each: Segment | Profile | Key need

    ### Competitive Position
    - Top 3 competitors and {company}'s main differentiator vs each
    - Porter's Five Forces: one sentence per force with rating [Low/Med/High]
    - SWOT: 2 bullets per quadrant

    ---

    ## PART 2: CHALLENGE IDENTIFICATION

    Identify EXACTLY 6 challenges. Use this format for each:

    ### Challenge [N]: [Title]
    - **Category**: [Operational / Sales / CX / Growth / Technology]
    - **Challenge**: [Specific problem — 1-2 sentences]
    - **Evidence**: [Direct data point from research]
    - **Business Impact**: [Quantified or qualified impact]
    - **Confidence Score**: [X/10] — [One sentence justification]

    ---

    FORMAT: Concise markdown. Keep total output under 900 words.
    All claims must reference the research dossier.
""")

_expected_prod = textwrap.dedent("""
    A concise Business Intelligence analysis for {company} containing:
    - Business model summary (revenue drivers, segments, competitive position)
    - Exactly 6 challenges with evidence, impact, and confidence scores
    - SWOT summary
    Under 900 words. Clean markdown.
""")

analysis_task = Task(
    agent=data_analyst_agent,
    description=_desc_test if TEST_MODE else _desc_prod,
    expected_output=_expected_test if TEST_MODE else _expected_prod,
    context=[research_task],
    output_file="analysis_report.md",
)
