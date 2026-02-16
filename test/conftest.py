import pytest
import numpy as np
from pathlib import Path
from layers_edx.element import Element, Composition
from layers_edx.detector.eds_detector import (
    EDSDetector,
    DetectorProperties,
    DetectorPosition,
    EDSCalibration,
)
from layers_edx.spectrum.spectrum_properties import SpectrumProperties
from layers_edx.xrt import XRayTransition
from layers_edx.units import ToSI


@pytest.fixture
def mock_element() -> Element:
    return Element("Si")


@pytest.fixture
def mock_composition(mock_element: Element) -> Composition:
    return Composition([mock_element], [1.0])


@pytest.fixture
def mock_xrt(mock_element: Element) -> XRayTransition:
    """Silicon Ka1 X-ray transition"""
    return XRayTransition(mock_element, "KA1")


@pytest.fixture
def mock_beam_energy_15kev():
    """15 keV beam energy in Joules"""
    return ToSI.kev(15.0)


@pytest.fixture
def mock_beam_energy_20kev():
    """20 keV beam energy in keV (for SpectrumProperties)"""
    return 20.0


@pytest.fixture
def mock_spectrum_data():
    """Standard test spectrum data with a peak at channel 17"""
    data = np.zeros(150)
    data[17] = 100.0
    return data


@pytest.fixture
def mock_detector():
    det_prop = DetectorProperties(1024, 10.0, 1.0)  # channel_count, area, thickness
    det_pos = DetectorPosition()
    det_cal = EDSCalibration(10.0)  # channel_width
    return EDSDetector(det_prop, det_pos, det_cal)


@pytest.fixture
def mock_spectrum_properties(
    mock_detector: EDSDetector, mock_beam_energy_20kev: float
) -> SpectrumProperties:
    return SpectrumProperties(mock_detector, mock_beam_energy_20kev)


# ============================================================================
# EPQ Cross-Validation Infrastructure
# ============================================================================


def epq_classes():
    """Locate EPQ compiled classes directory"""
    from pathlib import Path

    # Primary location: EPQ compiled classes in venv
    venv_epq_classes = Path(".venv") / "share" / "java" / "EPQ" / "target" / "classes"

    if venv_epq_classes.exists():
        return str(venv_epq_classes.absolute())

    pytest.skip("EPQ classes not found. Run 'mvn compile' in .venv/share/java/EPQ/.")


def run_java_test(java_file: str):
    """
    Compile and run a Java test file, return JSON output

    Args:
        java_file: Path to .java file

    Returns:
        Parsed JSON output from Java code
    """
    import subprocess
    import json
    import tempfile
    import os
    from pathlib import Path

    java_path = Path(java_file)
    epq_classes_path = Path(epq_classes())

    # Build classpath: EPQ classes + all dependency JARs
    classpath_parts = [str(epq_classes_path)]

    # Add all dependency JARs from Maven's dependency:copy-dependencies output
    dependency_dir = epq_classes_path.parent / "dependency"
    if dependency_dir.exists():
        for jar_file in dependency_dir.glob("*.jar"):
            classpath_parts.append(str(jar_file))

    classpath = os.pathsep.join(classpath_parts)
    with tempfile.TemporaryDirectory() as tmpdir:
        # Compile Java file
        compile_result = subprocess.run(
            ["javac", "-cp", classpath, str(java_path), "-d", tmpdir],
            capture_output=True,
            text=True,
        )

        if compile_result.returncode != 0:
            pytest.fail(f"Java compilation failed:\n{compile_result.stderr}")

        # Run Java class (assumes class name matches filename)
        class_name = java_path.stem
        run_result = subprocess.run(
            ["java", "-cp", f"{tmpdir}{os.pathsep}{classpath}", class_name],
            capture_output=True,
            text=True,
        )

        if run_result.returncode != 0:
            pytest.fail(f"Java execution failed:\n{run_result.stderr}")

        # Parse JSON output
        try:
            return json.loads(run_result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(
                f"Failed to parse Java output as JSON:\n{run_result.stdout}\nError: {e}"
            )


def compare_results(python_value, java_value, tolerance: float = 0.01):
    """
    Compare Python and Java results with relative tolerance

    Args:
        python_value: Result from layers-edx
        java_value: Result from EPQ
        tolerance: Relative tolerance (default 1%)

    Returns:
        True if values match within tolerance
    """
    # Handle single values
    if isinstance(python_value, (int, float)):
        return python_value == pytest.approx(java_value, rel=tolerance)

    # Handle arrays/lists
    py_arr = np.array(python_value)
    java_arr = np.array(java_value)

    return np.allclose(py_arr, java_arr, rtol=tolerance)


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "epq: EPQ cross-validation tests (requires Java and EPQ jar)"
    )
    config.addinivalue_line(
        "markers", "epq_env: EPQ environment setup verification tests"
    )

EPQ_PATH = "epq_dump"

def pytest_ignore_collect(collection_path: Path, config: pytest.Config) -> bool | None:
    path = Path(collection_path).resolve()

    # detect regression suite
    if EPQ_PATH not in path.parts:
        return None

    # allow if user explicitly asked for this file/dir
    for arg in config.args:
        arg_path = Path(arg)
        if arg_path == path or EPQ_PATH in arg_path.parts:
            return None

    # otherwise ignore it
    return True
