"""Local visual check: python -m http.server 8765 -d public, then run with a python that has playwright."""
import sys, os
from playwright.sync_api import sync_playwright
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8765"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "screenshots")
os.makedirs(OUT, exist_ok=True)
PAGES = ["index", "methodology", "record", "card", "live", "episodes", "shorts"]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    for label, vp in (("mobile", {"width": 390, "height": 844}), ("desktop", {"width": 1366, "height": 900})):
        ctx = b.new_context(viewport=vp, device_scale_factor=1 if label == "desktop" else 2)
        pg = ctx.new_page()
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        for name in PAGES:
            pg.goto(f"{BASE}/{name}.html", wait_until="networkidle")
            sw = pg.evaluate("document.documentElement.scrollWidth")
            pg.screenshot(path=f"{OUT}/{name}-{label}.png", full_page=True)
            print(f"{name}-{label}: scrollWidth={sw} (viewport {vp['width']})", "OVERFLOW" if sw > vp["width"] else "")
        if errs: print("console errors:", errs)
        ctx.close()
    b.close()
