"""CLI entry point for the AI Company Intelligence System."""
import groq_patch  # noqa: F401  — must be first import

from dotenv import load_dotenv
load_dotenv()

from crew import intelligence_crew  # noqa: E402


def run(company: str) -> str:
    print(f"\n{'='*60}")
    print(f"  AI Company Intelligence System")
    print(f"  Analyzing: {company}")
    print(f"{'='*60}\n")

    try:
        result = intelligence_crew.kickoff(inputs={"company": company})
    except Exception as exc:
        print(f"\nERROR during crew execution: {exc}")
        raise

    print("\n" + "="*60)
    print("  ANALYSIS COMPLETE")
    print("="*60)
    print(result)
    print("="*60 + "\n")

    print("Reports saved:")
    for f in ["research_findings.md", "analysis_report.md",
              "ai_strategy_report.md", "final_report.md", "ceo_pitch.md"]:
        print(f"  - {f}")

    return str(result)


if __name__ == "__main__":
    run("Prestige Group")
