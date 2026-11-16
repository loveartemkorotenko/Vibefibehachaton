"""Streamlit UI only — no business logic here.   OWNER: Акім (issue "A2").

Run: streamlit run app.py   (needs ANTHROPIC_API_KEY in env or .streamlit/secrets.toml)
"""
import streamlit as st

from garantovano import config, data
from garantovano.match import AnthropicClassifier, match
from garantovano.search import search, settlement_centroid

st.set_page_config(page_title="Гарантовано", page_icon="🩺", layout="centered")


@st.cache_resource
def load_all():
    return data.load_packages(), data.load_facilities(), data.load_rights(), data.load_meta()


packages, facilities, rights, meta = load_all()

st.title("Гарантовано")
st.caption("Де вам безкоштовно допоможуть за Програмою медичних гарантій — за відкритими даними НСЗУ.")

# 1. Need -----------------------------------------------------------------------------------------
text = st.text_area("Що вам потрібно?", placeholder=config.FLAGSHIP_EXAMPLES[0], max_chars=config.MAX_INPUT_CHARS)
# TODO(A2): example chips from config.FLAGSHIP_EXAMPLES that fill the text box.

# 2. Location -------------------------------------------------------------------------------------
regions = sorted({f.region for f in facilities})
region = st.selectbox("Область", regions, index=regions.index("М.КИЇВ"))
# TODO(A2): settlement select for the region; optional address -> one geocode call (geopy Nominatim,
#           user_agent "garantovano-demo"), fallback = settlement_centroid(...).

if st.button("Знайти", type="primary") and text.strip():
    try:
        result = match(text, packages, AnthropicClassifier())
    except NotImplementedError:
        result = None  # D1 not merged yet -> manual picker below
    if result and result.emergency:
        st.error(f"Якщо зараз є загрозливі симптоми — дзвоніть {config.EMERGENCY_NUMBER}. Не їдьте самі.")
    # TODO(A2): if result is None or result.needs_picker -> st.multiselect over packages (fail closed).
    # TODO(A2): search(...) -> pydeck map + cards (name, address, tel: link, packages, distance);
    #           flag "є неонатальна допомога" when "8" in facility.package_ids.
    # TODO(A2): rights card per chosen package from `rights` (+ source links), then config.DISCLAIMER.

st.divider()
st.caption(f"Дані: НСЗУ, data.gov.ua · зібрано {meta['built_at'][:10]} · {meta['divisions_out']} закладів · "
           f"гаряча лінія НСЗУ {config.NSZU_HOTLINE}")
