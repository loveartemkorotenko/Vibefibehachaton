"""Run issue D1's ten fixtures against the real API; never report offline accuracy.

Run from the repository root: ``python scripts/smoke_match.py``.
Use ``--check-only`` to inspect prerequisites without sending API requests.
Only case numbers and validated outcomes are printed, never prompts or API errors.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

# Direct script execution puts scripts/, rather than the project, on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from garantovano import config
from garantovano.data import load_packages

# Key env vars per provider; the smoke test checks the provider the app really uses.
KEY_ENV = {"gemma": ("GEMINI_API_KEY", "GOOGLE_API_KEY"), "anthropic": ("ANTHROPIC_API_KEY",)}


# Exact smoke fixtures and expected outcomes from GitHub issue #2, not app rules.
CASES = (
    ("я вагітна, де стати на облік", ("35",), False),
    ("де народжувати безкоштовно", ("7",), False),
    ("ветеран, треба поставити зуби", ("66",), False),
    ("мамі потрібна мамографія", ("10",), False),
    ("колоноскопія", ("13",), False),
    ("гемодіаліз", ("16",), False),
    ("хіміотерапія", ("17",), False),
    ("психолог після фронту", ("72",), False),
    ("у тата інсульт", ("5",), True),
    ("asdf qwerty", (), False),
)


def main(argv: list[str] | None = None) -> int:
    """Return 0 on verified acceptance, 1 on wrong output, 2 if unverified."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-only", action="store_true",
        help="Check the local catalog and API-key presence; do not call the API.",
    )
    args = parser.parse_args(argv)
    try:
        packages = load_packages()
    except Exception:
        print("UNVERIFIED: package catalog could not be loaded; no API calls made.")
        return 2
    if not all(pid in packages for _, ids, _ in CASES for pid in ids):
        print("UNVERIFIED: expected fixture IDs are missing from the catalog.")
        return 2
    provider = config.LLM_PROVIDER
    key_names = KEY_ENV.get(provider, KEY_ENV["gemma"])
    has_key = any(os.getenv(name, "").strip() for name in key_names)
    print(f"Provider under test: {provider} (set GARANTOVANO_PROVIDER to change).")
    if args.check_only:
        print("Catalog prerequisites: OK.")
        print(f"API key present ({' or '.join(key_names)}): {'yes' if has_key else 'no'}.")
        print("UNVERIFIED: no API calls made; model accuracy was not tested.")
        return 0 if has_key else 2
    if not has_key:
        print(f"UNVERIFIED: {' or '.join(key_names)} is missing; live smoke was skipped.")
        return 2

    try:
        from garantovano.match import default_classifier, match

        classifier = default_classifier()  # the same adapter app.py uses
    except Exception:
        print("UNVERIFIED: classifier unavailable; check installed dependencies.")
        return 2
    correct = pickers = wrong = unverified = 0
    print("LIVE API smoke — fixed issue #2 fixtures; no raw model text is shown.")
    print("case | expected | validated IDs | emergency | outcome")
    for index, (text, expected_ids, expected_emergency) in enumerate(CASES, 1):
        try:
            result = match(text, packages, classifier)
        except Exception:
            unverified += 1
            print(f"{index:02d}   | UNVERIFIED: matching raised an exception")
            continue
        if result.emergency != expected_emergency:
            outcome = "WRONG_EMERGENCY"
            wrong += 1
        elif result.reason == "llm_error":
            outcome = "UNVERIFIED_API_OR_OUTPUT_ERROR"
            unverified += 1
        elif result.needs_picker:
            if expected_ids:
                outcome = "PICKER"
                pickers += 1
            else:
                outcome = "CORRECT_PICKER"
                correct += 1
        elif set(result.package_ids) == set(expected_ids) and expected_ids:
            outcome = "CORRECT_MATCH"
            correct += 1
        else:
            outcome = "CONFIDENTLY_WRONG"
            wrong += 1
        expected = ",".join(expected_ids) or "picker"
        actual = ",".join(result.package_ids) or "—"
        print(f"{index:02d}   | {expected:8} | {actual:13} | {str(result.emergency):9} | {outcome}")

    total = len(CASES)
    print(f"Correct: {correct}/{total}; picker fallback: {pickers}/{total}; "
          f"wrong: {wrong}/{total}; unverified: {unverified}/{total}.")
    print("Picker fallback demonstrates safety, not correct model classification.")
    if wrong:
        print("FAIL: confidently wrong IDs or an incorrect emergency flag.")
        return 1
    # The issue's acceptance threshold is a smoke-test expectation, not app logic.
    if correct + pickers < 8 or unverified:
        print("UNVERIFIED: live smoke acceptance could not be fully verified.")
        return 2
    print("PASS: at least 8/10 correct-or-picker; zero wrong; all API outcomes verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
