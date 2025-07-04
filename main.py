import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
import json
import os

API_TOKEN = '7981318315:AAEkfUPrjUy53ffzr4Cfbks7ryXW22DHLmM'
CHANNEL_USERNAME = '@fbreport360'
VOTE_LINK = 'https://example.com/vote-demo'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

users_file = "users.json"

if not os.path.exists(users_file):
    with open(users_file, "w") as f:
        json.dump({}, f)

def load_users():
    with open(users_file, "r") as f:
        return json.load(f)

def save_users(data):
    with open(users_file, "w") as f:
        json.dump(data, f)

class WithdrawForm(StatesGroup):
    waiting_for_number = State()
    waiting_for_amount = State()
    waiting_for_note = State()

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    users = load_users()
    user_id = str(message.from_user.id)

    if user_id not in users:
        users[user_id] = {"balance": 0, "ref_by": None}
        args = message.get_args()
        if args and args.isdigit():
            users[user_id]["ref_by"] = args
            if args in users:
                users[args]["balance"] += 5  # Refer bonus
        save_users(users)

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🗳️ Vote Now", url=VOTE_LINK),
        InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"),
        InlineKeyboardButton("👥 Refer & Earn", callback_data="refer"),
        InlineKeyboardButton("💰 My Balance", callback_data="balance"),
        InlineKeyboardButton("🧾 Withdraw", callback_data="withdraw"),
    )
    await message.answer("👋 Welcome! Choose an option below:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == "refer")
async def show_refer(call: types.CallbackQuery):
    user_id = call.from_user.id
    link = f"https://t.me/{(await bot.get_me()).username}?start={user_id}"
    await call.message.answer(f"👥 Your referral link:
{link}")

@dp.callback_query_handler(lambda c: c.data == "balance")
async def show_balance(call: types.CallbackQuery):
    users = load_users()
    user_id = str(call.from_user.id)
    balance = users.get(user_id, {}).get("balance", 0)
    await call.message.answer(f"💰 Your current balance: {balance} points")

@dp.callback_query_handler(lambda c: c.data == "withdraw")
async def start_withdraw(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📱 Enter your bKash number:")
    await WithdrawForm.waiting_for_number.set()

@dp.message_handler(state=WithdrawForm.waiting_for_number)
async def get_number(message: types.Message, state: FSMContext):
    await state.update_data(number=message.text)
    await message.answer("💸 Enter amount to withdraw:")
    await WithdrawForm.waiting_for_amount.set()

@dp.message_handler(state=WithdrawForm.waiting_for_amount)
async def get_amount(message: types.Message, state: FSMContext):
    await state.update_data(amount=message.text)
    await message.answer("📝 Enter a note (optional):")
    await WithdrawForm.waiting_for_note.set()

@dp.message_handler(state=WithdrawForm.waiting_for_note)
async def get_note(message: types.Message, state: FSMContext):
    data = await state.get_data()
    note = message.text
    withdraw_info = f"🧾 Withdraw Request

📱 Number: {data['number']}
💸 Amount: {data['amount']}
📝 Note: {note}
👤 User: @{message.from_user.username or message.from_user.id}"
    await bot.send_message(chat_id=YOUR_ADMIN_ID, text=withdraw_info)
    await message.answer("✅ Your request has been submitted.")
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
