from pytest import approx
from layers_edx.element import Element, Composition, Material


def test_element_creation():
    si = Element("Si")
    assert si.name == "Si"
    assert si.atomic_number == 14

    si_by_z = Element(14)
    assert si_by_z.name == "Si"
    assert si_by_z == si


def test_element_properties():
    c = Element("C")
    assert c.atomic_weight > 0
    assert c.mass > 0
    assert c.ionization_energy > 0

    # Check specific values (approximate)
    assert c.atomic_weight == approx(12.01, rel=1e-3)


def test_element_comparison():
    h = Element("H")
    he = Element("He")
    assert h < he
    assert h != he
    assert h == Element("H")


def test_composition_creation_weight():
    si = Element("Si")
    o = Element("O")
    # SiO2 approx weights: Si=28, O=16*2=32. Total=60. Si=28/60=0.466, O=32/60=0.533
    comp = Composition([si, o], [28.0855, 2 * 15.9994])

    assert len(comp.elements) == 2
    assert comp.weight_fractions[si] == approx(28.0855 / (28.0855 + 31.9988))
    assert comp.weight_fractions[o] == approx(31.9988 / (28.0855 + 31.9988))


def test_composition_creation_atomic():
    si = Element("Si")
    o = Element("O")
    # SiO2: 1 Si, 2 O
    comp = Composition([si, o], [1.0, 2.0], weight=False)

    atomic_fracs = comp.atomic_fractions
    assert atomic_fracs[si] == approx(1.0 / 3.0)
    assert atomic_fracs[o] == approx(2.0 / 3.0)


def test_composition_normalization():
    fe = Element("Fe")
    comp = Composition([fe], [0.5])
    assert comp.weight_fractions[fe] == 1.0


def test_composition_properties():
    h = Element("H")  # ~1
    o = Element("O")  # ~16
    # H2O
    comp = Composition([h, o], [2.0, 1.0], weight=False)

    assert comp.mean_atomic_number > 1
    assert comp.mean_atomic_number < 10

    atoms = comp.atoms_per_kg
    assert atoms[h] > atoms[o]  # More H atoms than O atoms in H2O


def test_material():
    si = Element("Si")
    mat = Material(si)
    assert mat.density == approx(2.35, rel=0.1)  # Si density ~2.33

    # Custom density
    mat_custom = Material(si, density=10.0)
    assert mat_custom.density == 10.0
