import os
import re
import json
import random
import threading
import telebot
import psycopg2
import requests
import urllib.parse
import pytz
import uuid
import time
from telebot import types
from datetime import datetime, timedelta
from flask import Flask, request, send_from_directory, send_file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BOT_TOKEN = '8046489365:AAHAFBz4Ca07KcjqI0EJl76aIAu-rlVHw-4'
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

KST = pytz.timezone('Asia/Seoul')
UTC = pytz.utc

ADMIN_IDS = [8698678650, 8621088096, 7319936275]

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
<b>[평생]</b> · <a href="https://t.me/gamte59/127">띵벳</a>
<b>[평생]</b> · <a href="https://t.me/gamte59/123">스피드벳</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/44">지엑스뱃</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/60">우루스뱃</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/72">그랜드파리</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/74">룰라뱃</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/78">소울카지노</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/133">토지노인사이드</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/100">벨라뱃</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/100">부자뱃</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/111">로얄클럽</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/121">벳클라우드</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/125">라엘뱃</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/128">부엉이뱃</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/130">일식뱃</a>
<b>[도파민]</b> · <a href="https://t.me/gamte59/132">미르뱃</a>

💸 <b>급전</b>
──────────────────
<b>[도파민]</b> · <a href="https://t.me/gamte59/109">꾸러기급전</a>
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

💼 <b>이체 알바</b>
──────────────────
<b>[도파민]</b> · <a href="https://t.me/gamte59/87">창비팀 대면이체알바</a>

✨ <b>유심</b>
<b>[도파민]</b> · <a href="https://t.me/gamte59/104">친구유심</a>"""

KBO_TEAMS = ['KT', '삼성', 'LG', 'SSG', 'KIA', '한화', '두산', 'NC', '롯데', '키움']
KBO_TEAMS_DISPLAY = {
    'KT':'🔴 KT','삼성':'🔵 삼성','LG':'🔴 LG','SSG':'🟡 SSG','KIA':'🔴 KIA',
    '한화':'🟠 한화','두산':'🔵 두산','NC':'🔵 NC','롯데':'🔴 롯데','키움':'🟣 키움',
}

WEBAPP_BASE_URL = os.environ.get('WEBAPP_URL', 'https://telegram-bot-14vg.onrender.com')

CHAT_MILESTONES = {100: 500, 300: 1000, 500: 2000, 1000: 5000}

LEVELS = [
    {'name':'브론즈',  'emoji':'🥉', 'min_bet':0,      'max_bet':5000},
    {'name':'실버',    'emoji':'🥈', 'min_bet':10000,  'max_bet':8000},
    {'name':'골드',    'emoji':'🥇', 'min_bet':50000,  'max_bet':15000},
    {'name':'플래티넘','emoji':'💎', 'min_bet':200000, 'max_bet':30000},
    {'name':'다이아',  'emoji':'👑', 'min_bet':500000, 'max_bet':50000},
]

def get_user_level(total_bet):
    lvl = LEVELS[0]
    for l in LEVELS:
        if total_bet >= l['min_bet']: lvl = l
    return lvl

DAILY_MISSIONS = [
    {'id':'play3',  'desc':'오늘 3게임 참여',  'target':3,   'reward':500},
    {'id':'bet1000','desc':'1,000P 이상 베팅', 'target':1000,'reward':300},
    {'id':'win1',   'desc':'1번 당첨',          'target':1,   'reward':700},
]
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
    if dt is None: return None
    if dt.tzinfo is None: dt = UTC.localize(dt)
    else: dt = dt.astimezone(UTC)
    return dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')

def safe_mins(v):
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

        missing_cols = [
            ("points",       "total_bet",    "BIGINT DEFAULT 0"),
            ("points",       "last_attendance", "DATE"),
            ("casino_games", "started_at",   "TIMESTAMP DEFAULT NOW()"),
            ("casino_games", "settings",     "JSONB DEFAULT '{}'"),
        ]
        for tbl, col, typ in missing_cols:
            try:
                c.execute(f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS {col} {typ}")
                db.commit()
            except: db.rollback()

        extra_tables = [
            """CREATE TABLE IF NOT EXISTS daily_missions (
                id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL,
                group_id BIGINT NOT NULL, mission_id VARCHAR(30) NOT NULL,
                mission_date DATE NOT NULL, progress INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT FALSE,
                UNIQUE(user_id, group_id, mission_id, mission_date))""",
            """CREATE TABLE IF NOT EXISTS chat_milestone_logs (
                id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL,
                group_id BIGINT NOT NULL, milestone INTEGER NOT NULL,
                rewarded_date DATE NOT NULL,
                UNIQUE(user_id, group_id, milestone, rewarded_date))""",
            """CREATE TABLE IF NOT EXISTS bet_cooldowns (
                user_id BIGINT NOT NULL, group_id BIGINT NOT NULL,
                game_id VARCHAR(30) NOT NULL, last_bet TIMESTAMP,
                PRIMARY KEY(user_id, group_id, game_id))""",
            """CREATE TABLE IF NOT EXISTS daily_bet_totals (
                user_id BIGINT NOT NULL, group_id BIGINT NOT NULL,
                bet_date DATE NOT NULL, total INTEGER DEFAULT 0,
                PRIMARY KEY(user_id, group_id, bet_date))""",
            """CREATE TABLE IF NOT EXISTS auto_round_config (
                group_id BIGINT PRIMARY KEY,
                race_auto BOOLEAN DEFAULT TRUE,
                horse_auto BOOLEAN DEFAULT TRUE,
                round_minutes INTEGER DEFAULT 3,
                updated_at TIMESTAMP DEFAULT NOW())""",
            """CREATE TABLE IF NOT EXISTS withdrawal_requests (
                id SERIAL PRIMARY KEY, group_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL, user_name VARCHAR(255),
                amount INTEGER NOT NULL, status VARCHAR(20) DEFAULT 'pending',
                note TEXT, created_at TIMESTAMP DEFAULT NOW(),
                processed_at TIMESTAMP)""",
            """CREATE TABLE IF NOT EXISTS chat_milestone_settings (
                group_id BIGINT PRIMARY KEY,
                milestones JSONB DEFAULT '{}',
                enabled BOOLEAN DEFAULT TRUE,
                updated_at TIMESTAMP DEFAULT NOW())""",
            """CREATE TABLE IF NOT EXISTS point_logs (
                id SERIAL PRIMARY KEY, group_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL, user_name VARCHAR(255),
                amount INTEGER NOT NULL, reason TEXT,
                admin_id BIGINT, created_at TIMESTAMP DEFAULT NOW())""",
            """CREATE TABLE IF NOT EXISTS keyword_events (
                id SERIAL PRIMARY KEY, group_id BIGINT NOT NULL,
                admin_id BIGINT NOT NULL, title TEXT NOT NULL,
                keyword VARCHAR(100) NOT NULL, description TEXT DEFAULT '',
                max_participants INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(), ended_at TIMESTAMP)""",
            """CREATE TABLE IF NOT EXISTS keyword_event_participants (
                id SERIAL PRIMARY KEY,
                event_id INTEGER REFERENCES keyword_events(id),
                group_id BIGINT NOT NULL, user_id BIGINT NOT NULL,
                user_name VARCHAR(255),
                joined_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(event_id, user_id))""",
            """CREATE TABLE IF NOT EXISTS casino_open_status (
                group_id BIGINT PRIMARY KEY,
                is_open BOOLEAN DEFAULT FALSE,
                opened_by BIGINT,
                updated_at TIMESTAMP DEFAULT NOW())""",
        ]
        for ddl in extra_tables:
            try: c.execute(ddl); db.commit()
            except: db.rollback()

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
# ★ FIX: 카지노 오픈 상태 조회 함수 (DB 중복 커넥션 방지)
# ─────────────────────────────────────────────────────────
def is_casino_open(group_id):
    """카지노 오픈 여부 반환. DB 오류 시 True(열림) 반환해서 유저 차단 안 함"""
    db = get_db(); c = db.cursor()
    try:
        c.execute("SELECT is_open FROM casino_open_status WHERE group_id=%s", (group_id,))
        row = c.fetchone()
        return bool(row[0]) if row else False
    except:
        return False  # 조회 실패 시 닫힘으로 처리
    finally:
        try: c.close(); db.close()
        except: pass

# ─────────────────────────────────────────────────────────
# ★ FIX: 커맨드 분류 재설계
#
# CASINO_ONLY_COMMANDS  : 카지노가 열려있을 때만 허용 (일반 유저)
# ALWAYS_ALLOWED        : 카지노 오픈 여부와 무관하게 항상 허용
# ADMIN_ONLY_COMMANDS   : 관리자 전용 (카지노 상태 무관)
# ─────────────────────────────────────────────────────────
CASINO_ONLY_COMMANDS = [
    '/슬롯', '/룰렛', '/카지노',
    '/포인트', '/포인트랭킹',
    '/선물',
]

ALWAYS_ALLOWED_COMMANDS = [
    '/출석', '/리필',          # 항상 허용 (웹앱 안내)
    '/승', '/수정', '/리스트',
    '/채팅', '/채팅랭킹',
    '/내전', '/이벤트', '/투표', '/게임',
    '/제휴', '/노래',
    '/test',
]

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
def check_keyword_event(user_id, first_name, username, group_id, text):
    if not text: return
    text_stripped = text.strip()
    db = get_db(); c = db.cursor()
    try:
        c.execute("SELECT id,title,keyword,max_participants FROM keyword_events WHERE group_id=%s AND is_active=TRUE ORDER BY id DESC LIMIT 1",
                  (group_id,))
        ev = c.fetchone()
        if not ev: return
        ev_id, title, keyword, max_part = ev
        if text_stripped.lower() != keyword.lower(): return
        c.execute("SELECT 1 FROM keyword_event_participants WHERE event_id=%s AND user_id=%s", (ev_id, user_id))
        if c.fetchone(): return
        if max_part > 0:
            c.execute("SELECT COUNT(*) FROM keyword_event_participants WHERE event_id=%s", (ev_id,))
            current = c.fetchone()[0]
            if current >= max_part:
                try:
                    bot.send_message(group_id, f"⚠️ <b>{title}</b> 이벤트 인원이 마감됐어요! ({max_part}명 완료)", parse_mode='HTML')
                    c.execute("UPDATE keyword_events SET is_active=FALSE,ended_at=NOW() WHERE id=%s", (ev_id,))
                    db.commit()
                except: pass
                return
        name = clean_name(first_name) or (f"@{username}" if username else f"id:{user_id}")
        c.execute("INSERT INTO keyword_event_participants(event_id,group_id,user_id,user_name) VALUES(%s,%s,%s,%s)",
                  (ev_id, group_id, user_id, name))
        db.commit()
        c.execute("SELECT COUNT(*) FROM keyword_event_participants WHERE event_id=%s", (ev_id,))
        total = c.fetchone()[0]
        try:
            bot.send_message(group_id,
                f"✅ <b>{name}</b>님 이벤트 참여 완료!\n🏷 <b>{title}</b>\n👥 현재 참여자: {total}명" + (f" / {max_part}명" if max_part > 0 else ""),
                parse_mode='HTML')
        except: pass
        if max_part > 0 and total >= max_part:
            try:
                c.execute("UPDATE keyword_events SET is_active=FALSE,ended_at=NOW() WHERE id=%s", (ev_id,))
                db.commit()
                bot.send_message(group_id, f"🎉 <b>{title}</b> 이벤트 인원 마감!\n👥 총 {total}명 참여 완료!\n📋 /이벤트참여자 — 참여자 목록 확인", parse_mode='HTML')
            except: pass
    except Exception as e:
        print(f"keyword_event error: {e}")
        try: db.rollback()
        except: pass
    finally:
        try: c.close(); db.close()
        except: pass

def send_dm_link(user_id, group_id, title, desc, markup):
    """
    ★ FIX: DM 전송 실패 시 그룹에 짧은 안내 메시지 (3초 후 자동 삭제)
    """
    try:
        bot.send_message(user_id,
            f"{title}\n──────────────────\n{desc}\n──────────────────\n아래 버튼을 눌러 바로 이동하세요!",
            reply_markup=markup, parse_mode='HTML')
    except Exception as e:
        print(f"DM 전송 실패 (user_id:{user_id}): {e}")
        # DM 차단 유저에게 그룹 알림
        if group_id:
            try:
                sent = bot.send_message(group_id,
                    "⚠️ DM이 차단되어 있어요. @dopamin_ranking_bot 을 먼저 시작해주세요!")
                time.sleep(4)
                bot.delete_message(group_id, sent.message_id)
            except: pass

COOLDOWN_SECS = 30
DAILY_BET_LIMIT = 500000
SUSPICIOUS_THRESHOLD = 100000

def check_cooldown(user_id, group_id, game_id):
    db=get_db();c=db.cursor()
    try:
        c.execute("SELECT last_bet FROM bet_cooldowns WHERE user_id=%s AND group_id=%s AND game_id=%s",(user_id,group_id,game_id))
        row=c.fetchone()
        if not row: return False
        last=row[0]
        if last.tzinfo is None: last=UTC.localize(last)
        else: last=last.astimezone(UTC)
        return (datetime.now(UTC)-last).total_seconds()<COOLDOWN_SECS
    finally: c.close();db.close()

def set_cooldown(user_id, group_id, game_id):
    db=get_db();c=db.cursor()
    try:
        c.execute("""INSERT INTO bet_cooldowns(user_id,group_id,game_id,last_bet) VALUES(%s,%s,%s,NOW())
            ON CONFLICT(user_id,group_id,game_id) DO UPDATE SET last_bet=NOW()""",(user_id,group_id,game_id))
        db.commit()
    finally: c.close();db.close()

def check_daily_limit(user_id, group_id, amount):
    db=get_db();c=db.cursor()
    try:
        today=datetime.now(KST).date()
        c.execute("SELECT total FROM daily_bet_totals WHERE user_id=%s AND group_id=%s AND bet_date=%s",(user_id,group_id,today))
        row=c.fetchone(); current=row[0] if row else 0
        return (current+amount)>DAILY_BET_LIMIT
    finally: c.close();db.close()

def add_daily_bet(user_id, group_id, amount):
    db=get_db();c=db.cursor()
    try:
        today=datetime.now(KST).date()
        c.execute("""INSERT INTO daily_bet_totals(user_id,group_id,bet_date,total) VALUES(%s,%s,%s,%s)
            ON CONFLICT(user_id,group_id,bet_date) DO UPDATE SET total=daily_bet_totals.total+%s""",(user_id,group_id,today,amount,amount))
        db.commit()
    finally: c.close();db.close()

def check_suspicious(group_id, user_id, amount, game_id):
    if amount>=SUSPICIOUS_THRESHOLD:
        for admin_id in ADMIN_IDS:
            try: bot.send_message(admin_id,f"⚠️ <b>이상 베팅 감지</b>\n게임: {game_id}\n유저: {user_id}\n금액: {amount:,}P",parse_mode='HTML')
            except: pass

def update_mission(user_id, group_id, mission_id, increment=1):
    db=get_db();c=db.cursor()
    try:
        today=datetime.now(KST).date()
        mission=next((m for m in DAILY_MISSIONS if m['id']==mission_id),None)
        if not mission: return
        c.execute("""INSERT INTO daily_missions(user_id,group_id,mission_id,mission_date,progress)
            VALUES(%s,%s,%s,%s,%s) ON CONFLICT(user_id,group_id,mission_id,mission_date)
            DO UPDATE SET progress=LEAST(daily_missions.progress+%s,%s)
            WHERE NOT daily_missions.completed""",
            (user_id,group_id,mission_id,today,increment,increment,mission['target']))
        c.execute("SELECT progress,completed FROM daily_missions WHERE user_id=%s AND group_id=%s AND mission_id=%s AND mission_date=%s",
                  (user_id,group_id,mission_id,today))
        row=c.fetchone()
        if row and not row[1] and row[0]>=mission['target']:
            c.execute("UPDATE daily_missions SET completed=TRUE WHERE user_id=%s AND group_id=%s AND mission_id=%s AND mission_date=%s",
                      (user_id,group_id,mission_id,today))
            c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(mission['reward'],user_id,group_id))
            c.execute("INSERT INTO point_logs(group_id,user_id,user_name,amount,reason) SELECT %s,%s,first_name,%s,%s FROM points WHERE user_id=%s AND group_id=%s",
                      (group_id,user_id,mission['reward'],f"데일리 미션: {mission['desc']}",user_id,group_id))
        db.commit()
    except Exception as e: print(f"mission error: {e}"); db.rollback()
    finally: c.close();db.close()

def get_milestone_settings(group_id):
    db=get_db();c=db.cursor()
    try:
        c.execute("SELECT milestones,enabled FROM chat_milestone_settings WHERE group_id=%s",(group_id,))
        row=c.fetchone()
        if row and row[0]: return {'milestones':row[0],'enabled':row[1]}
        return {'milestones':CHAT_MILESTONES,'enabled':True}
    finally: c.close();db.close()

def check_chat_milestone(user_id, group_id, first_name, username):
    db=get_db();c=db.cursor()
    try:
        ms_cfg=get_milestone_settings(group_id)
        if not ms_cfg.get('enabled',True): return
        milestones=ms_cfg.get('milestones',CHAT_MILESTONES)
        milestone_map={int(k):v for k,v in milestones.items()} if isinstance(milestones,dict) else CHAT_MILESTONES
        today=datetime.now(KST).date()
        c.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND DATE(message_date)=%s",(user_id,group_id,today))
        cnt=c.fetchone()[0]
        for milestone,reward in milestone_map.items():
            if cnt>=milestone:
                c.execute("SELECT 1 FROM chat_milestone_logs WHERE user_id=%s AND group_id=%s AND milestone=%s AND rewarded_date=%s",
                          (user_id,group_id,milestone,today))
                if not c.fetchone():
                    c.execute("INSERT INTO chat_milestone_logs(user_id,group_id,milestone,rewarded_date) VALUES(%s,%s,%s,%s)",
                              (user_id,group_id,milestone,today))
                    c.execute("""INSERT INTO points(user_id,group_id,first_name,username,point)
                        VALUES(%s,%s,%s,%s,%s) ON CONFLICT(user_id,group_id)
                        DO UPDATE SET point=points.point+%s""",(user_id,group_id,first_name,username,reward,reward))
                    c.execute("INSERT INTO point_logs(group_id,user_id,user_name,amount,reason) VALUES(%s,%s,%s,%s,%s)",
                              (group_id,user_id,first_name,reward,f'채팅 {milestone}회 달성'))
                    db.commit()
                    try: bot.send_message(group_id,f"🎉 <b>{first_name}</b>님 오늘 채팅 <b>{milestone}회</b> 달성!\n💰 보너스 <b>{reward:,}P</b> 지급!",parse_mode='HTML')
                    except: pass
        db.commit()
    except Exception as e:
        print(f"chat_milestone error: {e}")
        try: db.rollback()
        except: pass
    finally: c.close();db.close()

def auto_race_round():
    db=get_db();c=db.cursor()
    try:
        c.execute("SELECT DISTINCT group_id FROM casino_games WHERE game_id='race' AND created_at>NOW()-INTERVAL '30 days'")
        groups=[r[0] for r in c.fetchall()]
        c.execute("SELECT group_id FROM auto_round_config WHERE race_auto=TRUE")
        groups=list(set(groups+[r[0] for r in c.fetchall()]))
        for group_id in groups:
            try:
                settings=get_casino_settings(group_id,'race')
                if not settings.get('auto_round',True): continue
                c.execute("SELECT id,status,started_at FROM casino_games WHERE group_id=%s AND game_id='race' AND status NOT IN ('closed','cancelled') ORDER BY id DESC LIMIT 1",(group_id,))
                row=c.fetchone()
                if not row:
                    c.execute("INSERT INTO casino_games(game_id,group_id,status,settings,started_at) VALUES('race',%s,'betting',%s,NOW())",(group_id,json.dumps(settings)))
                    db.commit()
                else:
                    round_id,status,started_at=row
                    if started_at and status=='betting':
                        started=started_at.replace(tzinfo=UTC) if started_at.tzinfo is None else started_at.astimezone(UTC)
                        elapsed=(datetime.now(UTC)-started).total_seconds()
                        if elapsed>=settings.get('round_minutes',3)*60:
                            force=settings.get('force_result'); win_rate=settings.get('rabbit_win_rate',60); house=settings.get('house_edge',5)
                            winner=force if force in ['rabbit','turtle'] else ('rabbit' if random.randint(1,100)<=win_rate else 'turtle')
                            c.execute("SELECT bet_on,SUM(amount) FROM casino_bets WHERE round_id=%s GROUP BY bet_on",(round_id,))
                            pools={r[0]:r[1] for r in c.fetchall()}; total_pool=sum(pools.values()); winner_pool=pools.get(winner,0)
                            odds=max(1.1,(total_pool*(1-house/100))/winner_pool) if winner_pool>0 else 2.0
                            c.execute("SELECT id,user_id,amount FROM casino_bets WHERE round_id=%s AND bet_on=%s",(round_id,winner))
                            for bet in c.fetchall():
                                payout=int(bet[2]*odds)
                                c.execute("UPDATE casino_bets SET won=TRUE,payout=%s WHERE id=%s",(payout,bet[0]))
                                c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(payout,bet[1],group_id))
                            c.execute("UPDATE casino_bets SET won=FALSE,payout=0 WHERE round_id=%s AND bet_on!=%s",(round_id,winner))
                            c.execute("UPDATE casino_games SET status='closed',result=%s,ended_at=NOW() WHERE id=%s",(winner,round_id))
                            c.execute("INSERT INTO casino_games(game_id,group_id,status,settings,started_at) VALUES('race',%s,'betting',%s,NOW())",(group_id,json.dumps(settings)))
                            db.commit()
            except Exception as e:
                print(f"auto_race error {group_id}: {e}")
                try: db.rollback()
                except: pass
    except Exception as e: print(f"auto_race_round error: {e}")
    finally:
        try: c.close();db.close()
        except: pass

def auto_horse_round():
    db=get_db();c=db.cursor()
    try:
        c.execute("SELECT DISTINCT group_id FROM casino_games WHERE game_id='horse' AND created_at>NOW()-INTERVAL '30 days'")
        groups=[r[0] for r in c.fetchall()]
        c.execute("SELECT group_id FROM auto_round_config WHERE horse_auto=TRUE")
        groups=list(set(groups+[r[0] for r in c.fetchall()]))
        for group_id in groups:
            try:
                settings=get_casino_settings(group_id,'horse')
                if not settings.get('auto_round',True): continue
                c.execute("SELECT id,status,started_at FROM casino_games WHERE group_id=%s AND game_id='horse' AND status NOT IN ('closed','cancelled') ORDER BY id DESC LIMIT 1",(group_id,))
                row=c.fetchone()
                if not row:
                    c.execute("INSERT INTO casino_games(game_id,group_id,status,settings,started_at) VALUES('horse',%s,'betting',%s,NOW())",(group_id,json.dumps(settings)))
                    db.commit()
                else:
                    round_id,status,started_at=row
                    if started_at and status=='betting':
                        started=started_at.replace(tzinfo=UTC) if started_at.tzinfo is None else started_at.astimezone(UTC)
                        elapsed=(datetime.now(UTC)-started).total_seconds()
                        if elapsed>=settings.get('round_minutes',3)*60:
                            horses=settings.get('horses',DEFAULT_CASINO_SETTINGS['horse']['horses'])
                            force=settings.get('force_result')
                            if force:
                                winner_h=next((h for h in horses if str(h['id'])==str(force) or h['name']==force),None) or horses[0]
                            else:
                                total_rate=sum(h.get('win_rate',20) for h in horses); r=random.randint(1,total_rate); acc=0; winner_h=horses[-1]
                                for h in horses:
                                    acc+=h.get('win_rate',20)
                                    if r<=acc: winner_h=h; break
                            winner_id=str(winner_h['id']); odds=winner_h.get('base_odds',2.5)
                            c.execute("SELECT id,user_id,amount,bet_on FROM casino_bets WHERE round_id=%s",(round_id,))
                            for bet in c.fetchall():
                                if str(bet[3])==winner_id:
                                    payout=int(bet[2]*odds)
                                    c.execute("UPDATE casino_bets SET won=TRUE,payout=%s WHERE id=%s",(payout,bet[0]))
                                    c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(payout,bet[1],group_id))
                                else:
                                    c.execute("UPDATE casino_bets SET won=FALSE,payout=0 WHERE id=%s",(bet[0],))
                            c.execute("UPDATE casino_games SET status='closed',result=%s,ended_at=NOW() WHERE id=%s",(winner_id,round_id))
                            c.execute("INSERT INTO casino_games(game_id,group_id,status,settings,started_at) VALUES('horse',%s,'betting',%s,NOW())",(group_id,json.dumps(settings)))
                            db.commit()
            except Exception as e:
                print(f"auto_horse error {group_id}: {e}")
                try: db.rollback()
                except: pass
    except Exception as e: print(f"auto_horse_round error: {e}")
    finally:
        try: c.close();db.close()
        except: pass

def start_scheduler():
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler=BackgroundScheduler(timezone=UTC)
    scheduler.add_job(auto_race_round,'interval',seconds=30,id='auto_race')
    scheduler.add_job(auto_horse_round,'interval',seconds=30,id='auto_horse')
    scheduler.start()
    print("✅ 스케줄러 시작")

# ─────────────────────────────────────────────────────────
# ★ 핵심 메시지 핸들러 (완전 재작성)
# ─────────────────────────────────────────────────────────
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    try:
        text = message.text or ''; user_id = message.from_user.id
        group_id = message.chat.id; first_name = message.from_user.first_name or '사용자'
        username = message.from_user.username or ''; now_kst = datetime.now(KST); today = now_kst.date()

        # ── 커맨드 처리 ──
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

        # ── ★ FIX: /출석 — 채팅방은 깔끔하게, 웹앱으로 안내 ──
        elif '/출석' in text:
            if message.chat.type == 'private': return
            casino_url = f"{WEBAPP_BASE_URL}/casino?userId={user_id}&groupId={group_id}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📅 출석 체크하기", url=casino_url))
            try:
                # 그룹 메시지 즉시 삭제
                bot.delete_message(group_id, message.message_id)
            except: pass
            # 그룹에 버튼만 표시 (텍스트 최소화)
            sent = bot.send_message(group_id,
                f"📅 <b>{first_name}</b>님 출석 체크!",
                reply_markup=markup, parse_mode='HTML')
            # DM으로도 전송 (조용히)
            send_dm_link(user_id, None,
                "📅 <b>출석 체크</b>",
                "카지노 홈에서 출석 체크 & 리필을 할 수 있어요!\n매일 +100P 출석 보너스!", markup)
            # 3초 후 그룹 메시지 삭제
            def _del():
                time.sleep(5)
                try: bot.delete_message(group_id, sent.message_id)
                except: pass
            threading.Thread(target=_del, daemon=True).start()

        # ── ★ FIX: /리필 — 채팅방은 깔끔하게, 웹앱으로 안내 ──
        elif '/리필' in text:
            if message.chat.type == 'private': return
            casino_url = f"{WEBAPP_BASE_URL}/casino?userId={user_id}&groupId={group_id}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("💧 리필하기", url=casino_url))
            try:
                bot.delete_message(group_id, message.message_id)
            except: pass
            sent = bot.send_message(group_id,
                f"💧 <b>{first_name}</b>님 포인트 리필!",
                reply_markup=markup, parse_mode='HTML')
            send_dm_link(user_id, None,
                "💧 <b>포인트 리필</b>",
                "카지노 홈에서 하루 5회 리필 가능해요!\n회당 +100P!", markup)
            def _del():
                time.sleep(5)
                try: bot.delete_message(group_id, sent.message_id)
                except: pass
            threading.Thread(target=_del, daemon=True).start()

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
            if my_point < amount: bot.reply_to(message, f"💸 포인트 부족!\n 보유: {my_point}포인트\n 필요: {amount}포인트"); return
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
            bot.reply_to(message, "🎮 게임 목록\n\n🎰 /슬롯 - 슬롯머신\n🎲 /다이스 - 다이스 배틀\n⚠️ 최소 배팅: 10포인트")

        # ── ★ FIX: /슬롯 /다이스 /카지노 — 중복 제거, url= 방식 통일 ──
        elif '/슬롯' in text:
            if message.chat.type == 'private': return
            slots_url = f"{WEBAPP_BASE_URL}/casino/slots?userId={user_id}&groupId={group_id}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🎰 슬롯머신 플레이", url=slots_url))
            bot.reply_to(message, "🎰", reply_markup=markup)
            send_dm_link(user_id, group_id, "🎰 <b>슬롯머신</b>", "최대 50배 잭팟 도전!", markup)

        elif '/다이스' in text:
            if message.chat.type == 'private': return
            dice_url = f"{WEBAPP_BASE_URL}/casino/dice?userId={user_id}&groupId={group_id}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🎲 다이스 배틀 플레이", url=dice_url))
            bot.reply_to(message, "🎲", reply_markup=markup)
            send_dm_link(user_id, group_id, "🎲 <b>다이스 배틀</b>", "봇과 주사위 대결! 승리시 1.95배!", markup)

        # ── ★ FIX: /카지노 중복 제거 — 하나로 통합 ──
        elif text.strip().startswith('/카지노') and not text.strip().startswith('/카지노관리'):
            if message.chat.type == 'private': return
            casino_url = f"{WEBAPP_BASE_URL}/casino?userId={user_id}&groupId={group_id}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🎰 카지노 입장", url=casino_url))
            bot.reply_to(message, "🎰", reply_markup=markup)
            send_dm_link(user_id, group_id, "🎰 <b>도파민 카지노</b>", "🐢 경주 · 🃏 바카라 · 🐴 경마\n🎰 슬롯 · 🎲 다이스 배틀", markup)

        elif '/채팅랭킹' in text:
            if message.chat.type == 'private': return
            monday = today - timedelta(days=today.weekday()); sunday = monday + timedelta(days=6)
            db = get_db(); c = db.cursor()
            try:
                c.execute("SELECT first_name,username,COUNT(*) as cnt FROM chat_logs WHERE group_id=%s AND message_date>=%s GROUP BY user_id,first_name,username ORDER BY cnt DESC LIMIT 5", (group_id, monday))
                rows = c.fetchall()
            finally: c.close(); db.close()
            medals = ['🥇','🥈','🥉','4️⃣','5️⃣']
            result = f"╔══ 🏆 주간 랭킹 ══╗\n 📅 {monday.strftime('%m/%d')} ~ {sunday.strftime('%m/%d')}\n\n"
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

        elif text.strip().startswith('/승'):
            if message.chat.type == 'private': return
            kbo_url = f"{WEBAPP_BASE_URL}/kbo?start={user_id}_{group_id}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚾ KBO 승 예측 참여하기", url=kbo_url))
            bot.reply_to(message, "⚾", reply_markup=markup)
            send_dm_link(user_id, group_id, "⚾ <b>KBO 승 예측</b>", "아래 버튼을 눌러 참여하세요!", markup)

        elif text.strip().startswith('/수정'):
            if message.chat.type == 'private': return
            kbo_url = f"{WEBAPP_BASE_URL}/kbo?start={user_id}_{group_id}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚾ KBO 승 예측 수정하기", url=kbo_url))
            bot.reply_to(message, "⚾", reply_markup=markup)
            send_dm_link(user_id, group_id, "⚾ <b>KBO 승 예측 수정</b>", "아래 버튼을 눌러 수정하세요!", markup)

        elif text.strip().startswith('/리스트'):
            if message.chat.type == 'private': return
            kbo_url = f"{WEBAPP_BASE_URL}/kbo?start={user_id}_{group_id}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📋 참여 목록 보기", url=kbo_url))
            bot.reply_to(message, "⚾", reply_markup=markup)
            send_dm_link(user_id, group_id, "📋 <b>KBO 참여 목록</b>", "아래 버튼을 눌러 확인하세요!", markup)

        elif text.strip().startswith('/내전수정'):
            if message.chat.type == 'private': return
            if user_id not in ADMIN_IDS: bot.reply_to(message, "⚠️ 관리자만 내전을 수정할 수 있어요!"); return
            parts = text.strip().split(); game_arg = parts[1] if len(parts) > 1 else ''
            game_map = {'롤':'lol','서든':'sa5','lol':'lol','sa':'sa5','sa5':'sa5','sa6':'sa6'}
            game_type = game_map.get(game_arg)
            if not game_type: bot.reply_to(message, "⚔️ 사용법: /내전수정 롤 또는 /내전수정 서든"); return
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

        elif text.strip().startswith('/카지노관리') or text.strip().startswith('/casino_admin'):
            if user_id not in ADMIN_IDS:
                bot.reply_to(message, "⚠️ 관리자만 사용할 수 있어요!"); return
            admin_url = f"{WEBAPP_BASE_URL}/casino/admin?adminId={user_id}&groupId={group_id}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("👑 관리자 페이지", url=admin_url))
            bot.reply_to(message, "👑 카지노 관리자 페이지", reply_markup=markup)

        elif text.strip().startswith('/이벤트종료'):
            if message.chat.type == 'private': return
            if user_id not in ADMIN_IDS: bot.reply_to(message,"⚠️ 관리자 전용"); return
            db=get_db();c=db.cursor()
            try:
                c.execute("UPDATE keyword_events SET is_active=FALSE,ended_at=NOW() WHERE group_id=%s AND is_active=TRUE",(group_id,))
                affected=c.rowcount; db.commit()
            finally: c.close();db.close()
            if affected>0: bot.reply_to(message,"✅ 이벤트가 종료됐어요!")
            else: bot.reply_to(message,"⚠️ 진행 중인 이벤트가 없어요.")

        elif text.strip().startswith('/이벤트참여자'):
            if message.chat.type == 'private': return
            if user_id not in ADMIN_IDS: bot.reply_to(message,"⚠️ 관리자 전용"); return
            db=get_db();c=db.cursor()
            try:
                c.execute("SELECT id,title,keyword FROM keyword_events WHERE group_id=%s AND is_active=TRUE ORDER BY id DESC LIMIT 1",(group_id,))
                ev=c.fetchone()
                if not ev: bot.reply_to(message,"⚠️ 진행 중인 이벤트가 없어요."); return
                c.execute("SELECT user_name,joined_at FROM keyword_event_participants WHERE event_id=%s ORDER BY joined_at",(ev[0],))
                parts=c.fetchall()
            finally: c.close();db.close()
            if not parts:
                bot.reply_to(message,f"📋 <b>{ev[1]}</b>\n참여자가 없어요.",parse_mode='HTML')
                return
            lines=[f"📋 <b>{ev[1]}</b> 참여자 목록 ({len(parts)}명)\n──────────────────"]
            for i,p in enumerate(parts,1):
                lines.append(f"   {i}. {p[0]}")
            bot.reply_to(message,"\n".join(lines),parse_mode='HTML')

        elif text.strip().startswith('/이벤트'):
            if message.chat.type == 'private': return
            if user_id not in ADMIN_IDS: bot.reply_to(message,"⚠️ 관리자 전용"); return
            args=text.strip().replace('/이벤트','').strip()
            if not args:
                bot.reply_to(message,
                    "📌 <b>이벤트 사용법</b>\n/이벤트 제목 | 키워드 | 설명 | 최대인원\n\n"
                    "<b>예시:</b>\n/이벤트 출석이벤트 | 참여 | 먼저 '참여' 입력한 10명 추첨! | 10\n\n"
                    "※ 참여자가 채팅창에 키워드를 입력하면 자동 참여돼요\n"
                    "/이벤트종료 — 이벤트 종료\n/이벤트참여자 — 참여자 목록", parse_mode='HTML')
                return
            parts_ev=[p.strip() for p in args.split('|')]
            title_ev   = parts_ev[0] if len(parts_ev)>0 else '이벤트'
            keyword_ev = parts_ev[1] if len(parts_ev)>1 else '참여'
            desc_ev    = parts_ev[2] if len(parts_ev)>2 else ''
            max_ev     = int(parts_ev[3]) if len(parts_ev)>3 and parts_ev[3].isdigit() else 0
            db=get_db();c=db.cursor()
            try:
                c.execute("UPDATE keyword_events SET is_active=FALSE,ended_at=NOW() WHERE group_id=%s AND is_active=TRUE",(group_id,))
                c.execute("INSERT INTO keyword_events(group_id,admin_id,title,keyword,description,max_participants) VALUES(%s,%s,%s,%s,%s,%s) RETURNING id",
                          (group_id,user_id,title_ev,keyword_ev,desc_ev,max_ev))
                ev_id=c.fetchone()[0]; db.commit()
            finally: c.close();db.close()
            max_str=f"\n👥 최대 인원: {max_ev}명" if max_ev>0 else ""
            desc_str=f"\n📢 {desc_ev}" if desc_ev else ""
            bot.send_message(group_id,
                f"🎉 <b>이벤트 시작!</b>\n──────────────────\n"
                f"🏷 <b>{title_ev}</b>{desc_str}{max_str}\n──────────────────\n"
                f"💬 채팅창에 <b>{keyword_ev}</b> 를 입력하면 자동 참여돼요!\n"
                f"📌 /이벤트참여자 — 참여자 확인\n📌 /이벤트종료 — 이벤트 종료", parse_mode='HTML')

        elif text.strip().startswith('/투표'):
            if message.chat.type == 'private': return
            if user_id not in ADMIN_IDS: bot.reply_to(message, "⚠️ 관리자만 투표 이벤트를 생성할 수 있어요!"); return
            room_id = str(uuid.uuid4())[:8]
            db = get_db(); c = db.cursor()
            try:
                c.execute("INSERT INTO vote_rooms (room_id, group_id, admin_id) VALUES (%s,%s,%s)", (room_id, group_id, user_id))
                db.commit()
            finally: c.close(); db.close()
            param = f"{user_id}|{group_id}|{room_id}"
            vote_url = f"{WEBAPP_BASE_URL}/vote?start={param}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚙️ 이벤트 설정하기", url=vote_url))
            bot.reply_to(message,
                "🎰 <b>도파민 투표 이벤트</b>\n──────────────────\n"
                "아래 버튼을 눌러 이벤트 내용, 타임어택 시간,\n추첨 스타일을 설정하고 스타트를 눌러주세요!\n\n"
                "⚠️ 관리자만 설정 화면이 보입니다.", reply_markup=markup, parse_mode='HTML')

        elif text.strip().startswith('/내전취소'):
            if message.chat.type == 'private': return
            if user_id not in ADMIN_IDS: bot.reply_to(message, "⚠️ 관리자만 내전을 취소할 수 있어요!"); return
            parts = text.strip().split(); game_arg = parts[1] if len(parts) > 1 else ''
            game_map = {'롤':'lol','서든':'sa','lol':'lol','sa':'sa','sa5':'sa5','sa6':'sa6'}
            game_type = game_map.get(game_arg)
            if not game_type: bot.reply_to(message, "⚔️ 사용법: /내전취소 롤 또는 /내전취소 서든"); return
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
            threading.Thread(target=check_chat_milestone,args=(user_id,group_id,first_name,username),daemon=True).start()
            threading.Thread(target=check_keyword_event,args=(user_id,first_name,username,group_id,text),daemon=True).start()

    except Exception as e:
        import traceback; print(f"handle_all error: {e}\n{traceback.format_exc()}")


# ─────────────────────────────────────────────────────────
# Flask 라우트 (기존과 동일 — 변경 없음)
# ─────────────────────────────────────────────────────────
@app.route('/kbo')
def serve_kbo(): return send_from_directory(BASE_DIR, 'kbo.html')

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
        if is_admin_req:
            if not admin_user_id or int(admin_user_id) not in ADMIN_IDS:
                return {'ok': False, 'error': '관리자 권한이 없어요.'}, 403
        else:
            now_kst = datetime.now(KST)
            if not is_vote_time(now_kst):
                return {'ok': False, 'error': '참여 가능 시간이 아니에요.'}, 403
        today = datetime.now(KST).date()
        c.execute("SELECT first_name, username FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
        row = c.fetchone()
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
            action_label = "수정 완료"; action = "수정"
        else:
            c.execute("INSERT INTO kbo_votes (user_id, group_id, first_name, username, teams, vote_date) VALUES (%s,%s,%s,%s,%s,%s)",
                      (user_id, group_id, first_name, username, teams_str, today))
            action_label = "예측 완료"; action = "완료"
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
        rows = c.fetchall(); result = []
        for row in rows:
            uid = row[0]; first = clean_name(row[1] or ''); uname = row[2] or ''
            name = first if first else (('@' + uname) if uname else ('id:' + str(uid)))
            result.append({'userId': uid, 'name': name, 'teams': row[3].split(',')})
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
    db = get_db(); c = db.cursor()
    try:
        user_id  = int(request.args.get('userId', 0))
        group_id = int(request.args.get('groupId', 0))
        now_kst  = datetime.now(KST); today = now_kst.date()
        vote_ok  = is_vote_time(now_kst)
        c.execute("SELECT first_name, username, teams FROM kbo_votes WHERE user_id=%s AND group_id=%s AND vote_date=%s",
                  (user_id, group_id, today))
        row = c.fetchone()
        if row:
            name  = clean_name(row[0]) if row[0] else (f"@{row[1]}" if row[1] else f"id:{user_id}")
            return {'voted': True, 'name': name, 'teams': row[2].split(','), 'isVoteTime': vote_ok}, 200
        return {'voted': False, 'isVoteTime': vote_ok}, 200
    except Exception as e:
        return {'voted': False, 'isVoteTime': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/naejeon')
def serve_naejeon(): return send_from_directory(BASE_DIR, 'naejeon.html')

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

@app.route('/vote')
def serve_vote(): return send_from_directory(BASE_DIR, 'vote.html')

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
            'endTime': to_utc_iso(row[8]),
            'participants': parts
        }, 200
    except Exception as e: return {'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/vote/start', methods=['POST'])
def vote_start():
    db = get_db(); c = db.cursor()
    try:
        data = request.get_json()
        room_id    = data.get('roomId'); user_id    = int(data.get('userId'))
        group_id   = int(data.get('groupId')); content    = data.get('content', '').strip()
        anim_style = data.get('animStyle', 'slot'); winners    = int(data.get('winners', 1))
        mins       = safe_mins(data.get('mins'))
        if user_id not in ADMIN_IDS: return {'ok': False, 'error': '관리자만 시작할 수 있어요.'}, 403
        if not content: return {'ok': False, 'error': '이벤트 내용을 입력해주세요.'}, 400
        end_time = datetime.now(UTC) + timedelta(minutes=mins) if mins else None
        c.execute("""UPDATE vote_rooms SET content=%s, mins=%s, winners=%s, anim_style=%s, started=TRUE, ended=FALSE, end_time=%s WHERE room_id=%s""",
            (content, mins, winners, anim_style, end_time, room_id))
        if c.rowcount == 0:
            return {'ok': False, 'error': f'room_id={room_id} 를 찾을 수 없어요.'}, 404
        db.commit()
        time_str   = f"{mins}분 타임어택" if mins else "제한 시간 없음"
        anim_names = {'slot':'🎰 슬롯머신','roulette':'🎡 룰렛','highlight':'⚡ 랜덤 하이라이트'}
        anim_label = anim_names.get(anim_style, anim_style)
        param    = f"{user_id}|{group_id}|{room_id}"
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
    "dice": {
        "win_odds": 1.95, "min_bet": 10, "max_bet": 10000,
        "house_edge": 5, "enabled": True
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

def is_casino_blacklisted(group_id, user_id):
    db = get_db(); c = db.cursor()
    try:
        c.execute("SELECT 1 FROM casino_blacklist WHERE group_id=%s AND user_id=%s", (group_id, user_id))
        return c.fetchone() is not None
    finally: c.close(); db.close()

@app.route('/casino')
def serve_casino(): return send_from_directory(BASE_DIR, 'casino.html')

@app.route('/casino/admin')
def serve_casino_admin(): return send_from_directory(BASE_DIR, 'casino_admin.html')

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

@app.route('/casino/attend', methods=['POST'])
def casino_attend():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json()
        user_id=int(data.get('userId',0)); group_id=int(data.get('groupId',0))
        today=datetime.now(KST).date()
        c.execute("SELECT last_attendance,first_name,username,point FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        row=c.fetchone()
        if row and row[0]==today:
            return {'ok':False,'error':'오늘 이미 출석했어요! 내일 다시 도전하세요 😊'},200
        reward=100
        name=row[1] or row[2] or f"id:{user_id}" if row else f"id:{user_id}"
        current_point=row[3] if row else 0
        if row:
            c.execute("UPDATE points SET point=point+%s,last_attendance=%s WHERE user_id=%s AND group_id=%s",
                      (reward,today,user_id,group_id))
        else:
            c.execute("INSERT INTO points(user_id,group_id,first_name,username,point,last_attendance) VALUES(%s,%s,%s,%s,%s,%s)",
                      (user_id,group_id,'','',reward,today))
        c.execute("INSERT INTO point_logs(group_id,user_id,user_name,amount,reason) VALUES(%s,%s,%s,%s,%s)",
                  (group_id,user_id,name,reward,'출석 보상'))
        db.commit()
        update_mission(user_id,group_id,'play3')
        return {'ok':True,'reward':reward,'newPoint':current_point+reward},200
    except Exception as e:
        import traceback; print(traceback.format_exc())
        return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/refill', methods=['POST'])
def casino_refill():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json()
        user_id=int(data.get('userId',0)); group_id=int(data.get('groupId',0))
        today=datetime.now(KST).date()
        c.execute("SELECT COUNT(*) FROM refill_logs WHERE user_id=%s AND group_id=%s AND refill_date=%s",
                  (user_id,group_id,today))
        count=c.fetchone()[0]
        if count>=5:
            return {'ok':False,'error':'오늘 리필을 5번 모두 사용했어요! 내일 다시 도전하세요 😊'},200
        reward=100
        c.execute("INSERT INTO refill_logs(user_id,group_id,first_name,username,refill_date) VALUES(%s,%s,%s,%s,%s)",
                  (user_id,group_id,'','',today))
        c.execute("""INSERT INTO points(user_id,group_id,first_name,username,point)
            VALUES(%s,%s,%s,%s,%s) ON CONFLICT(user_id,group_id)
            DO UPDATE SET point=points.point+%s""",
            (user_id,group_id,'','',reward,reward))
        c.execute("SELECT first_name,username,point FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        pr=c.fetchone()
        name=pr[0] or pr[1] or f"id:{user_id}" if pr else f"id:{user_id}"
        new_point=pr[2] if pr else reward
        c.execute("INSERT INTO point_logs(group_id,user_id,user_name,amount,reason) VALUES(%s,%s,%s,%s,%s)",
                  (group_id,user_id,name,reward,'리필'))
        db.commit()
        return {'ok':True,'reward':reward,'remaining':5-count-1,'newPoint':new_point},200
    except Exception as e:
        import traceback; print(traceback.format_exc())
        return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/point_grant', methods=['POST'])
def casino_point_grant():
    db = get_db(); c = db.cursor()
    try:
        data      = request.get_json()
        admin_id  = int(data.get('adminId', 0)); group_id  = int(data.get('groupId', 0))
        target_id = int(data.get('userId', 0));  amount    = int(data.get('amount', 0))
        reason    = data.get('reason', '관리자 지급')
        if admin_id not in ADMIN_IDS: return {'ok': False, 'error': '관리자만 사용할 수 있어요.'}, 403
        if amount == 0: return {'ok': False, 'error': '금액을 입력해주세요.'}, 400
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
            f"💰 <b>관리자 포인트 {action}</b>\n👤 {user_name}님\n{'➕' if amount>0 else '➖'} {abs(amount):,}P\n💼 잔여: {new_point:,}P\n📝 사유: {reason}", parse_mode='HTML')
        return {'ok': True, 'newPoint': new_point, 'userName': user_name}, 200
    except Exception as e: return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/casino/point_grant_all', methods=['POST'])
def casino_point_grant_all():
    db = get_db(); c = db.cursor()
    try:
        data     = request.get_json()
        admin_id = int(data.get('adminId', 0)); group_id = int(data.get('groupId', 0))
        amount   = int(data.get('amount', 0));  reason   = data.get('reason', '이벤트 지급')
        if admin_id not in ADMIN_IDS: return {'ok': False, 'error': '관리자만 사용할 수 있어요.'}, 403
        if amount <= 0: return {'ok': False, 'error': '지급 금액은 양수여야 해요.'}, 400
        c.execute("SELECT user_id, first_name, username FROM points WHERE group_id=%s", (group_id,))
        rows = c.fetchall()
        for row in rows:
            uid = row[0]; name = row[1] or row[2] or f"id:{uid}"
            c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s", (amount, uid, group_id))
            c.execute("INSERT INTO point_logs (group_id, user_id, user_name, amount, reason, admin_id) VALUES (%s,%s,%s,%s,%s,%s)",
                      (group_id, uid, name, amount, reason, admin_id))
        db.commit()
        bot.send_message(group_id, f"🎁 <b>전체 포인트 지급!</b>\n👥 {len(rows)}명에게 {amount:,}P 지급\n📝 사유: {reason}", parse_mode='HTML')
        return {'ok': True, 'count': len(rows)}, 200
    except Exception as e: return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/casino/blacklist', methods=['GET'])
def casino_get_blacklist():
    db = get_db(); c = db.cursor()
    try:
        group_id = int(request.args.get('groupId', 0))
        c.execute("""SELECT b.user_id, COALESCE(p.first_name, p.username, CAST(b.user_id AS VARCHAR)) as name,
                     b.reason, b.created_at FROM casino_blacklist b
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
        data = request.get_json()
        admin_id = int(data.get('adminId', 0)); group_id = int(data.get('groupId', 0))
        target_id = int(data.get('userId', 0)); reason = data.get('reason', ''); action = data.get('action', 'add')
        if admin_id not in ADMIN_IDS: return {'ok': False, 'error': '관리자만 사용할 수 있어요.'}, 403
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
    db = get_db(); c = db.cursor()
    try:
        group_id = int(request.args.get('groupId', 0)); days = int(request.args.get('days', 7))
        c.execute("""SELECT game_id, COUNT(*) as rounds,
                     SUM(CASE WHEN won THEN payout ELSE 0 END) as total_payout,
                     SUM(amount) as total_bet, COUNT(DISTINCT user_id) as players
                     FROM casino_bets WHERE group_id=%s AND created_at >= NOW() - INTERVAL '%s days'
                     GROUP BY game_id""", (group_id, days))
        rows = c.fetchall()
        return [{'gameId':r[0],'rounds':r[1],'totalPayout':r[2] or 0,'totalBet':r[3] or 0,
                 'profit':(r[3] or 0)-(r[2] or 0),'players':r[4]} for r in rows], 200
    except Exception as e: return [], 500
    finally: c.close(); db.close()

@app.route('/casino/point_logs')
def casino_point_logs():
    db = get_db(); c = db.cursor()
    try:
        group_id = int(request.args.get('groupId', 0)); limit = int(request.args.get('limit', 50))
        c.execute("SELECT user_name, amount, reason, created_at FROM point_logs WHERE group_id=%s ORDER BY created_at DESC LIMIT %s", (group_id, limit))
        rows = c.fetchall()
        return [{'userName':r[0],'amount':r[1],'reason':r[2],'createdAt':r[3].isoformat() if r[3] else None} for r in rows], 200
    except Exception as e: return [], 500
    finally: c.close(); db.close()

@app.route('/casino/users')
def casino_users():
    db = get_db(); c = db.cursor()
    try:
        group_id = int(request.args.get('groupId', 0))
        c.execute("""SELECT p.user_id, COALESCE(p.first_name, p.username, CAST(p.user_id AS VARCHAR)) as name,
                     p.point, CASE WHEN b.user_id IS NOT NULL THEN TRUE ELSE FALSE END as blacklisted
                     FROM points p LEFT JOIN casino_blacklist b ON b.user_id=p.user_id AND b.group_id=p.group_id
                     WHERE p.group_id=%s ORDER BY p.point DESC""", (group_id,))
        rows = c.fetchall()
        return [{'userId':r[0],'name':r[1],'point':r[2],'blacklisted':r[3]} for r in rows], 200
    except Exception as e: return [], 500
    finally: c.close(); db.close()

@app.route('/casino/race')
def serve_race(): return send_from_directory(BASE_DIR, 'race.html')

@app.route('/casino/race/state')
def race_state():
    db = get_db(); c = db.cursor()
    try:
        group_id = int(request.args.get('groupId', 0))
        c.execute("SELECT id, status, result, settings, created_at FROM casino_games WHERE group_id=%s AND game_id='race' ORDER BY id DESC LIMIT 1", (group_id,))
        row = c.fetchone()
        if not row: return {'status': 'idle', 'roundId': None, 'bets': {}, 'myBet': None}, 200
        round_id = row[0]; status = row[1]; result = row[2]
        user_id  = int(request.args.get('userId', 0))
        c.execute("SELECT bet_on, SUM(amount), COUNT(*) FROM casino_bets WHERE round_id=%s GROUP BY bet_on", (round_id,))
        bets_raw = c.fetchall()
        bets = {r[0]: {'total': r[1], 'count': r[2]} for r in bets_raw}
        total_pool = sum(b['total'] for b in bets.values())
        settings = get_casino_settings(group_id, 'race'); house = settings.get('house_edge', 5)
        odds = {}
        for opt in ['rabbit', 'turtle']:
            pool = bets.get(opt, {}).get('total', 0)
            if pool > 0 and total_pool > 0: odds[opt] = max(1.1, round((total_pool*(1-house/100))/pool, 2))
            else: odds[opt] = settings.get(f'{opt}_odds', 2.0)
        my_bet = None
        if user_id:
            c.execute("SELECT bet_on, amount FROM casino_bets WHERE round_id=%s AND user_id=%s", (round_id, user_id))
            mb = c.fetchone()
            if mb: my_bet = {'betOn': mb[0], 'amount': mb[1]}
        return {'status':status,'roundId':round_id,'result':result,'bets':bets,'odds':odds,'totalPool':total_pool,'myBet':my_bet,'settings':settings}, 200
    except Exception as e:
        import traceback; print(traceback.format_exc())
        return {'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/casino/race/open', methods=['POST'])
def race_open():
    db = get_db(); c = db.cursor()
    try:
        data = request.get_json(); admin_id = int(data.get('adminId', 0)); group_id = int(data.get('groupId', 0))
        if admin_id not in ADMIN_IDS: return {'ok': False, 'error': '관리자만 시작할 수 있어요.'}, 403
        c.execute("SELECT id FROM casino_games WHERE group_id=%s AND game_id='race' AND status NOT IN ('closed','cancelled')", (group_id,))
        if c.fetchone(): return {'ok': False, 'error': '이미 진행 중인 경주가 있어요.'}, 400
        settings = get_casino_settings(group_id, 'race')
        c.execute("INSERT INTO casino_games (game_id, group_id, status, settings) VALUES ('race',%s,'betting',%s) RETURNING id",
                  (group_id, json.dumps(settings)))
        round_id = c.fetchone()[0]; db.commit()
        casino_url = f"{WEBAPP_BASE_URL}/casino/race?groupId={group_id}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🐢 경주 베팅하기", url=casino_url))
        bot.send_message(group_id, f"🏁 <b>도파민 경주 시작!</b>\n──────────────────\n🐇 토끼 vs 🐢 거북이\n💰 최소 베팅: {settings.get('min_bet',10):,}P\n💰 최대 베팅: {settings.get('max_bet',10000):,}P\n──────────────────\n아래 버튼을 눌러 베팅하세요!", reply_markup=markup, parse_mode='HTML')
        return {'ok': True, 'roundId': round_id}, 200
    except Exception as e: return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/casino/race/bet', methods=['POST'])
def race_bet():
    db = get_db(); c = db.cursor()
    try:
        data = request.get_json(); round_id = int(data.get('roundId', 0)); group_id = int(data.get('groupId', 0))
        user_id = int(data.get('userId', 0)); user_name = (data.get('userName') or f"id:{user_id}").strip()
        bet_on = data.get('betOn', ''); amount = int(data.get('amount', 0))
        if bet_on not in ['rabbit','turtle']: return {'ok': False, 'error': '올바른 베팅 대상을 선택해주세요.'}, 400
        if is_casino_blacklisted(group_id, user_id): return {'ok': False, 'error': '게임 이용이 제한된 계정이에요.'}, 403
        settings = get_casino_settings(group_id, 'race')
        if amount < settings.get('min_bet', 10): return {'ok': False, 'error': f"최소 {settings['min_bet']:,}P 이상 베팅해주세요."}, 400
        if amount > settings.get('max_bet', 10000): return {'ok': False, 'error': f"최대 {settings['max_bet']:,}P 까지 베팅 가능해요."}, 400
        c.execute("SELECT status FROM casino_games WHERE id=%s", (round_id,))
        row = c.fetchone()
        if not row or row[0] != 'betting': return {'ok': False, 'error': '베팅 시간이 아니에요.'}, 400
        c.execute("SELECT id FROM casino_bets WHERE round_id=%s AND user_id=%s", (round_id, user_id))
        if c.fetchone(): return {'ok': False, 'error': '이미 베팅하셨어요.'}, 400
        c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
        pt_row = c.fetchone()
        if not pt_row or pt_row[0] < amount: return {'ok': False, 'error': f"포인트가 부족해요."}, 400
        c.execute("UPDATE points SET point=point-%s WHERE user_id=%s AND group_id=%s", (amount, user_id, group_id))
        c.execute("INSERT INTO casino_bets (game_id, round_id, group_id, user_id, user_name, bet_on, amount) VALUES ('race',%s,%s,%s,%s,%s,%s)",
                  (round_id, group_id, user_id, user_name, bet_on, amount))
        db.commit()
        return {'ok': True, 'betOn': bet_on, 'amount': amount}, 200
    except Exception as e:
        import traceback; print(traceback.format_exc())
        return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/casino/race/start', methods=['POST'])
def race_start():
    db = get_db(); c = db.cursor()
    try:
        data = request.get_json(); admin_id = int(data.get('adminId', 0))
        round_id = int(data.get('roundId', 0)); group_id = int(data.get('groupId', 0))
        if admin_id not in ADMIN_IDS: return {'ok': False, 'error': '관리자만 시작할 수 있어요.'}, 403
        c.execute("UPDATE casino_games SET status='running' WHERE id=%s AND group_id=%s", (round_id, group_id))
        db.commit()
        return {'ok': True}, 200
    except Exception as e: return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/casino/race/result', methods=['POST'])
def race_result():
    db = get_db(); c = db.cursor()
    try:
        data = request.get_json(); admin_id = int(data.get('adminId', 0))
        round_id = int(data.get('roundId', 0)); group_id = int(data.get('groupId', 0))
        if admin_id not in ADMIN_IDS: return {'ok': False, 'error': '관리자만 결과를 처리할 수 있어요.'}, 403
        settings = get_casino_settings(group_id, 'race')
        force = settings.get('force_result'); win_rate = settings.get('rabbit_win_rate', 60); house_edge = settings.get('house_edge', 5)
        if force in ['rabbit','turtle']: winner = force
        else: winner = 'rabbit' if random.randint(1,100) <= win_rate else 'turtle'
        c.execute("SELECT bet_on, SUM(amount) FROM casino_bets WHERE round_id=%s GROUP BY bet_on", (round_id,))
        pool_rows = c.fetchall(); pools = {r[0]: r[1] for r in pool_rows}
        total_pool = sum(pools.values()); winner_pool = pools.get(winner, 0)
        if winner_pool > 0: odds = max(1.1, (total_pool * (1-house_edge/100)) / winner_pool)
        else: odds = 2.0
        c.execute("SELECT id, user_id, user_name, amount FROM casino_bets WHERE round_id=%s AND bet_on=%s", (round_id, winner))
        winners = c.fetchall(); winner_list = []
        for bet in winners:
            payout = int(bet[3] * odds)
            c.execute("UPDATE casino_bets SET won=TRUE, payout=%s WHERE id=%s", (payout, bet[0]))
            c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s", (payout, bet[1], group_id))
            winner_list.append({'name': bet[2], 'amount': bet[3], 'payout': payout})
        c.execute("UPDATE casino_bets SET won=FALSE, payout=0 WHERE round_id=%s AND bet_on!=%s", (round_id, winner))
        c.execute("UPDATE casino_games SET status='closed', result=%s, ended_at=NOW() WHERE id=%s", (winner, round_id))
        db.commit()
        label = '🐇 토끼' if winner == 'rabbit' else '🐢 거북이'
        loser_label = '🐢 거북이' if winner == 'rabbit' else '🐇 토끼'
        winner_text = "\n".join([f"🏆 {w['name']} (+{w['payout']:,}P)" for w in winner_list[:10]])
        if not winner_text: winner_text = "베팅 참여자 없음"
        bot.send_message(group_id, f"🏁 <b>경주 결과!</b>\n──────────────────\n🥇 <b>우승: {label}</b>  vs  {loser_label}\n📊 배당률: {odds:.2f}배\n💰 총 베팅: {total_pool:,}P\n──────────────────\n<b>당첨자:</b>\n{winner_text}", parse_mode='HTML')
        return {'ok': True, 'winner': winner, 'odds': odds, 'winners': winner_list}, 200
    except Exception as e:
        import traceback; print(traceback.format_exc())
        return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/casino/slots')
def serve_slots(): return send_from_directory(BASE_DIR,'slots.html')

@app.route('/casino/slots/spin', methods=['POST'])
def slots_spin():
    db = get_db(); c = db.cursor()
    try:
        data = request.get_json(); group_id = int(data.get('groupId', 0)); user_id = int(data.get('userId', 0)); amount = int(data.get('amount', 0))
        if is_casino_blacklisted(group_id, user_id): return {'ok': False, 'error': '게임 이용이 제한된 계정이에요.'}, 403
        if amount < 20: return {'ok': False, 'error': '최소 20P 이상 베팅해주세요.'}, 400
        c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
        pt = c.fetchone()
        if not pt or pt[0] < amount: return {'ok': False, 'error': '포인트가 부족해요.'}, 400
        SYMBOLS = ['🍋','🍒','🍇','⭐','7️⃣','💎']; WEIGHTS = [30, 25, 20, 15, 7, 3]
        def weighted_rand():
            total = sum(WEIGHTS); r = random.randint(1, total); acc = 0
            for s, w in zip(SYMBOLS, WEIGHTS):
                acc += w
                if r <= acc: return s
            return SYMBOLS[0]
        s1, s2, s3 = weighted_rand(), weighted_rand(), weighted_rand(); result = [s1, s2, s3]
        MULT_3 = {'🍋':3,'🍒':4,'🍇':5,'⭐':7,'7️⃣':10,'💎':50}
        if s1 == s2 == s3: payout = amount * MULT_3.get(s1, 3)
        elif s1==s2 or s2==s3 or s1==s3: payout = int(amount * 1.5)
        else: payout = 0
        house_cut = int(payout * 0.05) if payout > 0 else 0
        net_payout = max(0, payout - house_cut)
        c.execute("UPDATE points SET point=point-%s,total_bet=COALESCE(total_bet,0)+%s WHERE user_id=%s AND group_id=%s", (amount, amount, user_id, group_id))
        if net_payout > 0: c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s", (net_payout, user_id, group_id))
        c.execute("INSERT INTO casino_games (game_id,group_id,status,result,settings,ended_at) VALUES ('slots',%s,'closed',%s,%s,NOW())",
                  (group_id, ''.join(result), json.dumps({'amount':amount,'payout':net_payout})))
        db.commit()
        add_daily_bet(user_id, group_id, amount); update_mission(user_id, group_id, 'play3')
        if net_payout > 0: update_mission(user_id, group_id, 'win1')
        return {'ok': True, 'payout': net_payout, 'result': result}, 200
    except Exception as e:
        import traceback; print(traceback.format_exc())
        return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/casino/dice')
def serve_dice(): return send_from_directory(BASE_DIR,'dice.html')

@app.route('/casino/dice/instant', methods=['POST'])
def dice_instant():
    """다이스 배틀 - 봇과 1:1 주사위 대결, 즉시 결과 처리"""
    db = get_db(); c = db.cursor()
    try:
        data = request.get_json(); group_id = int(data.get('groupId', 0)); user_id = int(data.get('userId', 0))
        amount = int(data.get('amount', 0))
        if is_casino_blacklisted(group_id, user_id): return {'ok': False, 'error': '게임 이용이 제한된 계정이에요.'}, 403
        if amount < 10: return {'ok': False, 'error': '최소 10P 이상 베팅해주세요.'}, 400
        if amount > 10000: return {'ok': False, 'error': '최대 10,000P까지 베팅 가능해요.'}, 400
        c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
        pt = c.fetchone()
        if not pt:
            c.execute("INSERT INTO points(user_id,group_id,first_name,username,point) VALUES(%s,%s,%s,%s,5000)",(user_id,group_id,'',''))
            db.commit(); current_pt=5000
        else: current_pt=pt[0]
        if current_pt < amount: return {'ok': False, 'error': '포인트가 부족해요.'}, 400

        player_roll = random.randint(1,6)
        bot_roll    = random.randint(1,6)
        if player_roll > bot_roll: result='win'
        elif player_roll < bot_roll: result='lose'
        else: result='draw'

        if result=='win':
            srv_payout = int(amount * 1.95)
            house_cut  = int(srv_payout * 0.05)
            payout = max(0, srv_payout - house_cut)
        elif result=='draw':
            payout = amount  # 베팅 환불
        else:
            payout = 0

        c.execute("UPDATE points SET point=point-%s WHERE user_id=%s AND group_id=%s", (amount, user_id, group_id))
        if payout > 0: c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s", (payout, user_id, group_id))
        won = (result=='win')
        c.execute("INSERT INTO casino_bets(game_id,group_id,user_id,bet_on,amount,payout,won) VALUES('dice',%s,%s,%s,%s,%s,%s)",
                  (group_id,user_id,f"{player_roll}v{bot_roll}",amount,payout,won))
        db.commit()
        add_daily_bet(user_id, group_id, amount); update_mission(user_id, group_id, 'play3')
        if won: update_mission(user_id, group_id, 'win1')
        return {'ok': True, 'playerRoll': player_roll, 'botRoll': bot_roll, 'result': result, 'payout': payout}, 200
    except Exception as e:
        import traceback; print(traceback.format_exc())
        return {'ok': False, 'error': str(e)}, 500
    finally: c.close(); db.close()

@app.route('/casino/baccarat')
def serve_baccarat(): return send_from_directory(BASE_DIR,'baccarat.html')

@app.route('/casino/baccarat/state')
def baccarat_state():
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0)); user_id=int(request.args.get('userId',0))
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
        c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
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
        bets=c.fetchall(); winners=[]
        for bet in bets:
            if bet[2]==result:
                payout=int(bet[3]*odds_map.get(result,2))
                c.execute("UPDATE casino_bets SET won=TRUE,payout=%s WHERE id=%s",(payout,bet[0]))
                c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(payout,bet[1],group_id))
                winners.append(payout)
            else: c.execute("UPDATE casino_bets SET won=FALSE,payout=0 WHERE id=%s",(bet[0],))
        c.execute("UPDATE casino_games SET status='closed',result=%s,ended_at=NOW() WHERE id=%s",(result,round_id))
        db.commit()
        labels={'player':'🔵 PLAYER WIN','banker':'🔴 BANKER WIN','tie':'🟢 TIE'}
        total_pool=sum(b[3] for b in bets); total_payout=sum(winners)
        bot.send_message(group_id,f"🃏 <b>바카라 결과!</b>\n──────────────────\n🏆 <b>{labels.get(result,result)}</b>\n💰 총 베팅: {total_pool:,}P\n🎁 총 지급: {total_payout:,}P\n👥 참여자: {len(bets)}명",parse_mode='HTML')
        return {'ok':True,'result':result},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/baccarat/instant', methods=['POST'])
def baccarat_instant():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json()
        group_id=int(data.get('groupId',0)); user_id=int(data.get('userId',0))
        bet_on=data.get('betOn',''); amount=int(data.get('amount',0))
        result=data.get('result','')
        if bet_on not in ['player','banker','tie']:
            return {'ok':False,'error':'올바른 베팅을 선택해주세요.'},400
        if is_casino_blacklisted(group_id,user_id):
            return {'ok':False,'error':'게임 이용이 제한된 계정이에요.'},403
        settings=get_casino_settings(group_id,'baccarat')
        if amount<settings.get('min_bet',10): return {'ok':False,'error':f"최소 {settings['min_bet']:,}P 이상"},400
        if amount>settings.get('max_bet',10000): return {'ok':False,'error':f"최대 {settings['max_bet']:,}P까지"},400
        c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        pt=c.fetchone()
        if not pt:
            c.execute("INSERT INTO points(user_id,group_id,first_name,username,point) VALUES(%s,%s,%s,%s,5000)",(user_id,group_id,'',''))
            db.commit(); current_pt=5000
        else: current_pt=pt[0]
        if current_pt<amount: return {'ok':False,'error':'포인트가 부족해요.'},400
        c.execute("UPDATE points SET point=point-%s WHERE user_id=%s AND group_id=%s",(amount,user_id,group_id))
        odds_map={'player':1.95,'banker':1.95,'tie':8.0}
        real_payout=int(amount*odds_map.get(result,2)) if bet_on==result else 0
        if real_payout>0:
            c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(real_payout,user_id,group_id))
        won=(bet_on==result)
        c.execute("INSERT INTO casino_bets(game_id,group_id,user_id,bet_on,amount,payout,won) VALUES('baccarat',%s,%s,%s,%s,%s,%s)",
                  (group_id,user_id,bet_on,amount,real_payout,won))
        db.commit()
        return {'ok':True,'payout':real_payout,'result':result,'won':won},200
    except Exception as e:
        import traceback; print(traceback.format_exc())
        return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/race/instant', methods=['POST'])
def race_instant():
    """즉시 1인 경주 - 서버가 결과 결정 후 포인트 처리"""
    db=get_db();c=db.cursor()
    try:
        data=request.get_json()
        group_id=int(data.get('groupId',0)); user_id=int(data.get('userId',0))
        bet_on=data.get('betOn',''); amount=int(data.get('amount',0))
        if bet_on not in ['rabbit','turtle']: return {'ok':False,'error':'토끼 또는 거북이를 선택해주세요.'},400
        if is_casino_blacklisted(group_id,user_id): return {'ok':False,'error':'게임 이용이 제한된 계정이에요.'},403
        if amount<10: return {'ok':False,'error':'최소 10P 이상 베팅해주세요.'},400
        c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        pt=c.fetchone()
        if not pt:
            c.execute("INSERT INTO points(user_id,group_id,first_name,username,point) VALUES(%s,%s,%s,%s,5000)",(user_id,group_id,'',''))
            db.commit(); current_pt=5000
        else: current_pt=pt[0]
        if current_pt<amount: return {'ok':False,'error':'포인트가 부족해요.'},400
        # 서버에서 결과 결정 (50:50)
        winner = random.choice(['rabbit','turtle'])
        won = (bet_on == winner)
        payout = int(amount * 1.9) if won else 0
        # 포인트 처리
        c.execute("UPDATE points SET point=point-%s WHERE user_id=%s AND group_id=%s",(amount,user_id,group_id))
        if payout>0: c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(payout,user_id,group_id))
        c.execute("INSERT INTO casino_bets(game_id,group_id,user_id,bet_on,amount,payout,won) VALUES('race',%s,%s,%s,%s,%s,%s)",
                  (group_id,user_id,bet_on,amount,payout,won))
        db.commit()
        return {'ok':True,'winner':winner,'payout':payout,'won':won},200
    except Exception as e:
        import traceback; print(traceback.format_exc())
        return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/horse/instant', methods=['POST'])
def horse_instant():
    """즉시 1인 경마 - 서버가 결과 결정 후 포인트 처리"""
    db=get_db();c=db.cursor()
    try:
        data=request.get_json()
        group_id=int(data.get('groupId',0)); user_id=int(data.get('userId',0))
        bet_on=int(data.get('betOn',0)); amount=int(data.get('amount',0))
        if is_casino_blacklisted(group_id,user_id): return {'ok':False,'error':'게임 이용이 제한된 계정이에요.'},403
        if amount<10: return {'ok':False,'error':'최소 10P 이상 베팅해주세요.'},400
        c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        pt=c.fetchone()
        if not pt:
            c.execute("INSERT INTO points(user_id,group_id,first_name,username,point) VALUES(%s,%s,%s,%s,5000)",(user_id,group_id,'',''))
            db.commit(); current_pt=5000
        else: current_pt=pt[0]
        if current_pt<amount: return {'ok':False,'error':'포인트가 부족해요.'},400
        # 서버에서 결과 결정 (가중 랜덤)
        DEFAULT_HORSES=[
            {'id':1,'weight':30,'odds':2.2},{'id':2,'weight':22,'odds':3.0},
            {'id':3,'weight':16,'odds':4.0},{'id':4,'weight':10,'odds':7.0},{'id':5,'weight':22,'odds':3.0}
        ]
        total=sum(h['weight'] for h in DEFAULT_HORSES)
        r=random.randint(1,total); acc=0; winner_h=DEFAULT_HORSES[-1]
        for h in DEFAULT_HORSES:
            acc+=h['weight']
            if r<=acc: winner_h=h; break
        winner_id=winner_h['id']
        won=(bet_on==winner_id)
        payout=int(amount*winner_h['odds']) if won else 0
        # 포인트 처리
        c.execute("UPDATE points SET point=point-%s WHERE user_id=%s AND group_id=%s",(amount,user_id,group_id))
        if payout>0: c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(payout,user_id,group_id))
        c.execute("INSERT INTO casino_bets(game_id,group_id,user_id,bet_on,amount,payout,won) VALUES('horse',%s,%s,%s,%s,%s,%s)",
                  (group_id,user_id,str(bet_on),amount,payout,won))
        db.commit()
        return {'ok':True,'winnerId':winner_id,'payout':payout,'won':won},200
    except Exception as e:
        import traceback; print(traceback.format_exc())
        return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/horse')
def serve_horse(): return send_from_directory(BASE_DIR,'horse.html')

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
        c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
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
            total_rate=sum(h.get('win_rate',20) for h in horses); r=random.randint(1,total_rate); acc=0; winner_h=horses[-1]
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

@app.route('/casino/open_status', methods=['GET'])
def casino_open_status_route():
    db=get_db(); c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0))
        c.execute("SELECT is_open FROM casino_open_status WHERE group_id=%s",(group_id,))
        row=c.fetchone()
        return {'isOpen': bool(row[0]) if row else False}, 200
    except: return {'isOpen':False}, 200
    finally: c.close(); db.close()

@app.route('/casino/open_toggle', methods=['POST'])
def casino_open_toggle():
    db=get_db(); c=db.cursor()
    try:
        data=request.get_json(); admin_id=int(data.get('adminId',0)); group_id=int(data.get('groupId',0)); is_open=bool(data.get('isOpen',False))
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        c.execute("INSERT INTO casino_open_status(group_id,is_open,opened_by,updated_at) VALUES(%s,%s,%s,NOW()) ON CONFLICT(group_id) DO UPDATE SET is_open=%s,opened_by=%s,updated_at=NOW()",
            (group_id,is_open,admin_id,is_open,admin_id))
        db.commit()
        try:
            msg = ("🎰 <b>카지노 오픈!</b>\n──────────────────\n지금 /카지노 를 입력해서 게임을 즐겨보세요!" if is_open
                   else "🔒 <b>카지노 마감</b>\n──────────────────\n카지노가 잠시 닫혔어요.")
            bot.send_message(group_id, msg, parse_mode='HTML')
        except: pass
        return {'ok':True,'isOpen':is_open}, 200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close(); db.close()

@app.route('/casino/check_admin')
def casino_check_admin():
    try:
        uid = int(request.args.get('userId',0) or request.args.get('adminId',0))
        return {'isAdmin': uid in ADMIN_IDS}, 200
    except: return {'isAdmin': False}, 200

@app.route('/casino/dashboard')
def casino_dashboard():
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0)); today=datetime.now(KST).date()
        c.execute("SELECT COALESCE(SUM(amount),0) FROM casino_bets WHERE group_id=%s AND DATE(created_at)=%s",(group_id,today))
        today_bet=c.fetchone()[0]
        c.execute("SELECT COALESCE(SUM(payout),0) FROM casino_bets WHERE group_id=%s AND won=TRUE AND DATE(created_at)=%s",(group_id,today))
        today_payout=c.fetchone()[0]
        c.execute("SELECT COUNT(DISTINCT user_id) FROM casino_bets WHERE group_id=%s AND DATE(created_at)=%s",(group_id,today))
        dau=c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM casino_games WHERE group_id=%s AND DATE(created_at)=%s",(group_id,today))
        rounds=c.fetchone()[0]
        c.execute("SELECT COALESCE(SUM(amount),0) FROM casino_bets WHERE group_id=%s AND created_at>=NOW()-INTERVAL '7 days'",(group_id,))
        week_bet=c.fetchone()[0]
        c.execute("SELECT COALESCE(SUM(payout),0) FROM casino_bets WHERE group_id=%s AND won=TRUE AND created_at>=NOW()-INTERVAL '7 days'",(group_id,))
        week_payout=c.fetchone()[0]
        return {'todayBet':int(today_bet),'todayPayout':int(today_payout),'todayProfit':int(today_bet-today_payout),
                'dau':dau,'rounds':rounds,'weekBet':int(week_bet),'weekProfit':int(week_bet-week_payout)},200
    except Exception as e: return {'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/missions')
def casino_missions():
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0)); user_id=int(request.args.get('userId',0))
        today=datetime.now(KST).date(); result=[]
        for m in DAILY_MISSIONS:
            c.execute("SELECT progress,completed FROM daily_missions WHERE user_id=%s AND group_id=%s AND mission_id=%s AND mission_date=%s",
                      (user_id,group_id,m['id'],today))
            row=c.fetchone()
            result.append({'id':m['id'],'desc':m['desc'],'target':m['target'],'reward':m['reward'],
                           'progress':row[0] if row else 0,'completed':row[1] if row else False})
        return result,200
    except Exception as e: return [],500
    finally: c.close();db.close()

@app.route('/casino/user_level')
def casino_user_level():
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0)); user_id=int(request.args.get('userId',0))
        c.execute("SELECT COALESCE(total_bet,0) FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        row=c.fetchone(); total_bet=row[0] if row else 0
        lvl=get_user_level(total_bet)
        return {'level':lvl,'totalBet':total_bet},200
    except: return {'level':LEVELS[0],'totalBet':0},200
    finally: c.close();db.close()

@app.route('/casino/my_bets')
def casino_my_bets():
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0)); user_id=int(request.args.get('userId',0)); limit=int(request.args.get('limit',30))
        c.execute("SELECT game_id,bet_on,amount,payout,won,created_at FROM casino_bets WHERE group_id=%s AND user_id=%s ORDER BY created_at DESC LIMIT %s",(group_id,user_id,limit))
        rows=c.fetchall()
        return [{'game':r[0],'choice':r[1],'amount':r[2],'payout':r[3],
                 'result':'win' if r[4] else ('lose' if r[4]==False else 'pending'),
                 'createdAt':r[5].isoformat() if r[5] else None} for r in rows],200
    except Exception as e: return [],500
    finally: c.close();db.close()

@app.route('/casino/withdraw', methods=['POST'])
def casino_withdraw():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); user_id=int(data.get('userId',0)); group_id=int(data.get('groupId',0))
        amount=int(data.get('amount',0)); note=data.get('note','')
        if amount<=0: return {'ok':False,'error':'금액을 입력해주세요.'},400
        c.execute("SELECT first_name,username,point FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        row=c.fetchone()
        if not row or row[2]<amount: return {'ok':False,'error':'포인트가 부족해요.'},400
        name=row[0] or row[1] or f"id:{user_id}"
        c.execute("INSERT INTO withdrawal_requests(group_id,user_id,user_name,amount,note) VALUES(%s,%s,%s,%s,%s)",(group_id,user_id,name,amount,note))
        db.commit()
        for admin_id in ADMIN_IDS:
            try: bot.send_message(admin_id,f"💸 <b>출금 신청</b>\n👤 {name}\n💰 {amount:,}P\n📝 {note or '없음'}",parse_mode='HTML')
            except: pass
        return {'ok':True},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/withdraw_list')
def casino_withdraw_list():
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0))
        c.execute("SELECT id,user_name,amount,status,note,created_at FROM withdrawal_requests WHERE group_id=%s ORDER BY created_at DESC LIMIT 50",(group_id,))
        rows=c.fetchall()
        return [{'id':r[0],'userName':r[1],'amount':r[2],'status':r[3],'note':r[4],'createdAt':r[5].isoformat() if r[5] else None} for r in rows],200
    except: return [],500
    finally: c.close();db.close()

@app.route('/casino/withdraw_process', methods=['POST'])
def casino_withdraw_process():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); admin_id=int(data.get('adminId',0)); req_id=int(data.get('requestId',0)); action=data.get('action','approve')
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        c.execute("SELECT user_id,group_id,amount,user_name,status FROM withdrawal_requests WHERE id=%s",(req_id,))
        row=c.fetchone()
        if not row: return {'ok':False,'error':'신청 없음'},404
        if row[4]!='pending': return {'ok':False,'error':'이미 처리됨'},400
        user_id,group_id,amount,user_name=row[0],row[1],row[2],row[3]
        if action=='approve':
            c.execute("UPDATE points SET point=point-%s WHERE user_id=%s AND group_id=%s",(amount,user_id,group_id))
            c.execute("INSERT INTO point_logs(group_id,user_id,user_name,amount,reason,admin_id) VALUES(%s,%s,%s,%s,%s,%s)",
                      (group_id,user_id,user_name,-amount,'출금 승인',admin_id))
            c.execute("UPDATE withdrawal_requests SET status='approved',processed_at=NOW() WHERE id=%s",(req_id,))
        else:
            c.execute("UPDATE withdrawal_requests SET status='rejected',processed_at=NOW() WHERE id=%s",(req_id,))
        db.commit()
        return {'ok':True},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/chat_milestone_settings', methods=['GET'])
def get_chat_milestone_settings():
    try:
        group_id=int(request.args.get('groupId',0))
        cfg=get_milestone_settings(group_id)
        return cfg,200
    except Exception as e: return {'error':str(e)},500

@app.route('/casino/chat_milestone_settings', methods=['POST'])
def save_chat_milestone_settings():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); admin_id=int(data.get('adminId',0)); group_id=int(data.get('groupId',0))
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        milestones=data.get('milestones',CHAT_MILESTONES); enabled=data.get('enabled',True)
        c.execute("INSERT INTO chat_milestone_settings(group_id,milestones,enabled,updated_at) VALUES(%s,%s,%s,NOW()) ON CONFLICT(group_id) DO UPDATE SET milestones=%s,enabled=%s,updated_at=NOW()",
            (group_id,json.dumps(milestones),enabled,json.dumps(milestones),enabled))
        db.commit()
        return {'ok':True},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/chat_milestone_status')
def chat_milestone_status():
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0)); today=datetime.now(KST).date()
        c.execute("""SELECT p.user_id,COALESCE(p.first_name,p.username,CAST(p.user_id AS VARCHAR)) as name,COUNT(cl.id) as today_count
            FROM points p LEFT JOIN chat_logs cl ON cl.user_id=p.user_id AND cl.group_id=p.group_id AND DATE(cl.message_date)=%s
            WHERE p.group_id=%s GROUP BY p.user_id,p.first_name,p.username ORDER BY today_count DESC""",(today,group_id))
        users=c.fetchall()
        c.execute("SELECT user_id,milestone FROM chat_milestone_logs WHERE group_id=%s AND rewarded_date=%s",(group_id,today))
        rewarded={(r[0],r[1]) for r in c.fetchall()}
        cfg=get_milestone_settings(group_id)
        milestones={int(k):v for k,v in cfg.get('milestones',CHAT_MILESTONES).items()} if isinstance(cfg.get('milestones'),dict) else CHAT_MILESTONES
        result=[]
        for u in users:
            uid,name,cnt=u
            ms_status={}
            for m,r in milestones.items():
                ms_status[str(m)]={'achieved':cnt>=m,'rewarded':(uid,m) in rewarded,'reward':r}
            result.append({'userId':uid,'name':name,'todayCount':cnt,'milestones':ms_status})
        return result,200
    except Exception as e: return [],500
    finally: c.close();db.close()

@app.route('/casino/chat_milestone_grant', methods=['POST'])
def chat_milestone_grant():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); admin_id=int(data.get('adminId',0)); group_id=int(data.get('groupId',0))
        target_id=int(data.get('userId',0)); milestone=int(data.get('milestone',0))
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        cfg=get_milestone_settings(group_id)
        milestones={int(k):v for k,v in cfg.get('milestones',CHAT_MILESTONES).items()} if isinstance(cfg.get('milestones'),dict) else CHAT_MILESTONES
        reward=milestones.get(milestone)
        if not reward: return {'ok':False,'error':'유효하지 않은 마일스톤'},400
        today=datetime.now(KST).date()
        c.execute("SELECT first_name,username FROM points WHERE user_id=%s AND group_id=%s",(target_id,group_id))
        row=c.fetchone()
        if not row: return {'ok':False,'error':'유저 없음'},404
        name=row[0] or row[1] or f"id:{target_id}"
        c.execute("SELECT 1 FROM chat_milestone_logs WHERE user_id=%s AND group_id=%s AND milestone=%s AND rewarded_date=%s",(target_id,group_id,milestone,today))
        if c.fetchone(): return {'ok':False,'error':'오늘 이미 지급됨'},400
        c.execute("INSERT INTO chat_milestone_logs(user_id,group_id,milestone,rewarded_date) VALUES(%s,%s,%s,%s)",(target_id,group_id,milestone,today))
        c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(reward,target_id,group_id))
        c.execute("INSERT INTO point_logs(group_id,user_id,user_name,amount,reason,admin_id) VALUES(%s,%s,%s,%s,%s,%s)",
                  (group_id,target_id,name,reward,f'채팅 {milestone}회 달성 (관리자 지급)',admin_id))
        db.commit()
        return {'ok':True,'reward':reward,'userName':name},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/auto_config', methods=['POST'])
def casino_auto_config():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); admin_id=int(data.get('adminId',0)); group_id=int(data.get('groupId',0))
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        race_auto=data.get('raceAuto',True); horse_auto=data.get('horseAuto',True); round_minutes=int(data.get('roundMinutes',3))
        c.execute("INSERT INTO auto_round_config(group_id,race_auto,horse_auto,round_minutes,updated_at) VALUES(%s,%s,%s,%s,NOW()) ON CONFLICT(group_id) DO UPDATE SET race_auto=%s,horse_auto=%s,round_minutes=%s,updated_at=NOW()",
            (group_id,race_auto,horse_auto,round_minutes,race_auto,horse_auto,round_minutes))
        db.commit()
        return {'ok':True},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/bet_cancel', methods=['POST'])
def bet_cancel():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); round_id=int(data.get('roundId',0)); group_id=int(data.get('groupId',0)); user_id=int(data.get('userId',0))
        c.execute("SELECT status,started_at,settings FROM casino_games WHERE id=%s AND group_id=%s",(round_id,group_id))
        row=c.fetchone()
        if not row: return {'ok':False,'error':'라운드 없음'},404
        if row[0]!='betting': return {'ok':False,'error':'베팅 마감 후에는 취소 불가'},400
        if row[1]:
            started=row[1].replace(tzinfo=UTC) if row[1].tzinfo is None else row[1].astimezone(UTC)
            elapsed=(datetime.now(UTC)-started).total_seconds()
            settings_db=row[2] or {}
            total_secs=(settings_db.get('round_minutes',3))*60
            remaining=total_secs-elapsed
            if remaining<30: return {'ok':False,'error':f'마감 30초 전에는 취소 불가 (남은:{int(remaining)}초)'},400
        c.execute("SELECT id,amount FROM casino_bets WHERE round_id=%s AND user_id=%s",(round_id,user_id))
        bet=c.fetchone()
        if not bet: return {'ok':False,'error':'베팅 기록 없음'},404
        c.execute("DELETE FROM casino_bets WHERE id=%s",(bet[0],))
        c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(bet[1],user_id,group_id))
        db.commit()
        return {'ok':True,'refund':bet[1]},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

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

@app.route('/admin/init_db')
def trigger_init_db():
    try:
        init_db()
        return '✅ DB 초기화 완료!', 200
    except Exception as e:
        return f'❌ 실패: {e}', 500

# Gunicorn/Render 환경에서도 반드시 실행
try:
    init_db()
    print("✅ DB 초기화 성공!")
except Exception as e:
    print(f"❌ DB init error: {e}")

try:
    start_scheduler()
except Exception as e:
    print(f"❌ 스케줄러 기동 실패: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
