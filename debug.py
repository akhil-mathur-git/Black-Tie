#WORKING BUT NEED TO ADD CORRECT SCORE


import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto("https://www.tab.co.nz/sports/table-tennis#inplay", timeout=60000)
        await page.wait_for_timeout(6000)

        match_cards = await page.locator("div.cursor-pointer").all()
        print(f"📦 Found {len(match_cards)} possible matches")

        data = []
        found_live = False
        found_valid_odds = False

        for idx, match in enumerate(match_cards):
            try:
                text = await match.inner_text()
                if "Live" not in text:
                    continue

                found_live = True
                print(f"\n🎯 Clicking match {idx + 1}: Live")
                await match.scroll_into_view_if_needed()
                await match.click()
                await page.wait_for_timeout(5000)

                await page.wait_for_selector('[data-testid="market-accordion-header"]', timeout=10000)

                market_headers = await page.locator('[data-testid="market-accordion-header"]').all()
                target_index = -1
                for i, header in enumerate(market_headers):
                    try:
                        name = await header.inner_text()
                        if "Set" in name and "Set Betting" in name:
                            print(f"🧩 Expanding: {name}")
                            await header.click()
                            await page.wait_for_timeout(1000)
                            target_index = i
                            break
                    except:
                        continue

                if target_index == -1:
                    print("⚠️ No 'Set' betting market found.")
                    await page.go_back()
                    await page.wait_for_timeout(2000)
                    continue

                # Get player names from label spans
                try:
                    labels = await page.locator("span.pricebutton-label").all_inner_texts()
                    player_labels = [name.strip() for name in labels if name.strip() and any(c.isalpha() for c in name)]
                    unique_players = []
                    for name in player_labels:
                        if name not in unique_players:
                            unique_players.append(name)
                        if len(unique_players) == 2:
                            break
                    if len(unique_players) < 2:
                        raise Exception("Only one player found")
                    players = unique_players
                    print(f"👥 Players: {players}")
                except:
                    print("❌ Failed to extract players from odds section")
                    await page.go_back()
                    await page.wait_for_timeout(2000)
                    continue

                # 🧠 Scope specifically to the Set Betting odds only
                market_header_handle = await market_headers[target_index].evaluate_handle(
                    "header => header.closest('[data-testid^=market-container]')"
                )
                set_block = await market_header_handle.query_selector(".accordion__content")

                if not set_block:
                    print("❌ Set betting block not found")
                    await page.go_back()
                    await page.wait_for_timeout(2000)
                    continue

                odds_spans = await set_block.query_selector_all('[data-testid="price-button-odds"]')
                raw_odds = []
                for span in odds_spans:
                    text = await span.inner_text()
                    if text.upper() != "SUS":
                        raw_odds.append(text)

                if not raw_odds:
                    print("🚫 No valid odds (all SUS)")
                    await page.go_back()
                    await page.wait_for_timeout(3000)
                    continue

                found_valid_odds = True
                print(f"💰 Odds: {raw_odds}")

                data.append({
                    "Timestamp": datetime.now().isoformat(),
                    "Player 1": players[0],
                    "Player 2": players[1],
                    "Set Betting Odds": "; ".join(raw_odds)
                })

                await page.go_back()
                await page.wait_for_timeout(3000)

            except Exception as e:
                print(f"❌ Error in match {idx + 1}: {e}")
                await page.go_back()
                await page.wait_for_timeout(3000)

        await browser.close()

        if not found_live:
            print("🚫 No live matches found")
        elif not found_valid_odds:
            print("🚫 No valid set betting odds found (all SUS)")

        df = pd.DataFrame(data)
        print("\n📅 Final Data:")
        print(df.to_string(index=False))
        df.to_csv("live_tab_set_betting.csv", index=False)

asyncio.run(main())
