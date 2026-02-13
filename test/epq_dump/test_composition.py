import random

import pytest
from pytest import approx  # type: ignore
from test.epq_dump.validators import CompositionDetailRow, CompositionSummaryRow
from layers_edx.element import Element, Composition
from test.epq_dump.conftest import FULL_SUITE


def get_params():
    """Get parameters for composition tests.

    Format: (elements_str, fractions_str)
    """
    if FULL_SUITE:
        return get_random_params(count=500, seed=42)

    test_cases = [
        ("Fe", "1.0"),  # Pure element
        ("Fe,O", "0.72,0.28"),  # Binary: Iron oxide
        ("Si,Al,O", "0.28,0.10,0.62"),  # Ternary: Feldspar
        ("C,H,O", "0.5,0.3,0.2"),  # Ternary: Organic
        ("Fe,Ni,Co", "0.5,0.3,0.2"),  # Ternary: Alloy
    ]
    return test_cases


def generate_random_compositions(
    count: int,
    min_elements: int = 2,
    max_elements: int = 4,
    normalize_fractions: bool = False,
    min_fraction: float = 0.05,
    max_fraction: float = 1.0,
    seed: int | None = None,
    element_range: tuple[int, int] = (1, 92),
) -> list[tuple[str, str]]:
    """Generate random composition test cases.

    Args:
        count: Number of test cases to generate
        min_elements: Minimum elements per composition (default: 2)
        max_elements: Maximum elements per composition (default: 4)
        normalize_fractions: If True, scale fractions to sum=1; if False, use raw values
            (default: True)
        min_fraction: Minimum fraction value for each element (default: 0.05)
        max_fraction: Maximum fraction value for each element (default: 1.0)
        seed: Random seed for reproducibility (default: None)
        element_range: Tuple of (min_atomic_number, max_atomic_number) for element
            selection (default: (1, 92))

    Returns:
        List of tuples in format: [(elements_str, fractions_str), ...]
        where elements_str is comma-separated element symbols (e.g., "Fe,O")
        and fractions_str is comma-separated fraction values (e.g., "0.7200,0.2800")

    Examples:
        # Generate 5 normalized compositions with seed for reproducibility
        >>> cases = generate_random_compositions(count=5, seed=42)

        # Generate pure elements and multi-element compositions
        >>> cases = generate_random_compositions(count=10, min_elements=1,
        ...     max_elements=3, seed=123)

        # Generate 10 unnormalized compositions with 2-3 elements
        >>> cases = generate_random_compositions(
        ...     count=10,
        ...     min_elements=2,
        ...     max_elements=3,
        ...     normalize_fractions=False,
        ...     seed=123
        ... )
    """
    if seed is not None:
        random.seed(seed)

    # Enforce constraints
    min_elements = max(1, min_elements)
    if min_elements > max_elements:
        raise ValueError(
            f"min_elements ({min_elements}) cannot be greater than \
                max_elements ({max_elements})"
        )

    # Ensure max_elements doesn't exceed available elements in range
    available_elements = element_range[1] - element_range[0] + 1
    if max_elements > available_elements:
        raise ValueError(
            f"max_elements ({max_elements}) exceeds available elements \
                ({available_elements}) in range {element_range}"
        )

    test_cases: list[tuple[str, str]] = []

    for _ in range(count):
        # Randomly choose number of elements for this composition
        num_elements = random.randint(min_elements, max_elements)

        # Randomly select unique atomic numbers
        atomic_numbers = random.sample(
            range(element_range[0], element_range[1] + 1), num_elements
        )

        # Get element symbols using Element.NAME
        symbols = [Element.NAME[z] for z in atomic_numbers]

        # Generate random fractions
        fractions = [
            random.uniform(min_fraction, max_fraction) for _ in range(num_elements)
        ]

        # Normalize if requested
        if normalize_fractions:
            total = sum(fractions)
            fractions = [f / total for f in fractions]

        # Format as strings
        elements_str = ",".join(symbols)
        fractions_str = ",".join(f"{f:.4f}" for f in fractions)

        test_cases.append((elements_str, fractions_str))

    return test_cases


def get_random_params(count: int = 10, seed: int = 42) -> list[tuple[str, str]]:
    """Get random composition test parameters with sensible defaults.

    Args:
        count: Number of test cases to generate (default: 10)
        seed: Random seed for reproducibility (default: 42)

    Returns:
        List of tuples in format: [(elements_str, fractions_str), ...]
    """
    return generate_random_compositions(count=count, seed=seed)


@pytest.mark.epq_ref(module="CompositionDetail")
@pytest.mark.parametrize("elements,fractions", get_params())
class TestCompositionDetail:
    """Test that Python Composition implementation matches Java reference for
    per-element properties."""

    @pytest.fixture(autouse=True)
    def setup(
        self, elements: str, fractions: str, java_dump: list[CompositionDetailRow]
    ):
        # Parse test inputs
        element_names = elements.split(",")
        fraction_values = [float(f) for f in fractions.split(",")]

        # Create Python composition
        # Element constructor accepts int (atomic number) or str (element symbol)
        py_elements = [Element(name.strip()) for name in element_names]
        self.py_composition = Composition(py_elements, fraction_values, weight=True)

        # Java reference data
        self.ref_rows = java_dump

    def _find_element_by_atomic_number(self, atomic_number: int):
        """Find element in composition by atomic number.

        Args:
            atomic_number: The atomic number to search for

        Returns:
            The Element object with matching atomic number

        Raises:
            AssertionError: If element not found
        """
        py_elem = next(
            (
                e
                for e in self.py_composition.elements
                if e.atomic_number == atomic_number
            ),
            None,
        )
        assert py_elem is not None, (
            f"Could not find element with atomic number {atomic_number}"
        )
        return py_elem

    def test_normalized_weight_fractions_match(self):
        py_fractions = self.py_composition.weight_fractions

        for ref_row in self.ref_rows:
            # Find corresponding element in Python composition
            py_elem = self._find_element_by_atomic_number(ref_row.atomic_number)
            py_wf = py_fractions[py_elem]

            assert ref_row.normalized_weight_fraction == approx(py_wf), (
                f"Normalized weight fraction mismatch for {ref_row.element}"
            )

    def test_atomic_fractions_match(self):
        py_atomic_fractions = self.py_composition.atomic_fractions

        for ref_row in self.ref_rows:
            # Find corresponding element
            py_elem = self._find_element_by_atomic_number(ref_row.atomic_number)
            py_af = py_atomic_fractions[py_elem]

            assert ref_row.atomic_percent == approx(py_af), (
                f"Atomic fraction mismatch for {ref_row.element}"
            )

    def test_atoms_per_kg_match(self):
        py_atoms_per_kg = self.py_composition.atoms_per_kg

        for ref_row in self.ref_rows:
            # Find corresponding element
            py_elem = self._find_element_by_atomic_number(ref_row.atomic_number)
            py_apk = py_atoms_per_kg[py_elem]

            assert ref_row.atoms_per_kg == approx(py_apk), (
                f"Atoms per kg mismatch for {ref_row.element}"
            )


@pytest.mark.epq_ref(module="CompositionSummary")
@pytest.mark.parametrize("elements,fractions", get_params())
class TestCompositionSummary:
    """Test that Python Composition implementation matches Java reference for
    aggregate properties."""

    @pytest.fixture(autouse=True)
    def setup(
        self, elements: str, fractions: str, java_dump: list[CompositionSummaryRow]
    ):
        # Parse test inputs
        element_names = elements.split(",")
        fraction_values = [float(f) for f in fractions.split(",")]

        # Create Python composition
        py_elements = [Element(name.strip()) for name in element_names]
        self.py_composition = Composition(py_elements, fraction_values, weight=True)

        # Java reference data (single row for whole composition)
        self.ref_row = java_dump[0]

    def test_element_count(self):
        assert self.ref_row.element_count == len(self.py_composition.elements)

    def test_mean_atomic_number(self):
        py_mean_z = self.py_composition.raw_mean_atomic_number

        assert self.ref_row.mean_atomic_number == approx(py_mean_z)

    def test_weight_avg_atomic_number(self):
        pytest.skip(reason="Not implemented")
        # py_wavg_z = self.py_composition.weight_avg_atomic_number
        # assert self.ref_row.weight_avg_atomic_number == approx(py_wavg_z)

    def test_sum_weight_fractions(self):
        py_sum = self.py_composition.raw_sum_weight_fractions

        assert self.ref_row.sum_weight_fraction == approx(py_sum)
