import asyncio
from playwright.async_api import async_playwright, Error
import random
import logging
import os

logging.basicConfig(level=logging.INFO)

class AdvancedScraper:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        ]

    async def create_browser_context(self, playwright):
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=random.choice(self.user_agents),
        )
        return browser, context

    async def simulate_human_behavior(self, page):
        await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
        await page.evaluate("""
            window.scrollTo({
                top: Math.floor(Math.random() * window.innerHeight),
                behavior: 'smooth'
            });
        """)
        await asyncio.sleep(random.uniform(1, 3))

    async def download_html(self, page, file_name):
        os.makedirs('downloaded_htmls', exist_ok=True)
        file_path = os.path.join('downloaded_htmls', file_name)
        
        try:
            content = await page.content()
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            logging.info(f"Downloaded HTML content to {file_name}")
        except Error as e:
            logging.error(f"Error during HTML download: {e}")

    async def scrape_case_links(self, page, base_url):
        await page.goto(base_url, wait_until="domcontentloaded")
        await self.simulate_human_behavior(page)

        case_links = await page.query_selector_all('a.ng-binding[href^="cases/"]')
        logging.info(f"Found {len(case_links)} case links.")

        for idx, case_link in enumerate(case_links):
            try:
                case_url = await case_link.get_attribute('href')
                logging.info(f"Case URL: {case_url}")
                case_url = f"https://www.oyez.org/{case_url}"
                
                new_page = await page.context.new_page()
                await new_page.goto(case_url, wait_until="domcontentloaded")
                await self.simulate_human_behavior(new_page)

                syllabus_link = await new_page.query_selector('a.ng-binding[title="Syllabus"]')
                if syllabus_link:
                    await syllabus_link.click()
                    await new_page.wait_for_load_state('domcontentloaded')
                    file_name = f"case_{idx+1}_syllabus.html"
                    await self.download_html(new_page, file_name)

                await new_page.close()

            except Exception as e:
                logging.error(f"Error navigating to or scraping case link: {e}")
                continue

    async def run(self, base_url):
        async with async_playwright() as p:
            browser, context = await self.create_browser_context(p)
            page = await context.new_page()

            try:
                await self.scrape_case_links(page, base_url)
                return "Scraping completed successfully."

            except Exception as e:
                logging.error(f"Error during scraping: {e}")
                return None
            finally:
                await browser.close()

async def main():
    scraper = AdvancedScraper()
    base_url = "https://www.oyez.org/issues/195"
    result = await scraper.run(base_url)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
