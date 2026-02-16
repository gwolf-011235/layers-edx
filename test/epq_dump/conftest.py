from typing import Iterable, cast
import pytest
from pytest import StashKey
import subprocess
from pathlib import Path
from test.epq_dump.csv_parser import parse_epq_batch_output
from test.epq_dump.core_models import DumpRequest, DumpArgs, CsvTable
from test.epq_dump.validators import validate_table
from pydantic import BaseModel
import os


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers"""
    config.addinivalue_line("markers", "epq_ref: test requires EPQ reference output")


# Global flag to control whether to run the full suite or a reduced set of tests
FULL_SUITE = os.getenv("PYTEST_FULL_SUITE", "false").lower() == "true"


# Global cache to store Java results for the duration of the session
JAVA_ORACLE_DATA: dict[DumpRequest, CsvTable] = {}

# Stash key for storing DumpRequest on pytest items
dump_request_key = StashKey[DumpRequest]()


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """
    HOOK: Runs after all tests are discovered but BEFORE they execute.
    Gathers all @pytest.mark.epq_ref requirements.
    """
    requests_to_run: set[DumpRequest] = set()

    for item in items:
        marker = item.get_closest_marker("epq_ref")
        if marker:
            module: str = marker.kwargs.get("module", "")
            # Accessing callspec requires a check as not all items have it
            callspec = getattr(item, "callspec", None)
            if callspec:
                raw_args: DumpArgs = tuple(
                    (str(k), str(v)) for k, v in callspec.params.items()
                )
                req = DumpRequest(module=module, args=raw_args)

                # Store the request in item's stash for the fixture to retrieve
                item.stash[dump_request_key] = req
                requests_to_run.add(req)

    if requests_to_run:
        print(
            f"\n[Java Oracle] Invoking JVM for {len(requests_to_run)} unique dumps..."
        )
        results = run_java_oracle_batch(requests_to_run)
        JAVA_ORACLE_DATA.update(results)


def run_java_oracle_batch(
    requests: Iterable[DumpRequest],
) -> dict[DumpRequest, CsvTable]:
    """Feeds all requests into Java via stdin and parses the result."""
    batch_input = "\n".join(r.to_batch_line() for r in requests) + "\n"

    java_project_root = (Path(__file__).parent.parent / "java").resolve()

    result = subprocess.run(
        [
            "mvn",
            "-q",
            "exec:java",
            "-Dexec.mainClass=epq.reference.TestDump",
            "-Dexec.args=batch",
        ],
        cwd=java_project_root,
        input=batch_input,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Java Oracle Failed:\n{result.stderr}")

    return dict(parse_epq_batch_output(result.stdout))


@pytest.fixture
def java_dump(request: pytest.FixtureRequest) -> list[BaseModel]:
    """
    Retrieve the cached CSV result for the current test as a list of
    validated Pydantic model instances.

    Uses pytest's StashKey to retrieve the DumpRequest stored during collection phase.

    Usage:
        @pytest.mark.epq_ref(module="XRayTransition")
        @pytest.mark.parametrize("Z, trans", [(26, "1")])
        def test_xray(Z: int, trans: int, java_dump: list[XRayTransitionRow]):
            assert len(java_dump) > 0
    """
    item = cast(pytest.Item, request.node)  # type: ignore
    req: DumpRequest | None = item.stash.get(dump_request_key, None)
    if req is None:
        pytest.fail("Test marked with java_dump must use @pytest.mark.epq_ref")

    data = JAVA_ORACLE_DATA.get(req)
    if data is None:
        pytest.fail(f"No Java data available for {req}")

    # Automatically validate against schema using module name from DumpRequest
    try:
        validated_data = validate_table(req.module, data)
        return validated_data
    except Exception as e:
        pytest.fail(f"Schema validation failed for module {req.module}: {e}")
