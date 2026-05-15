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

AFFILIATE_TEXT = """❤️카지노❤️
[평생제휴] 1️⃣ <a href="https://t.me/gamte59/31">렛츠뱃</a>
[평생제휴] 2️⃣ <a href="https://t.me/gamte59/28">예스뱃</a>
[도파민제휴] 3️⃣ <a href="https://t.me/gamte59/44">지엑스뱃</a>
[도파민제휴] 4️⃣ <a href="https://t.me/gamte59/46">케이비씨겜</a>
[도파민제휴] 5️⃣ <a href="https://t.me/gamte59/49">블록체인바카라</a>
[도파민제휴] 6️⃣ <a href="https://t.me/gamte59/60">우루스뱃</a>
[도파민제휴] 7️⃣ <a href="https://t.me/gamte59/60">마닐라</a>
[도파민제휴] 8️⃣ <a href="https://t.me/gamte59/70">미우카지노</a>
[도파민제휴] 9️⃣ <a href="https://t.me/gamte59/72">그랜드파리</a>
[도파민제휴] 🔟 <a href="https://t.me/gamte59/74">룰라뱃</a>
[도파민제휴] 1️⃣ <a href="https://t.me/gamte59/78">소울카지노</a>
[도파민제휴] 2️⃣ <a href="https://t.me/gamte59/84">123GAME카지노</a>

❤️급전❤️
[도파민제휴] 1️⃣ <a href="https://t.me/gamte59/16">OR급전</a>
[도파민제휴] 2️⃣ <a href="https://t.me/gamte59/77">빅딜OTC</a>

❤️장집❤️
[도파민제휴] 1️⃣ <a href="https://t.me/gamte59/37">미호 장집</a>
[도파민제휴] 2️⃣ <a href="https://t.me/gamte59/76">빅딜 장집</a>

❤️반환팀❤️
[도파민제휴] 1️⃣ <a href="https://t.me/gamte59/39">울프 반환팀</a>

❤️충전 계좌매입❤️
[평생제휴] 1️⃣ <a href="https://t.me/gamte59/42">저승사자</a>
[도파민제휴] 2️⃣ <a href="https://t.me/gamte59/58">김여포</a>
[도파민제휴] 3️⃣ <a href="https://t.me/gamte59/64">대문팀</a>
[도파민제휴] 4️⃣ <a href="https://t.me/gamte59/92">관짝</a>


❤️홀덤❤️
[도파민제휴] 1️⃣ <a href="https://t.me/gamte59/69">룽지홀덤</a>

❤️이체알바❤️
[도파민제휴] 1️⃣ <a href="https://t.me/gamte59/87">창비팀 대면이체알바</a>"""


CARD_TITLES = [
    ("🌟", "천 운", "하늘이 당신을 선택한 날"),
    ("🌙", "월 운", "달빛이 당신을 감싸는 날"),
    ("🔥", "화 운", "불꽃처럼 에너지가 넘치는 날"),
    ("🌊", "해 운", "바다처럼 넓은 기회의 날"),
    ("🐉", "용 운", "용이 강림한 날"),
    ("⭐", "성 운", "별이 빛나는 날"),
    ("🌸", "화 운", "꽃처럼 아름다운 날"),
    ("💎", "보 운", "보석처럼 빛나는 날"),
    ("🦁", "왕 운", "왕처럼 당당한 날"),
    ("🌈", "채 운", "무지개처럼 다채로운 날"),
    ("⚡", "뇌 운", "번개처럼 빠른 기회의 날"),
    ("🌺", "춘 운", "봄처럼 따뜻한 날"),
    ("🦋", "화 운", "나비처럼 자유로운 날"),
    ("🏔️", "산 운", "산처럼 굳건한 날"),
    ("🌙", "야 운", "고요한 밤처럼 차분한 날"),
    ("🎯", "명 운", "목표를 향해 나아가는 날"),
    ("🍀", "행 운", "네잎클로버가 찾아온 날"),
    ("🌊", "파 운", "파도처럼 힘차게 나아가는 날"),
    ("🦅", "비 운", "독수리처럼 높이 나는 날"),
    ("💫", "신 운", "신비로운 기운이 감도는 날"),
]

OPENING_LINES = [
    "새벽 3시, 하늘에서 별이 떨어졌어요",
    "오늘 아침 검은 고양이가 당신 곁을 지나갔어요",
    "달이 유독 밝게 빛나는 오늘",
    "바람이 동쪽에서 불어오는 날",
    "오늘 새벽 꿈속에서 용을 만났나요?",
    "붉은 노을이 당신의 하루를 물들여요",
    "오늘 아침 새 한 마리가 당신 창가에 앉았어요",
    "봄비가 내리는 오늘",
    "보름달이 뜨는 특별한 날",
    "오늘 거울 속 당신이 유난히 빛나 보여요",
    "구름 사이로 햇살이 쏟아지는 날",
    "오늘따라 바람이 당신 편인 것 같아요",
    "새벽 이슬처럼 상쾌한 오늘",
    "오늘 당신 주변에 좋은 기운이 맴돌아요",
    "하늘의 별들이 오늘 당신을 주목해요",
    "오늘 우주가 당신에게 속삭여요",
    "태양이 유독 따뜻하게 느껴지는 날",
    "오늘 바다에서 행운의 파도가 밀려와요",
    "봄꽃이 당신을 위해 피어나는 날",
    "오늘 하늘이 유독 파랗게 느껴지나요?",
    "무지개가 뜰 것 같은 기분 좋은 날",
    "오늘 당신의 직감을 믿어보세요",
    "고요한 새벽 하늘이 당신에게 말을 건네요",
    "오늘따라 마음이 가벼운 이유가 있어요",
    "겨울이 지나고 봄이 오듯 좋은 일이 생겨요",
    "오늘 당신은 특별한 에너지를 품고 있어요",
    "작은 행운들이 모여 큰 행운이 되는 날",
    "오늘 당신의 미소가 세상을 밝혀요",
    "새로운 시작을 알리는 바람이 불어요",
    "오늘 운명의 실이 당신 주변을 감싸고 있어요",
    "별자리가 오늘 당신 편에 서 있어요",
    "오늘 아침 커피 향처럼 달콤한 하루가 시작돼요",
    "구름 한 점 없는 맑은 하늘처럼 오늘은 맑아요",
    "오늘 당신 곁에 보이지 않는 수호천사가 있어요",
    "밤하늘의 북극성처럼 오늘 당신이 중심이에요",
    "오늘 나비 한 마리가 당신에게 행운을 전해줘요",
    "새벽 이슬방울처럼 오늘은 신선한 기운이 넘쳐요",
    "오늘 당신의 선택이 미래를 바꿀 수 있어요",
    "하늘과 땅이 하나가 되는 특별한 날이에요",
    "오늘 우연한 만남이 인연이 될 수 있어요",
    "분홍빛 노을처럼 오늘 하루가 물들어요",
    "오늘 당신이 내뱉는 말에 힘이 실려요",
    "달빛 아래 소원을 빌면 이루어지는 날이에요",
    "오늘 작은 것에서 큰 기쁨을 발견할 수 있어요",
    "봄바람처럼 상쾌한 소식이 찾아올 거예요",
    "오늘 당신의 노력이 빛을 발하는 날이에요",
    "은하수가 흐르는 밤처럼 낭만적인 하루예요",
    "오늘 숨겨진 재능이 발휘될 기회가 와요",
    "새벽 4시의 고요함처럼 오늘은 집중력이 높아요",
    "오늘 당신이 가는 길에 꽃이 피어나요",
]

FORTUNE_CONTENTS = [
    "숨겨왔던 재능이 빛을 발하는 날이에요",
    "망설였던 일을 지금 당장 시작하세요",
    "오늘 중요한 결정을 내려도 좋은 날이에요",
    "주변 사람의 말에 귀를 기울여보세요",
    "뜻밖의 곳에서 기회가 찾아올 거예요",
    "오늘 하루 자신감을 가지고 행동하세요",
    "작은 친절이 큰 행운으로 돌아오는 날",
    "오랫동안 기다려온 소식이 올 수 있어요",
    "새로운 인연이 당신 삶을 바꿀 수 있어요",
    "오늘은 평소보다 운이 따르는 날이에요",
    "직감을 믿고 행동하면 좋은 결과가 나와요",
    "오늘 당신의 노력이 인정받을 거예요",
    "긍정적인 마음이 행운을 불러오는 날",
    "오늘 포기하지 않으면 반드시 결실이 맺혀요",
    "주변을 돌아보면 행운이 숨어있어요",
    "오늘 새로운 도전을 두려워하지 마세요",
    "잃어버린 것을 찾게 되는 날이에요",
    "오늘 누군가와의 대화가 인생을 바꿔요",
    "오래된 인연이 다시 연결되는 날이에요",
    "오늘 당신의 아이디어가 빛을 발해요",
    "작은 것에 감사하면 더 큰 행운이 와요",
    "오늘 무언가를 시작하기에 완벽한 날이에요",
    "참아왔던 말을 꺼내기 좋은 날이에요",
    "오늘 뜻밖의 선물이 기다리고 있어요",
    "당신의 진심이 상대방에게 전해지는 날",
    "오늘 오랜 고민이 해결될 실마리가 보여요",
    "새로운 환경이 당신에게 잘 맞는 날이에요",
    "오늘 투자한 노력이 두 배로 돌아와요",
    "주변의 응원이 당신에게 힘이 되는 날",
    "오늘 뜻밖의 행운이 찾아올 준비를 하세요",
    "마음속 소원이 이루어질 조짐이 보여요",
    "오늘 당신이 선택하는 모든 것이 옳아요",
    "새벽부터 밤까지 좋은 기운이 함께해요",
    "오늘 누군가에게 먼저 손을 내밀어보세요",
    "기다리던 연락이 올 수 있는 날이에요",
    "오늘 당신의 매력이 최고조에 달해 있어요",
    "예상치 못한 도움을 받을 수 있는 날",
    "오늘 하루 여유를 가지면 더 좋은 결과가 나와요",
    "당신의 성실함이 빛을 발하는 날이에요",
    "오늘 작은 변화가 큰 결과를 만들어요",
    "숨겨진 행운이 당신 곁에 있어요",
    "오늘 처음 만나는 사람과 좋은 인연이 될 수 있어요",
    "마음이 통하는 사람과 대화하기 좋은 날",
    "오늘 당신의 직장운이 상승하는 날이에요",
    "새로운 취미를 시작하기 좋은 날이에요",
    "오늘 건강에 특별히 신경 써보세요",
    "가족과 함께하는 시간이 행운을 불러와요",
    "오늘 베푸는 만큼 돌아오는 날이에요",
    "당신을 아끼는 사람의 조언을 들어보세요",
    "오늘 하루 모든 것이 순조롭게 풀려요",
    "뜻하지 않은 곳에서 해결책이 나타나요",
    "오늘 당신의 인내가 드디어 보상받아요",
    "새로운 시작을 두려워하지 않는 날이에요",
    "오늘 당신 주변에 행운의 기운이 가득해요",
    "평소보다 자신을 더 사랑해주는 날이에요",
    "오늘 과감한 도전이 성공으로 이어져요",
    "소소한 행복이 가득한 하루가 될 거예요",
    "오늘 당신의 말 한마디가 큰 힘이 돼요",
    "숨어있던 기회가 드러나는 날이에요",
    "오늘 당신이 원하는 것을 얻을 수 있어요",
    "행운의 바람이 당신 등 뒤에서 불어요",
    "오늘 인내하면 내일 더 큰 기쁨이 와요",
    "당신의 노력이 주변에 영향을 미치는 날",
    "오늘 예상보다 일이 빠르게 해결돼요",
    "새로운 아이디어가 샘솟는 창의적인 날",
    "오늘 당신의 판단력이 최고조에 달해요",
    "좋은 소식을 기다리고 있다면 오늘이에요",
    "오늘 당신의 노력에 하늘이 화답해요",
    "막혔던 일이 술술 풀리는 날이에요",
    "오늘 당신에게 특별한 인연이 찾아와요",
    "평온한 마음이 행운을 부르는 날이에요",
    "오늘 당신의 선한 마음이 빛을 발해요",
    "뜻밖의 기쁜 소식이 들려오는 날이에요",
    "오늘 당신의 끈기가 결실을 맺어요",
    "주변의 사랑이 느껴지는 따뜻한 날이에요",
    "오늘 당신의 미래가 밝게 빛나고 있어요",
    "새로운 가능성이 열리는 날이에요",
    "오늘 당신이 내린 결정을 믿어보세요",
    "행운의 숫자가 당신 곁에 있는 날이에요",
    "오늘 당신의 열정이 주변을 감동시켜요",
]

MONEY_FORTUNES = [
    ("💰💰💰💰💰", "오늘 뜻밖의 수입이 생겨요"),
    ("💰💰💰💰░", "금전적으로 여유로운 날이에요"),
    ("💰💰💰░░", "작은 행운의 돈이 들어와요"),
    ("💰💰░░░", "지출을 줄이면 좋을 날이에요"),
    ("💰░░░░", "오늘은 큰 지출을 피하세요"),
    ("💰💰💰💰💰", "로또 한 장 사보는 건 어떨까요?"),
    ("💰💰💰💰░", "투자한 것이 돌아오는 날이에요"),
    ("💰💰💰░░", "소소한 행운의 돈이 생겨요"),
    ("💰💰░░░", "절약이 미덕인 날이에요"),
    ("💰💰💰💰💰", "금전운이 최고조인 날이에요"),
    ("💰💰💰░░", "예상치 못한 곳에서 돈이 들어와요"),
    ("💰💰💰💰░", "재물이 쌓이는 날이에요"),
    ("💰░░░░", "충동구매는 오늘 참아보세요"),
    ("💰💰💰💰💰", "오늘 금전적 결정이 빛을 발해요"),
    ("💰💰💰░░", "돈이 조금씩 모이는 날이에요"),
    ("💰💰💰💰░", "뜻밖의 보너스가 생길 수 있어요"),
    ("💰💰░░░", "오늘은 저축에 집중하세요"),
    ("💰💰💰💰💰", "금전적 기회를 놓치지 마세요"),
    ("💰💰💰░░", "오늘 선물을 받을 수도 있어요"),
    ("💰💰💰💰░", "재물운이 상승하는 날이에요"),
]

LOVE_FORTUNES = [
    ("💕💕💕💕💕", "운명의 사람을 만날 수 있어요"),
    ("💕💕💕💕░", "연인과 더욱 가까워지는 날이에요"),
    ("💕💕💕░░", "설레는 감정이 찾아오는 날이에요"),
    ("💕💕░░░", "혼자만의 시간이 필요한 날이에요"),
    ("💕░░░░", "감정을 정리하는 시간을 가지세요"),
    ("💕💕💕💕💕", "오늘 고백하면 성공할 수 있어요"),
    ("💕💕💕💕░", "오래된 인연이 새로워지는 날"),
    ("💕💕💕░░", "주변에 숨어있는 인연을 찾아보세요"),
    ("💕💕💕💕💕", "사랑이 활짝 피어나는 날이에요"),
    ("💕💕💕░░", "진심이 통하는 날이에요"),
    ("💕💕💕💕░", "새로운 만남이 설레는 날이에요"),
    ("💕💕░░░", "오늘은 혼자를 즐기는 날이에요"),
    ("💕💕💕💕💕", "연애운이 최고조인 날이에요"),
    ("💕💕💕░░", "좋아하는 사람에게 연락해보세요"),
    ("💕💕💕💕░", "달콤한 시간이 기다리고 있어요"),
    ("💕░░░░", "감정 기복에 주의하는 날이에요"),
    ("💕💕💕💕💕", "사랑의 기운이 넘치는 날이에요"),
    ("💕💕💕░░", "솔직한 감정 표현이 좋은 결과를 불러요"),
    ("💕💕💕💕░", "특별한 추억을 만들기 좋은 날"),
    ("💕💕░░░", "마음을 열고 대화해보는 날이에요"),
]

HEALTH_FORTUNES = [
    ("💪💪💪💪💪", "체력이 넘치는 날이에요"),
    ("💪💪💪💪░", "건강운이 좋은 날이에요"),
    ("💪💪💪░░", "가벼운 운동이 도움이 돼요"),
    ("💪💪░░░", "충분한 휴식이 필요한 날이에요"),
    ("💪░░░░", "오늘은 무리하지 마세요"),
    ("💪💪💪💪💪", "운동 시작하기 완벽한 날이에요"),
    ("💪💪💪💪░", "컨디션이 최고조인 날이에요"),
    ("💪💪💪░░", "스트레칭으로 몸을 풀어주세요"),
    ("💪💪💪💪💪", "에너지가 넘치는 날이에요"),
    ("💪💪░░░", "수분 섭취를 충분히 하세요"),
    ("💪💪💪💪░", "오늘 몸 상태가 매우 좋아요"),
    ("💪💪💪░░", "규칙적인 식사가 중요한 날이에요"),
    ("💪░░░░", "피로가 쌓인 날이니 쉬어가세요"),
    ("💪💪💪💪💪", "건강운이 최고인 날이에요"),
    ("💪💪💪░░", "산책이 활력을 줄 거예요"),
    ("💪💪💪💪░", "오늘 몸과 마음이 가벼워요"),
    ("💪💪░░░", "충분한 수면이 필요한 날이에요"),
    ("💪💪💪💪💪", "운동하면 기분이 좋아지는 날"),
    ("💪💪💪░░", "건강한 음식을 먹는 날이에요"),
    ("💪💪💪💪░", "활기찬 하루가 될 거예요"),
]

BORDER_EMOJIS = [
    "🔮", "🌟", "🌙", "🔥", "🌊", "🐉", "⭐", "🌸",
    "💎", "🦁", "🌈", "⚡", "🌺", "🦋", "🏔️", "🎯",
    "🍀", "🦅", "💫", "✨"
]

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
        CREATE TABLE IF NOT EXISTS highlow_games (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            group_id BIGINT NOT NULL,
            current_card INTEGER NOT NULL,
            bet INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vote_list (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            group_id BIGINT NOT NULL,
            first_name VARCHAR(255),
            username VARCHAR(255),
            vote_type VARCHAR(10) NOT NULL,
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

def card_emoji(num):
    cards = {1:'A', 2:'2', 3:'3', 4:'4', 5:'5',
             6:'6', 7:'7', 8:'8', 9:'9', 10:'10',
             11:'J', 12:'Q', 13:'K'}
    return cards.get(num, str(num))

def generate_fortune(user_id, today):
    seed = int(str(user_id) + today.strftime('%Y%m%d'))
    rng = random.Random(seed)
    border = rng.choice(BORDER_EMOJIS)
    title_emoji, title, title_desc = rng.choice(CARD_TITLES)
    opening = rng.choice(OPENING_LINES)
    content = rng.choice(FORTUNE_CONTENTS)
    money_star, money_text = rng.choice(MONEY_FORTUNES)
    love_star, love_text = rng.choice(LOVE_FORTUNES)
    health_star, health_text = rng.choice(HEALTH_FORTUNES)
    result = (
        f"{border} ━━━━━━━━━━━━━\n"
        f"   운명의 카드가 뽑혔어요\n"
        f"   {title_emoji} [ {title} ] {title_emoji}\n"
        f"   {title_desc}\n\n"
        f"   {opening}\n"
        f"   {content}\n\n"
        f"💰 금전운 {money_star}\n"
        f"   {money_text}\n\n"
        f"💕 연애운 {love_star}\n"
        f"   {love_text}\n\n"
        f"💪 건강운 {health_star}\n"
        f"   {health_text}\n"
        f"{border} ━━━━━━━━━━━━━"
    )
    return result

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
            bot.reply_to(message, AFFILIATE_TEXT, parse_mode='HTML', disable_web_page_preview=True)

        # ==================== /운세 ====================
        elif '/운세' in text:
            if message.chat.type == 'private':
                return
            fortune = generate_fortune(user_id, today)
            bot.reply_to(message,
                f"🔮 {first_name}님의 오늘의 운세\n"
                f"📅 {today.strftime('%Y년 %m월 %d일')}\n\n"
                f"{fortune}"
            )

        # ==================== 테더 환율 ====================
        elif re.search(r'(\d+(\.\d+)?)\s*테더', text):
            match = re.search(r'(\d+(\.\d+)?)\s*테더', text)
            amount = float(match.group(1))
            rate = get_usdt_rate()

            if rate is None:
                bot.reply_to(message, "⚠️ 환율 정보를 가져오지 못했어요. 잠시 후 다시 시도해주세요.")
                return

            base_amount = amount * rate
            fee = base_amount * 0.05
            total = base_amount + fee

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
                    "/선물 [포인트]\n\n"
                    "예시: /선물 100\n\n"
                    "⚠️ 최소 선물: 10포인트"
                )
                return

            parts = text.split()
            if len(parts) < 2 or not parts[1].isdigit():
                bot.reply_to(message,
                    "🎁 사용법: 선물할 상대의 메시지에 답장으로\n"
                    "/선물 [포인트]\n\n"
                    "예시: /선물 100\n\n"
                    "⚠️ 최소 선물: 10포인트"
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
                    f"💸 포인트가 부족해요!\n"
                    f"  보유: {my_point}포인트\n"
                    f"  필요: {amount}포인트"
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
                "🎡 /룰렛 [배팅] - 룰렛\n"
                "✌️ /가위바위보 [가위/바위/보] - 가위바위보\n\n"
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

        # ==================== /가위바위보 ====================
        elif '/가위바위보' in text:
            if message.chat.type == 'private':
                return

            point = get_point(user_id, group_id)
            if point < 20:
                bot.reply_to(message, f"💸 포인트가 부족해요!\n참가비: 20포인트\n현재 포인트: {point}포인트")
                return

            choices = ['✊ 바위', '✌️ 가위', '🖐 보']
            user_choice = None
            for c in choices:
                if c.split()[1] in text:
                    user_choice = c
                    break

            if not user_choice:
                bot.reply_to(message,
                    "✌️ 사용법: /가위바위보 [가위/바위/보]\n"
                    "예시: /가위바위보 가위\n\n"
                    "⚠️ 참가비: 20포인트\n"
                    "  이기면 40포인트 획득!"
                )
                return

            bot_choice = random.choice(choices)
            update_point(user_id, group_id, first_name, username, -20)

            if user_choice == bot_choice:
                result_text, won = "🤝 비겼어요!", 0
                update_point(user_id, group_id, first_name, username, 20)
            elif (user_choice == '✊ 바위' and bot_choice == '✌️ 가위') or \
                 (user_choice == '✌️ 가위' and bot_choice == '🖐 보') or \
                 (user_choice == '🖐 보' and bot_choice == '✊ 바위'):
                result_text, won = "🎉 이겼어요!", 20
                update_point(user_id, group_id, first_name, username, 40)
            else:
                result_text, won = "💀 졌어요!", -20

            new_point = get_point(user_id, group_id)
            bot.reply_to(message,
                f"╔══ ✌️ 가위바위보 ══╗\n"
                f"  나:  {user_choice}\n"
                f"  봇:  {bot_choice}\n\n"
                f"  {result_text}\n\n"
                f"  {'획득: +' + str(won) if won > 0 else '참가비 반환!' if won == 0 else '손실: ' + str(won)}포인트\n"
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
                "SELECT first_name, username, COUNT(*) as cnt FROM chat_logs WHERE group_id=%s AND message_date>=%s GROUP BY user_id, first_name, username ORDER BY cnt DESC LIMIT 5",
                (group_id, monday)
            )
            rows = cursor.fetchall()
            cursor.close()
            db.close()
            medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
            result = f"╔══ 🏆 주간 랭킹 ══╗\n"
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
            cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND DATE(message_date)=%s", (user_id, group_id, today))
            today_count = cursor.fetchone()[0]
            monday = today - timedelta(days=today.weekday())
            cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND message_date>=%s", (user_id, group_id, monday))
            week_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND EXTRACT(YEAR FROM message_date)=EXTRACT(YEAR FROM NOW()) AND EXTRACT(MONTH FROM message_date)=EXTRACT(MONTH FROM NOW())", (user_id, group_id))
            month_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s", (user_id, group_id))
            total_count = cursor.fetchone()[0]
            cursor.close()
            db.close()
            result = f"╔══ 📊 채팅 통계 ══╗\n"
            result += f"  👤 {first_name}님\n\n"
            result += f"  ☀️ 오늘       {today_count}개\n"
            result += f"  📆 이번 주   {week_count}개\n"
            result += f"  🗓 이번 달   {month_count}개\n"
            result += f"  💬 전체      {total_count}개\n\n"
            result += f"  🎀 오늘도 열심히 채팅했어요!\n"
            result += "╚══════════════════╝"
            bot.reply_to(message, result)

        # ==================== /승 또는 /패 ====================
        elif text.strip().startswith('/승') or text.strip().startswith('/패'):
            if message.chat.type == 'private':
                return

            current_time = now_kst.time()
            start_time = datetime.strptime("18:00", "%H:%M").time()
            end_time   = datetime.strptime("18:30", "%H:%M").time()

            if not (start_time <= current_time <= end_time):
                bot.reply_to(message,
                    "🚫 지금은 참여 시간이 아닙니다.\n\n"
                    "⏰ PM 18:00 ~ 18:30 배팅 시간입니다."
                )
                return

            vote_type = '승' if text.strip().startswith('/승') else '패'

            db = get_db()
            cursor = db.cursor()

            cursor.execute("""
                SELECT vote_type FROM vote_list
                WHERE user_id=%s AND group_id=%s AND vote_date=%s
            """, (user_id, group_id, today))
            existing = cursor.fetchone()

            if existing:
                cursor.close()
                db.close()
                bot.reply_to(message,
                    f"⚠️ 이미 오늘 [{existing[0]}] 으로 참여하셨어요!\n"
                    f"하루에 한 번만 참여할 수 있어요."
                )
                return

            cursor.execute("""
                INSERT INTO vote_list (user_id, group_id, first_name, username, vote_type, vote_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, group_id, first_name, username, vote_type, today))
            db.commit()

            cursor.execute("""
                SELECT COUNT(*) FROM vote_list
                WHERE group_id=%s AND vote_date=%s AND vote_type='승'
            """, (group_id, today))
            win_count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM vote_list
                WHERE group_id=%s AND vote_date=%s AND vote_type='패'
            """, (group_id, today))
            lose_count = cursor.fetchone()[0]

            cursor.close()
            db.close()

            emoji = '🏆' if vote_type == '승' else '💀'
            bot.reply_to(message,
                f"╔══ {emoji} 투표 완료 ══╗\n"
                f"  👤 {first_name}님\n"
                f"  선택: [{vote_type}]\n\n"
                f"  🏆 승: {win_count}명\n"
                f"  💀 패: {lose_count}명\n"
                f"╚══════════════════╝"
            )

        # ==================== /리스트 ====================
        elif text.strip().startswith('/리스트'):
            if message.chat.type == 'private':
                return

            db = get_db()
            cursor = db.cursor()

            cursor.execute("""
                SELECT first_name, username, vote_type
                FROM vote_list
                WHERE group_id=%s AND vote_date=%s
                ORDER BY vote_type, created_at
            """, (group_id, today))
            rows = cursor.fetchall()
            cursor.close()
            db.close()

            if not rows:
                bot.reply_to(message, "📋 오늘 참여한 사람이 없어요!")
                return

            win_list  = [r[0] or r[1] or '익명' for r in rows if r[2] == '승']
            lose_list = [r[0] or r[1] or '익명' for r in rows if r[2] == '패']

            result = f"╔══ 📋 오늘의 투표 리스트 ══╗\n"
            result += f"  📅 {today.strftime('%Y년 %m월 %d일')}\n\n"

            result += f"  🏆 승 ({len(win_list)}명)\n"
            if win_list:
                for name in win_list:
                    result += f"    • {name}\n"
            else:
                result += "    아직 없어요\n"

            result += f"\n  💀 패 ({len(lose_list)}명)\n"
            if lose_list:
                for name in lose_list:
                    result += f"    • {name}\n"
            else:
                result += "    아직 없어요\n"

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
