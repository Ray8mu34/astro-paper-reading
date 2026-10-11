"""Shared state validation and deterministic, offline report construction.

Validation certifies structure and consistency, never the truth of prose.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import base64
import mimetypes
from pathlib import Path

import jsonschema
import mistune

ROOT = Path(__file__).resolve().parents[1]
MODES = ("quick", "deep-md", "interactive-html", "critical-review")


def read_json(path):
    def reject(value):
        raise ValueError(f"Non-finite JSON number: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), parse_constant=reject)


def safe_artifact(workspace, relative):
    root = Path(workspace).resolve()
    path = (root / relative).resolve()
    if path == root or not path.is_relative_to(root):
        raise ValueError(f"Artifact path escapes workspace: {relative}")
    return path


def validate_analysis(data, *, publish=False, root=ROOT):
    schema = read_json(Path(root) / "schemas/analysis.schema.json")
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(data)
    sources = {s["id"]: s for s in data["sources"]}
    for collection in (data["sources"], data["claims"], data["concepts"], data["sections"]):
        ids = [s["id"] for s in collection]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate identifiers in analysis")
    for item in data["claims"] + data["parameters"]:
        for e in item["evidence"]:
            if e["source_id"] not in sources:
                raise ValueError(f"Unknown evidence source: {e['source_id']}")
            if item["kind"] == "R" and not sources[e["source_id"]]["accessed"]:
                raise ValueError("Reported result requires an accessed source")
        if item["kind"] == "I" and not item.get("assumptions") and not data["assumptions"]:
            raise ValueError("Inference requires assumptions")
    concepts = {c["id"]: c for c in data["concepts"]}
    def visit(cid, stack):
        if cid not in concepts:
            raise ValueError(f"Unknown concept dependency: {cid}")
        if cid in stack:
            raise ValueError("Concept dependency cycle")
        for dep in concepts[cid]["depends_on"]:
            visit(dep, stack | {cid})
    for cid in concepts:
        visit(cid, set())
    claims = {c["id"] for c in data["claims"]}
    for section in data["sections"]:
        if not set(section["claim_ids"]) <= claims:
            raise ValueError("Section references unknown claim")
    sections = {s['id']: s for s in data['sections']}
    reader = data.get('reader')
    if reader:
        labels = [r['section'] for r in reader['roadmap']]
        if len(labels) != len(set(labels)):
            raise ValueError('Duplicate original-paper section in roadmap')
        for row in reader['roadmap']:
            if row['source_id'] not in sources or not sources[row['source_id']]['accessed']:
                raise ValueError('Roadmap needs an accessed original source')
        for focus in reader['focus']:
            section = sections.get(focus['section_id'])
            if section is None or section.get('audience', 'reader') != 'reader':
                raise ValueError('Reading route must point to a main reader section')
    visual_ids = set()
    for visual in data.get('visuals', []):
        if visual['id'] in visual_ids or visual['section_id'] not in sections:
            raise ValueError('Duplicate visual or unknown visual section')
        visual_ids.add(visual['id'])
        if visual['placement'] == 'include':
            if sections[visual['section_id']].get('audience', 'reader') == 'internal':
                raise ValueError('Reader visual cannot be placed in internal notes')
            required = ['image'] if visual['kind'] == 'image' else ['fragment', 'interaction_gain']
            if any(not visual.get(k, '').strip() for k in required) or not visual['caption'].strip():
                raise ValueError('Included visual needs assets, a caption and interaction gain')
        for key in ('image', 'fragment', 'styles', 'script', 'data'):
            if key in visual:
                safe_artifact(Path.cwd(), visual[key])
        if visual.get('data') and not visual.get('data_id'):
            raise ValueError('Visual data needs a unique data island id')
    islands = [v['data_id'] for v in data.get('visuals', []) if v.get('data_id') and v['placement'] == 'include']
    if len(islands) != len(set(islands)) or 'astro-data' in islands:
        raise ValueError('Duplicate or reserved visual data id')
    for path in data["artifacts"].values():
        safe_artifact(Path.cwd(), path)
    artifact_paths = list(data['artifacts'].values()) + ([] if 'notes' in data['artifacts'] else ['analysis-notes.md'])
    if len(artifact_paths) != len(set(artifact_paths)):
        raise ValueError("Reader and internal destinations must differ")
    if publish:
        if data["status"] != "ready" or not data["question"].strip() or not data["paper"]["title"].strip():
            raise ValueError("Analysis is still a draft; Agent must read and populate it")
        if not data["claims"] or not data["sections"] or not data["unknowns"]:
            raise ValueError("Publish requires claims, narrative and explicit unknowns")
        if data["coverage"]["level"] != "full" and not data["coverage"]["teaching_only"] and data["mode"] != "quick":
            raise ValueError("Deep/review reports need full coverage or an explicit teaching-only label")
        if data['schema_version'] == '1.1' and data['mode'] != 'quick' and (not reader or not reader['overview'].strip() or not reader['roadmap']):
            raise ValueError('Reader edition needs an overview and original-paper roadmap')
        roles = {s["role"] for s in data["sections"] if s.get('audience', 'reader') != 'internal'}
        needed = {"limitations"}
        if data["mode"] in ("deep-md", "interactive-html"):
            needed |= {"background", "method", "evidence"}
            if data['schema_version'] == '1.0':
                needed.add('derivation')
        if data["mode"] == "critical-review":
            needed |= {"review", "evidence"}
        if not needed <= roles:
            raise ValueError(f"Missing mode-specific narrative roles: {sorted(needed - roles)}")
    return data


def analysis_hash(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def evidence_text(evidence):
    return "; ".join(f"{e['source_id']} — {e['locator']}" for e in evidence) or "无文献证据；见推导或教学说明"


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def reader_sections(data):
    for section in data['sections']:
        if section.get('audience', 'reader') == 'internal':
            continue
        if data['mode'] == 'quick' and (section['role'] in ('derivation', 'review') or section.get('audience') == 'appendix'):
            continue
        yield section


def visual_markdown(visual, data):
    if visual['kind'] == 'image':
        return f"![{visual['caption'].replace(']', '')}]({visual['image']})"
    return f"[打开交互：{visual['question']}]({data['artifacts']['html']}#visual-{visual['id']})"


def render_markdown(data):
    """Reader prose only; scientific work records have a separate renderer."""
    validate_analysis(data, publish=True)
    out = [f"<!-- astro-analysis-sha256: {analysis_hash(data)} -->", f"# {data['paper']['title']}"]
    reader = data.get('reader')
    # Legacy states remain buildable. Existing defensive prose still needs author editing.
    out.append(reader['overview'] if reader else data['question'])
    if reader and reader['roadmap']:
        sources = {s['id']: s for s in data['sources']}
        rows = ['## 原文结构导览', '|原文章节|在论证中的作用|回到原文看什么|', '|---|---|---|']
        for row in reader['roadmap']:
            url = sources[row['source_id']]['url']
            label = f"{row['section']} · {row['title']}"
            link = f"[{label}]({url.split('#')[0]}#page={row['page']})" if re.match(r'^https?://[^\s()]+$', url) else label
            rows.append('|'+ '|'.join(cell(x) for x in [link, row['argument'], row['focus']])+'|')
        out.append('\n'.join(rows))
    appendix_started = False
    for section in reader_sections(data):
        if section.get('audience') == 'appendix' and not appendix_started:
            out.append('<!-- astro-appendix-start -->')
            appendix_started = True
        if appendix_started and section.get('audience', 'reader') == 'reader':
            raise ValueError('Reader sections must precede supplementary appendices')
        text = section['markdown']
        for visual in data.get('visuals', []):
            if visual['section_id'] == section['id'] and visual['placement'] == 'include':
                marker = f"<!-- astro-visual:{visual['id']} -->"
                if text.count(marker) != 1:
                    raise ValueError('Each selected visual needs one contextual insertion marker: '+visual['id'])
                text = text.replace(marker, marker+'\n\n'+visual_markdown(visual, data))
        if re.search(r'<!-- astro-visual:([^>]+) -->', text):
            ids = re.findall(r'<!-- astro-visual:([^>]+) -->', text)
            allowed = {v['id'] for v in data.get('visuals', []) if v['placement'] == 'include' and v['section_id'] == section['id']}
            if set(ids) - allowed:
                raise ValueError('Unknown or omitted visual marker')
        out += [f"## {section['title']}", text]
        if section.get('module') and data['mode'] == 'interactive-html':
            out.append(f"<!-- astro-module:{section['module']} -->")
    if appendix_started:
        out.append('<!-- astro-appendix-end -->')
    # A compact bibliography links to the paper; access logs belong to notes.
    accessed = [s for s in data['sources'] if s['accessed'] and re.match(r'^https?://[^\s()]+$', s['url'])]
    if accessed:
        out += ['## 原文', '\n'.join(f"- [{s['title']}]({s['url']})" for s in accessed)]
    return '\n\n'.join(out)+'\n'


def render_notes(data):
    validate_analysis(data, publish=True)
    out = [f"<!-- astro-analysis-sha256: {analysis_hash(data)} -->", f"# {data['paper']['title']}",
           f"内部科学与执行记录\n\n模式：{data['mode']} · 阅读覆盖：{data['coverage']['level']} · 文献版本：{data['paper']['version']}"]
    for section in data["sections"]:
        if section.get('audience') != 'internal':
            continue
        out.extend([f"## {section['title']}", section["markdown"]])
    out += ['## 叙事选择', *[f"- {f['question']}：{f['why']}" for f in data.get('reader', {}).get('focus', [])]]
    out += ['## 图形选择记录', *[f"- {v['id']} / {v['placement']} / {v['basis']}：{v['question']}\n  理由：{v['why']}；替代：{v['alternative']}；交互增益：{v.get('interaction_gain', '不适用')}" for v in data.get('visuals', [])]]
    if data["parameters"]:
        rows = ["|变量|值|单位|类别|不确定性|参考系|定位|", "|---|---|---|---|---|---|---|"]
        for p in data["parameters"]:
            rows.append("|" + "|".join(cell(v) for v in [p["symbol"], "unknown" if p["value"] is None else p["value"], p["unit"], p["kind"], p["uncertainty"], p["frame"], evidence_text(p["evidence"])]) + "|")
        out += ["## 参数与参考系", "\n".join(rows)]
    out += ["## 论断与证据账本", "R：论文报告；D：独立推导；I：条件推断；T：教学模拟；S：候选解释。"]
    for claim in data["claims"]:
        out += [f"- **{claim['id']} [{claim['kind']}]** {claim['text']} — {evidence_text(claim['evidence'])}"]
        if claim["assumptions"]:
            out.append("  假设：" + "；".join(claim["assumptions"]))
    out += ["## 假设与未知项"] + [f"- {s}" for s in data["assumptions"] + data["unknowns"]]
    out += ["## 覆盖与复现状态", f"复现状态：{data['reproduction']['status']}"]
    out += [f"- {s}" for s in data["coverage"]["read"] + data["reproduction"]["notes"]]
    out += [f"- 未取得：{s}" for s in data["coverage"]["missing"]]
    out += ["## 来源"]
    for s in data["sources"]:
        # Only trusted URL schemes become links in the generated Markdown.
        url = s["url"]
        title = s["title"].replace("[", "\\[").replace("]", "\\]")
        link = f"[{title}]({url})" if re.match(r"^https?://[^\s()]+$", url) else title
        out += [f"- {s['id']}: {link} — {s['note']}"]
    return "\n\n".join(out) + "\n"


def validate_demo(data):
    import numpy as np
    if data.get("kind") != "teaching-not-paper-fit" or data.get("schema_version") != "1.0":
        raise ValueError("Demo must explicitly be teaching-not-paper-fit V1")
    if data["domains"]["u"] != [0, 10]:
        raise ValueError("Unsupported lookup u domain")
    if sorted(float(k) for k in data["tables"]) != sorted(data["domains"]["rho"]):
        raise ValueError("rho domain/table mismatch")
    for key, table in data["tables"].items():
        u, a = np.asarray(table["u"]), np.asarray(table["A"])
        if u.ndim != 1 or u.shape != a.shape or len(u) < 2 or not np.isfinite(u).all() or not np.isfinite(a).all():
            raise ValueError("Invalid lookup arrays")
        if float(key) != table["rho"] or u[0] != 0 or u[-1] != 10 or not (np.diff(u) > 0).all() or (a < 1).any():
            raise ValueError("Invalid lookup domain or magnification")
    expected = {(s, q) for s in data["domains"]["s"] for q in data["domains"]["q"]}
    if {(v["s"], v["q"]) for v in data["atlas"].values()} != expected:
        raise ValueError("Incomplete binary atlas")
    for entry in data["atlas"].values():
        z, c = np.asarray(entry["z"]), np.asarray(entry["caustic"])
        if z.ndim != 3 or z.shape[1:] != (4, 2) or c.shape != z.shape or not np.isfinite(z).all() or not np.isfinite(c).all():
            raise ValueError("Invalid critical curve arrays")
        if sorted(entry["end_permutation"]) != [0, 1, 2, 3] or entry["max_abs_det_j"] > 2e-7:
            raise ValueError("Invalid binary residual or closure permutation")
    obs = data["observations"]
    arrays = [np.asarray(obs[k]) for k in ("time_days", "flux", "sigma")]
    if obs["kind"] != "synthetic" or len({a.shape for a in arrays}) != 1 or any(a.ndim != 1 or not np.isfinite(a).all() for a in arrays) or (arrays[2] <= 0).any():
        raise ValueError("Invalid synthetic observations")
    return data


def build_html(markdown, *, demo=None, root=ROOT, analysis=None, workspace=None):
    root = Path(root)
    modules = re.findall(r"<!-- astro-module:([a-z-]+) -->", markdown)
    if modules and demo is None:
        raise ValueError("Interactive markers require --demo-data; no empty figures are allowed")
    if len(modules) != len(set(modules)) or set(modules) - {"single-lens", "binary-lens"}:
        raise ValueError("Duplicate or unsupported interactive module")
    from latex2mathml.converter import convert
    selected = {v['id']: v for v in (analysis or {}).get('visuals', [])
                if v['placement'] == 'include' and f"<!-- astro-visual:{v['id']} -->" in markdown}
    visual_html, visual_css, visual_scripts = {}, [], []
    if '<!-- astro-visual:' in markdown and (not analysis or workspace is None):
        raise ValueError('Selected visuals need canonical analysis and its workspace')
    for vid, visual in selected.items():
        def resource(key):
            return safe_artifact(workspace, visual[key])
        if visual['kind'] == 'image':
            path = resource('image')
            mime = mimetypes.guess_type(path.name)[0]
            if mime not in ('image/png', 'image/jpeg', 'image/webp'):
                raise ValueError('Source figure must be PNG, JPEG or WebP')
            payload = base64.b64encode(path.read_bytes()).decode('ascii')
            caption = html.escape(visual['caption'])
            visual_html[vid] = f'<figure class="source-figure" id="visual-{vid}"><img src="data:{mime};base64,{payload}" alt="{caption}" loading="lazy"><figcaption>{caption}</figcaption></figure>'
        else:
            fragment = resource('fragment').read_text(encoding='utf-8')
            visual_html[vid] = f'<div id="visual-{vid}" class="reader-interactive">{fragment}<p class="visual-caption">{html.escape(visual["caption"])}</p></div>'
            if visual.get('styles'):
                visual_css.append(resource('styles').read_text(encoding='utf-8'))
            if visual.get('data'):
                payload = json.dumps(read_json(resource('data')), ensure_ascii=False, allow_nan=False).replace('<', '\\u003c')
                visual_scripts.append(f'<script type="application/json" id="{visual["data_id"]}">{payload}</script>')
            if visual.get('script'):
                script_text = resource('script').read_text(encoding='utf-8')
                if re.search(r'</script', script_text, re.I):
                    raise ValueError('Unexpected closing script tag in local visual asset')
                visual_scripts.append(f'<script>{script_text}</script>')
    sections = list(reader_sections(analysis)) if analysis else []
    # Use original Markdown heading order, including titles with math, to assign anchors.
    section_queue = {s['title']: s['id'] for s in sections}
    heading_ids = [f"section-{section_queue[line[3:]]}" if line[3:] in section_queue else f'reading-heading-{i}'
                   for i, line in enumerate(l for l in markdown.splitlines() if l.startswith('## '))]
    class MathRenderer(mistune.HTMLRenderer):
        heading_index = 0
        def heading(self, text, level, **attrs):
            if level == 2:
                anchor = heading_ids[self.heading_index]
                self.heading_index += 1
                return f'<h2 id="{anchor}">{text}</h2>\n'
            return super().heading(text, level, **attrs)
        def block_math(self, text):
            return '<div class="equation">' + convert(text, display="block") + '</div>\n'
        def inline_math(self, text):
            return convert(text)
    renderer = mistune.create_markdown(renderer=MathRenderer(escape=True), plugins=["table", "math"])
    digest = re.search(r"astro-analysis-sha256: ([a-f0-9]{64})", markdown)
    text = re.sub(r"<!-- astro-analysis-sha256: [a-f0-9]{64} -->\n", "", markdown)
    text = text.replace('<!-- astro-appendix-start -->', '\n\nASTROAPPENDIXSTART\n\n').replace('<!-- astro-appendix-end -->', '\n\nASTROAPPENDIXEND\n\n')
    for vid, visual in selected.items():
        marker = f'<!-- astro-visual:{vid} -->\n\n'+visual_markdown(visual, analysis)
        if marker in text:
                text = text.replace(marker, f'\n\nASTROVISUAL{vid.upper()}\n\n')
    for module in modules:
        text = text.replace(f"<!-- astro-module:{module} -->", f"\n\nASTROINSERT{module.replace('-', '').upper()}\n\n")
    body = renderer(text)
    body = body.replace('<p>ASTROAPPENDIXSTART</p>', '<details class="supplement"><summary>进一步推导与科学讨论</summary><div class="supplement-content">').replace('<p>ASTROAPPENDIXEND</p>', '</div></details>')
    for vid, content in visual_html.items():
        body = body.replace(f'<p>ASTROVISUAL{vid.upper()}</p>', content)
    if analysis and analysis.get('reader', {}).get('focus'):
        links = ''.join(f'<li><a href="#section-{f["section_id"]}">{html.escape(f["question"])}</a></li>' for f in analysis['reader']['focus'])
        nav = f'<details class="reading-nav"><summary>选择一个问题深入阅读</summary><nav aria-label="深入阅读路线"><ul>{links}</ul></nav></details>'
        first = next((s for s in sections if s.get('audience', 'reader') == 'reader'), None)
        if first:
            body = body.replace(f'<h2 id="section-{first["id"]}">', nav+f'<h2 id="section-{first["id"]}">', 1)
    for module in modules:
        placeholder = f"<p>ASTROINSERT{module.replace('-', '').upper()}</p>"
        component = (root / f"assets/{module}.html").read_text(encoding="utf-8")
        body = body.replace(placeholder, component)
    title = next((l[2:] for l in markdown.splitlines() if l.startswith("# ")), "Astro Paper Reading")
    css = (root / "assets/report.css").read_text(encoding="utf-8")
    css += '\n' + '\n'.join(visual_css)
    script = (root / "assets/report.js").read_text(encoding="utf-8") if modules else ""
    payload = json.dumps(validate_demo(demo), ensure_ascii=False, allow_nan=False).replace("<", "\\u003c") if modules else "{}"
    # Block everything except embedded assets, MathML and same-document JS.
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; font-src data:; connect-src 'none'; base-uri 'none'">
<meta name="astro-analysis-sha256" content="{digest.group(1) if digest else ''}">
<title>{html.escape(title)}</title><style>{css}</style></head>
<body><header class="masthead"><span>ASTRO PAPER READING</span><span>理解问题，走进论证</span></header>
<main><article>{body}</article></main><footer><span>Astro Paper Reading</span><a href="{html.escape((analysis or {}).get('artifacts', {}).get('notes', 'analysis-notes.md'), quote=True)}">科学与构建记录</a></footer>
<script type="application/json" id="astro-data">{payload}</script><script>{script}</script>{''.join(visual_scripts)}</body></html>'''
