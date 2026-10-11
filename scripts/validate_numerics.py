"""Current independent checks of solver invariants and the recovered atlas."""
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from astro_xray.lensing import (binary_map, binary_det_j, critical_curves, lens_mass_earth,
                               pspl, relative_motion, uniform_fspl, uniform_fspl_disk_check)
from astro_xray.report import ROOT, read_json, validate_demo


def check_all():
    path=ROOT/"examples/ogle-2016-blg-1928/demo-data.json"
    data=validate_demo(read_json(path))
    results=dict(executed_utc=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,data_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    values=np.geomspace(.001,1000,300)
    expected=(values**2+2)/(values*np.sqrt(values**2+4))
    analytic_error=float(np.max(abs(pspl(values)-expected)/expected))
    assert analytic_error<1e-14
    centered_error=max(abs(uniform_fspl(0,rho)-np.hypot(rho,2)/rho) for rho in (.05,.2,.5,1,3.39))
    assert centered_error<1e-12
    disk=[]
    for u,rho in ((1,.3),(.8,.2),(3,1),(5,3.39)):
        err=abs(uniform_fspl(u,rho)-uniform_fspl_disk_check(u,rho,n=120))
        assert err<1e-9
        disk.append(dict(u=u,rho=rho,abs_error=err))
    interpolation=[]
    for table in data["tables"].values():
        rho=table["rho"]
        rng=np.random.default_rng(901+int(rho*100))
        u=np.r_[rng.uniform(0,10,80),rho+np.linspace(-min(rho,.1),.1,61),0,10]
        exact=np.array([uniform_fspl(float(x),rho) for x in u])
        sampled=np.interp(u,table["u"],table["A"])
        err=float(np.max(abs(sampled-exact)/exact))
        assert err<5e-4
        interpolation.append(dict(rho=rho,holdouts=len(u),max_relative_error=err))
    atlas=[]
    for entry in data["atlas"].values():
        zz=np.array(entry["z"]);z=zz[...,0]+1j*zz[...,1]
        cc=np.array(entry["caustic"]);c=cc[...,0]+1j*cc[...,1]
        s,q=entry["s"],entry["q"]
        e1,e2=1/(1+q),q/(1+q);z1,z2=-s*e2,s*e1
        # Independently written real-coordinate map, separate from binary_map.
        def deflect(xl,mass):
            dx=z.real-xl;dy=z.imag;r2=dx*dx+dy*dy
            return mass*(dx+1j*dy)/r2
        independent=z-deflect(z1,e1)-deflect(z2,e2)
        map_error=float(np.max(abs(c-independent)))
        det_error=float(np.max(abs(binary_det_j(z,s,q))))
        shear=e1/(z-z1)**2+e2/(z-z2)**2
        phase_error=float(np.max(abs(shear-np.exp(1j*np.linspace(0,2*np.pi,len(z)))[:,None])))
        endpoint_error=float(np.max(abs(z[-1]-z[0,entry["end_permutation"]])))
        assert map_error<1e-10 and det_error<2e-7 and phase_error<2e-7 and endpoint_error<1e-9
        assert np.max(abs(binary_map(z,s,q)-c))<1e-10
        atlas.append(dict(s=s,q=q,max_abs_det_j=det_error,mapping_abs_error=map_error,phase_equation_error=phase_error,endpoint_error=endpoint_error))
    fresh=[]
    for s,q in ((.6,.001),(.8,.1),(1,1),(1.25,.01)):
        a=critical_curves(s,q,n=128)
        assert a["max_abs_det_j"]<2e-7
        fresh.append(dict(s=s,q=q,n=128,max_abs_det_j=a["max_abs_det_j"]))
    results.update(status="PASS",pspl_relative_error=analytic_error,centered_absolute_error=centered_error,independent_source_disk=disk,interpolation=interpolation,binary_atlas=atlas,fresh_solver=fresh,conditional_mass_earth=[lens_mass_earth(.842,.1),lens_mass_earth(.842,.016)],relative_motion_mas_yr=relative_motion(.842,.0288),limits=["Sampled interpolation errors are not a global proof", "Jacobian and endpoint checks do not certify topology for continuous parameter ranges", "No binary photometric solver or real data fit comparison"])
    return results


def main():
    (ROOT/"validation").mkdir(parents=True,exist_ok=True)
    try:
        results=check_all()
    except Exception as e:
        (ROOT/"validation/current-numerics.json").write_text(json.dumps(dict(status="FAIL",error=str(e))),encoding="utf-8")
        raise
    (ROOT/"validation/current-numerics.json").write_text(json.dumps(results,indent=2,allow_nan=False),encoding="utf-8")
    print(f"PASS: 5 lookup tables, 20 binary pairs, independent disk integration, 4 fresh solves; max |det J|={max(r['max_abs_det_j'] for r in results['binary_atlas']):.3g}")


if __name__=="__main__":main()
