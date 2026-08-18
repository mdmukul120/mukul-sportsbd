import re
import json
import requests
from bs4 import BeautifulSoup

def scrape_cricket_lounge():
    url = "https://cricketlounge.tv/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        matches = []

        # পেজের সমস্ত লিঙ্ক ও কার্ড স্ক্র্যান করা
        for card in soup.find_all(['div', 'a'], class_=re.compile(r'card|match|item', re.I)):
            # ম্যাচের নাম
            title_elem = card.find(['h2', 'h3', 'h4', 'p', 'span'], class_=re.compile(r'title|name|team', re.I))
            title = title_elem.get_text(strip=True) if title_elem else None

            # ইমেজ URL
            img_elem = card.find('img')
            img_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else None

            # প্লেয়ার URL বা আইডি
            link_elem = card if card.name == 'a' else card.find('a')
            match_link = link_elem.get('href') if link_elem else None

            # যদি প্লেয়ার আইডি সরাসরি বা ম্যাচের লিংকে থাকে
            decimal_id = None
            if match_link:
                if not match_link.startswith('http'):
                    match_link = f"https://cricketlounge.tv{match_link}"
                
                try:
                    sub_res = requests.get(match_link, headers=headers, timeout=10)
                    id_match = re.search(r'decimalsports\.com/embeddedplayer/\?id=([a-zA-Z0-9]+)', sub_res.text)
                    if id_match:
                        decimal_id = id_match.group(1)
                except Exception:
                    pass

            if title and decimal_id:
                player_url = f"https://www.decimalsports.com/embeddedplayer/?id={decimal_id}"
                matches.append({
                    "match_name": title,
                    "image": img_url,
                    "player_url": player_url
                })

        # JSON ফাইলে ডাটা সেভ করা
        with open("matches.json", "w", encoding="utf-8") as f:
            json.dump(matches, f, ensure_ascii=False, indent=2)
            
        print(f"Successfully scraped {len(matches)} matches.")

    except Exception as e:
        print(f"Error scraping data: {e}")

if __name__ == "__main__":
    scrape_cricket_lounge()
