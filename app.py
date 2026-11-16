"""Entry point (Streamlit Cloud runs this file): page navigation with human-readable labels only."""
import streamlit as st

st.navigation([
    st.Page("home.py", title="Пошук допомоги", icon="🩺", default=True),
    st.Page("pages/1_Де_бракує_допомоги.py", title="Де бракує допомоги", icon="📊"),
]).run()
