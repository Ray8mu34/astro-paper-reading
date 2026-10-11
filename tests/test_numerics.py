import numpy as np
import pytest

from astro_xray.lensing import (binary_det_j, binary_map, binary_params, critical_curves,
                               lens_mass_earth, normalized_flux, pspl, relative_motion,
                               uniform_fspl, uniform_fspl_disk_check)


def test_single_lens_limits():
    assert pspl(1)==pytest.approx(3/np.sqrt(5),rel=1e-14)
    assert np.isinf(pspl(0))
    assert pspl(1e200)==1
    for u in (1e-154,1e-155,1e-160,1e-200,1e-300):
        assert pspl(u)==pytest.approx(1/u,rel=1e-14)
    assert np.all(np.diff(pspl(np.linspace(.001,10,1000)))<0)
    assert uniform_fspl(0,1)==pytest.approx(np.sqrt(5))
    assert uniform_fspl(1,0)==pspl(1)
    assert uniform_fspl(1,.3)==pytest.approx(uniform_fspl_disk_check(1,.3),abs=1e-9)
    assert uniform_fspl(1,.001,eps=1e-7)==pytest.approx(pspl(1),rel=1e-6)
    assert uniform_fspl(1-1e-6,1)==pytest.approx(uniform_fspl(1+1e-6,1),rel=3e-5)
    assert np.allclose(normalized_flux([1,2,3],0),1)
    assert np.allclose(normalized_flux([1,2,3],1),[1,2,3])


@pytest.mark.parametrize("s,q",[(.6,.001),(.8,.01),(1,.1),(1.25,1)])
def test_binary_equations_and_com(s,q):
    e1,e2,z1,z2=binary_params(s,q)
    assert e1*z1+e2*z2==pytest.approx(0,abs=1e-16)
    assert z2-z1==pytest.approx(s)
    a=critical_curves(s,q,n=96)
    assert np.max(abs(binary_det_j(a["z"],s,q)))<2e-7
    assert np.allclose(binary_map(a["z"],s,q),a["caustic"])
    assert np.max(abs(a["z"][-1]-a["z"][0,a["end_permutation"]]))<1e-9


def test_units():
    assert lens_mass_earth(.842,.1)==pytest.approx(.289841309517,rel=1e-10)
    assert relative_motion(.842,.0288)==pytest.approx(10.67848958,rel=1e-9)
    assert lens_mass_earth(.842,.016)/lens_mass_earth(.842,.1)==pytest.approx(6.25)


@pytest.mark.parametrize("call",[
    lambda:pspl(-1),lambda:pspl(np.nan),lambda:uniform_fspl(-1,1),lambda:uniform_fspl(1,-1),
    lambda:uniform_fspl(1,1,eps=0),lambda:uniform_fspl_disk_check(.1,1),lambda:normalized_flux(2,1.1),
    lambda:lens_mass_earth(842,0),lambda:relative_motion(.842,0),lambda:critical_curves(0,.1),
    lambda:critical_curves(1,2),lambda:critical_curves(1,.1,n=8),lambda:binary_map(np.inf,1,.1)
])
def test_invalid_physics_inputs(call):
    with pytest.raises(ValueError):call()
