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
        time.sleep(5)

        # পেজের সমস্ত ম্যাচ পেজের লিংক ফিল্টার করা
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        match_links = set()
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/match/' in href or '/live/' in href or '/stream/' in href:
                full_url = href if href.startswith('http') else f"https://cricketlounge.tv{href}"
                match_links.add(full_url)

        print(f"Scanned {len(match_links)} links for live players...")

        for link in match_links:
            try:
                driver.get(link)
                time.sleep(4)  # প্লেয়ার এবং iFrame লোড হতে সময় দেওয়া
                
                page_source = driver.page_source
                
                # iFrame বা মূল সোর্স কোড থেকে Decimal Sports প্লেয়ার আইডি খুঁজে বের করা
                id_match = re.search(r'decimalsports\.com/embeddedplayer/\?id=([a-zA-Z0-9]+)', page_source)
                
                # যদি ইমবেড প্লেয়ার আইডি পাওয়া যায়, কেবল তখনই ম্যাচটি যুক্ত করা হবে
                if id_match:
                    decimal_id = id_match.group(1)
                    inner_soup = BeautifulSoup(page_source, 'html.parser')

                    # টাইটেল সংগ্রহ
                    title_elem = inner_soup.find('h1') or inner_soup.find('h2') or inner_soup.find('title')
                    title = title_elem.get_text(strip=True).replace(" - Cricket Lounge", "").strip() if title_elem else "Live Match"

                    # ইমেজ/থাম্বনেইল সংগ্রহ
                    img_elem = inner_soup.find('img')
                    img_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else ""

                    # একটিভ ম্যাচ তৈরি
                    active_matches.append({
                        "match_name": title,
                        "status": "Live",
                        "image": img_url,
                        "player_url": f"https://www.decimalsports.com/embeddedplayer/?id={decimal_id}",
                        "match_link": link
                    })
                    print(f"[FOUND LIVE MATCH] {title} | ID: {decimal_id}")
                else:
                    print(f"[NO PLAYER FOUND] Skipping {link}")

            except Exception as e:
                print(f"Error checking link {link}: {e}")

        # JSON ফাইল সম্পূর্ণ নতুন তথ্য দিয়ে রাইট করা (পুরনো বা বাদ পড়া ম্যাচ অটো ডিলিট হয়ে যাবে)
        with open("matches.json", "w", encoding="utf-8") as f:
            json.dump(active_matches, f, ensure_ascii=False, indent=2)

        print(f"Successfully saved {len(active_matches)} active live matches.")

    except Exception as e:
        print(f"Scraper error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_cricket_lounge()
