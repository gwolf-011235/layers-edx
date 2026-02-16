import math
from abc import ABC, abstractmethod
from typing import Type
from layers_edx.atomic_shell import AtomicShell
from layers_edx.element import Composition
from layers_edx.material_properties.fl import Fluorescence
from layers_edx.material_properties.mac import MassAbsorptionCoefficient
from layers_edx.spectrum.spectrum_properties import SpectrumProperties
from layers_edx.units import ToSI
from layers_edx.xrt import XRayTransition


class Correction(ABC):
    fl = Fluorescence

    def __init__(
        self,
        composition: Composition,
        shell: AtomicShell,
        properties: SpectrumProperties,
    ):
        self._composition = composition
        self._shell = shell
        self._properties = properties
        self._beam_energy = ToSI.kev(properties.beam_energy)
        self._take_off_angle = properties.take_off_angle
        self._mac = MassAbsorptionCoefficient

    @property
    def composition(self) -> Composition:
        """The assumed composition of the sample."""
        return self._composition

    @property
    def shell(self) -> AtomicShell:
        """The ionized shell."""
        return self._shell

    @property
    def properties(self) -> SpectrumProperties:
        """The properties at which the data is assumed to be collected."""
        return self._properties

    @property
    def beam_energy(self) -> float:
        """The incident beam energy in J."""
        return self._beam_energy

    @property
    def take_off_angle(self) -> float:
        """
        The angle at which the detector is located. Measured up from the x-y plane in
        radians (rad).
        """
        return self._take_off_angle

    @property
    def mac(self) -> Type[MassAbsorptionCoefficient]:
        """The mass absorption coefficient instance."""
        return self._mac

    def chi(self, xrt: XRayTransition) -> float:
        """
        Retrieves the mass absorption coefficient for the specified `XRayTransition`.
        """
        return self.mac.compute_composition(self.composition, xrt.energy) / math.sin(
            self.take_off_angle
        )  # TODO: store for xrt

    @abstractmethod
    def compute_za_correction(self, xrt: XRayTransition) -> float:
        """
        Computes the ZA or Phi(rho z) part of the ZAF correction. The returned number is
        not necessarily meaningful in-and-of-itself. It may need to be compared with a
        standard to produce a correction factor.
        """

    def compute_zaf_correction(self, xrt: XRayTransition) -> float:
        """Computes the full ZAF correction."""
        za = self.compute_za_correction(xrt)
        f = self.fl.compute(
            self.composition, xrt, self.beam_energy, self.take_off_angle
        )
        return za * f


class NoCorrection(Correction):
    def compute_za_correction(self, xrt: XRayTransition) -> float:
        return 1.0

    def compute_zaf_correction(self, xrt: XRayTransition) -> float:
        return 1.0


class PhiRhoZ(Correction, ABC):
    @abstractmethod
    def compute_curve(self, rho_z: float) -> float:
        """Computes the height of the phi-rho-z at the specified z position."""

    def compute_absorbed(self, rho_z: float, xrt: XRayTransition) -> float:
        return self.compute_curve(rho_z) * math.exp(-self.chi(xrt) * rho_z)
