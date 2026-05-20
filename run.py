import telebot
import pyotp
import instaloader
import os
import sys
import time
import openpyxl
import random
import threading
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from concurrent.futures import ThreadPoolExecutor

# ========== LOCAL DATA STORAGE (JSON) ==========
DATA_FILE = "bot_data.json"

def load_local_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            return {"authorized_users": [6412225513], "good_accounts": []}
    return {"authorized_users": [6412225513], "good_accounts": []}

def save_local_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_local_data()
ADMIN_ID = 6412225513

def is_authorized(user_id):
    if user_id == ADMIN_ID: return True
    return user_id in data.get("authorized_users", [])

# ========== DYNAMIC BOT SETUP ==========
def start_bot():
    token = input("Enter your Telegram Bot Token: ").strip()
    if not token:
        print("Invalid Token!")
        return
    
    bot = telebot.TeleBot(token)
    user_sessions = {}

    def get_main_menu(user_id):
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(KeyboardButton("🚀 Start Processing"), KeyboardButton("❓ Help"))
        if user_id == ADMIN_ID:
            markup.add(KeyboardButton("👑 Admin Panel"))
        return markup

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        if not is_authorized(message.chat.id):
            bot.send_message(message.chat.id, "Access Denied!")
            return
        bot.send_message(message.chat.id, "Mass IG Extractor PRO\nUpload your .xlsx file.", reply_markup=get_main_menu(message.chat.id))

    @bot.message_handler(func=lambda message: message.text in ["👑 Admin Panel", "🚀 Start Processing", "❓ Help"])
    def handle_menu_buttons(message):
        chat_id = message.chat.id
        text = message.text

        if text == "👑 Admin Panel" and chat_id == ADMIN_ID:
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("Add User", callback_data="admin_add_user"), InlineKeyboardButton("Remove User", callback_data="admin_remove_user"))
            bot.send_message(chat_id, "Admin Panel", reply_markup=markup)
        elif text == "🚀 Start Processing":
            bot.send_message(chat_id, "Please upload your .xlsx file.")

    def batch_processor(chat_id):
        session = user_sessions[chat_id]
        session['is_processing'] = True
        batch = session['remaining'][:100]
        session['remaining'] = session['remaining'][100:]
        
        def worker(acc):
            username, password, two_fa = acc
            try:
                totp = pyotp.TOTP(two_fa.replace(" ", ""))
                L = instaloader.Instaloader()
                L.login(username, password)
                
                if L.context._session.cookies:
                    cookie_dict = {cookie.name: cookie.value for cookie in L.context._session.cookies}
                    if 'sessionid' in cookie_dict:
                        raw_cookie = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
                        session['good'].append((username, password, two_fa, raw_cookie))
                    else:
                        session['suspended'].append(acc)
                else:
                    session['bad'].append(acc)
            except Exception:
                session['bad'].append(acc)

        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(worker, batch)
        
        session['is_processing'] = False
        bot.send_message(chat_id, f"Batch finished. Good: {len(session['good'])}")

    @bot.message_handler(content_types=['document'])
    def handle_document(message):
        chat_id = message.chat.id
        if not is_authorized(chat_id): return
        
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("input.xlsx", 'wb') as f: f.write(downloaded_file)
        
        wb = openpyxl.load_workbook("input.xlsx")
        sheet = wb.active
        valid_accounts = []
        for row in sheet.iter_rows(values_only=True):
            if len(row) >= 3 and row[0]:
                valid_accounts.append((str(row[0]), str(row[1]), str(row[2])))
                
        user_sessions[chat_id] = {'remaining': valid_accounts, 'good': [], 'bad': [], 'suspended': []}
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Start", callback_data="start_batch"))
        bot.send_message(chat_id, f"File received. {len(valid_accounts)} accounts found.", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: True)
    def callback_query(call):
        if call.data == "start_batch":
            threading.Thread(target=batch_processor, args=(call.message.chat.id,)).start()
            bot.send_message(call.message.chat.id, "Processing started...")

    print("Bot is running...")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    start_bot()
