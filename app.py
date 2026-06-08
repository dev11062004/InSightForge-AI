import groq_patch        # noqa: F401  — must be first; patches litellm before crewai loads
import rate_limit_retry  # noqa: F401  — must be second; adds retry-with-backoff on RateLimitError
from rate_limit_retry import format_rate_limit_message
from test_mode import TEST_MODE

import streamlit as st
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Company Intelligence System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main { background: #0a0e1a; }

/* Hero banner */
.hero-banner {
    background: linear-gradient(135deg, #0D1B2A 0%, #1565C0 50%, #0D47A1 100%);
    padding: 2.5rem 2rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 20px 60px rgba(0,0,0,0.4);
}
.hero-title {
    font-size: 2.4rem; font-weight: 700; color: #FFFFFF;
    margin: 0; line-height: 1.2;
}
.hero-subtitle {
    font-size: 1.05rem; color: #90CAF9; margin-top: 0.5rem;
}
.hero-badge {
    display: inline-block; background: rgba(249,168,37,0.15);
    border: 1px solid #F9A825; color: #F9A825; border-radius: 20px;
    padding: 4px 14px; font-size: 0.75rem; font-weight: 600;
    margin-top: 1rem;
}

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, #0D1B2A, #1B2A3B);
    border: 1px solid rgba(21,101,192,0.3);
    border-radius: 12px; padding: 1.2rem;
    text-align: center; height: 100%;
    transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 30px rgba(21,101,192,0.3);
}
.metric-icon  { font-size: 2rem; margin-bottom: 0.4rem; }
.metric-value { font-size: 1.6rem; font-weight: 700; color: #F9A825; }
.metric-label { font-size: 0.78rem; color: #90CAF9; margin-top: 0.2rem; }

/* Pipeline steps */
.pipeline-step {
    background: #0D1B2A; border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.6rem;
    display: flex; align-items: center; gap: 12px;
    transition: border-color 0.3s;
}
.pipeline-step.active  { border-color: #F9A825; background: rgba(249,168,37,0.05); }
.pipeline-step.done    { border-color: #2E7D32; background: rgba(46,125,50,0.05); }
.pipeline-step.pending { border-color: rgba(255,255,255,0.06); }
.step-icon  { font-size: 1.5rem; min-width: 2rem; text-align: center; }
.step-title { font-size: 0.9rem; font-weight: 600; color: #E0E0E0; }
.step-desc  { font-size: 0.75rem; color: #78909C; margin-top: 2px; }

/* Company chip */
.company-chip {
    background: linear-gradient(135deg, #1565C0, #0D47A1);
    color: white; border-radius: 25px; padding: 6px 18px;
    display: inline-block; font-weight: 600; font-size: 0.85rem;
    margin: 4px; border: 1px solid rgba(255,255,255,0.15);
}

/* Section header */
.section-header {
    background: linear-gradient(90deg, #0D1B2A, transparent);
    border-left: 4px solid #1565C0; padding: 0.8rem 1rem;
    border-radius: 0 8px 8px 0; margin: 1rem 0 0.6rem 0;
    font-size: 1.1rem; font-weight: 600; color: #E0E0E0;
}

/* Status badge */
.badge-success { background:#1B5E20; color:#A5D6A7; border-radius:20px; padding:4px 12px; font-size:0.8rem; font-weight:600; }
.badge-warning { background:#4A2C00; color:#FFCC80; border-radius:20px; padding:4px 12px; font-size:0.8rem; font-weight:600; }
.badge-error   { background:#4E0000; color:#EF9A9A; border-radius:20px; padding:4px 12px; font-size:0.8rem; font-weight:600; }

/* Tab content */
.report-content {
    background: #0D1B2A; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px; padding: 1.5rem;
}

/* Override streamlit button */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #1565C0, #0D47A1) !important;
    color: white !important; border: none !important;
    border-radius: 8px !important; font-weight: 600 !important;
    padding: 0.55rem 1.8rem !important;
    transition: all 0.2s !important;
}
div[data-testid="stButton"] > button:hover {
    background: linear-gradient(135deg, #1976D2, #1565C0) !important;
    box-shadow: 0 4px 15px rgba(21,101,192,0.5) !important;
    transform: translateY(-1px) !important;
}

/* Confidence score badge */
.conf-high { color: #66BB6A; font-weight: 700; }
.conf-mid  { color: #FFA726; font-weight: 700; }
.conf-low  { color: #EF5350; font-weight: 700; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def check_api_keys():
    missing = [v for v in ["SERPER_API_KEY", "GROQ_API_KEY"] if not os.getenv(v)]
    return missing


def get_report_stats(report_text: str) -> dict:
    """Extract quick stats from the final report."""
    word_count   = len(report_text.split())
    source_count = report_text.count("[Source:")
    challenge_n  = report_text.lower().count("## challenge")
    ai_opps_n    = report_text.lower().count("### ai opportunity")
    return {
        "words":      word_count,
        "sources":    source_count,
        "challenges": challenge_n,
        "ai_opps":    ai_opps_n,
    }


def load_file(path: str) -> str:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def select_company(sample_name: str):
    st.session_state["company_input"] = sample_name


SAMPLE_COMPANIES = [
    "Adani Realty", "Sobha Limited", "Prestige Group",
    "Brigade Group", "Puravankara", "DLF Limited",
    "Godrej Properties", "Lodha Group",
]

PIPELINE_STEPS = [
    ("🔍", "Research Specialist",    "Gathering corporate intelligence from multiple sources"),
    ("📊", "Business Analyst",       "Analyzing business model, challenges & competitive landscape"),
    ("🤖", "AI Strategy Consultant", "Designing AI solutions for each identified challenge"),
    ("✍️", "Executive Writer",       "Producing the full BI report and CEO pitch"),
]


# ── Session state init ────────────────────────────────────────────────────────
for key, default in {
    "analysis_done":    False,
    "analysis_error":   None,
    "current_company":  "",
    "current_step":     -1,
    "start_time":       None,
    "elapsed":          0,
    "company_input":    "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    missing = check_api_keys()

    if missing:
        st.error("❌ Missing API Keys")
        for v in missing:
            st.code(f"{v}=your_key_here")
        st.info("Create a `.env` file in the project root with your keys.")
    else:
        st.success("✅ API Keys Configured")

    st.markdown("---")
    # ── TEST_MODE status banner ──────────────────────────────────
    if TEST_MODE:
        st.warning(
            "🧪 **TEST MODE ON**\n\n"
            "Using minimal prompts + smallest model.\n"
            "Output will be placeholder-quality.\n\n"
            "Set `TEST_MODE=false` in `.env` or `test_mode.py` for full reports."
        )
    else:
        st.info("📄 **Production Mode** — full reports enabled")

    st.markdown("---")
    st.markdown("### 🤖 Agent Pipeline")
    for icon, name, desc in PIPELINE_STEPS:
        st.markdown(f"**{icon} {name}**")
        st.caption(desc)
        st.markdown("")

    st.markdown("---")
    st.markdown("### 📋 Output Files")
    files = [
        ("🔍", "research_findings.md",  "Research Dossier"),
        ("📊", "analysis_report.md",    "BI Analysis"),
        ("🤖", "ai_strategy_report.md", "AI Strategy"),
        ("📝", "final_report.md",       "Full Report"),
        ("👔", "ceo_pitch.md",          "CEO Pitch"),
    ]
    for icon, fname, label in files:
        exists = os.path.exists(fname)
        status = "✅" if exists else "⬜"
        st.markdown(f"{status} {icon} `{label}`")

    st.markdown("---")
    st.caption("AI Company Intelligence System v2.0")
    st.caption("Powered by CrewAI · Groq · Serper")


# ── Main content ──────────────────────────────────────────────────────────────

# Hero
st.markdown("""
<div class="hero-banner">
    <div class="hero-title">🏢 AI Company Intelligence System</div>
    <div class="hero-subtitle">Multi-Agent Business Intelligence · AI Strategy · CEO Pitch</div>
    <span class="hero-badge">🚀 Powered by CrewAI 4-Agent Pipeline</span>
</div>
""", unsafe_allow_html=True)

# Input section
col_input, col_run = st.columns([3, 1])
with col_input:
    company = st.text_input(
        "🏢 Enter Company Name",
        placeholder="e.g., Prestige Group, Sobha Limited, Brigade Group...",
        help="Enter any Indian real estate or business conglomerate name",
        key="company_input",
    )

with col_run:
    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button(
        "🚀 Analyze Company",
        disabled=bool(missing),
        use_container_width=True,
        key="run_btn",
    )

# Quick-select companies
st.markdown("**Quick select:**")
cols = st.columns(len(SAMPLE_COMPANIES))
for i, sample in enumerate(SAMPLE_COMPANIES):
    with cols[i]:
        st.button(
            sample,
            key=f"sample_{i}",
            use_container_width=True,
            on_click=select_company,
            args=(sample,),
        )

st.markdown("---")

# ── Run analysis ──────────────────────────────────────────────────────────────
if run_btn and company.strip():
    from crew import intelligence_crew

    st.session_state.analysis_done  = False
    st.session_state.analysis_error = None
    st.session_state.current_company = company.strip()
    st.session_state.start_time = time.time()

    # Pipeline progress UI
    progress_placeholder = st.empty()
    status_placeholder   = st.empty()
    timer_placeholder    = st.empty()

    def render_pipeline(active_step: int):
        html = ""
        for idx, (icon, name, desc) in enumerate(PIPELINE_STEPS):
            if idx < active_step:
                css, prefix = "done",    "✅"
            elif idx == active_step:
                css, prefix = "active",  "⏳"
            else:
                css, prefix = "pending", "⬜"
            html += f"""
            <div class="pipeline-step {css}">
                <div class="step-icon">{icon}</div>
                <div>
                    <div class="step-title">{prefix} Agent {idx+1}: {name}</div>
                    <div class="step-desc">{desc}</div>
                </div>
            </div>"""
        progress_placeholder.markdown(html, unsafe_allow_html=True)

    render_pipeline(0)
    status_placeholder.info(f"🔬 Initializing analysis for **{company.strip()}**...")

    try:
        result = intelligence_crew.kickoff(inputs={"company": company.strip()})
        st.session_state.analysis_done  = True
        st.session_state.analysis_error = None
        st.session_state.elapsed = time.time() - st.session_state.start_time
        render_pipeline(4)
        progress_placeholder.empty()
        status_placeholder.success(
            f"✅ Analysis complete for **{company.strip()}** "
            f"in {st.session_state.elapsed:.0f}s"
        )
    except Exception as e:
        progress_placeholder.empty()
        err_str = str(e)
        # ── Detect Groq rate-limit errors and show a helpful message ──────
        is_rate_limit = any(kw in err_str for kw in (
            "RateLimitError", "rate_limit_exceeded", "Rate limit", "TPM"
        ))
        if is_rate_limit:
            friendly = format_rate_limit_message(e)
            status_placeholder.warning(friendly)
            st.session_state.analysis_error = "rate_limit"  # sentinel — keeps error state minimal
        else:
            st.session_state.analysis_error = err_str
            status_placeholder.error(f"❌ Error: {e}")
        st.session_state.analysis_done = True

elif run_btn and not company.strip():
    st.warning("Please enter a company name.")


# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.analysis_done and not st.session_state.analysis_error:
    comp = st.session_state.current_company

    # Metrics row
    final_text = load_file("final_report.md")
    stats = get_report_stats(final_text)

    st.markdown(f"""
    <div class="section-header">📊 Intelligence Report — {comp}</div>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4, m5 = st.columns(5)
    metrics = [
        (m1, "⏱️", f"{st.session_state.elapsed:.0f}s", "Analysis Time"),
        (m2, "📝", f"{stats['words']:,}", "Words Generated"),
        (m3, "🔗", str(stats['sources']), "Sources Cited"),
        (m4, "⚠️", str(stats['challenges']), "Challenges Found"),
        (m5, "🤖", str(stats['ai_opps']), "AI Opportunities"),
    ]
    for col, icon, val, lbl in metrics:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">{icon}</div>
                <div class="metric-value">{val}</div>
                <div class="metric-label">{lbl}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Report tabs
    tab_labels = [
        "📋 Full Report",
        "🔍 Research",
        "📊 BI Analysis",
        "🤖 AI Strategy",
        "👔 CEO Pitch",
    ]
    tabs = st.tabs(tab_labels)

    report_files = [
        ("final_report.md",       "Full Business Intelligence Report"),
        ("research_findings.md",  "Research Dossier"),
        ("analysis_report.md",    "Business Intelligence Analysis"),
        ("ai_strategy_report.md", "AI Strategy Report"),
        ("ceo_pitch.md",          "CEO Consulting Pitch"),
    ]

    for tab, (fname, title) in zip(tabs, report_files):
        with tab:
            content = load_file(fname)
            if content:
                # Download buttons row
                dl_col1, dl_col2, _ = st.columns([1, 1, 4])
                with dl_col1:
                    st.download_button(
                        label="📥 Download MD",
                        data=content,
                        file_name=fname,
                        mime="text/markdown",
                        key=f"dl_md_{fname}",
                    )
                with dl_col2:
                    try:
                        from pdf_export import markdown_to_pdf
                        pdf_bytes = markdown_to_pdf(content, comp)
                        st.download_button(
                            label="📄 Download PDF",
                            data=pdf_bytes,
                            file_name=fname.replace(".md", ".pdf"),
                            mime="application/pdf",
                            key=f"dl_pdf_{fname}",
                        )
                    except Exception as pdf_err:
                        st.caption(f"PDF unavailable: {pdf_err}")

                st.markdown("<div class='report-content'>", unsafe_allow_html=True)
                st.markdown(content)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning(f"⚠️ `{fname}` not generated yet.")

elif st.session_state.analysis_done and st.session_state.analysis_error:
    if st.session_state.analysis_error == "rate_limit":
        # Clean message already shown above — just a retry hint here
        st.info(
            "💡 **Tip:** The retry logic already waited and retried automatically. "
            "If you keep hitting rate limits, wait 60 s or upgrade your Groq plan."
        )
    else:
        st.error(f"❌ Analysis failed: {st.session_state.analysis_error}")
        with st.expander("Error details"):
            st.code(st.session_state.analysis_error)

else:
    # Welcome / empty state
    st.markdown("""
    <div style="text-align:center; padding:3rem 1rem; color:#78909C;">
        <div style="font-size:4rem; margin-bottom:1rem;">🏢</div>
        <div style="font-size:1.3rem; font-weight:600; color:#90CAF9; margin-bottom:0.5rem;">
            Ready to analyze any company
        </div>
        <div style="font-size:0.95rem; max-width:500px; margin:0 auto;">
            Enter a company name above and click <b>Analyze Company</b> to generate
            a full Business Intelligence report with AI strategy recommendations.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Feature cards
    st.markdown("<br>", unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns(4)
    features = [
        ("🔍", "Deep Research",     "13-section corporate dossier with cited sources"),
        ("📊", "BI Analysis",       "Business model, challenges & competitive landscape"),
        ("🤖", "AI Strategy",       "Phased AI roadmap with ROI estimates"),
        ("👔", "CEO Pitch",         "Personalized executive consulting pitch"),
    ]
    for col, (icon, title, desc) in zip([f1, f2, f3, f4], features):
        with col:
            st.markdown(f"""
            <div class="metric-card" style="padding:1.5rem;">
                <div style="font-size:2rem;">{icon}</div>
                <div style="font-size:0.95rem; font-weight:700; color:#E0E0E0; margin:0.5rem 0 0.3rem;">
                    {title}
                </div>
                <div style="font-size:0.78rem; color:#78909C;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<center><small>AI Company Intelligence System v2.0 · "
    "Built with CrewAI · Groq LLaMA · Serper · Streamlit · ReportLab</small></center>",
    unsafe_allow_html=True,
)