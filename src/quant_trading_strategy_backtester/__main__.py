"""Entry point for running the Streamlit application via ``python -m``."""

from . import app

if __name__ == "__main__":
    import os
    import sys

    import streamlit.web.cli as stcli

    sys.argv = ["streamlit", "run", os.path.abspath(app.__file__)]
    sys.exit(stcli.main())
