"""Optional framework-neutral Streamlit comparison surface for Day 11."""

import streamlit as st

st.set_page_config(page_title="Agentic PM Lab", layout="wide")
st.title("Agentic PM Lab — local comparison view")
st.warning(
    "Learning surface using mock portfolio data; no trades or investment advice."
)
st.subheader("Portfolio risk snapshot")
st.metric("Market value", "$1.25m")
st.metric("Volatility", "12.3%")
st.metric("Maximum drawdown", "-7.4%")
st.caption(
    "Canvas and API remain the primary integration paths. This Streamlit view exists only to compare UI frameworks."
)
