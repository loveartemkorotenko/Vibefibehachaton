"""UI smoke: both demo scenarios in a row via the manual picker, and 103 first. No network, no API key.

Note: AppTest drives the Streamlit backend only. Bug #15 (stale chips kept by the browser
frontend) does not reproduce here; it was verified by hand in a real browser.
"""
import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from garantovano import config  # noqa: E402
from garantovano.match import AnthropicClassifier  # noqa: E402


@pytest.fixture
def app(monkeypatch):
    def no_llm(self, text, packages):  # force the fail-closed picker path
        raise RuntimeError("LLM disabled in tests")
    monkeypatch.setattr(AnthropicClassifier, "classify", no_llm)
    return AppTest.from_file("../app.py", default_timeout=60).run()


def search_example(at, example):
    at.button(key=f"ex-{example}").click().run()
    next(b for b in at.button if b.label == "Знайти").click().run()


def result_lines(at):
    return [m.value for m in at.markdown if " км" in m.value]


def test_picker_resets_between_searches_and_both_demo_scenarios_find_facilities(app):
    pregnancy, veteran = config.FLAGSHIP_EXAMPLES[0], config.FLAGSHIP_EXAMPLES[1]

    search_example(app, pregnancy)
    assert app.multiselect[0].value == []
    app.multiselect[0].set_value(["35", "7"]).run()
    assert len(result_lines(app)) >= 5

    search_example(app, veteran)
    assert app.multiselect[0].value == [], "packages from the previous search must not stick"
    app.multiselect[0].set_value(["66"]).run()
    assert result_lines(app), "veteran dental search must find facilities in Kyiv"
    assert not [w for w in app.warning if "не знайдено" in w.value]


def test_emergency_banner_comes_first(app):
    app.text_area(key="need").set_value("У тата інсульт, куди їхати?").run()
    next(b for b in app.button if b.label == "Знайти").click().run()
    assert app.error and "103" in app.error[0].value
