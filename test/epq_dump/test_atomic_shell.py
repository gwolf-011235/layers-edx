import math
import pytest
from pytest import approx  # type: ignore
from test.epq_dump.validators import AtomicShellRow
from layers_edx.atomic_shell import AtomicShell
from layers_edx.element import Element
from test.epq_dump.conftest import FULL_SUITE


def get_params():
    """Get parameters for atomic shell tests."""
    if FULL_SUITE:
        return [(Z, shell) for Z in range(1, 110) for shell in range(0, 49)]
    return [
        (5, 2),  # B K-shell
        (26, 0),  # Fe K-shell
        (26, 1),  # Fe L1-shell
        (29, 0),  # Cu K-shell
        (79, 0),  # Au K-shell
        (82, 10),  # Pb specific shell
        (109, 24),  # nonexistent shell
    ]


@pytest.mark.epq_ref(module="AtomicShell")
@pytest.mark.parametrize("Z,shell_index", get_params())
class TestAtomicShellProperties:
    @pytest.fixture(autouse=True)
    def setup_shell(self, Z: int, shell_index: int, java_dump: list[AtomicShellRow]):
        self.shell = AtomicShell(Element(Z), shell_index)
        self.ref = java_dump[0]
        self.Z = Z
        self.shell_index = shell_index

    def test_shell_index(self):
        assert self.ref.shell_index == self.shell.shell

    def test_shell_name_siegbahn(self):
        assert self.ref.shell_name_siegbahn == self.shell.name

    @pytest.mark.skip(reason="Not implemented")
    def test_shell_name_iupac(self):
        # Python only supports Siegbahn notation
        pass

    @pytest.mark.skip(reason="Not implemented")
    def test_shell_name_atomic(self):
        # Python only supports Siegbahn notation
        pass

    def test_family(self):
        # Python family returns an index, EPQ returns a string name
        python_family_name = AtomicShell.FAMILY[self.shell.family]
        # EPQ familiy name only get up to O, else returns "None"
        if self.ref.family in AtomicShell.FAMILY:
            assert self.ref.family == python_family_name
        else:
            assert python_family_name in ["P", "Q"]

    def test_principal_quantum_number(self):
        assert self.ref.principal_quantum_number == self.shell.principal_quantum_number

    def test_orbital_angular_momentum(self):
        assert self.ref.orbital_angular_momentum == self.shell.orbital_angular_momentum

    def test_total_angular_momentum(self):
        assert self.ref.total_angular_momentum == approx(
            self.shell.total_angular_momentum
        )

    def test_capacity(self):
        assert self.ref.capacity == self.shell.capacity

    def test_exists(self):
        if self.ref.exists is None:
            pytest.skip("Exists is None in reference data")
        else:
            assert self.ref.exists == self.shell.exists

    def test_ground_state_occupancy(self):
        if self.ref.ground_state_occupancy is None:
            # Ground state occupancy is not available in EPQ for this shell
            pytest.skip("Ground state occupancy not available for this shell")
        else:
            assert self.ref.ground_state_occupancy == self.shell.ground_state_occupancy

    def test_edge_energy(self):
        if self.ref.edge_energy_ev is None:
            # Edge energy is not available in EPQ
            pytest.skip("Edge energy not available for this shell")
        elif self.ref.edge_energy_ev == -1.0:
            # EPQ uses -1.0 to indicate no algorithm supported for edge energy
            assert math.isnan(self.shell.edge_energy)
        else:
            assert self.ref.edge_energy_ev == approx(self.shell.edge_energy)

    def test_energy(self):
        if self.ref.energy_J is None:
            # Energy is not available (shell not occupied or no edge energy)
            pytest.skip("Energy not available for this shell")
        elif self.ref.energy_J == -1.0:
            # EPQ uses -1.0 to indicate no algorithm supported for energy
            assert math.isnan(self.shell.energy)
        else:
            assert self.ref.energy_J == approx(self.shell.energy)
