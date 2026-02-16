import random

import pytest
from pytest import approx  # type: ignore
from test.epq_dump.validators import LenardCoefficientRow
from layers_edx.element import Element
from layers_edx.xrt import XRayTransition
from layers_edx.material_properties.lc import LeonardCoefficient
from layers_edx.units import ToSI
from test.epq_dump.conftest import FULL_SUITE


def get_params():
    """
    Get parameters for Leonard coefficient tests.
    Returns tuples of (beam_energy, Z, trans, algo).
    """
    if FULL_SUITE:
        return get_random_params(count=500, seed=42)

    test_cases = [
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
    ]
    return test_cases


def generate_random_lenard_coefficient_params(
    count: int,
    beam_energy_range: tuple[float, float] = (10.0, 30.0),
    element_range: tuple[int, int] = (11, 79),
    transition_range: tuple[int, int] = (0, 10),
    algorithms: list[str] | None = None,
    seed: int | None = None,
) -> list[tuple[float, int, int, str]]:
    """Generate random Leonard coefficient test cases.

    Args:
        count: Number of test cases to generate
        beam_energy_range: Tuple of (min_keV, max_keV) for beam energy
            (default: (10.0, 30.0))
        element_range: Tuple of (min_Z, max_Z) for element atomic numbers
            (default: (11, 79) - Sodium to Gold)
        transition_range: Tuple of (min_trans, max_trans) for transition indices
            (default: (0, 10))
        algorithms: List of algorithms to randomly choose from
            (default: ["Heinrich"])
        seed: Random seed for reproducibility (default: None)

    Returns:
        List of tuples in format: [(beam_energy, Z, trans, algo), ...]
        where beam_energy is in keV, Z is atomic number, trans is transition
        index, and algo is the algorithm name.

    Examples:
        # Generate 10 test cases with default parameters and seed
        >>> cases = generate_random_lenard_coefficient_params(count=10, seed=42)

        # Generate test cases with specific energy and element ranges
        >>> cases = generate_random_lenard_coefficient_params(
        ...     count=20,
        ...     beam_energy_range=(15.0, 25.0),
        ...     element_range=(13, 29),
        ...     seed=123
        ... )
    """
    if seed is not None:
        random.seed(seed)

    if algorithms is None:
        algorithms = ["Heinrich"]

    # Enforce constraints
    if beam_energy_range[0] >= beam_energy_range[1]:
        raise ValueError(
            f"Invalid beam_energy_range: min ({beam_energy_range[0]}) must be less than "
            f"max ({beam_energy_range[1]})"
        )

    if element_range[0] > element_range[1]:
        raise ValueError(
            f"Invalid element_range: min ({element_range[0]}) > max ({element_range[1]})"
        )

    test_cases: list[tuple[float, int, int, str]] = []

    for _ in range(count):
        # Random beam energy
        beam_energy = random.uniform(beam_energy_range[0], beam_energy_range[1])

        # Random atomic number
        Z = random.randint(element_range[0], element_range[1])

        # Random transition index
        # For lighter elements (Z < 30), prefer K transitions (0-10)
        # For heavier elements, allow L and M transitions (0-30)
        if Z < 30:
            trans = random.randint(0, min(10, transition_range[1]))
        else:
            trans = random.randint(transition_range[0], transition_range[1])

        # Random algorithm
        algo = random.choice(algorithms)

        test_cases.append((beam_energy, Z, trans, algo))

    return test_cases


def get_random_params(
    count: int = 10, seed: int = 42
) -> list[tuple[float, int, int, str]]:
    """Get random Leonard coefficient test parameters with sensible defaults.

    Args:
        count: Number of test cases to generate (default: 10)
        seed: Random seed for reproducibility (default: 42)

    Returns:
        List of tuples in format: [(beam_energy, Z, trans, algo), ...]
    """
    return generate_random_lenard_coefficient_params(count=count, seed=seed)


@pytest.mark.epq_ref(module="LenardCoefficient")
@pytest.mark.parametrize(
    "beam_energy, Z, trans, algo",
    get_params(),
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
