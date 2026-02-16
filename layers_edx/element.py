from __future__ import annotations
from collections.abc import Sequence
from dataclasses import InitVar, dataclass, field

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


@dataclass(slots=True)
class Composition:
    """
    Represents the elemental composition of a material.

    Internally, compositions are stored canonically as **weight fractions**.
    Atomic fractions provided at initialization are automatically converted.

    Parameters
    ----------
    elements : Sequence[Element]
        Elements contained in the composition.
    fractions : Sequence[float]
        Fractions corresponding to each element.
    weight : bool, default=True
        If True, `fractions` are interpreted as weight fractions.
        If False, they are interpreted as atomic fractions and converted.

    Raises
    ------
    ValueError
        If input lengths mismatch, composition is empty,
        or normalization encounters zero total fraction.
    """

    # ----- constructor-only inputs -----
    elements_input: InitVar[Sequence[Element]]
    fractions_input: InitVar[Sequence[float]]
    weight: InitVar[bool] = True

    # ----- stored canonical state -----
    _elements: list[Element] = field(init=False)
    _weight_fractions: list[float] = field(init=False)

    # ---------- Static utilities ----------

    @staticmethod
    def normalize_fractions(fractions: Sequence[float]) -> list[float]:
        """
        Normalize fractions so their sum equals 1.

        If the input sequence is empty, an empty list is returned. If the sum
        of the fractions is zero, a list of zeros of equal length is returned.

        """
        if not fractions:
            return []
        s = sum(fractions)
        if s == 0:
            return [0.0 for _ in fractions]
        return [f / s for f in fractions]

    @staticmethod
    def atomic_from_weight(
        elements: Sequence[Element], fractions: Sequence[float]
    ) -> list[float]:
        """
        Convert weight fractions to atomic fractions.

        Returns normalized atomic fractions.
        """
        atomic_fractions = [
            fraction / element.atomic_weight
            for element, fraction in zip(elements, fractions)
        ]
        return Composition.normalize_fractions(atomic_fractions)

    @staticmethod
    def weight_from_atomic(
        elements: Sequence[Element], fractions: Sequence[float]
    ) -> list[float]:
        """
        Convert atomic fractions to weight fractions.

        Returns normalized weight fractions.
        """
        weight_fractions = [
            fraction * element.atomic_weight
            for element, fraction in zip(elements, fractions)
        ]
        return Composition.normalize_fractions(weight_fractions)

    # ---------- Initialization ----------

    def __post_init__(
        self,
        elements_input: Sequence[Element],
        fractions_input: Sequence[float],
        weight: bool,
    ):
        self._elements = list(elements_input)
        fractions = list(fractions_input)

        if len(self._elements) != len(fractions):
            raise ValueError("elements and fractions must have same length")

        if weight:
            self._weight_fractions = fractions
        else:
            self._weight_fractions = self.weight_from_atomic(self._elements, fractions)

    # ---------- Public access ----------

    @property
    def elements(self) -> list[Element]:
        """
        Elements contained in this composition.

        Returns a copy to prevent mutation of internal state.
        """
        return self._elements.copy()

    # ---------- Copy ----------

    def copy(self) -> Composition:
        """
        Return a shallow copy of this composition.
        """
        return Composition(self._elements, self._weight_fractions)

    # ---------- Fraction views ----------

    @property
    def raw_weight_fractions(self) -> dict[Element, float]:
        """
        Mapping of elements to stored (non-normalized) weight fractions.
        """
        return dict(zip(self._elements, self._weight_fractions))

    @property
    def weight_fractions(self) -> dict[Element, float]:
        """
        Mapping of elements to normalized weight fractions.
        """
        fractions = self.normalize_fractions(self._weight_fractions)
        return dict(zip(self._elements, fractions))

    @property
    def atomic_fractions(self) -> dict[Element, float]:
        """
        Mapping of elements to normalized atomic fractions.
        """
        return dict(
            zip(
                self._elements,
                self.atomic_from_weight(self._elements, self._weight_fractions),
            )
        )

    # ---------- Sums ----------

    @property
    def raw_sum_weight_fractions(self) -> float:
        """
        Sum of stored (non-normalized) weight fractions.
        """
        return sum(self._weight_fractions)

    @property
    def sum_weight_fractions(self) -> float:
        """
        Sum of normalized weight fractions.
        """
        return sum(self.weight_fractions.values())

    # ---------- Atoms per kg ----------

    @property
    def raw_atoms_per_kg(self) -> dict[Element, float]:
        """
        Number of atoms per kilogram using stored fractions.
        """
        return {e: f / e.mass for e, f in self.raw_weight_fractions.items()}

    @property
    def atoms_per_kg(self) -> dict[Element, float]:
        """
        Number of atoms per kilogram using normalized fractions.
        """
        return {e: f / e.mass for e, f in self.weight_fractions.items()}

    # ---------- Means ----------

    @property
    def raw_mean_atomic_number(self) -> float:
        """
        Mean atomic number using stored fractions.
        """
        return sum([e.atomic_number * f for e, f in self.raw_weight_fractions.items()])

    @property
    def mean_atomic_number(self) -> float:
        """
        Mean atomic number using normalized fractions.
        """
        return sum([e.atomic_number * f for e, f in self.weight_fractions.items()])

    # ---------- Comparison ----------

    def weight_difference(
        self, other: Composition, normalized: bool = True
    ) -> dict[Element, float]:
        """
        Compute element-wise weight fraction difference.

        Parameters
        ----------
        other : Composition
            Composition to subtract from this one.
        normalized : bool, default=True
            Whether to compare normalized fractions.

        Returns
        -------
        dict[Element, float]
            Mapping of element → difference (self - other).
        """
        self_f = self.weight_fractions if normalized else self.raw_weight_fractions
        other_f = other.weight_fractions if normalized else other.raw_weight_fractions

        diffs: dict[Element, float] = {}
        for e in self_f.keys() | other_f.keys():
            diffs[e] = self_f.get(e, 0.0) - other_f.get(e, 0.0)
        return diffs


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
