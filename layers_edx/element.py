from __future__ import annotations

from layers_edx import read_csv
from layers_edx.units import ToSI


class Element:
    NAME = [
        "None",
        "H",
        "He",
        "Li",
        "Be",
        "B",
        "C",
        "N",
        "O",
        "F",
        "Ne",
        "Na",
        "Mg",
        "Al",
        "Si",
        "P",
        "S",
        "Cl",
        "Ar",
        "K",
        "Ca",
        "Sc",
        "Ti",
        "V",
        "Cr",
        "Mn",
        "Fe",
        "Co",
        "Ni",
        "Cu",
        "Zn",
        "Ga",
        "Ge",
        "As",
        "Se",
        "Br",
        "Kr",
        "Rb",
        "Sr",
        "Y",
        "Zr",
        "Nb",
        "Mo",
        "Tc",
        "Ru",
        "Rh",
        "Pd",
        "Ag",
        "Cd",
        "In",
        "Sn",
        "Sb",
        "Te",
        "I",
        "Xe",
        "Cs",
        "Ba",
        "La",
        "Ce",
        "Pr",
        "Nd",
        "Pm",
        "Sm",
        "Eu",
        "Gd",
        "Tb",
        "Dy",
        "Ho",
        "Er",
        "Tm",
        "Yb",
        "Lu",
        "Hf",
        "Ta",
        "W",
        "Re",
        "Os",
        "Ir",
        "Pt",
        "Au",
        "Hg",
        "Tl",
        "Pb",
        "Bi",
        "Po",
        "At",
        "Rn",
        "Fr",
        "Ra",
        "Ac",
        "Th",
        "Pa",
        "U",
        "Np",
        "Pu",
        "Am",
        "Cm",
        "Bk",
        "Cf",
        "Es",
        "Fm",
        "Md",
        "No",
        "Lr",
        "Rf",
        "Db",
        "Sg",
        "Bh",
        "Hs",
        "Mt",
        "Ds",
        "Rg",
        "Cn",
        "Nh",
        "Fl",
        "Mc",
        "Lv",
        "Ts",
        "Og",
    ]

    ATOMIC_WEIGHT = [
        v[0]
        for v in read_csv(
            "AtomicWeights",
            row_offset=1,
            value_offset=1,
            fill_value=0.0,
        )
    ]

    IONIZATION_ENERGY = [
        v[0]
        for v in read_csv(
            "IonizationEnergies",
            row_offset=2,
            value_offset=1,
            conversion=ToSI.ev,
            fill_value=float("nan"),
        )
    ]

    @classmethod
    def from_name(cls, name: str) -> int:
        return cls.NAME.index(name)

    def __init__(self, element: int | str):
        self._atomic_number = (
            element if isinstance(element, int) else self.NAME.index(element)
        )

    def __lt__(self, other: Element):
        return self.atomic_number < other.atomic_number

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Element):
            return NotImplemented
        return self.atomic_number == other.atomic_number

    def __hash__(self) -> int:
        return self.atomic_number

    def __str__(self) -> str:
        return f"Element.{self.name}"

    @property
    def atomic_number(self) -> int:
        """The nuclear charge number, i.e., the number of protons, of the element."""
        return self._atomic_number

    @property
    def name(self) -> str:
        """The chemical symbol of the element."""
        return self.NAME[self.atomic_number]

    @property
    def atomic_weight(self) -> float:
        """The standard atomic weight of the element (g/mol)."""
        return self.ATOMIC_WEIGHT[self.atomic_number]

    @property
    def ionization_energy(self) -> float:
        """The first ionization energy for this element (J)."""
        return self.IONIZATION_ENERGY[self.atomic_number]

    @property
    def mass(self) -> float:
        """The mass of a single atom of the element (kg)."""
        return ToSI.amu(self.atomic_weight)


class Composition:
    @staticmethod
    def normalize_fractions(fractions: list[float]) -> list[float]:
        """Divides each of the values by the sum of all values."""
        fractions_sum = sum(fractions)
        return [fraction / fractions_sum for fraction in fractions]

    @staticmethod
    def atomic_from_weight(
        elements: list[Element], fractions: list[float]
    ) -> list[float]:
        """Computes the atomic fractions from the provided `elements`
        and weight `fractions`."""
        atomic_fractions = [
            fraction / element.atomic_weight
            for element, fraction in zip(elements, fractions)
        ]
        return Composition.normalize_fractions(atomic_fractions)

    @staticmethod
    def weight_from_atomic(
        elements: list[Element], fractions: list[float]
    ) -> list[float]:
        """Computes the weight fractions from the provided `elements`
        and atomic `fractions`."""
        weight_fractions = [
            fraction * element.atomic_weight
            for element, fraction in zip(elements, fractions)
        ]
        return Composition.normalize_fractions(weight_fractions)

    def __init__(
        self,
        elements: list[Element],
        fractions: list[float],
        weight: bool = True,
    ):
        self._elements = elements
        if weight:
            self._weight_fractions = fractions
        else:
            self._weight_fractions = self.weight_from_atomic(elements, fractions)

    def copy(self) -> Composition:
        """Initializes a new object with shallow copies of the `elements`
        and `weight_fractions` lists."""
        return Composition(self._elements.copy(), self._weight_fractions.copy())

    @property
    def elements(self) -> list[Element]:
        """The list of elements which are contained in this composition."""
        return self._elements

    @property
    def atomic_fractions(self) -> dict[Element, float]:
        """A dictionary mapping the elements to their atomic fractions
        as defined in this composition. Normalized to sum 100%."""
        return dict(
            zip(
                self.elements,
                self.atomic_from_weight(self.elements, self._weight_fractions),
            )
        )

    @property
    def raw_weight_fractions(self) -> dict[Element, float]:
        """A dictionary mapping the elements to their weight fractions
        as defined in this composition."""
        return dict(zip(self.elements, self._weight_fractions))

    @property
    def weight_fractions(self) -> dict[Element, float]:
        """A dictionary mapping the elements to their weight fractions
        which are normalized to sum 100%."""
        fractions = self.normalize_fractions(self._weight_fractions)
        return dict(zip(self.elements, fractions))

    @property
    def raw_sum_weight_fractions(self) -> float:
        """The non-normalized sum of the weight fractions."""
        return sum(self._weight_fractions)

    @property
    def sum_weight_fractions(self) -> float:
        """The sum of the normalized weight fractions."""
        return sum(self.weight_fractions.values())

    @property
    def raw_atoms_per_kg(self) -> dict[Element, float]:
        """Number of atoms of the elements in one kilogram of material
        with this composition."""
        return {e: f / e.mass for e, f in self.raw_weight_fractions.items()}

    @property
    def atoms_per_kg(self) -> dict[Element, float]:
        """Number of atoms of the elements in one kilogram of material
        with this normalized composition."""
        return {e: f / e.mass for e, f in self.weight_fractions.items()}

    @property
    def raw_mean_atomic_number(self) -> float:
        """The mean atomic number based on the raw weight fractions."""
        return sum([e.atomic_number * f for e, f in self.raw_weight_fractions.items()])

    @property
    def mean_atomic_number(self) -> float:
        """The mean atomic number based on the normalized weight fractions."""
        return sum([e.atomic_number * f for e, f in self.weight_fractions.items()])

    def weight_difference(
        self, other: Composition, normalized: bool = True
    ) -> dict[Element, float]:
        """Calculates the differences of two composition objects: self - other."""
        differences: dict[Element, float] = {}
        self_fractions = (
            self.weight_fractions if normalized else self.raw_weight_fractions
        )
        other_fractions = (
            other.weight_fractions if normalized else other.raw_weight_fractions
        )
        for e in self_fractions.keys() | other_fractions.keys():
            self_f = self_fractions[e] if e in self_fractions else 0
            other_f = other_fractions[e] if e in other_fractions else 0
            differences[e] = self_f - other_f
        return differences


class Material:
    DENSITY = [
        0.0,
        0.0,
        0.0,
        0.534,
        1.85,
        2.35,
        2.25,
        0.0,
        0.0,
        0.0,
        0.0,
        0.97,
        1.74,
        2.70,
        2.42,
        1.83,
        1.92,
        0.0,
        0.0,
        0.86,
        1.55,
        3.02,
        4.50,
        5.98,
        7.14,
        7.41,
        7.88,
        8.71,
        8.88,
        8.96,
        7.10,
        5.93,
        5.46,
        5.73,
        4.82,
        0.0,
        0.0,
        1.53,
        2.56,
        4.47,
        6.40,
        8.57,
        10.22,
        11.5,
        12.1,
        12.44,
        12.16,
        10.49,
        8.65,
        7.28,
        7.3,
        6.62,
        6.25,
        4.94,
        0.0,
        1.87,
        3.50,
        6.15,
        6.90,
        6.48,
        6.96,
        -1.0,
        7.75,
        5.26,
        7.95,
        8.27,
        8.54,
        8.80,
        9.05,
        9.33,
        6.97,
        9.84,
        13.3,
        16.6,
        19.3,
        21.0,
        22.5,
        22.42,
        21.45,
        19.3,
        14.19,
        11.86,
        11.34,
        9.78,
        9.3,
        -1.0,
        0.0,
        -1.0,
        5.0,
        -1.0,
        11.7,
        15.3,
        18.7,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
        -1.0,
    ]

    @classmethod
    def density_from_composition(cls, composition: Composition) -> float:
        density = 0
        for element, fraction in composition.weight_fractions.items():
            density += fraction * cls.DENSITY[element.atomic_number]
        return density

    def __init__(
        self, composition: Composition | Element, density: float | None = None
    ):
        if isinstance(composition, Element):
            composition = Composition([composition], [1.0])
        self._composition = composition
        self._density = (
            self.density_from_composition(composition) if density is None else density
        )

    @property
    def composition(self) -> Composition:
        """The composition of the material."""
        return self._composition

    @property
    def density(self) -> float:
        """The density of the material (g*cm-3)."""
        return self._density
