import textwrap
from crewai import Task
from agents.research_specialist import research_specialist_agent
from test_mode import TEST_MODE

# ── TEST_MODE prompt: ~50 tokens in, ~80 tokens out ──────────────────────────
_desc_test = textwrap.dedent("""
    Research {company} and return exactly 3 bullet points.
    Format:
    - [Fact 1 about the company]
    - [Fact 2 about the company]
    - [Fact 3 about the company]
    Maximum 60 words. No explanations. No headers.
""")

_expected_test = "3 bullet points about {company}. Under 60 words."

# ── PRODUCTION prompt ─────────────────────────────────────────────────────────
_desc_prod = textwrap.dedent("""
    Conduct corporate intelligence research on: **{company}**

    Search across company website, news, press releases, Wikipedia, and industry reports.
    Be concise — bullet points preferred over paragraphs. Cite every factual claim.

    ## 1. COMPANY OVERVIEW
    - Full name, founding year, headquarters, type (Public/Private)
    - Core business (2 sentences max)
    - CIN / stock ticker if listed

    ## 2. FINANCIALS
    - Annual revenue (most recent year) [Source]
    - Revenue trend (growing/stable/declining)
    - Key profitability metric if available

    ## 3. BUSINESS SEGMENTS
    - List all segments with 1-sentence description each

    ## 4. LEADERSHIP
    - CEO/MD name and brief background
    - 2-3 other key executives

    ## 5. RECENT NEWS (last 12 months)
    - 5 most important developments: [Date] Headline — Source URL

    ## 6. EXPANSION & PARTNERSHIPS
    - 3-4 announced projects or partnerships with timelines if known

    ## 7. COMPETITIVE POSITION
    - Top 3 competitors (name only + one differentiator)
    - {company}'s main competitive advantage

    ---
    FORMAT: Clean markdown bullet points. Every fact ends with [Source: name].
    Flag missing info as [NOT FOUND]. Do NOT fabricate data.
    KEEP OUTPUT UNDER 1200 WORDS.
""")

_expected_prod = textwrap.dedent("""
    A structured markdown research dossier on {company} covering all 7 sections.
    Every factual claim attributed to a source. Under 1200 words.
    Clean markdown with ## section headers.
""")

research_task = Task(
    agent=research_specialist_agent,
    description=_desc_test if TEST_MODE else _desc_prod,
    expected_output=_expected_test if TEST_MODE else _expected_prod,
    output_file="research_findings.md",
)
