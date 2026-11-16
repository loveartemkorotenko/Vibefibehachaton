"""UI smoke via Streamlit AppTest: examples, picker fallback, 103 first. No network, no API key.

AppTest drives the backend only; browser-side widget state (#15) is verified by hand.
"""
import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from garantovano import config  # noqa: E402
from garantovano.match import AnthropicClassifier, GemmaClassifier  # noqa: E402

SEARCH = "Знайти безкоштовну допомогу"


@pytest.fixture
def app(monkeypatch):
    def no_llm(self, text, packages):  # the model is never reachable in tests
        raise RuntimeError("LLM disabled in tests")
    monkeypatch.setattr(AnthropicClassifier, "classify", no_llm)
    monkeypatch.setattr(GemmaClassifier, "classify", no_llm)
    return AppTest.from_file("../app.py", default_timeout=60).run()


def result_lines(at):
    return [m.value for m in at.markdown if "Знайдено" in m.value]


@pytest.mark.parametrize("label", [label for label, _ in config.EXAMPLES])
def test_each_example_searches_at_once_without_the_model(app, label):
    app.button(key=f"ex-{label}").click().run()
    assert result_lines(app), f"{label}: no facilities found"
    assert not [w for w in app.warning if "не знайдено" in w.value]


def test_examples_in_a_row_never_show_old_results(app):
    pregnancy, veteran = config.EXAMPLES[0][0], config.EXAMPLES[1][0]
    app.button(key=f"ex-{pregnancy}").click().run()
    assert app.multiselect[0].value == ["35", "7"]
    app.button(key=f"ex-{veteran}").click().run()
    assert app.multiselect[0].value == ["66"]


def test_unknown_need_falls_back_to_picker(app):
    app.text_area(key="need").set_value("щось зовсім незрозуміле").run()
    next(b for b in app.button if b.label == SEARCH).click().run()
    assert app.multiselect[0].value == []
    app.multiselect[0].set_value(["13"]).run()
    assert result_lines(app)


def test_emergency_banner_shown(app):
    app.button(key=f"ex-{config.EXAMPLES[3][0]}").click().run()
    assert any("103" in m.value for m in app.markdown)
    assert result_lines(app)
