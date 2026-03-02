import os
import json
import time
import datetime
import feedparser
import requests
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 설정
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
STATE_FILE = "last_seen.json"

RSS_FEEDS = {
    "방통위": "https://www.korea.kr/rss/dept_kmcc.xml",
    "공정위": "https://www.korea.kr/rss/dept_ftc.xml",
    "개보위": "https://www.korea.kr/rss/dept_pipc.xml"
}

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=4)

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram configuration is missing.")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending telegram message: {e}")

def check_rss():
    state = load_state()
    new_state = state.copy()
    
    for name, url in RSS_FEEDS.items():
        print(f"Checking {name} RSS...")
        try:
            feed = feedparser.parse(url)
            last_link = state.get(name)
            
            # 피드에서 새로운 항목들 찾기 (위에서 아래로 최신순인 경우)
            new_entries = []
            for entry in feed.entries:
                if entry.link == last_link:
                    break
                new_entries.append(entry)
            
            # 최근 항목이 하나라도 있으면 업데이트
            if feed.entries:
                new_state[name] = feed.entries[0].link
            
            # 새로운 항목이 있으면 텔레그램으로 전송 (오래된 것부터)
            for entry in reversed(new_entries):
                message = f"<b>[{name} 보도자료]</b>\n\n{entry.title}\n\n<a href='{entry.link}'>바로가기</a>"
                send_telegram_message(message)
                print(f"Sent: {entry.title}")
                
        except Exception as e:
            print(f"Error parsing {name} RSS: {e}")
            
    save_state(new_state)

def is_work_time():
    now = datetime.datetime.now()
    # 요일 체크 (0=월, 1=화, ..., 4=금, 5=토, 6=일)
    if now.weekday() >= 5:
        return False
    
    # 시간 체크 (08:00 ~ 19:00)
    current_hour = now.hour
    if 8 <= current_hour < 19:
        return True
    
    return False

def main():
    print("RSS Pusher Agent started for GitHub Actions.")
    
    # 작업 시간 체크 (평일 08:00 ~ 19:00)
    # GitHub Actions의 Cron은 UTC 기준이므로 코드 내에서 현지 시간(KST) 체크가 안전함
    if not is_work_time():
        print(f"[{datetime.datetime.now()}] Outside working hours. Skipping check.")
        return

    # 첫 실행 시 현재 상태를 저장
    if not os.path.exists(STATE_FILE):
        print("Initializing state file...")
        state = {}
        for name, url in RSS_FEEDS.items():
            try:
                feed = feedparser.parse(url)
                if feed.entries:
                    state[name] = feed.entries[0].link
            except Exception as e:
                print(f"Error initializing {name}: {e}")
        save_state(state)
        print("State initialized. Monitoring will start from next run.")
        return

    print(f"[{datetime.datetime.now()}] Checking feeds...")
    check_rss()

if __name__ == "__main__":
    main()
