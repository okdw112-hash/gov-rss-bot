# RSS to Telegram Pusher

이 에이전트는 월~금, 08:00~19:00 사이에 30분 간격으로 지정된 위원회의 RSS 보도자료를 체크하여 새로운 글이 올라오면 텔레그램으로 전송합니다.

## GitHub Actions 설정 방법 (추천)

이 방법은 컴퓨터를 켜두지 않아도 깃허브 서버에서 자동으로 실행됩니다.

1.  이 코드를 GitHub 저장소(Repository)에 올립니다.
2.  GitHub 저장소의 **Settings > Secrets and variables > Actions**로 이동합니다.
3.  **New repository secret** 버튼을 눌러 다음 두 가지를 추가합니다:
    -   `TELEGRAM_BOT_TOKEN`: @BotFather를 통해 받은 토큰
    -   `TELEGRAM_CHAT_ID`: 메시지를 받을 채팅방 ID
4.  `.github/workflows/rss_push.yml` 파일에 의해 30분마다 자동으로 실행됩니다.
5.  최초 실행 시 `last_seen.json` 파일이 생성되어 커밋됩니다. 그 이후부터 새로운 글이 올라오면 푸시됩니다.

## 로컬 실행 방법 (테스트용)

```bash
python rss_pusher.py
```

## 대상 RSS
-   방통위: https://www.korea.kr/rss/dept_kmcc.xml
-   공정위: https://www.korea.kr/rss/dept_ftc.xml
-   개보위: https://www.korea.kr/rss/dept_pipc.xml
