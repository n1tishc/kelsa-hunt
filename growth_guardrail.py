"""Observe Canonical Store growth and gate only source expansion."""

import argparse
import json
import pathlib
import re
import statistics
import subprocess
import tempfile
import time
from dataclasses import dataclass


MIB = 1024 * 1024
STORE_WARNING_BYTES = 20 * MIB
STORE_HARD_BYTES = 25 * MIB
TIMING_WARNING_SECONDS = 1.6
TIMING_HARD_SECONDS = 2.0
GIT_WARNING_BYTES = 200 * MIB
GIT_HARD_BYTES = 250 * MIB
SHARDING_RESPONSE = (
    "deterministic 16-way uid sharding is the next response; "
    "this check does not migrate or prune Records automatically"
)


@dataclass(frozen=True)
class GrowthAssessment:
    warning_reasons: tuple[str, ...]
    gate_reasons: tuple[str, ...]

    @property
    def gate_active(self):
        return bool(self.gate_reasons)


class SourceExpansionBlocked(RuntimeError):
    pass


def configured_source_count(sources):
    configured = {("simplify", "default")}
    for platform, values in sources.items():
        if not isinstance(values, list):
            raise ValueError(f"{platform} source inventory must be a list")
        configured.update((platform, str(value)) for value in values)
    return len(configured)


def enforce_source_expansion(assessment, approved_sources, proposed_sources):
    approved_count = configured_source_count(approved_sources)
    proposed_count = configured_source_count(proposed_sources)
    if assessment.gate_active and proposed_count > approved_count:
        reasons = "; ".join(assessment.gate_reasons)
        raise SourceExpansionBlocked(
            f"source expansion blocked ({approved_count} -> {proposed_count}): "
            f"{reasons}. Next response: {SHARDING_RESPONSE}."
        )


def assess_growth(serialized_bytes, timing_check_medians, packed_git_bytes=None):
    warnings = []
    gate_reasons = []
    if serialized_bytes >= STORE_WARNING_BYTES:
        warnings.append("Canonical Store is at or above 20 MiB")
    if serialized_bytes >= STORE_HARD_BYTES:
        gate_reasons.append("Canonical Store is at or above 25 MiB")
    if (
        timing_check_medians
        and timing_check_medians[-1] >= TIMING_WARNING_SECONDS
    ):
        warnings.append(
            "median load-plus-save time is at or above 1.6 seconds"
        )
    if (
        len(timing_check_medians) >= 2
        and all(
            median >= TIMING_HARD_SECONDS
            for median in timing_check_medians[-2:]
        )
    ):
        gate_reasons.append(
            "median load-plus-save time was at or above 2 seconds "
            "on two consecutive checks"
        )
    if packed_git_bytes is not None and packed_git_bytes >= GIT_WARNING_BYTES:
        warnings.append("packed full-history Git is at or above 200 MiB")
    if packed_git_bytes is not None and packed_git_bytes >= GIT_HARD_BYTES:
        gate_reasons.append("packed full-history Git is at or above 250 MiB")
    return GrowthAssessment(tuple(warnings), tuple(gate_reasons))


def measure_timing_checks(store_path, checks=2, rounds=5):
    canonical_bytes = store_path.read_bytes()
    medians = []
    with tempfile.TemporaryDirectory() as directory:
        round_trip_path = pathlib.Path(directory) / "jobs.json"
        for _ in range(checks):
            samples = []
            for _ in range(rounds):
                round_trip_path.write_bytes(canonical_bytes)
                started = time.perf_counter()
                payload = json.loads(round_trip_path.read_text())
                round_trip_path.write_text(
                    json.dumps(payload, indent=0, sort_keys=True)
                )
                samples.append(time.perf_counter() - started)
            medians.append(statistics.median(samples))
    return tuple(medians)


def packed_git_bytes(repository):
    shallow = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "--is-shallow-repository"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if shallow != "false":
        raise RuntimeError("packed Git measurement requires a full-history checkout")
    output = subprocess.run(
        ["git", "-C", str(repository), "count-objects", "-v"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    values = dict(
        line.split(": ", 1)
        for line in output.splitlines()
        if ": " in line
    )
    return int(values.get("size-pack", "0")) * 1024


def sources_at_ref(repository, ref):
    if not re.fullmatch(r"[0-9a-fA-F]{40,64}", ref):
        raise ValueError("baseline ref must be a full commit hash")
    content = subprocess.run(
        ["git", "-C", str(repository), "show", f"{ref}:sources.json"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return json.loads(content)


def assessment_lines(assessment):
    lines = [
        f"WARNING growth guardrail: {reason}"
        for reason in assessment.warning_reasons
    ]
    lines.extend(
        f"EXPANSION GATE ACTIVE: {reason}"
        for reason in assessment.gate_reasons
    )
    if not assessment.warning_reasons and not assessment.gate_reasons:
        lines.append("growth guardrail: within limits")
    lines.append(f"next response if gated: {SHARDING_RESPONSE}")
    return lines


def run_check(store_path, sources_path, repository, baseline_ref):
    canonical = json.loads(store_path.read_text())
    timing_medians = measure_timing_checks(store_path)
    git_bytes = packed_git_bytes(repository)
    serialized_bytes = store_path.stat().st_size
    assessment = assess_growth(
        serialized_bytes,
        timing_medians,
        git_bytes,
    )
    current_sources = json.loads(sources_path.read_text())
    approved_sources = sources_at_ref(repository, baseline_ref)
    print(
        f"growth metrics: records={len(canonical.get('jobs', {}))} "
        f"serialized_bytes={serialized_bytes} "
        f"timing_medians={','.join(f'{value:.4f}' for value in timing_medians)} "
        f"packed_git_bytes={git_bytes}"
    )
    for line in assessment_lines(assessment):
        print(line)
    enforce_source_expansion(assessment, approved_sources, current_sources)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--store", type=pathlib.Path, default=pathlib.Path("jobs.json")
    )
    parser.add_argument(
        "--sources", type=pathlib.Path, default=pathlib.Path("sources.json")
    )
    parser.add_argument(
        "--repository", type=pathlib.Path, default=pathlib.Path(".")
    )
    parser.add_argument("--baseline-ref", required=True)
    args = parser.parse_args()
    try:
        run_check(args.store, args.sources, args.repository, args.baseline_ref)
    except SourceExpansionBlocked as error:
        parser.exit(1, f"ERROR: {error}\n")


if __name__ == "__main__":
    main()
