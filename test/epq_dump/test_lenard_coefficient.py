import pytest
from pytest import approx  # type: ignore
from test.epq_dump.validators import LenardCoefficientRow
from layers_edx.element import Element
from layers_edx.xrt import XRayTransition
from layers_edx.material_properties.lc import LeonardCoefficient
from layers_edx.units import ToSI


@pytest.mark.epq_ref(module="LenardCoefficient")
@pytest.mark.parametrize(
    "beam_energy, Z, trans, algo",
    [
        # Silicon K-alpha at various energies
        (10.0, 14, 0, "Heinrich"),
        (15.0, 14, 0, "Heinrich"),
        (20.0, 14, 0, "Heinrich"),
        # Iron K-alpha at various energies
        (15.0, 26, 0, "Heinrich"),
        (20.0, 26, 0, "Heinrich"),
        (30.0, 26, 0, "Heinrich"),
        # Copper K-alpha at various energies
        (15.0, 29, 0, "Heinrich"),
        (20.0, 29, 0, "Heinrich"),
        (30.0, 29, 0, "Heinrich"),
        # Gold L-alpha at higher energy
        (20.0, 79, 26, "Heinrich"),
        (30.0, 79, 26, "Heinrich"),
        # Additional elements and transitions
        (15.0, 13, 0, "Heinrich"),  # Aluminum K-alpha
        (20.0, 22, 0, "Heinrich"),  # Titanium K-alpha
        (25.0, 47, 0, "Heinrich"),  # Silver K-alpha
    ],
)
class TestLenardCoefficientHeinrich:
    """
    Test the Leonard coefficient computation against the Java EPQ reference
    implementation.

    Currently tests only the Heinrich 1967 algorithm, which is the default
    and only algorithm implemented in the Python codebase.
    """

    @pytest.fixture(autouse=True)
    def setup_reference(
        self,
        beam_energy: float,
        Z: int,
        trans: int,
        algo: str,
        java_dump: list[LenardCoefficientRow],
    ):
        """Setup fixture that extracts reference data from Java dump."""
        self.ref = java_dump[0]
        self.beam_energy_kev = beam_energy
        self.Z = Z
        self.trans = trans
        self.algo = algo

        # Create Python objects
        self.element = Element(Z)
        self.xrt = XRayTransition(self.element, trans)
        self.beam_energy_joules = ToSI.kev(beam_energy)

    @pytest.fixture
    def require_valid_transition(self):
        """Guard: skip if the transition doesn't exist or beam energy is too low."""

        if not self.ref.exists:
            pytest.skip(f"Transition {self.xrt} does not exist.")

        # Skip if beam energy is below edge energy (would cause division issues)
        if self.beam_energy_joules <= self.xrt.edge_energy:
            pytest.skip(
                f"Beam energy {self.beam_energy_kev} keV is below edge energy "
                f"{self.ref.edge_energy_kev:.2f} keV"
            )

    def test_coefficient_value(self, require_valid_transition: None):
        # Compute using Python implementation
        if self.algo == "Heinrich":
            coefficient_python = LeonardCoefficient.Heinrich1967.compute(
                self.beam_energy_joules, self.xrt
            )
        else:
            pytest.skip(f"Algorithm {self.algo} not yet implemented in Python")

        # Compare against Java reference
        assert self.ref.coefficient == approx(coefficient_python)
