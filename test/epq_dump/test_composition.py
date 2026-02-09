import pytest
from pytest import approx  # type: ignore
from test.epq_dump.validators import CompositionDetailRow, CompositionSummaryRow
from layers_edx.element import Element, Composition


def get_params():
    """Get parameters for composition tests.

    Format: (elements_str, fractions_str)
    """
    test_cases = [
        ("Fe", "1.0"),  # Pure element
        ("Fe,O", "0.72,0.28"),  # Binary: Iron oxide
        ("Si,Al,O", "0.28,0.10,0.62"),  # Ternary: Feldspar
        ("C,H,O", "0.5,0.3,0.2"),  # Ternary: Organic
        ("Fe,Ni,Co", "0.5,0.3,0.2"),  # Ternary: Alloy
    ]
    return test_cases


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

            assert py_wf == approx(
                ref_row.normalized_weight_fraction,
            ), f"Normalized weight fraction mismatch for {ref_row.element}"

    def test_atomic_fractions_match(self):
        py_atomic_fractions = self.py_composition.atomic_fractions

        for ref_row in self.ref_rows:
            # Find corresponding element
            py_elem = self._find_element_by_atomic_number(ref_row.atomic_number)
            py_af = py_atomic_fractions[py_elem]

            assert py_af == approx(ref_row.atomic_percent), (
                f"Atomic fraction mismatch for {ref_row.element}"
            )

    def test_atoms_per_kg_match(self):
        py_atoms_per_kg = self.py_composition.atoms_per_kg

        for ref_row in self.ref_rows:
            # Find corresponding element
            py_elem = self._find_element_by_atomic_number(ref_row.atomic_number)
            py_apk = py_atoms_per_kg[py_elem]

            assert py_apk == approx(ref_row.atoms_per_kg), (
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
        assert len(self.py_composition.elements) == self.ref_row.element_count

    def test_mean_atomic_number(self):
        py_mean_z = self.py_composition.mean_atomic_number

        assert py_mean_z == approx(self.ref_row.mean_atomic_number)

    def test_weight_avg_atomic_number(self):
        pytest.skip(reason="Not implemented")
        # py_wavg_z = self.py_composition.weight_avg_atomic_number
        # assert py_wavg_z == approx(self.ref_row.weight_avg_atomic_number)

    def test_sum_weight_fractions(self):
        py_sum = self.py_composition.sum_weight_fractions

        assert py_sum == approx(self.ref_row.sum_weight_fraction)
