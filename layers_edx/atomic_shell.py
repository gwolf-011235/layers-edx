from __future__ import annotations
from typing import Protocol, Type
from layers_edx import lli, llf, read_csv
from layers_edx.element import Element
from layers_edx.units import ToSI


def read_edge_energies(filename: str, offset: int = 0) -> llf:
    return read_csv(filename, value_offset=offset + 1, conversion=ToSI.ev)


class EdgeEnergy:
    class Database(Protocol):
        @classmethod
        def compute(cls, shell: AtomicShell) -> float: ...

    class Chantler2005(Database):
        EDGE_ENERGY = read_edge_energies("FFastEdgeDB")

        @classmethod
        def index(cls, shell: AtomicShell) -> int:
            if shell.shell <= AtomicShell.from_name("OV"):
                return shell.shell
            for p_shell in [
                AtomicShell.from_name(name) for name in ["PI", "PII", "PIII"]
            ]:
                if shell.shell == p_shell:
                    return shell.shell - 4
            return -1

        @classmethod
        def compute(cls, shell: AtomicShell) -> float:
            if shell.element.atomic_number < Element("Li").atomic_number:
                return 0.0
            if shell.element.atomic_number > Element("U").atomic_number:
                return 0.0
            i = cls.index(shell)
            if i < 0:
                return 0.0
            if i >= len(cls.EDGE_ENERGY[shell.element.atomic_number]):
                return 0.0
            return cls.EDGE_ENERGY[shell.element.atomic_number][cls.index(shell)]

    class Williams2011(Database):
        EDGE_ENERGY = read_edge_energies("WilliamsBinding")

        @classmethod
        def compute(cls, shell: AtomicShell) -> float:
            if shell.shell >= 29:
                return 0.0
            return cls.EDGE_ENERGY[shell.element.atomic_number][shell.shell]

    class NIST(Database):
        EDGE_ENERGY = read_edge_energies("NISTxrtdb", offset=9)

        @classmethod
        def compute(cls, shell: AtomicShell) -> float:
            if shell.element.atomic_number < Element("Ne").atomic_number:
                return 0.0
            if shell.element.atomic_number > Element("Fm").atomic_number:
                return 0.0
            if shell.shell > AtomicShell.from_name("LIII"):
                return 0.0
            return cls.EDGE_ENERGY[shell.element.atomic_number][shell.shell]

    class DTSA(Database):
        EDGE_ENERGY = read_edge_energies("EdgeEnergies")

        @classmethod
        def compute(cls, shell: AtomicShell) -> float:
            if shell.element.atomic_number < Element("Li").atomic_number:
                return 0.0
            if shell.element.atomic_number > Element("Es").atomic_number:
                return 0.0
            if shell.shell > AtomicShell.from_name("NI"):
                return 0.0
            return cls.EDGE_ENERGY[shell.element.atomic_number][shell.shell]

    @classmethod
    def compute(cls, shell: AtomicShell) -> float:
        """
        Compute edge energy for a given atomic shell by consulting multiple databases.

        This method attempts to find the edge energy by querying databases in priority
        order: Chantler2005, Williams2011, NIST, and DTSA. The first database that
        returns a positive value is used.

        :param shell: The atomic shell for which to compute the edge energy
        :type shell: AtomicShell
        :return: The edge energy in eV, or NaN if no valid value is found in any
            database
        :rtype: float
        """
        databases: list[Type[EdgeEnergy.Database]] = [
            cls.Chantler2005,
            cls.Williams2011,
            cls.NIST,
            cls.DTSA,
        ]
        for database in databases:
            value = database.compute(shell)
            if value > 0.0:
                return value
        return float("nan")


def read_ground_state_occupancies() -> lli:
    return read_csv("ElectronConfig", value_offset=1, column_offset=1, dtype=int)


class AtomicShell:
    NAME = [
        "K",
        "LI",
        "LII",
        "LIII",
        "MI",
        "MII",
        "MIII",
        "MIV",
        "MV",
        "NI",
        "NII",
        "NIII",
        "NIV",
        "NV",
        "NVI",
        "NVII",
        "OI",
        "OII",
        "OIII",
        "OIV",
        "OV",
        "OVI",
        "OVII",
        "OVIII",
        "OIX",
        "PI",
        "PII",
        "PIII",
        "PIV",
        "PV",
        "PVI",
        "PVII",
        "PVIII",
        "PIX",
        "PX",
        "PXI",
        "QI",
        "QII",
        "QIII",
        "QIV",
        "QV",
        "QVI",
        "QVII",
        "QVIII",
        "QIX",
        "QX",
        "QXI",
        "QXII",
        "QXIII",
    ]
    FAMILY = ["K", "L", "M", "N", "O", "P", "Q"]
    CAPACITY = [
        2,
        2,
        2,
        4,
        2,
        2,
        4,
        4,
        6,
        2,
        2,
        4,
        4,
        6,
        6,
        8,
        2,
        2,
        4,
        4,
        6,
        6,
        8,
        8,
        10,
        2,
        2,
        4,
        4,
        6,
        6,
        8,
        8,
        10,
        10,
        12,
        2,
        2,
        4,
        4,
        6,
        6,
        8,
        8,
        10,
        10,
        12,
        12,
        14,
    ]
    ORBITAL_ANGULAR_MOMENTUM = [
        0,
        0,
        1,
        1,
        0,
        1,
        1,
        2,
        2,
        0,
        1,
        1,
        2,
        2,
        3,
        3,
        0,
        1,
        1,
        2,
        2,
        3,
        3,
        4,
        4,
        0,
        1,
        1,
        2,
        2,
        3,
        3,
        4,
        4,
        5,
        5,
        0,
        1,
        1,
        2,
        2,
        3,
        3,
        4,
        4,
        5,
        5,
        6,
        6,
    ]
    TOTAL_ANGULAR_MOMENTUM = [
        0.5,
        0.5,
        0.5,
        1.5,
        0.5,
        0.5,
        1.5,
        1.5,
        2.5,
        0.5,
        0.5,
        1.5,
        1.5,
        2.5,
        2.5,
        3.5,
        0.5,
        0.5,
        1.5,
        1.5,
        2.5,
        2.5,
        3.5,
        3.5,
        4.5,
        0.5,
        0.5,
        1.5,
        1.5,
        2.5,
        2.5,
        3.5,
        3.5,
        4.5,
        4.5,
        5.5,
        0.5,
        0.5,
        1.5,
        1.5,
        2.5,
        2.5,
        3.5,
        3.5,
        4.5,
        4.5,
        5.5,
        5.5,
        6.5,
    ]
    GROUND_STATE_OCCUPANCY = read_ground_state_occupancies()

    @classmethod
    def from_name(cls, name: str) -> int:
        return cls.NAME.index(name)

    @classmethod
    def get_name(cls, shell: int) -> str:
        return cls.NAME[shell]

    @classmethod
    def family_from_name(cls, name: str) -> int:
        return cls.FAMILY.index(name[0])

    @classmethod
    def electric_dipole_permitted(cls, shell1: int, shell2: int) -> bool:
        if (
            abs(cls.TOTAL_ANGULAR_MOMENTUM[shell1] - cls.TOTAL_ANGULAR_MOMENTUM[shell2])
            > 1.0
        ):
            return False
        return (
            abs(
                cls.ORBITAL_ANGULAR_MOMENTUM[shell1]
                - cls.ORBITAL_ANGULAR_MOMENTUM[shell2]
            )
            == 1
        )

    @classmethod
    def electric_quadrupole_permitted(cls, shell1: int, shell2: int) -> bool:
        if (
            abs(cls.TOTAL_ANGULAR_MOMENTUM[shell1] - cls.TOTAL_ANGULAR_MOMENTUM[shell2])
            > 2.0
        ):
            return False
        if (
            cls.TOTAL_ANGULAR_MOMENTUM[shell1] == 0.5
            and cls.TOTAL_ANGULAR_MOMENTUM[shell2] == 0.5
        ):
            return False
        delta_l = abs(
            cls.ORBITAL_ANGULAR_MOMENTUM[shell1] - cls.ORBITAL_ANGULAR_MOMENTUM[shell2]
        )
        return delta_l == 0 or delta_l == 2

    def __init__(self, element: Element, shell: int | str):
        self._element = element
        self._shell = self.from_name(shell) if isinstance(shell, str) else shell

    @property
    def element(self) -> Element:
        return self._element

    @property
    def shell(self) -> int:
        return self._shell

    @property
    def family(self) -> int:
        return self.family_from_name(self.name)

    @property
    def name(self) -> str:
        return self.get_name(self.shell)

    @property
    def capacity(self) -> int:
        return self.CAPACITY[self.shell]

    @property
    def orbital_angular_momentum(self) -> int:
        return self.ORBITAL_ANGULAR_MOMENTUM[self.shell]

    @property
    def total_angular_momentum(self) -> float:
        return self.TOTAL_ANGULAR_MOMENTUM[self.shell]

    @property
    def ground_state_occupancy(self) -> int:
        occ = self.GROUND_STATE_OCCUPANCY[self.element.atomic_number]
        return occ[self.shell] if len(occ) > self.shell else 0

    @property
    def principal_quantum_number(self) -> int:
        """
        Gets the principal quantum number (n) associated with this shell.

        :return: The principal quantum number for this shell (1-7 for K-Q shells)
        :rtype: int
        :raises ValueError: If the shell name is invalid
        """
        n = 1
        for letter in ["K", "L", "M", "N", "O", "P", "Q"]:
            if letter in self.name:
                return n
            n += 1
        raise ValueError(f"Invalid shell name: {self.name}")

    @property
    def edge_energy(self) -> float:
        """
        Get the edge energy for this atomic shell.

        The edge energy is computed by consulting multiple databases in priority
        order. If no valid value is found, returns NaN.

        :return: The edge energy in eV, or NaN if unavailable
        :rtype: float
        """
        return EdgeEnergy.compute(self)

    @property
    def energy(self) -> float:
        return (
            self.edge_energy + self.element.ionization_energy
            if self.ground_state_occupancy
            else 0.0
        )

    @property
    def exists(self) -> bool:
        """
        Check if this atomic shell exists for its element.

        A shell is considered to exist if it has a non-zero edge energy

        :return: True if the shell exists, False otherwise
        :rtype: bool
        """
        return self.edge_energy > 0.0
