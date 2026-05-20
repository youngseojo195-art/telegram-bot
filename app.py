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

# ─────────────────────────────────────────────────────────
# 관리자 설정
# ─────────────────────────────────────────────────────────
ADMIN_IDS = [8698678650, 8236798970]

# ─────────────────────────────────────────────────────────
# GIF 설정
# ─────────────────────────────────────────────────────────
BASEBALL_GIF_FILE_ID = "CgACAgUAAxkBAAMzagl3svn3G8Jr7JDeNhdXbodfQnIAAi8dAAJux0hUOyDPUXIJtRs7BA"
NAEJEON_GIF_FILE_ID  = "CgACAgUAAxkBAAOGag0cXgdCIn_PggmqSmC0GM0GnC4AAkofAAKWbGhUMjetimSM_S47BA"
AFFILIATE_GIF_URL    = "CgACAgUAAxkBAAM4agmS7OD4fz1bxh5zNQPn8VNCpysAAmYdAAJux0hUYXAsQb02yzs7BA"

def send_baseball_gif(chat_id):
    if not BASEBALL_GIF_FILE_ID:
        return
    try:
        bot.send_animation(chat_id=chat_id, animation=BASEBALL_GIF_FILE_ID)
    except Exception as e:
        print(f"야구 GIF 전송 실패: {e}")

def send_naejeon_gif(chat_id):
    if not NAEJEON_GIF_FILE_ID:
        return
    try:
        bot.send_animation(chat_id=chat_id, animation=NAEJEON_GIF_FILE_ID)
    except Exception as e:
        print(f"내전 GIF 전송 실패: {e}")

def send_affiliate_gif(chat_id):
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
<b>[평생]</b> · <a href="https://t.me/spd1588/84">스피드벳</a>
<b>[평생]</b> · <a href="https://t.me/Gwaedwaji/15">띵벳</a>
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

WEBAPP_BASE_URL = os.environ.get('WEBAPP_URL', 'https://telegram-bot-14vg.onrender.com')

VOTE_START = "18:00"
VOTE_END   = "18:30"


# ─────────────────────────────────────────────────────────
# KBO 인라인 키보드 빌더
# ─────────────────────────────────────────────────────────
def build_team_keyboard(selected: list) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for team in KBO_TEAMS:
        label = f"✅ {team}" if team in selected else KBO_TEAMS_DISPLAY.get(team, team)
        buttons.append(types.InlineKeyboardButton(
            text=label, callback_data=f"kbo_toggle:{team}"
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
        lines.append(f"   • {KBO_TEAMS_DISPLAY.get(t, t)}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────
# DB 헬퍼
# ─────────────────────────────────────────────────────────
def clean_name(name):
    if not name:
        return ''
    cleaned = (name.strip()
               .replace('\u3164', '').replace('\u200b', '')
               .replace('\u200c', '').replace('\u200d', '')
               .replace('\ufeff', '').strip())
    return cleaned

def get_db():
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

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
            created_at TIMESTAMP DEFAULT NOW()
        )""")
        
        for col in [
            ("extra_text",  "TEXT DEFAULT ''"),
            ("pos_a",       "JSONB DEFAULT '[]'"),
            ("pos_b",       "JSONB DEFAULT '[]'"),
            ("started",     "BOOLEAN DEFAULT FALSE"),
            ("fund_type",   "VARCHAR(10) DEFAULT ''"),
            ("fund_amount", "TEXT DEFAULT ''"),
        ]:
            try:
                c.execute(f"ALTER TABLE naejeon_rooms ADD COLUMN IF NOT EXISTS {col[0]} {col[1]}")
                db.commit()
            except:
                db.rollback()
        try:
            c.execute("ALTER TABLE points ALTER COLUMN last_attendance TYPE DATE USING last_attendance::DATE")
            db.commit()
        except:
            db.rollback()
        db.commit()
    finally:
        c.close(); db.close()

def get_point(user_id, group_id):
    db = get_db(); c = db.cursor()
    try:
        c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
        row = c.fetchone()
        return row[0] if row else 0
    finally:
        c.close(); db.close()

def update_point(user_id, group_id, first_name, username, amount):
    db = get_db(); c = db.cursor()
    try:
        c.execute("""INSERT INTO points (user_id, group_id, first_name, username, point)
            VALUES (%s,%s,%s,%s,%s) ON CONFLICT (user_id, group_id)
            DO UPDATE SET point=points.point+%s, first_name=%s, username=%s""",
            (user_id, group_id, first_name, username, amount, amount, first_name, username))
        db.commit()
    finally:
        c.close(); db.close()

def save_message(user_id, username, first_name, group_id):
    db = get_db(); c = db.cursor()
    try:
        c.execute("INSERT INTO chat_logs (user_id,username,first_name,group_id,message_date) VALUES (%s,%s,%s,%s,%s)",
                  (user_id, username, first_name, group_id, datetime.now()))
        db.commit()
    finally:
        c.close(); db.close()

def get_pending(user_id, group_id):
    db = get_db(); c = db.cursor()
    try:
        c.execute("SELECT selected, message_id FROM kbo_pending WHERE user_id=%s AND group_id=%s", (user_id, group_id))
        row = c.fetchone()
        if row:
            return ([t for t in row[0].split(',') if t], row[1])
        return ([], None)
    finally:
        c.close(); db.close()

def get_pending_with_group(user_id):
    db = get_db(); c = db.cursor()
    try:
        c.execute("SELECT group_id, selected, message_id FROM kbo_pending WHERE user_id=%s LIMIT 1", (user_id,))
        row = c.fetchone()
        if row:
            group_id = row[0]
            selected = [t for t in row[1].split(',') if t]
            msg_id   = row[2]
            return (group_id, selected), msg_id
        return None, None
    finally:
        c.close(); db.close()

def set_pending(user_id, group_id, selected: list, message_id=None):
    db = get_db(); c = db.cursor()
    try:
        s = ','.join(selected)
        c.execute("""INSERT INTO kbo_pending (user_id, group_id, selected, message_id)
            VALUES (%s,%s,%s,%s) ON CONFLICT (user_id, group_id)
            DO UPDATE SET selected=%s, message_id=%s""",
            (user_id, group_id, s, message_id, s, message_id))
        db.commit()
    finally:
        c.close(); db.close()

def clear_pending(user_id, group_id):
    db = get_db(); c = db.cursor()
    try:
        c.execute("DELETE FROM kbo_pending WHERE user_id=%s AND group_id=%s", (user_id, group_id))
        db.commit()
    finally:
        c.close(); db.close()

def is_vote_time(now_kst):
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
    except:
        pass
    try:
        r = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=USDTKRW', timeout=5)
        if r.status_code == 200:
            return float(r.json()['price'])
    except:
        pass
    return None


# ─────────────────────────────────────────────────────────
# 내전 서든 모드 선택 콜백
# ─────────────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda call: call.data.startswith('nj_open:'))
def handle_nj_open(call):
    try:
        user_id    = call.from_user.id
        group_id   = call.message.chat.id

        if user_id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "⚠️ 관리자만 사용할 수 있어요!", show_alert=True)
            return

        parts      = call.data.split(':', 2)
        game_type  = parts[1]
        extra_text = parts[2] if len(parts) > 2 else ''

        game_names   = {'sa5': '서든어택 5v5', 'sa6': '서든어택 6v6'}
        display_name = game_names.get(game_type, '서든어택')

        db = get_db(); c = db.cursor()
        try:
            c.execute("SELECT room_id FROM naejeon_rooms WHERE group_id=%s AND game_type=%s AND status='open'",
                      (group_id, game_type))
            existing = c.fetchone()
            if existing:
                bot.answer_callback_query(call.id, "⚠️ 이미 진행 중인 내전이 있어요!", show_alert=True)
                return

            room_id = str(uuid.uuid4())[:8]
            c.execute("INSERT INTO naejeon_rooms (room_id, group_id, game_type, slots, extra_text) VALUES (%s,%s,%s,%s,%s)",
                      (room_id, group_id, game_type, '{}', extra_text))
            db.commit()
        finally:
            c.close(); db.close()

        param  = f"{user_id}_{group_id}_{game_type}_{room_id}"
        nj_url = f"{WEBAPP_BASE_URL}/naejeon?start={param}"

        group_msg = f"⚔️ {display_name} 내전 모집!"
        if extra_text:
            group_msg += f"\n{extra_text}"
        group_msg += f"\n\n아래 버튼을 눌러 참여하세요!\n⚠️ 처음 참여하시는 분은 @dopamin_ranking_bot 을 눌러 START 를 먼저 눌러주세요!"

        send_naejeon_gif(group_id)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚔️ 내전 참여하기", url=nj_url))
        bot.edit_message_text(group_msg, chat_id=group_id, message_id=call.message.message_id, reply_markup=markup)
        bot.answer_callback_query(call.id, f"✅ {display_name} 내전 시작!")

    except Exception as e:
        import traceback
        print(f"nj_open error: {e}\n{traceback.format_exc()}")
        bot.answer_callback_query(call.id, "오류가 발생했어요.")


# ─────────────────────────────────────────────────────────
# KBO 콜백 핸들러
# ─────────────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda call: call.data.startswith('kbo_'))
def handle_kbo_callback(call):
    try:
        user_id    = call.from_user.id
        first_name = call.from_user.first_name or '사용자'
        username   = call.from_user.username or ''
        now_kst    = datetime.now(KST)
        today      = now_kst.date()
        action     = call.data

        if not is_vote_time(now_kst):
            bot.answer_callback_query(call.id,
                f"⏰ 화~금 {VOTE_START}~{VOTE_END} 사이에만 참여 가능해요!", show_alert=True)
            return

        selected, msg_id = get_pending_with_group(user_id)
        if selected is None:
            bot.answer_callback_query(call.id, "⚠️ 세션이 만료됐어요. 그룹에서 /승 을 다시 입력해주세요.", show_alert=True)
            return
        group_id = selected[0]
        selected = selected[1]

        db = get_db(); c = db.cursor()
        try:
            c.execute("SELECT teams FROM kbo_votes WHERE user_id=%s AND group_id=%s AND vote_date=%s",
                      (user_id, group_id, today))
            already = c.fetchone()
        finally:
            c.close(); db.close()

        if action == "kbo_noop":
            if already:
                bot.answer_callback_query(call.id, "이미 제출하셨어요! 수정하려면 /수정 을 사용하세요.")
            else:
                bot.answer_callback_query(call.id, f"5개를 선택해야 제출할 수 있어요! (현재 {len(selected)}개)")
            return

        elif action == "kbo_reset":
            selected = []
            set_pending(user_id, group_id, selected, call.message.message_id)
            bot.edit_message_text(
                chat_id=user_id, message_id=call.message.message_id,
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
                chat_id=user_id, message_id=call.message.message_id,
                text=build_vote_message(selected),
                reply_markup=build_team_keyboard(selected)
            )

        elif action == "kbo_submit":
            if len(selected) != 5:
                bot.answer_callback_query(call.id, "5개를 선택해야 제출할 수 있어요!", show_alert=True)
                return
            teams_str = ','.join(selected)
            db = get_db(); c = db.cursor()
            try:
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
                db.commit()
            finally:
                c.close(); db.close()
                
            clear_pending(user_id, group_id)
            team_display = "\n".join([f"   {i+1}. {KBO_TEAMS_DISPLAY.get(t,t)}" for i, t in enumerate(selected)])
            bot.edit_message_text(
                chat_id=user_id, message_id=call.message.message_id,
                text=(
                    f"╔══ ⚾ KBO 승 {action_label} ══╗\n"
                    f"   👤 {first_name}님\n\n"
                    f"   선택한 팀 (5개):\n{team_display}\n\n"
                    f"   👥 오늘 참여자: {total}명\n"
                    f"   ✏️ 수정: 그룹에서 /수정 입력\n"
                    f"╚══════════════════╝"
                ),
                reply_markup=None
            )
            bot.answer_callback_query(call.id, f"✅ {action_label}!")

    except Exception as e:
        import traceback
        print(f"kbo callback error: {e}\n{traceback.format_exc()}")
        bot.answer_callback_query(call.id, "오류가 발생했어요. 다시 시도해주세요.")


# ─────────────────────────────────────────────────────────
# 메시지 핸들러
# ─────────────────────────────────────────────────────────
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    try:
        text       = message.text or ''
        user_id    = message.from_user.id
        group_id   = message.chat.id
        first_name = message.from_user.first_name or '사용자'
        username   = message.from_user.username or ''
        now_kst    = datetime.now(KST)
        today      = now_kst.date()

        # ── /test ──
        if '/test' in text:
            bot.reply_to(message, f"봇 작동 중! ✅\n내 user_id: {user_id}")

        # ── /포인트복구 (관리자) ──
        elif '/포인트복구' in text:
            if user_id not in ADMIN_IDS:
                bot.reply_to(message, "⚠️ 관리자만 사용할 수 있어요!"); return
            db = get_db(); c = db.cursor()
            try:
                c.execute("SELECT user_id, first_name, username, point FROM points WHERE group_id=%s ORDER BY point DESC", (group_id,))
                rows = c.fetchall()
            finally:
                c.close(); db.close()
            if not rows:
                bot.reply_to(message, "포인트 기록이 없어요."); return
            result = "╔══ 🔧 포인트 현황 ══╗\n\n"
            for row in rows:
                name = row[1] or row[2] or "익명"
                result += f"   • {name} (id:{row[0]}): {row[3]:,}P\n"
            result += "\n   ` 포인트 설정:\n"
            result += "   /포인트설정 [이름] [포인트]\n"
            result += "   /전체포인트초기화 확인\n"
            result += "╚══════════════════╝"
            bot.reply_to(message, result)

        # ── /포인트설정 (관리자) ──
        elif '/포인트설정' in text:
            if user_id not in ADMIN_IDS:
                bot.reply_to(message, "⚠️ 관리자만 사용할 수 있어요!"); return
            parts = text.split()
            if len(parts) < 3 or not parts[2].isdigit():
                bot.reply_to(message, "🔧 사용법: /포인트설정 [이름] [포인트]\n예: /포인트설정 홍길동 500"); return
            target_name = parts[1]
            new_pt = int(parts[2])
            db = get_db(); c = db.cursor()
            try:
                c.execute("UPDATE points SET point=%s WHERE first_name=%s AND group_id=%s", (new_pt, target_name, group_id))
                affected = c.rowcount
                db.commit()
            finally:
                c.close(); db.close()
            if affected > 0:
                bot.reply_to(message, f"✅ {target_name}님 포인트를 {new_pt:,}P로 설정했어요!")
            else:
                bot.reply_to(message, f"⚠️ {target_name}님을 찾을 수 없어요!")

        # ── /전체포인트초기화 (관리자) ──
        elif '/전체포인트초기화' in text:
            if user_id not in ADMIN_IDS:
                bot.reply_to(message, "⚠️ 관리자만 사용할 수 있어요!"); return
            if '확인' not in text:
                bot.reply_to(message, "⚠️ 정말 전체 포인트를 초기화하려면\n/전체포인트초기화 확인\n이라고 입력하세요!"); return
            db = get_db(); c = db.cursor()
            try:
                c.execute("UPDATE points SET point=0 WHERE group_id=%s", (group_id,))
                affected = c.rowcount
                db.commit()
            finally:
                c.close(); db.close()
            bot.reply_to(message, f"✅ {affected}명의 포인트를 전체 초기화했어요!")

        # ── /getfileid ──
        elif '/getfileid' in text:
            if message.reply_to_message:
                msg = message.reply_to_message
                file_id = None
                if msg.animation:  file_id = msg.animation.file_id
                elif msg.video:    file_id = msg.video.file_id
                elif msg.document: file_id = msg.document.file_id
                if file_id:
                    bot.reply_to(message, f"📋 file_id:\n\n<code>{file_id}</code>\n\nbot.py 상단 변수에 넣으세요!", parse_mode='HTML')
                else:
                    bot.reply_to(message, "⚠️ GIF나 영상 메시지에 답장해서 사용하세요.")
            else:
                bot.reply_to(message, "GIF/영상 메시지에 답장으로 /getfileid 를 입력하세요!")

        # ── /노래 ──
        elif '/노래' in text:
            query = text.replace('/노래', '').strip()
            if not query:
                bot.reply_to(message, "🎵 검색어를 입력해주세요!\n예시: /노래 아이유 좋은날"); return
            encoded = urllib.parse.quote(query)
            bot.reply_to(message, f"🎵 {query}\n\n🔗 유튜브:\nhttps://www.youtube.com/results?search_query={encoded}")

        # ── /제휴 ──
        elif '/제휴' in text:
            send_affiliate_gif(group_id)
            bot.reply_to(message, AFFILIATE_TEXT, parse_mode='HTML', disable_web_page_preview=True)

        # ── 테더 환율 ──
        elif re.search(r'(\d+(\.\d+)?)\s*테더', text):
            match = re.search(r'(\d+(\.\d+)?)\s*테더', text)
            amount = float(match.group(1))
            rate = get_usdt_rate()
            if rate is None:
                bot.reply_to(message, "⚠️ 환율 정보를 가져오지 못했어요."); return
            bot.reply_to(message, f"💰 USDT 환율 계산\n\n📈 현재 환율: {rate:,.0f}원\n💵 {amount:,.0f} USDT: {amount * rate:,.0f}원")

        # ── /출석 ──
        elif '/출석' in text:
            if message.chat.type == 'private': return
            db = get_db(); c = db.cursor()
            try:
                c.execute("SELECT last_attendance FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
                row = c.fetchone()
                if row and row[0] == today:
                    bot.reply_to(message, "⏰ 오늘 이미 출석했어요!\n자정이 지나면 다시 출석할 수 있어요 😊"); return
                c.execute("""INSERT INTO points (user_id,group_id,first_name,username,point,last_attendance)
                    VALUES (%s,%s,%s,%s,100,%s) ON CONFLICT (user_id,group_id)
                    DO UPDATE SET point=points.point+100, last_attendance=%s, first_name=%s, username=%s""",
                    (user_id, group_id, first_name, username, today, today, first_name, username))
                db.commit()
                c.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
                total = c.fetchone()[0]
            finally:
                c.close(); db.close()
            bot.reply_to(message, f"╔══ ✅ 출석 완료 ══╗\n   👤 {first_name}님\n\n   🎁 획득: 100포인트\n   💰 잔여: {total}포인트\n   🔄 리셋: 매일 자정 00:00\n╚══════════════════╝")

        # ── /리필 ──
        elif '/리필' in text:
            if message.chat.type == 'private': return
            db = get_db(); c = db.cursor()
            try:
                c.execute("SELECT COUNT(*) FROM refill_logs WHERE user_id=%s AND group_id=%s AND refill_date=%s", (user_id, group_id, today))
                count = c.fetchone()[0]
                if count >= 5:
                    bot.reply_to(message, "⚠️ 오늘 리필을 5번 모두 사용했어요!"); return
                c.execute("INSERT INTO refill_logs (user_id,group_id,first_name,username,refill_date) VALUES (%s,%s,%s,%s,%s)", (user_id, group_id, first_name, username, today))
                db.commit()
            finally:
                c.close(); db.close()
            update_point(user_id, group_id, first_name, username, 100)
            bot.reply_to(message, f"╔══ 🔄 리필 완료 ══╗\n   👤 {first_name}님\n\n   🎁 획득: 100포인트\n   💰 잔여: {get_point(user_id, group_id)}포인트\n   📊 오늘 남은 리필: {5 - count - 1}회\n   🔄 리셋: 매일 자정 00:00\n╚══════════════════╝")

        # ── /선물 ──
        elif '/선물' in text:
            if message.chat.type == 'private':
                bot.reply_to(message, "⚠️ 선물은 그룹에서만 사용할 수 있어요!"); return
            if not message.reply_to_message:
                bot.reply_to(message, "🎁 선물할 상대의 메시지에 답장으로\n/선물 [포인트]\n예시: /선물 100\n⚠️ 최소: 10포인트"); return
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
            bot.reply_to(message, f"╔══ 🎁 포인트 선물 ══╗\n   💝 {first_name} → {target_name}\n\n   🎀 선물: {amount}포인트\n\n   📤 {first_name} 잔여: {get_point(user_id, group_id)}포인트\n   📥 {target_name} 잔여: {get_point(target.id, group_id)}포인트\n╚══════════════════╝")

        # ── /포인트랭킹 ──
        elif '/포인트랭킹' in text:
            if message.chat.type == 'private': return
            db = get_db(); c = db.cursor()
            try:
                c.execute("SELECT first_name,username,point FROM points WHERE group_id=%s ORDER BY point DESC LIMIT 5", (group_id,))
                rows = c.fetchall()
            finally:
                c.close(); db.close()
            medals = ['🥇','🥈','🥉','4️⃣','5️⃣']
            result = "╔══ 💰 포인트 랭킹 ══╗\n\n"
            for i, row in enumerate(rows):
                result += f"   {medals[i]} {row[0] or row[1] or '익명':<10} {row[2]}포인트\n"
            result += "╚══════════════════╝"
            bot.reply_to(message, result)

        # ── /포인트 ──
        elif '/포인트' in text:
            if message.chat.type == 'private': return
            bot.reply_to(message, f"╔══ 💰 포인트 ══╗\n   👤 {first_name}님\n\n   💰 잔여: {get_point(user_id, group_id)}포인트\n╚══════════════════╝")

        # ── /게임 ──
        elif text.strip() in ['/게임', '/게임@dopamin_ranking_bot']:
            bot.reply_to(message, "🎮 게임 목록\n\n🎰 /슬롯 [배팅] - 슬롯머신\n🎡 /룰렛 [배팅] - 룰렛\n⚠️ 최소 배팅: 20포인트")

        # ── /슬롯 ──
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
            bot.reply_to(message, f"╔══ 🎰 슬롯머신 ══╗\n   [ {s1} | {s2} | {s3} ]\n\n   {rt}\n\n   배팅: {bet}포인트\n   {'획득: +' if won>=0 else '손실: '}{won}포인트\n   잔여: {get_point(user_id, group_id)}포인트\n╚══════════════════╝")

        # ── /룰렛 ──
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
            bot.reply_to(message, f"╔══ 🎡 룰렛 ══╗\n   결과: {label}\n\n   배팅: {bet}포인트\n   {'획득: +' if won>=0 else '손실: '}{won}포인트\n   잔여: {get_point(user_id, group_id)}포인트\n╚══════════════════╝")

        # ── /채팅랭킹 ──
        elif '/채팅랭킹' in text:
            if message.chat.type == 'private': return
            monday = today - timedelta(days=today.weekday())
            sunday = monday + timedelta(days=6)
            db = get_db(); c = db.cursor()
            try:
                c.execute("SELECT first_name,username,COUNT(*) as cnt FROM chat_logs WHERE group_id=%s AND message_date>=%s GROUP BY user_id,first_name,username ORDER BY cnt DESC LIMIT 5", (group_id, monday))
                rows = c.fetchall()
            finally:
                c.close(); db.close()
            medals = ['🥇','🥈','🥉','4️⃣','5️⃣']
            result  = f"╔══ 🏆 주간 랭킹 ══╗\n"
            result += f"   📅 {monday.strftime('%m/%d')} ~ {sunday.strftime('%m/%d')}\n\n"
            if rows:
                for i, r in enumerate(rows):
                    result += f"   {medals[i]} {r[0] or r[1] or '익명':<10} {r[2]}개\n"
            else:
                result += "   채팅 기록이 없어요 😅\n"
            result += "╚══════════════════╝"
            bot.reply_to(message, result)

        # ── /채팅 ──
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
            finally:
                c.close(); db.close()
            bot.reply_to(message, f"╔══ 📊 채팅 통계 ══╗\n   👤 {first_name}님\n\n   ☀️ 오늘       {today_count}개\n   이번 주   {week_count}개\n   🗓 이번 달   {month_count}개\n   💬 전체      {total_count}개\n\n   🎀 오늘도 열심히 채팅했어요!\n╚══════════════════╝")

        # ── /야구 ──
        elif text.strip().startswith('/야구'):
            if message.chat.type == 'private': return
            send_baseball_gif(group_id)
            bot.reply_to(message, f"⚾ KBO 승 예측 안내\n{'─' * 23}\n\n📅 참여 요일: 화 / 수 / 목 / 금\n⏰ 참여 시간: {VOTE_START} ~ {VOTE_END}\n📌 10개 팀 중 5개 선택\n📌 하루 1회 참여 (수정 가능)\n\n📩 참여 링크를 DM으로 전달드렸습니다!")
            try:
                param   = f"{user_id}_{group_id}"
                kbo_url = f"{WEBAPP_BASE_URL}/kbo?start={param}"
                markup  = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("⚾ KBO 승 예측 참여하기", url=kbo_url))
                bot.send_message(user_id, f"⚾ KBO 승 예측 참여 링크\n\n📅 참여 요일: 화 / 수 / 목 / 금\n⏰ 참여 시간: {VOTE_START} ~ {VOTE_END}\n\n아래 버튼을 눌러 참여하세요!", reply_markup=markup)
            except Exception as e:
                print(f"DM 전송 실패: {e}")
                bot.send_message(group_id, f"⚠️ {first_name}님, DM을 보낼 수 없어요!\n@dopamin_ranking_bot 을 눌러 START 를 먼저 눌러주세요!")

        # ── /승 ──
        elif text.strip().startswith('/승'):
            if message.chat.type == 'private': return
            if not is_vote_time(now_kst):
                bot.reply_to(message, f"🚫 지금은 참여할 수 없어요.\n\n📅 참여 가능 요일: 화 / 수 / 목 / 금\n⏰ 참여 가능 시간: PM {VOTE_START} ~ {VOTE_END}"); return
            db = get_db(); c = db.cursor()
            try:
                c.execute("SELECT teams FROM kbo_votes WHERE user_id=%s AND group_id=%s AND vote_date=%s", (user_id, group_id, today))
                existing = c.fetchone()
            finally:
                c.close(); db.close()
            if existing:
                existing_teams = existing[0].split(',')
                team_str = "\n".join([f"   {i+1}. {KBO_TEAMS_DISPLAY.get(t,t)}" for i,t in enumerate(existing_teams)])
                try:
                    bot.send_message(user_id, f"⚠️ 이미 오늘 예측에 참여하셨어요!\n\n선택하신 팀:\n{team_str}\n\n수정하려면 /수정 을 사용하세요.")
                except:
                    bot.reply_to(message, "⚠️ 이미 오늘 예측에 참여하셨어요! DM으로 확인해주세요.")
                return
            try:
                send_baseball_gif(user_id)
                selected = []
                set_pending(user_id, group_id, selected)
                sent = bot.send_message(user_id, build_vote_message(selected), reply_markup=build_team_keyboard(selected))
                set_pending(user_id, group_id, selected, sent.message_id)
                bot.reply_to(message, f"📩 {first_name}님, DM으로 팀 선택 메시지를 보내드렸어요!")
            except Exception as e:
                bot.reply_to(message, "⚠️ DM을 보낼 수 없어요!\n봇과 DM을 먼저 시작해주세요 👇\n@dopamin_ranking_bot 을 눌러 START 버튼을 눌러주세요!")

        # ── /수정 ──
        elif text.strip().startswith('/수정'):
            if message.chat.type == 'private': return
            if not is_vote_time(now_kst):
                bot.reply_to(message, f"🚫 지금은 수정할 수 없어요.\n\n📅 참여 가능 요일: 화 / 수 / 목 / 금\n⏰ 참여 가능 시간: PM {VOTE_START} ~ {VOTE_END}"); return
            db = get_db(); c = db.cursor()
            try:
                c.execute("SELECT teams FROM kbo_votes WHERE user_id=%s AND group_id=%s AND vote_date=%s", (user_id, group_id, today))
                existing = c.fetchone()
            finally:
                c.close(); db.close()
            if not existing:
                bot.reply_to(message, "⚠️ 오늘 예측에 참여하지 않으셨어요!\n/승 명령어로 먼저 예측에 참여해주세요."); return
            try:
                send_baseball_gif(user_id)
                current_teams = existing[0].split(',')
                set_pending(user_id, group_id, current_teams)
                sent = bot.send_message(user_id, build_vote_message(current_teams), reply_markup=build_team_keyboard(current_teams))
                set_pending(user_id, group_id, current_teams, sent.message_id)
                bot.reply_to(message, f"📩 {first_name}님, DM으로 수정 메시지를 보내드렸어요!")
            except Exception as e:
                bot.reply_to(message, "⚠️ DM을 보낼 수 없어요!\n@dopamin_ranking_bot 을 눌러 START 버튼을 눌러주세요!")

        # ── /리스트 ──
        elif text.strip().startswith('/리스트'):
            if message.chat.type == 'private': return
            db = get_db(); c = db.cursor()
            try:
                c.execute("SELECT user_id, first_name, username, teams FROM kbo_votes WHERE group_id=%s AND vote_date=%s ORDER BY created_at", (group_id, today))
                rows = c.fetchall()
            finally:
                c.close(); db.close()
            if not rows:
                bot.reply_to(message, "📋 오늘 예측에 참여한 사람이 없어요!"); return
            send_baseball_gif(group_id)
            result  = f"╔══ ⚾ KBO 승 예측 리스트 ══╗\n"
            result += f"   📅 {today.strftime('%Y년 %m월 %d일')}\n"
            result += f"   👥 참여자: {len(rows)}명\n"
            result += f"   {'─' * 21}\n"
            for row in rows:
                uid   = row[0]
                first = row[1] or ''
                uname = row[2] or ''
                teams_picked = row[3].split(',')
                team_icons = "  ".join([KBO_TEAMS_DISPLAY.get(t, t) for t in teams_picked])
                if first:     name = first
                elif uname:   name = f"@{uname}"
                else:         name = f"id:{uid}"
                result += f"   👤 {name}\n  {team_icons}\n  {'─' * 21}\n"
            result += "╚══════════════════╝"
            bot.reply_to(message, result)

        # ── /내전수정 (관리자 전용 마스터 수정 모드) ──
        elif text.strip().startswith('/내전수정'):
            if message.chat.type == 'private': return
            if user_id not in ADMIN_IDS:
                bot.reply_to(message, "⚠️ 관리자만 내전을 수정할 수 있어요!"); return
            
            parts = text.strip().split()
            game_arg = parts[1] if len(parts) > 1 else ''
            game_map = {'롤':'lol', '서든':'sa5', 'lol':'lol', 'sa':'sa5', 'sa5':'sa5', 'sa6':'sa6'}
            game_type = game_map.get(game_arg)
            
            if not game_type:
                bot.reply_to(message, "⚔️ 사용법: /내전수정 롤  또는  /내전수정 서든"); return
                
            db = get_db(); c = db.cursor()
            try:
                c.execute("SELECT room_id FROM naejeon_rooms WHERE group_id=%s AND game_type=%s ORDER BY created_at DESC LIMIT 1", (group_id, game_type))
                row = c.fetchone()
                if not row:
                    bot.reply_to(message, "⚠️ 수정할 수 있는 최근 내전 기록이 없습니다."); return
                room_id = row[0]
            finally:
                c.close(); db.close()
                
            param = f"{user_id}_{group_id}_{game_type}_{room_id}"
            nj_url = f"{WEBAPP_BASE_URL}/naejeon?start={param}&mode=edit"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🛠 내전 강제 수정하기", url=nj_url))
            
            bot.reply_to(message, f"👑 관리자 전용 내전 마스터 수정 링크가 생성되었습니다.\n인원이 가득 차서 잠긴 상태여도 강제 추가 및 내보내기가 가능합니다.", reply_markup=markup)

        # ── /내전취소 ──
        elif text.strip().startswith('/내전취소'):
            if message.chat.type == 'private': return
            if user_id not in ADMIN_IDS:
                bot.reply_to(message, "⚠️ 관리자만 내전을 취소할 수 있어요!"); return
            parts    = text.strip().split()
            game_arg = parts[1] if len(parts) > 1 else ''
            game_map = {'롤':'lol','서든':'sa','lol':'lol','sa':'sa','sa5':'sa5','sa6':'sa6'}
            game_type = game_map.get(game_arg)
            if not game_type:
                bot.reply_to(message, "⚔️ 사용법: /내전취소 롤  또는  /내전취소 서든"); return
            db = get_db(); c = db.cursor()
            try:
                if game_type == 'sa':
                    c.execute("UPDATE naejeon_rooms SET status='cancelled' WHERE group_id=%s AND game_type IN ('sa5','sa6') AND status='open'", (group_id,))
                else:
                    c.execute("UPDATE naejeon_rooms SET status='cancelled' WHERE group_id=%s AND game_type=%s AND status='open'", (group_id, game_type))
                affected = c.rowcount
                db.commit()
            finally:
                c.close(); db.close()
            if affected > 0:
                game_names = {'롤':'리그오브레전드','서든':'서든어택'}
                gname = game_names.get(game_arg, game_arg)
                bot.reply_to(message, f"✅ {gname} 내전이 취소됐어요!")
            else:
                bot.reply_to(message, "⚠️ 진행 중인 내전이 없어요!")

        # ── /내전 ──
        elif text.strip().startswith('/내전'):
            if message.chat.type == 'private': return
            if user_id not in ADMIN_IDS:
                bot.reply_to(message, "⚠️ 관리자만 내전을 열 수 있어요!"); return
            parts    = text.strip().split()
            game_arg = parts[1] if len(parts) > 1 else ''
            if game_arg not in ['롤', '서든']:
                bot.reply_to(message, "⚔️ 내전 사용법 (관리자만 가능해요)\n\n/예시: 내전 롤 5v5\n/예시: 내전 서든(5v5 / 6v6 선택)\n\n예시: /내전취소 롤\n예시: /내전취소 서든\n\n예시: /내전수정 롤\n예시: /내전수정 서든"); return

            extra_text = ' '.join(parts[2:]) if len(parts) > 2 else ''

            if game_arg == '서든':
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("⚔️ 서든 5v5", callback_data=f"nj_open:sa5:{extra_text}"),
                    types.InlineKeyboardButton("⚔️ 서든 6v6", callback_data=f"nj_open:sa6:{extra_text}"),
                )
                bot.reply_to(message, "⚔️ 서든어택 인원을 선택하세요!", reply_markup=markup)
                return

            game_type    = 'lol'
            display_name = '리그오브레전드 5v5'

            db = get_db(); c = db.cursor()
            try:
                c.execute("SELECT room_id FROM naejeon_rooms WHERE group_id=%s AND game_type=%s AND status='open'", (group_id, game_type))
                existing = c.fetchone()
                if existing:
                    bot.reply_to(message, "⚠️ 이미 진행 중인 내전이 있어요!"); return

                room_id = str(uuid.uuid4())[:8]
                c.execute("INSERT INTO naejeon_rooms (room_id, group_id, game_type, slots, extra_text) VALUES (%s,%s,%s,%s,%s)",
                          (room_id, group_id, game_type, '{}', extra_text))
                db.commit()
            finally:
                c.close(); db.close()

            param  = f"{user_id}_{group_id}_{game_type}_{room_id}"
            nj_url = f"{WEBAPP_BASE_URL}/naejeon?start={param}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚔️ 내전 참여하기", url=nj_url))

            send_naejeon_gif(group_id)
            msg = f"⚔️ {display_name} 내전 모집!"
            if extra_text:
                msg += f"\n{extra_text}"
            msg += "\n\n아래 버튼을 눌러 참여하세요!\n⚠️ 처음 참여하시는 분은 @dopamin_ranking_bot 을 눌러 START 를 먼저 눌러주세요!"
            bot.send_message(group_id, msg, reply_markup=markup)

        # ── 메시지 기록 ──
        elif message.chat.type in ['group', 'supergroup']:
            save_message(user_id, username, first_name, group_id)

    except Exception as e:
        import traceback
        print(f"handle_all error: {e}\n{traceback.format_exc()}")


# ─────────────────────────────────────────────────────────
# Flask 라우트 — KBO
# ─────────────────────────────────────────────────────────
@app.route('/kbo')
def serve_kbo():
    return send_from_directory('.', 'kbo.html')

@app.route('/kbo/submit', methods=['POST'])
def kbo_submit():
    db = get_db(); c = db.cursor()
    try:
        data     = request.get_json()
        user_id  = int(data.get('userId'))
        group_id = int(data.get('groupId'))
        teams    = data.get('teams', [])
        if len(teams) != 5:
            return {'ok': False}, 400
        today = datetime.now(KST).date()
        c.execute("SELECT first_name, username FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
        row = c.fetchone()
        first_name = clean_name(row[0]) if row and row[0] else ''
        username   = row[1] if row else ''
        if not first_name:
            first_name = f"@{username}" if username else f"id:{user_id}"
        teams_str = ','.join(teams)
        c.execute("SELECT id FROM kbo_votes WHERE user_id=%s AND group_id=%s AND vote_date=%s", (user_id, group_id, today))
        existing = c.fetchone()
        if existing:
            c.execute("UPDATE kbo_votes SET teams=%s, first_name=%s, username=%s WHERE user_id=%s AND group_id=%s AND vote_date=%s",
                      (teams_str, first_name, username, user_id, group_id, today))
            action_label = "수정 완료"
        else:
            c.execute("INSERT INTO kbo_votes (user_id, group_id, first_name, username, teams, vote_date) VALUES (%s,%s,%s,%s,%s,%s)",
                      (user_id, group_id, first_name, username, teams_str, today))
            action_label = "예측 완료"
        c.execute("SELECT COUNT(*) FROM kbo_votes WHERE group_id=%s AND vote_date=%s", (group_id, today))
        total = c.fetchone()[0]
        db.commit()
        team_display = '\n'.join([f"   {i+1}. {t}" for i, t in enumerate(teams)])
        bot.send_message(group_id, f"⚾ KBO 승 {action_label}\n   👤 {first_name}님\n\n   선택한 팀 (5개):\n{team_display}\n\n   👥 오늘 참여자: {total}명")
        return {'ok': True}, 200
    except Exception as e:
        import traceback
        print(f"kbo_submit error: {e}\n{traceback.format_exc()}")
        return {'ok': False}, 500
    finally:
        c.close(); db.close()

@app.route('/kbo/list')
def kbo_list():
    db = get_db(); c = db.cursor()
    try:
        group_id = int(request.args.get('groupId', 0))
        today = datetime.now(KST).date()
        c.execute("SELECT user_id, first_name, username, teams FROM kbo_votes WHERE group_id=%s AND vote_date=%s ORDER BY created_at", (group_id, today))
        rows = c.fetchall()
        result = []
        for row in rows:
            uid   = row[0]
            first = clean_name(row[1] or '')
            uname = row[2] or ''
            name  = first if first else (('@' + uname) if uname else ('id:' + str(uid)))
            teams = row[3].split(',')
            result.append({'name': name, 'teams': teams})
        return result, 200
    except:
        return [], 500
    finally:
        c.close(); db.close()

@app.route('/kbo/hot')
def kbo_hot():
    db = get_db(); c = db.cursor()
    try:
        group_id = int(request.args.get('groupId', 0))
        today = datetime.now(KST).date()
        c.execute("SELECT teams FROM kbo_votes WHERE group_id=%s AND vote_date=%s", (group_id, today))
        rows = c.fetchall()
        from collections import Counter
        cnt = Counter()
        for row in rows:
            for team in row[0].split(','):
                cnt[team] += 1
        result = [{'team': t, 'count': v} for t, v in cnt.most_common(3)]
        return result, 200
    except:
        return [], 500
    finally:
        c.close(); db.close()


# ─────────────────────────────────────────────────────────
# Flask 라우트 — 내전 
# ─────────────────────────────────────────────────────────
@app.route('/naejeon')
def serve_naejeon():
    return send_from_directory('.', 'naejeon.html')

@app.route('/naejeon/check_admin')
def naejeon_check_admin():
    try:
        user_id = int(request.args.get('userId', 0))
        return {'isAdmin': user_id in ADMIN_IDS}, 200
    except:
        return {'isAdmin': False}, 200

@app.route('/naejeon/room')
def naejeon_room():
    db = get_db(); c = db.cursor()
    try:
        room_id = request.args.get('roomId')
        c.execute("""
            SELECT game_type, slots, status, extra_text,
                   pos_a, pos_b, started, fund_type, fund_amount
            FROM naejeon_rooms WHERE room_id=%s
        """, (room_id,))
        row = c.fetchone()
        if not row:
            return {'error': '내전 방을 찾을 수 없어요.'}, 404
        return {
            'gameType':   row[0],
            'slots':      row[1] or {},
            'status':     row[2],
            'extraText':  row[3] or '',
            'posA':       row[4] or [],
            'posB':       row[5] or [],
            'started':    bool(row[6]),
            'fundType':   row[7] or '',
            'fundAmount': row[8] or '',
        }, 200
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        c.close(); db.close()

@app.route('/naejeon/setup', methods=['POST'])
def naejeon_setup():
    db = get_db(); c = db.cursor()
    try:
        data        = request.get_json()
        room_id     = data.get('roomId')
        user_id     = int(data.get('userId'))
        group_id    = int(data.get('groupId'))
        game_type   = data.get('gameType')
        extra_text  = data.get('extraText', '')
        pos_a       = data.get('posA', [])
        pos_b       = data.get('posB', [])
        fund_type   = data.get('fundType', '')
        fund_amount = data.get('fundAmount', '')

        if user_id not in ADMIN_IDS:
            return {'ok': False, 'error': '관리자만 사용할 수 있어요.'}, 403

        c.execute("""
            UPDATE naejeon_rooms
            SET extra_text=%s, pos_a=%s, pos_b=%s, started=TRUE,
                fund_type=%s, fund_amount=%s
            WHERE room_id=%s
        """, (extra_text, json.dumps(pos_a), json.dumps(pos_b), fund_type, fund_amount, room_id))
        db.commit()

        game_names = {'lol':'리그오브레전드 5v5','sa5':'서든어택 5v5','sa6':'서든어택 6v6'}
        gname  = game_names.get(game_type, '내전')
        param  = f"{user_id}_{group_id}_{game_type}_{room_id}"
        nj_url = f"{WEBAPP_BASE_URL}/naejeon?start={param}"

        # ── 금액 천 단위 콤마 + '원' 포맷팅 처리 ──
        display_amount = fund_amount
        if fund_amount.isdigit():
            display_amount = f"{int(fund_amount):,}원"  # 👈 콤마와 '원' 추가

        send_naejeon_gif(group_id)
        msg = f"⚙️ {gname} 내전 설정 변경 및 공지!"
        if extra_text:
            msg += f"\n📢 공지: {extra_text}"
        if fund_type and fund_amount:
            msg += f"\n💰 {fund_type} 조건: {display_amount}"
        msg += f"\n\n👉 <a href='{nj_url}'>[여기]를 눌러 내전 현황 보기</a>"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚔️ 내전 바로가기", url=nj_url))
        bot.send_message(group_id, msg, reply_markup=markup, parse_mode='HTML')

        c.execute("SELECT game_type, slots, status, extra_text, pos_a, pos_b, started, fund_type, fund_amount FROM naejeon_rooms WHERE room_id=%s", (room_id,))
        row2 = c.fetchone()
        return {
            'ok': True,
            'room': {
                'gameType':   row2[0],
                'slots':      row2[1] or {},
                'status':     row2[2],
                'extraText':  row2[3] or '',
                'posA':       row2[4] or [],
                'posB':       row2[5] or [],
                'started':    bool(row2[6]),
                'fundType':   row2[7] or '',
                'fundAmount': row2[8] or '',
            }
        }, 200
    except Exception as e:
        return {'ok': False, 'error': str(e)}, 500
    finally:
        c.close(); db.close()

@app.route('/naejeon/cancel', methods=['POST'])
def naejeon_cancel():
    db = get_db(); c = db.cursor()
    try:
        data     = request.get_json()
        room_id  = data.get('roomId')
        user_id  = int(data.get('userId', 0))
        group_id = int(data.get('groupId', 0))

        if user_id not in ADMIN_IDS:
            return {'ok': False, 'error': '관리자만 사용할 수 있어요.'}, 403

        c.execute("UPDATE naejeon_rooms SET status='cancelled' WHERE room_id=%s AND group_id=%s", (room_id, group_id))
        affected = c.rowcount
        db.commit()

        if affected > 0:
            try:
                bot.send_message(group_id, "⚔️ 내전이 관리자에 의해 취소됐어요.")
            except:
                pass
            return {'ok': True}, 200
        else:
            return {'ok': False, 'error': '내전을 찾을 수 없어요.'}, 404
    except Exception as e:
        return {'ok': False, 'error': str(e)}, 500
    finally:
        c.close(); db.close()

@app.route('/naejeon/admin_add', methods=['POST'])
def naejeon_admin_add():
    db = get_db(); c = db.cursor()
    try:
        data     = request.get_json()
        room_id  = data.get('roomId')
        user_id  = int(data.get('userId'))
        group_id = int(data.get('groupId'))
        slot_key = data.get('slotKey')
        name     = data.get('name', '').strip()

        if user_id not in ADMIN_IDS:
            return {'ok': False, 'error': '관리자만 사용할 수 있어요.'}, 403
        if not name:
            return {'ok': False, 'error': '이름을 입력해주세요.'}, 400

        c.execute("SELECT game_type, slots, status FROM naejeon_rooms WHERE room_id=%s FOR UPDATE", (room_id,))
        row = c.fetchone()
        if not row:
            return {'ok': False, 'error': '방을 찾을 수 없어요.'}, 404

        slots = row[1] if row[1] else {}
        slots[slot_key] = {'userId': f'admin_{uuid.uuid4().hex[:6]}', 'name': name, 'team': slot_key.split('_')[0]}

        total  = {'lol':10,'sa5':10,'sa6':12}.get(row[0], 10)
        filled = len([v for v in slots.values() if v and v.get('userId')])
        status = 'closed' if filled >= total else 'open'

        c.execute("UPDATE naejeon_rooms SET slots=%s, status=%s WHERE room_id=%s", (json.dumps(slots), status, room_id))
        db.commit()

        if status == 'closed':
            _send_naejeon_result(group_id, row[0], slots)

        c.execute("SELECT game_type, slots, status, extra_text, pos_a, pos_b, started, fund_type, fund_amount FROM naejeon_rooms WHERE room_id=%s", (room_id,))
        row2 = c.fetchone()
        return {
            'ok': True,
            'room': {
                'gameType':   row2[0],
                'slots':      row2[1] or {},
                'status':     row2[2],
                'extraText':  row2[3] or '',
                'posA':       row2[4] or [],
                'posB':       row2[5] or [],
                'started':    bool(row2[6]),
                'fundType':   row2[7] or '',
                'fundAmount': row2[8] or '',
            }
        }, 200
    except Exception as e:
        return {'ok': False, 'error': str(e)}, 500
    finally:
        c.close(); db.close()

@app.route('/naejeon/admin_remove', methods=['POST'])
def naejeon_admin_remove():
    db = get_db(); c = db.cursor()
    try:
        data     = request.get_json()
        room_id  = data.get('roomId')
        user_id  = int(data.get('userId'))
        group_id = int(data.get('groupId'))
        slot_key = data.get('slotKey')

        if user_id not in ADMIN_IDS:
            return {'ok': False, 'error': '관리자만 사용할 수 있어요.'}, 403

        c.execute("SELECT game_type, slots, status FROM naejeon_rooms WHERE room_id=%s FOR UPDATE", (room_id,))
        row = c.fetchone()
        if not row:
            return {'ok': False, 'error': '방을 찾을 수 없어요.'}, 404

        slots = row[1] if row[1] else {}
        if slot_key in slots:
            slots[slot_key] = None

        c.execute("UPDATE naejeon_rooms SET slots=%s, status='open' WHERE room_id=%s", (json.dumps(slots), room_id))
        db.commit()

        c.execute("SELECT game_type, slots, status, extra_text, pos_a, pos_b, started, fund_type, fund_amount FROM naejeon_rooms WHERE room_id=%s", (room_id,))
        row2 = c.fetchone()
        return {
            'ok': True,
            'room': {
                'gameType':   row2[0],
                'slots':      row2[1] or {},
                'status':     row2[2],
                'extraText':  row2[3] or '',
                'posA':       row2[4] or [],
                'posB':       row2[5] or [],
                'started':    bool(row2[6]),
                'fundType':   row2[7] or '',
                'fundAmount': row2[8] or '',
            }
        }, 200
    except Exception as e:
        return {'ok': False, 'error': str(e)}, 500
    finally:
        c.close(); db.close()

@app.route('/naejeon/join', methods=['POST'])
def naejeon_join():
    db = get_db(); c = db.cursor()
    try:
        data      = request.get_json()
        room_id   = data.get('roomId')
        user_id   = int(data.get('userId'))
        group_id  = int(data.get('groupId'))
        team      = data.get('team')
        pos_id    = data.get('posId')
        pos_label = data.get('posLabel')

        c.execute("SELECT game_type, slots, status FROM naejeon_rooms WHERE room_id=%s FOR UPDATE", (room_id,))
        row = c.fetchone()
        if not row:
            return {'ok': False, 'error': '방을 찾을 수 없어요.'}, 404
        if row[2] != 'open':
            return {'ok': False, 'error': '이미 마감된 내전이에요.'}, 400

        slots     = row[1] if row[1] else {}
        game_type = row[0]
        slot_key  = f"{team}_{pos_id}"

        for k, v in slots.items():
            if v and str(v.get('userId')) == str(user_id):
                return {'ok': False, 'error': '이미 참여하셨어요!'}, 400

        if slots.get(slot_key):
            return {'ok': False, 'error': '이미 선택된 포지션이에요!'}, 400

        c.execute("SELECT first_name, username FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
        ur   = c.fetchone()
        name = clean_name(ur[0]) if ur and ur[0] else (f"@{ur[1]}" if ur and ur[1] else f"id:{user_id}")

        slots[slot_key] = {'userId': user_id, 'name': name, 'posLabel': pos_label, 'team': team}

        total_map = {'lol':10,'sa5':10,'sa6':12}
        total     = total_map.get(game_type, 10)
        filled    = len([v for v in slots.values() if v])
        status    = 'closed' if filled >= total else 'open'

        c.execute("UPDATE naejeon_rooms SET slots=%s, status=%s WHERE room_id=%s", (json.dumps(slots), status, room_id))
        db.commit()

        if status == 'closed':
            _send_naejeon_result(group_id, game_type, slots)

        c.execute("SELECT game_type, slots, status, extra_text, pos_a, pos_b, started, fund_type, fund_amount FROM naejeon_rooms WHERE room_id=%s", (room_id,))
        row2 = c.fetchone()
        return {'ok': True, 'room': {'gameType': row2[0], 'slots': row2[1] or {}, 'status': row2[2], 'extraText': row2[3] or '', 'posA': row2[4] or [], 'posB': row2[5] or [], 'started': bool(row2[6]), 'fundType': row2[7] or '', 'fundAmount': row2[8] or ''}}, 200
    except Exception as e:
        import traceback
        print(f"naejeon_join error: {e}\n{traceback.format_exc()}")
        return {'ok': False, 'error': str(e)}, 500
    finally:
        c.close(); db.close()

@app.route('/naejeon/leave', methods=['POST'])
def naejeon_leave():
    db = get_db(); c = db.cursor()
    try:
        data    = request.get_json()
        room_id = data.get('roomId')
        user_id = int(data.get('userId'))

        c.execute("SELECT game_type, slots, status FROM naejeon_rooms WHERE room_id=%s FOR UPDATE", (room_id,))
        row = c.fetchone()
        if not row:
            return {'ok': False, 'error': '방을 찾을 수 없어요.'}, 404

        slots   = row[1] if row[1] else {}
        updated = False
        for k, v in list(slots.items()):
            if v and str(v.get('userId')) == str(user_id):
                slots[k] = None
                updated  = True
                break

        if not updated:
            return {'ok': False, 'error': '참여 기록을 찾을 수 없어요.'}, 400

        c.execute("UPDATE naejeon_rooms SET slots=%s, status='open' WHERE room_id=%s", (json.dumps(slots), room_id))
        db.commit()
        
        c.execute("SELECT game_type, slots, status, extra_text, pos_a, pos_b, started, fund_type, fund_amount FROM naejeon_rooms WHERE room_id=%s", (room_id,))
        row2 = c.fetchone()
        return {'ok': True, 'room': {'gameType': row2[0], 'slots': row2[1] or {}, 'status': row2[2], 'extraText': row2[3] or '', 'posA': row2[4] or [], 'posB': row2[5] or [], 'started': bool(row2[6]), 'fundType': row2[7] or '', 'fundAmount': row2[8] or ''}}, 200
    except Exception as e:
        return {'ok': False, 'error': str(e)}, 500
    finally:
        c.close(); db.close()

def _send_naejeon_result(group_id, game_type, slots):
    game_names = {'lol':'리그오브레전드 5v5','sa5':'서든어택 5v5','sa6':'서든어택 6v6'}
    pos_order = {
        'lol': ['top','jg','mid','adc','sup'],
        'sa5': ['sna','rfl1','rfl2','rfl3','rfl4'],
        'sa6': ['sna1','sna2','rfl1','rfl2','rfl3','rfl4'],
    }.get(game_type, [])
    pos_labels = {
        'top':'탑','jg':'정글','mid':'미드','adc':'원딜','sup':'서폿',
        'sna':'스나','sna1':'스나1','sna2':'스나2',
        'rfl1':'라플1','rfl2':'라플2','rfl3':'라플3','rfl4':'라플4',
    }
    result = f"⚔️ {game_names.get(game_type,'')} 내전 모집 완료!\n\n"
    for team_id, label in [('A','🟣 1팀'), ('B','🟢 2팀')]:
        result += f"{label}\n"
        for pos in pos_order:
            slot  = slots.get(f"{team_id}_{pos}")
            pname = pos_labels.get(pos, pos)
            uname = slot['name'] if (slot and slot.get('userId')) else '비어있음'
            result += f"   [{pname}] {uname}\n"
        result += "\n"
    try:
        bot.send_message(group_id, result)
    except:
        pass


# ─────────────────────────────────────────────────────────
# Webhook
# ─────────────────────────────────────────────────────────
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    try:
        json_str = request.stream.read().decode('utf-8')
        update   = telebot.types.Update.de_json(json_str)
        if update.message:
            handle_all(update.message)
        elif update.callback_query:
            if update.callback_query.data.startswith('kbo_'):
                handle_kbo_callback(update.callback_query)
            elif update.callback_query.data.startswith('nj_open:'):
                handle_nj_open(update.callback_query)
    except Exception as e:
        import traceback
        print(f"webhook error: {e}\n{traceback.format_exc()}")
    return 'OK', 200

@app.route('/')
def index():
    return 'Bot is running!', 200


# ─────────────────────────────────────────────────────────
# 시작
# ─────────────────────────────────────────────────────────
try:
    init_db()
    print("DB 초기화 성공!")
except Exception as e:
    print(f"DB init error: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
