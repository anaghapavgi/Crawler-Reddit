"""Dashboard entrypoint scaffold."""

from __future__ import annotations

import streamlit as st


def main() -> None:
    """Render scaffold home page."""
    st.set_page_config(page_title="Reddit Product Intelligence", layout="wide")
    st.title("Reddit Product Intelligence")
    st.info("Dashboard scaffold in progress. Demo-mode pages will be added in later phases.")


if __name__ == "__main__":
    main()
