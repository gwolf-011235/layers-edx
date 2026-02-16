# Testing Recipes

Step-by-step how-to guides for common tasks: adding a new dump module, writing a golden test, debugging, and troubleshooting.

## Recipe: Add a New Dump Module

This recipe shows how to add a new dump module to the Java oracle.

### Prerequisites

- `test/java/pom.xml` has the EPQ library as a dependency
- Maven 3.6+ is installed
- You're familiar with the EPQ API

### Steps

#### 1. Create the DumpModule Implementation

Create a new file: `test/java/src/main/java/epq/reference/ElementDump.java`

```java
package epq.reference;

import static epq.reference.CsvColumn.Type.*;

import gov.nist.microanalysis.EPQLibrary.Element;

public final class ElementDump implements DumpModule {

    // 1. Define the CSV schema
    static final CsvSchema SCHEMA = new CsvSchema(
        new CsvColumn("Z", INT, false),
        new CsvColumn("symbol", STRING, false),
        new CsvColumn("name", STRING, false),
        new CsvColumn("atomic_weight", DOUBLE, false)
    );

    @Override
    public String name() {
        return "Element";
    }

    @Override
    public String usage() {
        return "Element Z=<atomic-number>";
    }

    @Override
    public CsvSchema schema() {
        return SCHEMA;
    }

    @Override
    public void run(DumpContext ctx) throws IllegalArgumentException {
        // 2. Parse and validate arguments
        final int Z = ctx.getInt("Z", 1, 118);

        // 3. Fetch reference data
        final Element element = Element.byAtomicNumber(Z);

        // 4. Build and emit CSV row
        CsvRowBuilder rowBuilder = new CsvRowBuilder(SCHEMA);
        rowBuilder
            .set("Z", Z)
            .set("symbol", element.toAbbrev())
            .set("name", element.toString())
            .set("atomic_weight", element.getAtomicWeight());

        ctx.row(rowBuilder.buildRow());
        ctx.flush();
    }
}
```

**Key points**:
- Extend `DumpModule` interface
- Define a `CsvSchema` with `CsvColumn` entries:
  - Column name (lowercase with underscores)
  - Column type (`INT`, `DOUBLE`, `STRING`, `BOOL`)
  - Whether the column is nullable (`true` for optional, `false` for required)
- Implement `name()`: command name for CLI (e.g., "Element")
- Implement `usage()`: human-readable help string
- Implement `schema()`: returns the CSV schema
- Implement `run()`: the logic
  - Parse and validate arguments using `ctx.getInt()`, `ctx.getList()`, etc.
  - Use helper utilities like `DumpUtils.parseElement()` where applicable
  - Use `CsvRowBuilder` to construct rows type-safely
  - Call `ctx.row()` to emit the row
  - Call `ctx.flush()` at the end

**Example with List Arguments and Utilities**:

```java
@Override
public void run(DumpContext ctx) throws IllegalArgumentException {
    // Parse comma-separated lists
    List<String> elementNames = ctx.getList("elements");
    List<String> fractionStrs = ctx.getList("fractions");

    // Parse elements using DumpUtils
    for (String elemName : elementNames) {
        Element elm = DumpUtils.parseElement(elemName);  // Accepts symbol or Z
        if (elm == null) {
            throw new IllegalArgumentException("Unknown element: " + elemName);
        }
    }

    // Handle nullable values
    Double uncertainty = DumpUtils.sigma(uncertainValue);  // null if zero

    // Build row with nullable column
    rowBuilder.set("value", value)
              .set("uncertainty", uncertainty);  // Can be null
}
```

See `DumpCompositionDetail` for a complete working example with list arguments.

#### 2. Register the Module in TestDump

Open `test/java/src/main/java/epq/reference/TestDump.java` and add your module to the `MODULES` stream:

```java
private static final Map<String, DumpModule> MODULES = Stream.of(
        new DumpXRayTransition(),
        new DumpElement(),
        new DumpAtomicShell(),
        new DumpCompositionDetail(),
        new DumpCompositionSummary(),
        new YourNewDumpModule()  // ADD THIS LINE
    // add more here
).collect(Collectors.toMap(DumpModule::name, m -> m));
```

**Current Registered Modules**:
- `DumpXRayTransition` - X-ray transition properties
- `DumpElement` - Element properties and atomic data
- `DumpAtomicShell` - Atomic shell properties
- `DumpCompositionDetail` - Per-element composition properties
- `DumpCompositionSummary` - Aggregate composition properties

#### 3. Compile and Test Locally

```bash
cd test/java
mvn clean compile
```

If there are errors, fix them before proceeding.

#### 4. Test Manually (Single Mode)

```bash
cd test/java
mvn exec:java \
  -Dexec.mainClass=epq.reference.TestDump \
  -Dexec.args="Element Z=26"
```

Expected output:
```csv
Z,symbol,name,atomic_weight
26,Fe,Iron,55.845
```

If it fails:
- Check error message for missing required argument or invalid enum value
- Verify EPQ library has the method you're calling
- Print intermediate values to debug

#### 5. Test Batch Mode

```bash
cd test/java
echo -e "Element Z=26\nElement Z=79" | \
mvn exec:java \
  -Dexec.mainClass=epq.reference.TestDump \
  -Dexec.args="batch"
```

Expected output:
```
#BEGIN dump=Element Z=26
Z,symbol,name,atomic_weight
26,Fe,Iron,55.845
#END
#BEGIN dump=Element Z=79
Z,symbol,name,atomic_weight
79,Au,Gold,196.966569
#END
```

### Common Mistakes

**Mistake**: Schema column order doesn't match usage
```java
// WRONG - columns defined in one order, set in another
static final CsvSchema SCHEMA = new CsvSchema(
    new CsvColumn("name", STRING, false),
    new CsvColumn("Z", INT, false)
);
// ... later in run():
rowBuilder.set("Z", Z).set("name", element.toString());  // OK but confusing

// RIGHT - define columns in logical order (Z first)
static final CsvSchema SCHEMA = new CsvSchema(
    new CsvColumn("Z", INT, false),
    new CsvColumn("name", STRING, false)
);
```

**Mistake**: Wrong nullable flag
```java
// WRONG - marking required data as nullable
new CsvColumn("Z", INT, true)  // Z is always present!

// WRONG - marking optional data as non-nullable
new CsvColumn("ionization_energy", DOUBLE, false)  // May not exist for all elements!

// RIGHT - match nullability to data availability
new CsvColumn("Z", INT, false)  // Always present
new CsvColumn("ionization_energy", DOUBLE, true)  // Optional
```

**Mistake**: Not using typed setters
```java
// WRONG - setting values as strings when schema expects INT
rowBuilder.set("Z", String.valueOf(z));  // Runtime error!

// RIGHT - use values matching the schema type
rowBuilder.set("Z", z);  // INT in schema, int value
rowBuilder.set("atomic_weight", element.getAtomicWeight());  // DOUBLE
```

**Mistake**: Manual argument validation when helper methods exist
```java
// WRONG - manual parsing and validation
String zStr = ctx.get("Z");
int z = Integer.parseInt(zStr);
if (z < 1 || z > 118) {
    throw new IllegalArgumentException("Z out of range");
}

// RIGHT - use ctx.getInt() with range validation
final int Z = ctx.getInt("Z", 1, 118);
```

---

## Recipe: Write a Golden Test

This recipe shows how to write a pytest test that compares your Python implementation against the Java reference.

### Prerequisites

- Python 3.8+
- pytest installed
- `test/epq_dump/conftest.py` exists (the pytest bridge)
- `test/epq_dump/core_models.py` exists (DumpRequest type)
- A corresponding dump module exists in Java (see Recipe 1)

### Validator Reference

All EPQ dump data is validated using Pydantic models in `test.epq_dump.validators`. These models ensure type safety and provide IDE autocompletion for accessing dump data.

#### Available Validators

All validators are registered in `test/epq_dump/validators.py` in the `_MODELS` dictionary.

| Model | Dump Module | Purpose |
|-------|-------------|--------|
| `ElementRow` | `Element` | Element properties and atomic data |
| `XRayTransitionRow` | `XRayTransition` | X-ray transition properties |
| `AtomicShellRow` | `AtomicShell` | Atomic shell properties |
| `CompositionDetailRow` | `CompositionDetail` | Per-element composition data |
| `CompositionSummaryRow` | `CompositionSummary` | Aggregate composition properties |

#### Import and Use

```python
from test.epq_dump.validators import (
    ElementRow,
    XRayTransitionRow,
    AtomicShellRow,
    CompositionDetailRow,
    CompositionSummaryRow,
    validate_table
)

# In your test - the fixture type annotation tells pytest which validator to use
def test_element_data(java_dump: list[ElementRow]):
    # java_dump is automatically validated and typed as list[ElementRow]
    for element in java_dump:
        print(element.Z, element.symbol, element.name)
```

**Note on Nullable Fields**: Fields with `| EmptyStrToNone` type accept `None` values. These correspond to nullable columns in the Java schema where empty strings represent null values.

#### Model Attributes

**ElementRow**:
- `Z: int` - Atomic number
- `symbol: str` - Element symbol (e.g., "H", "Fe")
- `name: str` - Element name (e.g., "Hydrogen", "Iron")
- `atomic_weight: float` - Atomic weight in u
- `mass_in_kg: float` - Atomic mass in kilograms
- `ionization_energy: float | None` - Ionization energy (optional)
- `mean_ionization_potential: float` - Mean ionization potential

**XRayTransitionRow**:
- `Z: int` - Atomic number
- `transition_index: int` - Index of transition
- `transition_name: str` - Transition name (e.g., "K-L2")
- `source_shell: str` - Source shell (e.g., "K")
- `destination_shell: str` - Destination shell (e.g., "L2")
- `family: str` - Family name (e.g., "Ka")
- `is_well_known: bool` - Whether transition is well-known
- `exists: bool | None` - Whether transition exists (optional)
- `energy: float | None` - Transition energy in eV (optional)
- `edge_energy_eV: float | None` - Edge energy in eV (optional)
- `weight_default: float | None` - Default weight (optional)
- `weight_family: float | None` - Family weight (optional)
- `weight_destination: float | None` - Destination weight (optional)
- `weight_klm: float | None` - KLM weight (optional)

**AtomicShellRow**:
- `Z: int` - Atomic number
- `shell_index: int` - Shell index
- `shell_name_siegbahn: str` - Siegbahn notation (e.g., "K", "L1")
- `shell_name_iupac: str` - IUPAC notation
- `shell_name_atomic: str` - Atomic notation
- `family: str` - Shell family
- `principal_quantum_number: int` - Principal quantum number (n)
- `orbital_angular_momentum: int` - Orbital angular momentum (l)
- `total_angular_momentum: float` - Total angular momentum (j)
- `capacity: int` - Maximum electron capacity
- `exists: bool | None` - Whether shell exists for this element (optional)
- `ground_state_occupancy: int | None` - Ground state electron count (optional)
- `edge_energy_ev: float | None` - Binding energy in eV (optional)
- `energy_J: float | None` - Binding energy in Joules (optional)

**CompositionDetailRow** (one row per element in composition):
- `element: str` - Element symbol
- `atomic_number: int` - Atomic number
- `weight_fraction: float` - Mass fraction (unnormalized)
- `weight_fraction_sigma: float | None` - Uncertainty (optional)
- `normalized_weight_fraction: float` - Mass fraction (normalized to sum=1)
- `normalized_weight_fraction_sigma: float | None` - Uncertainty (optional)
- `atomic_percent: float` - Atomic percentage
- `atomic_percent_sigma: float | None` - Uncertainty (optional)
- `atoms_per_kg: float` - Number of atoms per kilogram
- `atoms_per_kg_sigma: float | None` - Uncertainty (optional)
- `stoichiometry: float` - Atomic fraction (stoichiometric coefficient)
- `stoichiometry_sigma: float | None` - Uncertainty (optional)

**CompositionSummaryRow** (single row for entire composition):
- `element_count: int` - Number of elements
- `weight_avg_atomic_number: float` - Weight-averaged atomic number
- `weight_avg_atomic_number_sigma: float | None` - Uncertainty (optional)
- `mean_atomic_number: float` - Mean atomic number
- `mean_atomic_number_sigma: float | None` - Uncertainty (optional)
- `sum_weight_fraction: float` - Sum of all weight fractions
- `sum_weight_fraction_sigma: float | None` - Uncertainty (optional)
- `optimal_representation: str` - Best representation type (STOICHIOMETRY, WEIGHT_PCT, UNDETERMINED)
- `is_uncertain: bool` - Whether composition has uncertainties
- `name: str | None` - Composition name if set (optional)

### Steps

#### 1. Determine Module and Parameters

Decide:
- Which dump module will provide the reference data? (e.g., "Element")
- What parameters does the Python function under test need? (e.g., Z=26)

Example: We're testing a function `get_element_name(z: int) -> str` and we want to verify it against Java.

#### 2. Create Test File

Create `test/epq_dump/test_element.py`:

```python
import pytest
from layers_edx.element import get_element_name  # Your module under test
from test.epq_dump.validators import ElementRow  # Pydantic model


@pytest.mark.epq_ref(module="Element")
@pytest.mark.parametrize("Z", range(1, 119))
def test_element_name(Z: int, java_dump: list[ElementRow]):
    """
    Verify that element names match Java reference.

    The @pytest.mark.epq_ref marker tells pytest to:
    1. Collect this test as a JVM-dependent test
    2. Request data from Java dump module "Element"
    3. Pass parametrized values (Z) as arguments to the Java module

    The java_dump fixture automatically:
    1. Looks up the cached CSV result from Java
    2. Validates it using the ElementRow Pydantic model
    3. Returns a list of validated model instances
    """
    assert len(java_dump) > 0

    # Access Pydantic model attributes directly
    reference_name = java_dump[0].name
    result_name = get_element_name(Z)

    assert result_name == reference_name
```

**Key elements**:
- `@pytest.mark.epq_ref(module="Element")`: Links test to dump module
- `@pytest.mark.parametrize(...)`: Generates multiple test cases
- `java_dump: list[ElementRow]`: Fixture that retrieves validated Pydantic model instances

#### 3. Run the Test

```bash
cd /workspaces/layers-edx

# Run all JVM-dependent tests
pytest -m "epq_ref" test/python/test_element.py -v

# Run one specific test
pytest -m "epq_ref" test/python/test_element.py::test_element_name[26] -v
```

Expected output:
```
test_element.py::test_element_name[1] PASSED
test_element.py::test_element_name[2] PASSED
...
test_element.py::test_element_name[26] PASSED
...
119 passed in 2.34s
```

#### 4. Debug If Tests Fail

If a test fails:

```bash
# Add -s to see print statements
pytest -m "epq_ref" test/python/test_element.py::test_element_name[26] -v -s
```

Inside your test, add debugging:

```python
def test_element_name(Z: int, java_dump: list[ElementRow]):
    print(f"\nDebug: java_dump = {java_dump}")

    assert len(java_dump) > 0
    reference_name = java_dump[0].name  # Pydantic model attribute
    result_name = get_element_name(Z)

    print(f"Reference: {reference_name}, Result: {result_name}")
    assert result_name == reference_name
```

#### 5. Add More Tests

Once the first test passes, add more:

```python
@pytest.mark.epq_ref(module="Element")
@pytest.mark.parametrize("Z", range(1, 119))
def test_element_symbol(Z: int, java_dump: list[ElementRow]):
    """Verify element symbols match Java reference."""
    assert len(java_dump) > 0
    reference_symbol = java_dump[0].symbol
    result_symbol = get_element_symbol(Z)
    assert result_symbol == reference_symbol


@pytest.mark.epq_ref(module="Element")
@pytest.mark.parametrize("Z", range(1, 119))
def test_element_mass(Z: int, java_dump: list[ElementRow]):
    """Verify element masses match Java reference."""
    assert len(java_dump) > 0
    reference_mass = java_dump[0].atomic_mass  # Already a float, no conversion needed
    result_mass = get_element_mass(Z)
    assert result_mass == pytest.approx(reference_mass)
```

All three tests will:
- Share the same Java invocation (batch mode)
- Reuse cached results (no extra JVM startup)

#### 6. Class-Based Tests (Recommended for Multiple Related Tests)

When testing multiple properties of the same object across many parameters, use a **class-based parametrized test**. This approach:
- Avoids repeating boilerplate in each test function
- Uses a shared setup fixture (`autouse=True`)
- Keeps related tests organized in a single class
- Works seamlessly with parametrization

Create `test/epq_dump/test_element.py`:

```python
import pytest
from pytest import approx
from test.epq_dump.validators import ElementRow
from layers_edx.element import Element


@pytest.mark.epq_ref(module="Element")
@pytest.mark.parametrize(
    "Z",
    range(1, 110),
)
class TestElementProperties:
    @pytest.fixture(autouse=True)
    def setup_element(self, Z: int, java_dump: list[ElementRow]):
        """Automatically called before each test method.

        The autouse=True parameter means this fixture runs without being
        explicitly requested by test methods.
        """
        self.element = Element(Z)
        self.ref = java_dump[0]

    def test_atomic_number(self):
        """Verify atomic number matches reference."""
        assert self.ref.Z == self.element.atomic_number

    def test_symbol(self):
        """Verify element symbol matches reference."""
        assert self.ref.symbol == self.element.name

    def test_atomic_weight(self):
        """Verify atomic weight matches reference (with tolerance)."""
        assert self.ref.atomic_weight == approx(self.element.atomic_weight, rel=1e-3)

    def test_mass_in_kg(self):
        """Verify mass in kg matches reference."""
        assert self.ref.mass_in_kg == approx(self.element.mass, rel=1e-3)

    def test_ionization_energy(self):
        """Verify ionization energy matches reference."""
        assert self.ref.ionization_energy == approx(
            self.element.ionization_energy, rel=1e-3
        )
```

**Key features**:

| Feature | Benefit |
|---------|---------|
| Class-level `@pytest.mark.parametrize` | All test methods inherit the parametrization (Z=1 to Z=109) |
| `@pytest.fixture(autouse=True)` on setup method | Initialization happens once per test case, not per method |
| `self.element` and `self.ref` as instance variables | Accessible to all test methods without re-fetching |
| Multiple focused test methods | Each method tests one property clearly |
| `approx()` for floats | Handles floating-point comparison tolerance |

**Run with**:

```bash
# Run all tests in the class (109 × 5 methods = 545 assertions)
pytest -m "epq_ref" test/epq_dump/test_element.py::TestElementProperties -v

# Run specific parametrized case
pytest -m "epq_ref" test/epq_dump/test_element.py::TestElementProperties::test_atomic_number[26] -v

# Run specific test method across all parameters
pytest -m "epq_ref" test/epq_dump/test_element.py::TestElementProperties::test_atomic_weight -v
```

**Expected output** (first 5 of 545 tests):

```
test_element.py::TestElementProperties::test_atomic_number[1] PASSED
test_element.py::TestElementProperties::test_symbol[1] PASSED
test_element.py::TestElementProperties::test_atomic_weight[1] PASSED
test_element.py::TestElementProperties::test_mass_in_kg[1] PASSED
test_element.py::TestElementProperties::test_ionization_energy[1] PASSED
...
545 passed in 3.45s
```

**When to use class-based tests**:
- Multiple related assertions on the same object
- Heavy setup (creating object once, reusing across tests)
- Parametrized across many values (Z=1..109)
- Want clear, focused test methods

**When to use function-based tests**:
- Single assertion per test
- Simple tests with no shared state
- Minimal setup needed

#### 7. Conditional Tests with Optional Reference Data

When reference data contains optional fields that only exist under certain conditions, use a **guard fixture** to skip tests gracefully when the data isn't available.

**Example scenario**: X-ray transitions have theoretical properties (source/destination shells) that always exist, but energy/weight properties only exist when the transition physically exists.

```python
import pytest
from test.epq_dump.validators import XRayTransitionRow
from layers_edx.element import Element
from layers_edx.xrt import XRayTransition
from layers_edx.atomic_shell import AtomicShell


@pytest.mark.epq_ref(module="XRayTransition")
@pytest.mark.parametrize(
    "Z, trans",
    [(26, 1), (79, 5), (6, 2)],  # Various elements and transitions
)
class TestXRayTransitionProperties:
    @pytest.fixture(autouse=True)
    def setup_transition(self, Z: int, trans: int, java_dump: list[XRayTransitionRow]):
        """Setup fixture - runs for all tests (no skipping here)."""
        self.xrt = XRayTransition(Element(Z), trans)
        self.ref = java_dump[0]

    @pytest.fixture
    def require_exists(self):
        """Guard fixture: skip if the transition isn't physically valid."""
        if not self.xrt.exists:
            pytest.skip(f"Transition {self.xrt} does not exist.")

    def test_source_shell(self):
        """Verify source shell (always available)."""
        assert self.ref.source_shell == self.xrt.source.name

    def test_destination_shell(self):
        """Verify destination shell (always available)."""
        assert self.ref.destination_shell == self.xrt.destination.name

    def test_family(self):
        """Verify family (always available)."""
        assert self.ref.family == AtomicShell.FAMILY[self.xrt.family]

    def test_exists(self):
        """Verify existence flag (always available)."""
        assert self.ref.exists == self.xrt.exists

    def test_energy_eV(self, require_exists: None):
        """Verify energy (only for transitions that exist)."""
        assert self.ref.energy_eV == pytest.approx(self.xrt.energy, rel=1e-3)

    def test_weight(self, require_exists: None):
        """Verify weight (only for transitions that exist)."""
        assert self.ref.weight_default == pytest.approx(self.xrt.weight, rel=1e-3)
```

**How the guard fixture works**:

1. Define a fixture (not `autouse=True`) that checks a condition
2. If condition fails, call `pytest.skip()` with a descriptive message
3. Request the fixture in test methods that need the guard
4. Tests without the fixture parameter run always
5. Tests with the fixture parameter run only if condition passes

**Output when transition doesn't exist**:

```
test_xrt.py::TestXRayTransitionProperties::test_source_shell[26-1] PASSED
test_xrt.py::TestXRayTransitionProperties::test_destination_shell[26-1] PASSED
test_xrt.py::TestXRayTransitionProperties::test_family[26-1] PASSED
test_xrt.py::TestXRayTransitionProperties::test_exists[26-1] PASSED
test_xrt.py::TestXRayTransitionProperties::test_energy_eV[26-1] SKIPPED (Transition does not exist)
test_xrt.py::TestXRayTransitionProperties::test_weight[26-1] SKIPPED (Transition does not exist)
```

**Output when transition exists**:

```
test_xrt.py::TestXRayTransitionProperties::test_source_shell[79-5] PASSED
test_xrt.py::TestXRayTransitionProperties::test_destination_shell[79-5] PASSED
test_xrt.py::TestXRayTransitionProperties::test_family[79-5] PASSED
test_xrt.py::TestXRayTransitionProperties::test_exists[79-5] PASSED
test_xrt.py::TestXRayTransitionProperties::test_energy_eV[79-5] PASSED
test_xrt.py::TestXRayTransitionProperties::test_weight[79-5] PASSED
```

**Benefits**:
- Explicit skip status (visible in test reports)
- Tests structural properties always
- Skips optional property tests cleanly
- Reusable across multiple test methods
- No external dependencies (pure pytest)
- Self-documenting (clear intent from fixture name)

**Multiple guard conditions**:

You can create multiple guard fixtures for different conditions:

```python
@pytest.fixture
def require_exists(self):
    if not self.xrt.exists:
        pytest.skip("Transition does not exist.")

@pytest.fixture
def require_well_known(self):
    if self.xrt.transition is None:
        pytest.skip("Transition is not well-known.")

def test_energy_eV(self, require_exists: None):
    # Only runs if transition exists
    assert self.ref.energy_eV == pytest.approx(self.xrt.energy, rel=1e-3)

def test_iupac_name(self, require_well_known: None):
    # Only runs if transition is well-known
    assert self.xrt.iupac_name == self.ref.iupac_name
```

### Common Mistakes

**Mistake**: Test lacks `@pytest.mark.epq_ref`
```python
# WRONG - java_dump fixture will raise ValueError
def test_something(java_dump):
    pass

# RIGHT
@pytest.mark.epq_ref(module="SomeModule")
def test_something(java_dump):
    pass
```

**Mistake**: Fixture type hint is wrong
```python
# WRONG - incorrect type hint
def test_something(java_dump: pd.DataFrame):
    pass

# RIGHT - use appropriate Pydantic model
from test.epq_dump.validators import ElementRow

def test_something(java_dump: list[ElementRow]):
    pass
```

**Mistake**: Using dictionary access instead of model attributes
```python
# WRONG - treating Pydantic model like a dict
reference_mass = java_dump[0]["AtomicMass"]

# RIGHT - access Pydantic model attributes directly
reference_mass = java_dump[0].atomic_mass
```

**Mistake**: Float comparison without epsilon
```python
# WRONG - floating-point rounding causes spurious failures
assert result_mass == reference_mass

# RIGHT - use pytest.approx or numpy.testing.assert_approx_equal
assert result_mass == pytest.approx(reference_mass)

# Or with tolerance
assert result_mass == pytest.approx(reference_mass, rel=1e-9)
```

---

## Recipe: Debug a Failing Test

This recipe helps identify and fix issues in a failing golden test.

### Scenario

Test `test_element_name[26]` fails with:
```
AssertionError: assert 'Fe' == 'Iron'
```

### Steps

#### 1. Verify the Dump Module Works

```bash
cd test/java
mvn exec:java \
  -Dexec.mainClass=epq.reference.TestDump \
  -Dexec.args="Element Z=26"
```

Output:
```csv
AtomicNumber,Name,Symbol,AtomicMass
26,Iron,Fe,5.587000000000e+01
```

**What we learned**: Java correctly returns "Iron" and "Fe".

#### 2. Print the Fixture Data

Modify the test temporarily:

```python
@pytest.mark.epq_ref(module="Element")
@pytest.mark.parametrize("Z", [26])
def test_element_name(Z: int, java_dump: list[ElementRow]):
    print(f"\nFull java_dump: {java_dump}")
    print(f"First row: {java_dump[0] if java_dump else 'EMPTY'}")

    assert len(java_dump) > 0
    reference_name = java_dump[0].name  # Pydantic model attribute
    result_name = get_element_name(Z)

    print(f"Reference: '{reference_name}' (type: {type(reference_name)})")
    print(f"Result: '{result_name}' (type: {type(result_name)})")

    assert result_name == reference_name
```

Run with `-s` to see output:

```bash
pytest -m "epq_ref" test/python/test_element.py::test_element_name[26] -v -s
```

Output:
```
Full java_dump: [ElementRow(atomic_number=26, name='Iron', symbol='Fe', atomic_mass=55.87)]
First row: ElementRow(atomic_number=26, name='Iron', symbol='Fe', atomic_mass=55.87)
Reference: 'Iron' (type: <class 'str'>)
Result: 'Fe' (type: <class 'str'>)
```

**What we learned**: Your `get_element_name()` function is returning the symbol ("Fe") instead of the name ("Iron"). The bug is in your implementation, not the test framework.

#### 3. Fix the Implementation

```python
# WRONG implementation
def get_element_name(z: int) -> str:
    element = Element.byAtomicNumber(z)
    return element.toAbbrev()  # Returns symbol, not name!

# CORRECT implementation
def get_element_name(z: int) -> str:
    element = Element.byAtomicNumber(z)
    return element.getName()  # Returns name
```

#### 4. Re-run the Test

```bash
pytest -m "epq_ref" test/python/test_element.py::test_element_name[26] -v -s
```

Output:
```
test_element.py::test_element_name[26] PASSED
```

### Debug Checklist

- [ ] Dump module works in single mode?
- [ ] Dump module works in batch mode?
- [ ] Java dump returns the expected CSV structure?
- [ ] Test fixture receives the data correctly?
- [ ] Expected column names match what Java emits?
- [ ] String-to-number conversions are correct?
- [ ] Float comparisons use `pytest.approx()`?

---

## Recipe: Troubleshoot Java Invocation Failures

### Symptom: Collection Fails

```
ERROR collecting test_element.py
RuntimeError: Java process failed with exit code 1
Stderr:
Error: Unknown dump module: ElementDump
Usage: TestDump <module> [key=value ...] or TestDump batch
```

### Diagnosis and Fix

1. Check that the module is registered in `TestDump.getDumpModules()`:

```bash
grep -n "Element" test/java/src/main/java/epq/reference/TestDump.java
```

If it's not there, add it (see Recipe 1, step 2).

2. Recompile:

```bash
cd test/java
mvn clean compile
```

3. Test manually:

```bash
cd test/java
mvn exec:java \
  -Dexec.mainClass=epq.reference.TestDump \
  -Dexec.args="Element Z=26"
```

---

### Symptom: Maven Not Found

```
FileNotFoundError: [Errno 2] No such file or directory: 'mvn'
```

### Diagnosis and Fix

Maven is not in PATH. Install it or add it to PATH:

```bash
which mvn
# If not found:
apt-get install maven

# Or add to PATH:
export PATH="/opt/maven/bin:$PATH"
```

---

### Symptom: EPQ Library Not Found

```
Error: Unable to find epq library in classpath
```

### Diagnosis and Fix

1. Check `pom.xml` has the EPQ dependency:

```bash
grep -A 5 "<dependency>" test/java/pom.xml | grep -i epq
```

2. Download dependencies:

```bash
cd test/java
mvn dependency:resolve
```

3. Try again.

---

### Symptom: Validator KeyError

```
KeyError: 'No pydantic model registered for dump module: CompositionDetail'
```

### Diagnosis and Fix

The Pydantic validator model is not registered in `test/epq_dump/validators.py`.

**Fix**:

1. Check if the model class exists:

```bash
grep "class CompositionDetailRow" test/epq_dump/validators.py
```

2. If the class exists but isn't registered, add it to `_MODELS` dictionary:

```python
_MODELS: Dict[str, Type[BaseModel]] = {
    "Element": ElementRow,
    "XRayTransition": XRayTransitionRow,
    "AtomicShell": AtomicShellRow,
    "CompositionDetail": CompositionDetailRow,  # ADD THIS
    "CompositionSummary": CompositionSummaryRow,
}
```

3. If the class doesn't exist, create it following the pattern of existing models.

---

### Symptom: Pydantic ValidationError on Nullable Field

```
pydantic.ValidationError: 1 validation error for ElementRow
ionization_energy
  Input should be a valid number [type=float_type, input_value='', input_type=str]
```

### Diagnosis and Fix

The Python model doesn't accept `None` but the Java CSV can return empty strings (representing null).

**Fix**: Use `EmptyStrToNone` type annotation for nullable fields:

```python
from test.epq_dump.validators import EmptyStrToNone

class ElementRow(BaseModel):
    Z: int
    ionization_energy: float | EmptyStrToNone  # Changed from: ionization_energy: float
```

This matches the Java schema where the column is marked nullable:

```java
new CsvColumn("ionization_energy", DOUBLE, true)  // nullable=true
```

---

### Symptom: CSV Parsing Fails with Quoted Field

```
csv.Error: field larger than field limit (131072)
```

### Diagnosis and Fix

This is unlikely but could occur if a field contains very large text. The `CsvWriter` automatically handles RFC 4180 escaping for:
- Fields with commas
- Fields with quotes (doubled)
- Fields with newlines

Check the Java stacktrace for the actual error. If the data is legitimately large, this may indicate a bug in the dump module (e.g., accidentally including large binary data).

**Debug**:

```bash
# Run the dump module directly to inspect output
cd test/java
mvn exec:java -Dexec.mainClass=epq.reference.TestDump -Dexec.args="ModuleName arg=value" | head -20
```

---

## Recipe: Test Compositions with List Arguments

This recipe shows how to test dump modules that accept comma-separated list arguments (e.g., compositions).

### Prerequisites

- Java dump modules `CompositionDetail` and/or `CompositionSummary` exist
- Corresponding Pydantic validators exist
- You understand the basics of golden testing (see Recipe 2)

### Pattern: Small Default Set, Large with FULL_SUITE

For composition testing, use a pattern that provides fast feedback during development but comprehensive coverage in CI:

```python
import os
from test.epq_dump.conftest import FULL_SUITE

def get_params():
    """Get test parameters based on FULL_SUITE environment variable."""
    if FULL_SUITE:
        # Comprehensive testing: 500 random compositions
        return generate_random_compositions(count=500, seed=42)

    # Fast feedback: Small hand-picked test set
    return [
        ("Fe", "1.0"),                    # Pure element
        ("Fe,O", "0.72,0.28"),            # Binary: Iron oxide
        ("Si,Al,O", "0.28,0.10,0.62"),    # Ternary: Feldspar
    ]

@pytest.mark.epq_ref(module="CompositionDetail")
@pytest.mark.parametrize("elements,fractions", get_params())
def test_composition(elements: str, fractions: str, java_dump: list[CompositionDetailRow]):
    # Test logic here
    pass
```

**Run in fast mode** (default):
```bash
pytest test/epq_dump/test_composition.py -v
# Runs 3 tests
```

**Run in comprehensive mode**:
```bash
PYTEST_FULL_SUITE=true pytest test/epq_dump/test_composition.py -v
# Runs 500 tests
```

### Complete Example: test_composition.py

```python
import pytest
from test.epq_dump.validators import CompositionDetailRow
from test.epq_dump.conftest import FULL_SUITE
from layers_edx.composition import Composition

def get_params():
    if FULL_SUITE:
        # Generate many random test cases
        import random
        random.seed(42)
        cases = []
        for _ in range(100):
            num_elements = random.randint(2, 4)
            elements = random.sample(["Fe", "O", "Si", "Al", "Ca", "Mg"], num_elements)
            fractions = [random.uniform(0.1, 0.9) for _ in elements]
            # Normalize
            total = sum(fractions)
            fractions = [f/total for f in fractions]

            elem_str = ",".join(elements)
            frac_str = ",".join(f"{f:.4f}" for f in fractions)
            cases.append((elem_str, frac_str))
        return cases

    # Default: small focused test set
    return [
        ("Fe", "1.0"),
        ("Fe,O", "0.72,0.28"),
        ("Si,Al,O", "0.28,0.10,0.62"),
    ]

@pytest.mark.epq_ref(module="CompositionDetail")
@pytest.mark.parametrize("elements,fractions", get_params())
def test_weight_fractions(elements: str, fractions: str, java_dump: list[CompositionDetailRow]):
    """Verify weight fractions match Java reference."""
    # Parse input
    elem_list = elements.split(",")
    frac_list = [float(f) for f in fractions.split(",")]

    # Create Python composition
    py_comp = Composition.from_mass_fractions(
        dict(zip(elem_list, frac_list))
    )

    # Compare each element
    assert len(java_dump) == len(elem_list)
    for row in java_dump:
        py_frac = py_comp.get_weight_fraction(row.element)
        assert py_frac == pytest.approx(row.weight_fraction, rel=1e-9)
```

**See Also**: `test/epq_dump/test_composition.py` for complete working examples with the `generate_random_compositions()` helper function.

---

## Recipe: Run Tests Without JVM

Sometimes you want to test your Python implementation without invoking Java (e.g., during rapid iteration).

### Option 1: Use a Different Marker

```python
@pytest.mark.skip_java  # Use a different marker
@pytest.mark.parametrize("Z", [26, 79])
def test_element_fast(Z: int):
    """Unit test that doesn't need Java."""
    result = get_element_name(Z)
    assert result is not None
    assert isinstance(result, str)
```

Run with:
```bash
pytest -m "skip_java" test/python/
```

### Option 2: Skip JVM-Dependent Tests

```bash
# Skip all @pytest.mark.epq_ref tests
pytest -m "not epq_ref" test/python/
```

### Option 3: Use Mock Data

```python
import pytest
from unittest.mock import patch

@pytest.mark.parametrize("Z, expected_name", [
    (26, "Iron"),
    (79, "Gold"),
])
def test_element_mock(Z: int, expected_name: str):
    """Test with mocked data (no Java)."""
    with patch("layers_edx.element.get_element_name") as mock_fn:
        mock_fn.return_value = expected_name
        result = mock_fn(Z)
        assert result == expected_name
```

Run with:
```bash
pytest test/python/test_element.py::test_element_mock -v
```

---

## Summary

| Task | Recipe |
|------|--------|
| Add a new dump module | Recipe 1 |
| Write a golden test | Recipe 2 |
| Debug a failing test | Recipe 3 |
| Fix Java invocation issues | Recipe 4 |
| Test compositions with list arguments | Recipe 5 (new) |
| Run tests without JVM | Recipe 6 |

## See Also

- [COMPOSITION_TESTING_GUIDE.md](COMPOSITION_TESTING_GUIDE.md) - Comprehensive guide to composition testing
- [JAVA_ORACLE_GUIDE.md](JAVA_ORACLE_GUIDE.md) - Complete Java API reference
- [PYTEST_BRIDGE_GUIDE.md](PYTEST_BRIDGE_GUIDE.md) - Pytest integration details
- [TESTING_ARCHITECTURE.md](TESTING_ARCHITECTURE.md) - Design principles and architecture
