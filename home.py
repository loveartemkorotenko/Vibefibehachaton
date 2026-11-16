"""Main page «Пошук допомоги». UI only: understanding, search and data live in garantovano/.

HTML/CSS here is static styling only (no user or dataset text goes into unsafe HTML).
"""
import pandas as pd
import pydeck as pdk
import streamlit as st

from garantovano import config, data
from garantovano.match import default_classifier, is_emergency_text
from garantovano.rules import understand
from garantovano.search import search, settlement_centroid

st.set_page_config(page_title="Гарантовано", page_icon="🩺", layout="centered")
st.markdown("""<style>
:root {--ivory: #FAF6EE; --card: #FFFDF8; --line: #E4DCCB; --blue: #1F5FAE; --blue-soft: #EAF1F8;
       --navy: #14263D; --muted: #4A5A6E;}
.block-container {max-width: 900px; padding-top: 2rem;}
[data-testid="stSidebar"] {background: #F2ECDF; border-right: 1px solid var(--line);}
h1 {font-size: 2.8rem !important; letter-spacing: -0.6px; margin-bottom: 0 !important; color: var(--navy) !important;}
h3 {color: var(--navy) !important;}
.g-eyebrow {display: inline-block; background: var(--blue-soft); color: var(--blue); font-weight: 700;
            font-size: 0.8rem; letter-spacing: 1.2px; text-transform: uppercase; padding: 4px 12px;
            border-radius: 999px; margin-bottom: 0.4rem;}
.g-sub {font-size: 1.12rem; color: var(--muted); margin: 0.3rem 0 1.2rem; line-height: 1.55;}
.g-sub b {color: var(--blue);}
[data-testid="stBaseButton-secondary"], button[kind="secondary"] {
    background: var(--card) !important; border: 1px solid #CFDCEC !important; color: var(--blue) !important;
    border-radius: 999px !important; font-weight: 600 !important;}
[data-testid="stBaseButton-secondary"]:hover, button[kind="secondary"]:hover {
    background: var(--blue-soft) !important; border-color: var(--blue) !important;}
[data-testid="stBaseButton-primary"], button[kind="primary"] {
    border-radius: 12px !important; font-weight: 700 !important; padding: 0.7rem 1rem !important;
    box-shadow: 0 6px 18px rgba(31, 95, 174, 0.22) !important;}
[data-testid="stVerticalBlockBorderWrapper"] {background: var(--card); border-color: var(--line) !important;
    border-radius: 14px !important; box-shadow: 0 1px 3px rgba(20, 38, 61, 0.06);}
[data-testid="stExpander"] details {background: var(--card); border-color: var(--line) !important; border-radius: 12px;}
.g-sos {background: #FDECEC; border: 2px solid #C5221F; border-radius: 14px; padding: 14px 18px;
        font-size: 1.2rem; font-weight: 700; color: #8A1C14; margin: 0.4rem 0 0.8rem;}
.g-pay {background: #FFF1D6; border-left: 4px solid #C77700; border-radius: 10px; padding: 10px 14px;
        font-weight: 600; color: #5C3600;}
.g-trust {font-size: 0.85rem; color: var(--muted);}
</style>""", unsafe_allow_html=True)


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


def run_understand(text: str):
    try:
        return understand(text, packages, default_classifier())
    except Exception:  # any surprise -> manual picker (fail closed)
        return None


def nice(name: str) -> str:
    """'ІВАНО-ФРАНКІВСЬКА' -> 'Івано-Франківська' (data is upper-case)."""
    return "-".join(part[:1] + part[1:].lower() for part in name.split("-"))


def region_label(region: str) -> str:
    return f"м. {nice(region[2:])}" if region.startswith("М.") else f"{nice(region)} обл."


def km(value: float) -> str:
    return f"{value:.1f} км".replace(".", ",")


def show_results(hits, package_id: str, origin) -> None:
    if not hits:
        st.warning("Поруч не знайдено закладів з цією послугою. "
                   f"Гаряча лінія НСЗУ {config.NSZU_HOTLINE} підкаже, куди звернутися.")
        return
    st.markdown(f"**Знайдено {len(hits)} закладів поруч** · найближчий — {km(hits[0].distance_km)}")
    df = pd.DataFrame([{"lat": h.facility.lat, "lng": h.facility.lng, "name": h.facility.division_name,
                        "addr": h.facility.address} for h in hits])
    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(latitude=origin[0], longitude=origin[1], zoom=11),
        layers=[
            pdk.Layer("ScatterplotLayer", df, get_position="[lng, lat]", get_radius=260,
                      get_fill_color=[31, 111, 235, 210], pickable=True),
            pdk.Layer("ScatterplotLayer", pd.DataFrame([{"lat": origin[0], "lng": origin[1]}]),
                      get_position="[lng, lat]", get_radius=180, get_fill_color=[220, 60, 40, 230]),
        ],
        tooltip={"text": "{name}\n{addr}"},
    ), height=320)
    for h in hits:
        f = h.facility
        with st.container(border=True):
            title, dist = st.columns([5, 1])
            title.markdown(f"**{f.division_name}**")
            dist.markdown(f"**{km(h.distance_km)}**")
            st.caption(f.legal_entity_name)
            links = [f"📍 {f.address}"]
            if f.phone:
                links.append(f"[📞 {f.phone}](tel:{f.phone.replace(' ', '')})")
            links.append(f"[🗺 Маршрут](https://www.google.com/maps/dir/?api=1&destination={f.lat},{f.lng})")
            st.markdown(" · ".join(links))
            if config.NEONATAL_PACKAGE_ID in f.package_ids and package_id != config.NEONATAL_PACKAGE_ID:
                st.caption("👶 є неонатальна допомога для складних випадків")


packages, facilities, rights, meta = load_all()
ss = st.session_state

# 1. Promise + need ---------------------------------------------------------------------------------
st.markdown('<span class="g-eyebrow">🩺 Безкоштовна медицина · дані НСЗУ</span>', unsafe_allow_html=True)
st.title("Гарантовано")
st.markdown('<p class="g-sub">Опишіть своїми словами, що вам потрібно, — покажемо найближчі заклади, '
            'де це <b>безкоштовно</b> за Програмою медичних гарантій, і що робити, якщо просять гроші.</p>',
            unsafe_allow_html=True)

cols = st.columns(len(config.EXAMPLES))
for col, (label, query) in zip(cols, config.EXAMPLES):
    if col.button(label, key=f"ex-{label}", use_container_width=True):
        ss.need = query
        ss.run_now = True  # one tap = search, never a stale result under a new question
text = st.text_area("Що вам потрібно?", key="need", height=90, max_chars=config.MAX_INPUT_CHARS,
                    placeholder="Напр.: «Мамі потрібна мамографія» або «Я вагітна, де народжувати?»")

# 2. Where --------------------------------------------------------------------------------------------
regions = sorted({f.region for f in facilities})
c1, c2, c3 = st.columns([1, 1, 1.3])
region = c1.selectbox("Область", regions, format_func=region_label,
                      index=regions.index(config.DEFAULT_REGION) if config.DEFAULT_REGION in regions else 0)
settlements = sorted({f.settlement for f in facilities if f.region == region})
default_city = region.removeprefix("М.")
settlement = c2.selectbox("Місто / село", settlements, format_func=nice,
                          index=settlements.index(default_city) if default_city in settlements else 0)
address = c3.text_input("Адреса (необов'язково)", placeholder="Оболонський проспект, 1")
st.caption("Адресу ми передаємо лише OpenStreetMap, щоб порахувати відстань.")

go = st.button("Знайти безкоштовну допомогу", type="primary", use_container_width=True)
if (go or ss.pop("run_now", False)) and text.strip():
    ss.result = run_understand(text)
    ss.searched_text = text
    ss.search_id = ss.get("search_id", 0) + 1  # fresh picker per search (#15)
if ss.get("searched_text") is not None and ss.searched_text != text:
    del ss["searched_text"]  # the question changed: hide answers to the old one

# 3. Answer -------------------------------------------------------------------------------------------
if "searched_text" in ss:
    result = ss.result
    if (result and result.emergency) or is_emergency_text(ss.searched_text):
        st.markdown(f'<div class="g-sos">🚑 Якщо зараз є загрозливі симптоми — дзвоніть '
                    f'{config.EMERGENCY_NUMBER}. Не їдьте самі.</div>', unsafe_allow_html=True)

    auto = [i for i in (result.package_ids if result and not result.needs_picker else ()) if i in packages]
    if not auto:
        st.info("Не вдалося точно визначити послугу — оберіть її зі списку.")
    ids = st.multiselect("Безкоштовні послуги за ПМГ" + (" · можна змінити" if auto else ""),
                         list(packages), default=auto, format_func=lambda i: packages[i].name,
                         key=f"picked-{ss.get('search_id', 0)}", max_selections=config.MAX_PACKAGES)

    if ids:
        centroid = settlement_centroid(facilities, region, settlement)
        geo = geocode(address.strip(), settlement) if address.strip() else None
        if address.strip() and geo is None:
            st.caption("Адресу не знайдено — рахуємо відстань від центру населеного пункту.")
        origin = geo or centroid
        # One tab per service: a facility never has to hold every package at once.
        tabs = st.tabs([packages[p].name[:42] for p in ids]) if len(ids) > 1 else [st.container()]
        for tab, pid in zip(tabs, ids):
            with tab:
                show_results(search(facilities, [pid], origin, region=region) if origin else [], pid, origin)

        st.subheader("Ваші права")
        for pid in ids:
            r = rights.get(pid)
            if not r:
                continue
            with st.expander(r["title"], expanded=pid == ids[0]):
                if r.get("emergency_note"):
                    st.error(r["emergency_note"])
                st.markdown(f"**Кому:** {r['eligible']}")
                st.markdown(f"**Направлення:** {r['referral_needed']}")
                for label, key in (("Що входить безкоштовно", "included"), ("Що взяти з собою", "bring")):
                    if r.get(key):
                        st.markdown(f"**{label}:**\n" + "\n".join(f"- {x}" for x in r[key]))
                st.markdown(f'<div class="g-pay">Просять гроші за цю послугу? Дзвоніть {config.NSZU_HOTLINE} '
                            '(НСЗУ) — це безкоштовно.</div>', unsafe_allow_html=True)
                if r.get("if_asked_to_pay"):
                    st.markdown("\n".join(f"- {x}" for x in r["if_asked_to_pay"]))
                srcs = r.get("sources") or []
                if srcs:
                    st.caption("Джерела: " + " · ".join(f"[{s.get('title') or s['url']}]({s['url']})" for s in srcs))
        st.caption(config.DISCLAIMER)

st.divider()
st.markdown(f'<p class="g-trust">Дані НСЗУ з data.gov.ua · зібрано {meta["built_at"][:10]} · '
            f'{meta["divisions_out"]} закладів · гаряча лінія НСЗУ {config.NSZU_HOTLINE}</p>',
            unsafe_allow_html=True)
