from __future__ import annotations

from typing import Annotated, Dict, Type, TypeAlias

from pydantic import BaseModel, BeforeValidator, ConfigDict
from test.epq_dump.core_models import CsvTable


def _empty_str_to_none(v: str | None) -> str | None:
    if v is None:
        return None
    if v == "":
        return None
    raise ValueError("Value is not empty")


EmptyStrToNone: TypeAlias = Annotated[None, BeforeValidator(_empty_str_to_none)]


class ElementRow(BaseModel):
    """Model for a single Element row."""

    Z: int
    symbol: str
    name: str
    atomic_weight: float
    mass_in_kg: float
    ionization_energy: float | EmptyStrToNone
    mean_ionization_potential: float

    model_config = ConfigDict(str_strip_whitespace=True, strict=False)


class XRayTransitionRow(BaseModel):
    """Model for a single XRayTransition row."""

    Z: int
    transition_index: int
    transition_name: str
    source_shell: str
    destination_shell: str
    family: str
    is_well_known: bool
    exists: bool | EmptyStrToNone
    energy: float | EmptyStrToNone
    edge_energy_eV: float | EmptyStrToNone
    weight_default: float | EmptyStrToNone
    weight_family: float | EmptyStrToNone
    weight_destination: float | EmptyStrToNone
    weight_klm: float | EmptyStrToNone

    model_config = ConfigDict(str_strip_whitespace=True, strict=False)


class AtomicShellRow(BaseModel):
    """Model for a single AtomicShell row."""

    Z: int
    shell_index: int
    shell_name_siegbahn: str
    shell_name_iupac: str
    shell_name_atomic: str
    family: str
    principal_quantum_number: int
    orbital_angular_momentum: int
    total_angular_momentum: float
    capacity: int
    exists: bool | EmptyStrToNone
    ground_state_occupancy: int | EmptyStrToNone
    edge_energy_ev: float | EmptyStrToNone
    energy_J: float | EmptyStrToNone

    model_config = ConfigDict(str_strip_whitespace=True, strict=False)


class CompositionRow(BaseModel):
    """Model for a single Composition row (one element per row)."""

    element: str
    atomic_number: int
    weight_fraction: float
    normalized_weight_fraction: float
    atomic_percent: float
    atoms_per_kg: float

    model_config = ConfigDict(str_strip_whitespace=True, strict=False)


_MODELS: Dict[str, Type[BaseModel]] = {
    "Element": ElementRow,
    "XRayTransition": XRayTransitionRow,
    "AtomicShell": AtomicShellRow,
    "Composition": CompositionRow,
}


def validate_table(module: str, table: CsvTable) -> list[BaseModel]:
    """Validate a Java CSV dump table against the registered pydantic model.

    Args:
        module: Dump module name (e.g., "XRayTransition")
        table: A CsvTable (list of dictionaries)

    Returns the validated CsvTable with types coerced, or raises a
    pydantic.ValidationError / KeyError if invalid.
    """
    model = _MODELS.get(module)
    if model is None:
        raise KeyError(f"No pydantic model registered for dump module: {module}")

    # Validate each row
    validated_rows = [model(**row) for row in table]

    return validated_rows
