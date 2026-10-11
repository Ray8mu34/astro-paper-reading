# Design audit — V1 scope

Targeted upstream retrieval, not a full repository audit: Paper X-Ray master
SKILL.md, references/figure-kit.html and LICENSE were retrieved on 2026-10-11.
Byte copies live in upstream/reference. The historic recovery upstream-ref is
not presumed to match the current retrieved master. See provenance.json for
resolved revision and hashes when recorded.

Inherited principles: semantic colors, mathematical serif typography, restrained
stroke weights, visible captions, interaction beside explanation. Figure Kit's
neural-network block primitives do not represent lens planes. V1 implements
independent SVG plotting primitives for lens geometry, curves and caustics;
it does not claim a verbatim Figure Kit port or DINO reproduction.

Offline system fonts and native MathML replace upstream network font/TeX
dependencies. Native selects intentionally accept OS-owned popup geometry.
No animation is needed: a time slider makes causal motion directly inspectable.
