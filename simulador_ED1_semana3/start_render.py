"""Render proporciona PORT. Flet espera FLET_SERVER_PORT para ft.run()."""
import os
import runpy
os.environ["FLET_SERVER_PORT"] = os.environ.get("PORT", "10000")
os.environ["FLET_SERVER_IP"] = "0.0.0.0"
os.environ["FLET_FORCE_WEB_SERVER"] = "true"
os.environ["ENVIRONMENT"] = "production"
runpy.run_path("main.py", run_name="__main__")
