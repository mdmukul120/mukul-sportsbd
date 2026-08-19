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
    active_matches = []

    try:
        main_url = "https://cricketlounge.tv/"
        driver.get(main_url)
        time.sleep(5)  # JS সম্পূর্ণ লোড হওয়ার জন্য সময় দেয়া

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # পেজের সমস্ত লিঙ্ক স্ক্যান করা
        match_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            # ম্যাচ সংক্রান্ত পেজ ফিল্টার করা
            if '/match/' in href or '/live/' in href:
                full_url = href if href.startswith('http') else f"https://cricketlounge.tv{href}"
                if full_url not in match_links:
                    match_links.append(full_url)

        print(f"Found {len(match_links)} potential match links.")

        # প্রতিটি ম্যাচের পেজে প্রবেশ করে লাইভ/আপকামিং ম্যাচ ফিল্টার করা
        for link in match_links:
            try:
                driver.get(link)
                time.sleep(3)
                
                page_source = driver.page_source
                match_soup = BeautifulSoup(page_source, 'html.parser')
                
                # যদি ম্যাচে "Match Ended" বা "Completed" লেখা থাকে তবে এড়িয়ে যাওয়া (Auto Delete Logic)
                is_ended = re.search(r'match ended|completed|result|finished', page_source, re.IGNORECASE)
                if is_ended:
                    print(f"Skipping finished match: {link}")
                    continue

                # ম্যাচের নাম সংগ্রহ
                title_elem = match_soup.find('h1') or match_soup.find('h2') or match_soup.find('title')
                title = title_elem.get_text(strip=True) if title_elem else "Cricket Match"
                title = title.replace(" - Cricket Lounge", "").strip()

                # থাম্বনেইল বা ইমেজ সংগ্রহ
                img_elem = match_soup.find('img')
                img_url = img_elem.get('src') if img_elem else ""

                # Decimal Sports Embedded Player ID বের করা
                decimal_id = None
                id_match = re.search(r'decimalsports\.com/embeddedplayer/\?id=([a-zA-Z0-9]+)', page_source)
                
                if id_match:
                    decimal_id = id_match.group(1)

                # শুধু এক্টিভ ও প্লেয়ার আইডি যুক্ত ম্যাচগুলো লিস্টে রাখা
                if decimal_id:
                    active_matches.append({
                        "match_name": title,
                        "image": img_url,
                        "player_url": f"https://www.decimalsports.com/embeddedplayer/?id={decimal_id}",
                        "status": "Active"
                    })
            except Exception as inner_e:
                print(f"Error processing {link}: {inner_e}")

        # JSON ফাইল আপডেট করা (পুরনো বা বাদ পড়া ম্যাচ অটোমেটিক রিমুভ হয়ে যাবে)
        with open("matches.json", "w", encoding="utf-8") as f:
            json.dump(active_matches, f, ensure_ascii=False, indent=2)

        print(f"Successfully saved {len(active_matches)} active matches.")

    except Exception as e:
        print(f"Main scraper failed: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_cricket_lounge()
