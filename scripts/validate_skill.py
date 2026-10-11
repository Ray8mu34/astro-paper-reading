"""Validate skill paths and optionally a state and its delivered artifacts."""
import argparse
import re
import sys
from pathlib import Path

import jsonschema
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from astro_xray.report import ROOT, build_html, read_json, render_markdown, render_notes, safe_artifact, validate_analysis, validate_demo


def validate_skill(root):
    errors = []
    required = ["SKILL.md", "schemas/analysis.schema.json", "references/visualization.md", "references/component-contract.md", "references/quality-gates.md", "scripts/new_analysis.py", "scripts/build_report.py", "scripts/validate_skill.py", "docs/DESIGN-AUDIT.md", "assets/report.css", "assets/report.js", "assets/single-lens.html", "assets/binary-lens.html"]
    for name in required:
        if not (root / name).is_file():
            errors.append(f"Missing required file: {name}")
    text = (root / "SKILL.md").read_text(encoding="utf-8-sig")
    front = yaml.safe_load(text.split("---", 2)[1])
    if front.get("name") != "astro-paper-reading" or not isinstance(front.get("description"), str):
        errors.append("Invalid Skill metadata")
    for path in [root / "SKILL.md", *list((root / "references").glob("*.md"))]:
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8-sig")):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            dest = (path.parent / target.split("#")[0]).resolve()
            if not dest.is_relative_to(root.resolve()) or not dest.exists():
                errors.append(f"Broken local reference in {path.name}: {target}")
    jsonschema.Draft202012Validator.check_schema(read_json(root / "schemas/analysis.schema.json"))
    return errors


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--analysis", type=Path)
    p.add_argument("--require-artifacts", action="store_true")
    p.add_argument("--demo-data", type=Path)
    args = p.parse_args()
    errors = validate_skill(args.root)
    if args.require_artifacts and not args.analysis:
        p.error("--require-artifacts needs --analysis")
    if args.analysis:
        data = validate_analysis(read_json(args.analysis), publish=args.require_artifacts, root=args.root)
        if args.require_artifacts:
            artifacts = dict(notes='analysis-notes.md', **data['artifacts']) if 'notes' not in data['artifacts'] else data['artifacts']
            for kind, rel in artifacts.items():
                path = safe_artifact(args.analysis.parent, rel)
                if not path.is_file() or not path.stat().st_size:
                    errors.append(f"Missing {kind} artifact: {path}")
                elif kind == "markdown" and path.read_text(encoding="utf-8-sig") != render_markdown(data):
                    errors.append("Markdown does not match analysis")
                elif kind == 'notes' and path.read_text(encoding='utf-8-sig') != render_notes(data):
                    errors.append('Internal notes do not match analysis')
                elif kind == "html":
                    content = path.read_text(encoding="utf-8")
                    demo = read_json(args.demo_data) if args.demo_data else None
                    if not demo and "astro-module:" in render_markdown(data):
                        import json
                        embedded = re.search(r'<script type="application/json" id="astro-data">(.*?)</script>', content, re.S)
                        if embedded:
                            demo = json.loads(embedded.group(1), parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
                    if build_html(render_markdown(data), demo=demo, root=args.root, analysis=data, workspace=args.analysis.parent) != content:
                        errors.append("HTML content/assets do not match current analysis and data; rebuild")
    if args.demo_data:
        validate_demo(read_json(args.demo_data))
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    if errors:
        return 1
    print("PASS: skill structure, references and requested state/artifacts")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, IndexError, yaml.YAMLError, jsonschema.ValidationError, jsonschema.SchemaError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
