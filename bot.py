import os
import asyncio
from datetime import datetime, timedelta, timezone
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiohttp import web

# --- CẤU HÌNH ---
API_TOKEN = "8705440748:AAH4pKvslCzJfapxmjvI1U69k7Kgo7VYvPA"
BOT_USERNAME = "@AATMPAY68Ubot"
ADMIN_IDS = [2106916939, 228160692]
RATE_FILE_USDT = "rate_usdt.txt"
FEE_FILE = "fee.txt"
COUNTER_FILE = "counter.txt"
DATE_FILE = "last_date.txt"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- HÀM HỖ TRỢ ---
def format_vn(value):
    return f"{value:,.0f}".replace(",", ".")

def get_value(file_path, default):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try: return float(f.read().strip())
            except: return default
    return default

def save_value(file_path, value):
    with open(file_path, "w") as f:
        f.write(str(value))

# --- BỘ ĐẾM ORDER ---
def get_next_order_id():
    tz_vietnam = timezone(timedelta(hours=7))
    today = datetime.now(tz_vietnam).strftime("%Y-%m-%d")
    if os.path.exists(DATE_FILE):
        with open(DATE_FILE, "r") as f:
            last_date = f.read().strip()
    else:
        last_date = ""
    
    if last_date != today:
        current_counter = 1
        save_value(DATE_FILE, today)
    else:
        current_counter = int(get_value(COUNTER_FILE, 1))
    
    save_value(COUNTER_FILE, current_counter + 1)
    return current_counter

# --- LỆNH ADMIN ---
@dp.message(Command("setrate"))
async def set_rate(message: Message):
    if message.from_user.id not in ADMIN_IDS: return
    try:
        val = float(message.text.split()[1])
        save_value(RATE_FILE_USDT, val)
        await message.answer(f"✅ Tỷ giá VND/USDT: {format_vn(val)}")
    except: await message.answer("⚠️ Lỗi định dạng.")

@dp.message(Command("setfee"))
async def set_fee(message: Message):
    if message.from_user.id not in ADMIN_IDS: return
    try:
        val = float(message.text.split()[1].replace('%', ''))
        save_value(FEE_FILE, val)
        await message.answer(f"✅ Đã cập nhật phí: {val}%")
    except: await message.answer("⚠️ Lỗi định dạng.")

# --- XỬ LÝ ĐỐI SOÁT ---
@dp.message()
async def process_message(message: Message):
    if not message.text or BOT_USERNAME not in message.text: return
    
    raw_text = message.text.replace(BOT_USERNAME, "").strip()
    clean_text = raw_text.replace(',', '').replace('.', '')
    
    if clean_text.isdigit():
        try:
            import_vnd = float(clean_text)
            
            rate_vnd_usdt = get_value(RATE_FILE_USDT, 25000)
            fee_percent = get_value(FEE_FILE, 6.0)
            
            fee_amount = import_vnd * (fee_percent / 100)
            remaining_vnd = import_vnd - fee_amount
            usdt_amount = remaining_vnd / rate_vnd_usdt
            
            order_id = get_next_order_id()
            current_time = datetime.now(timezone(timedelta(hours=7))).strftime("%H:%M:%S - %d/%m/%Y")
            
            response = (
                f"📊 **KẾT QUẢ ĐỐI SOÁT**\n\n"
                f"Order: #{order_id} | {current_time}\n"
                f"--------------------------\n"
                f"Số tiền: {format_vn(import_vnd)} VND\n"
                f"=> Phí ({fee_percent}%): {format_vn(fee_amount)} VND\n"
                f"=> Thực nhận (VND): {format_vn(remaining_vnd)} VND\n"
                f"--------------------------\n"
                f"Tỷ giá: {format_vn(rate_vnd_usdt)}\n"
                f"Quy đổi sang USDT: **{usdt_amount:.2f} USDT**"
            )
            await message.answer(response, parse_mode="Markdown")
        except Exception as e:
            print(f"Lỗi logic: {e}")

async def start_web_server():
    app = web.Application()
    app.add_routes([web.get('/', lambda r: web.Response(text="Bot is alive"))])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000)))
    await site.start()

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())