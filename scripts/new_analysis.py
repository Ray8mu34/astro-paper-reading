"""Create a draft only; no remote retrieval, inference, or overwrite."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from astro_xray.report import MODES, validate_analysis


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--mode", choices=MODES, default="deep-md")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    data = dict(schema_version="1.1", status="draft", mode=args.mode,
                paper=dict(title="", input=args.input, version="unknown", kind="unknown"),
                coverage=dict(level="none", read=[], missing=["Paper has not been read"], teaching_only=False),
                sources=[], question="", concepts=[], claims=[], parameters=[], assumptions=[], sections=[],
                unknowns=["Evidence not collected"], reproduction=dict(status="not-run", notes=[]),
                artifacts=dict(markdown="report.md", html="report.html", notes="analysis-notes.md"))
    validate_analysis(data)
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "analysis.json").open("x", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
    print(f"Draft created: {args.out / 'analysis.json'}; Agent reading is required")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
