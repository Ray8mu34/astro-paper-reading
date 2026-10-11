#!/usr/bin/env python3
"""Create deterministic teaching data and a discrete binary critical-curve atlas."""
from __future__ import annotations
import json, sys, hashlib, platform
from pathlib import Path
import numpy as np
from scipy import __version__ as scipy_version
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from astro_xray.lensing import uniform_fspl, critical_curves, normalized_flux

def main():
    tables = {}
    interpolation_checks = []
    for rho in [0.05, 0.2, 0.5, 1.0, 3.39]:
        # Dense near u=rho; no interpolation along rho, s or q.
        u = np.unique(np.r_[np.linspace(0, 10, 1801),
                            np.linspace(max(0,rho-0.15),rho+0.15,1201),
                            np.linspace(0,min(10,2*rho),801)])
        a = np.array([uniform_fspl(x, rho) for x in u])
        rng = np.random.default_rng(420 + int(100*rho))
        check_u = np.r_[rng.uniform(0,10,160),
                        rho + rng.uniform(-min(.1,rho),.1,100)]
        exact = np.array([uniform_fspl(x,rho) for x in check_u])
        approx = np.interp(check_u,u,a)
        err = float(np.max(abs(approx-exact)/exact))
        if err > 5e-4:
            raise RuntimeError(f"Interpolation budget exceeded at rho={rho}: {err}")
        tables[str(rho)] = {"rho":rho,"u":u.tolist(),"A":a.tolist()}
        interpolation_checks.append({"rho":rho,"holdouts":len(check_u),"max_relative_error":err})
    atlas = {}
    for q in [.001, .01, .1, 1.0]:
        for s in [.6, .8, 1., 1.25, 1/.6]:
            a = critical_curves(s,q,n=768)
            atlas[f"{q:g}/{s:.6f}"] = {
                "s":s,"q":q,"z":np.stack([a['z'].real,a['z'].imag],axis=-1).tolist(),
                "caustic":np.stack([a['caustic'].real,a['caustic'].imag],axis=-1).tolist(),
                "max_abs_det_j":a['max_abs_det_j'],"end_permutation":a['end_permutation']}
    # Entirely synthetic data. Not digitized from Figure 1 or represented as OGLE data.
    rng=np.random.default_rng(1928)
    t=np.sort(np.r_[np.linspace(-.2,.2,49),rng.uniform(-.12,.12,28)])
    truth={"t0_days":0.,"tE_days":.0288,"u0":.59,"rho":3.39,"fs":1.,"Gamma":0.}
    mag=np.array([uniform_fspl(float(np.hypot(x/.0288,.59)),3.39) for x in t])
    sigma=np.full(len(t),.009)
    flux=normalized_flux(mag,1.)+rng.normal(0,sigma)
    data={"schema_version":"1.0", "kind":"teaching-not-paper-fit",
          "basis":{"single_lens":"numerical_uniform_source_linear_interpolation",
                   "binary":"numerical_critical_curve_quartic_no_photometry",
                   "frame":"static lens; single-lens theta_E or binary TOTAL-mass theta_E; COM origin"},
          "domains":{"u":[0,10],"rho":[.05,.2,.5,1.,3.39],"s":[.6,.8,1.,1.25,1/.6],"q":[.001,.01,.1,1.]},
          "tables":tables,"atlas":atlas,
          "observations":{"kind":"synthetic","seed":1928,"truth":truth,"time_days":t.tolist(),"flux":flux.tolist(),"sigma":sigma.tolist()},
          "validation":{"interpolation":interpolation_checks,
                        "max_abs_det_j":max(a['max_abs_det_j'] for a in atlas.values()),
                        "phase_samples":769,"binary_parameter_pairs":len(atlas),
                        "numpy":np.__version__,"scipy":scipy_version,"python":platform.python_version()}}
    dest=ROOT/'examples/ogle-2016-blg-1928/demo-data.json'
    dest.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8')
    check=data['validation'] | {"data_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),"bytes":dest.stat().st_size}
    (ROOT/"validation").mkdir(parents=True,exist_ok=True)
    (ROOT/'validation/numerics.json').write_text(json.dumps(check,indent=2),encoding='utf-8')
    print(json.dumps(check,indent=2))
if __name__=='__main__': main()
