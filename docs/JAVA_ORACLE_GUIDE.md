# Java Oracle Guide

This document is a complete reference for the Java components that implement the CLI program which acts as reference oracle.

## Overview

All Java reference dumps are accessed via a **single CLI entry point**:

```bash
mvn exec:java \
  -Dexec.mainClass=epq.reference.TestDump \
  -Dexec.args="<command> [args...]"
```

Each dump module interprets its own arguments, emits exactly one CSV table, and contains no shared domain logic.

## Environment Setup

Before using the Java oracle, you must set up the EPQ Java library. This section covers configuration and installation using the scripts provided in the `scripts/` directory.

### Quick Start

Use the Python setup script (recommended):

```bash
python scripts/setup_epq.py
```

This script will:
1. Read the EPQ version from `epq_config.py`
2. Generate `pom.xml` from `pom.template` with the correct version for EPQ
3. Update `test/java/pom.xml` with the same version for the CLI program
4. Compile the EPQ library
5. Install it to your local Maven repository (~/.m2/repository)
6. Compile the CLI program

**Note on test/java/pom.xml**

The `test/java/pom.xml` file is tracked in git with a `NUMBER_VERSION` placeholder. Local changes can be ignored using

```bash
git update-index --skip-worktree test/java/pom.xml
```

This allows the setup script to update it with the actual version without affecting git status.

**Note on generated/modified files in submodule**

The script and Java build tooling (Maven, IDEs) will modify and create various project files in `.epq-reference/` which are not in .gitignore:

- `pom.xml` (generated from `pom.template` by setup script)
- Eclipse project files (`.classpath`, `.project`, `.settings/*`)

Since `.epq-reference/` is a git submodule pointing to the upstream EPQ repository, these local modifications will appear in `git status`. You can safely ignore them. Use git's submodule ignore feature (recommended):

```bash
git config submodule..epq-reference.ignore dirty
```

This tells git to ignore untracked and modified files within the submodule. Verify with `git status`.

**VS Code Limitation**

VS Code will still show submodule changes in its Source Control view and badge count. This is a [known limitation since 2020](https://github.com/microsoft/vscode/issues/95822). While you can filter out submodule files in the Source Control panel (they won't be listed individually), the badge number on the Source Control icon will still include them.

Workaround: disable auto-submodule detection and auto repository detection in settings. However this disables tracking of all submodules

```JSON
{
  "git.detectSubmodules": false,
  "git.autoRepositoryDetection": "openEditors",

}
```

### Prerequisites

- **Java 21 or higher**
- **Maven 3.6 or higher**
- **EPQ repository** submodule in `.epq-reference/`

### Version number

EPQ version management is centralized in `scripts/epq_config.py`. This file stores the EPQ version number as a single source of truth.

To update the EPQ version used throughout the project:

1. Edit `scripts/epq_config.py` and change the `EPQ_VERSION` value
2. Run `python scripts/setup_epq.py` to regenerate pom.xml files and reinstall

This ensures the version is consistent across:
- `.epq-reference/pom.xml` (EPQ library itself)
- `test/java/pom.xml` (test code that depends on EPQ)

### Manual Setup Steps

If you need to perform individual steps manually:

**Generate pom.xml from template:**

```bash
cd .epq-reference
sed "s/NUMBER_VERSION/15.1.43/g" pom.template > pom.xml
```

**Compile EPQ:**

```bash
cd .epq-reference
mvn compile
```

**Install EPQ to local Maven repository:**

```bash
cd .epq-reference
mvn install
```

This installs the EPQ JAR to `~/.m2/repository/gov/nist/microanalysis/epq/` where it can be used as a dependency by other Maven projects.

### Troubleshooting

**Java version mismatch:**

EPQ requires Java 21 or higher. Check your Java version:

```bash
java -version
```

**Maven not found:**

Install Maven from https://maven.apache.org/download.cgi

**EPQ repository not found:**

Make sure the EPQ repository is cloned to `.epq-reference/`:

```bash
git submodule update --init
```

**Compilation errors:**

Make sure you're using Java 21 or higher and that the pom.xml has been generated.

**Git showing changes to test/java/pom.xml:**

If you need to re-enable git tracking of local changes:

```bash
git update-index --no-skip-worktree test/java/pom.xml
```

To ignore local changes again:

```bash
git update-index --skip-worktree test/java/pom.xml
```

## TestDump

`TestDump` is the **single Java entry point** for all golden-test dumps. Located at `test/java/src/main/java/epq/reference/TestDump.java`.

### Responsibilities

- Acts as a CLI dispatcher
- Routes requests to the appropriate `DumpModule`
- Handles single vs batch execution modes
- Owns all process-exit behavior
- Prints usage and error messages
- Emits framing markers in batch mode

### Invocation Modes

#### Single Mode (Human-Facing)

```bash
mvn exec:java -Dexec.mainClass=epq.reference.TestDump -Dexec.args="XRayTransition Z=26 trans=1"
```

**Output**: Raw CSV only (no framing markers)

```csv
Energy,EdgeEnergy,OccupancyNumber
6403.9,123.4,2
```

**Use case**: Debugging, manual inspection, shell scripting

#### Batch Mode (Machine-Facing)

```bash
mvn exec:java -Dexec.mainClass=epq.reference.TestDump -Dexec.args="batch"
```

**Input**: `stdin`, one request per line

```
XRayTransition Z=26 trans=1
EdgeEnergy Z=79
```

**Output**: Framed CSV blocks (see [TESTING_ARCHITECTURE.md](TESTING_ARCHITECTURE.md) for format)

```
#BEGIN dump=XRayTransition Z=26 trans=1
Energy,EdgeEnergy,OccupancyNumber
6403.9,123.4,2
#END

#BEGIN dump=Element Z=79
Energy
91600.5
#END
```

**Use case**: Pytest integration, batch processing

## DumpContext

`DumpContext` represents the **execution context for a single dump invocation**. Located at `test/java/src/main/java/epq/reference/DumpContext.java`.

It is deliberately small and generic. Think of it as a "request container" with argument parsing and CSV output helpers.

### Responsibilities

- Parse `key=value` arguments from the command line
- Preserve deterministic argument order
- Provide argument accessors (required and optional)
- Own CSV output helper CsvWriter

### Argument Parsing

Arguments must be of the form `key=value`.

**Validation**:
- Arguments must match pattern `key=value`
- Duplicate keys are rejected
- Syntax errors result in `IllegalArgumentException`

### Argument Access

`DumpContext` provides an API for accessing command-line arguments with built-in validation.

#### API Reference

| Method | Description |
|--------|-------------|
| `String get(String key)` | Get required string argument; throws if missing |
| `String getOrDefault(String key, String default)` | Get optional string argument with default value |
| `int getInt(String key)` | Parse required integer argument; throws if missing or invalid |
| `int getInt(String key, int min, int max)` | Parse and validate integer within range [min, max] |
| `List<String> getList(String key)` | Parse comma-separated list; each element trimmed |
| `Map<String, String> args()` | Get read-only view of all arguments in insertion order |

#### Examples

```java
// Required argument - throws if not present
String z = ctx.get("Z");

// Optional argument with default
String trans = ctx.getOrDefault("trans", "1");

// Required integer argument
int z_int = ctx.getInt("Z");

// Required integer argument with range validation
int z_validated = ctx.getInt("Z", 1, 118);  // min=1, max=118; throws if out of range

// Comma-separated list
List<String> elements = ctx.getList("elements");  // "Fe,O,Si" → ["Fe", "O", "Si"]

// Read-only view of all arguments
Map<String, String> args = ctx.args();
```

### CSV Output

`DumpContext` exposes an instance of `CsvWriter` through methods `header()`, `row()` and `flush()`.

## DumpUtils

`DumpUtils` provides **shared utility methods** used across multiple dump modules. Located at `test/java/src/main/java/epq/reference/DumpUtils.java`.

### API Reference

#### parseElement(String input)

Parse an element from either a symbol or atomic number string.

```java
public static Element parseElement(String input)
```

**Accepts**:
- Element symbols: `"Fe"`, `"Au"`, `"Si"`
- Atomic numbers as strings: `"26"`, `"79"`, `"14"`

**Returns**: `Element` object, or `null` if not found

#### sigma(UncertainValue2 uv)

Extract uncertainty (sigma) from EPQ's `UncertainValue2`, returning `null` if zero or unavailable.

```java
public static Double sigma(UncertainValue2 uv)
```

**Purpose**: Convert zero uncertainties to `null` for cleaner CSV output (empty cell instead of `0.000000000000e+00`)

**Returns**: `Double` with uncertainty value, or `null` if uncertainty is zero

## Deterministic CSV Output: Four-Class Design

Four coordinated classes ensure deterministic CSV output: `CsvColumn`, `CsvSchema`, `CsvRowBuilder`, and `CsvWriter`. Located in `test/java/src/main/java/epq/reference/`.

### Architecture Overview

```
CsvColumn → CsvSchema → CsvRowBuilder → CsvWriter
```

Each class enforces a specific invariant:

1. **CsvColumn** - Defines column metadata
2. **CsvSchema** - Immutable column collection with deterministic order
3. **CsvRowBuilder** - Type-safe, order-enforcing row construction
4. **CsvWriter** - Serialization and output

### CsvColumn

Immutable record storing metadata for a single column.

**Responsibilities**:
- Define column name, type, and nullability
- Enable compile-time type safety in row building

### CsvSchema

Immutable record holding an ordered list of columns.

**Responsibilities**:
- Enforce fixed column order via immutable `List.copyOf()`
- Provide deterministic header generation
- Define the contract for all rows

### CsvRowBuilder

Stateful builder that enforces schema compliance during row construction.

**Responsibilities**:
- Validate column names against schema (throw `IllegalArgumentException` if unknown)
- Enforce type safety: `set()` accepts `Object`; `buildRow()` serializes by column type
- Check nullability constraints
- **Key invariant**: `buildRow()` outputs columns in schema order, not insertion order
- Serialize values using locale-independent formatting

**Complete Example**:

```java
CsvRowBuilder builder = new CsvRowBuilder(schema);
builder.set("Z", 26)                    // INT
       .set("Energy", 6403.9)            // DOUBLE
       .set("OccupancyNumber", 2);       // INT
String[] row = builder.buildRow();       // Order matches schema, not insertion order
```

**Null Handling**:

```java
// Schema with nullable column
static final CsvSchema SCHEMA = new CsvSchema(
    new CsvColumn("Z", INT, false),                  // Required
    new CsvColumn("ionization_energy", DOUBLE, true) // Optional (nullable)
);

// Set null value for optional column
Double ionizationEnergy = null;  // Not available for this element
try {
    ionizationEnergy = element.getIonizationEnergy();
} catch (EPQFatalException e) {
    // Leave as null
}

builder.set("Z", Z)
       .set("ionization_energy", ionizationEnergy);  // null is OK for nullable column

String[] row = builder.buildRow();
// Result: ["26", ""]  - null serializes to empty string
```

**Type-Safe Serialization**:

| Java Type | CSV Output | Format |
|-----------|------------|--------|
| `Integer` | `"26"` | Plain integer |
| `Double` | `"6.403900000000e+03"` | Scientific notation (12 decimal places) |
| `String` | `"Iron"` | As-is |
| `Boolean` | `"true"` or `"false"` | Lowercase |
| `null` (nullable column) | `""` | Empty string |

### CsvWriter

Writes header and rows to output stream with RFC 4180-compliant escaping.

**Responsibilities**:
- Write CSV header from schema
- Write data rows with comma separation
- Auto-write header before first row if not explicitly written
- Escape fields containing commas, quotes, or newlines per RFC 4180
- Flush output when requested

**Field Escaping (RFC 4180)**:

```java
// Fields with special characters are automatically quoted and escaped
"Simple value"     → Simple value      // No quotes needed
"Has, comma"       → "Has, comma"      // Quoted
"Has "quote""      → "Has ""quote"""  // Internal quotes doubled
"Has\nnewline"     → "Has\nnewline"    // Quoted
```

Python's `csv.DictReader()` automatically handles these escapes during parsing.

### Design Invariants

**Determinism is achieved through**:
1. **Schema-enforced column order**: `CsvSchema` holds immutable, ordered column list
2. **Order-agnostic row building**: `CsvRowBuilder.buildRow()` outputs columns in schema order, not insertion order
3. **Locale-independent formatting**: All double values use `Locale.ROOT` and `"%.12e"` format
4. **Type-safe serialization**: Column type determines serialization method
5. **No dynamic column definitions**: Schema is fixed before any data is written


## DumpModule

`DumpModule` represents **one dumpable unit of reference behavior**. Each module corresponds roughly to one EPQ concept (e.g., `XRayTransition`, `EdgeEnergy`).

Located at `test/java/src/main/java/epq/reference/DumpModule.java` (interface) and implementations like `test/java/src/main/java/epq/reference/XRayTransitionDump.java`.

### Interface

```java
public interface DumpModule {
    /// Module command name (e.g., "XRayTransition")
    String name();

    /// Human-readable usage string
    String usage();

    /// Return the CSV schema.
    CsvSchema schema();

    /// Execute the dump, parse arguments, emit CSV
    /// @throws IllegalArgumentException if arguments are invalid
    void run(DumpContext ctx) throws IllegalArgumentException;
}
```

### Responsibilities

A `DumpModule`:

- Defines its command name
- Declares its usage string (human-readable, shown on error)
- Defines the schema for CSV output
- Parses and validates its own arguments
- Executes reference logic
- Emits CSV via `DumpContext.row()` and `DumpContext.flush()`

### Argument Validation Model

Two-tier error handling:

1. **Syntax errors** (argument parsing):
   - Handled by `DumpContext` in constructor
   - Throws `IllegalArgumentException` if `key=value` format is malformed
   - Thrown immediately, before `DumpModule.run()` is called

2. **Semantic errors** (validation):
   - Handled by `DumpModule.run()`
   - Throws `IllegalArgumentException` if arguments are valid syntax but invalid values
   - Caught by `TestDump`, which decides how to surface the error

### Example Error Flow

```java
// Syntax error: caught before run()
ctx.get("Z");  // argument doesn't exist → IllegalArgumentException

ctx.getInt("Z"); // argument not convertible to int → IllegalArgumentException

// Semantic error: caught during run()
trans t = ctx.get("trans");  // valid syntax
if (z < 1 || z > 118) {
    throw new IllegalArgumentException("trans out of range");
}
```

### Error Propagation

1. `DumpModule.run()` throws `IllegalArgumentException`
2. `TestDump` catches it
3. If in single mode, prints module usage and error message
4. If in batch mode, prints framing marker with error note
5. Exit code is always 1

---

## Registering a New DumpModule

To add a new dump module:

1. Create a class implementing `DumpModule` in `test/java/src/main/java/epq/reference/`
2. Implement `name()`, `usage()`, `schema()` and `run()`
3. Register it in `TestDump.getDumpModules()`

Example:

```java
// In TestDump.java
private static final Map<String, DumpModule> MODULES = Stream.of(
            new DumpXRayTransition(),
            new DumpElement()
            // add more here
    ).collect(Collectors.toMap(DumpModule::name, m -> m));
```

## Maven Layout

This project uses the standard Maven layout:

```
test/java/
├── src/main/java/
│   └── epq/reference/
│       ├── TestDump.java
│       ├── DumpContext.java
│       ├── CsvWriter.java
│       ├── DumpModule.java
│       └── (implementations)
├── pom.xml
└── target/
```

**Benefits**:
- Zero custom build configuration
- Maximum IDE and tooling compatibility
- Fewer failure modes when invoking Maven from pytest or CI
- Standard Maven plugins work out of the box

## Using run_testdump.py

For convenience, the `scripts/run_testdump.py` helper script provides a simpler interface to invoke `TestDump` without needing to remember the full Maven command syntax.

### Usage

```bash
python scripts/run_testdump.py <module> [arg1=value1] [arg2=value2] ...
```

### Examples

**Single invocation:**

```bash
python scripts/run_testdump.py Element Z=1
python scripts/run_testdump.py XRayTransition Z=26 trans=1
```

**Batch mode (read from stdin):**

```bash
echo "Element Z=1" | python scripts/run_testdump.py batch
```

**Multiple batch requests:**

```bash
cat << EOF | python scripts/run_testdump.py batch
Element Z=1
Element Z=79
XRayTransition Z=26 trans=1
EOF
```

### How It Works

The script:
1. Takes all command-line arguments and joins them with spaces
2. Passes them to `TestDump` via Maven's `-Dexec.args` parameter
3. Automatically finds the Java project root directory
4. Runs Maven from the correct working directory
5. Logs the command and working directory to stderr for debugging
6. Exits with the same return code as Maven
