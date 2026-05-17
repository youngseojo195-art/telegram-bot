import os
import re
import json
import random
import telebot
import psycopg2
import requests
import urllib.parse
import pytz
from telebot import types
from datetime import datetime, timedelta
from flask import Flask, request

BOT_TOKEN = '8046489365:AAHAFBz4Ca07KcjqI0EJl76aIAu-rlVHw-4'
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

KST = pytz.timezone('Asia/Seoul')

# ─────────────────────────────────────────────────────────
# GIF 설정
# BASEBALL_GIF_FILE_ID : /getfileid 로 얻은 file_id 입력
# AFFILIATE_GIF_URL    : 제휴 GIF URL
# ─────────────────────────────────────────────────────────
BASEBALL_GIF_FILE_ID = "CgACAgUAAxkBAAMzagl3svn3G8Jr7JDeNhdXbodfQnIAAi8dAAJux0hUOyDPUXIJtRs7BA"
AFFILIATE_GIF_URL    = None   # ← 제휴 GIF URL을 여기에 넣으세요

def send_baseball_gif(chat_id):
    """야구 GIF 전송. file_id 없으면 스킵."""
    if not BASEBALL_GIF_FILE_ID:
        return
    try:
        bot.send_animation(chat_id=chat_id, animation=BASEBALL_GIF_FILE_ID)
    except Exception as e:
        print(f"야구 GIF 전송 실패: {e}")

def send_affiliate_gif(chat_id):
    """제휴 GIF 전송. URL 없으면 스킵."""
    if not AFFILIATE_GIF_URL:
        return
    try:
        bot.send_animation(chat_id=chat_id, animation=AFFILIATE_GIF_URL)
    except Exception as e:
        print(f"제휴 GIF 전송 실패: {e}")

# ─────────────────────────────────────────────────────────
# 제휴 텍스트
# ─────────────────────────────────────────────────────────
AFFILIATE_TEXT = """🎰 <b>카지노</b>
──────────────────
<b>[평생]</b> · <a href="https://t.me/gamte59/31">렛츠뱃</a>
<b>[평생]</b> · <a href="https://t.me/gamte59/28">예스뱃</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/44">지엑스뱃</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/46">케이비씨겜</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/49">블록체인바카라</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/60">우루스뱃</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/60">마닐라</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/70">미우카지노</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/72">그랜드파리</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/74">룰라뱃</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/78">소울카지노</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/84">123GAME카지노</a>

💸 <b>급전</b>
──────────────────
<b>[도파민]</b> · <a href="https://t.me/gamte59/16">OR급전</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/77">빅딜OTC</a>

🏠 <b>장집</b>
──────────────────
<b>[도파민]</b> · <a href="https://t.me/gamte59/37">미호 장집</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/76">빅딜 장집</a>

🔄 <b>반환팀</b>
──────────────────
<b>[도파민]</b> · <a href="https://t.me/gamte59/39">울프 반환팀</a>

💳 <b>충전 계좌매입</b>
──────────────────
<b>[평생]</b> · <a href="https://t.me/gamte59/42">저승사자</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/58">김여포</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/64">대문팀</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/92">관짝</a>

♠️ <b>홀덤</b>
──────────────────
<b>[도파민]</b> · <a href="https://t.me/gamte59/69">룽지홀덤</a>

💼 <b>이체 알바</b>
──────────────────
<b>[도파민]</b> · <a href="https://t.me/gamte59/87">창비팀 대면이체알바</a>"""

# ─────────────────────────────────────────────────────────
# KBO 팀 설정
# ─────────────────────────────────────────────────────────
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

VOTE_START = "18:00"
VOTE_END   = "18:30"

# ─────────────────────────────────────────────────────────
# 인라인 키보드 빌더
# ─────────────────────────────────────────────────────────
def build_team_keyboard(selected: list) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for team in KBO_TEAMS:
        label = f"✅ {team}" if team in selected else KBO_TEAMS_DISPLAY.get(team, team)
        buttons.append(types.InlineKeyboardButton(
            text=label,
            callback_data=f"kbo_toggle:{team}"
        ))
    markup.add(*buttons)
    count = len(selected)
    if count == 5:
        markup.add(
            types.InlineKeyboardButton("🔄 초기화", callback_data="kbo_reset"),
            types.InlineKeyboardButton(f"✅ 제출하기 ({count}/5)", callback_data="kbo_submit")
        )
    else:
        markup.add(
            types.InlineKeyboardButton("🔄 초기화", callback_data="kbo_reset"),
            types.InlineKeyboardButton(f"⬜ 선택 중 ({count}/5)", callback_data="kbo_noop")
        )
    return markup

def build_vote_message(selected: list) -> str:
    count = len(selected)
    if count == 0:
        status = "팀을 선택해주세요"
    elif count < 5:
        status = f"{count}개 선택 — {5 - count}개 더 선택하세요"
    else:
        status = "5개 선택 완료! 제출하기를 눌러주세요 ✅"
    lines = ["⚾ KBO 승 예측 — 팀 선택", "", f"📊 {status}", ""]
    for t in selected:
        lines.append(f"  • {KBO_TEAMS_DISPLAY.get(t, t)}")
    return "\n".join(lines)

# ─────────────────────────────────────────────────────────
# DB 헬퍼
# ─────────────────────────────────────────────────────────
def get_db():
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def init_db():
    db = get_db()
    c = db.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS chat_logs (
        id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL,
        username VARCHAR(255), first_name VARCHAR(255),
        group_id BIGINT NOT NULL, message_date TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT NOW())""")
    c.execute("""CREATE TABLE IF NOT EXISTS points (
        id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL,
        group_id BIGINT NOT NULL, first_name VARCHAR(255),
        username VARCHAR(255), point INTEGER DEFAULT 0,
        last_attendance DATE, UNIQUE(user_id, group_id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS refill_logs (
        id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL,
        group_id BIGINT NOT NULL, first_name VARCHAR(255),
        username VARCHAR(255), refill_date DATE NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS kbo_votes (
        id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL,
        group_id BIGINT NOT NULL, first_name VARCHAR(255),
        username VARCHAR(255), teams TEXT NOT NULL,
        vote_date DATE NOT NULL, created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(user_id, group_id, vote_date))""")
    c.execute("""CREATE TABLE IF NOT EXISTS kbo_pending (
        user_id BIGINT NOT NULL, group_id BIGINT NOT NULL,
        selected TEXT NOT NULL DEFAULT '', message_id BIGINT,
        PRIMARY KEY (user_id, group_id))""")
    try:
        c.execute("ALTER TABLE points ALTER COLUMN last_attendance TYPE DATE USING last_attendance::DATE")
        db.commit()
    except:
        db.rollback()
    db.commit()
    c.close(); db.close()

def get_point(user_id, group_id):
    db = get_db(); c = db.cursor()
    c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
    row = c.fetchone(); c.close(); db.close()
    return row[0] if row else 0

def update_point(user_id, group_id, first_name, username, amount):
    db = get_db(); c = db.cursor()
    c.execute("""INSERT INTO points (user_id, group_id, first_name, username, point)
        VALUES (%s,%s,%s,%s,%s) ON CONFLICT (user_id, group_id)
        DO UPDATE SET point=points.point+%s, first_name=%s, username=%s""",
        (user_id, group_id, first_name, username, amount, amount, first_name, username))
    db.commit(); c.close(); db.close()

def save_message(user_id, username, first_name, group_id):
    db = get_db(); c = db.cursor()
    c.execute("INSERT INTO chat_logs (user_id,username,first_name,group_id,message_date) VALUES (%s,%s,%s,%s,%s)",
              (user_id, username, first_name, group_id, datetime.now()))
    db.commit(); c.close(); db.close()

def get_pending(user_id, group_id):
    db = get_db(); c = db.cursor()
    c.execute("SELECT selected, message_id FROM kbo_pending WHERE user_id=%s AND group_id=%s", (user_id, group_id))
    row = c.fetchone(); c.close(); db.close()
    if row:
        return ([t for t in row[0].split(',') if t], row[1])
    return ([], None)

def set_pending(user_id, group_id, selected: list, message_id=None):
    db = get_db(); c = db.cursor()
    s = ','.join(selected)
    c.execute("""INSERT INTO kbo_pending (user_id, group_id, selected, message_id)
        VALUES (%s,%s,%s,%s) ON CONFLICT (user_id, group_id)
        DO UPDATE SET selected=%s, message_id=%s""",
        (user_id, group_id, s, message_id, s, message_id))
    db.commit(); c.close(); db.close()

def clear_pending(user_id, group_id):
    db = get_db(); c = db.cursor()
    c.execute("DELETE FROM kbo_pending WHERE user_id=%s AND group_id=%s", (user_id, group_id))
    db.commit(); c.close(); db.close()

def is_vote_time(now_kst):
    # 화=1, 수=2, 목=3, 금=4 만 허용
    if now_kst.weekday() not in [1, 2, 3, 4]:
        return False
    cur = now_kst.time()
    return (datetime.strptime(VOTE_START, "%H:%M").time()
            <= cur <=
            datetime.strptime(VOTE_END, "%H:%M").time())

def get_usdt_rate():
    try:
        r = requests.get('https://api.upbit.com/v1/ticker?markets=KRW-USDT', timeout=5)
        if r.status_code == 200:
            return float(r.json()[0]['trade_price'])
    except: pass
    try:
        r = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=USDTKRW', timeout=5)
        if r.status_code == 200:
            return float(r.json()['price'])
    except: pass
    return None

# ─────────────────────────────────────────────────────────
# 인라인 키보드 콜백 핸들러
# ─────────────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda call: call.data.startswith('kbo_'))
def handle_kbo_callback(call):
    try:
        user_id    = call.from_user.id
        group_id   = call.message.chat.id
        first_name = call.from_user.first_name or '사용자'
        username   = call.from_user.username or ''
        now_kst    = datetime.now(KST)
        today      = now_kst.date()
        action     = call.data

        if not is_vote_time(now_kst):
            bot.answer_callback_query(call.id, f"⏰ {VOTE_START}~{VOTE_END} 사이에만 참여 가능해요!", show_alert=True)
            return

        db = get_db(); c = db.cursor()
        c.execute("SELECT teams FROM kbo_votes WHERE user_id=%s AND group_id=%s AND vote_date=%s",
                  (user_id, group_id, today))
        already = c.fetchone(); c.close(); db.close()

        if already and action not in ("kbo_submit", "kbo_reset", "kbo_noop") and not action.startswith("kbo_toggle"):
            pass

        selected, msg_id = get_pending(user_id, group_id)

        # 이미 제출한 사람이 팀 토글 / 제출 외 버튼 누를 때
        if already and action == "kbo_noop":
            bot.answer_callback_query(call.id, "이미 제출하셨어요! 수정하려면 /수정 을 사용하세요.")
            return

        if action == "kbo_noop":
            bot.answer_callback_query(call.id, f"5개를 선택해야 제출할 수 있어요! (현재 {len(selected)}개)")
            return

        elif action == "kbo_reset":
            selected = []
            set_pending(user_id, group_id, selected, call.message.message_id)
            bot.edit_message_text(
                chat_id=group_id, message_id=call.message.message_id,
                text=build_vote_message(selected),
                reply_markup=build_team_keyboard(selected)
            )
            bot.answer_callback_query(call.id, "초기화 됐어요!")

        elif action.startswith("kbo_toggle:"):
            team = action.split(":")[1]
            if team in selected:
                selected.remove(team)
                bot.answer_callback_query(call.id, f"{KBO_TEAMS_DISPLAY.get(team, team)} 선택 취소")
            else:
                if len(selected) >= 5:
                    bot.answer_callback_query(call.id, "이미 5개 선택! 초기화 후 다시 선택하세요.", show_alert=True)
                    return
                selected.append(team)
                bot.answer_callback_query(call.id, f"{KBO_TEAMS_DISPLAY.get(team, team)} 선택! ({len(selected)}/5)")
            set_pending(user_id, group_id, selected, call.message.message_id)
            bot.edit_message_text(
                chat_id=group_id, message_id=call.message.message_id,
                text=build_vote_message(selected),
                reply_markup=build_team_keyboard(selected)
            )

        elif action == "kbo_submit":
            if len(selected) != 5:
                bot.answer_callback_query(call.id, "5개를 선택해야 제출할 수 있어요!", show_alert=True)
                return
            teams_str = ','.join(selected)
            db = get_db(); c = db.cursor()
            if already:
                c.execute("""UPDATE kbo_votes SET teams=%s, first_name=%s, username=%s
                    WHERE user_id=%s AND group_id=%s AND vote_date=%s""",
                    (teams_str, first_name, username, user_id, group_id, today))
                action_label = "수정 완료"
            else:
                c.execute("""INSERT INTO kbo_votes (user_id, group_id, first_name, username, teams, vote_date)
                    VALUES (%s,%s,%s,%s,%s,%s)""",
                    (user_id, group_id, first_name, username, teams_str, today))
                action_label = "예측 완료"
            c.execute("SELECT COUNT(*) FROM kbo_votes WHERE group_id=%s AND vote_date=%s", (group_id, today))
            total = c.fetchone()[0]
            db.commit(); c.close(); db.close()
            clear_pending(user_id, group_id)
            team_display = "\n".join([f"  {i+1}. {KBO_TEAMS_DISPLAY.get(t,t)}" for i,t in enumerate(selected)])
            bot.edit_message_text(
                chat_id=group_id, message_id=call.message.message_id,
                text=(
                    f"╔══ ⚾ KBO 승 {action_label} ══╗\n"
                    f"  👤 {first_name}님\n\n"
                    f"  선택한 팀 (5개):\n{team_display}\n\n"
                    f"  👥 오늘 참여자: {total}명\n"
                    f"  ✏️ 수정: /수정 명령어 사용\n"
                    f"╚══════════════════╝"
                ),
                reply_markup=None
            )
            bot.answer_callback_query(call.id, f"✅ {action_label}!")

    except Exception as e:
        import traceback
        print(f"callback error: {e}\n{traceback.format_exc()}")
        bot.answer_callback_query(call.id, "오류가 발생했어요. 다시 시도해주세요.")

# ─────────────────────────────────────────────────────────
# 메시지 핸들러
# ─────────────────────────────────────────────────────────
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    try:
        print(f"메시지 받음: '{message.text}' / 타입: {message.chat.type}")
        text       = message.text or ''
        user_id    = message.from_user.id
        group_id   = message.chat.id
        first_name = message.from_user.first_name or '사용자'
        username   = message.from_user.username or ''
        now_kst    = datetime.now(KST)
        today      = now_kst.date()

        # ── /test ──────────────────────────────────────
        if '/test' in text:
            bot.reply_to(message, "봇 작동 중! ✅")

        # ── /getfileid (봇에 영상/GIF 보내면 file_id 반환) ──
        elif '/getfileid' in text:
            if message.reply_to_message:
                msg = message.reply_to_message
                file_id = None
                if msg.animation:
                    file_id = msg.animation.file_id
                elif msg.video:
                    file_id = msg.video.file_id
                elif msg.document:
                    file_id = msg.document.file_id
                if file_id:
                    bot.reply_to(message,
                        f"📋 file_id:\n\n<code>{file_id}</code>\n\n"
                        f"위 값을 bot.py의 BASEBALL_GIF_FILE_ID 에 넣으세요!",
                        parse_mode='HTML'
                    )
                else:
                    bot.reply_to(message, "⚠️ 영상/GIF 파일을 찾을 수 없어요. GIF나 영상 메시지에 답장해서 사용하세요.")
            else:
                bot.reply_to(message, "⚾ GIF/영상 메시지에 답장으로 /getfileid 를 입력하면 file_id를 알려드려요!")

        # ── /노래 ──────────────────────────────────────
        elif '/노래' in text:
            query = text.replace('/노래', '').strip()
            if not query:
                bot.reply_to(message, "🎵 검색어를 입력해주세요!\n예시: /노래 아이유 좋은날")
                return
            encoded = urllib.parse.quote(query)
            bot.reply_to(message, f"🎵 {query}\n\n🔗 유튜브 검색 결과:\nhttps://www.youtube.com/results?search_query={encoded}")

        # ── /제휴 ──────────────────────────────────────
        elif '/제휴' in text:
            send_affiliate_gif(group_id)
            bot.reply_to(message, AFFILIATE_TEXT, parse_mode='HTML', disable_web_page_preview=True)

        # ── 테더 환율 ───────────────────────────────────
        elif re.search(r'(\d+(\.\d+)?)\s*테더', text):
            match = re.search(r'(\d+(\.\d+)?)\s*테더', text)
            amount = float(match.group(1))
            rate = get_usdt_rate()
            if rate is None:
                bot.reply_to(message, "⚠️ 환율 정보를 가져오지 못했어요. 잠시 후 다시 시도해주세요.")
                return
            bot.reply_to(message,
                f"💰 USDT 환율 계산\n\n"
                f"📈 현재 환율: {rate:,.0f}원\n"
                f"💵 {amount:,.0f} USDT: {amount * rate:,.0f}원"
            )

        # ── /출석 ──────────────────────────────────────
        elif '/출석' in text:
            if message.chat.type == 'private': return
            db = get_db(); c = db.cursor()
            c.execute("SELECT last_attendance FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
            row = c.fetchone()
            if row and row[0] == today:
                c.close(); db.close()
                bot.reply_to(message, "⏰ 오늘 이미 출석했어요!\n자정(00:00)이 지나면 다시 출석할 수 있어요 😊")
                return
            c.execute("""INSERT INTO points (user_id,group_id,first_name,username,point,last_attendance)
                VALUES (%s,%s,%s,%s,100,%s) ON CONFLICT (user_id,group_id)
                DO UPDATE SET point=points.point+100, last_attendance=%s, first_name=%s, username=%s""",
                (user_id, group_id, first_name, username, today, today, first_name, username))
            db.commit()
            c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
            total = c.fetchone()[0]; c.close(); db.close()
            bot.reply_to(message,
                f"╔══ ✅ 출석 완료 ══╗\n"
                f"  👤 {first_name}님\n\n"
                f"  🎁 획득: 100포인트\n"
                f"  💰 잔여: {total}포인트\n"
                f"  🔄 리셋: 매일 자정 00:00\n"
                f"╚══════════════════╝"
            )

        # ── /리필 ──────────────────────────────────────
        elif '/리필' in text:
            if message.chat.type == 'private': return
            db = get_db(); c = db.cursor()
            c.execute("SELECT COUNT(*) FROM refill_logs WHERE user_id=%s AND group_id=%s AND refill_date=%s",
                      (user_id, group_id, today))
            count = c.fetchone()[0]
            if count >= 5:
                c.close(); db.close()
                bot.reply_to(message, "⚠️ 오늘 리필을 5번 모두 사용했어요!\n자정(00:00)이 지나면 다시 사용할 수 있어요 😊")
                return
            c.execute("INSERT INTO refill_logs (user_id,group_id,first_name,username,refill_date) VALUES (%s,%s,%s,%s,%s)",
                      (user_id, group_id, first_name, username, today))
            db.commit(); c.close(); db.close()
            update_point(user_id, group_id, first_name, username, 100)
            bot.reply_to(message,
                f"╔══ 🔄 리필 완료 ══╗\n"
                f"  👤 {first_name}님\n\n"
                f"  🎁 획득: 100포인트\n"
                f"  💰 잔여: {get_point(user_id, group_id)}포인트\n"
                f"  📊 오늘 남은 리필: {5 - count - 1}회\n"
                f"  🔄 리셋: 매일 자정 00:00\n"
                f"╚══════════════════╝"
            )

        # ── /선물 ──────────────────────────────────────
        elif '/선물' in text:
            if message.chat.type == 'private':
                bot.reply_to(message, "⚠️ 선물은 그룹에서만 사용할 수 있어요!"); return
            if not message.reply_to_message:
                bot.reply_to(message, "🎁 선물할 상대의 메시지에 답장으로\n/선물 [포인트]\n\n예시: /선물 100\n\n⚠️ 최소: 10포인트"); return
            parts = text.split()
            if len(parts) < 2 or not parts[1].isdigit():
                bot.reply_to(message, "🎁 사용법: /선물 [포인트]\n예시: /선물 100"); return
            amount = int(parts[1])
            if amount < 10:
                bot.reply_to(message, "⚠️ 최소 선물 포인트는 10포인트예요!"); return
            target = message.reply_to_message.from_user
            if target.id == user_id:
                bot.reply_to(message, "⚠️ 자기 자신에게는 선물할 수 없어요!"); return
            if target.is_bot:
                bot.reply_to(message, "⚠️ 봇에게는 선물할 수 없어요!"); return
            my_point = get_point(user_id, group_id)
            if my_point < amount:
                bot.reply_to(message, f"💸 포인트 부족!\n  보유: {my_point}포인트\n  필요: {amount}포인트"); return
            target_name = target.first_name or '상대방'
            update_point(user_id, group_id, first_name, username, -amount)
            update_point(target.id, group_id, target_name, target.username or '', amount)
            bot.reply_to(message,
                f"╔══ 🎁 포인트 선물 ══╗\n"
                f"  💝 {first_name} → {target_name}\n\n"
                f"  🎀 선물: {amount}포인트\n\n"
                f"  📤 {first_name} 잔여: {get_point(user_id, group_id)}포인트\n"
                f"  📥 {target_name} 잔여: {get_point(target.id, group_id)}포인트\n"
                f"╚══════════════════╝"
            )

        # ── /포인트랭킹 ────────────────────────────────
        elif '/포인트랭킹' in text:
            if message.chat.type == 'private': return
            db = get_db(); c = db.cursor()
            c.execute("SELECT first_name,username,point FROM points WHERE group_id=%s ORDER BY point DESC LIMIT 5", (group_id,))
            rows = c.fetchall(); c.close(); db.close()
            medals = ['🥇','🥈','🥉','4️⃣','5️⃣']
            result = "╔══ 💰 포인트 랭킹 ══╗\n\n"
            for i, row in enumerate(rows):
                result += f"  {medals[i]} {row[0] or row[1] or '익명':<10} {row[2]}포인트\n"
            result += "╚══════════════════╝"
            bot.reply_to(message, result)

        # ── /포인트 ────────────────────────────────────
        elif '/포인트' in text:
            if message.chat.type == 'private': return
            bot.reply_to(message,
                f"╔══ 💰 포인트 ══╗\n"
                f"  👤 {first_name}님\n\n"
                f"  💰 잔여: {get_point(user_id, group_id)}포인트\n"
                f"╚══════════════════╝"
            )

        # ── /게임 ──────────────────────────────────────
        elif text.strip() in ['/게임', '/게임@dopamin_ranking_bot']:
            bot.reply_to(message,
                "🎮 게임 목록\n\n"
                "🎰 /슬롯 [배팅] - 슬롯머신\n"
                "🎡 /룰렛 [배팅] - 룰렛\n\n"
                "⚠️ 최소 배팅: 20포인트"
            )

        # ── /슬롯 ──────────────────────────────────────
        elif '/슬롯' in text:
            if message.chat.type == 'private': return
            parts = text.split()
            if len(parts) < 2 or not parts[1].isdigit():
                bot.reply_to(message, "🎰 사용법: /슬롯 [배팅포인트]\n예시: /슬롯 100"); return
            bet = int(parts[1])
            if bet < 20:
                bot.reply_to(message, "⚠️ 최소 배팅은 20포인트예요!"); return
            if get_point(user_id, group_id) < bet:
                bot.reply_to(message, f"💸 포인트 부족!\n현재: {get_point(user_id, group_id)}포인트"); return
            symbols = ['🍋','🍒','🍇','⭐','7️⃣','💎']
            weights = [30, 25, 20, 15, 7, 3]
            s1, s2, s3 = [random.choices(symbols, weights=weights)[0] for _ in range(3)]
            if s1 == s2 == s3:
                m, rt = {'💎':(50,"💎 JACKPOT! 50배!"),'7️⃣':(10,"7️⃣ 럭키세븐! 10배!"),'⭐':(7,"⭐ 스타! 7배!")}.get(s1,(5,"🎉 3개 일치! 5배!"))
                won = bet * m - bet
            elif s1==s2 or s2==s3 or s1==s3:
                won = int(bet*1.5)-bet; rt="✨ 2개 일치! 1.5배!"
            else:
                won = -bet; rt="💀 꽝!"
            update_point(user_id, group_id, first_name, username, won)
            bot.reply_to(message,
                f"╔══ 🎰 슬롯머신 ══╗\n"
                f"  [ {s1} | {s2} | {s3} ]\n\n"
                f"  {rt}\n\n"
                f"  배팅: {bet}포인트\n"
                f"  {'획득: +' if won>=0 else '손실: '}{won}포인트\n"
                f"  잔여: {get_point(user_id, group_id)}포인트\n"
                f"╚══════════════════╝"
            )

        # ── /룰렛 ──────────────────────────────────────
        elif '/룰렛' in text:
            if message.chat.type == 'private': return
            parts = text.split()
            if len(parts) < 2 or not parts[1].isdigit():
                bot.reply_to(message, "🎡 사용법: /룰렛 [배팅포인트]\n예시: /룰렛 100"); return
            bet = int(parts[1])
            if bet < 20:
                bot.reply_to(message, "⚠️ 최소 배팅은 20포인트예요!"); return
            if get_point(user_id, group_id) < bet:
                bot.reply_to(message, f"💸 포인트 부족!\n현재: {get_point(user_id, group_id)}포인트"); return
            roulette = [('💀 꽝',0,55),('🔵 1.5배',1.5,20),('🟢 2배',2,15),('🟡 3배',3,7),('🔴 5배',5,2),('💎 10배',10,1)]
            label, mult, _ = roulette[random.choices(range(len(roulette)), weights=[r[2] for r in roulette])[0]]
            won = int(bet*mult)-bet if mult>0 else -bet
            update_point(user_id, group_id, first_name, username, won)
            bot.reply_to(message,
                f"╔══ 🎡 룰렛 ══╗\n"
                f"  결과: {label}\n\n"
                f"  배팅: {bet}포인트\n"
                f"  {'획득: +' if won>=0 else '손실: '}{won}포인트\n"
                f"  잔여: {get_point(user_id, group_id)}포인트\n"
                f"╚══════════════════╝"
            )

        # ── /채팅랭킹 ──────────────────────────────────
        elif '/채팅랭킹' in text:
            if message.chat.type == 'private': return
            monday = today - timedelta(days=today.weekday())
            sunday = monday + timedelta(days=6)
            db = get_db(); c = db.cursor()
            c.execute(
                "SELECT first_name,username,COUNT(*) as cnt FROM chat_logs "
                "WHERE group_id=%s AND message_date>=%s "
                "GROUP BY user_id,first_name,username ORDER BY cnt DESC LIMIT 5",
                (group_id, monday)
            )
            rows = c.fetchall(); c.close(); db.close()
            medals = ['🥇','🥈','🥉','4️⃣','5️⃣']
            result  = f"╔══ 🏆 주간 랭킹 ══╗\n"
            result += f"  📅 {monday.strftime('%m/%d')} ~ {sunday.strftime('%m/%d')}\n\n"
            if rows:
                for i, r in enumerate(rows):
                    result += f"  {medals[i]} {r[0] or r[1] or '익명':<10} {r[2]}개\n"
            else:
                result += "  채팅 기록이 없어요 😅\n"
            result += "╚══════════════════╝"
            bot.reply_to(message, result)

        # ── /채팅 ──────────────────────────────────────
        elif '/채팅' in text:
            if message.chat.type == 'private': return
            monday = today - timedelta(days=today.weekday())
            db = get_db(); c = db.cursor()
            c.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND DATE(message_date)=%s", (user_id, group_id, today))
            today_count = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND message_date>=%s", (user_id, group_id, monday))
            week_count = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s "
                      "AND EXTRACT(YEAR FROM message_date)=EXTRACT(YEAR FROM NOW()) "
                      "AND EXTRACT(MONTH FROM message_date)=EXTRACT(MONTH FROM NOW())", (user_id, group_id))
            month_count = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s", (user_id, group_id))
            total_count = c.fetchone()[0]; c.close(); db.close()
            bot.reply_to(message,
                f"╔══ 📊 채팅 통계 ══╗\n"
                f"  👤 {first_name}님\n\n"
                f"  ☀️ 오늘       {today_count}개\n"
                f"  📆 이번 주   {week_count}개\n"
                f"  🗓 이번 달   {month_count}개\n"
                f"  💬 전체      {total_count}개\n\n"
                f"  🎀 오늘도 열심히 채팅했어요!\n"
                f"╚══════════════════╝"
            )

        # ── /야구 (안내 메시지) ────────────────────────
        elif text.strip().startswith('/야구'):
            if message.chat.type == 'private': return
            send_baseball_gif(group_id)
            team_list = "  " + "  /  ".join(KBO_TEAMS)
            bot.reply_to(message,
                f"⚾ KBO 승 예측 안내\n"
                f"{'─' * 23}\n\n"
                f"📋 선택 가능 팀 (10개):\n{team_list}\n\n"
                f"{'─' * 23}\n"
                f"✅ /승        — 버튼으로 5개 팀 선택\n"
                f"✏️  /수정     — 선택 변경\n"
                f"📋 /리스트  — 오늘 참여 현황\n"
                f"{'─' * 23}\n\n"
                f"⏰ 참여 시간: PM {VOTE_START} ~ {VOTE_END}\n"
                f"📅 참여 요일: 화 / 수 / 목 / 금\n"
                f"📌 10개 팀 중 5개만 선택 가능\n"
                f"📌 하루 1회 참여 (수정 가능)"
            )

        # ── /승 (인라인 키보드 팀 선택) ───────────────
        elif text.strip().startswith('/승'):
            if message.chat.type == 'private': return
            if not is_vote_time(now_kst):
                bot.reply_to(message,
                    f"🚫 지금은 참여할 수 없어요.\n\n"
                    f"📅 참여 가능 요일: 화 / 수 / 목 / 금\n"
                    f"⏰ 참여 가능 시간: PM {VOTE_START} ~ {VOTE_END}"
                ); return

            db = get_db(); c = db.cursor()
            c.execute("SELECT teams FROM kbo_votes WHERE user_id=%s AND group_id=%s AND vote_date=%s",
                      (user_id, group_id, today))
            existing = c.fetchone(); c.close(); db.close()

            if existing:
                existing_teams = existing[0].split(',')
                team_str = "\n".join([f"  {i+1}. {KBO_TEAMS_DISPLAY.get(t,t)}" for i,t in enumerate(existing_teams)])
                bot.reply_to(message,
                    f"⚠️ 이미 오늘 예측에 참여하셨어요!\n\n"
                    f"선택하신 팀:\n{team_str}\n\n"
                    f"수정하려면 /수정 을 사용하세요."
                ); return

            # GIF 전송 후 키보드 표시
            send_baseball_gif(group_id)
            selected = []
            set_pending(user_id, group_id, selected)
            sent = bot.send_message(
                group_id,
                build_vote_message(selected),
                reply_markup=build_team_keyboard(selected)
            )
            set_pending(user_id, group_id, selected, sent.message_id)

        # ── /수정 ──────────────────────────────────────
        elif text.strip().startswith('/수정'):
            if message.chat.type == 'private': return
            if not is_vote_time(now_kst):
                bot.reply_to(message,
                    f"🚫 지금은 수정할 수 없어요.\n\n"
                    f"📅 참여 가능 요일: 화 / 수 / 목 / 금\n"
                    f"⏰ 참여 가능 시간: PM {VOTE_START} ~ {VOTE_END}"
                ); return

            db = get_db(); c = db.cursor()
            c.execute("SELECT teams FROM kbo_votes WHERE user_id=%s AND group_id=%s AND vote_date=%s",
                      (user_id, group_id, today))
            existing = c.fetchone(); c.close(); db.close()

            if not existing:
                bot.reply_to(message,
                    "⚠️ 오늘 예측에 참여하지 않으셨어요!\n"
                    "/승 명령어로 먼저 예측에 참여해주세요."
                ); return

            # 기존 선택 불러와서 키보드 재표시
            send_baseball_gif(group_id)
            current_teams = existing[0].split(',')
            set_pending(user_id, group_id, current_teams)
            sent = bot.send_message(
                group_id,
                build_vote_message(current_teams),
                reply_markup=build_team_keyboard(current_teams)
            )
            set_pending(user_id, group_id, current_teams, sent.message_id)

        # ── /리스트 ────────────────────────────────────
        elif text.strip().startswith('/리스트'):
            if message.chat.type == 'private': return
            db = get_db(); c = db.cursor()
            c.execute("""SELECT first_name, username, teams FROM kbo_votes
                WHERE group_id=%s AND vote_date=%s ORDER BY created_at""",
                (group_id, today))
            rows = c.fetchall(); c.close(); db.close()

            if not rows:
                bot.reply_to(message, "📋 오늘 예측에 참여한 사람이 없어요!"); return

            send_baseball_gif(group_id)
            result  = f"╔══ ⚾ KBO 승 예측 리스트 ══╗\n"
            result += f"  📅 {today.strftime('%Y년 %m월 %d일')}\n"
            result += f"  👥 참여자: {len(rows)}명\n"
            result += f"  {'─' * 21}\n"
            for row in rows:
                name = row[0] or row[1] or '익명'
                teams_picked = row[2].split(',')
                team_icons = "  ".join([KBO_TEAMS_DISPLAY.get(t, t) for t in teams_picked])
                result += f"  👤 {name}\n  {team_icons}\n  {'─' * 21}\n"
            result += "╚══════════════════╝"
            bot.reply_to(message, result)

        # ── 메시지 기록 ────────────────────────────────
        elif message.chat.type in ['group', 'supergroup']:
            save_message(user_id, username, first_name, group_id)

    except Exception as e:
        import traceback
        print(f"handle_all error: {e}\n{traceback.format_exc()}")

# ─────────────────────────────────────────────────────────
# Flask 라우트
# ─────────────────────────────────────────────────────────
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    try:
        json_str = request.stream.read().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        if update.message:
            handle_all(update.message)
        elif update.callback_query:
            handle_kbo_callback(update.callback_query)
        print("처리 완료!")
    except Exception as e:
        import traceback
        print(f"webhook error: {e}\n{traceback.format_exc()}")
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
