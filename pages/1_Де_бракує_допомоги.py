"""Streamlit presentation of NSZU access calculations. OWNER: Діма (#5)."""
from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from garantovano import data
from garantovano.analytics import analyze_access
from garantovano.models import Facility, Package


st.set_page_config(page_title="Де бракує допомоги — Гарантовано", page_icon="📊", layout="wide")


@st.cache_data(show_spinner=False)
def load_inputs() -> tuple[dict[str, Package], list[Facility], dict]:
    return data.load_packages(), data.load_facilities(), data.load_meta()


@st.cache_data(show_spinner="Рахуємо відстані до найближчих закладів…")
def load_report(package_id: str, threshold_km: float) -> tuple[dict[str, float], float | None, float | None]:
    _, facilities, _ = load_inputs()
    return analyze_access(facilities, package_id, threshold_km=threshold_km)


st.title("Де бракує допомоги")
st.write(
    "Порівнюємо відстань від точок первинної допомоги до найближчих закладів, "
    "які мають договір з НСЗУ за обраним пакетом."
)
st.caption(
    "Наш розрахунок за відкритими даними НСЗУ; відстань по прямій; "
    "точки первинки — наближення, не населення."
)

try:
    packages, facilities, meta = load_inputs()
except (OSError, ValueError, KeyError):
    st.error("Не вдалося завантажити дані для аналітики. Спробуйте пізніше.")
    st.stop()

package_options = [pid for pid in ("5", "6", "7") if pid in packages]
if not package_options:
    st.info("У поточному наборі даних немає пакетів для цього порівняння.")
    st.stop()

package_id = st.selectbox(
    "Вид допомоги",
    package_options,
    index=package_options.index("6") if "6" in package_options else 0,
    format_func=lambda pid: packages[pid].name,
)
threshold_km = 50.0

try:
    regions, national_share, median_km = load_report(package_id, threshold_km)
except ValueError:
    st.info("У поточному наборі даних немає закладів з обраним пакетом для порівняння.")
    st.stop()

st.caption(f"НСЗУ · дані зібрано {meta['built_at'][:10]}")
if national_share is None or median_km is None:
    st.info("У поточному наборі даних немає точок первинки для розрахунку.")
else:
    share_column, distance_column = st.columns(2)
    share_column.metric(
        f"Точок первинки далі ніж за {threshold_km:g} км",
        f"{national_share:.1%}".replace(".", ","),
    )
    distance_column.metric(
        "Медіанна відстань до допомоги",
        f"{median_km:.1f} км".replace(".", ","),
    )
    st.subheader("Віддаленість за областями")
    chart_data = pd.DataFrame({"Область": list(regions), "Частка": list(regions.values())})
    chart = (
        alt.Chart(chart_data)
        .mark_bar(color="#16756b")
        .encode(
            x=alt.X(
                "Частка:Q",
                title=f"Частка точок первинки далі ніж за {threshold_km:g} км",
                axis=alt.Axis(format=".0%"),
                scale=alt.Scale(domain=[0, 1]),
            ),
            y=alt.Y("Область:N", sort="-x", title=None),
            tooltip=[alt.Tooltip("Область:N"), alt.Tooltip("Частка:Q", format=".1%")],
        )
        .properties(height=alt.Step(25))
    )
    st.altair_chart(chart, width="stretch")
    st.caption(
        "Для кожної точки первинки шукаємо найближчий заклад по всій Україні, "
        "зокрема в сусідній області. Відстань не враховує дороги, час у дорозі "
        "та фактичну можливість отримати допомогу сьогодні."
    )

st.divider()
st.markdown(
    "Джерела НСЗУ на data.gov.ua: "
    f"[договори за пакетами]({meta['sources']['contracts']}) · "
    f"[підрозділи та координати]({meta['sources']['divisions']}) · "
    f"[перелік пакетів]({meta['sources']['packages']})"
)
