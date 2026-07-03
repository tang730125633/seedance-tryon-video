#!/usr/bin/env python3
"""把 HTML 渲染成长图 PNG（Playwright/Chromium，2x 高清）。一般由 make_poster.py 调用。"""
import sys, asyncio
from playwright.async_api import async_playwright
HTML = sys.argv[1]; OUT = sys.argv[2]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 824, "height": 1200}, device_scale_factor=2)
        await pg.goto("file://" + HTML, wait_until="networkidle")
        try:
            await pg.wait_for_function("window.__fontsready===true", timeout=15000)
        except Exception:
            pass
        await pg.wait_for_timeout(1500)
        elt = await pg.query_selector("#poster")
        await elt.screenshot(path=OUT)
        await b.close()
        print("rendered", OUT)
asyncio.run(main())
