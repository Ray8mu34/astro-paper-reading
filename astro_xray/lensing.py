"""Dimensionless static, thin point-mass lens calculations.

Single-lens distances are angular separations / theta_E. Binary coordinates use
TOTAL-mass theta_E and the centre of mass. This module computes critical curves,
not general binary image solutions or binary photometric magnifications.
"""
from __future__ import annotations
import math
from typing import Any
import numpy as np
from scipy.integrate import quad
from scipy.optimize import linear_sum_assignment

KAPPA_MAS_PER_MSUN = 8.144  # rounded conventional coefficient, not an exact constant
MSUN_PER_MEARTH = 332946.0487  # adequate for the precision of these teaching examples
DAYS_PER_YEAR = 365.25

def _finite_nonnegative(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return value

def pspl(u: Any) -> Any:
    """Analytic point-source point-lens magnification. A(0)=+infinity explicitly."""
    x = np.asarray(u, dtype=float)
    if np.any(~np.isfinite(x)) or np.any(x < 0):
        raise ValueError("u must be finite and nonnegative")
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        # Stable at large u; the familiar u**2 formula overflows unnecessarily.
        # The inverse-square expression overflows for tiny positive u.
        # Use the direct expression there, and the scaled one for large u.
        a = np.where(x < 1.0, (x*x + 2.0) / (x*np.hypot(x, 2.0)),
                     (1.0 + 2.0 / x**2) / np.sqrt(1.0 + 4.0 / x**2))
        a = np.where(x == 0, np.inf, a)
    return float(a) if a.ndim == 0 else a

def uniform_fspl(u: float, rho: float, *, eps: float = 2e-10) -> float:
    """Uniform circular source via a lens-centred, one-dimensional area integral.

    The point-lens singularity cancels against the polar area element. Full
    rings are integrated analytically; partial rings are integrated adaptively.
    This is NOT a limb-darkened source model. eps is an integration tolerance,
    not a guaranteed error in an independently interpolated browser lookup.
    """
    u = _finite_nonnegative("u", u)
    rho = _finite_nonnegative("rho", rho)
    if eps <= 0 or not math.isfinite(eps):
        raise ValueError("eps must be positive and finite")
    if rho == 0:
        return pspl(u)
    if u == 0:
        return math.hypot(rho, 2.0) / rho
    full_radius = max(rho - u, 0.0)
    area_weighted = math.pi * full_radius * math.hypot(full_radius, 2.0)
    lo, hi = abs(u - rho), u + rho
    def partial(r: float) -> float:
        if r == 0:
            angle = math.pi if u == rho else 0.0
        else:
            c = (r*r + u*u - rho*rho) / (2*r*u)
            angle = 2 * math.acos(max(-1.0, min(1.0, c)))
        return angle * (r*r + 2.0) / math.hypot(r, 2.0)
    val, err = quad(partial, lo, hi, epsabs=eps*math.pi*rho*rho,
                    epsrel=eps, limit=160)
    result = (area_weighted + val) / (math.pi * rho*rho)
    if not math.isfinite(result) or result < 1 - 1e-9:
        raise ArithmeticError("Invalid finite-source integration result")
    return result

def uniform_fspl_disk_check(u: float, rho: float, n: int = 120) -> float:
    """Independent source-centred 2-D Gaussian quadrature, only u>rho.

    Used to test the ring-integral implementation away from the singularity;
    not an alternative production solver for a source covering the lens.
    """
    if not (u > rho > 0) or n < 8:
        raise ValueError("Independent disk check requires u>rho>0 and n>=8")
    x, w = np.polynomial.legendre.leggauss(n)
    r = rho * (x + 1) / 2
    wr = rho * w / 2
    phi = np.pi * (x + 1)
    wp = np.pi * w
    d = np.sqrt(u*u + r[:, None]**2 + 2*u*r[:, None]*np.cos(phi)[None, :])
    return float(np.sum(pspl(d) * (wr*r)[:, None] * wp[None, :]) / (np.pi*rho*rho))

def normalized_flux(a: Any, fs: float) -> Any:
    """F/F_base=fs*A+1-fs. This teaching API requires nonnegative blend flux."""
    if not math.isfinite(fs) or not 0 <= fs <= 1:
        raise ValueError("Teaching normalized fs must be in [0,1]")
    return fs*np.asarray(a) + 1-fs

def lens_mass_earth(theta_e_uas: float, pi_rel_mas: float) -> float:
    if not (math.isfinite(theta_e_uas) and math.isfinite(pi_rel_mas)
            and theta_e_uas > 0 and pi_rel_mas > 0):
        raise ValueError("theta_E and pi_rel must be positive and finite")
    return (theta_e_uas/1000)**2 / (KAPPA_MAS_PER_MSUN*pi_rel_mas) * MSUN_PER_MEARTH

def relative_motion(theta_e_uas: float, t_e_days: float) -> float:
    if not (theta_e_uas > 0 and t_e_days > 0 and
            math.isfinite(theta_e_uas) and math.isfinite(t_e_days)):
        raise ValueError("theta_E and t_E must be positive and finite")
    return theta_e_uas/1000 / t_e_days * DAYS_PER_YEAR

def binary_params(s: float, q: float) -> tuple[float, float, float, float]:
    if not (math.isfinite(s) and math.isfinite(q) and s > 0 and 0 < q <= 1):
        raise ValueError("Require finite s>0 and 0<q<=1")
    e1, e2 = 1/(1+q), q/(1+q)
    return e1, e2, -s*e2, s*e1

def binary_map(z: Any, s: float, q: float) -> Any:
    e1, e2, z1, z2 = binary_params(s, q)
    a = np.asarray(z, dtype=complex)
    if np.any(~np.isfinite(a)) or np.any(a == z1) or np.any(a == z2):
        raise ValueError("Image position must be finite and not at a lens")
    return a - e1/(np.conj(a)-z1) - e2/(np.conj(a)-z2)

def binary_det_j(z: Any, s: float, q: float) -> Any:
    e1, e2, z1, z2 = binary_params(s, q)
    a = np.asarray(z, dtype=complex)
    with np.errstate(divide="ignore", invalid="ignore"):
        return 1 - abs(e1/(a-z1)**2 + e2/(a-z2)**2)**2

def critical_curves(s: float, q: float, n: int = 768) -> dict[str, Any]:
    """Solve the critical-curve quartic at n phases, then map to caustics.

    Branches are tracked by minimum-distance assignment. The permutation at
    2*pi is saved, not incorrectly closed branch-by-branch. This is a numerical
    atlas, not a certification at all real-valued s,q or at topology boundaries.
    """
    if n < 32:
        raise ValueError("At least 32 phase samples required")
    e1, e2, z1, z2 = binary_params(s, q)
    p1 = np.array([1.0, -2*z1, z1*z1])
    p2 = np.array([1.0, -2*z2, z2*z2])
    prod = np.polymul(p1, p2).astype(complex)
    sub = np.pad(e1*p2 + e2*p1, (2, 0))
    phases = np.linspace(0, 2*np.pi, n+1)
    roots = []
    for phase in phases:
        r = np.roots(np.exp(1j*phase)*prod - sub)
        if roots:
            _, col = linear_sum_assignment(abs(roots[-1][:, None]-r[None, :]))
            r = r[col]
        else:
            r = r[np.lexsort((r.imag, r.real))]
        roots.append(r)
    z = np.asarray(roots)
    caustics = binary_map(z, s, q)
    _, end_permutation = linear_sum_assignment(abs(z[-1][:, None]-z[0][None, :]))
    error = float(np.max(abs(binary_det_j(z, s, q))))
    if not np.isfinite(z).all() or not np.isfinite(caustics).all() or error > 2e-7:
        raise ArithmeticError(f"Critical curve residual {error:g} exceeds atlas budget")
    return {"s": s, "q": q, "z": z, "caustic": caustics,
            "max_abs_det_j": error, "end_permutation": end_permutation.tolist()}
