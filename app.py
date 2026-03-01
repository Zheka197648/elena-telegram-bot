import os
import logging
from flask import Flask, request, jsonify
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
import asyncio
import threading

# === Настройка логирования ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Переменные окружения ===
# === НАСТРОЙКИ БОТА (жёстко прописаны) ===
BOT_TOKEN = '7864111232:AAFVqAvCuvyP7SlT8jXRQjVgGV2i1O0w37Y'
ELENA_CHAT_ID = '1033584084'
SITE_URL = 'https://elena-realtor.pages.dev'
# ==========================================
# === Инициализация ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = Flask(__name__)

# === Машина состояний ===
class ClientSurvey(StatesGroup):
    waiting_for_property_type = State()
    waiting_for_rooms = State()
    waiting_for_budget = State()
    waiting_for_district = State()
    waiting_for_timeline = State()
    waiting_for_payment = State()
    waiting_for_floor = State()
    waiting_for_area = State()
    waiting_for_amenities = State()
    waiting_for_renovation = State()

# === Данные клиента ===
client_data = {}

# === Словари ответов ===
PROPERTY_TYPES = {
    "prop_apartment": "🏢 Квартира",
    "prop_house": "🏡 Частный дом",
    "prop_newbuilding": "🏗 Новостройка",
    "prop_invest": "🔄 Инвестировать"
}

ROOMS = {
    "room_studio": "🚪 Студия",
    "room_1": "1️⃣ Одна комната",
    "room_2": "2️⃣ Две комнаты",
    "room_3": "3️⃣ Три комнаты",
    "room_4plus": "4️⃣ Четыре+ комнаты",
    "room_any": "❓ Не важно"
}

BUDGETS = {
    "budget_under3": "до 3 млн ₽",
    "budget_3to5": "3–5 млн ₽",
    "budget_5to7": "5–7 млн ₽",
    "budget_7to10": "7–10 млн ₽",
    "budget_10plus": "10+ млн ₽",
    "budget_discuss": "💬 Обсудить"
}

DISTRICTS = {
    "dist_center": "🎯 Центр",
    "dist_sunny": "☀️ Солнечный",
    "dist_lenino": "🌲 Ново-Ленино",
    "dist_oktyabr": "🚉 Октябрьский",
    "dist_sverdlov": "🏭 Свердловский",
    "dist_rightbank": "🌊 Правобережный",
    "dist_any": "🗺 Любой район",
    "dist_custom": "📍 Свой вариант"
}

TIMELINES = {
    "time_urgent": "⚡ Срочно (до 2 недель)",
    "time_month": "📅 В течение месяца",
    "time_1to3months": "🗓 1–3 месяца",
    "time_looking": "🔍 Просто присматриваюсь"
}

PAYMENTS = {
    "pay_cash": "💵 Наличные",
    "pay_mortgage_approved": "🏦 Ипотека (одобрена)",
    "pay_mortgage_help": "❓ Нужна помощь с ипотекой",
    "pay_sell_own": "🔄 Продажа своей недвижимости"
}

FLOORS = {
    "floor_any": "📊 Не важно",
    "floor_not_first": "⬇️ Не первый",
    "floor_not_last": "⬆️ Не последний",
    "floor_middle": "🎯 Только средний (3–5 этаж)",
    "floor_high": "🌆 Только высокий с видом"
}

AREAS = {
    "area_under30": "до 30 м²",
    "area_30to50": "30–50 м²",
    "area_50to70": "50–70 м²",
    "area_70to100": "70–100 м²",
    "area_100plus": "100+ м²",
    "area_custom": "💬 Напишу сам"
}

RENOVATIONS = {
    "reno_any": "✅ Ремонт не важен",
    "reno_with": "✨ Хочу с ремонтом",
    "reno_self": "🔨 Готов делать сам",
    "reno_comment": "💬 Напишу комментарий"
}

AMENITIES = {
    "amen_transport": "🚌 Транспорт",
    "amen_school": "🎓 Школа/сад",
    "amen_shops": "🛒 Магазины",
    "amen_park": "🌳 Парк",
    "amen_clinic": "🏥 Поликлиника",
    "amen_parking": "🚗 Парковка",
    "amen_quiet": "🔇 Тишина"
}

# === Клавиатуры ===
def get_property_type_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏢 Квартира", callback_data="prop_apartment"))
    builder.row(InlineKeyboardButton(text="🏡 Частный дом", callback_data="prop_house"))
    builder.row(InlineKeyboardButton(text="🏗 Новостройка", callback_data="prop_newbuilding"))
    builder.row(InlineKeyboardButton(text="🔄 Инвестировать", callback_data="prop_invest"))
    return builder.as_markup()

def get_rooms_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🚪 Студия", callback_data="room_studio"))
    builder.row(
        InlineKeyboardButton(text="1️⃣ Одна", callback_data="room_1"),
        InlineKeyboardButton(text="2️⃣ Две", callback_data="room_2")
    )
    builder.row(
        InlineKeyboardButton(text="3️⃣ Три", callback_data="room_3"),
        InlineKeyboardButton(text="4️⃣ Четыре+", callback_data="room_4plus")
    )
    builder.row(InlineKeyboardButton(text="❓ Не важно", callback_data="room_any"))
    return builder.as_markup()

def get_budget_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="до 3 млн ₽", callback_data="budget_under3"))
    builder.row(InlineKeyboardButton(text="3–5 млн ₽", callback_data="budget_3to5"))
    builder.row(InlineKeyboardButton(text="5–7 млн ₽", callback_data="budget_5to7"))
    builder.row(InlineKeyboardButton(text="7–10 млн ₽", callback_data="budget_7to10"))
    builder.row(InlineKeyboardButton(text="10+ млн ₽", callback_data="budget_10plus"))
    builder.row(InlineKeyboardButton(text="💬 Обсудить", callback_data="budget_discuss"))
    return builder.as_markup()

def get_district_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎯 Центр", callback_data="dist_center"),
        InlineKeyboardButton(text="☀️ Солнечный", callback_data="dist_sunny")
    )
    builder.row(
        InlineKeyboardButton(text="🌲 Ново-Ленино", callback_data="dist_lenino"),
        InlineKeyboardButton(text="🚉 Октябрьский", callback_data="dist_oktyabr")
    )
    builder.row(
        InlineKeyboardButton(text="🏭 Свердловский", callback_data="dist_sverdlov"),
        InlineKeyboardButton(text="🌊 Правобережный", callback_data="dist_rightbank")
    )
    builder.row(
        InlineKeyboardButton(text="🗺 Любой", callback_data="dist_any"),
        InlineKeyboardButton(text="📍 Свой вариант", callback_data="dist_custom")
    )
    return builder.as_markup()

def get_timeline_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⚡ Срочно (до 2 недель)", callback_data="time_urgent"))
    builder.row(InlineKeyboardButton(text="📅 В течение месяца", callback_data="time_month"))
    builder.row(InlineKeyboardButton(text="🗓 1–3 месяца", callback_data="time_1to3months"))
    builder.row(InlineKeyboardButton(text="🔍 Просто присматриваюсь", callback_data="time_looking"))
    return builder.as_markup()

def get_payment_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💵 Наличные", callback_data="pay_cash"))
    builder.row(InlineKeyboardButton(text="🏦 Ипотека (одобрена)", callback_data="pay_mortgage_approved"))
    builder.row(InlineKeyboardButton(text="❓ Нужна помощь с ипотекой", callback_data="pay_mortgage_help"))
    builder.row(InlineKeyboardButton(text="🔄 Продажа своей недвижимости", callback_data="pay_sell_own"))
    return builder.as_markup()

def get_floor_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📊 Не важно", callback_data="floor_any"))
    builder.row(InlineKeyboardButton(text="⬇️ Не первый", callback_data="floor_not_first"))
    builder.row(InlineKeyboardButton(text="⬆️ Не последний", callback_data="floor_not_last"))
    builder.row(InlineKeyboardButton(text="🎯 Только средний (3–5 этаж)", callback_data="floor_middle"))
    builder.row(InlineKeyboardButton(text="🌆 Только высокий с видом", callback_data="floor_high"))
    return builder.as_markup()

def get_area_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="до 30 м²", callback_data="area_under30"))
    builder.row(InlineKeyboardButton(text="30–50 м²", callback_data="area_30to50"))
    builder.row(InlineKeyboardButton(text="50–70 м²", callback_data="area_50to70"))
    builder.row(InlineKeyboardButton(text="70–100 м²", callback_data="area_70to100"))
    builder.row(InlineKeyboardButton(text="100+ м²", callback_data="area_100plus"))
    builder.row(InlineKeyboardButton(text="💬 Напишу сам", callback_data="area_custom"))
    return builder.as_markup()

def get_amenities_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🚌 Транспорт", callback_data="amen_transport"),
        InlineKeyboardButton(text="🎓 Школа/сад", callback_data="amen_school")
    )
    builder.row(
        InlineKeyboardButton(text="🛒 Магазины", callback_data="amen_shops"),
        InlineKeyboardButton(text="🌳 Парк", callback_data="amen_park")
    )
    builder.row(
        InlineKeyboardButton(text="🏥 Поликлиника", callback_data="amen_clinic"),
        InlineKeyboardButton(text="🚗 Парковка", callback_data="amen_parking")
    )
    builder.row(
        InlineKeyboardButton(text="🔇 Тишина", callback_data="amen_quiet"),
        InlineKeyboardButton(text="✅ Далее", callback_data="amen_done")
    )
    return builder.as_markup()

def get_renovation_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Ремонт не важен", callback_data="reno_any"))
    builder.row(InlineKeyboardButton(text="✨ Хочу с ремонтом", callback_data="reno_with"))
    builder.row(InlineKeyboardButton(text="🔨 Готов делать сам", callback_data="reno_self"))
    builder.row(InlineKeyboardButton(text="💬 Напишу комментарий", callback_data="reno_comment"))
    return builder.as_markup()

# === Обработчики ===

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    args = message.text.split()
    lead_id = args[1] if len(args) > 1 else "unknown"
    
    await state.update_data(lead_id=lead_id)
    await state.update_data(client_id=message.from_user.id)
    await state.update_data(client_name=message.from_user.first_name)
    await state.update_data(client_username=message.from_user.username or "не указан")
    await state.update_data(client_phone="не указан")
    await state.update_data(amenities=[])
    
    welcome_text = f"""
👋 Здравствуйте, {message.from_user.first_name}!

Я помощник Елены Ямковой — риелтора в Иркутске.

Вижу, вы оставили заявку на подбор недвижимости. 
Давайте уточним несколько деталей — это займёт всего 2-3 минуты!

Начнём? 👇
    """
    
    await message.answer(welcome_text, reply_markup=get_property_type_keyboard())
    await state.set_state(ClientSurvey.waiting_for_property_type)

@dp.callback_query(ClientSurvey.waiting_for_property_type)
async def process_property_type(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(property_type=callback.data)
    await callback.message.edit_text(f"✅ Вы выбрали: {PROPERTY_TYPES[callback.data]}\n\n📍 Следующий вопрос:", reply_markup=None)
    await callback.message.answer("2️⃣ Сколько комнат вы рассматриваете?", reply_markup=get_rooms_keyboard())
    await state.set_state(ClientSurvey.waiting_for_rooms)
    await callback.answer()

@dp.callback_query(ClientSurvey.waiting_for_rooms)
async def process_rooms(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(rooms=callback.data)
    await callback.message.edit_text(f"✅ Вы выбрали: {ROOMS[callback.data]}\n\n📍 Следующий вопрос:", reply_markup=None)
    await callback.message.answer("3️⃣ Какой у вас бюджет?", reply_markup=get_budget_keyboard())
    await state.set_state(ClientSurvey.waiting_for_budget)
    await callback.answer()

@dp.callback_query(ClientSurvey.waiting_for_budget)
async def process_budget(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(budget=callback.data)
    await callback.message.edit_text(f"✅ Вы выбрали: {BUDGETS[callback.data]}\n\n📍 Следующий вопрос:", reply_markup=None)
    await callback.message.answer("4️⃣ Какой район Иркутска вас интересует?", reply_markup=get_district_keyboard())
    await state.set_state(ClientSurvey.waiting_for_district)
    await callback.answer()

@dp.callback_query(ClientSurvey.waiting_for_district)
async def process_district(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(district=callback.data)
    await callback.message.edit_text(f"✅ Вы выбрали: {DISTRICTS[callback.data]}\n\n📍 Следующий вопрос:", reply_markup=None)
    await callback.message.answer("5️⃣ Когда планируете покупку?", reply_markup=get_timeline_keyboard())
    await state.set_state(ClientSurvey.waiting_for_timeline)
    await callback.answer()

@dp.callback_query(ClientSurvey.waiting_for_timeline)
async def process_timeline(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(timeline=callback.data)
    await callback.message.edit_text(f"✅ Вы выбрали: {TIMELINES[callback.data]}\n\n📍 Следующий вопрос:", reply_markup=None)
    await callback.message.answer("6️⃣ Как будете оплачивать?", reply_markup=get_payment_keyboard())
    await state.set_state(ClientSurvey.waiting_for_payment)
    await callback.answer()

@dp.callback_query(ClientSurvey.waiting_for_payment)
async def process_payment(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(payment=callback.data)
    await callback.message.edit_text(f"✅ Вы выбрали: {PAYMENTS[callback.data]}\n\n📍 Следующий вопрос:", reply_markup=None)
    await callback.message.answer("7️⃣ Есть ли предпочтения по этажу?", reply_markup=get_floor_keyboard())
    await state.set_state(ClientSurvey.waiting_for_floor)
    await callback.answer()

@dp.callback_query(ClientSurvey.waiting_for_floor)
async def process_floor(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(floor=callback.data)
    await callback.message.edit_text(f"✅ Вы выбрали: {FLOORS[callback.data]}\n\n📍 Следующий вопрос:", reply_markup=None)
    await callback.message.answer("8️⃣ Какая площадь вам нужна?", reply_markup=get_area_keyboard())
    await state.set_state(ClientSurvey.waiting_for_area)
    await callback.answer()

@dp.callback_query(ClientSurvey.waiting_for_area)
async def process_area(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(area=callback.data)
    await callback.message.edit_text(f"✅ Вы выбрали: {AREAS[callback.data]}\n\n📍 Следующий вопрос:", reply_markup=None)
    await callback.message.answer("9️⃣ Что для вас важно рядом с домом?\n<i>(можно выбрать несколько, затем «Далее»)</i>", reply_markup=get_amenities_keyboard())
    await state.set_state(ClientSurvey.waiting_for_amenities)
    await callback.answer()

@dp.callback_query(ClientSurvey.waiting_for_amenities)
async def process_amenities(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "amen_done":
        data = await state.get_data()
        amenities = data.get("amenities", [])
        amenities_text = ", ".join([AMENITIES.get(a, a) for a in amenities]) if amenities else "Не указано"
        await state.update_data(amenities_final=amenities_text)
        await callback.message.edit_text(f"✅ Инфраструктура: {amenities_text}\n\n📍 Последний вопрос:", reply_markup=None)
        await callback.message.answer("🔟 Какие пожелания по ремонту?", reply_markup=get_renovation_keyboard())
        await state.set_state(ClientSurvey.waiting_for_renovation)
    else:
        data = await state.get_data()
        amenities = data.get("amenities", [])
        if callback.data in amenities:
            amenities.remove(callback.data)
        else:
            amenities.append(callback.data)
        await state.update_data(amenities=amenities)
        await callback.message.answer(f"✅ Добавлено: {AMENITIES.get(callback.data, callback.data)}\nВыберите ещё или нажмите «Далее»:", reply_markup=get_amenities_keyboard())
    await callback.answer()

@dp.callback_query(ClientSurvey.waiting_for_renovation)
async def process_renovation(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(renovation=callback.data)
    await callback.message.edit_text(f"✅ Вы выбрали: {RENOVATIONS[callback.data]}\n\n", reply_markup=None)
    await send_survey_to_elena(callback.message, state)
    await state.clear()
    await callback.answer()

# === Отправка анкеты Елене ===

async def send_survey_to_elena(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    survey_text = f"""
🎯 <b>НОВАЯ КВАЛИФИЦИРОВАННАЯ ЗАЯВКА</b>
━━━━━━━━━━━━━━━━━━━━
👤 <b>Клиент:</b> {data.get('client_name', 'Не указано')}
📱 <b>Telegram:</b> @{data.get('client_username', 'не указан')}
🆔 <b>ID заявки:</b> {data.get('lead_id', 'unknown')}
📅 <b>Дата:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}

🏠 <b>Параметры поиска:</b>
• Тип: {PROPERTY_TYPES.get(data.get('property_type'), 'Не указано')}
• Комнат: {ROOMS.get(data.get('rooms'), 'Не указано')}
• Бюджет: {BUDGETS.get(data.get('budget'), 'Не указано')}
• Район: {DISTRICTS.get(data.get('district'), 'Не указано')}
• Срок: {TIMELINES.get(data.get('timeline'), 'Не указано')}
• Оплата: {PAYMENTS.get(data.get('payment'), 'Не указано')}
• Этаж: {FLOORS.get(data.get('floor'), 'Не указано')}
• Площадь: {AREAS.get(data.get('area'), 'Не указано')}
• Инфраструктура: {data.get('amenities_final', 'Не указано')}
• Ремонт: {RENOVATIONS.get(data.get('renovation'), 'Не указано')}

🔗 <b>Источник:</b> {SITE_URL}
━━━━━━━━━━━━━━━━━━━━
✅ <b>Готова к показу!</b>
    """
    
    try:
        await bot.send_message(chat_id=ELENA_CHAT_ID, text=survey_text, parse_mode="HTML")
        thank_text = f"""
🎉 <b>Спасибо за ответы!</b>

Елена уже получила вашу анкету и в ближайшее время свяжется с вами!

📞 Если нужно срочно: 8 (904) 146-10-81
💬 Или напишите: @Elena_Yamkovaya

Хорошего дня! 🏠
        """
        await message.answer(thank_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
        await message.answer("⚠️ Ошибка. Позвоните: 8 (904) 146-10-81")

# === Flask Webhook ===

@app.route('/webhook', methods=['POST'])
async def webhook():
    update = await request.json
    asyncio.create_task(dp.feed_webhook_update(bot, types.Update(**update), bot))
    return jsonify({'ok': True})

@app.route('/')
def home():
    return '🤖 Бот работает! Webhook: /webhook'

# === Запуск ===

def run_flask():
    app.run(host='0.0.0.0', port=7860)

if __name__ == '__main__':
    thread = threading.Thread(target=run_flask)
    thread.start()

    logger.info("🚀 Бот запущен на Hugging Face Spaces!")

