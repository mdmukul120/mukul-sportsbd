import re
import json
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# আপকামিং ম্যাচের জন্য ডিফল্ট ভিডিও লিংক
UPCOMING_VIDEO_URL = "Https://dtvoeevhaseb5.cloudfront.net/user-uploads/68a11d79-b983-42a8-8181-0d356a132d6a.mp4"

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
        time.sleep(5)

        # পেজ সম্পূর্ণ নিচে স্ক্রোল করে সব কার্ড লোড করা
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # পেজের সমস্ত ম্যাচ পেজের লিংক ফিল্টার করা
        match_links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/match/' in href or '/live/' in href or '/stream/' in href:
                full_url = href if href.startswith('http') else f"https://cricketlounge.tv{href}"
                match_links.add(full_url)

        print(f"Total Matches Found: {len(match_links)}")

        for link in match_links:
            try:
                driver.get(link)
                time.sleep(4)
                
                page_source = driver.page_source
                inner_soup = BeautifulSoup(page_source, 'html.parser')

                # ১. ম্যাচের নাম বের করা
                title_elem = inner_soup.find('h1') or inner_soup.find('h2') or inner_soup.find('title')
                title = title_elem.get_text(strip=True).replace(" - Cricket Lounge", "").strip() if title_elem else "Cricket Match"

                # ২. ইমবেড প্লেয়ার আইডি খোঁজা (Decimal Sports)
                decimal_id = None
                id_match = re.search(r'decimalsports\.com/embeddedplayer/\?id=([a-zA-Z0-9]+)', page_source)
                if id_match:
                    decimal_id = id_match.group(1)

                # ৩. ম্যাচের স্ট্যাটাস নির্ধারণ করা (Live, Upcoming, Recent)
                status = "Upcoming"
                if re.search(r'match ended|completed|finished|result', page_source, re.IGNORECASE):
                    status = "Recent / Ended"
                elif decimal_id or re.search(r'live', page_source, re.IGNORECASE):
                    status = "Live"

                # ৪. আপকামিং ম্যাচের স্টার্ট টাইম বের করা
                start_time = "TBD"
                time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM)?(?:\s*UTC|\s*GMT)?)', page_source, re.IGNORECASE)
                date_match = re.search(r'(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b)', page_source, re.IGNORECASE)
                
                if time_match and date_match:
                    start_time = f"{date_match.group(1)} at {time_match.group(1)}"
                elif time_match:
                    start_time = time_match.group(1)

                # ৫. ছবি/থাম্বনেইল বের করা
                img_elem = inner_soup.find('img')
                img_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else ""

                # ৬. প্লেয়ার ইউআরএল লজিক
                if status == "Live" and decimal_id:
                    player_url = f"https://www.decimalsports.com/embeddedplayer/?id={decimal_id}"
                elif status == "Upcoming":
                    player_url = UPCOMING_VIDEO_URL
                else:
                    player_url = f"https://www.decimalsports.com/embeddedplayer/?id={decimal_id}" if decimal_id else "N/A"

                matches.append({
                    "match_name": title,
                    "status": status,
                    "start_time": start_time,
                    "image": img_url,
                    "player_url": player_url,
                    "match_link": link
                })

                print(f"Scraped: {title} | Status: {status} | Start Time: {start_time}")

            except Exception as e:
                print(f"Error scraping match {link}: {e}")

        # JSON ফাইলে সব ডাটা সেভ করা
        with open("matches.json", "w", encoding="utf-8") as f:
            json.dump(matches, f, ensure_ascii=False, indent=2)

        print(f"Successfully saved {len(matches)} matches to matches.json")

    except Exception as e:
        print(f"Scraper error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_cricket_lounge()
