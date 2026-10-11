"""Operate the real file:// report offline in local Chromium; save evidence."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from astro_xray.lensing import normalized_flux, uniform_fspl
from astro_xray.report import ROOT


def run(report, output, executable):
    from playwright.sync_api import sync_playwright
    output.mkdir(parents=True,exist_ok=True)
    evidence=dict(status="RUNNING",executed_utc=datetime.now(timezone.utc).isoformat(),report=str(report.resolve()),checks=[],screenshots=[],errors=[],network_requests=[])
    def check(ok, description):
        evidence["checks"].append(dict(description=description,passed=bool(ok)))
        if not ok:raise AssertionError(description)
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=str(executable) if executable else None,headless=True)
            evidence["browser_version"]=browser.version
            context=browser.new_context(viewport=dict(width=1440,height=1000),offline=True,reduced_motion="reduce")
            page=context.new_page()
            page.on("pageerror",lambda e:evidence["errors"].append(str(e)))
            page.on("console",lambda msg:evidence["errors"].append(msg.text) if msg.type=="error" else None)
            page.on("request",lambda req:evidence["network_requests"].append(req.url) if req.url.startswith(("http:","https:")) else None)
            page.goto(report.resolve().as_uri(),wait_until="load")
            check(page.locator("svg path.model").count()==1,"Initial single-lens numerical curve exists")
            check(page.locator("svg path.critical").count()==4,"Initial four numerical critical tracks exist")
            check(page.locator("math").count()>=5,"Offline MathML renders real equations")
            check(not page.locator("#single-error").is_visible() and not page.locator("#binary-error").is_visible(),"Initial modules have no inline errors")
            def state(module):return json.loads(page.locator("#"+module+"-lens").get_attribute("data-state"))
            def set_range(id,value):
                page.locator("#"+id).evaluate("(e,v)=>{e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}))}",str(value))
            def paths(id):return page.locator("#"+id).evaluate("e=>Array.from(e.querySelectorAll('path')).map(p=>p.getAttribute('d')).join('|')")
            def shot(name,locator=None):
                file=output/(name+".png")
                if locator:page.locator(locator).screenshot(path=str(file))
                else:page.screenshot(path=str(file),full_page=True)
                evidence["screenshots"].append(str(file))
            shot("desktop-single","#single-lens");shot("desktop-binary","#binary-lens");shot("desktop-report")
            obs_before=page.locator("#single-curve .observation").count()
            check(obs_before==77,"All 77 fixed synthetic observations render")
            binary_before=state("binary")
            source_before=page.locator("#single-geometry .current").get_attribute("cx")
            set_range("single-time",2)
            check(state("single")["tau"]==2 and page.locator("#single-geometry .current").get_attribute("cx")!=source_before,"Time changes source geometry and linked marker")
            s=state("single")
            expected=float(normalized_flux(uniform_fspl(np.hypot(s["tau"],s["u0"]),s["rho"]),s["fs"]))
            check(abs(s["flux"]-expected)/expected<5e-4,"Browser flux agrees with independent current Python integration")
            model_before=paths("single-curve")
            set_range("single-u0",.2)
            check(paths("single-curve")!=model_before,"u0 changes curve")
            set_range("single-te",.06)
            check(abs(state("single")["time"]-.12)<1e-12,"tE changes physical-time coordinate")
            for rho in ("0","0.05","0.2","0.5","1.0","3.39"):
                page.select_option("#single-rho",rho)
                check(state("single")["rho"]==float(rho),"rho option "+rho+" updates numeric model")
            set_range("single-fs",.4)
            check(state("single")["fs"]==.4,"Blending control updates actual flux")
            check(state("binary")==binary_before,"Single controls do not change binary state")
            page.uncheck("#single-points");check(page.locator("#single-curve .observation").count()==0,"Synthetic point toggle works")
            page.check("#single-points");check(page.locator("#single-curve .observation").count()==77,"Point toggle restores fixed data")
            page.click("#single-reset");check(state("single")["rho"]==3.39 and state("single")["tau"]==0,"Single reset works")
            # Arrow key input is independent of scripted input-event coverage.
            page.locator("#single-time").focus();page.keyboard.press("ArrowRight")
            check(abs(state("single")["tau"]-.02)<1e-12,"Range is keyboard operable")
            check(page.locator("#single-time").evaluate("e=>getComputedStyle(e).outlineStyle")!="none","Keyboard focus is visible")
            page.click("#single-reset")
            single_before=state("single")
            shapes=[]
            for q in ("0.001","0.01","0.1","1"):
                page.select_option("#binary-q",q)
                for separation in ("0.6","0.8","1","1.25","1.6666666666666667"):
                    page.select_option("#binary-s",separation)
                    b=state("binary")
                    check(b["q"]==float(q) and b["s"]==float(separation),f"Binary atlas q={q}, s={separation} operates")
                    check(abs(b["s"]*b["comparison_s"]-1)<1e-10,"Close–wide uses a computed reciprocal")
                    shapes.append(paths("binary-caustic"))
            check(len(set(shapes))==20,"All 20 atlas combinations have distinct curve data")
            page.select_option("#binary-view","central")
            check("中心裁窗" in page.locator("#binary-caustic").text_content(),"Central view explicitly labels cropping")
            before=paths("binary-caustic");set_range("binary-angle",45);set_range("binary-impact",-.15)
            check(paths("binary-caustic")!=before and state("binary")["angle"]==45 and state("binary")["impact"]==-.15,"Schematic angle and offset update trajectory")
            check(state("single")==single_before,"Binary controls do not change single-lens state")
            page.click("#binary-reset");check(state("binary")["s"]==.8 and state("binary")["view"]=="full","Binary reset works")
            # Out-of-domain calls are rejected rather than clamped/extrapolated.
            for u,rho in ((10.01,1),(-.1,1),(1,.3)):
                rejected=page.evaluate("([u,rho])=>{try{AstroXray.interpolate(u,rho);return false}catch(e){return true}}",[u,rho])
                check(rejected,f"Reject unsupported interpolation u={u}, rho={rho}")
            page.locator("#single-rho").evaluate("e=>{e.add(new Option('unsupported','0.3'));e.value='0.3';e.dispatchEvent(new Event('input'))}")
            check(page.locator("#single-error").is_visible() and page.locator("#single-curve path").count()==0,"Invalid parameter shows visible error and clears stale plot")
            page.click("#single-reset");check(not page.locator("#single-error").is_visible(),"Reset recovers invalid parameter state")
            # Full article reflow, with internal scrolling allowed for equations/tables.
            for width in (1440,768,390,320):
                page.set_viewport_size(dict(width=width,height=900))
                page.locator("#single-lens").scroll_into_view_if_needed()
                overflow=page.evaluate("document.documentElement.scrollWidth>window.innerWidth+1")
                check(not overflow,f"No document horizontal overflow at {width}px")
                check(page.locator(".axis-label").evaluate_all("els=>els.every(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0})"),f"Axis labels have layout at {width}px")
                if width==390:
                    shot("mobile-single","#single-lens");shot("mobile-binary","#binary-lens");shot("mobile-report")
            page.set_viewport_size(dict(width=390,height=900))
            page.select_option("#binary-q","0.001");page.select_option("#binary-view","central")
            shot("mobile-central","#binary-lens")
            # Native-select keyboard open and commit on the narrow viewport.
            page.locator("#single-rho").focus();page.keyboard.press("Home");page.keyboard.press("ArrowDown");page.keyboard.press("Enter")
            check(state("single")["rho"]==.05,"Native select accepts keyboard option changes")
            check(not evidence["errors"],"No JavaScript or console errors")
            check(not evidence["network_requests"],"Offline file:// makes zero HTTP(S) requests")
            check(page.evaluate("getComputedStyle(document.documentElement).scrollbarColor")!="auto","Global scrollbar baseline is applied")
            browser.close()
        evidence["status"]="PASS"
    except Exception as e:
        evidence["status"]="FAIL";evidence["failure"]=str(e)
        raise
    finally:
        (output/"browser.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding="utf-8")
    return evidence


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report",type=Path,default=ROOT/"examples/ogle-2016-blg-1928/report.html")
    p.add_argument("--out",type=Path,default=ROOT/"validation/browser")
    p.add_argument("--executable",type=Path)
    args=p.parse_args()
    exe=args.executable
    if not exe:
        exe=next((path for path in (Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")) if path.exists()),None)
    result=run(args.report,args.out,exe)
    print(f"PASS: {len(result['checks'])} actual browser checks; {len(result['screenshots'])} screenshots; zero external requests")


if __name__=="__main__":main()
