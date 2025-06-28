import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto("https://www.tab.co.nz/sports/table-tennis", timeout=60000)
        await page.wait_for_timeout(7000)  # wait extra long for all cards to load

        # Use broadest clickable selector (cursor-pointer divs under any grid)
        match_cards = await page.locator("div.cursor-pointer").all()
        print(f"📦 Found {len(match_cards)} clickable divs")

        matches_data = []

        for idx, match in enumerate(match_cards):
            try:
                text = await match.inner_text()
                print(f"\n🧪 Card {idx + 1}:\n{text}")

                if "Live" not in text:
                    continue

                print(f"🔍 Clicking live match {idx + 1}")
                await match.scroll_into_view_if_needed()
                await match.click()
                await page.wait_for_timeout(5000)

                players = await page.locator('[data-testid="competitor-name"]').all_inner_texts()
                odds = await page.locator('[data-testid="price-button-odds"]').all_inner_texts()
                markets = await page.locator('[data-testid="market-name"]').all_inner_texts()

                print(f"👤 Players: {players}")
                print(f"💰 Odds: {odds}")
                print(f"🧠 Markets: {markets}")

                if len(players) >= 2 and odds:
                    matches_data.append({
                        "Timestamp": datetime.now().isoformat(),
                        "Player 1": players[0],
                        "Player 2": players[1],
                        "Markets": "; ".join(markets),
                        "Raw Odds": "; ".join(odds)
                    })

                await page.go_back()
                await page.wait_for_timeout(3000)

            except Exception as e:
                print(f"❌ Error on card {idx + 1}: {e}")
                await page.go_back()
                await page.wait_for_timeout(3000)

        await browser.close()

        df = pd.DataFrame(matches_data)
        print("\n✅ FINAL TABLE TENNIS ODDS SNAPSHOT:")
        print(df.to_string(index=False))
        df.to_csv("live_tab_table_tennis.csv", index=False)

asyncio.run(main())