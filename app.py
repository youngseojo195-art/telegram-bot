import os, re, json, random, telebot, psycopg2, requests, urllib.parse, pytz, uuid, threading
from telebot import types
from datetime import datetime, timedelta, date
from flask import Flask, request, send_from_directory, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

BOT_TOKEN = '8046489365:AAHAFBz4Ca07KcjqI0EJl76aIAu-rlVHw-4'
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

KST = pytz.timezone('Asia/Seoul')
UTC = pytz.utc

ADMIN_IDS = [8698678650, 8236798970, 8621088096, 7319936275]

BASEBALL_GIF_FILE_ID = "CgACAgUAAxkBAAMzagl3svn3G8Jr7JDeNhdXbodfQnIAAi8dAAJux0hUOyDPUXIJtRs7BA"
NAEJEON_GIF_FILE_ID  = "CgACAgUAAxkBAAOGag0cXgdCIn_PggmqSmC0GM0GnC4AAkofAAKWbGhUMjetimSM_S47BA"
AFFILIATE_GIF_URL    = "CgACAgUAAxkBAAM4agmS7OD4fz1bxh5zNQPn8VNCpysAAmYdAAJux0hUYXAsQb02yzs7BA"

WEBAPP_BASE_URL = os.environ.get('WEBAPP_URL', 'https://telegram-bot-14vg.onrender.com')
VOTE_START = "18:00"
VOTE_END   = "18:30"

# ── 채팅 포인트 마일스톤 ──
CHAT_MILESTONES = {100: 500, 300: 1000, 500: 2000, 1000: 5000}

# ── 레벨 시스템 ──
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

# ── 데일리 미션 정의 ──
DAILY_MISSIONS = [
    {'id':'play3',  'desc':'오늘 3게임 참여',    'target':3,   'reward':500},
    {'id':'bet1000','desc':'1,000P 이상 베팅',   'target':1000,'reward':300},
    {'id':'win1',   'desc':'1번 당첨',           'target':1,   'reward':700},
]

def send_baseball_gif(chat_id):
    try: bot.send_animation(chat_id=chat_id, animation=BASEBALL_GIF_FILE_ID)
    except: pass

def send_naejeon_gif(chat_id):
    try: bot.send_animation(chat_id=chat_id, animation=NAEJEON_GIF_FILE_ID)
    except: pass

def send_affiliate_gif(chat_id):
    try: bot.send_animation(chat_id=chat_id, animation=AFFILIATE_GIF_URL)
    except: pass

AFFILIATE_TEXT = """🎰 <b>카지노</b>
──────────────────
<b>[평생]</b> · <a href="https://t.me/gamte59/31">렛츠뱃</a>
<b>[평생]</b> · <a href="https://t.me/gamte59/28">예스뱃</a>
<b>[평생]</b> · <a href="https://t.me/gamte59/96">스피드벳</a>"""

KBO_TEAMS = ['KT','삼성','LG','SSG','KIA','한화','두산','NC','롯데','키움']
KBO_TEAMS_DISPLAY = {
    'KT':'🔴 KT','삼성':'🔵 삼성','LG':'🔴 LG','SSG':'🟡 SSG','KIA':'🔴 KIA',
    '한화':'🟠 한화','두산':'🔵 두산','NC':'🔵 NC','롯데':'🔴 롯데','키움':'🟣 키움',
}

# ─────────────────────────────────────────────────────────
# DB
# ─────────────────────────────────────────────────────────
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
    except: return None

def clean_name(name):
    if not name: return ''
    return (name.strip()
            .replace('\u3164','').replace('\u200b','')
            .replace('\u200c','').replace('\u200d','')
            .replace('\ufeff','').strip())

def init_db():
    db = get_db(); c = db.cursor()
    try:
        # ── 기존 테이블 ──
        c.execute("""CREATE TABLE IF NOT EXISTS chat_logs (
            id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL,
            username VARCHAR(255), first_name VARCHAR(255),
            group_id BIGINT NOT NULL, message_date TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT NOW())""")
        c.execute("""CREATE TABLE IF NOT EXISTS points (
            id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL,
            group_id BIGINT NOT NULL, first_name VARCHAR(255),
            username VARCHAR(255), point INTEGER DEFAULT 0,
            last_attendance DATE, total_bet BIGINT DEFAULT 0,
            UNIQUE(user_id, group_id))""")
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
            id SERIAL PRIMARY KEY, room_id VARCHAR(50) NOT NULL UNIQUE,
            group_id BIGINT NOT NULL, game_type VARCHAR(10) NOT NULL,
            slots JSONB NOT NULL DEFAULT '{}', status VARCHAR(20) DEFAULT 'open',
            extra_text TEXT DEFAULT '', pos_a JSONB DEFAULT '[]',
            pos_b JSONB DEFAULT '[]', started BOOLEAN DEFAULT FALSE,
            fund_type VARCHAR(10) DEFAULT '', fund_amount TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT NOW())""")
        c.execute("""CREATE TABLE IF NOT EXISTS naejeon_events (
            room_id VARCHAR(50) PRIMARY KEY, end_time TIMESTAMP NOT NULL,
            winner_count INTEGER NOT NULL, reward_text TEXT NOT NULL,
            is_active BOOLEAN DEFAULT FALSE)""")
        c.execute("""CREATE TABLE IF NOT EXISTS vote_rooms (
            room_id VARCHAR(50) PRIMARY KEY, group_id BIGINT NOT NULL,
            admin_id BIGINT NOT NULL, content TEXT DEFAULT '',
            mins INTEGER, winners INTEGER DEFAULT 1,
            anim_style VARCHAR(20) DEFAULT 'slot',
            started BOOLEAN DEFAULT FALSE, ended BOOLEAN DEFAULT FALSE,
            end_time TIMESTAMP, created_at TIMESTAMP DEFAULT NOW())""")
        c.execute("""CREATE TABLE IF NOT EXISTS vote_participants (
            id SERIAL PRIMARY KEY, room_id VARCHAR(50) NOT NULL,
            user_id BIGINT NOT NULL, name VARCHAR(255),
            joined_at TIMESTAMP DEFAULT NOW(), UNIQUE(room_id, user_id))""")

        # ── 카지노 테이블 ──
        casino_ddl = [
            """CREATE TABLE IF NOT EXISTS casino_games (
                id SERIAL PRIMARY KEY, game_id VARCHAR(30) NOT NULL,
                group_id BIGINT NOT NULL, status VARCHAR(20) DEFAULT 'open',
                result VARCHAR(50), settings JSONB DEFAULT '{}',
                started_at TIMESTAMP DEFAULT NOW(),
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
            # 새 테이블
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
        ]
        for ddl in casino_ddl:
            try: c.execute(ddl); db.commit()
            except: db.rollback()

        # ── 컬럼 추가 (기존 테이블) ──
        alters = [
            ("points","total_bet","BIGINT DEFAULT 0"),
            ("points","level","VARCHAR(20) DEFAULT '브론즈'"),
            ("casino_games","started_at","TIMESTAMP DEFAULT NOW()"),
        ]
        for tbl, col, typ in alters:
            try:
                c.execute(f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS {col} {typ}")
                db.commit()
            except: db.rollback()

        db.commit()
    finally:
        c.close(); db.close()

# ─────────────────────────────────────────────────────────
# 포인트 유틸
# ─────────────────────────────────────────────────────────
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
        c.execute("""INSERT INTO points (user_id,group_id,first_name,username,point)
            VALUES (%s,%s,%s,%s,%s) ON CONFLICT(user_id,group_id)
            DO UPDATE SET point=points.point+%s, first_name=%s, username=%s""",
            (user_id,group_id,first_name,username,amount,amount,first_name,username))
        db.commit()
    finally: c.close(); db.close()

def add_point_log(group_id, user_id, user_name, amount, reason, admin_id=None):
    db = get_db(); c = db.cursor()
    try:
        c.execute("INSERT INTO point_logs(group_id,user_id,user_name,amount,reason,admin_id) VALUES(%s,%s,%s,%s,%s,%s)",
                  (group_id,user_id,user_name,amount,reason,admin_id))
        db.commit()
    finally: c.close(); db.close()

# ─────────────────────────────────────────────────────────
# 채팅 마일스톤 체크
# ─────────────────────────────────────────────────────────
def check_chat_milestone(user_id, group_id, first_name, username):
    """오늘 채팅 수 확인 후 마일스톤 포인트 지급"""
    db = get_db(); c = db.cursor()
    try:
        today = datetime.now(KST).date()
        c.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND DATE(message_date)=%s",
                  (user_id, group_id, today))
        cnt = c.fetchone()[0]

        for milestone, reward in CHAT_MILESTONES.items():
            if cnt >= milestone:
                # 이미 지급했는지 확인
                c.execute("SELECT 1 FROM chat_milestone_logs WHERE user_id=%s AND group_id=%s AND milestone=%s AND rewarded_date=%s",
                          (user_id, group_id, milestone, today))
                if not c.fetchone():
                    # 지급
                    c.execute("INSERT INTO chat_milestone_logs(user_id,group_id,milestone,rewarded_date) VALUES(%s,%s,%s,%s)",
                              (user_id, group_id, milestone, today))
                    c.execute("""INSERT INTO points(user_id,group_id,first_name,username,point)
                        VALUES(%s,%s,%s,%s,%s) ON CONFLICT(user_id,group_id)
                        DO UPDATE SET point=points.point+%s""",
                        (user_id,group_id,first_name,username,reward,reward))
                    c.execute("INSERT INTO point_logs(group_id,user_id,user_name,amount,reason) VALUES(%s,%s,%s,%s,%s)",
                              (group_id,user_id,first_name,reward,f'채팅 {milestone}회 달성'))
                    db.commit()
                    try:
                        bot.send_message(group_id,
                            f"🎉 <b>{first_name}</b>님 오늘 채팅 <b>{milestone}회</b> 달성!\n"
                            f"💰 보너스 <b>{reward:,}P</b> 지급!", parse_mode='HTML')
                    except: pass
        db.commit()
    except Exception as e:
        print(f"chat_milestone error: {e}")
        db.rollback()
    finally: c.close(); db.close()

# ─────────────────────────────────────────────────────────
# 데일리 미션
# ─────────────────────────────────────────────────────────
def update_mission(user_id, group_id, mission_id, increment=1):
    db = get_db(); c = db.cursor()
    try:
        today = datetime.now(KST).date()
        mission = next((m for m in DAILY_MISSIONS if m['id']==mission_id), None)
        if not mission: return
        c.execute("""INSERT INTO daily_missions(user_id,group_id,mission_id,mission_date,progress)
            VALUES(%s,%s,%s,%s,%s) ON CONFLICT(user_id,group_id,mission_id,mission_date)
            DO UPDATE SET progress=LEAST(daily_missions.progress+%s, %s)
            WHERE NOT daily_missions.completed""",
            (user_id,group_id,mission_id,today,increment,increment,mission['target']))
        c.execute("SELECT progress, completed FROM daily_missions WHERE user_id=%s AND group_id=%s AND mission_id=%s AND mission_date=%s",
                  (user_id,group_id,mission_id,today))
        row = c.fetchone()
        if row and not row[1] and row[0] >= mission['target']:
            c.execute("UPDATE daily_missions SET completed=TRUE WHERE user_id=%s AND group_id=%s AND mission_id=%s AND mission_date=%s",
                      (user_id,group_id,mission_id,today))
            c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",
                      (mission['reward'],user_id,group_id))
            c.execute("INSERT INTO point_logs(group_id,user_id,user_name,amount,reason) SELECT %s,%s,first_name,%s,%s FROM points WHERE user_id=%s AND group_id=%s",
                      (group_id,user_id,mission['reward'],f"데일리 미션: {mission['desc']}",user_id,group_id))
        db.commit()
    except Exception as e: print(f"mission error: {e}"); db.rollback()
    finally: c.close(); db.close()

# ─────────────────────────────────────────────────────────
# 쿨다운 / 일일한도 / 이상감지
# ─────────────────────────────────────────────────────────
COOLDOWN_SECS = 30
DAILY_BET_LIMIT = 500000
SUSPICIOUS_THRESHOLD = 100000   # 1회 10만P 이상 자동 감지

def check_cooldown(user_id, group_id, game_id):
    """True = 쿨다운 중"""
    db = get_db(); c = db.cursor()
    try:
        c.execute("SELECT last_bet FROM bet_cooldowns WHERE user_id=%s AND group_id=%s AND game_id=%s",
                  (user_id,group_id,game_id))
        row = c.fetchone()
        if not row: return False
        diff = (datetime.now(UTC) - (row[0].replace(tzinfo=UTC) if row[0].tzinfo is None else row[0])).total_seconds()
        return diff < COOLDOWN_SECS
    finally: c.close(); db.close()

def set_cooldown(user_id, group_id, game_id):
    db = get_db(); c = db.cursor()
    try:
        c.execute("""INSERT INTO bet_cooldowns(user_id,group_id,game_id,last_bet) VALUES(%s,%s,%s,NOW())
            ON CONFLICT(user_id,group_id,game_id) DO UPDATE SET last_bet=NOW()""",
            (user_id,group_id,game_id))
        db.commit()
    finally: c.close(); db.close()

def check_daily_limit(user_id, group_id, amount):
    """True = 한도 초과"""
    db = get_db(); c = db.cursor()
    try:
        today = datetime.now(KST).date()
        c.execute("SELECT total FROM daily_bet_totals WHERE user_id=%s AND group_id=%s AND bet_date=%s",
                  (user_id,group_id,today))
        row = c.fetchone()
        current = row[0] if row else 0
        return (current + amount) > DAILY_BET_LIMIT
    finally: c.close(); db.close()

def add_daily_bet(user_id, group_id, amount):
    db = get_db(); c = db.cursor()
    try:
        today = datetime.now(KST).date()
        c.execute("""INSERT INTO daily_bet_totals(user_id,group_id,bet_date,total) VALUES(%s,%s,%s,%s)
            ON CONFLICT(user_id,group_id,bet_date) DO UPDATE SET total=daily_bet_totals.total+%s""",
            (user_id,group_id,today,amount,amount))
        db.commit()
    finally: c.close(); db.close()

def check_suspicious(group_id, user_id, amount, game_id):
    if amount >= SUSPICIOUS_THRESHOLD:
        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(admin_id,
                    f"⚠️ <b>이상 베팅 감지</b>\n게임: {game_id}\n유저: {user_id}\n금액: {amount:,}P",
                    parse_mode='HTML')
            except: pass

# ─────────────────────────────────────────────────────────
# 카지노 기본 설정
# ─────────────────────────────────────────────────────────
DEFAULT_CASINO_SETTINGS = {
    "race": {
        "rabbit_win_rate":60,"min_bet":10,"max_bet":10000,
        "house_edge":5,"enabled":True,"force_result":None,
        "rabbit_odds":1.8,"turtle_odds":2.5,"auto_round":True,"round_minutes":3
    },
    "baccarat": {
        "player_win_rate":45,"banker_win_rate":46,
        "min_bet":10,"max_bet":10000,"house_edge":5,
        "enabled":True,"force_result":None
    },
    "horse": {
        "horses":[
            {"id":1,"name":"번개","emoji":"⚡","win_rate":30,"base_odds":2.5},
            {"id":2,"name":"폭풍","emoji":"🌪️","win_rate":20,"base_odds":3.5},
            {"id":3,"name":"황금","emoji":"⭐","win_rate":15,"base_odds":5.0},
            {"id":4,"name":"다이아","emoji":"💎","win_rate":10,"base_odds":7.0},
            {"id":5,"name":"불꽃","emoji":"🔥","win_rate":25,"base_odds":3.0},
        ],
        "min_bet":10,"max_bet":10000,"house_edge":5,
        "enabled":True,"force_result":None,"auto_round":True,"round_minutes":3
    },
    "bigwheel":{
        "segments":[
            {"label":"2배","multiplier":2,"color":"#2266cc","probability":30},
            {"label":"3배","multiplier":3,"color":"#22aa66","probability":20},
            {"label":"5배","multiplier":5,"color":"#cc8800","probability":15},
            {"label":"10배","multiplier":10,"color":"#aa2222","probability":10},
            {"label":"20배","multiplier":20,"color":"#882288","probability":5},
            {"label":"꽝","multiplier":0,"color":"#222233","probability":20},
        ],
        "min_bet":10,"max_bet":10000,"house_edge":5,"enabled":True
    }
}

def get_casino_settings(group_id, game_id):
    db = get_db(); c = db.cursor()
    try:
        c.execute("SELECT settings FROM casino_settings WHERE group_id=%s AND game_id=%s",(group_id,game_id))
        row = c.fetchone()
        base = DEFAULT_CASINO_SETTINGS.get(game_id,{}).copy()
        if row and row[0]: base.update(row[0])
        return base
    finally: c.close(); db.close()

def save_casino_settings(group_id, game_id, settings):
    db = get_db(); c = db.cursor()
    try:
        c.execute("""INSERT INTO casino_settings(group_id,game_id,settings,updated_at)
            VALUES(%s,%s,%s,NOW()) ON CONFLICT(group_id,game_id)
            DO UPDATE SET settings=%s,updated_at=NOW()""",
            (group_id,game_id,json.dumps(settings),json.dumps(settings)))
        db.commit()
    finally: c.close(); db.close()

def is_casino_blacklisted(group_id, user_id):
    db = get_db(); c = db.cursor()
    try:
        c.execute("SELECT 1 FROM casino_blacklist WHERE group_id=%s AND user_id=%s",(group_id,user_id))
        return c.fetchone() is not None
    finally: c.close(); db.close()

# ─────────────────────────────────────────────────────────
# 자동 라운드 스케줄러
# ─────────────────────────────────────────────────────────
def auto_race_round():
    """모든 그룹의 경주 자동 라운드 처리"""
    db = get_db(); c = db.cursor()
    try:
        # auto_round 설정된 그룹 조회
        c.execute("SELECT DISTINCT group_id FROM auto_round_config WHERE race_auto=TRUE")
        groups = [r[0] for r in c.fetchall()]
        # 설정 없으면 기존 활성 그룹 대상
        if not groups:
            c.execute("SELECT DISTINCT group_id FROM casino_games WHERE game_id='race' AND created_at > NOW() - INTERVAL '7 days'")
            groups = [r[0] for r in c.fetchall()]

        for group_id in groups:
            try:
                settings = get_casino_settings(group_id, 'race')
                if not settings.get('auto_round', True): continue

                # 현재 진행중인 라운드 확인
                c.execute("SELECT id,status,started_at FROM casino_games WHERE group_id=%s AND game_id='race' AND status NOT IN ('closed','cancelled') ORDER BY id DESC LIMIT 1",
                          (group_id,))
                row = c.fetchone()

                if not row:
                    # 새 라운드 오픈
                    _open_race_round(group_id, settings, c, db)
                else:
                    round_id, status, started_at = row
                    if started_at:
                        started = started_at.replace(tzinfo=UTC) if started_at.tzinfo is None else started_at.astimezone(UTC)
                        elapsed = (datetime.now(UTC) - started).total_seconds()
                        mins = settings.get('round_minutes', 3)

                        if status == 'betting' and elapsed >= mins * 60:
                            # 베팅 마감 → 결과 처리
                            _process_race_result(group_id, round_id, settings, c, db)
                            # 즉시 새 라운드 오픈
                            _open_race_round(group_id, settings, c, db)
            except Exception as e:
                print(f"auto_race error group {group_id}: {e}")
                db.rollback()
    except Exception as e:
        print(f"auto_race_round error: {e}")
    finally:
        try: c.close(); db.close()
        except: pass

def auto_horse_round():
    """경마 자동 라운드"""
    db = get_db(); c = db.cursor()
    try:
        c.execute("SELECT DISTINCT group_id FROM auto_round_config WHERE horse_auto=TRUE")
        groups = [r[0] for r in c.fetchall()]
        if not groups:
            c.execute("SELECT DISTINCT group_id FROM casino_games WHERE game_id='horse' AND created_at > NOW() - INTERVAL '7 days'")
            groups = [r[0] for r in c.fetchall()]

        for group_id in groups:
            try:
                settings = get_casino_settings(group_id, 'horse')
                if not settings.get('auto_round', True): continue

                c.execute("SELECT id,status,started_at FROM casino_games WHERE group_id=%s AND game_id='horse' AND status NOT IN ('closed','cancelled') ORDER BY id DESC LIMIT 1",
                          (group_id,))
                row = c.fetchone()

                if not row:
                    _open_horse_round(group_id, settings, c, db)
                else:
                    round_id, status, started_at = row
                    if started_at:
                        started = started_at.replace(tzinfo=UTC) if started_at.tzinfo is None else started_at.astimezone(UTC)
                        elapsed = (datetime.now(UTC) - started).total_seconds()
                        mins = settings.get('round_minutes', 3)
                        if status == 'betting' and elapsed >= mins * 60:
                            _process_horse_result(group_id, round_id, settings, c, db)
                            _open_horse_round(group_id, settings, c, db)
            except Exception as e:
                print(f"auto_horse error group {group_id}: {e}")
                db.rollback()
    except Exception as e:
        print(f"auto_horse_round error: {e}")
    finally:
        try: c.close(); db.close()
        except: pass

def _open_race_round(group_id, settings, c, db):
    c.execute("INSERT INTO casino_games(game_id,group_id,status,settings,started_at) VALUES('race',%s,'betting',%s,NOW()) RETURNING id",
              (group_id, json.dumps(settings)))
    db.commit()

def _open_horse_round(group_id, settings, c, db):
    c.execute("INSERT INTO casino_games(game_id,group_id,status,settings,started_at) VALUES('horse',%s,'betting',%s,NOW()) RETURNING id",
              (group_id, json.dumps(settings)))
    db.commit()

def _process_race_result(group_id, round_id, settings, c, db):
    force = settings.get('force_result')
    win_rate = settings.get('rabbit_win_rate', 60)
    house_edge = settings.get('house_edge', 5)
    winner = force if force in ['rabbit','turtle'] else ('rabbit' if random.randint(1,100)<=win_rate else 'turtle')

    c.execute("SELECT bet_on,SUM(amount) FROM casino_bets WHERE round_id=%s GROUP BY bet_on",(round_id,))
    pools = {r[0]:r[1] for r in c.fetchall()}
    total_pool = sum(pools.values())
    winner_pool = pools.get(winner,0)
    odds = max(1.1,(total_pool*(1-house_edge/100))/winner_pool) if winner_pool>0 else 2.0

    c.execute("SELECT id,user_id,user_name,amount FROM casino_bets WHERE round_id=%s AND bet_on=%s",(round_id,winner))
    winners = c.fetchall()
    for bet in winners:
        payout = int(bet[3]*odds)
        c.execute("UPDATE casino_bets SET won=TRUE,payout=%s WHERE id=%s",(payout,bet[0]))
        c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(payout,bet[1],group_id))
        c.execute("INSERT INTO point_logs(group_id,user_id,user_name,amount,reason) VALUES(%s,%s,%s,%s,%s)",
                  (group_id,bet[1],bet[2],payout,f'경주 당첨 ({winner}) x{odds:.2f}'))
        update_mission(bet[1], group_id, 'win1')

    c.execute("UPDATE casino_bets SET won=FALSE,payout=0 WHERE round_id=%s AND bet_on!=%s",(round_id,winner))
    c.execute("UPDATE casino_games SET status='closed',result=%s,ended_at=NOW() WHERE id=%s",(winner,round_id))
    db.commit()

def _process_horse_result(group_id, round_id, settings, c, db):
    horses = settings.get('horses', DEFAULT_CASINO_SETTINGS['horse']['horses'])
    force = settings.get('force_result')
    if force:
        winner_h = next((h for h in horses if str(h['id'])==str(force) or h['name']==force), None)
    else:
        total_rate = sum(h.get('win_rate',20) for h in horses)
        r = random.randint(1,total_rate); acc = 0; winner_h = horses[-1]
        for h in horses:
            acc += h.get('win_rate',20)
            if r<=acc: winner_h=h; break

    winner_id = str(winner_h['id'])
    odds = winner_h.get('base_odds',2.5)
    c.execute("SELECT id,user_id,user_name,amount FROM casino_bets WHERE round_id=%s",(round_id,))
    bets = c.fetchall()
    for bet in bets:
        if str(bet[2])==winner_id or str(bet[2])==winner_h.get('name',''):
            payout = int(bet[3]*odds)
            c.execute("UPDATE casino_bets SET won=TRUE,payout=%s WHERE id=%s",(payout,bet[0]))
            c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(payout,bet[1],group_id))
            c.execute("INSERT INTO point_logs(group_id,user_id,user_name,amount,reason) VALUES(%s,%s,%s,%s,%s)",
                      (group_id,bet[1],bet[2],payout,f'경마 당첨 ({winner_h["name"]}) x{odds}'))
            update_mission(bet[1], group_id, 'win1')
        else:
            c.execute("UPDATE casino_bets SET won=FALSE,payout=0 WHERE id=%s",(bet[0],))
    c.execute("UPDATE casino_games SET status='closed',result=%s,ended_at=NOW() WHERE id=%s",(winner_id,round_id))
    db.commit()

# ─────────────────────────────────────────────────────────
# KBO 유틸
# ─────────────────────────────────────────────────────────
def build_team_keyboard(selected):
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for team in KBO_TEAMS:
        label = f"✅ {team}" if team in selected else KBO_TEAMS_DISPLAY.get(team,team)
        buttons.append(types.InlineKeyboardButton(text=label,callback_data=f"kbo_toggle:{team}"))
    markup.add(*buttons)
    count = len(selected)
    if count==5:
        markup.add(types.InlineKeyboardButton("🔄 초기화",callback_data="kbo_reset"),
                   types.InlineKeyboardButton(f"✅ 제출하기 ({count}/5)",callback_data="kbo_submit"))
    else:
        markup.add(types.InlineKeyboardButton("🔄 초기화",callback_data="kbo_reset"),
                   types.InlineKeyboardButton(f"⬜ 선택 중 ({count}/5)",callback_data="kbo_noop"))
    return markup

def build_vote_message(selected):
    count = len(selected)
    if count==0: status="팀을 선택해주세요"
    elif count<5: status=f"{count}개 선택 — {5-count}개 더"
    else: status="5개 완료! 제출하기를 눌러주세요 ✅"
    lines=["⚾ KBO 승 예측",f"📊 {status}",""]
    for t in selected: lines.append(f"   • {KBO_TEAMS_DISPLAY.get(t,t)}")
    return "\n".join(lines)

def get_pending_with_group(user_id):
    db=get_db();c=db.cursor()
    try:
        c.execute("SELECT group_id,selected,message_id FROM kbo_pending WHERE user_id=%s LIMIT 1",(user_id,))
        row=c.fetchone()
        if row: return (row[0],[t for t in row[1].split(',') if t]),row[2]
        return None,None
    finally: c.close();db.close()

def set_pending(user_id,group_id,selected,message_id=None):
    db=get_db();c=db.cursor()
    try:
        s=','.join(selected)
        c.execute("""INSERT INTO kbo_pending(user_id,group_id,selected,message_id) VALUES(%s,%s,%s,%s)
            ON CONFLICT(user_id,group_id) DO UPDATE SET selected=%s,message_id=%s""",
            (user_id,group_id,s,message_id,s,message_id))
        db.commit()
    finally: c.close();db.close()

def clear_pending(user_id,group_id):
    db=get_db();c=db.cursor()
    try:
        c.execute("DELETE FROM kbo_pending WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        db.commit()
    finally: c.close();db.close()

def is_vote_time(now_kst):
    if now_kst.weekday() not in [1,2,3,4]: return False
    cur=now_kst.time()
    return (datetime.strptime(VOTE_START,"%H:%M").time()<=cur<=datetime.strptime(VOTE_END,"%H:%M").time())

def get_usdt_rate():
    try:
        r=requests.get('https://api.upbit.com/v1/ticker?markets=KRW-USDT',timeout=5)
        if r.status_code==200: return float(r.json()[0]['trade_price'])
    except: pass
    return None

def save_message(user_id,username,first_name,group_id):
    db=get_db();c=db.cursor()
    try:
        c.execute("INSERT INTO chat_logs(user_id,username,first_name,group_id,message_date) VALUES(%s,%s,%s,%s,%s)",
                  (user_id,username,first_name,group_id,datetime.now()))
        db.commit()
    finally: c.close();db.close()

# ─────────────────────────────────────────────────────────
# 콜백 핸들러
# ─────────────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda call: call.data.startswith('nj_open:'))
def handle_nj_open(call):
    try:
        user_id=call.from_user.id; group_id=call.message.chat.id
        if user_id not in ADMIN_IDS:
            bot.answer_callback_query(call.id,"⚠️ 관리자만 사용할 수 있어요!",show_alert=True); return
        parts=call.data.split(':',2); game_type=parts[1]; extra_text=parts[2] if len(parts)>2 else ''
        game_names={'sa5':'서든어택 5v5','sa6':'서든어택 6v6'}
        display_name=game_names.get(game_type,'서든어택')
        db=get_db();c=db.cursor()
        try:
            c.execute("SELECT room_id FROM naejeon_rooms WHERE group_id=%s AND game_type=%s AND status='open'",(group_id,game_type))
            if c.fetchone(): bot.answer_callback_query(call.id,"⚠️ 이미 진행 중인 내전이 있어요!",show_alert=True); return
            room_id=str(uuid.uuid4())[:8]
            c.execute("INSERT INTO naejeon_rooms(room_id,group_id,game_type,slots,extra_text) VALUES(%s,%s,%s,%s,%s)",
                      (room_id,group_id,game_type,'{}',extra_text))
            db.commit()
        finally: c.close();db.close()
        param=f"{user_id}_{group_id}_{game_type}_{room_id}"
        nj_url=f"{WEBAPP_BASE_URL}/naejeon?start={param}"
        msg=f"⚔️ {display_name} 내전 모집!"
        if extra_text: msg+=f"\n{extra_text}"
        msg+=f"\n\n아래 버튼을 눌러 참여하세요!"
        send_naejeon_gif(group_id)
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚔️ 내전 참여하기",url=nj_url))
        bot.edit_message_text(msg,chat_id=group_id,message_id=call.message.message_id,reply_markup=markup)
        bot.answer_callback_query(call.id,f"✅ {display_name} 내전 시작!")
    except Exception as e:
        import traceback; print(f"nj_open error: {e}\n{traceback.format_exc()}")
        bot.answer_callback_query(call.id,"오류가 발생했어요.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('kbo_'))
def handle_kbo_callback(call):
    try:
        user_id=call.from_user.id; first_name=call.from_user.first_name or '사용자'
        username=call.from_user.username or ''; now_kst=datetime.now(KST)
        today=now_kst.date(); action=call.data
        if not is_vote_time(now_kst):
            bot.answer_callback_query(call.id,f"⏰ 화~금 {VOTE_START}~{VOTE_END} 사이에만 가능해요!",show_alert=True); return
        selected_data,msg_id=get_pending_with_group(user_id)
        if selected_data is None:
            bot.answer_callback_query(call.id,"⚠️ 세션 만료. /승 을 다시 입력해주세요.",show_alert=True); return
        group_id=selected_data[0]; selected=selected_data[1]
        db=get_db();c=db.cursor()
        try:
            c.execute("SELECT teams FROM kbo_votes WHERE user_id=%s AND group_id=%s AND vote_date=%s",(user_id,group_id,today))
            already=c.fetchone()
        finally: c.close();db.close()
        if action=="kbo_noop":
            bot.answer_callback_query(call.id,"이미 제출하셨어요!" if already else f"5개를 선택해야 해요! (현재 {len(selected)}개)"); return
        elif action=="kbo_reset":
            selected=[];set_pending(user_id,group_id,selected,call.message.message_id)
            bot.edit_message_text(chat_id=user_id,message_id=call.message.message_id,
                text=build_vote_message(selected),reply_markup=build_team_keyboard(selected))
            bot.answer_callback_query(call.id,"초기화!")
        elif action.startswith("kbo_toggle:"):
            team=action.split(":")[1]
            if team in selected: selected.remove(team); bot.answer_callback_query(call.id,f"{team} 취소")
            else:
                if len(selected)>=5: bot.answer_callback_query(call.id,"5개 선택 완료! 초기화 후 재선택",show_alert=True); return
                selected.append(team); bot.answer_callback_query(call.id,f"{team} 선택! ({len(selected)}/5)")
            set_pending(user_id,group_id,selected,call.message.message_id)
            bot.edit_message_text(chat_id=user_id,message_id=call.message.message_id,
                text=build_vote_message(selected),reply_markup=build_team_keyboard(selected))
        elif action=="kbo_submit":
            if len(selected)!=5: bot.answer_callback_query(call.id,"5개를 선택해야 해요!",show_alert=True); return
            teams_str=','.join(selected)
            db=get_db();c=db.cursor()
            try:
                if already:
                    c.execute("UPDATE kbo_votes SET teams=%s,first_name=%s,username=%s WHERE user_id=%s AND group_id=%s AND vote_date=%s",
                        (teams_str,first_name,username,user_id,group_id,today))
                    action_label="수정 완료"
                else:
                    c.execute("INSERT INTO kbo_votes(user_id,group_id,first_name,username,teams,vote_date) VALUES(%s,%s,%s,%s,%s,%s)",
                        (user_id,group_id,first_name,username,teams_str,today))
                    action_label="예측 완료"
                c.execute("SELECT COUNT(*) FROM kbo_votes WHERE group_id=%s AND vote_date=%s",(group_id,today))
                total=c.fetchone()[0]; db.commit()
            finally: c.close();db.close()
            clear_pending(user_id,group_id)
            team_display="\n".join([f"   {i+1}. {KBO_TEAMS_DISPLAY.get(t,t)}" for i,t in enumerate(selected)])
            bot.edit_message_text(chat_id=user_id,message_id=call.message.message_id,
                text=f"⚾ KBO 승 {action_label}\n   👤 {first_name}님\n\n{team_display}\n\n   👥 오늘 참여자: {total}명",
                reply_markup=None)
            bot.answer_callback_query(call.id,f"✅ {action_label}!")
    except Exception as e:
        import traceback; print(f"kbo callback error: {e}\n{traceback.format_exc()}")
        bot.answer_callback_query(call.id,"오류가 발생했어요.")

# ─────────────────────────────────────────────────────────
# 메시지 핸들러
# ─────────────────────────────────────────────────────────
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    try:
        text=message.text or ''; user_id=message.from_user.id
        group_id=message.chat.id; first_name=message.from_user.first_name or '사용자'
        username=message.from_user.username or ''; now_kst=datetime.now(KST); today=now_kst.date()

        if '/test' in text:
            bot.reply_to(message,f"✅ 봇 작동 중!\nuser_id: {user_id}")

        elif '/포인트복구' in text:
            if user_id not in ADMIN_IDS: bot.reply_to(message,"⚠️ 관리자 전용"); return
            db=get_db();c=db.cursor()
            try:
                c.execute("SELECT user_id,first_name,username,point FROM points WHERE group_id=%s ORDER BY point DESC",(group_id,))
                rows=c.fetchall()
            finally: c.close();db.close()
            if not rows: bot.reply_to(message,"포인트 기록 없음"); return
            result="╔══ 포인트 현황 ══╗\n"
            for r in rows: result+=f"   • {r[1] or r[2] or '익명'} (id:{r[0]}): {r[3]:,}P\n"
            bot.reply_to(message,result+"╚══════════════════╝")

        elif '/포인트설정' in text:
            if user_id not in ADMIN_IDS: bot.reply_to(message,"⚠️ 관리자 전용"); return
            parts=text.split()
            if len(parts)<3 or not parts[2].isdigit(): bot.reply_to(message,"사용법: /포인트설정 [이름] [포인트]"); return
            target_name=parts[1]; new_pt=int(parts[2])
            db=get_db();c=db.cursor()
            try:
                c.execute("UPDATE points SET point=%s WHERE first_name=%s AND group_id=%s",(new_pt,target_name,group_id))
                affected=c.rowcount; db.commit()
            finally: c.close();db.close()
            bot.reply_to(message,f"✅ {target_name}님 → {new_pt:,}P" if affected>0 else f"⚠️ {target_name} 찾을 수 없음")

        elif '/전체포인트초기화' in text:
            if user_id not in ADMIN_IDS: bot.reply_to(message,"⚠️ 관리자 전용"); return
            if '확인' not in text: bot.reply_to(message,"⚠️ /전체포인트초기화 확인"); return
            db=get_db();c=db.cursor()
            try:
                c.execute("UPDATE points SET point=0 WHERE group_id=%s",(group_id,))
                affected=c.rowcount; db.commit()
            finally: c.close();db.close()
            bot.reply_to(message,f"✅ {affected}명 전체 초기화 완료")

        elif '/getfileid' in text:
            if message.reply_to_message:
                msg=message.reply_to_message; file_id=None
                if msg.animation: file_id=msg.animation.file_id
                elif msg.video: file_id=msg.video.file_id
                elif msg.document: file_id=msg.document.file_id
                if file_id: bot.reply_to(message,f"📋 file_id:\n<code>{file_id}</code>",parse_mode='HTML')
                else: bot.reply_to(message,"⚠️ GIF/영상 메시지에 답장 후 사용")
            else: bot.reply_to(message,"GIF/영상에 답장으로 /getfileid 입력")

        elif '/노래' in text:
            query=text.replace('/노래','').strip()
            if not query: bot.reply_to(message,"🎵 검색어 입력"); return
            bot.reply_to(message,f"🎵 {query}\nhttps://www.youtube.com/results?search_query={urllib.parse.quote(query)}")

        elif '/제휴' in text:
            send_affiliate_gif(group_id)
            bot.reply_to(message,AFFILIATE_TEXT,parse_mode='HTML',disable_web_page_preview=True)

        elif re.search(r'(\d+(\.\d+)?)\s*테더',text):
            match=re.search(r'(\d+(\.\d+)?)\s*테더',text); amount=float(match.group(1))
            rate=get_usdt_rate()
            if rate is None: bot.reply_to(message,"⚠️ 환율 정보 오류"); return
            bot.reply_to(message,f"💰 {rate:,.0f}원/USDT\n💵 {amount:,.0f} USDT = {amount*rate:,.0f}원")

        elif '/출석' in text:
            if message.chat.type=='private': return
            # 웹앱에서 처리하도록 URL만 안내
            casino_url=f"{WEBAPP_BASE_URL}/casino?userId={user_id}&groupId={group_id}"
            markup=types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🎰 카지노에서 출석하기",url=casino_url))
            bot.reply_to(message,"📅 카지노 앱에서 출석 체크하세요!",reply_markup=markup)

        elif '/리필' in text:
            if message.chat.type=='private': return
            casino_url=f"{WEBAPP_BASE_URL}/casino?userId={user_id}&groupId={group_id}"
            markup=types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🎰 카지노에서 리필하기",url=casino_url))
            bot.reply_to(message,"💧 카지노 앱에서 리필하세요!",reply_markup=markup)

        elif '/선물' in text:
            if message.chat.type=='private': bot.reply_to(message,"⚠️ 그룹에서만 사용 가능"); return
            if not message.reply_to_message: bot.reply_to(message,"🎁 상대 메시지에 답장 후\n/선물 [포인트]"); return
            parts=text.split()
            if len(parts)<2 or not parts[1].isdigit(): bot.reply_to(message,"🎁 /선물 [포인트]"); return
            amount=int(parts[1])
            if amount<10: bot.reply_to(message,"⚠️ 최소 10P"); return
            target=message.reply_to_message.from_user
            if target.id==user_id: bot.reply_to(message,"⚠️ 자신에게 불가"); return
            if target.is_bot: bot.reply_to(message,"⚠️ 봇에게 불가"); return
            my_point=get_point(user_id,group_id)
            if my_point<amount: bot.reply_to(message,f"💸 포인트 부족 (보유: {my_point}P)"); return
            target_name=target.first_name or '상대방'
            update_point(user_id,group_id,first_name,username,-amount)
            update_point(target.id,group_id,target_name,target.username or '',amount)
            bot.reply_to(message,f"🎁 {first_name} → {target_name}\n💝 {amount:,}P 선물 완료!")

        elif '/포인트랭킹' in text:
            if message.chat.type=='private': return
            db=get_db();c=db.cursor()
            try:
                c.execute("SELECT first_name,username,point FROM points WHERE group_id=%s ORDER BY point DESC LIMIT 5",(group_id,))
                rows=c.fetchall()
            finally: c.close();db.close()
            medals=['🥇','🥈','🥉','4️⃣','5️⃣']
            result="╔══ 💰 포인트 랭킹 ══╗\n"
            for i,r in enumerate(rows):
                result+=f"   {medals[i]} {r[0] or r[1] or '익명':<10} {r[2]:,}P\n"
            bot.reply_to(message,result+"╚══════════════════╝")

        elif '/포인트' in text:
            if message.chat.type=='private': return
            bot.reply_to(message,f"💰 {first_name}님: {get_point(user_id,group_id):,}P")

        elif '/채팅랭킹' in text:
            if message.chat.type=='private': return
            monday=today-timedelta(days=today.weekday()); sunday=monday+timedelta(days=6)
            db=get_db();c=db.cursor()
            try:
                c.execute("SELECT first_name,username,COUNT(*) as cnt FROM chat_logs WHERE group_id=%s AND message_date>=%s GROUP BY user_id,first_name,username ORDER BY cnt DESC LIMIT 5",(group_id,monday))
                rows=c.fetchall()
            finally: c.close();db.close()
            medals=['🥇','🥈','🥉','4️⃣','5️⃣']
            result=f"╔══ 주간 채팅 랭킹 ══╗\n   {monday.strftime('%m/%d')}~{sunday.strftime('%m/%d')}\n"
            for i,r in enumerate(rows):
                result+=f"   {medals[i]} {r[0] or r[1] or '익명':<10} {r[2]}개\n"
            bot.reply_to(message,result+"╚══════════════════╝")

        elif '/채팅' in text:
            if message.chat.type=='private': return
            monday=today-timedelta(days=today.weekday())
            db=get_db();c=db.cursor()
            try:
                c.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND DATE(message_date)=%s",(user_id,group_id,today))
                today_count=c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND message_date>=%s",(user_id,group_id,monday))
                week_count=c.fetchone()[0]
            finally: c.close();db.close()
            bot.reply_to(message,f"📊 {first_name}님\n   오늘: {today_count}개\n   이번 주: {week_count}개")

        elif text.strip().startswith('/야구'):
            if message.chat.type=='private': return
            send_baseball_gif(group_id)
            kbo_url=f"{WEBAPP_BASE_URL}/kbo?start={user_id}_{group_id}"
            markup=types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚾ KBO 승 예측",url=kbo_url))
            bot.reply_to(message,f"⚾ KBO 승 예측\n📅 화~금 {VOTE_START}~{VOTE_END}",reply_markup=markup,parse_mode='HTML')

        elif text.strip().startswith('/승') or text.strip().startswith('/수정') or text.strip().startswith('/리스트'):
            if message.chat.type=='private': return
            kbo_url=f"{WEBAPP_BASE_URL}/kbo?start={user_id}_{group_id}"
            markup=types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚾ KBO 예측 참여",url=kbo_url))
            bot.reply_to(message,"⚾ 아래 버튼을 눌러 참여하세요!",reply_markup=markup)

        elif text.strip().startswith('/카지노'):
            if message.chat.type=='private': return
            casino_url=f"{WEBAPP_BASE_URL}/casino?userId={user_id}&groupId={group_id}"
            markup=types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🎰 카지노 입장",url=casino_url))
            # URL만 전달, 내용 없음
            bot.reply_to(message,"🎰",reply_markup=markup)

        elif text.strip().startswith('/카지노관리') or text.strip().startswith('/casino_admin'):
            if user_id not in ADMIN_IDS: bot.reply_to(message,"⚠️ 관리자 전용"); return
            admin_url=f"{WEBAPP_BASE_URL}/casino/admin?adminId={user_id}&groupId={group_id}"
            markup=types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("👑 관리자 페이지",url=admin_url))
            bot.reply_to(message,"👑",reply_markup=markup)

        elif text.strip().startswith('/투표'):
            if message.chat.type=='private': return
            if user_id not in ADMIN_IDS: bot.reply_to(message,"⚠️ 관리자 전용"); return
            room_id=str(uuid.uuid4())[:8]
            db=get_db();c=db.cursor()
            try:
                c.execute("INSERT INTO vote_rooms(room_id,group_id,admin_id) VALUES(%s,%s,%s)",(room_id,group_id,user_id))
                db.commit()
            finally: c.close();db.close()
            param=f"{user_id}|{group_id}|{room_id}"
            vote_url=f"{WEBAPP_BASE_URL}/vote?start={param}"
            markup=types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚙️ 이벤트 설정",url=vote_url))
            bot.reply_to(message,"🎰",reply_markup=markup)

        elif text.strip().startswith('/내전수정'):
            if message.chat.type=='private': return
            if user_id not in ADMIN_IDS: bot.reply_to(message,"⚠️ 관리자 전용"); return
            parts=text.strip().split(); game_arg=parts[1] if len(parts)>1 else ''
            game_map={'롤':'lol','서든':'sa5','lol':'lol','sa':'sa5','sa5':'sa5','sa6':'sa6'}
            game_type=game_map.get(game_arg)
            if not game_type: bot.reply_to(message,"⚔️ /내전수정 롤 or /내전수정 서든"); return
            db=get_db();c=db.cursor()
            try:
                c.execute("SELECT room_id FROM naejeon_rooms WHERE group_id=%s AND game_type=%s ORDER BY created_at DESC LIMIT 1",(group_id,game_type))
                row=c.fetchone()
            finally: c.close();db.close()
            if not row: bot.reply_to(message,"⚠️ 최근 내전 없음"); return
            room_id=row[0]; param=f"{user_id}_{group_id}_{game_type}_{room_id}"
            nj_url=f"{WEBAPP_BASE_URL}/naejeon?start={param}&mode=edit"
            markup=types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🛠 내전 수정",url=nj_url))
            bot.reply_to(message,"👑",reply_markup=markup)

        elif text.strip().startswith('/내전취소'):
            if message.chat.type=='private': return
            if user_id not in ADMIN_IDS: bot.reply_to(message,"⚠️ 관리자 전용"); return
            parts=text.strip().split(); game_arg=parts[1] if len(parts)>1 else ''
            game_map={'롤':'lol','서든':'sa','lol':'lol','sa':'sa','sa5':'sa5','sa6':'sa6'}
            game_type=game_map.get(game_arg)
            if not game_type: bot.reply_to(message,"⚔️ /내전취소 롤 or /내전취소 서든"); return
            db=get_db();c=db.cursor()
            try:
                if game_type=='sa':
                    c.execute("UPDATE naejeon_rooms SET status='cancelled' WHERE group_id=%s AND game_type IN ('sa5','sa6') AND status='open'",(group_id,))
                else:
                    c.execute("UPDATE naejeon_rooms SET status='cancelled' WHERE group_id=%s AND game_type=%s AND status='open'",(group_id,game_type))
                affected=c.rowcount; db.commit()
            finally: c.close();db.close()
            bot.reply_to(message,f"✅ 내전 취소" if affected>0 else "⚠️ 진행 중인 내전 없음")

        elif text.strip().startswith('/내전'):
            if message.chat.type=='private': return
            if user_id not in ADMIN_IDS: bot.reply_to(message,"⚠️ 관리자 전용"); return
            parts=text.strip().split(); game_arg=parts[1] if len(parts)>1 else ''
            if game_arg not in ['롤','서든']:
                bot.reply_to(message,"⚔️ /내전 롤 or /내전 서든"); return
            extra_text=' '.join(parts[2:]) if len(parts)>2 else ''
            if game_arg=='서든':
                markup=types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("⚔️ 서든 5v5",callback_data=f"nj_open:sa5:{extra_text}"),
                    types.InlineKeyboardButton("⚔️ 서든 6v6",callback_data=f"nj_open:sa6:{extra_text}"),
                )
                bot.reply_to(message,"⚔️ 서든어택 인원을 선택하세요!",reply_markup=markup); return
            game_type='lol'; display_name='리그오브레전드 5v5'
            db=get_db();c=db.cursor()
            try:
                c.execute("SELECT room_id FROM naejeon_rooms WHERE group_id=%s AND game_type=%s AND status='open'",(group_id,game_type))
                if c.fetchone(): bot.reply_to(message,"⚠️ 이미 진행 중인 내전 있음"); return
                room_id=str(uuid.uuid4())[:8]
                c.execute("INSERT INTO naejeon_rooms(room_id,group_id,game_type,slots,extra_text) VALUES(%s,%s,%s,%s,%s)",
                          (room_id,group_id,game_type,'{}',extra_text))
                db.commit()
            finally: c.close();db.close()
            param=f"{user_id}_{group_id}_{game_type}_{room_id}"
            nj_url=f"{WEBAPP_BASE_URL}/naejeon?start={param}"
            markup=types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚔️ 내전 참여하기",url=nj_url))
            send_naejeon_gif(group_id)
            msg=f"⚔️ {display_name} 내전 모집!"
            if extra_text: msg+=f"\n{extra_text}"
            bot.send_message(group_id,msg,reply_markup=markup)

        elif message.chat.type in ['group','supergroup']:
            save_message(user_id,username,first_name,group_id)
            # 채팅 마일스톤 체크 (비동기로 처리)
            threading.Thread(target=check_chat_milestone,args=(user_id,group_id,first_name,username),daemon=True).start()

    except Exception as e:
        import traceback; print(f"handle_all error: {e}\n{traceback.format_exc()}")

# ─────────────────────────────────────────────────────────
# Flask 라우트 — 공통
# ─────────────────────────────────────────────────────────
@app.route('/casino/check_admin')
def casino_check_admin():
    try:
        admin_id=int(request.args.get('adminId',0))
        return {'isAdmin':admin_id in ADMIN_IDS},200
    except: return {'isAdmin':False},200

@app.route('/casino')
def serve_casino(): return send_from_directory('.','casino.html')

@app.route('/casino/admin')
def serve_casino_admin(): return send_from_directory('.','casino_admin.html')

@app.route('/kbo')
def serve_kbo(): return send_from_directory('.','kbo.html')

@app.route('/naejeon')
def serve_naejeon(): return send_from_directory('.','naejeon.html')

@app.route('/vote')
def serve_vote(): return send_from_directory('.','vote.html')

# ─────────────────────────────────────────────────────────
# 출석 / 리필
# ─────────────────────────────────────────────────────────
@app.route('/casino/attend', methods=['POST'])
def casino_attend():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json()
        user_id=int(data.get('userId',0))
        group_id=int(data.get('groupId',0))
        today=datetime.now(KST).date()
        c.execute("SELECT last_attendance,first_name,username FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        row=c.fetchone()
        if row and row[0]==today:
            return {'ok':False,'error':'오늘 이미 출석했어요!'},200
        reward=100
        if row:
            c.execute("UPDATE points SET point=point+%s,last_attendance=%s WHERE user_id=%s AND group_id=%s",
                      (reward,today,user_id,group_id))
            name=row[1] or row[2] or f"id:{user_id}"
        else:
            c.execute("INSERT INTO points(user_id,group_id,first_name,username,point,last_attendance) VALUES(%s,%s,%s,%s,%s,%s)",
                      (user_id,group_id,'','' ,reward,today))
            name=f"id:{user_id}"
        c.execute("INSERT INTO point_logs(group_id,user_id,user_name,amount,reason) VALUES(%s,%s,%s,%s,%s)",
                  (group_id,user_id,name,reward,'출석 보상'))
        db.commit()
        update_mission(user_id,group_id,'play3')
        return {'ok':True,'reward':reward},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/refill', methods=['POST'])
def casino_refill():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json()
        user_id=int(data.get('userId',0))
        group_id=int(data.get('groupId',0))
        today=datetime.now(KST).date()
        c.execute("SELECT COUNT(*) FROM refill_logs WHERE user_id=%s AND group_id=%s AND refill_date=%s",
                  (user_id,group_id,today))
        count=c.fetchone()[0]
        if count>=5: return {'ok':False,'error':'오늘 리필을 5번 모두 사용했어요!'},200
        reward=100
        c.execute("INSERT INTO refill_logs(user_id,group_id,first_name,username,refill_date) VALUES(%s,%s,%s,%s,%s)",
                  (user_id,group_id,'','',today))
        c.execute("""INSERT INTO points(user_id,group_id,first_name,username,point)
            VALUES(%s,%s,%s,%s,%s) ON CONFLICT(user_id,group_id)
            DO UPDATE SET point=points.point+%s""",
            (user_id,group_id,'','',reward,reward))
        c.execute("SELECT first_name,username FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        pr=c.fetchone(); name=pr[0] or pr[1] or f"id:{user_id}" if pr else f"id:{user_id}"
        c.execute("INSERT INTO point_logs(group_id,user_id,user_name,amount,reason) VALUES(%s,%s,%s,%s,%s)",
                  (group_id,user_id,name,reward,'리필'))
        db.commit()
        return {'ok':True,'reward':reward,'remaining':5-count-1},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

# ─────────────────────────────────────────────────────────
# 포인트 지급 (관리자)
# ─────────────────────────────────────────────────────────
@app.route('/casino/point_grant', methods=['POST'])
def casino_point_grant():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json()
        admin_id=int(data.get('adminId',0))
        group_id=int(data.get('groupId',0))
        target_id=int(data.get('userId',0))
        amount=int(data.get('amount',0))
        reason=data.get('reason','관리자 지급')
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자만 사용할 수 있어요.'},403
        if amount==0: return {'ok':False,'error':'금액을 입력해주세요.'},400
        c.execute("SELECT first_name,username,point FROM points WHERE user_id=%s AND group_id=%s",(target_id,group_id))
        row=c.fetchone()
        if not row: return {'ok':False,'error':'유저를 찾을 수 없어요.'},404
        user_name=row[0] or row[1] or f"id:{target_id}"
        new_point=row[2]+amount
        if new_point<0: return {'ok':False,'error':f'포인트 부족. 현재: {row[2]:,}P'},400
        c.execute("UPDATE points SET point=%s WHERE user_id=%s AND group_id=%s",(new_point,target_id,group_id))
        c.execute("INSERT INTO point_logs(group_id,user_id,user_name,amount,reason,admin_id) VALUES(%s,%s,%s,%s,%s,%s)",
                  (group_id,target_id,user_name,amount,reason,admin_id))
        db.commit()
        return {'ok':True,'newPoint':new_point,'userName':user_name},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/point_grant_all', methods=['POST'])
def casino_point_grant_all():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json()
        admin_id=int(data.get('adminId',0))
        group_id=int(data.get('groupId',0))
        amount=int(data.get('amount',0))
        reason=data.get('reason','이벤트 지급')
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        if amount<=0: return {'ok':False,'error':'금액은 양수'},400
        c.execute("SELECT user_id,first_name,username FROM points WHERE group_id=%s",(group_id,))
        rows=c.fetchall()
        for r in rows:
            uid=r[0]; name=r[1] or r[2] or f"id:{uid}"
            c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(amount,uid,group_id))
            c.execute("INSERT INTO point_logs(group_id,user_id,user_name,amount,reason,admin_id) VALUES(%s,%s,%s,%s,%s,%s)",
                      (group_id,uid,name,amount,reason,admin_id))
        db.commit()
        return {'ok':True,'count':len(rows)},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

# ─────────────────────────────────────────────────────────
# 채팅 마일스톤 관리자 컨트롤
# ─────────────────────────────────────────────────────────
@app.route('/casino/chat_milestone_status')
def chat_milestone_status():
    """오늘 채팅 마일스톤 달성 현황"""
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0))
        today=datetime.now(KST).date()
        c.execute("""
            SELECT p.user_id, COALESCE(p.first_name,p.username,CAST(p.user_id AS VARCHAR)) as name,
                   COUNT(cl.id) as today_count
            FROM points p
            LEFT JOIN chat_logs cl ON cl.user_id=p.user_id AND cl.group_id=p.group_id AND DATE(cl.message_date)=%s
            WHERE p.group_id=%s
            GROUP BY p.user_id,p.first_name,p.username
            ORDER BY today_count DESC
        """,(today,group_id))
        users=c.fetchall()
        c.execute("SELECT user_id,milestone FROM chat_milestone_logs WHERE group_id=%s AND rewarded_date=%s",(group_id,today))
        rewarded={(r[0],r[1]) for r in c.fetchall()}
        result=[]
        for u in users:
            uid,name,cnt=u
            milestones_status={}
            for m in CHAT_MILESTONES:
                milestones_status[m]={'achieved':cnt>=m,'rewarded':(uid,m) in rewarded,'reward':CHAT_MILESTONES[m]}
            result.append({'userId':uid,'name':name,'todayCount':cnt,'milestones':milestones_status})
        return result,200
    except Exception as e: return [],500
    finally: c.close();db.close()

@app.route('/casino/chat_milestone_grant', methods=['POST'])
def chat_milestone_grant():
    """관리자가 수동으로 마일스톤 포인트 지급"""
    db=get_db();c=db.cursor()
    try:
        data=request.get_json()
        admin_id=int(data.get('adminId',0))
        group_id=int(data.get('groupId',0))
        target_id=int(data.get('userId',0))
        milestone=int(data.get('milestone',0))
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        reward=CHAT_MILESTONES.get(milestone)
        if not reward: return {'ok':False,'error':'유효하지 않은 마일스톤'},400
        today=datetime.now(KST).date()
        c.execute("SELECT first_name,username FROM points WHERE user_id=%s AND group_id=%s",(target_id,group_id))
        row=c.fetchone()
        if not row: return {'ok':False,'error':'유저 없음'},404
        name=row[0] or row[1] or f"id:{target_id}"
        # 중복 지급 방지
        c.execute("SELECT 1 FROM chat_milestone_logs WHERE user_id=%s AND group_id=%s AND milestone=%s AND rewarded_date=%s",
                  (target_id,group_id,milestone,today))
        if c.fetchone(): return {'ok':False,'error':'오늘 이미 지급됨'},400
        c.execute("INSERT INTO chat_milestone_logs(user_id,group_id,milestone,rewarded_date) VALUES(%s,%s,%s,%s)",
                  (target_id,group_id,milestone,today))
        c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(reward,target_id,group_id))
        c.execute("INSERT INTO point_logs(group_id,user_id,user_name,amount,reason,admin_id) VALUES(%s,%s,%s,%s,%s,%s)",
                  (group_id,target_id,name,reward,f'채팅 {milestone}회 달성 (관리자 지급)',admin_id))
        db.commit()
        return {'ok':True,'reward':reward,'userName':name},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

# ─────────────────────────────────────────────────────────
# 유저 / 통계 / 로그
# ─────────────────────────────────────────────────────────
@app.route('/casino/users')
def casino_users():
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0))
        c.execute("""SELECT p.user_id,
            COALESCE(p.first_name,p.username,CAST(p.user_id AS VARCHAR)) as name,
            p.point, p.total_bet,
            CASE WHEN b.user_id IS NOT NULL THEN TRUE ELSE FALSE END as blacklisted
            FROM points p
            LEFT JOIN casino_blacklist b ON b.user_id=p.user_id AND b.group_id=p.group_id
            WHERE p.group_id=%s ORDER BY p.point DESC""",(group_id,))
        rows=c.fetchall()
        return [{'userId':r[0],'name':r[1],'point':r[2],'totalBet':r[3] or 0,'blacklisted':r[4]} for r in rows],200
    except Exception as e: return [],500
    finally: c.close();db.close()

@app.route('/casino/point_logs')
def casino_point_logs():
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0))
        limit=int(request.args.get('limit',50))
        c.execute("SELECT user_name,amount,reason,created_at FROM point_logs WHERE group_id=%s ORDER BY created_at DESC LIMIT %s",
                  (group_id,limit))
        rows=c.fetchall()
        return [{'userName':r[0],'amount':r[1],'reason':r[2],'createdAt':r[3].isoformat() if r[3] else None} for r in rows],200
    except: return [],500
    finally: c.close();db.close()

@app.route('/casino/my_bets')
def casino_my_bets():
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0))
        user_id=int(request.args.get('userId',0))
        limit=int(request.args.get('limit',30))
        c.execute("""SELECT cb.game_id,cb.bet_on,cb.amount,cb.payout,cb.won,cb.created_at
            FROM casino_bets cb
            WHERE cb.group_id=%s AND cb.user_id=%s
            ORDER BY cb.created_at DESC LIMIT %s""",(group_id,user_id,limit))
        rows=c.fetchall()
        result=[]
        for r in rows:
            result.append({
                'game':r[0],'choice':r[1],'amount':r[2],'payout':r[3],
                'result':'win' if r[4] else ('lose' if r[4]==False else 'pending'),
                'createdAt':r[5].isoformat() if r[5] else None
            })
        return result,200
    except Exception as e: return [],500
    finally: c.close();db.close()

@app.route('/casino/stats')
def casino_stats():
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0))
        days=int(request.args.get('days',7))
        c.execute("""SELECT game_id,COUNT(*) as rounds,
            SUM(CASE WHEN won THEN payout ELSE 0 END) as total_payout,
            SUM(amount) as total_bet,COUNT(DISTINCT user_id) as players
            FROM casino_bets WHERE group_id=%s AND created_at>=NOW()-INTERVAL '%s days'
            GROUP BY game_id""",(group_id,days))
        rows=c.fetchall()
        return [{'gameId':r[0],'rounds':r[1],'totalPayout':r[2] or 0,'totalBet':r[3] or 0,
                 'profit':(r[3] or 0)-(r[2] or 0),'players':r[4]} for r in rows],200
    except: return [],500
    finally: c.close();db.close()

@app.route('/casino/dashboard')
def casino_dashboard():
    """실시간 수익 대시보드"""
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0))
        today=datetime.now(KST).date()
        c.execute("SELECT SUM(amount) FROM casino_bets WHERE group_id=%s AND DATE(created_at)=%s",(group_id,today))
        today_bet=c.fetchone()[0] or 0
        c.execute("SELECT SUM(payout) FROM casino_bets WHERE group_id=%s AND won=TRUE AND DATE(created_at)=%s",(group_id,today))
        today_payout=c.fetchone()[0] or 0
        c.execute("SELECT COUNT(DISTINCT user_id) FROM casino_bets WHERE group_id=%s AND DATE(created_at)=%s",(group_id,today))
        dau=c.fetchone()[0] or 0
        c.execute("SELECT COUNT(*) FROM casino_games WHERE group_id=%s AND DATE(created_at)=%s",(group_id,today))
        rounds=c.fetchone()[0] or 0
        return {'todayBet':today_bet,'todayPayout':today_payout,
                'todayProfit':today_bet-today_payout,'dau':dau,'rounds':rounds},200
    except Exception as e: return {'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/missions')
def casino_missions():
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0))
        user_id=int(request.args.get('userId',0))
        today=datetime.now(KST).date()
        result=[]
        for m in DAILY_MISSIONS:
            c.execute("SELECT progress,completed FROM daily_missions WHERE user_id=%s AND group_id=%s AND mission_id=%s AND mission_date=%s",
                      (user_id,group_id,m['id'],today))
            row=c.fetchone()
            result.append({'id':m['id'],'desc':m['desc'],'target':m['target'],'reward':m['reward'],
                           'progress':row[0] if row else 0,'completed':row[1] if row else False})
        return result,200
    except: return [],500
    finally: c.close();db.close()

@app.route('/casino/user_level')
def casino_user_level():
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0))
        user_id=int(request.args.get('userId',0))
        c.execute("SELECT total_bet FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        row=c.fetchone()
        total_bet=row[0] if row else 0
        lvl=get_user_level(total_bet or 0)
        return {'level':lvl,'totalBet':total_bet},200
    except: return {'level':LEVELS[0],'totalBet':0},200
    finally: c.close();db.close()

# ─────────────────────────────────────────────────────────
# 블랙리스트
# ─────────────────────────────────────────────────────────
@app.route('/casino/blacklist', methods=['GET'])
def casino_get_blacklist():
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0))
        c.execute("""SELECT b.user_id,COALESCE(p.first_name,p.username,CAST(b.user_id AS VARCHAR)) as name,
            b.reason,b.created_at FROM casino_blacklist b
            LEFT JOIN points p ON p.user_id=b.user_id AND p.group_id=b.group_id
            WHERE b.group_id=%s""",(group_id,))
        rows=c.fetchall()
        return [{'userId':r[0],'name':r[1],'reason':r[2],'createdAt':r[3].isoformat() if r[3] else None} for r in rows],200
    except: return [],500
    finally: c.close();db.close()

@app.route('/casino/blacklist', methods=['POST'])
def casino_mod_blacklist():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); admin_id=int(data.get('adminId',0))
        group_id=int(data.get('groupId',0)); target_id=int(data.get('userId',0))
        reason=data.get('reason',''); action=data.get('action','add')
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        if action=='remove':
            c.execute("DELETE FROM casino_blacklist WHERE group_id=%s AND user_id=%s",(group_id,target_id))
        else:
            c.execute("INSERT INTO casino_blacklist(group_id,user_id,reason) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING",
                      (group_id,target_id,reason))
        db.commit(); return {'ok':True},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

# ─────────────────────────────────────────────────────────
# 카지노 설정
# ─────────────────────────────────────────────────────────
@app.route('/casino/settings', methods=['GET'])
def casino_get_settings():
    try:
        group_id=int(request.args.get('groupId',0))
        game_id=request.args.get('gameId','')
        return get_casino_settings(group_id,game_id),200
    except Exception as e: return {'error':str(e)},500

@app.route('/casino/settings', methods=['POST'])
def casino_save_settings_route():
    try:
        data=request.get_json(); admin_id=int(data.get('adminId',0))
        group_id=int(data.get('groupId',0)); game_id=data.get('gameId','')
        settings=data.get('settings',{})
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        save_casino_settings(group_id,game_id,settings)
        return {'ok':True},200
    except Exception as e: return {'ok':False,'error':str(e)},500

@app.route('/casino/auto_config', methods=['POST'])
def casino_auto_config():
    """자동 라운드 설정"""
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); admin_id=int(data.get('adminId',0))
        group_id=int(data.get('groupId',0))
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        race_auto=data.get('raceAuto',True)
        horse_auto=data.get('horseAuto',True)
        round_minutes=int(data.get('roundMinutes',3))
        c.execute("""INSERT INTO auto_round_config(group_id,race_auto,horse_auto,round_minutes,updated_at)
            VALUES(%s,%s,%s,%s,NOW()) ON CONFLICT(group_id)
            DO UPDATE SET race_auto=%s,horse_auto=%s,round_minutes=%s,updated_at=NOW()""",
            (group_id,race_auto,horse_auto,round_minutes,race_auto,horse_auto,round_minutes))
        db.commit()
        return {'ok':True},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

# ─────────────────────────────────────────────────────────
# 경주 라우트
# ─────────────────────────────────────────────────────────
@app.route('/casino/race')
def serve_race(): return send_from_directory('.','race.html')

@app.route('/casino/race/state')
def race_state():
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0))
        user_id=int(request.args.get('userId',0))
        c.execute("SELECT id,status,result,settings,started_at FROM casino_games WHERE group_id=%s AND game_id='race' ORDER BY id DESC LIMIT 1",(group_id,))
        row=c.fetchone()

        # 없으면 자동 생성
        if not row:
            settings=get_casino_settings(group_id,'race')
            c.execute("INSERT INTO casino_games(game_id,group_id,status,settings,started_at) VALUES('race',%s,'betting',%s,NOW()) RETURNING id,status,result,settings,started_at",
                      (group_id,json.dumps(settings)))
            row=c.fetchone(); db.commit()

        round_id,status,result,settings_db,started_at=row
        settings=get_casino_settings(group_id,'race')

        c.execute("SELECT bet_on,SUM(amount),COUNT(*) FROM casino_bets WHERE round_id=%s GROUP BY bet_on",(round_id,))
        bets={r[0]:{'total':r[1],'count':r[2]} for r in c.fetchall()}
        total_pool=sum(b['total'] for b in bets.values())
        house=settings.get('house_edge',5)
        odds={}
        for opt in ['rabbit','turtle']:
            pool=bets.get(opt,{}).get('total',0)
            if pool>0 and total_pool>0:
                odds[opt]=max(1.1,round((total_pool*(1-house/100))/pool,2))
            else:
                odds[opt]=settings.get(f'{opt}_odds',2.0)

        my_bet=None
        if user_id:
            c.execute("SELECT bet_on,amount FROM casino_bets WHERE round_id=%s AND user_id=%s",(round_id,user_id))
            mb=c.fetchone()
            if mb: my_bet={'betOn':mb[0],'amount':mb[1]}

        # 타이머 정보
        timer_info=None
        if started_at and status=='betting':
            started=started_at.replace(tzinfo=UTC) if started_at.tzinfo is None else started_at.astimezone(UTC)
            elapsed=(datetime.now(UTC)-started).total_seconds()
            total_secs=settings.get('round_minutes',3)*60
            remaining=max(0,total_secs-elapsed)
            timer_info={'totalSecs':total_secs,'remainingSecs':int(remaining),'startedAt':to_utc_iso(started_at)}

        return {'status':status,'roundId':round_id,'result':result,'bets':bets,
                'odds':odds,'totalPool':total_pool,'myBet':my_bet,
                'settings':settings,'timerInfo':timer_info},200
    except Exception as e:
        import traceback; print(traceback.format_exc())
        return {'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/race/open', methods=['POST'])
def race_open():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); admin_id=int(data.get('adminId',0)); group_id=int(data.get('groupId',0))
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        c.execute("SELECT id FROM casino_games WHERE group_id=%s AND game_id='race' AND status NOT IN ('closed','cancelled')",(group_id,))
        if c.fetchone(): return {'ok':False,'error':'이미 진행 중'},400
        settings=get_casino_settings(group_id,'race')
        c.execute("INSERT INTO casino_games(game_id,group_id,status,settings,started_at) VALUES('race',%s,'betting',%s,NOW()) RETURNING id",
                  (group_id,json.dumps(settings)))
        round_id=c.fetchone()[0]; db.commit()
        return {'ok':True,'roundId':round_id},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/race/bet', methods=['POST'])
def race_bet():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); round_id=int(data.get('roundId',0))
        group_id=int(data.get('groupId',0)); user_id=int(data.get('userId',0))
        user_name=(data.get('userName') or f"id:{user_id}").strip()
        bet_on=data.get('betOn',''); amount=int(data.get('amount',0))

        if bet_on not in ['rabbit','turtle']: return {'ok':False,'error':'올바른 항목 선택'},400
        if is_casino_blacklisted(group_id,user_id): return {'ok':False,'error':'이용 제한'},403
        if check_cooldown(user_id,group_id,'race'): return {'ok':False,'error':f'쿨다운 중 ({COOLDOWN_SECS}초)'},400
        if check_daily_limit(user_id,group_id,amount): return {'ok':False,'error':f'일일 한도 초과 ({DAILY_BET_LIMIT:,}P)'},400

        settings=get_casino_settings(group_id,'race')
        lvl=get_user_level(0)  # TODO: 실제 total_bet 조회
        if amount<settings.get('min_bet',10): return {'ok':False,'error':f"최소 {settings['min_bet']:,}P"},400
        if amount>settings.get('max_bet',10000): return {'ok':False,'error':f"최대 {settings['max_bet']:,}P"},400

        c.execute("SELECT status FROM casino_games WHERE id=%s",(round_id,))
        row=c.fetchone()
        if not row or row[0]!='betting': return {'ok':False,'error':'베팅 시간 아님'},400
        c.execute("SELECT id FROM casino_bets WHERE round_id=%s AND user_id=%s",(round_id,user_id))
        if c.fetchone(): return {'ok':False,'error':'이미 베팅'},400
        c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        pt=c.fetchone()
        if not pt or pt[0]<amount: return {'ok':False,'error':'포인트 부족'},400

        c.execute("UPDATE points SET point=point-%s,total_bet=COALESCE(total_bet,0)+%s WHERE user_id=%s AND group_id=%s",
                  (amount,amount,user_id,group_id))
        c.execute("INSERT INTO casino_bets(game_id,round_id,group_id,user_id,user_name,bet_on,amount) VALUES('race',%s,%s,%s,%s,%s,%s)",
                  (round_id,group_id,user_id,user_name,bet_on,amount))
        db.commit()
        set_cooldown(user_id,group_id,'race')
        add_daily_bet(user_id,group_id,amount)
        check_suspicious(group_id,user_id,amount,'race')
        update_mission(user_id,group_id,'play3')
        update_mission(user_id,group_id,'bet1000')
        return {'ok':True,'betOn':bet_on,'amount':amount},200
    except Exception as e:
        import traceback; print(traceback.format_exc())
        return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/race/start', methods=['POST'])
def race_start():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); admin_id=int(data.get('adminId',0))
        round_id=int(data.get('roundId',0)); group_id=int(data.get('groupId',0))
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        c.execute("UPDATE casino_games SET status='running' WHERE id=%s AND group_id=%s",(round_id,group_id))
        db.commit(); return {'ok':True},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/race/result', methods=['POST'])
def race_result():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); admin_id=int(data.get('adminId',0))
        round_id=int(data.get('roundId',0)); group_id=int(data.get('groupId',0))
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        settings=get_casino_settings(group_id,'race')
        force=settings.get('force_result'); win_rate=settings.get('rabbit_win_rate',60); house=settings.get('house_edge',5)
        winner=force if force in ['rabbit','turtle'] else ('rabbit' if random.randint(1,100)<=win_rate else 'turtle')
        c.execute("SELECT bet_on,SUM(amount) FROM casino_bets WHERE round_id=%s GROUP BY bet_on",(round_id,))
        pools={r[0]:r[1] for r in c.fetchall()}
        total_pool=sum(pools.values()); winner_pool=pools.get(winner,0)
        odds=max(1.1,(total_pool*(1-house/100))/winner_pool) if winner_pool>0 else 2.0
        c.execute("SELECT id,user_id,user_name,amount FROM casino_bets WHERE round_id=%s AND bet_on=%s",(round_id,winner))
        winners=c.fetchall(); winner_list=[]
        for bet in winners:
            payout=int(bet[3]*odds)
            c.execute("UPDATE casino_bets SET won=TRUE,payout=%s WHERE id=%s",(payout,bet[0]))
            c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(payout,bet[1],group_id))
            c.execute("INSERT INTO point_logs(group_id,user_id,user_name,amount,reason) VALUES(%s,%s,%s,%s,%s)",
                      (group_id,bet[1],bet[2],payout,f'경주 당첨 x{odds:.2f}'))
            winner_list.append({'name':bet[2],'amount':bet[3],'payout':payout})
            update_mission(bet[1],group_id,'win1')
        c.execute("UPDATE casino_bets SET won=FALSE,payout=0 WHERE round_id=%s AND bet_on!=%s",(round_id,winner))
        c.execute("UPDATE casino_games SET status='closed',result=%s,ended_at=NOW() WHERE id=%s",(winner,round_id))
        db.commit()
        # 자동 다음 라운드 오픈
        settings2=get_casino_settings(group_id,'race')
        if settings2.get('auto_round',True):
            c2=db.cursor() if not db.closed else get_db().cursor()
            try:
                db2=get_db();c2=db2.cursor()
                c2.execute("INSERT INTO casino_games(game_id,group_id,status,settings,started_at) VALUES('race',%s,'betting',%s,NOW())",
                           (group_id,json.dumps(settings2)))
                db2.commit(); c2.close(); db2.close()
            except: pass
        return {'ok':True,'winner':winner,'odds':odds,'winners':winner_list},200
    except Exception as e:
        import traceback; print(traceback.format_exc())
        return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

# ─────────────────────────────────────────────────────────
# 바카라
# ─────────────────────────────────────────────────────────
@app.route('/casino/baccarat')
def serve_baccarat(): return send_from_directory('.','baccarat.html')

@app.route('/casino/baccarat/state')
def baccarat_state():
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0)); user_id=int(request.args.get('userId',0))
        c.execute("SELECT id,status,result,settings FROM casino_games WHERE group_id=%s AND game_id='baccarat' ORDER BY id DESC LIMIT 1",(group_id,))
        row=c.fetchone()
        if not row: return {'status':'idle','roundId':None,'myBet':None,'settings':get_casino_settings(group_id,'baccarat')},200
        round_id,status,result,_=row
        my_bet=None
        if user_id:
            c.execute("SELECT bet_on,amount FROM casino_bets WHERE round_id=%s AND user_id=%s",(round_id,user_id))
            mb=c.fetchone()
            if mb: my_bet={'betOn':mb[0],'amount':mb[1]}
        c.execute("SELECT bet_on,SUM(amount),COUNT(*) FROM casino_bets WHERE round_id=%s GROUP BY bet_on",(round_id,))
        bets={r[0]:{'total':r[1],'count':r[2]} for r in c.fetchall()}
        return {'status':status,'roundId':round_id,'result':result,'myBet':my_bet,
                'bets':bets,'settings':get_casino_settings(group_id,'baccarat')},200
    except Exception as e: return {'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/baccarat/open', methods=['POST'])
def baccarat_open():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); admin_id=int(data.get('adminId',0)); group_id=int(data.get('groupId',0))
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        c.execute("SELECT id FROM casino_games WHERE group_id=%s AND game_id='baccarat' AND status NOT IN ('closed','cancelled')",(group_id,))
        if c.fetchone(): return {'ok':False,'error':'이미 진행 중'},400
        settings=get_casino_settings(group_id,'baccarat')
        c.execute("INSERT INTO casino_games(game_id,group_id,status,settings,started_at) VALUES('baccarat',%s,'betting',%s,NOW()) RETURNING id",
                  (group_id,json.dumps(settings)))
        round_id=c.fetchone()[0]; db.commit()
        return {'ok':True,'roundId':round_id},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/baccarat/bet', methods=['POST'])
def baccarat_bet():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); round_id=int(data.get('roundId',0)); group_id=int(data.get('groupId',0))
        user_id=int(data.get('userId',0)); bet_on=data.get('betOn',''); amount=int(data.get('amount',0))
        if bet_on not in ['player','banker','tie']: return {'ok':False,'error':'올바른 항목'},400
        if is_casino_blacklisted(group_id,user_id): return {'ok':False,'error':'이용 제한'},403
        if check_cooldown(user_id,group_id,'baccarat'): return {'ok':False,'error':f'쿨다운 중'},400
        if check_daily_limit(user_id,group_id,amount): return {'ok':False,'error':'일일 한도 초과'},400
        settings=get_casino_settings(group_id,'baccarat')
        if amount<settings.get('min_bet',10): return {'ok':False,'error':f"최소 {settings['min_bet']:,}P"},400
        if amount>settings.get('max_bet',10000): return {'ok':False,'error':f"최대 {settings['max_bet']:,}P"},400
        c.execute("SELECT status FROM casino_games WHERE id=%s",(round_id,))
        row=c.fetchone()
        if not row or row[0]!='betting': return {'ok':False,'error':'베팅 시간 아님'},400
        c.execute("SELECT id FROM casino_bets WHERE round_id=%s AND user_id=%s",(round_id,user_id))
        if c.fetchone(): return {'ok':False,'error':'이미 베팅'},400
        c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        pt=c.fetchone()
        if not pt or pt[0]<amount: return {'ok':False,'error':'포인트 부족'},400
        c.execute("UPDATE points SET point=point-%s,total_bet=COALESCE(total_bet,0)+%s WHERE user_id=%s AND group_id=%s",
                  (amount,amount,user_id,group_id))
        c.execute("INSERT INTO casino_bets(game_id,round_id,group_id,user_id,bet_on,amount) VALUES('baccarat',%s,%s,%s,%s,%s)",
                  (round_id,group_id,user_id,bet_on,amount))
        db.commit()
        set_cooldown(user_id,group_id,'baccarat')
        add_daily_bet(user_id,group_id,amount)
        update_mission(user_id,group_id,'play3')
        return {'ok':True},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/baccarat/result', methods=['POST'])
def baccarat_result():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); admin_id=int(data.get('adminId',0))
        round_id=int(data.get('roundId',0)); group_id=int(data.get('groupId',0))
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
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
                update_mission(bet[1],group_id,'win1')
            else:
                c.execute("UPDATE casino_bets SET won=FALSE,payout=0 WHERE id=%s",(bet[0],))
        c.execute("UPDATE casino_games SET status='closed',result=%s,ended_at=NOW() WHERE id=%s",(result,round_id))
        db.commit()
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
        c.execute("SELECT id,status,result,settings,started_at FROM casino_games WHERE group_id=%s AND game_id='horse' ORDER BY id DESC LIMIT 1",(group_id,))
        row=c.fetchone()
        settings=get_casino_settings(group_id,'horse')

        if not row:
            c.execute("INSERT INTO casino_games(game_id,group_id,status,settings,started_at) VALUES('horse',%s,'betting',%s,NOW()) RETURNING id,status,result,settings,started_at",
                      (group_id,json.dumps(settings)))
            row=c.fetchone(); db.commit()

        round_id,status,result,_,started_at=row
        c.execute("SELECT bet_on,SUM(amount),COUNT(*) FROM casino_bets WHERE round_id=%s GROUP BY bet_on",(round_id,))
        bets={str(r[0]):{'total':r[1],'count':r[2]} for r in c.fetchall()}
        my_bet=None
        if user_id:
            c.execute("SELECT bet_on,amount FROM casino_bets WHERE round_id=%s AND user_id=%s",(round_id,user_id))
            mb=c.fetchone()
            if mb: my_bet={'betOn':mb[0],'amount':mb[1]}

        timer_info=None
        if started_at and status=='betting':
            started=started_at.replace(tzinfo=UTC) if started_at.tzinfo is None else started_at.astimezone(UTC)
            elapsed=(datetime.now(UTC)-started).total_seconds()
            total_secs=settings.get('round_minutes',3)*60
            remaining=max(0,total_secs-elapsed)
            timer_info={'totalSecs':total_secs,'remainingSecs':int(remaining),'startedAt':to_utc_iso(started_at)}

        return {'status':status,'roundId':round_id,'result':result,'bets':bets,
                'myBet':my_bet,'settings':settings,'timerInfo':timer_info},200
    except Exception as e: return {'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/horse/open', methods=['POST'])
def horse_open():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); admin_id=int(data.get('adminId',0)); group_id=int(data.get('groupId',0))
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        c.execute("SELECT id FROM casino_games WHERE group_id=%s AND game_id='horse' AND status NOT IN ('closed','cancelled')",(group_id,))
        if c.fetchone(): return {'ok':False,'error':'이미 진행 중'},400
        settings=get_casino_settings(group_id,'horse')
        c.execute("INSERT INTO casino_games(game_id,group_id,status,settings,started_at) VALUES('horse',%s,'betting',%s,NOW()) RETURNING id",
                  (group_id,json.dumps(settings)))
        round_id=c.fetchone()[0]; db.commit()
        return {'ok':True,'roundId':round_id},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/horse/bet', methods=['POST'])
def horse_bet():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); round_id=int(data.get('roundId',0)); group_id=int(data.get('groupId',0))
        user_id=int(data.get('userId',0)); bet_on=data.get('betOn'); amount=int(data.get('amount',0))
        if is_casino_blacklisted(group_id,user_id): return {'ok':False,'error':'이용 제한'},403
        if check_cooldown(user_id,group_id,'horse'): return {'ok':False,'error':'쿨다운 중'},400
        if check_daily_limit(user_id,group_id,amount): return {'ok':False,'error':'일일 한도 초과'},400
        settings=get_casino_settings(group_id,'horse')
        if amount<settings.get('min_bet',10): return {'ok':False,'error':f"최소 {settings['min_bet']:,}P"},400
        if amount>settings.get('max_bet',10000): return {'ok':False,'error':f"최대 {settings['max_bet']:,}P"},400
        c.execute("SELECT status FROM casino_games WHERE id=%s",(round_id,))
        row=c.fetchone()
        if not row or row[0]!='betting': return {'ok':False,'error':'베팅 시간 아님'},400
        c.execute("SELECT id FROM casino_bets WHERE round_id=%s AND user_id=%s",(round_id,user_id))
        if c.fetchone(): return {'ok':False,'error':'이미 베팅'},400
        c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        pt=c.fetchone()
        if not pt or pt[0]<amount: return {'ok':False,'error':'포인트 부족'},400
        c.execute("UPDATE points SET point=point-%s,total_bet=COALESCE(total_bet,0)+%s WHERE user_id=%s AND group_id=%s",
                  (amount,amount,user_id,group_id))
        c.execute("INSERT INTO casino_bets(game_id,round_id,group_id,user_id,bet_on,amount) VALUES('horse',%s,%s,%s,%s,%s)",
                  (round_id,group_id,user_id,str(bet_on),amount))
        db.commit()
        set_cooldown(user_id,group_id,'horse')
        add_daily_bet(user_id,group_id,amount)
        check_suspicious(group_id,user_id,amount,'horse')
        update_mission(user_id,group_id,'play3')
        return {'ok':True},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/horse/result', methods=['POST'])
def horse_result():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); admin_id=int(data.get('adminId',0))
        round_id=int(data.get('roundId',0)); group_id=int(data.get('groupId',0))
        if admin_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        settings=get_casino_settings(group_id,'horse')
        horses=settings.get('horses',DEFAULT_CASINO_SETTINGS['horse']['horses'])
        force=settings.get('force_result')
        if force:
            winner_h=next((h for h in horses if str(h['id'])==str(force) or h['name']==force),None) or horses[0]
        else:
            total_rate=sum(h.get('win_rate',20) for h in horses)
            r=random.randint(1,total_rate); acc=0; winner_h=horses[-1]
            for h in horses:
                acc+=h.get('win_rate',20)
                if r<=acc: winner_h=h; break
        winner_id=str(winner_h['id']); odds=winner_h.get('base_odds',2.5)
        c.execute("SELECT id,user_id,user_name,amount,bet_on FROM casino_bets WHERE round_id=%s",(round_id,))
        bets=c.fetchall()
        for bet in bets:
            if str(bet[4])==winner_id:
                payout=int(bet[3]*odds)
                c.execute("UPDATE casino_bets SET won=TRUE,payout=%s WHERE id=%s",(payout,bet[0]))
                c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(payout,bet[1],group_id))
                c.execute("INSERT INTO point_logs(group_id,user_id,user_name,amount,reason) VALUES(%s,%s,%s,%s,%s)",
                          (group_id,bet[1],bet[2],payout,f'경마 당첨 ({winner_h["name"]}) x{odds}'))
                update_mission(bet[1],group_id,'win1')
            else:
                c.execute("UPDATE casino_bets SET won=FALSE,payout=0 WHERE id=%s",(bet[0],))
        c.execute("UPDATE casino_games SET status='closed',result=%s,ended_at=NOW() WHERE id=%s",(winner_id,round_id))
        db.commit()
        # 자동 다음 라운드
        settings2=get_casino_settings(group_id,'horse')
        if settings2.get('auto_round',True):
            try:
                db2=get_db();c2=db2.cursor()
                c2.execute("INSERT INTO casino_games(game_id,group_id,status,settings,started_at) VALUES('horse',%s,'betting',%s,NOW())",
                           (group_id,json.dumps(settings2)))
                db2.commit(); c2.close(); db2.close()
            except: pass
        return {'ok':True,'result':winner_id,'winner':winner_h},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

# ─────────────────────────────────────────────────────────
# 슬롯 / 룰렛 / 빅휠
# ─────────────────────────────────────────────────────────
@app.route('/casino/slots')
def serve_slots(): return send_from_directory('.','slots.html')

@app.route('/casino/slots/spin', methods=['POST'])
def slots_spin():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); group_id=int(data.get('groupId',0))
        user_id=int(data.get('userId',0)); amount=int(data.get('amount',0)); result=data.get('result',[])
        if is_casino_blacklisted(group_id,user_id): return {'ok':False,'error':'이용 제한'},403
        if amount<20: return {'ok':False,'error':'최소 20P'},400
        if check_daily_limit(user_id,group_id,amount): return {'ok':False,'error':'일일 한도 초과'},400
        c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        pt=c.fetchone()
        if not pt or pt[0]<amount: return {'ok':False,'error':'포인트 부족'},400
        MULT_3={'🍋':3,'🍒':4,'🍇':5,'⭐':7,'7️⃣':10,'💎':50}
        s1,s2,s3=result[0],result[1],result[2]
        if s1==s2==s3: payout=amount*MULT_3.get(s1,3)
        elif s1==s2 or s2==s3 or s1==s3: payout=int(amount*1.5)
        else: payout=0
        net_payout=max(0,payout-int(payout*0.05)) if payout>0 else 0
        c.execute("UPDATE points SET point=point-%s,total_bet=COALESCE(total_bet,0)+%s WHERE user_id=%s AND group_id=%s",
                  (amount,amount,user_id,group_id))
        if net_payout>0:
            c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(net_payout,user_id,group_id))
        c.execute("INSERT INTO casino_games(game_id,group_id,status,result,settings,ended_at) VALUES('slots',%s,'closed',%s,%s,NOW())",
                  (group_id,''.join(result),json.dumps({'amount':amount,'payout':net_payout})))
        db.commit()
        add_daily_bet(user_id,group_id,amount)
        update_mission(user_id,group_id,'play3')
        if net_payout>0: update_mission(user_id,group_id,'win1')
        return {'ok':True,'payout':net_payout},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/roulette')
def serve_roulette(): return send_from_directory('.','roulette.html')

@app.route('/casino/roulette/spin', methods=['POST'])
def roulette_spin():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); group_id=int(data.get('groupId',0)); user_id=int(data.get('userId',0))
        amount=int(data.get('amount',0)); bet_type=data.get('betType',''); bet_value=data.get('betValue')
        if is_casino_blacklisted(group_id,user_id): return {'ok':False,'error':'이용 제한'},403
        if amount<10: return {'ok':False,'error':'최소 10P'},400
        if check_daily_limit(user_id,group_id,amount): return {'ok':False,'error':'일일 한도 초과'},400
        c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        pt=c.fetchone()
        if not pt or pt[0]<amount: return {'ok':False,'error':'포인트 부족'},400
        NUM_COLORS={0:'green',1:'red',2:'black',3:'red',4:'black',5:'red',6:'black',7:'red',8:'black',9:'red',
                    10:'black',11:'black',12:'red',13:'black',14:'red',15:'black',16:'red',17:'black',18:'red',
                    19:'red',20:'black',21:'red',22:'black',23:'red',24:'black',25:'red',26:'black',27:'red',
                    28:'black',29:'black',30:'red',31:'black',32:'red',33:'black',34:'red',35:'black',36:'red'}
        srv_result=random.randint(0,36); color=NUM_COLORS.get(srv_result,'black')
        srv_won=False
        if bet_type=='color': srv_won=(bet_value==color)
        elif bet_type=='simple':
            if bet_value=='odd': srv_won=srv_result>0 and srv_result%2==1
            elif bet_value=='even': srv_won=srv_result>0 and srv_result%2==0
            elif bet_value=='low': srv_won=1<=srv_result<=18
            elif bet_value=='high': srv_won=19<=srv_result<=36
        elif bet_type=='number': srv_won=(int(bet_value)==srv_result)
        if bet_type=='number': odds=35
        elif bet_type=='color' and bet_value=='green': odds=14
        else: odds=2
        srv_payout=amount*odds if srv_won else 0
        net_payout=max(0,srv_payout-int(srv_payout*0.05)) if srv_payout>0 else 0
        c.execute("UPDATE points SET point=point-%s,total_bet=COALESCE(total_bet,0)+%s WHERE user_id=%s AND group_id=%s",
                  (amount,amount,user_id,group_id))
        if net_payout>0:
            c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(net_payout,user_id,group_id))
        c.execute("INSERT INTO casino_games(game_id,group_id,status,result,settings,ended_at) VALUES('roulette',%s,'closed',%s,%s,NOW())",
                  (group_id,str(srv_result),json.dumps({'amount':amount,'betType':bet_type,'betValue':str(bet_value),'payout':net_payout})))
        db.commit()
        add_daily_bet(user_id,group_id,amount)
        update_mission(user_id,group_id,'play3')
        if srv_won: update_mission(user_id,group_id,'win1')
        return {'ok':True,'result':srv_result,'won':srv_won,'payout':net_payout},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/casino/bigwheel')
def serve_bigwheel(): return send_from_directory('.','bigwheel.html')

@app.route('/casino/bigwheel/spin', methods=['POST'])
def bigwheel_spin():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); group_id=int(data.get('groupId',0)); user_id=int(data.get('userId',0))
        amount=int(data.get('amount',0))
        if is_casino_blacklisted(group_id,user_id): return {'ok':False,'error':'이용 제한'},403
        settings=get_casino_settings(group_id,'bigwheel')
        segs=settings.get('segments',DEFAULT_CASINO_SETTINGS['bigwheel']['segments'])
        if amount<settings.get('min_bet',10): return {'ok':False,'error':f"최소 {settings['min_bet']:,}P"},400
        if amount>settings.get('max_bet',10000): return {'ok':False,'error':f"최대 {settings['max_bet']:,}P"},400
        if check_daily_limit(user_id,group_id,amount): return {'ok':False,'error':'일일 한도 초과'},400
        c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        pt=c.fetchone()
        if not pt or pt[0]<amount: return {'ok':False,'error':'포인트 부족'},400
        total_prob=sum(s.get('prob',s.get('probability',10)) for s in segs)
        r=random.randint(1,total_prob); acc=0; result_idx=len(segs)-1
        for i,s in enumerate(segs):
            acc+=s.get('prob',s.get('probability',10))
            if r<=acc: result_idx=i; break
        result_seg=segs[result_idx]
        payout=int(amount*result_seg['multiplier']) if result_seg['multiplier']>0 else 0
        net_payout=max(0,payout-int(amount*(settings.get('house_edge',5)/100))) if payout>0 else 0
        c.execute("UPDATE points SET point=point-%s,total_bet=COALESCE(total_bet,0)+%s WHERE user_id=%s AND group_id=%s",
                  (amount,amount,user_id,group_id))
        if net_payout>0:
            c.execute("UPDATE points SET point=point+%s WHERE user_id=%s AND group_id=%s",(net_payout,user_id,group_id))
        c.execute("INSERT INTO casino_games(game_id,group_id,status,result,settings,ended_at) VALUES('bigwheel',%s,'closed',%s,%s,NOW())",
                  (group_id,result_seg['label'],json.dumps(settings)))
        db.commit()
        add_daily_bet(user_id,group_id,amount)
        update_mission(user_id,group_id,'play3')
        if net_payout>0: update_mission(user_id,group_id,'win1')
        return {'ok':True,'resultIdx':result_idx,'result':result_seg,'payout':net_payout},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

# ─────────────────────────────────────────────────────────
# KBO, 내전, 투표 라우트 (기존 유지)
# ─────────────────────────────────────────────────────────
@app.route('/kbo/submit', methods=['POST'])
def kbo_submit():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); user_id=int(data.get('userId')); group_id=int(data.get('groupId'))
        teams=data.get('teams',[]); is_admin_req=data.get('isAdmin',False); admin_user_id=data.get('adminUserId')
        if len(teams)!=5: return {'ok':False,'error':'5개 팀 선택'},400
        if is_admin_req:
            if not admin_user_id or int(admin_user_id) not in ADMIN_IDS:
                return {'ok':False,'error':'관리자 권한 없음'},403
        else:
            if not is_vote_time(datetime.now(KST)):
                return {'ok':False,'error':'참여 가능 시간 아님'},403
        today=datetime.now(KST).date()
        c.execute("SELECT first_name,username FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        row=c.fetchone()
        user_name_from_client=(data.get('userName') or '').strip()
        if user_name_from_client: first_name=clean_name(user_name_from_client); username=row[1] if row else ''
        else:
            first_name=clean_name(row[0]) if row and row[0] else ''
            username=row[1] if row else ''
            if not first_name: first_name=f"@{username}" if username else f"id:{user_id}"
        teams_str=','.join(teams)
        c.execute("SELECT id FROM kbo_votes WHERE user_id=%s AND group_id=%s AND vote_date=%s",(user_id,group_id,today))
        existing=c.fetchone()
        if existing:
            c.execute("UPDATE kbo_votes SET teams=%s,first_name=%s,username=%s WHERE user_id=%s AND group_id=%s AND vote_date=%s",
                      (teams_str,first_name,username,user_id,group_id,today))
            action="수정"
        else:
            c.execute("INSERT INTO kbo_votes(user_id,group_id,first_name,username,teams,vote_date) VALUES(%s,%s,%s,%s,%s,%s)",
                      (user_id,group_id,first_name,username,teams_str,today))
            action="완료"
        c.execute("SELECT COUNT(*) FROM kbo_votes WHERE group_id=%s AND vote_date=%s",(group_id,today))
        total=c.fetchone()[0]; db.commit()
        return {'ok':True,'action':action},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/kbo/list')
def kbo_list():
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0)); today=datetime.now(KST).date()
        c.execute("SELECT user_id,first_name,username,teams FROM kbo_votes WHERE group_id=%s AND vote_date=%s ORDER BY created_at",(group_id,today))
        rows=c.fetchall()
        result=[]
        for r in rows:
            uid=r[0]; first=clean_name(r[1] or ''); uname=r[2] or ''
            name=first if first else (f"@{uname}" if uname else f"id:{uid}")
            result.append({'userId':uid,'name':name,'teams':r[3].split(',')})
        return result,200
    except: return [],500
    finally: c.close();db.close()

@app.route('/kbo/hot')
def kbo_hot():
    db=get_db();c=db.cursor()
    try:
        group_id=int(request.args.get('groupId',0)); today=datetime.now(KST).date()
        c.execute("SELECT teams FROM kbo_votes WHERE group_id=%s AND vote_date=%s",(group_id,today))
        rows=c.fetchall()
        from collections import Counter; cnt=Counter()
        for r in rows:
            for team in r[0].split(','): cnt[team]+=1
        return [{'team':t,'count':v} for t,v in cnt.most_common(3)],200
    except: return [],500
    finally: c.close();db.close()

@app.route('/kbo/my')
def kbo_my():
    db=get_db();c=db.cursor()
    try:
        user_id=int(request.args.get('userId',0)); group_id=int(request.args.get('groupId',0))
        now_kst=datetime.now(KST); today=now_kst.date(); vote_ok=is_vote_time(now_kst)
        c.execute("SELECT first_name,username,teams FROM kbo_votes WHERE user_id=%s AND group_id=%s AND vote_date=%s",(user_id,group_id,today))
        row=c.fetchone()
        if row:
            name=clean_name(row[0]) if row[0] else (f"@{row[1]}" if row[1] else f"id:{user_id}")
            return {'voted':True,'name':name,'teams':row[2].split(','),'isVoteTime':vote_ok},200
        return {'voted':False,'isVoteTime':vote_ok},200
    except Exception as e: return {'voted':False,'isVoteTime':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/naejeon/check_admin')
def naejeon_check_admin():
    try:
        user_id=int(request.args.get('userId',0))
        return {'isAdmin':user_id in ADMIN_IDS},200
    except: return {'isAdmin':False},200

@app.route('/naejeon/room')
def naejeon_room():
    db=get_db();c=db.cursor()
    try:
        room_id=request.args.get('roomId')
        c.execute("SELECT game_type,slots,status,extra_text,pos_a,pos_b,started,fund_type,fund_amount FROM naejeon_rooms WHERE room_id=%s",(room_id,))
        row=c.fetchone()
        if not row: return {'error':'방 없음'},404
        c.execute("SELECT end_time,winner_count,reward_text,is_active FROM naejeon_events WHERE room_id=%s",(room_id,))
        ev=c.fetchone()
        event_data=None
        if ev and ev[3]:
            event_data={'endTime':to_utc_iso(ev[0]),'winnerCount':ev[1],'rewardText':ev[2]}
        return {'gameType':row[0],'slots':row[1] or {},'status':row[2],'extraText':row[3] or '',
                'posA':row[4] or [],'posB':row[5] or [],'started':bool(row[6]),
                'fundType':row[7] or '','fundAmount':row[8] or '','event':event_data},200
    except Exception as e: return {'error':str(e)},500
    finally: c.close();db.close()

@app.route('/naejeon/join', methods=['POST'])
def naejeon_join():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); room_id=data.get('roomId')
        user_id=int(data.get('userId')); group_id=int(data.get('groupId'))
        team=data.get('team'); pos_id=data.get('posId'); pos_label=data.get('posLabel')
        c.execute("SELECT game_type,slots,status FROM naejeon_rooms WHERE room_id=%s FOR UPDATE",(room_id,))
        row=c.fetchone()
        if not row: return {'ok':False,'error':'방 없음'},404
        if row[2]!='open': return {'ok':False,'error':'마감됨'},400
        slots=row[1] if row[1] else {}; game_type=row[0]; slot_key=f"{team}_{pos_id}"
        for k,v in slots.items():
            if v and str(v.get('userId'))==str(user_id): return {'ok':False,'error':'이미 참여'},400
        if slots.get(slot_key): return {'ok':False,'error':'이미 선택된 포지션'},400
        c.execute("SELECT first_name,username FROM points WHERE user_id=%s AND group_id=%s",(user_id,group_id))
        ur=c.fetchone()
        name=clean_name(ur[0]) if ur and ur[0] else (f"@{ur[1]}" if ur and ur[1] else f"id:{user_id}")
        slots[slot_key]={'userId':user_id,'name':name,'posLabel':pos_label,'team':team}
        total={'lol':10,'sa5':10,'sa6':12}.get(game_type,10)
        filled=len([v for v in slots.values() if v])
        status='closed' if filled>=total else 'open'
        c.execute("UPDATE naejeon_rooms SET slots=%s,status=%s WHERE room_id=%s",(json.dumps(slots),status,room_id))
        db.commit()
        if status=='closed': _send_naejeon_result(group_id,game_type,slots)
        c.execute("SELECT game_type,slots,status,extra_text,pos_a,pos_b,started,fund_type,fund_amount FROM naejeon_rooms WHERE room_id=%s",(room_id,))
        row2=c.fetchone()
        return {'ok':True,'room':{'gameType':row2[0],'slots':row2[1] or {},'status':row2[2],
            'extraText':row2[3] or '','posA':row2[4] or [],'posB':row2[5] or [],
            'started':bool(row2[6]),'fundType':row2[7] or '','fundAmount':row2[8] or ''}},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/naejeon/leave', methods=['POST'])
def naejeon_leave():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); room_id=data.get('roomId'); user_id=int(data.get('userId'))
        c.execute("SELECT game_type,slots,status FROM naejeon_rooms WHERE room_id=%s FOR UPDATE",(room_id,))
        row=c.fetchone()
        if not row: return {'ok':False,'error':'방 없음'},404
        slots=row[1] if row[1] else {}; updated=False
        for k,v in list(slots.items()):
            if v and str(v.get('userId'))==str(user_id):
                slots[k]=None; updated=True; break
        if not updated: return {'ok':False,'error':'참여 기록 없음'},400
        c.execute("UPDATE naejeon_rooms SET slots=%s,status='open' WHERE room_id=%s",(json.dumps(slots),room_id))
        db.commit()
        c.execute("SELECT game_type,slots,status,extra_text,pos_a,pos_b,started,fund_type,fund_amount FROM naejeon_rooms WHERE room_id=%s",(room_id,))
        row2=c.fetchone()
        return {'ok':True,'room':{'gameType':row2[0],'slots':row2[1] or {},'status':row2[2],
            'extraText':row2[3] or '','posA':row2[4] or [],'posB':row2[5] or [],
            'started':bool(row2[6]),'fundType':row2[7] or '','fundAmount':row2[8] or ''}},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/naejeon/cancel', methods=['POST'])
def naejeon_cancel():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); room_id=data.get('roomId')
        user_id=int(data.get('userId',0)); group_id=int(data.get('groupId',0))
        if user_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        c.execute("UPDATE naejeon_rooms SET status='cancelled' WHERE room_id=%s AND group_id=%s",(room_id,group_id))
        affected=c.rowcount; db.commit()
        return ({'ok':True},200) if affected>0 else ({'ok':False,'error':'방 없음'},404)
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/naejeon/setup', methods=['POST'])
def naejeon_setup():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); room_id=data.get('roomId')
        user_id=int(data.get('userId')); group_id=int(data.get('groupId'))
        game_type=data.get('gameType'); extra_text=data.get('extraText','')
        pos_a=data.get('posA',[]); pos_b=data.get('posB',[])
        fund_type=data.get('fundType',''); fund_amount=data.get('fundAmount','')
        if user_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        c.execute("UPDATE naejeon_rooms SET extra_text=%s,pos_a=%s,pos_b=%s,started=TRUE,fund_type=%s,fund_amount=%s WHERE room_id=%s",
            (extra_text,json.dumps(pos_a),json.dumps(pos_b),fund_type,fund_amount,room_id))
        db.commit()
        param=f"{user_id}_{group_id}_{game_type}_{room_id}"
        nj_url=f"{WEBAPP_BASE_URL}/naejeon?start={param}"
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚔️ 내전 바로가기",url=nj_url))
        bot.send_message(group_id,f"⚙️ 내전 설정 변경!\n👉 <a href='{nj_url}'>[내전 현황 보기]</a>",
                         reply_markup=markup,parse_mode='HTML')
        c.execute("SELECT game_type,slots,status,extra_text,pos_a,pos_b,started,fund_type,fund_amount FROM naejeon_rooms WHERE room_id=%s",(room_id,))
        row2=c.fetchone()
        return {'ok':True,'room':{'gameType':row2[0],'slots':row2[1] or {},'status':row2[2],
            'extraText':row2[3] or '','posA':row2[4] or [],'posB':row2[5] or [],
            'started':bool(row2[6]),'fundType':row2[7] or '','fundAmount':row2[8] or ''}},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/naejeon/admin_add', methods=['POST'])
def naejeon_admin_add():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); room_id=data.get('roomId')
        user_id=int(data.get('userId')); group_id=int(data.get('groupId'))
        slot_key=data.get('slotKey'); name=data.get('name','').strip()
        if user_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        if not name: return {'ok':False,'error':'이름 입력'},400
        c.execute("SELECT game_type,slots,status FROM naejeon_rooms WHERE room_id=%s FOR UPDATE",(room_id,))
        row=c.fetchone()
        if not row: return {'ok':False,'error':'방 없음'},404
        slots=row[1] if row[1] else {}
        slots[slot_key]={'userId':f'admin_{uuid.uuid4().hex[:6]}','name':name,'team':slot_key.split('_')[0]}
        total={'lol':10,'sa5':10,'sa6':12}.get(row[0],10)
        filled=len([v for v in slots.values() if v and v.get('userId')])
        status='closed' if filled>=total else 'open'
        c.execute("UPDATE naejeon_rooms SET slots=%s,status=%s WHERE room_id=%s",(json.dumps(slots),status,room_id))
        db.commit()
        if status=='closed': _send_naejeon_result(group_id,row[0],slots)
        c.execute("SELECT game_type,slots,status,extra_text,pos_a,pos_b,started,fund_type,fund_amount FROM naejeon_rooms WHERE room_id=%s",(room_id,))
        row2=c.fetchone()
        return {'ok':True,'room':{'gameType':row2[0],'slots':row2[1] or {},'status':row2[2],
            'extraText':row2[3] or '','posA':row2[4] or [],'posB':row2[5] or [],
            'started':bool(row2[6]),'fundType':row2[7] or '','fundAmount':row2[8] or ''}},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/naejeon/admin_remove', methods=['POST'])
def naejeon_admin_remove():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); room_id=data.get('roomId')
        user_id=int(data.get('userId')); slot_key=data.get('slotKey')
        if user_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        c.execute("SELECT game_type,slots FROM naejeon_rooms WHERE room_id=%s FOR UPDATE",(room_id,))
        row=c.fetchone()
        if not row: return {'ok':False,'error':'방 없음'},404
        slots=row[1] if row[1] else {}
        if slot_key in slots: slots[slot_key]=None
        c.execute("UPDATE naejeon_rooms SET slots=%s,status='open' WHERE room_id=%s",(json.dumps(slots),room_id))
        db.commit()
        c.execute("SELECT game_type,slots,status,extra_text,pos_a,pos_b,started,fund_type,fund_amount FROM naejeon_rooms WHERE room_id=%s",(room_id,))
        row2=c.fetchone()
        return {'ok':True,'room':{'gameType':row2[0],'slots':row2[1] or {},'status':row2[2],
            'extraText':row2[3] or '','posA':row2[4] or [],'posB':row2[5] or [],
            'started':bool(row2[6]),'fundType':row2[7] or '','fundAmount':row2[8] or ''}},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/naejeon/start_event', methods=['POST'])
def start_event():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); room_id=data.get('roomId')
        user_id=int(data.get('userId')); group_id=int(data.get('groupId'))
        mins=int(data.get('mins',5)); winners=int(data.get('winners',1)); reward=data.get('reward','').strip()
        if user_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        if not reward: return {'ok':False,'error':'보상 입력'},400
        end_time=datetime.now(UTC)+timedelta(minutes=mins)
        c.execute("""INSERT INTO naejeon_events(room_id,end_time,winner_count,reward_text,is_active)
            VALUES(%s,%s,%s,%s,TRUE) ON CONFLICT(room_id) DO UPDATE SET
            end_time=%s,winner_count=%s,reward_text=%s,is_active=TRUE""",
            (room_id,end_time,winners,reward,end_time,winners,reward))
        db.commit()
        return {'ok':True},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/naejeon/finish_event', methods=['POST'])
def finish_event():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); room_id=data.get('roomId')
        c.execute("SELECT is_active,winner_count,reward_text FROM naejeon_events WHERE room_id=%s",(room_id,))
        ev=c.fetchone()
        if not ev or not ev[0]: return {'ok':False,'error':'이미 종료'},400
        winner_count,reward_text=ev[1],ev[2]
        c.execute("SELECT group_id,slots FROM naejeon_rooms WHERE room_id=%s",(room_id,))
        room=c.fetchone()
        if not room: return {'ok':False,'error':'방 없음'},404
        group_id,slots=room[0],room[1]
        candidates=[v.get('name','익명') for k,v in slots.items() if v and v.get('userId') and not str(v.get('userId')).startswith('admin_')]
        winners=random.sample(candidates,min(len(candidates),winner_count)) if candidates else []
        c.execute("UPDATE naejeon_events SET is_active=FALSE WHERE room_id=%s",(room_id,)); db.commit()
        return {'ok':True,'winners':winners},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

def _send_naejeon_result(group_id,game_type,slots):
    pos_order={'lol':['top','jg','mid','adc','sup'],'sa5':['sna','rfl1','rfl2','rfl3','rfl4'],'sa6':['sna1','sna2','rfl1','rfl2','rfl3','rfl4']}.get(game_type,[])
    pos_labels={'top':'탑','jg':'정글','mid':'미드','adc':'원딜','sup':'서폿','sna':'스나','sna1':'스나1','sna2':'스나2','rfl1':'라플1','rfl2':'라플2','rfl3':'라플3','rfl4':'라플4'}
    game_names={'lol':'LoL 5v5','sa5':'서든 5v5','sa6':'서든 6v6'}
    result=f"⚔️ {game_names.get(game_type,'')} 내전 완료!\n\n"
    for team_id,label in [('A','🟣 1팀'),('B','🟢 2팀')]:
        result+=f"{label}\n"
        for pos in pos_order:
            slot=slots.get(f"{team_id}_{pos}")
            result+=f"   [{pos_labels.get(pos,pos)}] {slot['name'] if (slot and slot.get('userId')) else '비어있음'}\n"
        result+="\n"
    try: bot.send_message(group_id,result)
    except: pass

# 투표 라우트
@app.route('/vote/room')
def vote_room():
    db=get_db();c=db.cursor()
    try:
        room_id=request.args.get('roomId')
        c.execute("SELECT room_id,group_id,content,mins,winners,anim_style,started,ended,end_time FROM vote_rooms WHERE room_id=%s",(room_id,))
        row=c.fetchone()
        if not row: return {'error':'이벤트 없음'},404
        c.execute("SELECT user_id,name FROM vote_participants WHERE room_id=%s ORDER BY joined_at",(room_id,))
        parts=[{'userId':r[0],'name':r[1]} for r in c.fetchall()]
        return {'roomId':row[0],'groupId':row[1],'content':row[2] or '','mins':row[3],'winners':row[4],
                'animStyle':row[5] or 'slot','started':bool(row[6]),'ended':bool(row[7]),
                'endTime':to_utc_iso(row[8]),'participants':parts},200
    except Exception as e: return {'error':str(e)},500
    finally: c.close();db.close()

@app.route('/vote/start', methods=['POST'])
def vote_start():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); room_id=data.get('roomId')
        user_id=int(data.get('userId')); group_id=int(data.get('groupId'))
        content=data.get('content','').strip(); anim_style=data.get('animStyle','slot')
        winners=int(data.get('winners',1)); mins=safe_mins(data.get('mins'))
        if user_id not in ADMIN_IDS: return {'ok':False,'error':'관리자 전용'},403
        if not content: return {'ok':False,'error':'이벤트 내용 입력'},400
        end_time=datetime.now(UTC)+timedelta(minutes=mins) if mins else None
        c.execute("""UPDATE vote_rooms SET content=%s,mins=%s,winners=%s,anim_style=%s,started=TRUE,ended=FALSE,end_time=%s
            WHERE room_id=%s""",(content,mins,winners,anim_style,end_time,room_id))
        if c.rowcount==0: return {'ok':False,'error':'room 없음'},404
        db.commit()
        param=f"{user_id}|{group_id}|{room_id}"
        vote_url=f"{WEBAPP_BASE_URL}/vote?start={param}"
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🙋 이벤트 참여하기",url=vote_url))
        bot.send_message(group_id,f"🎰 이벤트 시작!\n📢 {content}",reply_markup=markup,parse_mode='HTML')
        return {'ok':True},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/vote/join', methods=['POST'])
def vote_join():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); room_id=data.get('roomId')
        user_id=int(data.get('userId')); group_id=int(data.get('groupId'))
        user_name_from_client=(data.get('userName') or '').strip()
        c.execute("SELECT started,ended FROM vote_rooms WHERE room_id=%s",(room_id,))
        row=c.fetchone()
        if not row: return {'ok':False,'error':'이벤트 없음'},404
        if not row[0]: return {'ok':False,'error':'미시작'},400
        if row[1]: return {'ok':False,'error':'종료됨'},400
        name=clean_name(user_name_from_client) if user_name_from_client else None
        if not name:
            c.execute("SELECT first_name,username FROM points WHERE user_id=%s ORDER BY id DESC LIMIT 1",(user_id,))
            ur=c.fetchone()
            if ur and ur[0]: name=clean_name(ur[0])
            elif ur and ur[1]: name=f"@{ur[1]}"
        if not name: name=f"id:{user_id}"
        c.execute("INSERT INTO vote_participants(room_id,user_id,name) VALUES(%s,%s,%s) ON CONFLICT(room_id,user_id) DO NOTHING",(room_id,user_id,name))
        db.commit()
        c.execute("SELECT user_id,name FROM vote_participants WHERE room_id=%s ORDER BY joined_at",(room_id,))
        parts=[{'userId':r[0],'name':r[1]} for r in c.fetchall()]
        return {'ok':True,'participants':parts},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/vote/leave', methods=['POST'])
def vote_leave():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); room_id=data.get('roomId'); user_id=int(data.get('userId'))
        c.execute("SELECT ended FROM vote_rooms WHERE room_id=%s",(room_id,))
        row=c.fetchone()
        if not row or row[0]: return {'ok':False,'error':'취소 불가'},400
        c.execute("DELETE FROM vote_participants WHERE room_id=%s AND user_id=%s",(room_id,user_id)); db.commit()
        c.execute("SELECT user_id,name FROM vote_participants WHERE room_id=%s ORDER BY joined_at",(room_id,))
        parts=[{'userId':r[0],'name':r[1]} for r in c.fetchall()]
        return {'ok':True,'participants':parts},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

@app.route('/vote/draw', methods=['POST'])
def vote_draw():
    db=get_db();c=db.cursor()
    try:
        data=request.get_json(); room_id=data.get('roomId')
        c.execute("SELECT group_id,content,winners,anim_style,ended FROM vote_rooms WHERE room_id=%s",(room_id,))
        row=c.fetchone()
        if not row: return {'ok':False,'error':'이벤트 없음'},404
        if row[4]: return {'ok':False,'error':'이미 추첨됨'},400
        group_id,content,winner_count,anim_style=row[0],row[1],row[2],row[3]
        c.execute("SELECT user_id,name FROM vote_participants WHERE room_id=%s ORDER BY joined_at",(room_id,))
        parts=[{'userId':r[0],'name':r[1]} for r in c.fetchall()]
        winners=[]
        if parts:
            shuffled=parts.copy(); random.shuffle(shuffled)
            winners=[p['name'] for p in shuffled[:min(winner_count,len(shuffled))]]
        c.execute("UPDATE vote_rooms SET ended=TRUE WHERE room_id=%s",(room_id,)); db.commit()
        return {'ok':True,'winners':winners,'animStyle':anim_style,'content':content,'participants':parts},200
    except Exception as e: return {'ok':False,'error':str(e)},500
    finally: c.close();db.close()

# ─────────────────────────────────────────────────────────
# Webhook & 메인
# ─────────────────────────────────────────────────────────
@app.route('/'+BOT_TOKEN, methods=['POST'])
def webhook():
    try:
        json_str=request.stream.read().decode('utf-8')
        update=telebot.types.Update.de_json(json_str)
        if update.message: handle_all(update.message)
        elif update.callback_query:
            if update.callback_query.data.startswith('kbo_'): handle_kbo_callback(update.callback_query)
            elif update.callback_query.data.startswith('nj_open:'): handle_nj_open(update.callback_query)
    except Exception as e:
        import traceback; print(f"webhook error: {e}\n{traceback.format_exc()}")
    return 'OK',200

@app.route('/')
def index(): return 'Bot is running!',200

# ─────────────────────────────────────────────────────────
# 스케줄러 시작
# ─────────────────────────────────────────────────────────
def start_scheduler():
    scheduler=BackgroundScheduler(timezone=UTC)
    # 30초마다 체크 (3분 라운드 정밀도 확보)
    scheduler.add_job(auto_race_round, 'interval', seconds=30, id='auto_race')
    scheduler.add_job(auto_horse_round,'interval', seconds=30, id='auto_horse')
    scheduler.start()
    print("✅ 스케줄러 시작")

try:
    init_db()
    print("✅ DB 초기화 성공")
except Exception as e:
    print(f"❌ DB init error: {e}")

if __name__=='__main__':
    start_scheduler()
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)))
else:
    # gunicorn 등 외부 서버 사용 시
    start_scheduler()
