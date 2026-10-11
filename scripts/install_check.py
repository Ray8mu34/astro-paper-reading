"""Invoke an actually extracted Skill from an unrelated workspace in four modes.

Uses prepared analysis; this is an executable lifecycle check, not a new reading.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from astro_xray.report import MODES, ROOT


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("skill",type=Path)
    p.add_argument("--out",type=Path,default=ROOT/".test-work/installed-invocation")
    p.add_argument("--record",type=Path,default=ROOT/"validation/installation.json")
    args=p.parse_args();skill=args.skill.resolve();workspace=args.out.resolve()
    workspace.mkdir(parents=True,exist_ok=True)
    record=dict(skill_directory=str(skill),python=sys.executable,status="RUNNING",commands=[],limitation="Prepared shared analysis invoked in four modes; app's discovery in a fresh chat is not tested")
    def call(script,*options):
        cmd=[sys.executable,"-X","utf8",str(skill/"scripts"/script),*map(str,options)]
        result=subprocess.run(cmd,cwd=workspace,capture_output=True,text=True,encoding="utf-8")
        record["commands"].append(dict(command=cmd,exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr))
        if result.returncode:raise RuntimeError(result.stderr or result.stdout)
    try:
        call("validate_skill.py")
        call("new_analysis.py","local-unread-paper.pdf","--mode","quick","--out",workspace/"draft")
        example=skill/"examples/ogle-2016-blg-1928"
        original=json.loads((example/"analysis.json").read_text(encoding="utf-8"))
        for mode in MODES:
            dest=workspace/mode;dest.mkdir(exist_ok=True)
            data=original.copy();data["mode"]=mode
            state=dest/"analysis.json"
            state.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
            call("build_report.py","--analysis",state,"--demo-data",example/"demo-data.json")
            call("validate_skill.py","--analysis",state,"--require-artifacts","--demo-data",example/"demo-data.json")
        record["status"]="PASS"
        print(f"PASS: actual installed Skill, four modes, {len(record['commands'])} CLI invocations")
    except Exception as e:
        record["status"]="FAIL";record["failure"]=str(e);raise
    finally:
        args.record.parent.mkdir(parents=True,exist_ok=True)
        args.record.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")


if __name__=="__main__":main()
