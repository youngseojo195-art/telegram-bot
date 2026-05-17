import os
import re
import random
import telebot
import psycopg2
import requests
import urllib.parse
import pytz
from datetime import datetime, timedelta
from flask import Flask, request

BOT_TOKEN = '8046489365:AAHAFBz4Ca07KcjqI0EJl76aIAu-rlVHw-4'
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

KST = pytz.timezone('Asia/Seoul')

# ← 여기에 실제 GIF URL 교체
AFFILIATE_GIF_URL = "https://media.giphy.com/media/your_gif_id/giphy.gif"

AFFILIATE_TEXT = """<b>┌─────────────────────┐</b>
<b>         🎰 카 지 노</b>
<b>└─────────────────────┘</b>

✅ <b>[평생]</b> <a href="https://t.me/gamte59/31">렛츠뱃</a>
✅ <b>[평생]</b> <a href="https://t.me/gamte59/28">예스뱃</a>
✅ <b>[도파민]</b> <a href="https://t.me/gamte59/44">지엑스뱃</a>
✅ <b>[도파민]</b> <a href="https://t.me/gamte59/46">케이비씨겜</a>
✅ <b>[도파민]</b> <a href="https://t.me/gamte59/49">블록체인바카라</a>
✅ <b>[도파민]</b> <a href="https://t.me/gamte59/60">우루스뱃</a>
✅ <b>[도파민]</b> <a href="https://t.me/gamte59/60">마닐라</a>
✅ <b>[도파민]</b> <a href="https://t.me/gamte59/70">미우카지노</a>
✅ <b>[도파민]</b> <a href="https://t.me/gamte59/72">그랜드파리</a>
✅ <b>[도파민]</b> <a href="https://t.me/gamte59/74">룰라뱃</a>
✅ <b>[도파민]</b> <a href="https://t.me/gamte59/78">소울카지노</a>
✅ <b>[도파민]</b> <a href="https://t.me/gamte59/84">123GAME카지노</a>

<b>┌─────────────────────┐</b>
<b>         💸 급 전</b>
<b>└─────────────────────┘</b>

✅ <b>[도파민]</b> <a href="https://t.me/gamte59/16">OR급전</a>
✅ <b>[도파민]</b> <a href="https://t.me/gamte59/77">빅딜OTC</a>

<b>┌─────────────────────┐</b>
<b>         🏠 장 집</b>
<b>└─────────────────────┘</b>

✅ <b>[도파민]</b> <a href="https://t.me/gamte59/37">미호 장집</a>
✅ <b>[도파민]</b> <a href="https://t.me/gamte59/76">빅딜 장집</a>

<b>┌─────────────────────┐</b>
<b>         🔄 반 환 팀</b>
<b>└─────────────────────┘</b>

✅ <b>[도파민]</b> <a href="https://t.me/gamte59/39">울프 반환팀</a>

<b>┌─────────────────────┐</b>
<b>      💳 충전 계좌매입</b>
<b>└─────────────────────┘</b>

✅ <b>[평생]</b> <a href="https://t.me/gamte59/42">저승사자</a>
✅ <b>[도파민]</b> <a href="https://t.me/gamte59/58">김여포</a>
✅ <b>[도파민]</b> <a href="https://t.me/gamte59/64">대문팀</a>
✅ <b>[도파민]</b> <a href="https://t.me/gamte59/92">관짝</a>

<b>┌─────────────────────┐</b>
<b>         ♠️ 홀 덤</b>
<b>└─────────────────────┘</b>

✅ <b>[도파민]</b> <a href="https://t.me/gamte59/69">룽지홀덤</a>

<b>┌─────────────────────┐</b>
<b>       💼 이체 알바</b>
<b>└─────────────────────┘</b>

✅ <b>[도파민]</b> <a href="https://t.me/gamte59/87">창비팀 대면이체알바</a>"""

# KBO 팀 목록
KBO_TEAMS = ['KT', '삼성', 'LG', 'SSG', 'KIA', '한화', '두산', 'NC', '롯데', '키움']
KBO_TEAMS_DISPLAY = {
    'KT':   '🔴 KT',
    '삼성': '🔵 삼성',
    'LG':   '🔴 LG',
    'SSG':  '🟡 SSG',
    'KIA':  '🔴 KIA',
    '한화': '🟠 한화',
    '두산': '🔵 두산',
    'NC':   '🔵 NC',
    '롯데': '🔴 롯데',
    '키움': '🟣 키움',
}

# 승 예측 참여 가능 시간 (18:00 ~ 18:30)
VOTE_START = "18:00"
VOTE_END   = "18:30"


def get_db():
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def init_db():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            username VARCHAR(255),
            first_name VARCHAR(255),
            group_id BIGINT NOT NULL,
            message_date TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS points (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            group_id BIGINT NOT NULL,
            first_name VARCHAR(255),
            username VARCHAR(255),
            point INTEGER DEFAULT 0,
            last_attendance DATE,
            UNIQUE(user_id, group_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS refill_logs (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            group_id BIGINT NOT NULL,
            first_name VARCHAR(255),
            username VARCHAR(255),
            refill_date DATE NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kbo_votes (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            group_id BIGINT NOT NULL,
            first_name VARCHAR(255),
            username VARCHAR(255),
            teams TEXT NOT NULL,
            vote_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, group_id, vote_date)
        )
    """)
    try:
        cursor.execute("""
            ALTER TABLE points
            ALTER COLUMN last_attendance TYPE DATE
            USING last_attendance::DATE
        """)
        db.commit()
    except:
        db.rollback()
    db.commit()
    cursor.close()
    db.close()

def get_point(user_id, group_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
    row = cursor.fetchone()
    cursor.close()
    db.close()
    return row[0] if row else 0

def update_point(user_id, group_id, first_name, username, amount):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO points (user_id, group_id, first_name, username, point)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id, group_id)
        DO UPDATE SET point = points.point + %s, first_name=%s, username=%s
    """, (user_id, group_id, first_name, username, amount, amount, first_name, username))
    db.commit()
    cursor.close()
    db.close()

def save_message(user_id, username, first_name, group_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO chat_logs (user_id, username, first_name, group_id, message_date) VALUES (%s, %s, %s, %s, %s)",
        (user_id, username, first_name, group_id, datetime.now())
    )
    db.commit()
    cursor.close()
    db.close()

def parse_teams_from_text(text):
    """텍스트에서 KBO 팀 이름 파싱 (순서 유지, 중복 제거)"""
    clean = re.sub(r'^/\S+\s*', '', text).strip()
    found = []
    for team in KBO_TEAMS:
        if team in clean and team not in found:
            found.append(team)
    return found

def is_vote_time(now_kst):
    current = now_kst.time()
    start = datetime.strptime(VOTE_START, "%H:%M").time()
    end   = datetime.strptime(VOTE_END,   "%H:%M").time()
    return start <= current <= end

def get_usdt_rate():
    try:
        response = requests.get('https://api.upbit.com/v1/ticker?markets=KRW-USDT', timeout=5)
        if response.status_code == 200:
            return float(response.json()[0]['trade_price'])
    except:
        pass
    try:
        response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=USDTKRW', timeout=5)
        if response.status_code == 200:
            return float(response.json()['price'])
    except:
        pass
    return None


@bot.message_handler(func=lambda m: True)
def handle_all(message):
    try:
        print(f"메시지 받음: '{message.text}' / 타입: {message.chat.type}")
        text = message.text or ''
        user_id = message.from_user.id
        group_id = message.chat.id
        first_name = message.from_user.first_name or '사용자'
        username = message.from_user.username or ''

        now_kst = datetime.now(KST)
        today = now_kst.date()

        # ==================== /test ====================
        if '/test' in text:
            bot.reply_to(message, "봇 작동 중! ✅")

        # ==================== /노래 ====================
        elif '/노래' in text:
            query = text.replace('/노래', '').strip()
            if not query:
                bot.reply_to(message, "🎵 검색어를 입력해주세요!\n예시: /노래 아이유 좋은날")
                return
            encoded = urllib.parse.quote(query)
            youtube_url = f"https://www.youtube.com/results?search_query={encoded}"
            bot.reply_to(message, f"🎵 {query}\n\n🔗 유튜브 검색 결과:\n{youtube_url}")

        # ==================== /제휴 ====================
        elif '/제휴' in text:
            try:
                bot.send_animation(chat_id=group_id, animation=AFFILIATE_GIF_URL)
            except Exception as gif_err:
                print(f"GIF 전송 실패: {gif_err}")
            bot.reply_to(message, AFFILIATE_TEXT, parse_mode='HTML', disable_web_page_preview=True)

        # ==================== 테더 환율 ====================
        elif re.search(r'(\d+(\.\d+)?)\s*테더', text):
            match = re.search(r'(\d+(\.\d+)?)\s*테더', text)
            amount = float(match.group(1))
            rate = get_usdt_rate()
            if rate is None:
                bot.reply_to(message, "⚠️ 환율 정보를 가져오지 못했어요. 잠시 후 다시 시도해주세요.")
                return
            base_amount = amount * rate
            bot.reply_to(message,
                f"💰 USDT 환율 계산\n\n"
                f"📈 현재 환율: {rate:,.0f}원\n\n"
                f"💵 {amount:,.0f} USDT: {base_amount:,.0f}원\n"
            )

        # ==================== /출석 ====================
        elif '/출석' in text:
            if message.chat.type == 'private':
                return
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "SELECT last_attendance FROM points WHERE user_id=%s AND group_id=%s",
                (user_id, group_id)
            )
            row = cursor.fetchone()
            if row and row[0] == today:
                cursor.close()
                db.close()
                bot.reply_to(message, "⏰ 오늘 이미 출석했어요!\n자정(00:00)이 지나면 다시 출석할 수 있어요 😊")
                return
            cursor.execute("""
                INSERT INTO points (user_id, group_id, first_name, username, point, last_attendance)
                VALUES (%s, %s, %s, %s, 100, %s)
                ON CONFLICT (user_id, group_id)
                DO UPDATE SET point = points.point + 100, last_attendance=%s, first_name=%s, username=%s
            """, (user_id, group_id, first_name, username, today, today, first_name, username))
            db.commit()
            cursor.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
            total = cursor.fetchone()[0]
            cursor.close()
            db.close()
            bot.reply_to(message,
                f"╔══ ✅ 출석 완료 ══╗\n"
                f"  👤 {first_name}님\n\n"
                f"  🎁 획득: 100포인트\n"
                f"  💰 잔여: {total}포인트\n"
                f"  🔄 리셋: 매일 자정 00:00\n"
                f"╚══════════════════╝"
            )

        # ==================== /리필 ====================
        elif '/리필' in text:
            if message.chat.type == 'private':
                return
            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM refill_logs
                WHERE user_id=%s AND group_id=%s AND refill_date=%s
            """, (user_id, group_id, today))
            count = cursor.fetchone()[0]
            if count >= 5:
                cursor.close()
                db.close()
                bot.reply_to(message, "⚠️ 오늘 리필을 5번 모두 사용했어요!\n자정(00:00)이 지나면 다시 사용할 수 있어요 😊")
                return
            cursor.execute("""
                INSERT INTO refill_logs (user_id, group_id, first_name, username, refill_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, group_id, first_name, username, today))
            db.commit()
            cursor.close()
            db.close()
            update_point(user_id, group_id, first_name, username, 100)
            new_point = get_point(user_id, group_id)
            remaining = 5 - (count + 1)
            bot.reply_to(message,
                f"╔══ 🔄 리필 완료 ══╗\n"
                f"  👤 {first_name}님\n\n"
                f"  🎁 획득: 100포인트\n"
                f"  💰 잔여: {new_point}포인트\n"
                f"  📊 오늘 남은 리필: {remaining}회\n"
                f"  🔄 리셋: 매일 자정 00:00\n"
                f"╚══════════════════╝"
            )

        # ==================== /선물 ====================
        elif '/선물' in text:
            if message.chat.type == 'private':
                bot.reply_to(message, "⚠️ 선물은 그룹에서만 사용할 수 있어요!")
                return
            if not message.reply_to_message:
                bot.reply_to(message,
                    "🎁 사용법: 선물할 상대의 메시지에 답장으로\n"
                    "/선물 [포인트]\n\n예시: /선물 100\n\n⚠️ 최소 선물: 10포인트"
                )
                return
            parts = text.split()
            if len(parts) < 2 or not parts[1].isdigit():
                bot.reply_to(message,
                    "🎁 사용법: 선물할 상대의 메시지에 답장으로\n"
                    "/선물 [포인트]\n\n예시: /선물 100\n\n⚠️ 최소 선물: 10포인트"
                )
                return
            amount = int(parts[1])
            if amount < 10:
                bot.reply_to(message, "⚠️ 최소 선물 포인트는 10포인트예요!")
                return
            target = message.reply_to_message.from_user
            target_id = target.id
            target_name = target.first_name or '상대방'
            if target_id == user_id:
                bot.reply_to(message, "⚠️ 자기 자신에게는 선물할 수 없어요!")
                return
            if target.is_bot:
                bot.reply_to(message, "⚠️ 봇에게는 선물할 수 없어요!")
                return
            my_point = get_point(user_id, group_id)
            if my_point < amount:
                bot.reply_to(message,
                    f"💸 포인트가 부족해요!\n  보유: {my_point}포인트\n  필요: {amount}포인트"
                )
                return
            update_point(user_id, group_id, first_name, username, -amount)
            update_point(target_id, group_id, target_name, target.username or '', amount)
            my_new_point = get_point(user_id, group_id)
            target_new_point = get_point(target_id, group_id)
            bot.reply_to(message,
                f"╔══ 🎁 포인트 선물 ══╗\n"
                f"  💝 {first_name} → {target_name}\n\n"
                f"  🎀 선물: {amount}포인트\n\n"
                f"  📤 {first_name} 잔여: {my_new_point}포인트\n"
                f"  📥 {target_name} 잔여: {target_new_point}포인트\n"
                f"╚══════════════════╝"
            )

        # ==================== /포인트랭킹 ====================
        elif '/포인트랭킹' in text:
            if message.chat.type == 'private':
                return
            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                SELECT first_name, username, point
                FROM points WHERE group_id=%s
                ORDER BY point DESC LIMIT 5
            """, (group_id,))
            rows = cursor.fetchall()
            cursor.close()
            db.close()
            medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
            result = "╔══ 💰 포인트 랭킹 ══╗\n\n"
            if not rows:
                result += "  포인트 기록이 없어요 😅\n"
            else:
                for i, row in enumerate(rows):
                    name = row[0] or row[1] or '익명'
                    result += f"  {medals[i]} {name:<10} {row[2]}포인트\n"
            result += "╚══════════════════╝"
            bot.reply_to(message, result)

        # ==================== /포인트 ====================
        elif '/포인트' in text:
            if message.chat.type == 'private':
                return
            point = get_point(user_id, group_id)
            bot.reply_to(message,
                f"╔══ 💰 포인트 ══╗\n"
                f"  👤 {first_name}님\n\n"
                f"  💰 잔여: {point}포인트\n"
                f"╚══════════════════╝"
            )

        # ==================== /게임 ====================
        elif text.strip() in ['/게임', '/게임@dopamin_ranking_bot']:
            bot.reply_to(message,
                "🎮 게임 목록\n\n"
                "🎰 /슬롯 [배팅] - 슬롯머신\n"
                "🎡 /룰렛 [배팅] - 룰렛\n\n"
                "⚠️ 최소 참가비: 20포인트"
            )

        # ==================== /슬롯 ====================
        elif '/슬롯' in text:
            if message.chat.type == 'private':
                return
            parts = text.split()
            if len(parts) < 2 or not parts[1].isdigit():
                bot.reply_to(message, "🎰 사용법: /슬롯 [배팅포인트]\n예시: /슬롯 100")
                return
            bet = int(parts[1])
            if bet < 20:
                bot.reply_to(message, "⚠️ 최소 배팅은 20포인트예요!")
                return
            point = get_point(user_id, group_id)
            if point < bet:
                bot.reply_to(message, f"💸 포인트가 부족해요!\n현재 포인트: {point}포인트")
                return
            symbols = ['🍋', '🍒', '🍇', '⭐', '7️⃣', '💎']
            weights = [30, 25, 20, 15, 7, 3]
            s1 = random.choices(symbols, weights=weights)[0]
            s2 = random.choices(symbols, weights=weights)[0]
            s3 = random.choices(symbols, weights=weights)[0]
            if s1 == s2 == s3:
                if s1 == '💎':
                    multiplier, result_text = 50, "💎 JACKPOT! 50배!"
                elif s1 == '7️⃣':
                    multiplier, result_text = 10, "7️⃣ 럭키세븐! 10배!"
                elif s1 == '⭐':
                    multiplier, result_text = 7, "⭐ 스타! 7배!"
                else:
                    multiplier, result_text = 5, "🎉 3개 일치! 5배!"
                won = bet * multiplier - bet
            elif s1 == s2 or s2 == s3 or s1 == s3:
                multiplier, result_text = 1.5, "✨ 2개 일치! 1.5배!"
                won = int(bet * 1.5) - bet
            else:
                multiplier, result_text = 0, "💀 꽝!"
                won = -bet
            update_point(user_id, group_id, first_name, username, won)
            new_point = get_point(user_id, group_id)
            bot.reply_to(message,
                f"╔══ 🎰 슬롯머신 ══╗\n"
                f"  [ {s1} | {s2} | {s3} ]\n\n"
                f"  {result_text}\n\n"
                f"  배팅: {bet}포인트\n"
                f"  {'획득: +' if won > 0 else '손실: '}{won}포인트\n"
                f"  잔여: {new_point}포인트\n"
                f"╚══════════════════╝"
            )

        # ==================== /룰렛 ====================
        elif '/룰렛' in text:
            if message.chat.type == 'private':
                return
            parts = text.split()
            if len(parts) < 2 or not parts[1].isdigit():
                bot.reply_to(message, "🎡 사용법: /룰렛 [배팅포인트]\n예시: /룰렛 100")
                return
            bet = int(parts[1])
            if bet < 20:
                bot.reply_to(message, "⚠️ 최소 배팅은 20포인트예요!")
                return
            point = get_point(user_id, group_id)
            if point < bet:
                bot.reply_to(message, f"💸 포인트가 부족해요!\n현재 포인트: {point}포인트")
                return
            roulette = [
                ('💀 꽝', 0, 55),
                ('🔵 1.5배', 1.5, 20),
                ('🟢 2배', 2, 15),
                ('🟡 3배', 3, 7),
                ('🔴 5배', 5, 2),
                ('💎 10배', 10, 1),
            ]
            idx = random.choices(range(len(roulette)), weights=[r[2] for r in roulette])[0]
            label, multiplier, _ = roulette[idx]
            won = int(bet * multiplier) - bet if multiplier > 0 else -bet
            update_point(user_id, group_id, first_name, username, won)
            new_point = get_point(user_id, group_id)
            bot.reply_to(message,
                f"╔══ 🎡 룰렛 ══╗\n"
                f"  결과: {label}\n\n"
                f"  배팅: {bet}포인트\n"
                f"  {'획득: +' if won > 0 else '손실: '}{won}포인트\n"
                f"  잔여: {new_point}포인트\n"
                f"╚══════════════════╝"
            )

        # ==================== /채팅랭킹 ====================
        elif '/채팅랭킹' in text:
            if message.chat.type == 'private':
                return
            monday = today - timedelta(days=today.weekday())
            sunday = monday + timedelta(days=6)
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "SELECT first_name, username, COUNT(*) as cnt FROM chat_logs "
                "WHERE group_id=%s AND message_date>=%s "
                "GROUP BY user_id, first_name, username ORDER BY cnt DESC LIMIT 5",
                (group_id, monday)
            )
            rows = cursor.fetchall()
            cursor.close()
            db.close()
            medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
            result  = f"╔══ 🏆 주간 랭킹 ══╗\n"
            result += f"  📅 {monday.strftime('%m/%d')} ~ {sunday.strftime('%m/%d')}\n\n"
            if not rows:
                result += "  채팅 기록이 없어요 😅\n"
            else:
                for i, row in enumerate(rows):
                    name = row[0] or row[1] or '익명'
                    result += f"  {medals[i]} {name:<10} {row[2]}개\n"
            result += "╚══════════════════╝"
            bot.reply_to(message, result)

        # ==================== /채팅 ====================
        elif '/채팅' in text:
            if message.chat.type == 'private':
                return
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND DATE(message_date)=%s",
                (user_id, group_id, today)
            )
            today_count = cursor.fetchone()[0]
            monday = today - timedelta(days=today.weekday())
            cursor.execute(
                "SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND message_date>=%s",
                (user_id, group_id, monday)
            )
            week_count = cursor.fetchone()[0]
            cursor.execute(
                "SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s "
                "AND EXTRACT(YEAR FROM message_date)=EXTRACT(YEAR FROM NOW()) "
                "AND EXTRACT(MONTH FROM message_date)=EXTRACT(MONTH FROM NOW())",
                (user_id, group_id)
            )
            month_count = cursor.fetchone()[0]
            cursor.execute(
                "SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s",
                (user_id, group_id)
            )
            total_count = cursor.fetchone()[0]
            cursor.close()
            db.close()
            result  = f"╔══ 📊 채팅 통계 ══╗\n"
            result += f"  👤 {first_name}님\n\n"
            result += f"  ☀️ 오늘       {today_count}개\n"
            result += f"  📆 이번 주   {week_count}개\n"
            result += f"  🗓 이번 달   {month_count}개\n"
            result += f"  💬 전체      {total_count}개\n\n"
            result += f"  🎀 오늘도 열심히 채팅했어요!\n"
            result += "╚══════════════════╝"
            bot.reply_to(message, result)

        # ==================== /승 (KBO 승 예측) ====================
        elif text.strip().startswith('/승'):
            if message.chat.type == 'private':
                return

            if not is_vote_time(now_kst):
                bot.reply_to(message,
                    "🚫 지금은 참여 시간이 아닙니다.\n\n"
                    f"⏰ PM {VOTE_START} ~ {VOTE_END} 사이에 참여해주세요."
                )
                return

            teams = parse_teams_from_text(text)

            if len(teams) == 0:
                team_list = " / ".join(KBO_TEAMS)
                bot.reply_to(message,
                    f"⚾ KBO 승 예측 사용법\n\n"
                    f"/승 [팀1] [팀2] [팀3] [팀4] [팀5]\n\n"
                    f"📋 선택 가능 팀:\n  {team_list}\n\n"
                    f"✅ 10개 팀 중 5개 선택\n"
                    f"예시: /승 KT 삼성 LG SSG KIA"
                )
                return

            if len(teams) != 5:
                bot.reply_to(message,
                    f"⚠️ 정확히 5개 팀을 선택해야 해요!\n"
                    f"현재 선택: {len(teams)}개 ({', '.join(teams)})\n\n"
                    f"예시: /승 KT 삼성 LG SSG KIA"
                )
                return

            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                SELECT teams FROM kbo_votes
                WHERE user_id=%s AND group_id=%s AND vote_date=%s
            """, (user_id, group_id, today))
            existing = cursor.fetchone()

            if existing:
                cursor.close()
                db.close()
                existing_teams = existing[0].split(',')
                team_str = "\n".join(
                    [f"  {i+1}. {KBO_TEAMS_DISPLAY.get(t, t)}" for i, t in enumerate(existing_teams)]
                )
                bot.reply_to(message,
                    f"⚠️ 이미 오늘 예측에 참여하셨어요!\n\n"
                    f"선택하신 팀:\n{team_str}\n\n"
                    f"수정하려면 /수정 을 사용하세요."
                )
                return

            teams_str = ','.join(teams)
            cursor.execute("""
                INSERT INTO kbo_votes (user_id, group_id, first_name, username, teams, vote_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, group_id, first_name, username, teams_str, today))
            db.commit()

            cursor.execute("""
                SELECT COUNT(*) FROM kbo_votes WHERE group_id=%s AND vote_date=%s
            """, (group_id, today))
            total_participants = cursor.fetchone()[0]
            cursor.close()
            db.close()

            team_display = "\n".join(
                [f"  {i+1}. {KBO_TEAMS_DISPLAY.get(t, t)}" for i, t in enumerate(teams)]
            )
            bot.reply_to(message,
                f"╔══ ⚾ KBO 승 예측 완료 ══╗\n"
                f"  👤 {first_name}님\n\n"
                f"  선택한 팀 (5개):\n"
                f"{team_display}\n\n"
                f"  👥 오늘 참여자: {total_participants}명\n"
                f"  ✏️ 수정: /수정 명령어 사용\n"
                f"╚══════════════════╝"
            )

        # ==================== /수정 (KBO 예측 수정) ====================
        elif text.strip().startswith('/수정'):
            if message.chat.type == 'private':
                return

            if not is_vote_time(now_kst):
                bot.reply_to(message,
                    "🚫 지금은 수정 시간이 아닙니다.\n\n"
                    f"⏰ PM {VOTE_START} ~ {VOTE_END} 사이에 수정 가능합니다."
                )
                return

            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                SELECT teams FROM kbo_votes
                WHERE user_id=%s AND group_id=%s AND vote_date=%s
            """, (user_id, group_id, today))
            existing = cursor.fetchone()

            if not existing:
                cursor.close()
                db.close()
                bot.reply_to(message,
                    "⚠️ 오늘 예측에 참여하지 않으셨어요!\n"
                    "/승 명령어로 먼저 예측에 참여해주세요."
                )
                return

            teams = parse_teams_from_text(text)

            # 팀 없이 /수정만 입력 → 현재 선택 안내
            if len(teams) == 0:
                existing_teams = existing[0].split(',')
                team_str = "\n".join(
                    [f"  {i+1}. {KBO_TEAMS_DISPLAY.get(t, t)}" for i, t in enumerate(existing_teams)]
                )
                team_list = " / ".join(KBO_TEAMS)
                cursor.close()
                db.close()
                bot.reply_to(message,
                    f"╔══ ✏️ 예측 수정 ══╗\n"
                    f"  👤 {first_name}님의 현재 선택:\n\n"
                    f"{team_str}\n\n"
                    f"  📋 팀 목록:\n  {team_list}\n\n"
                    f"  🔄 수정 방법:\n"
                    f"  /수정 [팀1] [팀2] [팀3] [팀4] [팀5]\n"
                    f"  예시: /수정 KT 두산 LG NC 키움\n"
                    f"╚══════════════════╝"
                )
                return

            if len(teams) != 5:
                cursor.close()
                db.close()
                bot.reply_to(message,
                    f"⚠️ 정확히 5개 팀을 선택해야 해요!\n"
                    f"현재 선택: {len(teams)}개 ({', '.join(teams)})\n\n"
                    f"예시: /수정 KT 삼성 LG SSG KIA"
                )
                return

            teams_str = ','.join(teams)
            cursor.execute("""
                UPDATE kbo_votes SET teams=%s, first_name=%s, username=%s
                WHERE user_id=%s AND group_id=%s AND vote_date=%s
            """, (teams_str, first_name, username, user_id, group_id, today))
            db.commit()
            cursor.close()
            db.close()

            team_display = "\n".join(
                [f"  {i+1}. {KBO_TEAMS_DISPLAY.get(t, t)}" for i, t in enumerate(teams)]
            )
            bot.reply_to(message,
                f"╔══ ✅ 예측 수정 완료 ══╗\n"
                f"  👤 {first_name}님\n\n"
                f"  변경된 선택 (5개):\n"
                f"{team_display}\n"
                f"╚══════════════════╝"
            )

        # ==================== /리스트 (KBO 예측 리스트) ====================
        elif text.strip().startswith('/리스트'):
            if message.chat.type == 'private':
                return

            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                SELECT first_name, username, teams
                FROM kbo_votes
                WHERE group_id=%s AND vote_date=%s
                ORDER BY created_at
            """, (group_id, today))
            rows = cursor.fetchall()
            cursor.close()
            db.close()

            if not rows:
                bot.reply_to(message, "📋 오늘 예측에 참여한 사람이 없어요!")
                return

            result  = f"╔══ ⚾ KBO 승 예측 리스트 ══╗\n"
            result += f"  📅 {today.strftime('%Y년 %m월 %d일')}\n"
            result += f"  👥 참여자: {len(rows)}명\n"
            result += f"  {'─' * 21}\n"

            for row in rows:
                name = row[0] or row[1] or '익명'
                teams_picked = row[2].split(',')
                team_icons = " ".join([KBO_TEAMS_DISPLAY.get(t, t) for t in teams_picked])
                result += f"  👤 {name}\n"
                result += f"  {team_icons}\n"
                result += f"  {'─' * 21}\n"

            result += "╚══════════════════╝"
            bot.reply_to(message, result)

        # ==================== 메시지 기록 ====================
        elif message.chat.type in ['group', 'supergroup']:
            save_message(user_id, username, first_name, group_id)

    except Exception as e:
        import traceback
        print(f"handle_all error: {e}")
        print(traceback.format_exc())


@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    try:
        json_str = request.stream.read().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        if update.message:
            handle_all(update.message)
        print("처리 완료!")
    except Exception as e:
        import traceback
        print(f"webhook error: {e}")
        print(traceback.format_exc())
    return 'OK', 200

@app.route('/')
def index():
    return 'Bot is running!', 200

try:
    init_db()
    print("DB 초기화 성공!")
except Exception as e:
    print(f"DB init error: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
