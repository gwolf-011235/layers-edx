import pytest
from pytest import approx  # type: ignore
from test.epq_dump.validators import XRayTransitionRow
from layers_edx.element import Element
from layers_edx.xrt import XRayTransition
from layers_edx.atomic_shell import AtomicShell
from test.epq_dump.conftest import FULL_SUITE

def get_params():
    """Get parameters for XRT tests."""
    if FULL_SUITE:
        return [(Z, trans) for Z in range(1, 110) for trans in range(0, 77)]
    return [(4, 0), (5, 1), (45, 9), (96, 0)]

@pytest.mark.epq_ref(module="XRayTransition")
@pytest.mark.parametrize("Z, trans", get_params())
class TestXRayTransitionProperties:
    @pytest.fixture(autouse=True)
    def setup_transition(self, Z: int, trans: int, java_dump: list[XRayTransitionRow]):
        self.xrt = XRayTransition(Element(Z), trans)
        self.ref = java_dump[0]

    @pytest.fixture
    def require_exists(self):
        """Guard: skip if the transition isn't physically valid."""
        if not self.ref.exists:
            pytest.skip(f"Transition {self.xrt} does not exist.")

    def test_source_shell(self):
        assert self.ref.source_shell == self.xrt.source.name

    def test_destination_shell(self):
        assert self.ref.destination_shell == self.xrt.destination.name

    def test_transition_family(self):
        assert self.ref.family == AtomicShell.FAMILY[self.xrt.family]

    def test_exists(self):
        if self.ref.exists is None:
            pytest.skip("Reference data does not specify existence.")
        assert self.ref.exists == self.xrt.exists

    def test_energy(self, require_exists: None):
        assert self.ref.energy == approx(self.xrt.energy)

    def test_edge_energy_eV(self, require_exists: None):
        assert self.ref.edge_energy_eV == approx(self.xrt.edge_energy)

    def test_weight_default(self, require_exists: None):
        assert self.ref.weight_default == approx(self.xrt.weight("default"))

    def test_weight_family(self, require_exists: None):
        assert self.ref.weight_family == approx(self.xrt.weight("family"))

    def test_weight_destination(self, require_exists: None):
        assert self.ref.weight_destination == approx(self.xrt.weight("destination"))

    def test_weight_klm(self, require_exists: None):
        assert self.ref.weight_klm == approx(self.xrt.weight("klm"))
