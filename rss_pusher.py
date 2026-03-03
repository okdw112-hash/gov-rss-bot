import os
import json
import datetime
import feedparser
import requests

# 설정 (GitHub Secrets에서 가져옴)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
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
        print("❌ Telegram configuration is missing.")
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
        print(f"❌ Error sending telegram message: {e}")

def is_work_time():
    # GitHub Actions의 서버 시간(UTC)을 한국 시간(KST, UTC+9)으로 변환
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_kst = now_utc + datetime.timedelta(hours=9)
    
    # 요일 체크 (0=월, ..., 4=금)
    if now_kst.weekday() >= 5:
        print(f"[{now_kst}] 주말입니다. 건너뜁니다.")
        return False

    # 시간 체크 (08:00 ~ 19:00)
    current_hour = now_kst.hour
    print(f"현재 한국 시간: {now_kst}")
    
    if 8 <= current_hour < 19:
        return True

    print("영업 시간(08-19시) 외 시간입니다. 건너뜁니다.")
    return False

def check_rss():
    state = load_state()
    new_state = state.copy()
    found_any_new = False

    for name, url in RSS_FEEDS.items():
        print(f"Checking {name} RSS...")
        try:
            feed = feedparser.parse(url)
            last_link = state.get(name)

            new_entries = []
            for entry in feed.entries:
                if entry.link == last_link:
                    break
                new_entries.append(entry)

            if feed.entries:
                new_state[name] = feed.entries[0].link

            for entry in reversed(new_entries):
                message = f"<b>[{name} 보도자료]</b>\n\n{entry.title}\n\n<a href='{entry.link}'>바로가기</a>"
                send_telegram_message(message)
                print(f"✅ Sent: {entry.title}")
                found_any_new = True

        except Exception as e:
            print(f"❌ Error parsing {name} RSS: {e}")

    if not found_any_new:
        print("최신 보도자료가 없습니다. 텔레그램을 보내지 않습니다.")
    
    save_state(new_state)

def main():
    print("🚀 RSS Pusher Agent started.")

    if not is_work_time():
        return

    # 첫 실행 시 초기화 로직
    if not os.path.exists(STATE_FILE):
        print("Initializing state file...")
        state = {}
        for name, url in RSS_FEEDS.items():
            try:
                feed = feedparser.parse(url)
                if feed.entries:
                    state[name] = feed.entries[0].link
            except Exception as e:
                print(f"Error: {e}")
        save_state(state)
        # 테스트를 위해 초기화 시점에 메시지 하나 발송
        send_telegram_message("✅ RSS 알림 비서가 정상적으로 활성화되었습니다.")
        return

    check_rss()

if __name__ == "__main__":
    main()
