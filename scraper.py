import re
import json
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def scrape_cricket_lounge():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    matches = []

    try:
        main_url = "https://cricketlounge.tv/"
        driver.get(main_url)
        time.sleep(5)  # JavaScript লোড হওয়ার সময় দেওয়া

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # পেজের সমস্ত অ্যাঙ্কর (a) ট্যাগ থেকে লাইভ ম্যাচের লিংক খোঁজা
        match_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/match/' in href or '/live/' in href:
                full_url = href if href.startswith('http') else f"https://cricketlounge.tv{href}"
                if full_url not in match_links:
                    match_links.append(full_url)

        print(f"Found {len(match_links)} match pages.")

        # প্রতিটি ম্যাচের পেজে ঢুকে মূল তথ্য বের করা
        for link in match_links:
            driver.get(link)
            time.sleep(3)
            match_soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # ম্যাচের টাইটেল খোঁজা
            title_elem = match_soup.find('h1') or match_soup.find('h2') or match_soup.find('title')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Match"

            # ইমেজ URL খোঁজা
            img_elem = match_soup.find('img')
            img_url = img_elem.get('src') if img_elem else ""

            # Decimal Sports এর প্লেয়ার আইডি বের করা
            decimal_id = None
            page_text = driver.page_source
            id_match = re.search(r'decimalsports\.com/embeddedplayer/\?id=([a-zA-Z0-9]+)', page_text)
            
            if id_match:
                decimal_id = id_match.group(1)

            if decimal_id:
                matches.append({
                    "match_name": title,
                    "image": img_url,
                    "player_url": f"https://www.decimalsports.com/embeddedplayer/?id={decimal_id}"
                })

        # JSON সেভ
        with open("matches.json", "w", encoding="utf-8") as f:
            json.dump(matches, f, ensure_ascii=False, indent=2)

        print(f"Scraped {len(matches)} matches successfully.")

    except Exception as e:
        print(f"Scraping failed: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_cricket_lounge()
