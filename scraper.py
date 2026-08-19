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
        time.sleep(6)  # পেজ লোড হওয়ার জন্য অপেক্ষা

        # পেজ সম্পূর্ণ নিচে স্ক্রোল করা যাতে লেজি-লোড হওয়া ম্যাচগুলোও চলে আসে
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # পেজের সমস্ত লিঙ্ক ফিল্টার করা
        match_links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/match/' in href or '/live/' in href or '/stream/' in href:
                full_url = href if href.startswith('http') else f"https://cricketlounge.tv{href}"
                match_links.add(full_url)

        print(f"Total Match Links Found: {len(match_links)}")

        for link in match_links:
            try:
                driver.get(link)
                time.sleep(4)  # প্লেয়ার এবং তথ্য লোড হওয়ার জন্য সময়
                
                inner_source = driver.page_source
                inner_soup = BeautifulSoup(inner_source, 'html.parser')

                # ১. ম্যাচের নাম বের করা
                title = "Unknown Match"
                title_elem = inner_soup.find('h1') or inner_soup.find('h2') or inner_soup.find('title')
                if title_elem:
                    title = title_elem.get_text(strip=True).replace(" - Cricket Lounge", "").strip()

                # ২. ম্যাচের স্ট্যাটাস চেক করা (Live, Upcoming, Ended)
                status = "Upcoming / Live"
                if re.search(r'match ended|completed|finished|result', inner_source, re.IGNORECASE):
                    status = "Ended"
                elif re.search(r'live', inner_source, re.IGNORECASE):
                    status = "Live"

                # ৩. ইমেজ URL সংগ্রহ
                img_url = ""
                img_elem = inner_soup.find('img')
                if img_elem:
                    img_url = img_elem.get('src') or img_elem.get('data-src') or ""

                # ৪. Decimal Sports Embedded Player ID বের করা
                decimal_id = None
                id_match = re.search(r'decimalsports\.com/embeddedplayer/\?id=([a-zA-Z0-9]+)', inner_source)
                
                if id_match:
                    decimal_id = id_match.group(1)

                # ডাটা যুক্ত করা (যদি প্লেয়ার লিংক না-ও পাওয়া যায়, তবুও আপকামিং বা শেষ হওয়া ম্যাচগুলোর লিস্ট থাকবে)
                player_url = f"https://www.decimalsports.com/embeddedplayer/?id={decimal_id}" if decimal_id else "N/A"

                matches.append({
                    "match_name": title,
                    "status": status,
                    "image": img_url,
                    "player_url": player_url,
                    "match_link": link
                })

                print(f"Scraped: {title} | Status: {status} | Player URL: {player_url}")

            except Exception as e:
                print(f"Error scraping match link {link}: {e}")

        # JSON ফাইলের তথ্য আপডেট
        with open("matches.json", "w", encoding="utf-8") as f:
            json.dump(matches, f, ensure_ascii=False, indent=2)

        print(f"Total Scraped Matches Saved: {len(matches)}")

    except Exception as e:
        print(f"Main Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_cricket_lounge()
