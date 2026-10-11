"""Build Markdown and optional HTML from one validated analysis state."""
import argparse
import sys
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from astro_xray.report import build_html, read_json, render_markdown, render_notes, safe_artifact


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--analysis", type=Path, help="Required verified analysis (or analysis.json beside --markdown)")
    p.add_argument("--markdown", type=Path, help="Previously generated Markdown; rejects stale/edited content")
    p.add_argument("--out", type=Path, help="Override HTML destination")
    p.add_argument("--demo-data", type=Path)
    p.add_argument("--md-only", action="store_true")
    args = p.parse_args()
    if not args.analysis and not args.markdown:
        p.error("--analysis or --markdown is required")
    analysis_path = args.analysis or args.markdown.parent / "analysis.json"
    data = read_json(analysis_path)
    md = render_markdown(data)
    if args.markdown and args.markdown.read_text(encoding="utf-8-sig") != md:
        raise ValueError("Markdown is stale or edited; update analysis.json and rebuild")
    md_path = safe_artifact(analysis_path.parent, data["artifacts"]["markdown"])
    html_path = args.out or safe_artifact(analysis_path.parent, data["artifacts"]["html"])
    notes_path = safe_artifact(analysis_path.parent, data['artifacts'].get('notes', 'analysis-notes.md'))
    targets = [html_path.resolve(), md_path.resolve(), notes_path.resolve(), analysis_path.resolve()]
    if len(targets) != len(set(targets)):
        raise ValueError("Output cannot overwrite analysis, Markdown or internal notes")
    demo = read_json(args.demo_data) if args.demo_data else None
    rendered = build_html(md, demo=demo, analysis=data, workspace=analysis_path.parent) if not args.md_only else None
    notes = render_notes(data)
    # Validate and render completely before replacing any output.
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md, encoding="utf-8")
    print(f"Markdown: {md_path}")
    notes_path.parent.mkdir(parents=True, exist_ok=True)
    notes_path.write_text(notes, encoding='utf-8')
    print(f'Internal notes: {notes_path}')
    if rendered is not None:
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(rendered, encoding="utf-8")
        print(f"HTML: {html_path}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, jsonschema.ValidationError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
