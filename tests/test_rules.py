"""Deterministic fast path (garantovano/rules.py) on the real package catalogue; no network."""
import pytest

from garantovano import config, data
from garantovano.models import LLMClassification
from garantovano.rules import keyword_packages, understand

PACKAGES = data.load_packages()


class FakeLLM:
    def __init__(self, ids=(), error=None):
        self.ids, self.error, self.calls = list(ids), error, 0

    def classify(self, text, packages):
        self.calls += 1
        if self.error:
            raise self.error
        return LLMClassification(self.ids, False, 0.9)


@pytest.mark.parametrize("text,expected", [
    (config.FLAGSHIP_EXAMPLES[0], ("35", "7")),
    ("Я ветеран, мені треба поставити зуби", ("66",)),
    ("Мамі потрібна мамографія", ("10",)),
    ("У тата ІНСУЛЬТ", ("5",)),
    ("потрібен психолог після фронту", ("72",)),
    ("де зробити колоноскопію", ("13",)),
])
def test_common_needs_map_to_packages(text, expected):
    assert keyword_packages(text, PACKAGES) == expected


def test_rule_path_skips_the_model_and_keeps_103():
    llm = FakeLLM(error=RuntimeError("must not be called"))
    result = understand("У тата інсульт, куди їхати?", PACKAGES, llm)
    assert result.package_ids == ("5",) and result.emergency and result.reason == "rule"
    assert not result.needs_picker and llm.calls == 0


def test_dental_without_veteran_status_goes_to_the_model():
    assert keyword_packages("дитині треба полікувати зуби", PACKAGES) == ()
    llm = FakeLLM(["34"])
    assert understand("дитині треба полікувати зуби", PACKAGES, llm).package_ids == ("34",)
    assert llm.calls == 1


@pytest.mark.parametrize("text,reason", [("   ", "empty"), ("вагітна " * 80, "too_long")])
def test_empty_or_too_long_keep_match_contract(text, reason):
    llm = FakeLLM(["35"])
    result = understand(text, PACKAGES, llm)
    assert result.needs_picker and result.reason == reason and llm.calls == 0


def test_rule_ids_exist_in_catalogue():
    for _, ids in config.KEYWORD_RULES:
        assert set(ids) <= PACKAGES.keys()
