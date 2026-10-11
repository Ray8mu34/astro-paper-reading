import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def ready():
    return dict(schema_version="1.0", status="ready", mode="deep-md",
                paper=dict(title="Test scientific teaching report", input="local", version="v1", kind="theory"),
                coverage=dict(level="none", read=[], missing=["No real paper"], teaching_only=True),
                sources=[dict(id="local", title="Local derivation", url="", accessed=True, note="Teaching")],
                question="What does A(u) measure?", concepts=[],
                claims=[dict(id="analytic", kind="D", text="Point-source analytic result", evidence=[], assumptions=[])],
                parameters=[], assumptions=["Static point-mass lens"],
                sections=[dict(id=role, role=role, title=role, markdown="Inspect $u$ and the assumptions.", claim_ids=["analytic"])
                          for role in ("background", "method", "derivation", "evidence", "limitations", "review")],
                unknowns=["Lens distance"], reproduction=dict(status="teaching", notes=["No fit"]),
                artifacts=dict(markdown="report.md", html="report.html"))
