# scraper.py

import asyncio
from playwright.async_api import async_playwright
import csv
import os

OUTPUT_FILE = "herrenlose_parzellen_aargau.csv"
GEMEINDEN = [
    "Aarau", "Baden", "Brugg", "Lenzburg", "Zofingen", "Wettingen", "Möhlin", "Oftringen",
    "Rheinfelden", "Wohlen", "Frick", "Klingnau", "Kaisten", "Kölliken", "Sins", "Spreitenbach"
]

async def scrape_parzellen():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        results = []
        for gemeinde in GEMEINDEN:
            try:
                print(f"🔍 Suche in {gemeinde}...")
                await page.goto("https://www.ag.ch/de/dfr/geoportal/geoportal.jsp", timeout=60000)
                await page.fill("input[type='search']", gemeinde)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(3000)  # warte auf Ladezeit

                content = await page.content()
                if "EGRID" not in content or "Eigentümer" not in content:
                    print(f"❓ Möglicherweise herrenlos in {gemeinde}")
                    results.append({
                        "Gemeinde": gemeinde,
                        "Status": "Verdacht: keine EGRID/Eigentümer",
                        "Link": page.url
                    })
                else:
                    print(f"✅ Eigentümerdaten vorhanden in {gemeinde}")
            except Exception as e:
                print(f"⚠️ Fehler in {gemeinde}: {e}")
                results.append({
                    "Gemeinde": gemeinde,
                    "Status": f"Fehler: {e}",
                    "Link": ""
                })

        # Exportieren
        keys = results[0].keys()
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)

        print(f"✅ Fertig! Datei gespeichert als {OUTPUT_FILE}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_parzellen())
