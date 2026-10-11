import copy
import json
import subprocess
import sys

import jsonschema
import pytest
from bs4 import BeautifulSoup
from astro_xray.report import ROOT, MODES, build_html, read_json, render_markdown, validate_analysis


def run(script, *args):
    return subprocess.run([sys.executable, str(ROOT / "scripts" / script), *map(str, args)], capture_output=True, text=True)


@pytest.mark.parametrize("mode", MODES)
def test_each_mode_builds_from_state(ready, tmp_path, mode):
    ready["mode"] = mode
    path = tmp_path / "analysis.json"
    path.write_text(json.dumps(ready), encoding="utf-8")
    result = run("build_report.py", "--analysis", path)
    assert result.returncode == 0, result.stderr
    text = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert text == render_markdown(ready)
    page = BeautifulSoup((tmp_path / "report.html").read_text(encoding="utf-8"), "html.parser")
    assert page.find("math") and page.h1.text == ready["paper"]["title"]
    assert page.find("meta", attrs={"name": "astro-analysis-sha256"})["content"]


def test_draft_and_overwrite_protection(tmp_path):
    result = run("new_analysis.py", "missing.pdf", "--out", tmp_path)
    assert result.returncode == 0
    assert read_json(tmp_path / "analysis.json")["coverage"]["level"] == "none"
    assert run("new_analysis.py", "new.pdf", "--out", tmp_path).returncode != 0
    assert run("build_report.py", "--analysis", tmp_path / "analysis.json").returncode != 0
    assert not (tmp_path / "report.md").exists()


@pytest.mark.parametrize("mutation", ["source", "cycle", "path", "inference", "coverage", "role", "claim", "duplicate"])
def test_invalid_scientific_state_rejected(ready, mutation):
    if mutation == "source":
        ready["claims"][0].update(kind="R", evidence=[dict(source_id="missing", locator="p.1")])
    elif mutation == "cycle":
        ready["concepts"] = [dict(id="loop", definition="x", depends_on=["loop"])]
    elif mutation == "path":
        ready["artifacts"]["html"] = "../outside.html"
    elif mutation == "inference":
        ready["claims"][0]["kind"] = "I"
        ready["assumptions"] = []
    elif mutation == "coverage":
        ready["coverage"]["teaching_only"] = False
    elif mutation == "role":
        ready["sections"] = ready["sections"][:2]
    elif mutation == "claim":
        ready["sections"][0]["claim_ids"] = ["missing"]
    else:
        ready["sources"] *= 2
    with pytest.raises((ValueError, jsonschema.ValidationError)):
        validate_analysis(ready, publish=True)


def test_stale_markdown_and_missing_file(ready, tmp_path):
    path = tmp_path / "analysis.json"
    path.write_text(json.dumps(ready), encoding="utf-8")
    assert run("build_report.py", "--analysis", path).returncode == 0
    md = tmp_path / "report.md"
    assert run("build_report.py", "--markdown", md).returncode == 0
    original = (tmp_path / "report.html").read_bytes()
    md.write_text("# invented", encoding="utf-8")
    assert run("build_report.py", "--markdown", md).returncode != 0
    assert (tmp_path / "report.html").read_bytes() == original
    assert run("build_report.py", "--analysis", tmp_path / "absent.json").returncode != 0


def test_artifact_gate_and_script_safety(ready, tmp_path):
    path = tmp_path / "analysis.json"
    path.write_text(json.dumps(ready), encoding="utf-8")
    assert run("validate_skill.py", "--analysis", path, "--require-artifacts").returncode != 0
    ready["sections"][0]["markdown"] = '<script>window.bad=true</script> [bad](javascript:alert(1))'
    page = BeautifulSoup(build_html(render_markdown(ready)), "html.parser")
    assert not any("window.bad" in s.text for s in page.find_all("script"))
    assert not any(a.get("href", "").startswith("javascript:") for a in page.find_all("a"))


def test_nan_not_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"value":NaN}')
    with pytest.raises(ValueError):
        read_json(path)


def test_edited_html_and_missing_required_file(ready, tmp_path):
    path=tmp_path/"analysis.json"
    ready["mode"]="interactive-html"
    path.write_text(json.dumps(ready),encoding="utf-8")
    assert run("build_report.py","--analysis",path).returncode==0
    assert run("validate_skill.py","--analysis",path,"--require-artifacts").returncode==0
    html_path=tmp_path/"report.html"
    html_path.write_text(html_path.read_text(encoding="utf-8").replace("What does A(u) measure?","Invented result"),encoding="utf-8")
    assert run("validate_skill.py","--analysis",path,"--require-artifacts").returncode!=0
    import shutil
    skill=tmp_path/"skill"
    shutil.copytree(ROOT,skill,ignore=shutil.ignore_patterns(".git",".test-work","dist","__pycache__","validation","examples","upstream"))
    (skill/"assets/report.js").unlink()
    assert run("validate_skill.py","--root",skill).returncode!=0
