import textwrap
from crewai import Task
from agents.ai_strategy_agent import ai_strategy_agent
from tasks.analysis_task import analysis_task
from test_mode import TEST_MODE

# NOTE: Context is [analysis_task] only — analysis already digested the research.

# ── TEST_MODE prompt ──────────────────────────────────────────────────────────
_desc_test = textwrap.dedent("""
    Based on the challenges, suggest 3 AI solutions for {company}.
    Format:
    - AI Solution 1: [one sentence]
    - AI Solution 2: [one sentence]
    - AI Solution 3: [one sentence]
    Maximum 60 words. No explanations. No headers.
""")

_expected_test = "3 bullet-point AI solutions for {company}. Under 60 words."

# ── PRODUCTION prompt ─────────────────────────────────────────────────────────
_desc_prod = textwrap.dedent("""
    Design an AI Transformation Strategy for: **{company}**

    Use ONLY the Business Intelligence analysis from the previous task.
    Do NOT re-summarise prior content — go straight to recommendations.

    For each of the 6 challenges identified by the analyst, design one AI solution.

    Use EXACTLY this format for each:

    ---

    ### AI Opportunity [N]: [Title]
    - **Addresses**: Challenge [N] — [Challenge Title]
    - **Solution**: [Specific named solution — platform, integration point, deployment model]
    - **Tech Stack**: [Specific tools: LLM name, framework, API, platform]
    - **Implementation**:
      - Phase 1 (0-3 mo): [2-3 specific steps]
      - Phase 2 (3-9 mo): [2-3 specific steps]
    - **Estimated ROI**: [Quantified estimate with 1-sentence reasoning]
    - **Business Impact**: [1-2 specific measurable outcomes]

    ---

    After all 6 opportunities, add:

    ## Strategic Roadmap Summary
    | Phase | Timeline | Top 2 Initiatives | Expected Impact |
    |-------|----------|-------------------|-----------------|
    | Quick Wins | 0-6 mo | ... | ... |
    | Core Build | 6-18 mo | ... | ... |
    | Scale | 18-36 mo | ... | ... |

    ## Investment Estimate
    [Low / Medium / High tier with 2-sentence justification]

    ---
    FORMAT: Concise markdown. Solutions must be {company}-specific.
    KEEP OUTPUT UNDER 1000 WORDS.
""")

_expected_prod = textwrap.dedent("""
    An AI strategy document for {company} with:
    - Exactly 6 AI opportunity recommendations (one per challenge)
    - Each with: solution, tech stack, 2-phase implementation, ROI, impact
    - A phased roadmap summary table
    - Investment tier estimate
    Under 1000 words. Clean markdown. Company-specific, not generic.
""")

ai_strategy_task = Task(
    agent=ai_strategy_agent,
    description=_desc_test if TEST_MODE else _desc_prod,
    expected_output=_expected_test if TEST_MODE else _expected_prod,
    context=[analysis_task],
    output_file="ai_strategy_report.md",
)
