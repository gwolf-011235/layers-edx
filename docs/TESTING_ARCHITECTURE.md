# Testing Architecture

This document covers the design principles, three-phase execution model, and the CSV contract that bridges Java and Python.

## Design Principles

### Why Golden Testing?

The approach treats Java as the authoritative reference. Python tests verify that the port produces identical results for the same inputs. This provides:

- **Correctness by construction**: Any discrepancy is caught immediately
- **Confidence during refactoring**: Behavioral changes are visible
- **Language-agnostic validation**: Porting errors are detected, not implementation bugs


### Determinism and Reproducibility

All components enforce deterministic behavior:

- Argument order is preserved (not sorted)
- CSV output uses fixed column order
- Floating-point formatting is locale-independent (`Locale.ROOT`)
- Scientific notation: `"%.12e"` for all floats
- Duplicate arguments are rejected

This ensures that the same test produces identical results across runs, making diffs meaningful and results cacheable.

## Three-Phase Execution Model

### Phase 1: Collection (Python)

**When**: During pytest collection (before any tests run)

**What happens**:
1. Pytest discovers all test functions marked with `@pytest.mark.epq_ref`
2. The `pytest_collection_modifyitems` hook (in `conftest.py`) extracts `DumpRequest` objects from each test's marker and arguments from parametrize decorators
3. All unique requests are deduplicated and accumulated

**Why**: By collecting all requests upfront, we can batch them and minimize JVM startup cost.

### Phase 2: Execution (Java)

**When**: Before any tests execute

**What happens**:
1. Pytest launches CLI program *Testdump*
2. All collected `DumpRequest` objects are converted to **batch mode** format (one request per line)
3. Requests are written to `stdin` of the Java process
4. The Java process parses each request, dispatches to the appropriate `DumpModule`, and emits *framed* CSV output
5. All output is captured and parsed into a global cache (`JAVA_ORACLE_DATA`)


### Phase 3: Verification (Python)

**When**: As tests execute

**What happens**:
1. Each test function receives the `java_dump` fixture
2. The fixture retrieves the pre-computed CSV results from the global cache
3. CSV rows are validated against **Pydantic models** (e.g., `XRayTransitionRow`, `ElementRow`) to ensure correct types and schema compliance
4. The test verifies its specific assertions against the reference data

**Why**: Tests run fast because all JVM interactions are batched and cached.

## Batching and JVM Startup Optimization

### Minimizing JVM Costs

Starting the JVM is expensive (typically 1-2 seconds). To avoid this overhead:

1. **Single JVM instance**: All requests are sent to one Java process
2. **Batch mode**: Requests are collected during pytest collection phase
3. **Deduplication**: Identical requests are cached and reused

### Canonicalization and Deduplication

`DumpRequest` automatically sorts arguments by key name. This ensures:
- `(Z=26, trans=1)` and `(trans=1, Z=26)` map to the same request
- Only one Java call is made for both cases
- Requests are deterministic and cacheable

This deduplication means that 1000 test cases might only need 50-100 unique Java calls, dramatically reducing total execution time.

## CSV as the Wire Format

### Why CSV?

CSV is the contract between Java and Python. It was chosen because:

- **Stable**: Schema is made explicit
- **Human-readable**: Can be inspected manually for debugging
- **Easy to parse**: Python has robust CSVReader()

### CSV Guarantees

1. **Fixed column order**: Determined by the `DumpModule` at emission time
2. **Locale independence**: Uses `Locale.ROOT` for formatting (decimal point, not comma)
3. **Scientific notation**: Floating-point numbers use `"%.12e"` format (12 decimal places)
4. **Header row**: First row names all columns
5. **RFC 4180 compliance**: Fields with commas, quotes, or newlines are properly escaped
6. **Null representation**: `null` values serialize as empty strings

### Floating-Point Format

All `DOUBLE` type columns use scientific notation with 12 decimal places:

```java
String.format(Locale.ROOT, "%.12e", value)
```

**Example output**:
```csv
Z,energy_eV,atomic_weight
26,6.403900000000e+03,5.584500000000e+01
```

**Why 12 decimal places?**

12 decimal places provides sufficient precision for all physical constants and measurements in EPQ:
- Energy values: typically 1-100 keV (requires ~6-7 significant figures)
- Mass values: atomic weights (requires ~10 significant figures)
- IEEE 754 double precision: ~15-17 decimal digits
- 12 decimal places in scientific notation preserves full precision while remaining human-readable

**Locale independence**:

Using `Locale.ROOT` ensures:
- Decimal point (`.`) not comma (`,`) regardless of system locale
- Consistent parsing across different regional settings
- Reproducible output on all systems

### Null Handling

Null values in Java are represented as **empty strings** in CSV output.

**Java side** - Nullable columns:
```java
// Schema definition
static final CsvSchema SCHEMA = new CsvSchema(
    new CsvColumn("Z", INT, false),                  // Required
    new CsvColumn("ionization_energy", DOUBLE, true) // Nullable
);

// Setting null value
Double ionizationEnergy = null;  // Not available
rowBuilder.set("ionization_energy", ionizationEnergy);

// CSV output: Z,ionization_energy\n26,\n
// Empty string represents null
```

**Python side** - Pydantic validation:
```python
from test.epq_dump.validators import EmptyStrToNone

class ElementRow(BaseModel):
    Z: int
    ionization_energy: float | EmptyStrToNone  # Accepts None
```

**The `EmptyStrToNone` type**:

```python
def _empty_str_to_none(v: str | None) -> str | None:
    if v is None or v == "":
        return None
    raise ValueError("Value is not empty")

EmptyStrToNone: TypeAlias = Annotated[None, BeforeValidator(_empty_str_to_none)]
```

This type annotation converts empty strings to `None` during Pydantic validation.

**Design rationale**:

1. **CSV simplicity**: No special null marker needed (e.g., `NULL`, `N/A`)
2. **Standard compliance**: Empty fields are standard CSV practice
3. **Type safety**: Pydantic enforces correct null handling on Python side
4. **Java utility**: `DumpUtils.sigma()` returns `null` for zero uncertainties, producing clean CSV

### Example

```csv
Z,Energy,TransitionName
26,6403.9,KA1
26,5889.8,KA2
79,91600.5,LA1
```

### Schema Validation

The CSV schema is enforced on both sides:

**Java side (emission)**:
- Each `DumpModule` defines its output schema using `CsvSchema`, `CsvColumn`, and `CsvRowBuilder`
- Schema declares column names, types, and order
- `CsvRowBuilder` enforces type-safe row construction
- Column order is fixed and deterministic
- Type formatting is consistent (e.g., floats always use scientific notation)

**Python side (validation)**:
- Pydantic models (e.g., `XRayTransitionRow`, `ElementRow`) define expected schema
- Each CSV row is parsed and validated against its corresponding model
- Type mismatches, missing fields, or unexpected columns raise validation errors
- This ensures Java and Python stay synchronized

See individual test files for module-specific Pydantic models.

## Batch Mode Protocol

This section specifies the technical protocol for how Python communicates with the Java TestDump program. In batch mode, multiple requests are sent to a single Java process via stdin, and responses are returned as framed CSV blocks on stdout.

### Protocol Overview

- **Transport**: stdin/stdout pipes
- **Input format**: One request per line (text)
- **Output format**: Framed CSV blocks with `#BEGIN`/`#END` markers
- **Execution**: Single JVM instance handles all requests sequentially

### Input Format (stdin)

One request per line:

```
<module-name> [key=value] ...
```

Example:
```
XRayTransition Z=26 trans=1
XRayTransition Z=79 trans=2
Element Z=6
```

### Output Format (stdout)

Each response is framed with markers:

```
#BEGIN dump=<request-line>
<csv-header>
<csv-row-1>
<csv-row-2>
...
#END

#BEGIN dump=<next-request-line>
...
```

### Frame Parsing

Python parses frames by:
1. Reading lines until `#BEGIN dump=...` is found
2. Extracting the request (after `dump=`)
3. Collecting CSV lines until `#END` is found
4. Parsing CSV lines into a list of dictionaries
5. Caching the result keyed by `DumpRequest`

### Invocation Command

```bash
mvn exec:java -Dexec.mainClass=epq.reference.TestDump -Dexec.args="batch"
```

## Error Handling and Propagation

### Error Flow

```
DumpModule.run(ctx)
    ↓
    ├─ Syntax Error (argument parsing)
    │   → DumpContext throws IllegalArgumentException
    │   → TestDump catches, prints error message and usage
    │   → Exit code 1
    │
    └─ Semantic Error (validation failure)
        → DumpModule throws IllegalArgumentException
        → TestDump catches, prints error message and module usage
        → Exit code 1
```

### User-Facing Errors

All user errors are handled centrally by `TestDump`:
- Unknown dump module name
- Missing required arguments
- Argument parsing errors (malformed key=value)
- Semantic validation failures (invalid enum value, out-of-range Z)

**Behavior**:
- Print error message (no stack trace)
- Print module usage
- Exit with code 1

### No Java Stack Traces

For user errors, no Java exception stack trace is emitted. The error message is human-readable and actionable.

For infrastructure errors (e.g., Maven not found, IO exceptions), stderr will contain the actual Java exception.


## Future Extensions

- **Configuration**: Per-module allowed-argument validation
- **Output formats**: JSON or metadata support
- **Performance**: Optional caching to disk between test runs
