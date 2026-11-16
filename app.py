"""Streamlit UI only — no business logic here.   OWNER: Акім (issue "A2").

Run: streamlit run app.py   (needs ANTHROPIC_API_KEY in env or .streamlit/secrets.toml)
"""
import pandas as pd
import pydeck as pdk
import streamlit as st

from garantovano import config, data
from garantovano.match import default_classifier, is_emergency_text, match
from garantovano.search import search, settlement_centroid

st.set_page_config(page_title="Гарантовано", page_icon="🩺", layout="centered")


@st.cache_resource
def load_all():
    return data.load_packages(), data.load_facilities(), data.load_rights(), data.load_meta()


@st.cache_data(show_spinner=False, ttl=3600)
def geocode(address: str, settlement: str):
    """One Nominatim call; None on any failure (UI falls back to the settlement centroid)."""
    try:
        from geopy.geocoders import Nominatim
        loc = Nominatim(user_agent="garantovano-demo", timeout=5).geocode(
            f"{address}, {settlement.title()}, Україна", country_codes="ua")
        return (loc.latitude, loc.longitude) if loc else None
    except Exception:
        return None


def run_match(text: str):
    try:
        return match(text, packages, default_classifier())
    except Exception:  # D1 not merged yet / no key / network -> manual picker (fail closed)
        return None


packages, facilities, rights, meta = load_all()
ss = st.session_state

st.title("Гарантовано")
st.caption("Де вам безкоштовно допоможуть за Програмою медичних гарантій — за відкритими даними НСЗУ.")

# 1. Need -----------------------------------------------------------------------------------------
st.write("Приклади:")
cols = st.columns(len(config.FLAGSHIP_EXAMPLES))
for col, ex in zip(cols, config.FLAGSHIP_EXAMPLES):
    if col.button(ex[:40] + ("…" if len(ex) > 40 else ""), key=f"ex-{ex}", use_container_width=True):
        ss.need = ex
text = st.text_area("Що вам потрібно?", key="need", placeholder=config.FLAGSHIP_EXAMPLES[0],
                    max_chars=config.MAX_INPUT_CHARS)

# 2. Location -------------------------------------------------------------------------------------
regions = sorted({f.region for f in facilities})
c1, c2 = st.columns(2)
region = c1.selectbox("Область", regions, index=regions.index("М.КИЇВ") if "М.КИЇВ" in regions else 0)
settlements = sorted({f.settlement for f in facilities if f.region == region})
default_city = region.removeprefix("М.")
settlement = c2.selectbox("Населений пункт", settlements,
                          index=settlements.index(default_city) if default_city in settlements else 0)
address = st.text_input("Адреса або район (необов'язково)", placeholder="напр. Оболонський проспект, 1")

if st.button("Знайти", type="primary") and text.strip():
    ss.result = run_match(text)
    ss.searched_text = text
    ss.pop("picked", None)

if "searched_text" in ss:
    result = ss.result
    if (result and result.emergency) or is_emergency_text(ss.searched_text):
        st.error(f"🚑 Якщо зараз є загрозливі симптоми — дзвоніть **{config.EMERGENCY_NUMBER}**. Не їдьте самі.")

    # 3. Packages (LLM result or manual picker, fail closed) -------------------------------------
    ids = list(result.package_ids) if result else []
    if result is None or result.needs_picker:
        st.info("Не вдалося точно визначити послугу — оберіть її зі списку.")
        ids = st.multiselect("Послуга за ПМГ", list(packages), default=[i for i in ids if i in packages],
                             format_func=lambda i: packages[i].name, key="picked",
                             max_selections=config.MAX_PACKAGES)
    else:
        st.success("Безкоштовно за ПМГ: " + " · ".join(packages[i].name for i in ids if i in packages))

    if ids:
        # 4. Search -----------------------------------------------------------------------------
        centroid = settlement_centroid(facilities, region, settlement)
        geo = geocode(address.strip(), settlement) if address.strip() else None
        if address.strip() and geo is None:
            st.caption("Адресу не знайдено — рахуємо відстань від центру населеного пункту.")
        origin = geo or centroid
        hits = search(facilities, ids, origin, region=region) if origin else []

        if not hits:
            st.warning("У цій області не знайдено закладів з усіма обраними послугами. "
                       f"Зателефонуйте на гарячу лінію НСЗУ {config.NSZU_HOTLINE}.")
        else:
            df = pd.DataFrame([{"lat": h.facility.lat, "lng": h.facility.lng,
                                "name": h.facility.legal_entity_name, "addr": h.facility.address} for h in hits])
            st.pydeck_chart(pdk.Deck(
                map_style=None,
                initial_view_state=pdk.ViewState(latitude=origin[0], longitude=origin[1], zoom=10),
                layers=[
                    pdk.Layer("ScatterplotLayer", df, get_position="[lng, lat]", get_radius=300,
                              get_fill_color=[220, 40, 60, 200], pickable=True),
                    pdk.Layer("ScatterplotLayer", pd.DataFrame([{"lat": origin[0], "lng": origin[1]}]),
                              get_position="[lng, lat]", get_radius=200, get_fill_color=[30, 110, 230, 220]),
                ],
                tooltip={"text": "{name}\n{addr}"},
            ))
            names = "; ".join(packages[p].name for p in ids if p in packages)
            for h in hits:
                f = h.facility
                with st.container(border=True):
                    st.markdown(f"**{f.legal_entity_name}**  \n{f.division_name}")
                    st.write(f"📍 {f.address} · {h.distance_km:.1f} км")
                    if f.phone:
                        st.markdown(f"📞 [{f.phone}](tel:{f.phone.replace(' ', '')})")
                    st.caption("Договір НСЗУ: " + names)
                    if "8" in f.package_ids and "8" not in ids:
                        st.caption("👶 є неонатальна допомога")

        # 5. Rights -----------------------------------------------------------------------------
        st.subheader("Ваші права")
        for pid in ids:
            r = rights.get(pid)
            if not r:
                continue
            with st.expander(r["title"], expanded=len(ids) == 1):
                if r.get("emergency_note"):
                    st.error(r["emergency_note"])
                st.markdown(f"**Кому:** {r['eligible']}")
                st.markdown(f"**Направлення:** {r['referral_needed']}")
                for label, key in (("Що входить безкоштовно", "included"), ("Що взяти з собою", "bring"),
                                   ("Якщо просять гроші", "if_asked_to_pay")):
                    if r.get(key):
                        st.markdown(f"**{label}:**\n" + "\n".join(f"- {x}" for x in r[key]))
                srcs = r.get("sources") or []
                if srcs:
                    st.caption("Джерела: " + " · ".join(f"[{s.get('title') or s['url']}]({s['url']})" for s in srcs))
        st.info(config.DISCLAIMER)

st.divider()
st.caption(f"Дані: НСЗУ, data.gov.ua · зібрано {meta['built_at'][:10]} · {meta['divisions_out']} закладів · "
           f"гаряча лінія НСЗУ {config.NSZU_HOTLINE}")
