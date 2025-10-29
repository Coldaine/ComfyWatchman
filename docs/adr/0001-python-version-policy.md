# ADR 0001: Python Version Policy for ComfyWatchman

- Status: Accepted
- Date: 2025-10-29
- Owners: ComfyWatchman maintainers

## Context

ComfyWatchman is a Python CLI/tooling layer that analyzes ComfyUI workflows and automates dependency resolution and downloads. It must coexist with users' ComfyUI environments (core + custom nodes) and with PyTorch wheels on Linux.

Upstream signals as of 2025-10-29:

- Python release windows (official devguide):
  - 3.10 security-only until 2026-10; 3.11 until 2027-10; 3.12 until 2028-10; 3.13 until 2029-10. 3.9 exits security in 2025-10.
- ComfyUI README: "Python 3.13 is very well supported. If you have trouble with some custom node dependencies on 3.13 you can try 3.12." 3.14 can work only if `kornia` is removed (not recommended).
- PyTorch: latest stable requires Python 3.10+; install guidance lists support through Python 3.14 on Linux.

Project constraints:

- Favor a single minimum version mandate that avoids unnecessary friction for users and CI, with a long EOL runway.
- Avoid hard-pinning to an exact Python minor; keep flexibility for users on newer interpreters where compatible.

## Decision

- Mandate minimum Python version: 3.12 (requires-python ">=3.12").
- Also test/support: 3.13 (to stay ahead and surface incompatibilities early).
- Do not mandate 3.14 yet due to `kornia` caveat in ComfyUI README and potential ecosystem lag.

This is a minimum version policy, not an exact pin. Users on 3.13 should generally be fine; if custom nodes lag, our documentation will recommend using 3.12.

## Rationale

- Ecosystem compatibility: ComfyUI explicitly recommends 3.12 as fallback if some custom nodes are not 3.13-ready.
- Longevity: 3.12 receives security updates until 2028-10; 3.13 until 2029-10.
- PyTorch support: Stable PyTorch requires Python 3.10+, and vendor tooling lists 3.10–3.14 as supported, so 3.12 sits in the well-supported middle.

## What we have already done

- Migrated to a Ruff-only toolchain (replacing Black and flake8) to unify lint/format, speed up CI, and simplify configuration.
- Aligned lint configuration for modern Python while suppressing pyupgrade rules that conflict with older targets; this prepares us to enable stricter rules once 3.12 is the baseline.
- Verified upstream guidance for Python EOL, ComfyUI Python support, and PyTorch’s Python range to ground this decision.

Note: As of this ADR, the core source hasn’t introduced 3.12-specific syntax that would break older interpreters; the mandate is a policy we’ll enforce via packaging metadata and CI.

## Consequences

- Users must have Python 3.12+ to install and run ComfyWatchman. 3.13 is supported; 3.14 may work but is not recommended due to upstream ecosystem caveats.
- We can enable additional Ruff/pyupgrade checks (e.g., type hinting improvements) once the pyproject target and CI matrix are bumped, reducing legacy shims and making code cleaner.

## Implementation plan (small, incremental)

1. Packaging metadata
   - Update `pyproject.toml`:
     - `requires-python = ">=3.12"`
     - Trove classifiers: add `Programming Language :: Python :: 3.12` and `3.13`; ensure `3 :: Only` style classifiers reflect support accurately (no exact pin).
2. Tooling
   - Update Ruff target: `target-version = "py312"`.
   - Revisit `pyupgrade` ignores (e.g., remove `UP006`, `UP045` ignores added for older targets) and auto-fix where safe.
3. CI
   - Test matrix: required on 3.12; allowed/optional on 3.13.
   - Gate on `ruff check` and unit tests for both versions.
4. Docs
   - INSTALL/README: state “Requires Python 3.12+; tested on 3.12 and 3.13. If you encounter custom-node issues on 3.13, use 3.12.”

These steps keep flexibility: we set a minimum, test the next version, and avoid any hard pin to a single minor.

## Risks and mitigations

- Risk: Some ComfyUI custom nodes might have lagging support on 3.13.
  - Mitigation: Official docs will recommend 3.12 as the fallback; CI will continue to run 3.12 as the required baseline.
- Risk: Users on 3.14 might hit `kornia` or other ecosystem issues.
  - Mitigation: We will not advertise 3.14 support yet; we’ll revisit once upstream guidance stabilizes.

## Success criteria

- Packaging publishes and installs cleanly on Python 3.12 and 3.13 (Linux).
- CI: Lint and tests green on 3.12; green or actionable issues surfaced on 3.13.
- Fewer compatibility reports from users compared to older baselines.

## Alternatives considered

- Mandate 3.13 now: Longer runway but slightly higher risk of custom-node friction; still tested to prepare for future.
- Mandate 3.14: Rejected for now due to `kornia` caveat and higher ecosystem risk.

## References

- [Python devguide “Status of Python versions”](https://devguide.python.org/versions/)
- [ComfyUI README (Python version notes)](https://github.com/comfyanonymous/ComfyUI)
- [PyTorch Get Started (Python support)](https://pytorch.org/get-started/locally/)
