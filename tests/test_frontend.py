import re

import pytest
import yaml
from bs4 import BeautifulSoup
from astro_xray.report import ROOT, build_html, read_json, render_markdown, validate_demo


def test_embedded_interactive_contract(ready):
    ready["mode"] = "interactive-html"
    ready["sections"][1]["module"] = "single-lens"
    ready["sections"][3]["module"] = "binary-lens"
    md = render_markdown(ready)
    with pytest.raises(ValueError, match="demo-data"):
        build_html(md)
    data = read_json(ROOT / "examples/ogle-2016-blg-1928/demo-data.json")
    page = BeautifulSoup(build_html(md, demo=data), "html.parser")
    assert len(page.select("svg")) == 5
    assert len(page.select(".experiment")) == 2
    assert all(page.find("label", attrs={"for":e["id"]}) for e in page.select("input,select"))
    assert not page.select("script[src],link[href],img[src]")
    assert page.find(id="astro-data") and "synthetic" in page.find(id="astro-data").text
    assert "ASTROINSERT" not in page.text


def test_bad_demo_rejected():
    data = read_json(ROOT / "examples/ogle-2016-blg-1928/demo-data.json")
    validate_demo(data)
    data["tables"]["0.05"]["u"][1] = -1
    with pytest.raises(ValueError):
        validate_demo(data)


def test_design_color_drift():
    design = (ROOT / "DESIGN.md").read_text(encoding="utf-8")
    tokens = yaml.safe_load(design.split("---", 2)[1])["colors"]
    css = (ROOT / "assets/report.css").read_text(encoding="utf-8")
    for name, value in tokens.items():
        assert re.search(r"--" + name + r"\s*:\s*" + re.escape(value), css, re.I)
