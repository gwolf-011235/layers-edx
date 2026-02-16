import pytest
from pytest import approx  # type: ignore
from test.epq_dump.validators import ElementRow
from layers_edx.element import Element
from test.epq_dump.conftest import FULL_SUITE


def get_params():
    """Get parameters for element tests."""
    if FULL_SUITE:
        return list(range(1, 110))
    return [1, 6, 26, 29, 79, 82]


@pytest.mark.epq_ref(module="Element")
@pytest.mark.parametrize("Z", get_params())
class TestElementProperties:
    @pytest.fixture(autouse=True)
    def setup_element(self, Z: int, java_dump: list[ElementRow]):
        self.element = Element(Z)
        self.ref = java_dump[0]

    def test_atomic_number(self):
        assert self.ref.Z == self.element.atomic_number

    def test_symbol(self):
        assert self.ref.symbol == self.element.name

    def test_atomic_weight(self):
        assert self.ref.atomic_weight == approx(self.element.atomic_weight)

    def test_mass_in_kg(self):
        assert self.ref.mass_in_kg == approx(self.element.mass)

    def test_ionization_energy(self):
        if self.ref.ionization_energy is None:
            pytest.skip("Ionization energy is None in reference data")
        assert self.ref.ionization_energy == approx(self.element.ionization_energy)

    @pytest.mark.skip(reason="Not implemented")
    def test_mean_ionization_potential(self):
        pass
        # assert self.ref.mean_ionization_potential == approx(
        #     self.element.mean_ionization_potential
        # )
