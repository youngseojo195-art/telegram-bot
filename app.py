import os
import re
import json
import random
import telebot
import psycopg2
import requests
import urllib.parse
import pytz
import uuid
from telebot import types
from datetime import datetime, timedelta
from flask import Flask, request, send_from_directory

BOT_TOKEN = '8046489365:AAHAFBz4Ca07KcjqI0EJl76aIAu-rlVHw-4'
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

KST = pytz.timezone('Asia/Seoul')
UTC = pytz.utc

ADMIN_IDS = [8698678650, 8236798970, 8621088096, 7319936275]

BASEBALL_GIF_FILE_ID = "CgACAgUAAxkBAAMzagl3svn3G8Jr7JDeNhdXbodfQnIAAi8dAAJux0hUOyDPUXIJtRs7BA"
NAEJEON_GIF_FILE_ID  = "CgACAgUAAxkBAAOGag0cXgdCIn_PggmqSmC0GM0GnC4AAkofAAKWbGhUMjetimSM_S47BA"
AFFILIATE_GIF_URL    = "CgACAgUAAxkBAAM4agmS7OD4fz1bxh5zNQPn8VNCpysAAmYdAAJux0hUYXAsQb02yzs7BA"

def send_baseball_gif(chat_id):
    if not BASEBALL_GIF_FILE_ID: return
    try: bot.send_animation(chat_id=chat_id, animation=BASEBALL_GIF_FILE_ID)
    except Exception as e: print(f"야구 GIF 전송 실패: {e}")

def send_naejeon_gif(chat_id):
    if not NAEJEON_GIF_FILE_ID: return
    try: bot.send_animation(chat_id=chat_id, animation=NAEJEON_GIF_FILE_ID)
    except Exception as e: print(f"내전 GIF 전송 실패: {e}")

def send_affiliate_gif(chat_id):
    if not AFFILIATE_GIF_URL: return
    try: bot.send_animation(chat_id=chat_id, animation=AFFILIATE_GIF_URL)
    except Exception as e: print(f"제휴 GIF 전송 실패: {e}")

AFFILIATE_TEXT = """🎰 <b>카지노</b>
──────────────────
<b>[평생]</b> · <a href="https://t.me/gamte59/31">렛츠뱃</a>
<b>[평생]</b> · <a href="https://t.me/gamte59/28">예스뱃</a>
<b>[평생]</b> · <a href="https://t.me/gamte59/96">스피드벳</a>
<b>[평생]</b> · <a href="https://t.me/gamte59/94">띵벳</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/44">지엑스뱃</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/46">케이비씨겜</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/49">블록체인바카라</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/60">우루스뱃</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/62">마닐라</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/70">미우카지노</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/72">그랜드파리</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/74">룰라뱃</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/78">소울카지노</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/84">123GAME카지노</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/100">벨라벳</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/100">부자벳</a>

💸 <b>급전</b>
──────────────────
<b>[도파민]</b> · <a href="https://t.me/gamte59/16">OR급전</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/77">빅딜OTC</a>

🏠 <b>장집</b>
──────────────────
<b>[도파민]</b> · <a href="https://t.me/gamte59/76">빅딜 장집</a>

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

KBO_TEAMS = ['KT', '삼성', 'LG', 'SSG', 'KIA', '한화', '두산', 'NC', '롯데', '키움']
KBO_TEAMS_DISPLAY = {
    'KT':'🔴 KT','삼성':'🔵 삼성','LG':'🔴 LG','SSG':'🟡 SSG','KIA':'🔴 KIA',
    '한화':'🟠 한화','두산':'🔵 두산','NC':'🔵 NC','롯데':'🔴 롯데','키움':'🟣 키움',
}

WEBAPP_BASE_URL = os.environ.get('WEBAPP_URL', 'https://telegram-bot-14vg.onrender.com')
VOTE_START = "18:00"
VOTE_END   = "18:30"

def build_team_keyboard(selected):
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for team in KBO_TEAMS:
        label = f"✅ {team}" if team in selected else KBO_TEAMS_DISPLAY.get(team, team)
        buttons.append(types.InlineKeyboardButton(text=label, callback_data=f"kbo_toggle:{team}"))
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

def build_vote_message(selected):
    count = len(selected)
    if count == 0: status = "팀을 선택해주세요"
    elif count < 5: status = f"{count}개 선택 — {5 - count}개 더 선택하세요"
    else: status = "5개 선택 완료! 제출하기를 눌러주세요 ✅"
    lines = ["⚾ KBO 승 예측 — 팀 선택", "", f"📊 {status}", ""]
    for t in selected:
        lines.append(f"   • {KBO_TEAMS_DISPLAY.get(t, t)}")
    return "\n".join(lines)

def clean_name(name):
    if not name: return ''
    return (name.strip()
            .replace('\u3164','').replace('\u200b','')
            .replace('\u200c','').replace('\u200d','')
            .replace('\ufeff','').strip())

def get_db():
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def to_utc_iso(dt):
    """datetime → JS가 확실히 인식하는 UTC ISO 문자열 (Z 접미사)"""
    if dt is None: return None
    if dt.tzinfo is None:
        dt = UTC.localize(dt)
    else:
        dt = dt.astimezone(UTC)
    return dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')

def safe_mins(v):
    """mins 값 안전 변환. None/빈값/0 → None"""
    try:
        i = int(v)
        return i if i > 0 else None
    except (ValueError, TypeError):
        return None

def init_db():
    db = get_db(); c = db.cursor()
    try:
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
        c.execute("""CREATE TABLE IF NOT EXISTS naejeon_rooms (
            id SERIAL PRIMARY KEY,
            room_id VARCHAR(50) NOT NULL UNIQUE,
            group_id BIGINT NOT NULL,
            game_type VARCHAR(10) NOT NULL,
            slots JSONB NOT NULL DEFAULT '{}',
            status VARCHAR(20) DEFAULT 'open',
            extra_text TEXT DEFAULT '',
            pos_a JSONB DEFAULT '[]',
            pos_b JSONB DEFAULT '[]',
            started BOOLEAN DEFAULT FALSE,
            fund_type VARCHAR(10) DEFAULT '',
            fund_amount TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT NOW())""")
        c.execute("""CREATE TABLE IF NOT EXISTS naejeon_events (
            room_id VARCHAR(50) PRIMARY KEY,
            end_time TIMESTAMP NOT NULL,
            winner_count INTEGER NOT NULL,
            reward_text TEXT NOT NULL,
            is_active BOOLEAN DEFAULT FALSE)""")
        c.execute("""CREATE TABLE IF NOT EXISTS vote_rooms (
            room_id    VARCHAR(50) PRIMARY KEY,
            group_id   BIGINT NOT NULL,
            admin_id   BIGINT NOT NULL,
            content    TEXT DEFAULT '',
            mins       INTEGER,
            winners    INTEGER DEFAULT 1,
            anim_style VARCHAR(20) DEFAULT 'slot',
            started    BOOLEAN DEFAULT FALSE,
            ended      BOOLEAN DEFAULT FALSE,
            end_time   TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW())""")
        c.execute("""CREATE TABLE IF NOT EXISTS vote_participants (
            id        SERIAL PRIMARY KEY,
            room_id   VARCHAR(50) NOT NULL,
            user_id   BIGINT NOT NULL,
            name      VARCHAR(255),
            joined_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(room_id, user_id))""")
        for col in [
            ("extra_text","TEXT DEFAULT ''"),("pos_a","JSONB DEFAULT '[]'"),
            ("pos_b","JSONB DEFAULT '[]'"),("started","BOOLEAN DEFAULT FALSE"),
            ("fund_type","VARCHAR(10) DEFAULT ''"),("fund_amount","TEXT DEFAULT ''"),
        ]:
            try:
                c.execute(f"ALTER TABLE naejeon_rooms ADD COLUMN IF NOT EXISTS {col[0]} {col[1]}")
                db.commit()
            except: db.rollback()
        try:
            c.execute("ALTER TABLE points ALTER COLUMN last_attendance TYPE DATE USING last_attendance::DATE")
            db.commit()
        except: db.rollback()

        # ── 카지노 테이블 ──
        casino_ddl = [
            """CREATE TABLE IF NOT EXISTS casino_games (
                id SERIAL PRIMARY KEY, game_id VARCHAR(30) NOT NULL,
                group_id BIGINT NOT NULL, status VARCHAR(20) DEFAULT 'open',
                result VARCHAR(50), settings JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW(), ended_at TIMESTAMP)""",
            """CREATE TABLE IF NOT EXISTS casino_bets (
                id SERIAL PRIMARY KEY, game_id VARCHAR(30) NOT NULL,
                round_id INTEGER REFERENCES casino_games(id),
                group_id BIGINT NOT NULL, user_id BIGINT NOT NULL,
                user_name VARCHAR(255), bet_on VARCHAR(50) NOT NULL,
                amount INTEGER NOT NULL, payout INTEGER DEFAULT 0,
                won BOOLEAN, created_at TIMESTAMP DEFAULT NOW())""",
            """CREATE TABLE IF NOT EXISTS casino_settings (
                group_id BIGINT NOT NULL, game_id VARCHAR(30) NOT NULL,
                settings JSONB DEFAULT '{}',
                updated_at TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (group_id, game_id))""",
            """CREATE TABLE IF NOT EXISTS casino_blacklist (
                group_id BIGINT NOT NULL, user_id BIGINT NOT NULL,
                reason TEXT, created_at TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (group_id, user_id))""",
            """CREATE TABLE IF NOT EXISTS point_logs (
                id SERIAL PRIMARY KEY, group_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL, user_name VARCHAR(255),
                amount INTEGER NOT NULL, reason TEXT,
                admin_id BIGINT, created_at TIMESTAMP DEFAULT NOW())""",
        ]
        for ddl in casino_ddl:
            try: c.execute(ddl); db.commit()
            except: db.rollback()
        db.commit()
    finally:
        c.close(); db.close()

def get_point(user_id, group_id):
    db = get_db(); c = db.cursor()
    try:
        c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
        row = c.fetchone()
        return row[0] if row else 0
    finally: c.close(); db.close()

def update_point(user_id, group_id, first_name, username, amount):
    db = get_db(); c = db.cursor()
    try:
        c.execute("""INSERT INTO points (user_id, group_id, first_name, username, point)
            VALUES (%s,%s,%s,%s,%s) ON CONFLICT (user_id, group_id)
            DO UPDATE SET point=points.point+%s, first_name=%s, username=%s""",
            (user_id, group_id, first_name, username, amount, amount, first_name, username))
        db.commit()
    finally: c.close(); db.close()

def save_message(user_id, username, first_name, group_id):
    db = get_db(); c = db.cursor()
    try:
        c.execute("INSERT INTO chat_logs (user_id,username,first_name,group_id,message_date) VALUES (%s,%s,%s,%s,%s)",
                  (user_id, username, first_name, group_id, datetime.now()))
        db.commit()
    finally: c.close(); db.close()

def get_pending_with_group(user_id):
    db = get_db(); c = db.cursor()
    try:
        c.execute("SELECT group_id, selected, message_id FROM kbo_pending WHERE user_id=%s LIMIT 1", (user_id,))
        row = c.fetchone()
        if row:
            return (row[0], [t for t in row[1].split(',') if t]), row[2]
        return None, None
    finally: c.close(); db.close()

def set_pending(user_id, group_id, selected, message_id=None):
    db = get_db(); c = db.cursor()
    try:
        s = ','.join(selected)
        c.execute("""INSERT INTO kbo_pending (user_id, group_id, selected, message_id)
            VALUES (%s,%s,%s,%s) ON CONFLICT (user_id, group_id)
            DO UPDATE SET selected=%s, message_id=%s""",
            (user_id, group_id, s, message_id, s, message_id))
        db.commit()
    finally: c.close(); db.close()

def clear_pending(user_id, group_id):
    db = get_db(); c = db.cursor()
    try:
        c.execute("DELETE FROM kbo_pending WHERE user_id=%s AND group_id=%s", (user_id, group_id))
        db.commit()
    finally: c.close(); db.close()

def is_vote_time(now_kst):
    if now_kst.weekday() not in [1, 2, 3, 4]: return False
    cur = now_kst.time()
    return (datetime.strptime(VOTE_START, "%H:%M").time()
            <= cur <=
            datetime.strptime(VOTE_END, "%H:%M").time())

def get_usdt_rate():
    try:
        r = requests.get('https://api.upbit.com/v1/ticker?markets=KRW-USDT', timeout=5)
        if r.status_code == 200: return float(r.json()[0]['trade_price'])
    except: pass
    try:
        r = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=USDTKRW', timeout=5)
        if r.status_code == 200: return float(r.json()['price'])
    except: pass
    return None

# ─────────────────────────────────────────────────────────
# 콜백 핸들러
# ─────────────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda call: call.data.startswith('nj_open:'))
def handle_nj_open(call):
    try:
        user_id = call.from_user.id; group_id = call.message.chat.id
        if user_id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "⚠️ 관리자만 사용할 수 있어요!", show_alert=True); return
        parts = call.data.split(':', 2)
        game_type = parts[1]; extra_text = parts[2] if len(parts) > 2 else ''
        game_names = {'sa5':'서든어택 5v5','sa6':'서든어택 6v6'}
        display_name = game_names.get(game_type, '서든어택')
        db = get_db(); c = db.cursor()
        try:
            c.execute("SELECT room_id FROM naejeon_rooms WHERE group_id=%s AND game_type=%s AND status='open'", (group_id, game_type))
            if c.fetchone():
                bot.answer_callback_query(call.id, "⚠️ 이미 진행 중인 내전이 있어요!", show_alert=True); return
            room_id = str(uuid.uuid4())[:8]
            c.execute("INSERT INTO naejeon_rooms (room_id, group_id, game_type, slots, extra_text) VALUES (%s,%s,%s,%s,%s)",
                      (room_id, group_id, game_type, '{}', extra_text))
            db.commit()
        finally: c.close(); db.close()
        param = f"{user_id}_{group_id}_{game_type}_{room_id}"
        nj_url = f"{WEBAPP_BASE_URL}/naejeon?start={param}"
        msg = f"⚔️ {display_name} 내전 모집!"
        if extra_text: msg += f"\n{extra_text}"
        msg += "\n\n아래 버튼을 눌러 참여하세요!\n⚠️ 처음 참여하시는 분은 @dopamin_ranking_bot 을 눌러 START 를 먼저 눌러주세요!"
        send_naejeon_gif(group_id)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚔️ 내전 참여하기", url=nj_url))
        bot.edit_message_text(msg, chat_id=group_id, message_id=call.message.message_id, reply_markup=markup)
        bot.answer_callback_query(call.id, f"✅ {display_name} 내전 시작!")
    except Exception as e:
        import traceback; print(f"nj_open error: {e}\n{traceback.format_exc()}")
        bot.answer_callback_query(call.id, "오류가 발생했어요.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('kbo_'))
def handle_kbo_callback(call):
    try:
        user_id = call.from_user.id; first_name = call.from_user.first_name or '사용자'
        username = call.from_user.username or ''; now_kst = datetime.now(KST)
        today = now_kst.date(); action = call.data
        if not is_vote_time(now_kst):
            bot.answer_callback_query(call.id, f"⏰ 화~금 {VOTE_START}~{VOTE_END} 사이에만 참여 가능해요!", show_alert=True); return
        selected_data, msg_id = get_pending_with_group(user_id)
        if selected_data is None:
            bot.answer_callback_query(call.id, "⚠️ 세션이 만료됐어요. 그룹에서 /승 을 다시 입력해주세요.", show_alert=True); return
        group_id = selected_data[0]; selected = selected_data[1]
        db = get_db(); c = db.cursor()
        try:
            c.execute("SELECT teams FROM kbo_votes WHERE user_id=%s AND group_id=%s AND vote_date=%s", (user_id, group_id, today))
            already = c.fetchone()
        finally: c.close(); db.close()
        if action == "kbo_noop":
            bot.answer_callback_query(call.id, "이미 제출하셨어요!" if already else f"5개를 선택해야 제출할 수 있어요! (현재 {len(selected)}개)"); return
        elif action == "kbo_reset":
            selected = []; set_pending(user_id, group_id, selected, call.message.message_id)
            bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id,
                text=build_vote_message(selected), reply_markup=build_team_keyboard(selected))
            bot.answer_callback_query(call.id, "초기화 됐어요!")
        elif action.startswith("kbo_toggle:"):
            team = action.split(":")[1]
            if team in selected:
                selected.remove(team); bot.answer_callback_query(call.id, f"{KBO_TEAMS_DISPLAY.get(team, team)} 선택 취소")
            else:
                if len(selected) >= 5:
                    bot.answer_callback_query(call.id, "이미 5개 선택! 초기화 후 다시 선택하세요.", show_alert=True); return
                selected.append(team); bot.answer_callback_query(call.id, f"{KBO_TEAMS_DISPLAY.get(team, team)} 선택! ({len(selected)}/5)")
            set_pending(user_id, group_id, selected, call.message.message_id)
            bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id,
                text=build_vote_message(selected), reply_markup=build_team_keyboard(selected))
        elif action == "kbo_submit":
            if len(selected) != 5:
                bot.answer_callback_query(call.id, "5개를 선택해야 제출할 수 있어요!", show_alert=True); return
            teams_str = ','.join(selected)
            db = get_db(); c = db.cursor()
            try:
                if already:
                    c.execute("UPDATE kbo_votes SET teams=%s, first_name=%s, username=%s WHERE user_id=%s AND group_id=%s AND vote_date=%s",
                        (teams_str, first_name, username, user_id, group_id, today))
                    action_label = "수정 완료"
                else:
                    c.execute("INSERT INTO kbo_votes (user_id, group_id, first_name, username, teams, vote_date) VALUES (%s,%s,%s,%s,%s,%s)",
                        (user_id, group_id, first_name, username, teams_str, today))
                    action_label = "예측 완료"
                c.execute("SELECT COUNT(*) FROM kbo_votes WHERE group_id=%s AND vote_date=%s", (group_id, today))
                total = c.fetchone()[0]; db.commit()
            finally: c.close(); db.close()
            clear_pending(user_id, group_id)
            team_display = "\n".join([f"   {i+1}. {KBO_TEAMS_DISPLAY.get(t,t)}" for i, t in enumerate(selected)])
            bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id,
                text=(f"╔══ ⚾ KBO 승 {action_label} ══╗\n   👤 {first_name}님\n\n"
                      f"   선택한 팀 (5개):\n{team_display}\n\n"
                      f"   👥 오늘 참여자: {total}명\n   ✏️ 수정: 그룹에서 /수정 입력\n╚══════════════════╝"),
                reply_markup=None)
            bot.answer_callback_query(call.id, f"✅ {action_label}!")
    except Exception as e:
        import traceback; print(f"kbo callback error: {e}\n{traceback.format_exc()}")
        bot.answer_callback_query(call.id, "오류가 발생했어요. 다시 시도해주세요.")

# ─────────────────────────────────────────────────────────
# 메시지 핸들러
# ─────────────────────────────────────────────────────────
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    try:
        text = message.text or ''; user_id = message.from_user.id
        group_id = message.chat.id; first_name = message.from_user.first_name or '사용자'
        username = message.from_user.username or ''; now_kst = datetime.now(KST); today = now_kst.date()

        if '/test' in text:
            bot.reply_to(message, f"봇 작동 중! ✅\n내 user_id: {user_id}")

        elif '/포인트복구' in text:
            if user_id not in ADMIN_IDS: bot.reply_to(message, "⚠️ 관리자만 사용할 수 있어요!"); return
            db = get_db(); c = db.cursor()
            try:
                c.execute("SELECT user_id, first_name, username, point FROM points WHERE group_id=%s ORDER BY point DESC", (group_id,))
                rows = c.fetchall()
            finally: c.close(); db.close()
            if not rows: bot.reply_to(message, "포인트 기록이 없어요."); return
            result = "╔══ 🔧 포인트 현황 ══╗\n\n"
            for row in rows:
                result += f"   • {row[1] or row[2] or '익명'} (id:{row[0]}): {row[3]:,}P\n"
            result += "\n   /포인트설정 [이름] [포인트]\n   /전체포인트초기화 확인\n╚══════════════════╝"
            bot.reply_to(message, result)

        elif '/포인트설정' in text:
            if user_id not in ADMIN_IDS: bot.reply_to(message, "⚠️ 관리자만 사용할 수 있어요!"); return
            parts = text.split()
            if len(parts) < 3 or not parts[2].isdigit(): bot.reply_to(message, "🔧 사용법: /포인트설정 [이름] [포인트]"); return
            target_name = parts[1]; new_pt = int(parts[2])
            db = get_db(); c = db.cursor()
            try:
                c.execute("UPDATE points SET point=%s WHERE first_name=%s AND group_id=%s", (new_pt, target_name, group_id))
                affected = c.rowcount; db.commit()
            finally: c.close(); db.close()
            bot.reply_to(message, f"✅ {target_name}님 포인트를 {new_pt:,}P로 설정했어요!" if affected > 0 else f"⚠️ {target_name}님을 찾을 수 없어요!")

        elif '/전체포인트초기화' in text:
            if user_id not in ADMIN_IDS: bot.reply_to(message, "⚠️ 관리자만 사용할 수 있어요!"); return
            if '확인' not in text: bot.reply_to(message, "⚠️ /전체포인트초기화 확인 이라고 입력하세요!"); return
            db = get_db(); c = db.cursor()
            try:
                c.execute("UPDATE points SET point=0 WHERE group_id=%s", (group_id,))
                affected = c.rowcount; db.commit()
            finally: c.close(); db.close()
            bot.reply_to(message, f"✅ {affected}명의 포인트를 전체 초기화했어요!")

        elif '/getfileid' in text:
            if message.reply_to_message:
                msg = message.reply_to_message; file_id = None
                if msg.animation: file_id = msg.animation.file_id
                elif msg.video: file_id = msg.video.file_id
                elif msg.document: file_id = msg.document.file_id
                if file_id: bot.reply_to(message, f"📋 file_id:\n\n<code>{file_id}</code>", parse_mode='HTML')
                else: bot.reply_to(message, "⚠️ GIF나 영상 메시지에 답장해서 사용하세요.")
            else: bot.reply_to(message, "GIF/영상 메시지에 답장으로 /getfileid 를 입력하세요!")

        elif '/노래' in text:
            query = text.replace('/노래', '').strip()
            if not query: bot.reply_to(message, "🎵 검색어를 입력해주세요!"); return
            bot.reply_to(message, f"🎵 {query}\n\n🔗 유튜브:\nhttps://www.youtube.com/results?search_query={urllib.parse.quote(query)}")

        elif '/제휴' in text:
            send_affiliate_gif(group_id)
            bot.reply_to(message, AFFILIATE_TEXT, parse_mode='HTML', disable_web_page_preview=True)

        elif re.search(r'(\d+(\.\d+)?)\s*테더', text):
            match = re.search(r'(\d+(\.\d+)?)\s*테더', text); amount = float(match.group(1))
            rate = get_usdt_rate()
            if rate is None: bot.reply_to(message, "⚠️ 환율 정보를 가져오지 못했어요."); return
            bot.reply_to(message, f"💰 USDT 환율 계산\n\n📈 현재 환율: {rate:,.0f}원\n💵 {amount:,.0f} USDT: {amount * rate:,.0f}원")

        elif '/출석' in text:
            if message.chat.type == 'private': return
            db = get_db(); c = db.cursor()
            try:
                c.execute("SELECT last_attendance FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
                row = c.fetchone()
                if row and row[0] == today: bot.reply_to(message, "⏰ 오늘 이미 출석했어요!"); return
                c.execute("""INSERT INTO points (user_id,group_id,first_name,username,point,last_attendance)
                    VALUES (%s,%s,%s,%s,100,%s) ON CONFLICT (user_id,group_id)
                    DO UPDATE SET point=points.point+100, last_attendance=%s, first_name=%s, username=%s""",
                    (user_id, group_id, first_name, username, today, today, first_name, username))
                db.commit()
                c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
                total = c.fetchone()[0]
            finally: c.close(); db.close()
            bot.reply_to(message, f"╔══ ✅ 출석 완료 ══╗\n   👤 {first_name}님\n\n   🎁 획득: 100포인트\n   💰 잔여: {total}포인트\n   🔄 리셋: 매일 자정 00:00\n╚══════════════════╝")

        elif '/리필' in text:
            if message.chat.type == 'private': return
            db = get_db(); c = db.cursor()
            try:
                c.execute("SELECT COUNT(*) FROM refill_logs WHERE user_id=%s AND group_id=%s AND refill_date=%s", (user_id, group_id, today))
                count = c.fetchone()[0]
                if count >= 5: bot.reply_to(message, "⚠️ 오늘 리필을 5번 모두 사용했어요!"); return
                c.execute("INSERT INTO refill_logs (user_id,group_id,first_name,username,refill_date) VALUES (%s,%s,%s,%s,%s)", (user_id, group_id, first_name, username, today))
                db.commit()
            finally: c.close(); db.close()
            update_point(user_id, group_id, first_name, username, 100)
            bot.reply_to(message, f"╔══ 🔄 리필 완료 ══╗\n   👤 {first_name}님\n\n   🎁 획득: 100포인트\n   💰 잔여: {get_point(user_id, group_id)}포인트\n   📊 오늘 남은 리필: {5 - count - 1}회\n   🔄 리셋: 매일 자정 00:00\n╚══════════════════╝")

        elif '/선물' in text:
            if message.chat.type == 'private': bot.reply_to(message, "⚠️ 선물은 그룹에서만 사용할 수 있어요!"); return
            if not message.reply_to_message: bot.reply_to(message, "🎁 선물할 상대의 메시지에 답장으로\n/선물 [포인트]\n⚠️ 최소: 10포인트"); return
            parts = text.split()
            if len(parts) < 2 or not parts[1].isdigit(): bot.reply_to(message, "🎁 사용법: /선물 [포인트]"); return
            amount = int(parts[1])
            if amount < 10: bot.reply_to(message, "⚠️ 최소 선물 포인트는 10포인트예요!"); return
            target = message.reply_to_message.from_user
            if target.id == user_id: bot.reply_to(message, "⚠️ 자기 자신에게는 선물할 수 없어요!"); return
            if target.is_bot: bot.reply_to(message, "⚠️ 봇에게는 선물할 수 없어요!"); return
            my_point = get_point(user_id, group_id)
            if my_point < amount: bot.reply_to(message, f"💸 포인트 부족!\n  보유: {my_point}포인트\n  필요: {amount}포인트"); return
            target_name = target.first_name or '상대방'
            update_point(user_id, group_id, first_name, username, -amount)
            update_point(target.id, group_id, target_name, target.username or '', amount)
            bot.reply_to(message, f"╔══ 🎁 포인트 선물 ══╗\n   💝 {first_name} → {target_name}\n\n   🎀 선물: {amount}포인트\n\n   📤 {first_name} 잔여: {get_point(user_id, group_id)}포인트\n   📥 {target_name} 잔여: {get_point(target.id, group_id)}포인트\n╚══════════════════╝")

        elif '/포인트랭킹' in text:
            if message.chat.type == 'private': return
            db = get_db(); c = db.cursor()
            try:
                c.execute("SELECT first_name,username,point FROM points WHERE group_id=%s ORDER BY point DESC LIMIT 5", (group_id,))
                rows = c.fetchall()
            finally: c.close(); db.close()
            medals = ['🥇','🥈','🥉','4️⃣','5️⃣']
            result = "╔══ 💰 포인트 랭킹 ══╗\n\n"
            for i, row in enumerate(rows):
                result += f"   {medals[i]} {row[0] or row[1] or '익명':<10} {row[2]}포인트\n"
            bot.reply_to(message, result + "╚══════════════════╝")

        elif '/포인트' in text:
            if message.chat.type == 'private': return
            bot.reply_to(message, f"╔══ 💰 포인트 ══╗\n   👤 {first_name}님\n\n   💰 잔여: {get_point(user_id, group_id)}포인트\n╚══════════════════╝")

        elif text.strip() in ['/게임', '/게임@dopamin_ranking_bot']:
            bot.reply_to(message, "🎮 게임 목록\n\n🎰 /슬롯 [배팅] - 슬롯머신\n🎡 /룰렛 [배팅] - 룰렛\n⚠️ 최소 배팅: 20포인트")

        elif '/슬롯' in text:
            if message.chat.type == 'private': return
            parts = text.split()
            if len(parts) < 2 or not parts[1].isdigit(): bot.reply_to(message, "🎰 사용법: /슬롯 [배팅포인트]"); return
            bet = int(parts[1])
            if bet < 20: bot.reply_to(message, "⚠️ 최소 배팅은 20포인트예요!"); return
            if get_point(user_id, group_id) < bet: bot.reply_to(message, f"💸 포인트 부족!\n현재: {get_point(user_id, group_id)}포인트"); return
            symbols = ['🍋','🍒','🍇','⭐','7️⃣','💎']; weights = [30, 25, 20, 15, 7, 3]
            s1, s2, s3 = [random.choices(symbols, weights=weights)[0] for _ in range(3)]
            if s1 == s2 == s3:
                m, rt = {'💎':(50,"💎 JACKPOT! 50배!"),'7️⃣':(10,"7️⃣ 럭키세븐! 10배!"),'⭐':(7,"⭐ 스타! 7배!")}.get(s1,(5,"🎉 3개 일치! 5배!"))
                won = bet * m - bet
            elif s1==s2 or s2==s3 or s1==s3: won = int(bet*1.5)-bet; rt="✨ 2개 일치! 1.5배!"
            else: won = -bet; rt="💀 꽝!"
            update_point(user_id, group_id, first_name, username, won)
            bot.reply_to(message, f"╔══ 🎰 슬롯머신 ══╗\n   [ {s1} | {s2} | {s3} ]\n\n   {rt}\n\n   배팅: {bet}포인트\n   {'획득: +' if won>=0 else '손실: '}{won}포인트\n   잔여: {get_point(user_id, group_id)}포인트\n╚══════════════════╝")

        elif '/룰렛' in text:
            if message.chat.type == 'private': return
            parts = text.split()
            if len(parts) < 2 or not parts[1].isdigit(): bot.reply_to(message, "🎡 사용법: /룰렛 [배팅포인트]"); return
            bet = int(parts[1])
            if bet < 20: bot.reply_to(message, "⚠️ 최소 배팅은 20포인트예요!"); return
            if get_point(user_id, group_id) < bet: bot.reply_to(message, f"💸 포인트 부족!\n현재: {get_point(user_id, group_id)}포인트"); return
            roulette = [('💀 꽝',0,55),('🔵 1.5배',1.5,20),('🟢 2배',2,15),('🟡 3배',3,7),('🔴 5배',5,2),('💎 10배',10,1)]
            label, mult, _ = roulette[random.choices(range(len(roulette)), weights=[r[2] for r in roulette])[0]]
            won = int(bet*mult)-bet if mult>0 else -bet
            update_point(user_id, group_id, first_name, username, won)
            bot.reply_to(message, f"╔══ 🎡 룰렛 ══╗\n   결과: {label}\n\n   배팅: {bet}포인트\n   {'획득: +' if won>=0 else '손실: '}{won}포인트\n   잔여: {get_point(user_id, group_id)}포인트\n╚══════════════════╝")

        elif '/채팅랭킹' in text:
            if message.chat.type == 'private': return
            monday = today - timedelta(days=today.weekday()); sunday = monday + timedelta(days=6)
            db = get_db(); c = db.cursor()
            try:
                c.execute("SELECT first_name,username,COUNT(*) as cnt FROM chat_logs WHERE group_id=%s AND message_date>=%s GROUP BY user_id,first_name,username ORDER BY cnt DESC LIMIT 5", (group_id, monday))
                rows = c.fetchall()
            finally: c.close(); db.close()
            medals = ['🥇','🥈','🥉','4️⃣','5️⃣']
            result = f"╔══ 🏆 주간 랭킹 ══╗\n   📅 {monday.strftime('%m/%d')} ~ {sunday.strftime('%m/%d')}\n\n"
            for i, r in enumerate(rows):
                result += f"   {medals[i]} {r[0] or r[1] or '익명':<10} {r[2]}개\n"
            if not rows: result += "   채팅 기록이 없어요 😅\n"
            bot.reply_to(message, result + "╚══════════════════╝")

        elif '/채팅' in text:
            if message.chat.type == 'private': return
            monday = today - timedelta(days=today.weekday())
            db = get_db(); c = db.cursor()
            try:
                c.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND DATE(message_date)=%s", (user_id, group_id, today))
                today_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND message_date>=%s", (user_id, group_id, monday))
                week_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND EXTRACT(YEAR FROM message_date)=EXTRACT(YEAR FROM NOW()) AND EXTRACT(MONTH FROM message_date)=EXTRACT(MONTH FROM NOW())", (user_id, group_id))
                month_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s", (user_id, group_id))
                total_count = c.fetchone()[0]
            finally: c.close(); db.close()
            bot.reply_to(message, f"╔══ 📊 채팅 통계 ══╗\n   👤 {first_name}님\n\n   ☀️ 오늘       {today_count}개\n   이번 주   {week_count}개\n   🗓 이번 달   {month_count}개\n   💬 전체      {total_count}개\n\n   🎀 오늘도 열심히 채팅했어요!\n╚══════════════════╝")

        elif text.strip().startswith('/야구'):
            if message.chat.type == 'private': return
            send_baseball_gif(group_id)
            kbo_url = f"{WEBAPP_BASE_URL}/kbo?start={user_id}_{group_id}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚾ KBO 승 예측 참여하기", url=kbo_url))
            bot.reply_to(message,
                f"⚾ <b>KBO 승 예측</b>\n──────────────────\n"
                f"📅 참여 요일: 화 / 수 / 목 / 금\n"
                f"⏰ 참여 시간: {VOTE_START} ~ {VOTE_END}\n"
                f"📌 10개 팀 중 5개 선택\n──────────────────\n"
                f"아래 버튼을 눌러 바로 참여하세요!",
                reply_markup=markup, parse_mode='HTML')

        elif text.strip().startswith('/승'):
            if message.chat.type == 'private': return
            kbo_url = f"{WEBAPP_BASE_URL}/kbo?start={user_id}_{group_id}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚾ KBO 승 예측 참여하기", url=kbo_url))
            bot.reply_to(message, "⚾ 아래 버튼을 눌러 KBO 승 예측에 참여하세요!", reply_markup=markup)

        elif text.strip().startswith('/수정'):
            if message.chat.type == 'private': return
            kbo_url = f"{WEBAPP_BASE_URL}/kbo?start={user_id}_{group_id}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚾ KBO 승 예측 수정하기", url=kbo_url))
            bot.reply_to(message, "⚾ 아래 버튼을 눌러 예측을 수정하세요!", reply_markup=markup)

        elif text.strip().startswith('/리스트'):
            if message.chat.type == 'private': return
            kbo_url = f"{WEBAPP_BASE_URL}/kbo?start={user_id}_{group_id}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📋 참여 목록 보기", url=kbo_url))
            bot.reply_to(message, "⚾ 아래 버튼을 눌러 오늘 참여 목록을 확인하세요!", reply_markup=markup)

        elif text.strip().startswith('/내전수정'):
            if message.chat.type == 'private': return
            if user_id not in ADMIN_IDS: bot.reply_to(message, "⚠️ 관리자만 내전을 수정할 수 있어요!"); return
            parts = text.strip().split(); game_arg = parts[1] if len(parts) > 1 else ''
            game_map = {'롤':'lol','서든':'sa5','lol':'lol','sa':'sa5','sa5':'sa5','sa6':'sa6'}
            game_type = game_map.get(game_arg)
            if not game_type: bot.reply_to(message, "⚔️ 사용법: /내전수정 롤  또는  /내전수정 서든"); return
            db = get_db(); c = db.cursor()
            try:
                c.execute("SELECT room_id FROM naejeon_rooms WHERE group_id=%s AND game_type=%s ORDER BY created_at DESC LIMIT 1", (group_id, game_type))
                row = c.fetchone()
                if not row: bot.reply_to(message, "⚠️ 수정할 수 있는 최근 내전 기록이 없습니다."); return
                room_id = row[0]
            finally: c.close(); db.close()
            param = f"{user_id}_{group_id}_{game_type}_{room_id}"
            nj_url = f"{WEBAPP_BASE_URL}/naejeon?start={param}&mode=edit"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🛠 내전 강제 수정하기", url=nj_url))
            bot.reply_to(message, "👑 관리자 전용 내전 마스터 수정 링크가 생성되었습니다.", reply_markup=markup)

        elif text.strip().startswith('/카지노'):
            if message.chat.type == 'private': return
            casino_url = f"{WEBAPP_BASE_URL}/casino?userId={user_id}&groupId={group_id}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🎰 카지노 입장", url=casino_url))
            bot.reply_to(message,
                "🎰 <b>도파민 카지노</b>\n──────────────────\n"
                "🐢 토끼 vs 거북이\n🃏 바카라\n🐴 경마\n🎡 빅휠\n"
                "──────────────────\n"
                "아래 버튼을 눌러 입장하세요!",
                reply_markup=markup, parse_mode='HTML')

        elif text.strip().startswith('/카지노관리') or text.strip().startswith('/casino_admin'):
            if user_id not in ADMIN_IDS:
                bot.reply_to(message, "⚠️ 관리자만 사용할 수 있어요!"); return
            admin_url = f"{WEBAPP_BASE_URL}/casino/admin?adminId={user_id}&groupId={group_id}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("👑 관리자 페이지", url=admin_url))
            bot.reply_to(message, "👑 카지노 관리자 페이지", reply_markup=markup)

        # ── /투표 ── ★ | 구분자 사용 (음수 groupId 문제 해결) ★
        elif text.strip().startswith('/투표'):
            if message.chat.type == 'private': return
            if user_id not in ADMIN_IDS: bot.reply_to(message, "⚠️ 관리자만 투표 이벤트를 생성할 수 있어요!"); return
            room_id = str(uuid.uuid4())[:8]
            db = get_db(); c = db.cursor()
            try:
                c.execute("INSERT INTO vote_rooms (room_id, group_id, admin_id) VALUES (%s,%s,%s)", (room_id, group_id, user_id))
                db.commit()
            finally: c.close(); db.close()
            param = f"{user_id}|{group_id}|{room_id}"   # ★ | 구분자
            vote_url = f"{WEBAPP_BASE_URL}/vote?start={param}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚙️ 이벤트 설정하기", url=vote_url))
            bot.reply_to(message,
                "🎰 <b>도파민 투표 이벤트</b>\n──────────────────\n"
                "아래 버튼을 눌러 이벤트 내용, 타임어택 시간,\n추첨 스타일을 설정하고 스타트를 눌러주세요!\n\n"
                "⚠️ 관리자만 설정 화면이 보입니다.",
                reply_markup=markup, parse_mode='HTML')

        elif text.strip().startswith('/내전취소'):
            if message.chat.type == 'private': return
            if user_id not in ADMIN_IDS: bot.reply_to(message, "⚠️ 관리자만 내전을 취소할 수 있어요!"); return
            parts = text.strip().split(); game_arg = parts[1] if len(parts) > 1 else ''
            game_map = {'롤':'lol','서든':'sa','lol':'lol','sa':'sa','sa5':'sa5','sa6':'sa6'}
            game_type = game_map.get(game_arg)
            if not game_type: bot.reply_to(message, "⚔️ 사용법: /내전취소 롤  또는  /내전취소 서든"); return
            db = get_db(); c = db.cursor()
            try:
                if game_type == 'sa':
                    c.execute("UPDATE naejeon_rooms SET status='cancelled' WHERE group_id=%s AND game_type IN ('sa5','sa6') AND status='open'", (group_id,))
                else:
                    c.execute("UPDATE naejeon_rooms SET status='cancelled' WHERE group_id=%s AND game_type=%s AND status='open'", (group_id, game_type))
                affected = c.rowcount; db.commit()
            finally: c.close(); db.close()
            game_names = {'롤':'리그오브레전드','서든':'서든어택'}
            if affected > 0: bot.reply_to(message, f"✅ {game_names.get(game_arg, game_arg)} 내전이 취소됐어요!")
            else: bot.reply_to(message, "⚠️ 진행 중인 내전이 없어요!")

        elif text.strip().startswith('/내전'):
            if message.chat.type == 'private': return
            if user_id not in ADMIN_IDS: bot.reply_to(message, "⚠️ 관리자만 내전을 열 수 있어요!"); return
            parts = text.strip().split(); game_arg = parts[1] if len(parts) > 1 else ''
            if game_arg not in ['롤', '서든']:
                bot.reply_to(message, "⚔️ 내전 사용법\n\n예시: /내전 롤\n예시: /내전 서든\n예시: /내전취소 롤\n예시: /내전수정 롤"); return
            extra_text = ' '.join(parts[2:]) if len(parts) > 2 else ''
            if game_arg == '서든':
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("⚔️ 서든 5v5", callback_data=f"nj_open:sa5:{extra_text}"),
                    types.InlineKeyboardButton("⚔️ 서든 6v6", callback_data=f"nj_open:sa6:{extra_text}"),
                )
                bot.reply_to(message, "⚔️ 서든어택 인원을 선택하세요!", reply_markup=markup); return
            game_type = 'lol'; display_name = '리그오브레전드 5v5'
            db = get_db(); c = db.cursor()
            try:
                c.execute("SELECT room_id FROM naejeon_rooms WHERE group_id=%s AND game_type=%s AND status='open'", (group_id, game_type))
                if c.fetchone(): bot.reply_to(message, "⚠️ 이미 진행 중인 내전이 있어요!"); return
                room_id = str(uuid.uuid4())[:8]
                c.execute("INSERT INTO naejeon_rooms (room_id, group_id, game_type, slots, extra_text) VALUES (%s,%s,%s,%s,%s)",
                          (room_id, group_id, game_type, '{}', extra_text))
                db.commit()
            finally: c.close(); db.close()
            param = f"{user_id}_{group_id}_{game_type}_{room_id}"
            nj_url = f"{WEBAPP_BASE_URL}/naejeon?start={param}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚔️ 내전 참여하기", url=nj_url))
            send_naejeon_gif(group_id)
            msg = f"⚔️ {display_name} 내전 모집!"
            if extra_text: msg += f"\n{extra_text}"
            msg += "\n\n아래 버튼을 눌러 참여하세요!\n⚠️ 처음 참여하시는 분은 @dopamin_ranking_bot 을 눌러 START 를 먼저 눌러주세요!"
            bot.send_message(group_id, msg, reply_markup=markup)

        elif message.chat.type in ['group', 'supergroup']:
            save_message(user_id, username, first_name, group_id)

    except Exception as e:
        import traceback; print(f"handle_all error: {e}\n{traceback.format_exc()}")


# ─────────────────────────────────────────────────────────
# Flask 라우트
# ─────────────────────────────────────────────────────────
@app.route('/kbo')
def serve_kbo(): return send_from_directory('.', 'kbo.html')

@app.route('/kbo/submit', methods=['POST'])
def kbo_submit():
    db = get_db(); c = db.cursor()
    try:
        data          = request.get_json()
        user_id       = int(data.get('userId'))
        group_id      = int(data.get('groupId'))
        teams         = data.get('teams', [])
        is_admin_req  = data.get('isAdmin', False)
        admin_user_id = data.get('adminUserId')

        if len(teams) != 5: return {'ok': False, 'error': '5개 팀을 선택해주세요.'}, 400

        # ★ 관리자 검증: isAdmin=True면 adminUserId가 실제 관리자인지 확인
        if is_admin_req:
            if not admin_user_id or int(admin_user_id) not in ADMIN_IDS:
                return {'ok': False, 'error': '관리자 권한이 없어요.'}, 403
        else:
            # 일반 유저: 참여 가능 시간 체크
            now_kst = datetime.now(KST)
            if not is_vote_time(now_kst):
                return {'ok': False, 'error': '참여 가능 시간이 아니에요.'}, 403

        today = datetime.now(KST).date()
        c.execute("SELECT first_name, username FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
        row = c.fetchone()

        # ★ userName 우선 (직접 입력), 없으면 points 테이블
        user_name_from_client = (data.get('userName') or '').strip()
        if user_name_from_client:
            first_name = clean_name(user_name_from_client)
            username   = row[1] if row else ''
        else:
            first_name = clean_name(row[0]) if row and row[0] else ''
            username   = row[1] if row else ''
            if not first_name: first_name = f"@{username}" if username else f"id:{user_id}"

        teams_str = ','.join(teams)
        c.execute("SELECT id FROM kbo_votes WHERE user_id=%s AND group_id=%s AND vote_date=%s", (user_id, group_id, today))
        existing = c.fetchone()
        if existing:
            c.execute("UPDATE kbo_votes SET teams=%s, first_name=%s, username=%s WHERE user_id=%s AND group_id=%s AND vote_date=%s",
                      (teams_str, first_name, username, user_id, group_id, today))
            action_label = "수정 완료"
            action       = "수정"
        else:
            c.execute("INSERT INTO kbo_votes (user_id, group_id, first_name, username, teams, vote_date) VALUES (%s,%s,%s,%s,%s,%s)",
                      (user_id, group_id, first_name, username, teams_str, today))
            action_label = "예측 완료"
            action       = "완료"
        c.execute("SELECT COUNT(*) FROM kbo_votes WHERE group_id=%s AND vote_date=%s", (group_id, today))
        total = c.fetchone()[0]; db.commit()
        team_display = '\n'.join([f"   {i+1}. {t}" for i, t in enumerate(teams)])
        admin_tag = " (관리자 수정)" if is_admin_req else ""
        bot.send_message(group_id, f"⚾ KBO 승 {action_label}{admin_tag}\n   👤 {first_name}님\n\n   선택한 팀 (5개):\n{team_display}\n\n   👥 오늘 참여자: {total}명")
        return {'ok': True, 'action': action}, 200
    except Exception as e:
        import traceback; print(f"kbo_submit error: {e}\n{traceback.format_exc()}")
        return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/kbo/list')
def kbo_list():
    db = get_db(); c = db.cursor()
    try:
        group_id = int(request.args.get('groupId', 0)); today = datetime.now(KST).date()
        c.execute("SELECT user_id, first_name, username, teams FROM kbo_votes WHERE group_id=%s AND vote_date=%s ORDER BY created_at", (group_id, today))
        rows = c.fetchall()
        result = []
        for row in rows:
            uid = row[0]; first = clean_name(row[1] or ''); uname = row[2] or ''
            name = first if first else (('@' + uname) if uname else ('id:' + str(uid)))
            result.append({'userId': uid, 'name': name, 'teams': row[3].split(',')})  # ★ userId 추가
        return result, 200
    except: return [], 500
    finally: c.close(); db.close()

@app.route('/kbo/hot')
def kbo_hot():
    db = get_db(); c = db.cursor()
    try:
        group_id = int(request.args.get('groupId', 0)); today = datetime.now(KST).date()
        c.execute("SELECT teams FROM kbo_votes WHERE group_id=%s AND vote_date=%s", (group_id, today))
        rows = c.fetchall()
        from collections import Counter; cnt = Counter()
        for row in rows:
            for team in row[0].split(','): cnt[team] += 1
        return [{'team': t, 'count': v} for t, v in cnt.most_common(3)], 200
    except: return [], 500
    finally: c.close(); db.close()

@app.route('/kbo/my')
def kbo_my():
    """오늘 내 예측 조회 + 참여 가능 시간 여부 반환"""
    db = get_db(); c = db.cursor()
    try:
        user_id  = int(request.args.get('userId', 0))
        group_id = int(request.args.get('groupId', 0))
        now_kst  = datetime.now(KST)
        today    = now_kst.date()
        vote_ok  = is_vote_time(now_kst)

        c.execute("SELECT first_name, username, teams FROM kbo_votes WHERE user_id=%s AND group_id=%s AND vote_date=%s",
                  (user_id, group_id, today))
        row = c.fetchone()
        if row:
            name  = clean_name(row[0]) if row[0] else (f"@{row[1]}" if row[1] else f"id:{user_id}")
            teams = row[2].split(',')
            return {'voted': True, 'name': name, 'teams': teams, 'isVoteTime': vote_ok}, 200
        else:
            return {'voted': False, 'isVoteTime': vote_ok}, 200
    except Exception as e:
        return {'voted': False, 'isVoteTime': False, 'error': str(e)}, 500
    finally:
        c.close(); db.close()

@app.route('/naejeon')
def serve_naejeon(): return send_from_directory('.', 'naejeon.html')

@app.route('/naejeon/check_admin')
def naejeon_check_admin():
    try:
        user_id = int(request.args.get('userId', 0))
        return {'isAdmin': user_id in ADMIN_IDS}, 200
    except: return {'isAdmin': False}, 200

@app.route('/naejeon/room')
def naejeon_room():
    db = get_db(); c = db.cursor()
    try:
        room_id = request.args.get('roomId')
        c.execute("SELECT game_type, slots, status, extra_text, pos_a, pos_b, started, fund_type, fund_amount FROM naejeon_rooms WHERE room_id=%s", (room_id,))
        row = c.fetchone()
        if not row: return {'error': '내전 방을 찾을 수 없어요.'}, 404
        c.execute("SELECT end_time, winner_count, reward_text, is_active FROM naejeon_events WHERE room_id=%s", (room_id,))
        ev = c.fetchone()
        event_data = None
        if ev and ev[3]:
            event_data = {'endTime': to_utc_iso(ev[0]), 'winnerCount': ev[1], 'rewardText': ev[2]}
        return {'gameType': row[0], 'slots': row[1] or {}, 'status': row[2], 'extraText': row[3] or '',
                'posA': row[4] or [], 'posB': row[5] or [], 'started': bool(row[6]),
                'fundType': row[7] or '', 'fundAmount': row[8] or '', 'event': event_data}, 200
    except Exception as e: return {'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/naejeon/setup', methods=['POST'])
def naejeon_setup():
    db = get_db(); c = db.cursor()
    try:
        data = request.get_json(); room_id = data.get('roomId')
        user_id = int(data.get('userId')); group_id = int(data.get('groupId'))
        game_type = data.get('gameType'); extra_text = data.get('extraText', '')
        pos_a = data.get('posA', []); pos_b = data.get('posB', [])
        fund_type = data.get('fundType', ''); fund_amount = data.get('fundAmount', '')
        if user_id not in ADMIN_IDS: return {'ok': False, 'error': '관리자만 사용할 수 있어요.'}, 403
        c.execute("UPDATE naejeon_rooms SET extra_text=%s, pos_a=%s, pos_b=%s, started=TRUE, fund_type=%s, fund_amount=%s WHERE room_id=%s",
            (extra_text, json.dumps(pos_a), json.dumps(pos_b), fund_type, fund_amount, room_id))
        db.commit()
        game_names = {'lol':'리그오브레전드 5v5','sa5':'서든어택 5v5','sa6':'서든어택 6v6'}
        gname = game_names.get(game_type, '내전')
        param = f"{user_id}_{group_id}_{game_type}_{room_id}"
        nj_url = f"{WEBAPP_BASE_URL}/naejeon?start={param}"
        display_amount = f"{int(fund_amount):,}원" if fund_amount.isdigit() else fund_amount
        send_naejeon_gif(group_id)
        msg = f"⚙️ {gname} 내전 설정 변경 및 공지!"
        if extra_text: msg += f"\n📢 공지: {extra_text}"
        if fund_type and fund_amount: msg += f"\n💰 {fund_type} 조건: {display_amount}"
        msg += f"\n\n👉 <a href='{nj_url}'>[여기]를 눌러 내전 현황 보기</a>"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚔️ 내전 바로가기", url=nj_url))
        bot.send_message(group_id, msg, reply_markup=markup, parse_mode='HTML')
        c.execute("SELECT game_type, slots, status, extra_text, pos_a, pos_b, started, fund_type, fund_amount FROM naejeon_rooms WHERE room_id=%s", (room_id,))
        row2 = c.fetchone()
        return {'ok': True, 'room': {'gameType': row2[0], 'slots': row2[1] or {}, 'status': row2[2],
            'extraText': row2[3] or '', 'posA': row2[4] or [], 'posB': row2[5] or [],
            'started': bool(row2[6]), 'fundType': row2[7] or '', 'fundAmount': row2[8] or ''}}, 200
    except Exception as e: return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/naejeon/cancel', methods=['POST'])
def naejeon_cancel():
    db = get_db(); c = db.cursor()
    try:
        data = request.get_json(); room_id = data.get('roomId')
        user_id = int(data.get('userId', 0)); group_id = int(data.get('groupId', 0))
        if user_id not in ADMIN_IDS: return {'ok': False, 'error': '관리자만 사용할 수 있어요.'}, 403
        c.execute("UPDATE naejeon_rooms SET status='cancelled' WHERE room_id=%s AND group_id=%s", (room_id, group_id))
        affected = c.rowcount; db.commit()
        if affected > 0:
            try: bot.send_message(group_id, "⚔️ 내전이 관리자에 의해 취소됐어요.")
            except: pass
            return {'ok': True}, 200
        return {'ok': False, 'error': '내전을 찾을 수 없어요.'}, 404
    except Exception as e: return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/naejeon/admin_add', methods=['POST'])
def naejeon_admin_add():
    db = get_db(); c = db.cursor()
    try:
        data = request.get_json(); room_id = data.get('roomId')
        user_id = int(data.get('userId')); group_id = int(data.get('groupId'))
        slot_key = data.get('slotKey'); name = data.get('name', '').strip()
        if user_id not in ADMIN_IDS: return {'ok': False, 'error': '관리자만 사용할 수 있어요.'}, 403
        if not name: return {'ok': False, 'error': '이름을 입력해주세요.'}, 400
        c.execute("SELECT game_type, slots, status FROM naejeon_rooms WHERE room_id=%s FOR UPDATE", (room_id,))
        row = c.fetchone()
        if not row: return {'ok': False, 'error': '방을 찾을 수 없어요.'}, 404
        slots = row[1] if row[1] else {}
        slots[slot_key] = {'userId': f'admin_{uuid.uuid4().hex[:6]}', 'name': name, 'team': slot_key.split('_')[0]}
        total = {'lol':10,'sa5':10,'sa6':12}.get(row[0], 10)
        filled = len([v for v in slots.values() if v and v.get('userId')])
        status = 'closed' if filled >= total else 'open'
        c.execute("UPDATE naejeon_rooms SET slots=%s, status=%s WHERE room_id=%s", (json.dumps(slots), status, room_id))
        db.commit()
        if status == 'closed': _send_naejeon_result(group_id, row[0], slots)
        c.execute("SELECT game_type, slots, status, extra_text, pos_a, pos_b, started, fund_type, fund_amount FROM naejeon_rooms WHERE room_id=%s", (room_id,))
        row2 = c.fetchone()
        return {'ok': True, 'room': {'gameType': row2[0], 'slots': row2[1] or {}, 'status': row2[2],
            'extraText': row2[3] or '', 'posA': row2[4] or [], 'posB': row2[5] or [],
            'started': bool(row2[6]), 'fundType': row2[7] or '', 'fundAmount': row2[8] or ''}}, 200
    except Exception as e: return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/naejeon/admin_remove', methods=['POST'])
def naejeon_admin_remove():
    db = get_db(); c = db.cursor()
    try:
        data = request.get_json(); room_id = data.get('roomId')
        user_id = int(data.get('userId')); group_id = int(data.get('groupId'))
        slot_key = data.get('slotKey')
        if user_id not in ADMIN_IDS: return {'ok': False, 'error': '관리자만 사용할 수 있어요.'}, 403
        c.execute("SELECT game_type, slots, status FROM naejeon_rooms WHERE room_id=%s FOR UPDATE", (room_id,))
        row = c.fetchone()
        if not row: return {'ok': False, 'error': '방을 찾을 수 없어요.'}, 404
        slots = row[1] if row[1] else {}
        if slot_key in slots: slots[slot_key] = None
        c.execute("UPDATE naejeon_rooms SET slots=%s, status='open' WHERE room_id=%s", (json.dumps(slots), room_id))
        db.commit()
        c.execute("SELECT game_type, slots, status, extra_text, pos_a, pos_b, started, fund_type, fund_amount FROM naejeon_rooms WHERE room_id=%s", (room_id,))
        row2 = c.fetchone()
        return {'ok': True, 'room': {'gameType': row2[0], 'slots': row2[1] or {}, 'status': row2[2],
            'extraText': row2[3] or '', 'posA': row2[4] or [], 'posB': row2[5] or [],
            'started': bool(row2[6]), 'fundType': row2[7] or '', 'fundAmount': row2[8] or ''}}, 200
    except Exception as e: return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/naejeon/join', methods=['POST'])
def naejeon_join():
    db = get_db(); c = db.cursor()
    try:
        data = request.get_json(); room_id = data.get('roomId')
        user_id = int(data.get('userId')); group_id = int(data.get('groupId'))
        team = data.get('team'); pos_id = data.get('posId'); pos_label = data.get('posLabel')
        c.execute("SELECT game_type, slots, status FROM naejeon_rooms WHERE room_id=%s FOR UPDATE", (room_id,))
        row = c.fetchone()
        if not row: return {'ok': False, 'error': '방을 찾을 수 없어요.'}, 404
        if row[2] != 'open': return {'ok': False, 'error': '이미 마감된 내전이에요.'}, 400
        slots = row[1] if row[1] else {}; game_type = row[0]; slot_key = f"{team}_{pos_id}"
        for k, v in slots.items():
            if v and str(v.get('userId')) == str(user_id): return {'ok': False, 'error': '이미 참여하셨어요!'}, 400
        if slots.get(slot_key): return {'ok': False, 'error': '이미 선택된 포지션이에요!'}, 400
        c.execute("SELECT first_name, username FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
        ur = c.fetchone()
        name = clean_name(ur[0]) if ur and ur[0] else (f"@{ur[1]}" if ur and ur[1] else f"id:{user_id}")
        slots[slot_key] = {'userId': user_id, 'name': name, 'posLabel': pos_label, 'team': team}
        total = {'lol':10,'sa5':10,'sa6':12}.get(game_type, 10)
        filled = len([v for v in slots.values() if v])
        status = 'closed' if filled >= total else 'open'
        c.execute("UPDATE naejeon_rooms SET slots=%s, status=%s WHERE room_id=%s", (json.dumps(slots), status, room_id))
        db.commit()
        if status == 'closed': _send_naejeon_result(group_id, game_type, slots)
        c.execute("SELECT game_type, slots, status, extra_text, pos_a, pos_b, started, fund_type, fund_amount FROM naejeon_rooms WHERE room_id=%s", (room_id,))
        row2 = c.fetchone()
        return {'ok': True, 'room': {'gameType': row2[0], 'slots': row2[1] or {}, 'status': row2[2],
            'extraText': row2[3] or '', 'posA': row2[4] or [], 'posB': row2[5] or [],
            'started': bool(row2[6]), 'fundType': row2[7] or '', 'fundAmount': row2[8] or ''}}, 200
    except Exception as e:
        import traceback; print(f"naejeon_join error: {e}\n{traceback.format_exc()}")
        return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/naejeon/leave', methods=['POST'])
def naejeon_leave():
    db = get_db(); c = db.cursor()
    try:
        data = request.get_json(); room_id = data.get('roomId'); user_id = int(data.get('userId'))
        c.execute("SELECT game_type, slots, status FROM naejeon_rooms WHERE room_id=%s FOR UPDATE", (room_id,))
        row = c.fetchone()
        if not row: return {'ok': False, 'error': '방을 찾을 수 없어요.'}, 404
        slots = row[1] if row[1] else {}; updated = False
        for k, v in list(slots.items()):
            if v and str(v.get('userId')) == str(user_id):
                slots[k] = None; updated = True; break
        if not updated: return {'ok': False, 'error': '참여 기록을 찾을 수 없어요.'}, 400
        c.execute("UPDATE naejeon_rooms SET slots=%s, status='open' WHERE room_id=%s", (json.dumps(slots), room_id))
        db.commit()
        c.execute("SELECT game_type, slots, status, extra_text, pos_a, pos_b, started, fund_type, fund_amount FROM naejeon_rooms WHERE room_id=%s", (room_id,))
        row2 = c.fetchone()
        return {'ok': True, 'room': {'gameType': row2[0], 'slots': row2[1] or {}, 'status': row2[2],
            'extraText': row2[3] or '', 'posA': row2[4] or [], 'posB': row2[5] or [],
            'started': bool(row2[6]), 'fundType': row2[7] or '', 'fundAmount': row2[8] or ''}}, 200
    except Exception as e: return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

def _send_naejeon_result(group_id, game_type, slots):
    game_names = {'lol':'리그오브레전드 5v5','sa5':'서든어택 5v5','sa6':'서든어택 6v6'}
    pos_order = {'lol':['top','jg','mid','adc','sup'],'sa5':['sna','rfl1','rfl2','rfl3','rfl4'],'sa6':['sna1','sna2','rfl1','rfl2','rfl3','rfl4']}.get(game_type, [])
    pos_labels = {'top':'탑','jg':'정글','mid':'미드','adc':'원딜','sup':'서폿','sna':'스나','sna1':'스나1','sna2':'스나2','rfl1':'라플1','rfl2':'라플2','rfl3':'라플3','rfl4':'라플4'}
    result = f"⚔️ {game_names.get(game_type,'')} 내전 모집 완료!\n\n"
    for team_id, label in [('A','🟣 1팀'),('B','🟢 2팀')]:
        result += f"{label}\n"
        for pos in pos_order:
            slot = slots.get(f"{team_id}_{pos}")
            result += f"   [{pos_labels.get(pos,pos)}] {slot['name'] if (slot and slot.get('userId')) else '비어있음'}\n"
        result += "\n"
    try: bot.send_message(group_id, result)
    except: pass

@app.route('/naejeon/start_event', methods=['POST'])
def start_event():
    db = get_db(); c = db.cursor()
    try:
        data = request.get_json(); room_id = data.get('roomId')
        user_id = int(data.get('userId')); group_id = int(data.get('groupId'))
        mins = int(data.get('mins', 5)); winners = int(data.get('winners', 1)); reward = data.get('reward', '').strip()
        if user_id not in ADMIN_IDS: return {'ok': False, 'error': '관리자만 사용할 수 있어요.'}, 403
        if not reward: return {'ok': False, 'error': '보상 내용을 입력해주세요.'}, 400
        end_time = datetime.now(UTC) + timedelta(minutes=mins)
        c.execute("""INSERT INTO naejeon_events (room_id, end_time, winner_count, reward_text, is_active)
            VALUES (%s,%s,%s,%s,TRUE) ON CONFLICT (room_id) DO UPDATE SET
            end_time=%s, winner_count=%s, reward_text=%s, is_active=TRUE""",
            (room_id, end_time, winners, reward, end_time, winners, reward))
        db.commit()
        formatted_reward = f"{int(reward):,}원" if reward.isdigit() else reward
        bot.send_message(group_id,
            f"🚨 <b>도파민 타임어택 투표 런칭!</b> 🚨\n──────────────────\n"
            f"⏱ <b>제한시간:</b> {mins}분 배틀\n🎁 <b>이벤트 보상:</b> {formatted_reward}\n👥 <b>추첨 인원:</b> {winners}명\n──────────────────\n"
            f"⚠️ 타이머 종료 전까지 자리를 선점하세요!", parse_mode='HTML')
        return {'ok': True}, 200
    except Exception as e: return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/naejeon/finish_event', methods=['POST'])
def finish_event():
    db = get_db(); c = db.cursor()
    try:
        data = request.get_json(); room_id = data.get('roomId')
        c.execute("SELECT is_active, winner_count, reward_text FROM naejeon_events WHERE room_id=%s", (room_id,))
        ev = c.fetchone()
        if not ev or not ev[0]: return {'ok': False, 'error': '이미 종료되었거나 없는 이벤트입니다.'}, 400
        winner_count, reward_text = ev[1], ev[2]
        c.execute("SELECT group_id, slots FROM naejeon_rooms WHERE room_id=%s", (room_id,))
        room = c.fetchone()
        if not room: return {'ok': False, 'error': '방을 찾을 수 없습니다.'}, 404
        group_id, slots = room[0], room[1]
        candidates = [v.get('name','익명') for k,v in slots.items() if v and v.get('userId') and not str(v.get('userId')).startswith('admin_')]
        winners = random.sample(candidates, min(len(candidates), winner_count)) if candidates else []
        c.execute("UPDATE naejeon_events SET is_active=FALSE WHERE room_id=%s", (room_id,)); db.commit()
        formatted_reward = f"{int(reward_text):,}원" if reward_text.isdigit() else reward_text
        winner_lines = "\n".join([f"🥇 <b>{name}</b>" for name in winners]) if winners else "❌ 참여자 부족으로 인한 추첨 취소"
        bot.send_message(group_id,
            f"🏁 <b>타임어택 이벤트 종료!</b> 🏁\n──────────────────\n🎁 <b>지급 보상:</b> {formatted_reward}\n\n"
            f"🎉 <b>당첨자:</b>\n{winner_lines}\n──────────────────\n축하드립니다! 당첨자는 방장에게 보상을 수령하세요! 🥳", parse_mode='HTML')
        return {'ok': True, 'winners': winners}, 200
    except Exception as e: return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

# ─────────────────────────────────────────────────────────
# 투표 이벤트 라우트
# ─────────────────────────────────────────────────────────
@app.route('/vote')
def serve_vote(): return send_from_directory('.', 'vote.html')

@app.route('/vote/room')
def vote_room():
    db = get_db(); c = db.cursor()
    try:
        room_id = request.args.get('roomId')
        c.execute("SELECT room_id, group_id, content, mins, winners, anim_style, started, ended, end_time FROM vote_rooms WHERE room_id=%s", (room_id,))
        row = c.fetchone()
        if not row: return {'error': '이벤트를 찾을 수 없어요.'}, 404
        c.execute("SELECT user_id, name FROM vote_participants WHERE room_id=%s ORDER BY joined_at", (room_id,))
        parts = [{'userId': r[0], 'name': r[1]} for r in c.fetchall()]
        return {
            'roomId': row[0], 'groupId': row[1], 'content': row[2] or '',
            'mins': row[3], 'winners': row[4], 'animStyle': row[5] or 'slot',
            'started': bool(row[6]), 'ended': bool(row[7]),
            'endTime': to_utc_iso(row[8]),   # ★ UTC ISO Z 포맷
            'participants': parts
        }, 200
    except Exception as e: return {'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/vote/start', methods=['POST'])
def vote_start():
    db = get_db(); c = db.cursor()
    try:
        data = request.get_json()
        room_id    = data.get('roomId')
        user_id    = int(data.get('userId'))
        group_id   = int(data.get('groupId'))
        content    = data.get('content', '').strip()
        anim_style = data.get('animStyle', 'slot')
        winners    = int(data.get('winners', 1))
        mins       = safe_mins(data.get('mins'))   # ★ 안전 변환

        if user_id not in ADMIN_IDS: return {'ok': False, 'error': '관리자만 시작할 수 있어요.'}, 403
        if not content: return {'ok': False, 'error': '이벤트 내용을 입력해주세요.'}, 400

        end_time = datetime.now(UTC) + timedelta(minutes=mins) if mins else None  # ★ UTC 저장

        c.execute("""UPDATE vote_rooms
            SET content=%s, mins=%s, winners=%s, anim_style=%s, started=TRUE, ended=FALSE, end_time=%s
            WHERE room_id=%s""",
            (content, mins, winners, anim_style, end_time, room_id))

        if c.rowcount == 0:
            return {'ok': False, 'error': f'room_id={room_id} 를 찾을 수 없어요. /투표 를 다시 입력해주세요.'}, 404

        db.commit()

        time_str   = f"{mins}분 타임어택" if mins else "제한 시간 없음"
        anim_names = {'slot':'🎰 슬롯머신','roulette':'🎡 룰렛','highlight':'⚡ 랜덤 하이라이트'}
        anim_label = anim_names.get(anim_style, anim_style)
        param    = f"{user_id}|{group_id}|{room_id}"   # ★ | 구분자
        vote_url = f"{WEBAPP_BASE_URL}/vote?start={param}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🙋 이벤트 참여하기", url=vote_url))
        bot.send_message(group_id,
            f"🎰 <b>도파민 투표 이벤트 시작!</b>\n──────────────────\n"
            f"📢 <b>이벤트:</b> {content}\n⏱ <b>시간:</b> {time_str}\n"
            f"👥 <b>당첨자:</b> {winners}명\n🎬 <b>추첨 방식:</b> {anim_label}\n──────────────────\n"
            f"아래 버튼을 눌러 참여하세요!",
            reply_markup=markup, parse_mode='HTML')
        return {'ok': True}, 200
    except Exception as e:
        import traceback; print(f"vote_start error: {e}\n{traceback.format_exc()}")
        return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/vote/join', methods=['POST'])
def vote_join():
    db = get_db(); c = db.cursor()
    try:
        data = request.get_json(); room_id = data.get('roomId')
        user_id = int(data.get('userId')); group_id = int(data.get('groupId'))
        user_name_from_client = (data.get('userName') or '').strip()
        c.execute("SELECT started, ended FROM vote_rooms WHERE room_id=%s", (room_id,))
        row = c.fetchone()
        if not row: return {'ok': False, 'error': '이벤트를 찾을 수 없어요.'}, 404
        if not row[0]: return {'ok': False, 'error': '아직 시작되지 않은 이벤트예요.'}, 400
        if row[1]: return {'ok': False, 'error': '이미 종료된 이벤트예요.'}, 400
        # ★ 이름 우선순위: 직접 입력 → points 테이블 → id:숫자
        name = clean_name(user_name_from_client) if user_name_from_client else None
        if not name:
            c.execute("SELECT first_name, username FROM points WHERE user_id=%s ORDER BY id DESC LIMIT 1", (user_id,))
            ur = c.fetchone()
            if ur and ur[0]: name = clean_name(ur[0])
            elif ur and ur[1]: name = f"@{ur[1]}"
        if not name: name = f"id:{user_id}"
        c.execute("INSERT INTO vote_participants (room_id, user_id, name) VALUES (%s,%s,%s) ON CONFLICT (room_id, user_id) DO NOTHING", (room_id, user_id, name))
        db.commit()
        c.execute("SELECT user_id, name FROM vote_participants WHERE room_id=%s ORDER BY joined_at", (room_id,))
        parts = [{'userId': r[0], 'name': r[1]} for r in c.fetchall()]
        return {'ok': True, 'participants': parts}, 200
    except Exception as e: return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/vote/leave', methods=['POST'])
def vote_leave():
    db = get_db(); c = db.cursor()
    try:
        data = request.get_json(); room_id = data.get('roomId'); user_id = int(data.get('userId'))
        c.execute("SELECT ended FROM vote_rooms WHERE room_id=%s", (room_id,))
        row = c.fetchone()
        if not row or row[0]: return {'ok': False, 'error': '취소할 수 없는 이벤트예요.'}, 400
        c.execute("DELETE FROM vote_participants WHERE room_id=%s AND user_id=%s", (room_id, user_id)); db.commit()
        c.execute("SELECT user_id, name FROM vote_participants WHERE room_id=%s ORDER BY joined_at", (room_id,))
        parts = [{'userId': r[0], 'name': r[1]} for r in c.fetchall()]
        return {'ok': True, 'participants': parts}, 200
    except Exception as e: return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/vote/draw', methods=['POST'])
def vote_draw():
    db = get_db(); c = db.cursor()
    try:
        data = request.get_json(); room_id = data.get('roomId')
        c.execute("SELECT group_id, content, winners, anim_style, ended FROM vote_rooms WHERE room_id=%s", (room_id,))
        row = c.fetchone()
        if not row: return {'ok': False, 'error': '이벤트를 찾을 수 없어요.'}, 404
        if row[4]: return {'ok': False, 'error': '이미 추첨이 완료됐어요.'}, 400
        group_id, content, winner_count, anim_style = row[0], row[1], row[2], row[3]
        c.execute("SELECT user_id, name FROM vote_participants WHERE room_id=%s ORDER BY joined_at", (room_id,))
        parts = [{'userId': r[0], 'name': r[1]} for r in c.fetchall()]
        winners = []
        if parts:
            shuffled = parts.copy(); random.shuffle(shuffled)
            winners = [p['name'] for p in shuffled[:min(winner_count, len(shuffled))]]
        c.execute("UPDATE vote_rooms SET ended=TRUE WHERE room_id=%s", (room_id,)); db.commit()
        anim_names = {'slot':'🎰 슬롯머신','roulette':'🎡 룰렛','highlight':'⚡ 랜덤 하이라이트'}
        winner_text = "\n".join([f"🏆 <b>{n}</b>" for n in winners]) if winners else "❌ 참여자 없음"
        bot.send_message(group_id,
            f"🎉 <b>투표 이벤트 추첨 결과!</b>\n──────────────────\n"
            f"📢 <b>{content}</b>\n🎬 추첨 방식: {anim_names.get(anim_style,'')}\n\n"
            f"{winner_text}\n──────────────────\n축하드립니다! 당첨자는 방장에게 보상을 수령하세요 🥳", parse_mode='HTML')
        return {'ok': True, 'winners': winners, 'animStyle': anim_style, 'content': content, 'participants': parts}, 200
    except Exception as e:
        import traceback; print(f"vote_draw error: {e}\n{traceback.format_exc()}")
        return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()



# ═══════════════════════════════════════════════════════
# 카지노 기본 설정
# ═══════════════════════════════════════════════════════
DEFAULT_CASINO_SETTINGS = {
    "race": {
        "rabbit_win_rate": 60, "min_bet": 10, "max_bet": 10000,
        "house_edge": 5, "enabled": True, "force_result": None,
        "rabbit_odds": 1.8, "turtle_odds": 2.5
    },
    "baccarat": {
        "player_win_rate": 45, "banker_win_rate": 46,
        "min_bet": 10, "max_bet": 10000,
        "house_edge": 5, "enabled": True, "force_result": None
    },
    "horse": {
        "horses": [
            {"id":1,"name":"번개","emoji":"⚡","win_rate":30,"base_odds":2.5},
            {"id":2,"name":"폭풍","emoji":"🌪️","win_rate":20,"base_odds":3.5},
            {"id":3,"name":"황금","emoji":"⭐","win_rate":15,"base_odds":5.0},
            {"id":4,"name":"다이아","emoji":"💎","win_rate":10,"base_odds":7.0},
            {"id":5,"name":"불꽃","emoji":"🔥","win_rate":25,"base_odds":3.0},
        ],
        "min_bet": 10, "max_bet": 10000, "house_edge": 5,
        "enabled": True, "force_result": None
    },
    "bigwheel": {
        "segments": [
            {"label":"2배","multiplier":2,"color":"#2266cc","probability":30},
            {"label":"3배","multiplier":3,"color":"#22aa66","probability":20},
            {"label":"5배","multiplier":5,"color":"#cc8800","probability":15},
            {"label":"10배","multiplier":10,"color":"#aa2222","probability":10},
            {"label":"20배","multiplier":20,"color":"#882288","probability":5},
            {"label":"꽝","multiplier":0,"color":"#222233","probability":20},
        ],
        "min_bet": 10, "max_bet": 10000, "house_edge": 5, "enabled": True
    }
}

def get_casino_settings(group_id, game_id):
    db = get_db(); c = db.cursor()
    try:
        c.execute("SELECT settings FROM casino_settings WHERE group_id=%s AND game_id=%s", (group_id, game_id))
        row = c.fetchone()
        if row and row[0]:
            base = DEFAULT_CASINO_SETTINGS.get(game_id, {}).copy()
            base.update(row[0])
            return base
        return DEFAULT_CASINO_SETTINGS.get(game_id, {}).copy()
    finally: c.close(); db.close()

def save_casino_settings(group_id, game_id, settings):
    db = get_db(); c = db.cursor()
    try:
        c.execute("""INSERT INTO casino_settings (group_id, game_id, settings, updated_at)
            VALUES (%s,%s,%s,NOW()) ON CONFLICT (group_id, game_id)
            DO UPDATE SET settings=%s, updated_at=NOW()""",
            (group_id, game_id, json.dumps(settings), json.dumps(settings)))
        db.commit()
    finally: c.close(); db.close()

def calc_dynamic_odds(bets_by_option, total_pool, option, house_edge=5):
    """베팅 풀 기반 동적 배당률 계산"""
    option_pool = bets_by_option.get(option, 0)
    if option_pool == 0 or total_pool == 0:
        return 2.0
    raw_odds = (total_pool * (1 - house_edge/100)) / option_pool
    return max(1.1, round(raw_odds, 2))

def is_casino_blacklisted(group_id, user_id):
    db = get_db(); c = db.cursor()
    try:
        c.execute("SELECT 1 FROM casino_blacklist WHERE group_id=%s AND user_id=%s", (group_id, user_id))
        return c.fetchone() is not None
    finally: c.close(); db.close()

# ─────────────────────────────────────────────────────────
# 카지노 메인 & 공통
# ─────────────────────────────────────────────────────────
@app.route('/casino')
def serve_casino(): return send_from_directory('.', 'casino.html')

@app.route('/casino/admin')
def serve_casino_admin(): return send_from_directory('.', 'casino_admin.html')

@app.route('/casino/settings', methods=['GET'])
def casino_get_settings():
    try:
        group_id = int(request.args.get('groupId', 0))
        game_id  = request.args.get('gameId', '')
        return get_casino_settings(group_id, game_id), 200
    except Exception as e: return {'error': str(e)}, 500

@app.route('/casino/settings', methods=['POST'])
def casino_save_settings():
    try:
        data      = request.get_json()
        admin_id  = int(data.get('adminId', 0))
        group_id  = int(data.get('groupId', 0))
        game_id   = data.get('gameId', '')
        settings  = data.get('settings', {})
        if admin_id not in ADMIN_IDS:
            return {'ok': False, 'error': '관리자만 설정할 수 있어요.'}, 403
        save_casino_settings(group_id, game_id, settings)
        return {'ok': True}, 200
    except Exception as e: return {'ok': False, 'error': str(e)}, 500

@app.route('/casino/point_grant', methods=['POST'])
def casino_point_grant():
    """관리자 포인트 지급/차감"""
    db = get_db(); c = db.cursor()
    try:
        data      = request.get_json()
        admin_id  = int(data.get('adminId', 0))
        group_id  = int(data.get('groupId', 0))
        target_id = int(data.get('userId', 0))
        amount    = int(data.get('amount', 0))
        reason    = data.get('reason', '관리자 지급')
        if admin_id not in ADMIN_IDS:
            return {'ok': False, 'error': '관리자만 사용할 수 있어요.'}, 403
        if amount == 0:
            return {'ok': False, 'error': '금액을 입력해주세요.'}, 400
        c.execute("SELECT first_name, username, point FROM points WHERE user_id=%s AND group_id=%s", (target_id, group_id))
        row = c.fetchone()
        if not row: return {'ok': False, 'error': '유저를 찾을 수 없어요.'}, 404
        user_name = row[0] or row[1] or f"id:{target_id}"
        new_point = row[2] + amount
        if new_point < 0: return {'ok': False, 'error': f'포인트가 부족해요. 현재: {row[2]}P'}, 400
        c.execute("UPDATE points SET point=%s WHERE user_id=%s AND group_id=%s", (new_point, target_id, group_id))
        c.execute("INSERT INTO point_logs (group_id, user_id, user_name, amount, reason, admin_id) VALUES (%s,%s,%s,%s,%s,%s)",
                  (group_id, target_id, user_name, amount, reason, admin_id))
        db.commit()
        action = "지급" if amount > 0 else "차감"
        bot.send_message(group_id,
            f"💰 <b>관리자 포인트 {action}</b>\n"
            f"👤 {user_name}님\n"
            f"{'➕' if amount>0 else '➖'} {abs(amount):,}P\n"
            f"💼 잔여: {new_point:,}P\n"
            f"📝 사유: {reason}", parse_mode='HTML')
        return {'ok': True, 'newPoint': new_point, 'userName': user_name}, 200
    except Exception as e: return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/casino/point_grant_all', methods=['POST'])
def casino_point_grant_all():
    """전체 유저 포인트 일괄 지급"""
    db = get_db(); c = db.cursor()
    try:
        data     = request.get_json()
        admin_id = int(data.get('adminId', 0))
        group_id = int(data.get('groupId', 0))
        amount   = int(data.get('amount', 0))
        reason   = data.get('reason', '이벤트 지급')
        if admin_id not in ADMIN_IDS:
            return {'ok': False, 'error': '관리자만 사용할 수 있어요.'}, 403
        if amount <= 0:
            return {'ok': False, 'error': '지급 금액은 양수여야 해요.'}, 400
        c.execute("SELECT user_id, first_name, username FROM points WHERE group_id=%s", (group_id,))
        rows = c.fetchall()
        for row in rows:
            uid  = row[0]
            name = row[1] or row[2] or f"id:{uid}"
            c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s", (amount, uid, group_id))
            c.execute("INSERT INTO point_logs (group_id, user_id, user_name, amount, reason, admin_id) VALUES (%s,%s,%s,%s,%s,%s)",
                      (group_id, uid, name, amount, reason, admin_id))
        db.commit()
        bot.send_message(group_id,
            f"🎁 <b>전체 포인트 지급!</b>\n"
            f"👥 {len(rows)}명에게 {amount:,}P 지급\n"
            f"📝 사유: {reason}", parse_mode='HTML')
        return {'ok': True, 'count': len(rows)}, 200
    except Exception as e: return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/casino/blacklist', methods=['GET'])
def casino_get_blacklist():
    db = get_db(); c = db.cursor()
    try:
        group_id = int(request.args.get('groupId', 0))
        c.execute("""SELECT b.user_id, COALESCE(p.first_name, p.username, CAST(b.user_id AS VARCHAR)) as name,
                     b.reason, b.created_at
                     FROM casino_blacklist b
                     LEFT JOIN points p ON p.user_id=b.user_id AND p.group_id=b.group_id
                     WHERE b.group_id=%s""", (group_id,))
        rows = c.fetchall()
        return [{'userId':r[0],'name':r[1],'reason':r[2],'createdAt':r[3].isoformat() if r[3] else None} for r in rows], 200
    except Exception as e: return [], 500
    finally: c.close(); db.close()

@app.route('/casino/blacklist', methods=['POST'])
def casino_add_blacklist():
    db = get_db(); c = db.cursor()
    try:
        data      = request.get_json()
        admin_id  = int(data.get('adminId', 0))
        group_id  = int(data.get('groupId', 0))
        target_id = int(data.get('userId', 0))
        reason    = data.get('reason', '')
        action    = data.get('action', 'add')   # add or remove
        if admin_id not in ADMIN_IDS:
            return {'ok': False, 'error': '관리자만 사용할 수 있어요.'}, 403
        if action == 'remove':
            c.execute("DELETE FROM casino_blacklist WHERE group_id=%s AND user_id=%s", (group_id, target_id))
        else:
            c.execute("INSERT INTO casino_blacklist (group_id, user_id, reason) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                      (group_id, target_id, reason))
        db.commit()
        return {'ok': True}, 200
    except Exception as e: return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/casino/stats')
def casino_stats():
    """게임별 통계"""
    db = get_db(); c = db.cursor()
    try:
        group_id = int(request.args.get('groupId', 0))
        days     = int(request.args.get('days', 7))
        c.execute("""SELECT game_id, COUNT(*) as rounds,
                     SUM(CASE WHEN won THEN payout ELSE 0 END) as total_payout,
                     SUM(amount) as total_bet,
                     COUNT(DISTINCT user_id) as players
                     FROM casino_bets
                     WHERE group_id=%s AND created_at >= NOW() - INTERVAL '%s days'
                     GROUP BY game_id""", (group_id, days))
        rows = c.fetchall()
        result = []
        for r in rows:
            result.append({
                'gameId':      r[0],
                'rounds':      r[1],
                'totalPayout': r[2] or 0,
                'totalBet':    r[3] or 0,
                'profit':      (r[3] or 0) - (r[2] or 0),
                'players':     r[4]
            })
        return result, 200
    except Exception as e: return [], 500
    finally: c.close(); db.close()

@app.route('/casino/point_logs')
def casino_point_logs():
    db = get_db(); c = db.cursor()
    try:
        group_id = int(request.args.get('groupId', 0))
        limit    = int(request.args.get('limit', 50))
        c.execute("""SELECT user_name, amount, reason, created_at
                     FROM point_logs WHERE group_id=%s
                     ORDER BY created_at DESC LIMIT %s""", (group_id, limit))
        rows = c.fetchall()
        return [{'userName':r[0],'amount':r[1],'reason':r[2],
                 'createdAt':r[3].isoformat() if r[3] else None} for r in rows], 200
    except Exception as e: return [], 500
    finally: c.close(); db.close()

@app.route('/casino/users')
def casino_users():
    """유저 목록 + 포인트"""
    db = get_db(); c = db.cursor()
    try:
        group_id = int(request.args.get('groupId', 0))
        c.execute("""SELECT p.user_id,
                     COALESCE(p.first_name, p.username, CAST(p.user_id AS VARCHAR)) as name,
                     p.point,
                     CASE WHEN b.user_id IS NOT NULL THEN TRUE ELSE FALSE END as blacklisted
                     FROM points p
                     LEFT JOIN casino_blacklist b ON b.user_id=p.user_id AND b.group_id=p.group_id
                     WHERE p.group_id=%s ORDER BY p.point DESC""", (group_id,))
        rows = c.fetchall()
        return [{'userId':r[0],'name':r[1],'point':r[2],'blacklisted':r[3]} for r in rows], 200
    except Exception as e: return [], 500
    finally: c.close(); db.close()

# ─────────────────────────────────────────────────────────
# 경주 (토끼 vs 거북이)
# ─────────────────────────────────────────────────────────
@app.route('/casino/race')
def serve_race(): return send_from_directory('.', 'race.html')

@app.route('/casino/race/state')
def race_state():
    db = get_db(); c = db.cursor()
    try:
        group_id = int(request.args.get('groupId', 0))
        c.execute("""SELECT id, status, result, settings, created_at
                     FROM casino_games WHERE group_id=%s AND game_id='race'
                     ORDER BY id DESC LIMIT 1""", (group_id,))
        row = c.fetchone()
        if not row:
            return {'status': 'idle', 'roundId': None, 'bets': {}, 'myBet': None}, 200

        round_id = row[0]; status = row[1]; result = row[2]
        user_id  = int(request.args.get('userId', 0))

        # 베팅 현황
        c.execute("""SELECT bet_on, SUM(amount), COUNT(*)
                     FROM casino_bets WHERE round_id=%s GROUP BY bet_on""", (round_id,))
        bets_raw = c.fetchall()
        bets = {r[0]: {'total': r[1], 'count': r[2]} for r in bets_raw}
        total_pool = sum(b['total'] for b in bets.values())

        # 배당률 계산
        settings = get_casino_settings(group_id, 'race')
        house    = settings.get('house_edge', 5)
        odds = {}
        for opt in ['rabbit', 'turtle']:
            pool = bets.get(opt, {}).get('total', 0)
            if pool > 0 and total_pool > 0:
                odds[opt] = max(1.1, round((total_pool*(1-house/100))/pool, 2))
            else:
                odds[opt] = settings.get(f'{opt}_odds', 2.0)

        # 내 베팅
        my_bet = None
        if user_id:
            c.execute("SELECT bet_on, amount FROM casino_bets WHERE round_id=%s AND user_id=%s", (round_id, user_id))
            mb = c.fetchone()
            if mb: my_bet = {'betOn': mb[0], 'amount': mb[1]}

        return {
            'status':    status,
            'roundId':   round_id,
            'result':    result,
            'bets':      bets,
            'odds':      odds,
            'totalPool': total_pool,
            'myBet':     my_bet,
            'settings':  settings
        }, 200
    except Exception as e:
        import traceback; print(traceback.format_exc())
        return {'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/casino/race/open', methods=['POST'])
def race_open():
    """관리자가 베팅 오픈"""
    db = get_db(); c = db.cursor()
    try:
        data     = request.get_json()
        admin_id = int(data.get('adminId', 0))
        group_id = int(data.get('groupId', 0))
        if admin_id not in ADMIN_IDS:
            return {'ok': False, 'error': '관리자만 시작할 수 있어요.'}, 403
        # 기존 진행중인 게임 확인
        c.execute("SELECT id FROM casino_games WHERE group_id=%s AND game_id='race' AND status NOT IN ('closed','cancelled')", (group_id,))
        if c.fetchone():
            return {'ok': False, 'error': '이미 진행 중인 경주가 있어요.'}, 400
        settings = get_casino_settings(group_id, 'race')
        c.execute("INSERT INTO casino_games (game_id, group_id, status, settings) VALUES ('race',%s,'betting',%s) RETURNING id",
                  (group_id, json.dumps(settings)))
        round_id = c.fetchone()[0]; db.commit()
        casino_url = f"{WEBAPP_BASE_URL}/casino/race?groupId={group_id}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🐢 경주 베팅하기", url=casino_url))
        bot.send_message(group_id,
            f"🏁 <b>도파민 경주 시작!</b>\n"
            f"──────────────────\n"
            f"🐇 토끼 vs 🐢 거북이\n"
            f"💰 최소 베팅: {settings.get('min_bet',10):,}P\n"
            f"💰 최대 베팅: {settings.get('max_bet',10000):,}P\n"
            f"──────────────────\n"
            f"아래 버튼을 눌러 베팅하세요!", reply_markup=markup, parse_mode='HTML')
        return {'ok': True, 'roundId': round_id}, 200
    except Exception as e: return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/casino/race/bet', methods=['POST'])
def race_bet():
    db = get_db(); c = db.cursor()
    try:
        data      = request.get_json()
        round_id  = int(data.get('roundId', 0))
        group_id  = int(data.get('groupId', 0))
        user_id   = int(data.get('userId', 0))
        user_name = (data.get('userName') or f"id:{user_id}").strip()
        bet_on    = data.get('betOn', '')
        amount    = int(data.get('amount', 0))

        if bet_on not in ['rabbit','turtle']:
            return {'ok': False, 'error': '올바른 베팅 대상을 선택해주세요.'}, 400
        if is_casino_blacklisted(group_id, user_id):
            return {'ok': False, 'error': '게임 이용이 제한된 계정이에요.'}, 403

        settings = get_casino_settings(group_id, 'race')
        if amount < settings.get('min_bet', 10):
            return {'ok': False, 'error': f"최소 {settings['min_bet']:,}P 이상 베팅해주세요."}, 400
        if amount > settings.get('max_bet', 10000):
            return {'ok': False, 'error': f"최대 {settings['max_bet']:,}P 까지 베팅 가능해요."}, 400

        c.execute("SELECT status FROM casino_games WHERE id=%s", (round_id,))
        row = c.fetchone()
        if not row or row[0] != 'betting':
            return {'ok': False, 'error': '베팅 시간이 아니에요.'}, 400

        # 이미 베팅했는지
        c.execute("SELECT id FROM casino_bets WHERE round_id=%s AND user_id=%s", (round_id, user_id))
        if c.fetchone():
            return {'ok': False, 'error': '이미 베팅하셨어요.'}, 400

        # 포인트 차감
        c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
        pt_row = c.fetchone()
        if not pt_row or pt_row[0] < amount:
            return {'ok': False, 'error': f"포인트가 부족해요."}, 400
        c.execute("UPDATE points SET point=point-%s WHERE user_id=%s AND group_id=%s", (amount, user_id, group_id))
        c.execute("INSERT INTO casino_bets (game_id, round_id, group_id, user_id, user_name, bet_on, amount) VALUES ('race',%s,%s,%s,%s,%s,%s)",
                  (round_id, group_id, user_id, user_name, bet_on, amount))
        db.commit()
        label = '🐇 토끼' if bet_on == 'rabbit' else '🐢 거북이'
        return {'ok': True, 'betOn': bet_on, 'amount': amount}, 200
    except Exception as e:
        import traceback; print(traceback.format_exc())
        return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/casino/race/start', methods=['POST'])
def race_start():
    """관리자가 경주 시작 (베팅 마감)"""
    db = get_db(); c = db.cursor()
    try:
        data     = request.get_json()
        admin_id = int(data.get('adminId', 0))
        round_id = int(data.get('roundId', 0))
        group_id = int(data.get('groupId', 0))
        if admin_id not in ADMIN_IDS:
            return {'ok': False, 'error': '관리자만 시작할 수 있어요.'}, 403
        c.execute("UPDATE casino_games SET status='running' WHERE id=%s AND group_id=%s", (round_id, group_id))
        db.commit()
        return {'ok': True}, 200
    except Exception as e: return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/casino/race/result', methods=['POST'])
def race_result():
    """경주 결과 처리"""
    db = get_db(); c = db.cursor()
    try:
        data     = request.get_json()
        admin_id = int(data.get('adminId', 0))
        round_id = int(data.get('roundId', 0))
        group_id = int(data.get('groupId', 0))
        if admin_id not in ADMIN_IDS:
            return {'ok': False, 'error': '관리자만 결과를 처리할 수 있어요.'}, 403

        settings    = get_casino_settings(group_id, 'race')
        force       = settings.get('force_result')
        win_rate    = settings.get('rabbit_win_rate', 60)
        house_edge  = settings.get('house_edge', 5)

        # 결과 결정
        if force in ['rabbit','turtle']:
            winner = force
        else:
            winner = 'rabbit' if random.randint(1,100) <= win_rate else 'turtle'

        # 베팅 현황
        c.execute("SELECT bet_on, SUM(amount) FROM casino_bets WHERE round_id=%s GROUP BY bet_on", (round_id,))
        pool_rows = c.fetchall()
        pools = {r[0]: r[1] for r in pool_rows}
        total_pool = sum(pools.values())
        winner_pool = pools.get(winner, 0)

        # 배당률 계산
        if winner_pool > 0:
            odds = max(1.1, (total_pool * (1-house_edge/100)) / winner_pool)
        else:
            odds = 2.0

        # 당첨자 정산
        c.execute("SELECT id, user_id, user_name, amount FROM casino_bets WHERE round_id=%s AND bet_on=%s", (round_id, winner))
        winners = c.fetchall()
        winner_list = []
        for bet in winners:
            payout = int(bet[3] * odds)
            c.execute("UPDATE casino_bets SET won=TRUE, payout=%s WHERE id=%s", (payout, bet[0]))
            c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s", (payout, bet[1], group_id))
            winner_list.append({'name': bet[2], 'amount': bet[3], 'payout': payout})

        # 패자 처리
        c.execute("UPDATE casino_bets SET won=FALSE, payout=0 WHERE round_id=%s AND bet_on!=%s", (round_id, winner))
        c.execute("UPDATE casino_games SET status='closed', result=%s, ended_at=NOW() WHERE id=%s", (winner, round_id))
        db.commit()

        label = '🐇 토끼' if winner == 'rabbit' else '🐢 거북이'
        loser_label = '🐢 거북이' if winner == 'rabbit' else '🐇 토끼'
        winner_text = "\n".join([f"🏆 {w['name']} (+{w['payout']:,}P)" for w in winner_list[:10]])
        if not winner_text: winner_text = "베팅 참여자 없음"

        bot.send_message(group_id,
            f"🏁 <b>경주 결과!</b>\n──────────────────\n"
            f"🥇 <b>우승: {label}</b>  vs  {loser_label}\n"
            f"📊 배당률: {odds:.2f}배\n"
            f"💰 총 베팅: {total_pool:,}P\n──────────────────\n"
            f"<b>당첨자:</b>\n{winner_text}", parse_mode='HTML')

        return {'ok': True, 'winner': winner, 'odds': odds, 'winners': winner_list}, 200
    except Exception as e:
        import traceback; print(traceback.format_exc())
        return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

# ─────────────────────────────────────────────────────────
# /카지노 커맨드
# ─────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────
# 바카라
# ─────────────────────────────────────────────────────────
@app.route('/casino/baccarat')
def serve_baccarat(): return send_from_directory('.','baccarat.html')

@app.route('/casino/baccarat/state')
def baccarat_state():
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0))
        user_id=int(request.args.get('userId',0))
        c.execute("SELECT id,status,result,settings FROM casino_games WHERE group_id=%s AND game_id='baccarat' ORDER BY id DESC LIMIT 1",(group_id,))
        row=c.fetchone()
        if not row: return {'status':'idle','roundId':None,'myBet':None,'settings':get_casino_settings(group_id,'baccarat')},200
        round_id,status,result,settings=row
        my_bet=None
        if user_id:
            c.execute("SELECT bet_on,amount FROM casino_bets WHERE round_id=%s AND user_id=%s",(round_id,user_id))
            mb=c.fetchone()
            if mb: my_bet={'betOn':mb[0],'amount':mb[1]}
        return {'status':status,'roundId':round_id,'result':result,'myBet':my_bet,'settings':get_casino_settings(group_id,'baccarat')},200
    except Exception as e: return {'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/baccarat/open',methods=['POST'])
def baccarat_open():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); admin_id=int(data.get('adminId',0)); group_id=int(data.get('groupId',0))
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자만 시작할 수 있어요.'},403
        c.execute("SELECT id FROM casino_games WHERE group_id=%s AND game_id='baccarat' AND status NOT IN ('closed','cancelled')",(group_id,))
        if c.fetchone(): return {'ok':False,'error':'이미 진행 중인 게임이 있어요.'},400
        settings=get_casino_settings(group_id,'baccarat')
        c.execute("INSERT INTO casino_games (game_id,group_id,status,settings) VALUES ('baccarat',%s,'betting',%s) RETURNING id",(group_id,json.dumps(settings)))
        round_id=c.fetchone()[0]; db.commit()
        casino_url=f"{WEBAPP_BASE_URL}/casino/baccarat?groupId={group_id}"
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🃏 바카라 베팅하기",url=casino_url))
        bot.send_message(group_id,f"🃏 <b>바카라 베팅 시작!</b>\n──────────────────\n🔵 PLAYER vs 🔴 BANKER\n아래 버튼을 눌러 베팅하세요!",reply_markup=markup,parse_mode='HTML')
        return {'ok':True,'roundId':round_id},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/baccarat/bet',methods=['POST'])
def baccarat_bet():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); round_id=int(data.get('roundId',0)); group_id=int(data.get('groupId',0))
        user_id=int(data.get('userId',0)); bet_on=data.get('betOn',''); amount=int(data.get('amount',0))
        if bet_on not in ['player','banker','tie']: return {'ok':False,'error':'올바른 베팅 대상을 선택해주세요.'},400
        if is_casino_blacklisted(group_id,user_id): return {'ok':False,'error':'게임 이용이 제한된 계정이에요.'},403
        settings=get_casino_settings(group_id,'baccarat')
        if amount<settings.get('min_bet',10): return {'ok':False,'error':f"최소 {settings['min_bet']:,}P 이상 베팅해주세요."},400
        if amount>settings.get('max_bet',10000): return {'ok':False,'error':f"최대 {settings['max_bet']:,}P까지 베팅 가능해요."},400
        c.execute("SELECT status FROM casino_games WHERE id=%s",(round_id,))
        row=c.fetchone()
        if not row or row[0]!='betting': return {'ok':False,'error':'베팅 시간이 아니에요.'},400
        c.execute("SELECT id FROM casino_bets WHERE round_id=%s AND user_id=%s",(round_id,user_id))
        if c.fetchone(): return {'ok':False,'error':'이미 베팅하셨어요.'},400
        c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        pt=c.fetchone()
        if not pt or pt[0]<amount: return {'ok':False,'error':'포인트가 부족해요.'},400
        c.execute("UPDATE points SET point=point-%s WHERE user_id=%s AND group_id=%s",(amount,user_id,group_id))
        c.execute("INSERT INTO casino_bets (game_id,round_id,group_id,user_id,bet_on,amount) VALUES ('baccarat',%s,%s,%s,%s,%s)",(round_id,group_id,user_id,bet_on,amount))
        db.commit()
        return {'ok':True},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/baccarat/result',methods=['POST'])
def baccarat_result():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); admin_id=int(data.get('adminId',0)); round_id=int(data.get('roundId',0)); group_id=int(data.get('groupId',0))
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자만 결과를 처리할 수 있어요.'},403
        settings=get_casino_settings(group_id,'baccarat')
        force=settings.get('force_result'); p_rate=settings.get('player_win_rate',45); b_rate=settings.get('banker_win_rate',46)
        if force in ['player','banker','tie']: result=force
        else:
            r=random.randint(1,100)
            if r<=p_rate: result='player'
            elif r<=p_rate+b_rate: result='banker'
            else: result='tie'
        odds_map={'player':1.95,'banker':1.95,'tie':8.0}
        c.execute("SELECT id,user_id,bet_on,amount FROM casino_bets WHERE round_id=%s",(round_id,))
        bets=c.fetchall()
        winners=[]
        for bet in bets:
            if bet[2]==result:
                payout=int(bet[3]*odds_map.get(result,2))
                c.execute("UPDATE casino_bets SET won=TRUE,payout=%s WHERE id=%s",(payout,bet[0]))
                c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(payout,bet[1],group_id))
                winners.append(payout)
            else:
                c.execute("UPDATE casino_bets SET won=FALSE,payout=0 WHERE id=%s",(bet[0],))
        c.execute("UPDATE casino_games SET status='closed',result=%s,ended_at=NOW() WHERE id=%s",(result,round_id))
        db.commit()
        labels={'player':'🔵 PLAYER WIN','banker':'🔴 BANKER WIN','tie':'🟢 TIE'}
        total_pool=sum(b[3] for b in bets); total_payout=sum(winners)
        bot.send_message(group_id,f"🃏 <b>바카라 결과!</b>\n──────────────────\n🏆 <b>{labels.get(result,result)}</b>\n💰 총 베팅: {total_pool:,}P\n🎁 총 지급: {total_payout:,}P\n👥 참여자: {len(bets)}명",parse_mode='HTML')
        return {'ok':True,'result':result},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

# ─────────────────────────────────────────────────────────
# 경마
# ─────────────────────────────────────────────────────────
@app.route('/casino/horse')
def serve_horse(): return send_from_directory('.','horse.html')

@app.route('/casino/horse/state')
def horse_state():
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0)); user_id=int(request.args.get('userId',0))
        c.execute("SELECT id,status,result,settings FROM casino_games WHERE group_id=%s AND game_id='horse' ORDER BY id DESC LIMIT 1",(group_id,))
        row=c.fetchone()
        settings=get_casino_settings(group_id,'horse')
        if not row: return {'status':'idle','roundId':None,'myBet':None,'bets':{},'settings':settings},200
        round_id,status,result,_=row
        c.execute("SELECT bet_on,SUM(amount),COUNT(*) FROM casino_bets WHERE round_id=%s GROUP BY bet_on",(round_id,))
        bets={str(r[0]):{'total':r[1],'count':r[2]} for r in c.fetchall()}
        my_bet=None
        if user_id:
            c.execute("SELECT bet_on,amount FROM casino_bets WHERE round_id=%s AND user_id=%s",(round_id,user_id))
            mb=c.fetchone()
            if mb: my_bet={'betOn':mb[0],'amount':mb[1]}
        return {'status':status,'roundId':round_id,'result':result,'bets':bets,'myBet':my_bet,'settings':settings},200
    except Exception as e: return {'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/horse/open',methods=['POST'])
def horse_open():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); admin_id=int(data.get('adminId',0)); group_id=int(data.get('groupId',0))
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자만 시작할 수 있어요.'},403
        c.execute("SELECT id FROM casino_games WHERE group_id=%s AND game_id='horse' AND status NOT IN ('closed','cancelled')",(group_id,))
        if c.fetchone(): return {'ok':False,'error':'이미 진행 중인 경마가 있어요.'},400
        settings=get_casino_settings(group_id,'horse')
        c.execute("INSERT INTO casino_games (game_id,group_id,status,settings) VALUES ('horse',%s,'betting',%s) RETURNING id",(group_id,json.dumps(settings)))
        round_id=c.fetchone()[0]; db.commit()
        horses=settings.get('horses',[])
        horse_list="\n".join([f"{h['emoji']} {h['name']} (배당 x{h.get('base_odds',2.5)})" for h in horses])
        casino_url=f"{WEBAPP_BASE_URL}/casino/horse?groupId={group_id}"
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🐴 경마 베팅하기",url=casino_url))
        bot.send_message(group_id,f"🐴 <b>경마 베팅 시작!</b>\n──────────────────\n{horse_list}\n──────────────────\n아래 버튼을 눌러 베팅하세요!",reply_markup=markup,parse_mode='HTML')
        return {'ok':True,'roundId':round_id},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/horse/bet',methods=['POST'])
def horse_bet():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); round_id=int(data.get('roundId',0)); group_id=int(data.get('groupId',0))
        user_id=int(data.get('userId',0)); bet_on=data.get('betOn'); amount=int(data.get('amount',0))
        if is_casino_blacklisted(group_id,user_id): return {'ok':False,'error':'게임 이용이 제한된 계정이에요.'},403
        settings=get_casino_settings(group_id,'horse')
        if amount<settings.get('min_bet',10): return {'ok':False,'error':f"최소 {settings['min_bet']:,}P 이상 베팅해주세요."},400
        if amount>settings.get('max_bet',10000): return {'ok':False,'error':f"최대 {settings['max_bet']:,}P까지 베팅 가능해요."},400
        c.execute("SELECT status FROM casino_games WHERE id=%s",(round_id,))
        row=c.fetchone()
        if not row or row[0]!='betting': return {'ok':False,'error':'베팅 시간이 아니에요.'},400
        c.execute("SELECT id FROM casino_bets WHERE round_id=%s AND user_id=%s",(round_id,user_id))
        if c.fetchone(): return {'ok':False,'error':'이미 베팅하셨어요.'},400
        c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        pt=c.fetchone()
        if not pt or pt[0]<amount: return {'ok':False,'error':'포인트가 부족해요.'},400
        c.execute("UPDATE points SET point=point-%s WHERE user_id=%s AND group_id=%s",(amount,user_id,group_id))
        c.execute("INSERT INTO casino_bets (game_id,round_id,group_id,user_id,bet_on,amount) VALUES ('horse',%s,%s,%s,%s,%s)",(round_id,group_id,user_id,str(bet_on),amount))
        db.commit()
        return {'ok':True},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/horse/result',methods=['POST'])
def horse_result():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); admin_id=int(data.get('adminId',0)); round_id=int(data.get('roundId',0)); group_id=int(data.get('groupId',0))
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자만 결과를 처리할 수 있어요.'},403
        settings=get_casino_settings(group_id,'horse')
        horses=settings.get('horses',[{'id':1,'name':'번개','win_rate':30,'base_odds':2.5},{'id':2,'name':'폭풍','win_rate':20,'base_odds':3.5},{'id':3,'name':'황금','win_rate':15,'base_odds':5.0},{'id':4,'name':'다이아','win_rate':10,'base_odds':7.0},{'id':5,'name':'불꽃','win_rate':25,'base_odds':3.0}])
        force=settings.get('force_result')
        if force:
            winner_h=next((h for h in horses if str(h['id'])==str(force) or h['name']==force),None)
        else:
            total_rate=sum(h.get('win_rate',20) for h in horses)
            r=random.randint(1,total_rate); acc=0; winner_h=horses[-1]
            for h in horses:
                acc+=h.get('win_rate',20)
                if r<=acc: winner_h=h; break
        winner_id=str(winner_h['id']); odds=winner_h.get('base_odds',2.5)
        c.execute("SELECT id,user_id,bet_on,amount FROM casino_bets WHERE round_id=%s",(round_id,))
        bets=c.fetchall(); winners=[]
        for bet in bets:
            if str(bet[2])==winner_id:
                payout=int(bet[3]*odds)
                c.execute("UPDATE casino_bets SET won=TRUE,payout=%s WHERE id=%s",(payout,bet[0]))
                c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(payout,bet[1],group_id))
                winners.append(payout)
            else: c.execute("UPDATE casino_bets SET won=FALSE,payout=0 WHERE id=%s",(bet[0],))
        c.execute("UPDATE casino_games SET status='closed',result=%s,ended_at=NOW() WHERE id=%s",(winner_id,round_id))
        db.commit()
        total_pool=sum(b[3] for b in bets); total_payout=sum(winners)
        bot.send_message(group_id,f"🐴 <b>경마 결과!</b>\n──────────────────\n🥇 <b>{winner_h.get('emoji','')} {winner_h['name']} 우승!</b>\n📊 배당: x{odds}\n💰 총 베팅: {total_pool:,}P\n🎁 총 지급: {total_payout:,}P",parse_mode='HTML')
        return {'ok':True,'result':winner_id,'winner':winner_h},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

# ─────────────────────────────────────────────────────────
# 빅휠 (혼자 즉시 스핀)
# ─────────────────────────────────────────────────────────
@app.route('/casino/bigwheel')
def serve_bigwheel(): return send_from_directory('.','bigwheel.html')

@app.route('/casino/bigwheel/spin',methods=['POST'])
def bigwheel_spin():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); group_id=int(data.get('groupId',0)); user_id=int(data.get('userId',0))
        bet_on=int(data.get('betOn',0)); amount=int(data.get('amount',0))
        if is_casino_blacklisted(group_id,user_id): return {'ok':False,'error':'게임 이용이 제한된 계정이에요.'},403
        settings=get_casino_settings(group_id,'bigwheel')
        segs=settings.get('segments',[
            {'label':'2배','multiplier':2,'color':'#1a3a6a','prob':30},
            {'label':'3배','multiplier':3,'color':'#1a4a2a','prob':20},
            {'label':'5배','multiplier':5,'color':'#4a3000','prob':15},
            {'label':'10배','multiplier':10,'color':'#4a1010','prob':10},
            {'label':'20배','multiplier':20,'color':'#3a1050','prob':5},
            {'label':'꽝','multiplier':0,'color':'#1a1a2a','prob':20},
        ])
        if amount<settings.get('min_bet',10): return {'ok':False,'error':f"최소 {settings['min_bet']:,}P 이상"},400
        if amount>settings.get('max_bet',10000): return {'ok':False,'error':f"최대 {settings['max_bet']:,}P까지"},400
        c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        pt=c.fetchone()
        if not pt or pt[0]<amount: return {'ok':False,'error':'포인트가 부족해요.'},400

        # 결과 결정
        total_prob=sum(s.get('prob',10) for s in segs)
        r=random.randint(1,total_prob); acc=0; result_idx=len(segs)-1
        for i,s in enumerate(segs):
            acc+=s.get('prob',10)
            if r<=acc: result_idx=i; break

        result_seg=segs[result_idx]
        payout=int(amount*result_seg['multiplier']) if result_seg['multiplier']>0 else 0
        house_cut=int(amount*(settings.get('house_edge',5)/100))
        net_payout=max(0,payout-house_cut) if payout>0 else 0

        # 포인트 처리
        c.execute("UPDATE points SET point=point-%s WHERE user_id=%s AND group_id=%s",(amount,user_id,group_id))
        if net_payout>0:
            c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(net_payout,user_id,group_id))

        # 기록
        c.execute("INSERT INTO casino_games (game_id,group_id,status,result,settings,ended_at) VALUES ('bigwheel',%s,'closed',%s,%s,NOW())",(group_id,result_seg['label'],json.dumps(settings)))
        round_id=c.lastrowid if hasattr(c,'lastrowid') else None
        db.commit()
        return {'ok':True,'resultIdx':result_idx,'result':result_seg,'payout':net_payout},200
    except Exception as e:
        import traceback; print(traceback.format_exc())
        return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()


# ─────────────────────────────────────────────────────────
# Webhook
# ─────────────────────────────────────────────────────────
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    try:
        json_str = request.stream.read().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        if update.message: handle_all(update.message)
        elif update.callback_query:
            if update.callback_query.data.startswith('kbo_'): handle_kbo_callback(update.callback_query)
            elif update.callback_query.data.startswith('nj_open:'): handle_nj_open(update.callback_query)
    except Exception as e:
        import traceback; print(f"webhook error: {e}\n{traceback.format_exc()}")
    return 'OK', 200

@app.route('/')
def index(): return 'Bot is running!', 200

try:
    init_db(); print("DB 초기화 성공!")
except Exception as e: print(f"DB init error: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
