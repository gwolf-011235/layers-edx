from __future__ import annotations
from layers_edx import read_csv, llf
from layers_edx.atomic_shell import EdgeEnergy, AtomicShell
from layers_edx.element import Element
from layers_edx.units import ToSI
from typing import Literal

# Type alias for weight normalization parameter
WeightNormalization = Literal["default", "family", "destination", "klm"]

K_FAMILY = ["KA1", "KA2", "KB1", "KB2", "KB3", "KB4", "KB5"]
L_FAMILY = [
    "L3N2",
    "L3N3",
    "L3O2",
    "L3O3",
    "L3P1",
    "LA1",
    "LA2",
    "LB15",
    "LB2",
    "LB5",
    "LB6",
    "LB7",
    "Ll",
    "Ls",
    "Lt",
    "Lu",
    "L2M2",
    "L2M5",
    "L2N2",
    "L2N3",
    "L2N5",
    "L2O2",
    "L2O3",
    "L2P2",
    "LB1",
    "LB17",
    "LG1",
    "LG5",
    "LG6",
    "LG8",
    "Ln",
    "Lv",
    "L1M1",
    "L1N1",
    "L1N4",
    "L1O1",
    "L1O4",
    "LB10",
    "LB3",
    "LB4",
    "LB9",
    "LG2",
    "LG11",
    "LG3",
    "LG4",
    "LG4p",
]
M_FAMILY = [
    "M1N2",
    "M1N3",
    "M2M4",
    "M2N1",
    "M2N4",
    "M2O4",
    "M3M4",
    "M3M5",
    "M3N1",
    "M3N4",
    "M3O1",
    "M3O4",
    "M3O5",
    "MG",
    "M4N3",
    "M4O2",
    "MB",
    "MZ2",
    "M5O3",
    "MA1",
    "MA2",
    "MZ1",
]
N_FAMILY = ["N4N6", "N5N6"]
FAMILIES = {"K": K_FAMILY, "L": L_FAMILY, "M": M_FAMILY, "N": N_FAMILY}
NAME = K_FAMILY + L_FAMILY + M_FAMILY + N_FAMILY
SOURCE_SHELL = [
    AtomicShell.from_name(shell)
    for shell in [
        "LIII",
        "LII",
        "MIII",
        "NIII",
        "MII",
        "NV",
        "MV",
        "NII",
        "NIII",
        "OII",
        "OIII",
        "PI",
        "MV",
        "MIV",
        "NIV",
        "NV",
        "OIV",
        "NI",
        "OI",
        "MI",
        "MIII",
        "MII",
        "NVI",
        "MII",
        "MV",
        "NII",
        "NIII",
        "NV",
        "OII",
        "OIII",
        "PII",
        "MIV",
        "MIII",
        "NIV",
        "NI",
        "OIV",
        "OI",
        "MI",
        "NVI",
        "MI",
        "NI",
        "NIV",
        "OI",
        "OIV",
        "MIV",
        "MIII",
        "MII",
        "MV",
        "NII",
        "NV",
        "NIII",
        "OIII",
        "OII",
        "NII",
        "NIII",
        "MIV",
        "NI",
        "NIV",
        "OIV",
        "MIV",
        "MV",
        "NI",
        "NIV",
        "OI",
        "OIV",
        "OV",
        "NV",
        "NIII",
        "OII",
        "NVI",
        "NII",
        "OIII",
        "NVII",
        "NVI",
        "NIII",
        "NVI",
        "NVI",
    ]
]
DESTINATION_SHELL = [
    AtomicShell.from_name(shell)
    for shell in [
        "K",
        "K",
        "K",
        "K",
        "K",
        "K",
        "K",
        "LIII",
        "LIII",
        "LIII",
        "LIII",
        "LIII",
        "LIII",
        "LIII",
        "LIII",
        "LIII",
        "LIII",
        "LIII",
        "LIII",
        "LIII",
        "LIII",
        "LIII",
        "LIII",
        "LII",
        "LII",
        "LII",
        "LII",
        "LII",
        "LII",
        "LII",
        "LII",
        "LII",
        "LII",
        "LII",
        "LII",
        "LII",
        "LII",
        "LII",
        "LII",
        "LI",
        "LI",
        "LI",
        "LI",
        "LI",
        "LI",
        "LI",
        "LI",
        "LI",
        "LI",
        "LI",
        "LI",
        "LI",
        "LI",
        "MI",
        "MI",
        "MII",
        "MII",
        "MII",
        "MII",
        "MIII",
        "MIII",
        "MIII",
        "MIII",
        "MIII",
        "MIII",
        "MIII",
        "MIII",
        "MIV",
        "MIV",
        "MIV",
        "MIV",
        "MV",
        "MV",
        "MV",
        "MV",
        "NIV",
        "NV",
    ]
]
LINE_WEIGHT: llf = read_csv("LineWeights", row_offset=1, value_offset=1)


def transition_from_name(name: str) -> int:
    return NAME.index(name)


def transition_from_shells(source: int, destination: int) -> int | None:
    result = None
    for i in range(len(NAME)):
        if source == SOURCE_SHELL[i] and destination == DESTINATION_SHELL[i]:
            result = i
            break
    return result


def destination_shell_from_transition(transition: int) -> int:
    """
    Get the shell to which the electron jumps during the x-ray emission process.
    The destination shell is typically a core electron.
    """
    return DESTINATION_SHELL[transition]


def family_from_transition(transition: int) -> int:
    dest_name = AtomicShell.get_name(destination_shell_from_transition(transition))
    return AtomicShell.family_from_name(dest_name)


def weight_normalization(weights_list: llf) -> tuple[llf, llf, llf]:
    dest_len = AtomicShell.from_name("NV") - AtomicShell.from_name("K") + 1
    dest_norm = [[0.0] * dest_len for _ in range(len(weights_list))]
    fam_len = AtomicShell.family_from_name("N") - AtomicShell.family_from_name("K") + 1
    fam_norm = [[0.0] * fam_len for _ in range(len(weights_list))]
    klm_norm = [[0.0] * fam_len for _ in range(len(weights_list))]
    for atomic_number, weights in enumerate(weights_list[1:], start=1):
        for transition, weight in enumerate(weights):
            destination = destination_shell_from_transition(transition)
            dest_norm[atomic_number][destination] += weight
            family = family_from_transition(transition)
            if weight > klm_norm[atomic_number][family]:
                klm_norm[atomic_number][family] = weight
            fam_norm[atomic_number][family] += weight
        for destination in range(dest_len):
            if dest_norm[atomic_number][destination] == 0.0:
                dest_norm[atomic_number][destination] = 1.0
        for family in range(fam_len):
            if fam_norm[atomic_number][family] == 0.0:
                fam_norm[atomic_number][family] = 1.0
            if klm_norm[atomic_number][family] == 0.0:
                klm_norm[atomic_number][family] = 1.0
    return fam_norm, dest_norm, klm_norm


FAMILY_NORM, DESTINATION_NORM, KLM_NORM = weight_normalization(LINE_WEIGHT)


class TransitionEnergy:
    ee = EdgeEnergy

    @classmethod
    def compute(cls, xrt: XRayTransition) -> float:
        edge_destination = cls.ee.compute(xrt.destination)
        edge_source = cls.ee.compute(xrt.source)
        if edge_destination > 0.0 and edge_source > 0.0:
            result = edge_destination - edge_source
            if result == 0.0 or (ToSI.ev(0.1) < result < ToSI.ev(1.0e6)):
                return result
        return -1.0


class XRayTransition:
    @classmethod
    def _source_shell(cls, element: Element, transition: int) -> int:
        """
        Some transitions are not consistent with the standard naming schemes.
        For example, C Ka is K-L2 and not K-L3 because L3 doesn't exist in C
        and Ka refers to the brightest K line.
        """
        result = SOURCE_SHELL[transition]
        atomic_number = element.atomic_number
        if atomic_number in [Element.from_name("Li"), Element.from_name("Be")]:
            if result in [AtomicShell.from_name("LII"), AtomicShell.from_name("LIII")]:
                result = AtomicShell.from_name("LI")
        elif atomic_number in [Element.from_name("B"), Element.from_name("C")]:
            if result == AtomicShell.from_name("LIII"):
                result = AtomicShell.from_name("LII")
        elif atomic_number in [Element.from_name("Al"), Element.from_name("Si")]:
            if result == AtomicShell.from_name("MIII"):
                result = AtomicShell.from_name("MII")
        elif atomic_number in [
            Element.from_name("Sc"),
            Element.from_name("Ti"),
            Element.from_name("V"),
        ]:
            if result == AtomicShell.from_name("MV"):
                result = AtomicShell.from_name("MIV")
        elif atomic_number in [Element.from_name("Ga"), Element.from_name("Ge")]:
            if result == AtomicShell.from_name("NIII"):
                result = AtomicShell.from_name("NII")
        elif atomic_number in [Element.from_name("Kr")]:
            if result == AtomicShell.from_name("NV"):
                result = AtomicShell.from_name("NIII")
        elif atomic_number in [Element.from_name("Y"), Element.from_name("Zr")]:
            if result == AtomicShell.from_name("NV"):
                result = AtomicShell.from_name("NIV")
        elif atomic_number in [Element.from_name("Nb"), Element.from_name("Mo")]:
            if result == AtomicShell.from_name("NV"):
                result = AtomicShell.from_name("NIV")
            elif result == AtomicShell.from_name("OII"):
                result = AtomicShell.from_name("OI")
        elif atomic_number in [
            Element.from_name("Tc"),
            Element.from_name("Ru"),
            Element.from_name("Rh"),
            Element.from_name("Pd"),
            Element.from_name("Ag"),
        ]:
            if result == AtomicShell.from_name("OII"):
                result = AtomicShell.from_name("OI")
        elif atomic_number in [Element.from_name("Cd"), Element.from_name("In")]:
            if result in [AtomicShell.from_name("OII"), AtomicShell.from_name("OIII")]:
                result = AtomicShell.from_name("OI")
        elif atomic_number in [Element.from_name("Sn")]:
            if result == AtomicShell.from_name("OIII"):
                result = AtomicShell.from_name("OI")
        elif atomic_number in [
            Element.from_name("Pr"),
            Element.from_name("Nd"),
            Element.from_name("Pm"),
            Element.from_name("Sm"),
            Element.from_name("Eu"),
        ]:
            if result == AtomicShell.from_name("NVII"):
                result = AtomicShell.from_name("NVI")
        elif atomic_number in [Element.from_name("Yb")]:
            if result == AtomicShell.from_name("OIV"):
                result = AtomicShell.from_name("OIII")
        elif atomic_number in [Element.from_name("W")]:
            if result == AtomicShell.from_name("OV"):
                result = AtomicShell.from_name("OIV")
        elif atomic_number in [Element.from_name("Au"), Element.from_name("Hg")]:
            if result == AtomicShell.from_name("PI"):
                result = AtomicShell.from_name("OVIII")
        elif atomic_number in [Element.from_name("Tl"), Element.from_name("Pb")]:
            if result == AtomicShell.from_name("PI"):
                result = AtomicShell.from_name("OIX")
        elif atomic_number in [Element.from_name("Ra")]:
            if result == AtomicShell.from_name("PII"):
                result = AtomicShell.from_name("PI")
        return result

    @classmethod
    def get_weight(
        cls,
        element: Element,
        transition: int,
        normalization: WeightNormalization = "default",
    ) -> float:
        """Gets the transition weight associated with this transition.

        Args:
            element: The element for this transition.
            transition: The transition index.
            normalization: How to normalize the weight. Options:
                - 'default': Raw weight from LINE_WEIGHT table
                - 'family': Normalized by sum of all transitions in the family
                - 'destination': Normalized by sum of all transitions to the
                  destination shell
                - 'klm': Normalized by the maximum weight in the family

        Returns:
            The (normalized) transition weight.

        Raises:
            ValueError: If normalization is not a valid option.
        """
        z = element.atomic_number
        if transition >= len(LINE_WEIGHT[z]):
            return 0.0
        if normalization == "default":
            return LINE_WEIGHT[z][transition]
        elif normalization == "family":
            return (
                LINE_WEIGHT[z][transition]
                / FAMILY_NORM[z][family_from_transition(transition)]
            )
        elif normalization == "destination":
            return (
                LINE_WEIGHT[z][transition]
                / DESTINATION_NORM[z][destination_shell_from_transition(transition)]
            )
        elif normalization == "klm":
            return (
                LINE_WEIGHT[z][transition]
                / KLM_NORM[z][family_from_transition(transition)]
            )
        else:
            raise ValueError(
                f"Invalid normalization '{normalization}'. "
                f"Must be one of: 'default', 'family', 'destination', 'klm'"
            )

    @classmethod
    def transition_with_lowest_energy(cls, element: Element, family: list[str]) -> int:
        """
        Returns the transition index of the line in the specified `family`
        with the lowest x-ray energy.
        """
        min_energy = float("inf")
        min_transition = -1
        for name in family:
            xrt = XRayTransition(element, name)
            if xrt.exists and xrt.energy < min_energy:
                # to silence type checker: xrt.exists guarantees transition is not None
                assert xrt.transition is not None
                min_energy = xrt.energy
                min_transition = xrt.transition
        return min_transition

    def __init__(
        self,
        element: Element,
        transition: int | str | None = None,
        source: int | None = None,
        destination: int | None = None,
    ):
        """
        Create an object corresponding to a specific x-ray transition in a
        specific element.
        """
        if transition is not None:
            self._transition = (
                transition_from_name(transition)
                if isinstance(transition, str)
                else transition
            )
            self._source = AtomicShell(
                element, self._source_shell(element, self._transition)
            )
            self._destination = AtomicShell(
                element, DESTINATION_SHELL[self._transition]
            )
        elif source is not None and destination is not None:
            transition = transition_from_shells(source, destination)
            self._transition = transition
            self._source = AtomicShell(element, source)
            self._destination = AtomicShell(element, destination)
        else:
            raise ValueError(
                "Either `transition` or `source` & `destination` must be provided!"
            )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, XRayTransition):
            return NotImplemented
        return (
            self.transition == other.transition
            and self.source_shell == other.source_shell
            and self.destination_shell == other.destination_shell
        )

    def __hash__(self) -> int:
        return hash((self.transition, self.source_shell, self.destination_shell))

    @property
    def transition(self) -> int | None:
        return self._transition

    @property
    def source(self) -> AtomicShell:
        return self._source

    @property
    def source_shell(self) -> int:
        return self.source.shell

    @property
    def destination(self) -> AtomicShell:
        return self._destination

    @property
    def destination_shell(self) -> int:
        return self.destination.shell

    @property
    def family(self) -> int:
        if self.transition is None:
            raise ValueError("Cannot get family of invalid transition")
        return family_from_transition(self.transition)

    @property
    def element(self) -> Element:
        return self.source.element

    @property
    def energy(self) -> float:
        return TransitionEnergy.compute(self)

    @property
    def edge_energy(self) -> float:
        return EdgeEnergy.compute(self.destination)

    @property
    def exists(self) -> bool:
        return (
            self.transition is not None
            and self.source.exists
            and self.destination.exists
            and self.weight() > 0.0
        )

    def weight(
        self,
        normalization: WeightNormalization = "default",
    ) -> float:
        if self.transition is None:
            return 0.0
        return self.get_weight(self.element, self.transition, normalization)


class XRayTransitionSet:
    def __init__(
        self,
        element: Element,
        low_energy: float = 0.0,
        high_energy: float = float("inf"),
        min_weight: float = 0.0,
        populate: bool = True,
    ):
        """
        Constructs an `XRayTransitionSet` consisting of all transitions for the
        specified `element` between the `low_energy` and `high_energy` having a
        `min_weight`. Creates an empty `xrts` if `populate` is set to False.
        """
        self._element = element
        self._xrts: set[XRayTransition] = set()
        if populate is False:
            return
        for transition in range(len(NAME)):
            xrt = XRayTransition(element, transition)
            if (
                xrt.exists
                and low_energy <= xrt.energy <= high_energy
                and min_weight <= xrt.weight("klm")
            ):
                self._xrts.add(xrt)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, XRayTransitionSet):
            return NotImplemented
        return self.xrts == other.xrts

    def __hash__(self) -> int:
        return sum([hash(xrt) for xrt in self.xrts])

    @property
    def element(self) -> Element:
        """The `element` represented by this `XRayTransitionSet`."""
        return self._element

    @property
    def xrts(self) -> set[XRayTransition]:
        """The set of `XRayTransition` objects contained in this `XRayTransitionSet`."""
        return self._xrts

    @property
    def weightiest_transition(self) -> XRayTransition:
        """Returns the single weightiest transition."""
        max_weight = 0.0
        result: XRayTransition | None = None
        for xrt in self.xrts:
            weight = xrt.weight("family")
            if weight > max_weight:
                max_weight = weight
                result = xrt
        if result is None:
            raise ValueError("Cannot get weightiest transition from empty set")
        return result

    def contains(self, xrt: XRayTransition):
        """Checks if the `XRayTransitionSet` contains the specified `XRayTransition`."""
        return xrt in self.xrts

    def add(self, xrt: XRayTransition):
        """Adds the `xrt` to the `self.xrts` if they represent the same element."""
        if self.element == xrt.element and xrt.exists:
            self._xrts.add(xrt)

    def remove(self, xrt: XRayTransition):
        """Removes the `xrt` from the `self.xrts`."""
        self._xrts.remove(xrt)

    @staticmethod
    def from_xrts(xrts: set[XRayTransition]) -> XRayTransitionSet:
        xrt_set = XRayTransitionSet(next(iter(xrts)).element, populate=False)
        for xrt in xrts:
            xrt_set.add(xrt)
        return xrt_set

    @staticmethod
    def all_xrts(element: Element, max_energy: float) -> XRayTransitionSet:
        """
        Constructs the full set of `XRayTransition`s
        of edge energy less than `max_energy`.
        """
        xrt_set = XRayTransitionSet(element, populate=False)
        for name in NAME:
            xrt = XRayTransition(element, name)
            if xrt.exists and xrt.edge_energy < max_energy:
                xrt_set.add(xrt)
        return xrt_set

    def similarity(self, xrt_set: XRayTransitionSet) -> float:
        score = 0.0
        total = 0.0
        for xrt in self.xrts | xrt_set.xrts:
            weight = xrt.weight("family")
            total += weight
            if xrt in self.xrts and xrt in xrt_set.xrts:
                score += weight
        return score / total if total > 0.0 else 0.0
