"""Create a reproducible portable Skill ZIP and a file hash manifest."""
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from astro_xray.report import ROOT
from validate_skill import validate_skill


def package(out):
    errors=validate_skill(ROOT)
    if errors:raise ValueError("; ".join(errors))
    excluded={".git",".pytest_cache","__pycache__","dist","build",".test-work","source-pages","validation"}
    members=[]
    for path in sorted(ROOT.rglob("*")):
        rel=path.relative_to(ROOT)
        if not path.is_file() or any(p in excluded or p.endswith(".egg-info") for p in rel.parts):continue
        if path.name in {"paper.pdf","paper-extracted.txt","release-manifest.json","package.json","package-lock.json"} or path.suffix in {".pyc",".pyo"}:continue
        members.append((path,rel))
    out.parent.mkdir(parents=True,exist_ok=True)
    manifest=[]
    with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path,rel in members:
            content=path.read_bytes()
            name="astro-paper-reading/"+rel.as_posix()
            info=zipfile.ZipInfo(name,date_time=(2026,10,12,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16
            z.writestr(info,content)
            manifest.append(dict(path=name,bytes=len(content),sha256=hashlib.sha256(content).hexdigest()))
        z.writestr("astro-paper-reading/RELEASE-MANIFEST.json",json.dumps(manifest,indent=2))
    with zipfile.ZipFile(out) as z:
        if z.testzip():raise ValueError("ZIP CRC failed")
    record=dict(zip=str(out.resolve()),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),bytes=out.stat().st_size,files=len(manifest),excluded="Git/cache/build folders and downloaded paper PDF/text/source page images; downloaded literature and local execution records excluded")
    (ROOT/"validation").mkdir(parents=True,exist_ok=True)
    (ROOT/"validation/release-manifest.json").write_text(json.dumps(record,indent=2),encoding="utf-8")
    print(json.dumps(record,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,default=ROOT/"dist/astro-paper-reading-v1.1.skill.zip")
    package(p.parse_args().out)
