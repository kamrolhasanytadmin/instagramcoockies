import telebot
import pyotp
import instaloader
import os
import sys
import time
import openpyxl
import random
import threading
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from concurrent.futures import ThreadPoolExecutor

# নেটওয়ার্ক ড্রপ বা ভিপিএন চেঞ্জের সময় বিশাল এরর মেসেজ হাইড করার জন্য
telebot.logger.setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner():
    clear_screen()
    banner = """
\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
\033[1;32m      🔥 MASS IG COOKIE EXTRACTOR PRO 🔥
\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
\033[1;33m[+] Developer : \033[1;37mKamrol
\033[1;33m[+] Version   : \033[1;37m10.0 (Ultimate Tor Auto)
\033[1;33m[+] Features  : \033[1;37m100 IDs -> Tor IP Change -> Auto Resume
\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m
    """
    print(banner)

show_banner()
while True:
    TOKEN = input("\033[1;32m🔑 Enter Your Telegram Bot Token: \033[0m").strip()
    if TOKEN:
        break

try:
    bot = telebot.TeleBot(TOKEN)
    bot_info = bot.get_me()
    print(f"\n\033[1;32m✅ Successfully Logged in as: @{bot_info.username}\033[0m")
    print("\033[1;33m[!] Type \033[1;31m/stop\033[1;33m in terminal to shut down the bot.\033[0m\n")
except Exception as e:
    print("\n\033[1;31m❌ Invalid Token! Please check your token and run again.\033[0m")
    sys.exit()

user_sessions = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    welcome_text = (
        "🔥 *MASS IG Extractor PRO (Tor Auto)* 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ *অটো প্রক্সি:* ১০০টা করে আইডি চেক করবে, নিজে থেকে IP Change করবে এবং মেসেজ দিয়ে আবার শুরু করবে!\n"
        "👉 আপনার `.xlsx` (Excel) ফাইলটি আপলোড করুন।\n"
        "• কলাম A = Username | কলাম B = Pass | কলাম C = 2FA Key\n"
    )
    bot.send_message(chat_id, welcome_text, parse_mode='Markdown')

@bot.message_handler(content_types=['document'])
def handle_document(message):
    chat_id = message.chat.id
    if chat_id in user_sessions and user_sessions[chat_id].get('is_processing'):
        bot.send_message(chat_id, "⚠️ আপনার একটি কাজ রানিং আছে! আগে সেটি Stop করুন।")
        return

    try:
        file_name = message.document.file_name.lower()
        if not file_name.endswith('.xlsx'):
            bot.send_message(chat_id, "❌ দয়া করে শুধুমাত্র .xlsx (Excel) ফাইল আপলোড করুন!")
            return

        bot.send_message(chat_id, "📥 ফাইল রিসিভ হচ্ছে, একটু অপেক্ষা করুন...")
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_filename = f"input_{chat_id}.xlsx"
        with open(input_filename, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        wb = openpyxl.load_workbook(input_filename)
        sheet = wb.active
        
        valid_accounts = []
        for row in sheet.iter_rows(values_only=True):
            if len(row) >= 3 and row[0] and row[1] and row[2]:
                user = str(row[0]).strip()
                if user.lower() in ['username', 'user', 'id', 'user name']: continue
                valid_accounts.append((user, str(row[1]).strip(), str(row[2]).strip()))

        os.remove(input_filename)

        if not valid_accounts:
            bot.send_message(chat_id, "❌ ফাইলে কোনো সঠিক ডেটা পাওয়া যায়নি!")
            return

        user_sessions[chat_id] = {
            'remaining': valid_accounts.copy(),
            'good': [], 'bad': [], 'suspended': [],            
            'is_processing': False, 'stop_requested': False
        }

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("▶️ Start Auto Processing", callback_data="start_auto"))
        
        bot.send_message(
            chat_id, 
            f"✅ *ফাইল রিসিভ হয়েছে!*\n📦 *অ্যাকাউন্ট:* {len(valid_accounts)}\n\n"
            f"👇 অটোমেটিক কাজ শুরু করতে নিচের বাটনে ক্লিক করুন:", 
            reply_markup=markup, parse_mode='Markdown'
        )
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ ফাইল রিড করতে সমস্যা হয়েছে: {e}")

# অটো প্রসেসর থ্রেড (এটি ব্যাকগ্রাউন্ডে কাজ করবে)
def auto_processor(chat_id):
    session = user_sessions[chat_id]
    session['is_processing'] = True
    session['stop_requested'] = False
    
    while session['remaining'] and not session['stop_requested']:
        # ১০০টি করে অ্যাকাউন্টের ব্যাচ
        batch = session['remaining'][:100]
        session['remaining'] = session['remaining'][100:]
        unprocessed = []

        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("🛑 Stop Auto", callback_data="stop_batch"),
            InlineKeyboardButton("📥 Live Download", callback_data="live_download")
        )

        process_msg = bot.send_message(
            chat_id, 
            f"🔄 *Processing {len(batch)} Accounts...*\n(Tor Proxy Active)\n\n"
            f"🟢 Good: {len(session['good'])} | 🔴 Bad: {len(session['bad'])} | 🟡 Susp: {len(session['suspended'])}\n\n"
            f"মাঝপথে থামাতে চাইলে 'Stop Auto' চাপ দিন।", 
            reply_markup=markup, parse_mode='Markdown'
        )

        def worker(acc):
            if session['stop_requested']:
                unprocessed.append(acc)
                return
            username, password, two_fa = acc
            time.sleep(random.uniform(1.0, 3.0)) # অ্যান্টি-স্প্যাম গ্যাপ
            
            try:
                totp = pyotp.TOTP(two_fa.replace(" ", ""))
                two_fa_code = totp.now()

                L = instaloader.Instaloader()
                # 🚀 MAGIC: সবসময় Tor Proxy ব্যবহার করবে!
                L.context._session.proxies = {
                    "http": "socks5h://127.0.0.1:9050",
                    "https": "socks5h://127.0.0.1:9050"
                }
                
                try:
                    L.login(username, password)
                except instaloader.exceptions.TwoFactorAuthRequiredException:
                    L.two_factor_login(two_fa_code)
                except Exception:
                    session['bad'].append(acc)
                    return

                # লাইভ চেকার (সাসপেন্ড আইডি ধরার জন্য)
                try:
                    profile = instaloader.Profile.from_username(L.context, username)
                    _ = profile.followers
                except Exception:
                    session['suspended'].append(acc)
                    return

                cookie_dict = {cookie.name: cookie.value for cookie in L.context._session.cookies}
                if 'datr' not in cookie_dict: cookie_dict['datr'] = 'HS3naU6ORdMLlg8ma6NYa3hy'
                if 'wd' not in cookie_dict: cookie_dict['wd'] = f"{random.randint(360, 501)}x{random.randint(700, 954)}"
                if 'dpr' not in cookie_dict: cookie_dict['dpr'] = '2.15625'
                
                keys_order = ['datr', 'ig_did', 'mid', 'dpr', 'csrftoken', 'ds_user_id', 'sessionid', 'wd', 'rur']
                final_cookies = [f"{k}={cookie_dict[k]}" for k in keys_order if k in cookie_dict]
                for k, v in cookie_dict.items():
                    if k not in keys_order: final_cookies.append(f"{k}={v}")
                        
                raw_cookie_string = "; ".join(final_cookies)
                session['good'].append((username, password, raw_cookie_string))

            except Exception:
                session['bad'].append(acc)

        # স্পিড ২০ রাখা হয়েছে যাতে Tor এর স্পিডে ড্রপ না হয়
        with ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(worker, batch)

        if unprocessed:
            session['remaining'] = unprocessed + session['remaining']

        # কাজ শেষে বাটন মেসেজ ডিলিট
        try: bot.delete_message(chat_id, process_msg.message_id)
        except: pass

        if session['stop_requested']:
            break
            
        # ১০০টি শেষ, এবার Auto IP Change এবং নোটিফিকেশন
        if session['remaining']:
            wait_msg = bot.send_message(chat_id, "♻️ *100 Accounts Done!*\n\nChanging Tor IP... Please wait 10s...", parse_mode='Markdown')
            os.system("pkill -HUP tor") # Tor IP চেঞ্জ কমান্ড
            time.sleep(10) # নতুন আইপি কানেক্ট হওয়ার জন্য ১০ সেকেন্ড গ্যাপ
            try: bot.edit_message_text("✅ *Tor IP Changed Successfully!*\n\nAuto resuming next 100 batch...", chat_id=chat_id, message_id=wait_msg.message_id, parse_mode='Markdown')
            except: pass
            time.sleep(3)
            try: bot.delete_message(chat_id, wait_msg.message_id)
            except: pass

    # লুপ শেষ হলে (ফিনিশ বা স্টপ)
    session['is_processing'] = False
    remaining_count = len(session['remaining'])

    markup = InlineKeyboardMarkup()
    if session['stop_requested']:
        if remaining_count > 0:
            markup.row(InlineKeyboardButton("▶️ Resume Auto", callback_data="start_auto"))
        markup.row(InlineKeyboardButton("📥 Download Backup Files", callback_data="download_files_pause"))
        markup.row(InlineKeyboardButton("⏹ Finish & Clear", callback_data="download_files_finish"))
        bot.send_message(chat_id, f"⏸ *কাজ থামানো হয়েছে!*\n🟢 Good: {len(session['good'])} | 🔴 Bad: {len(session['bad'])} | 🟡 Susp: {len(session['suspended'])}\n📦 বাকি আছে: {remaining_count} টি", reply_markup=markup, parse_mode='Markdown')
    else:
        markup.add(InlineKeyboardButton("📥 Download Final Files", callback_data="download_files_finish"))
        bot.send_message(chat_id, f"✅ *সবগুলোর কাজ শেষ!*\n🟢 Good: {len(session['good'])} | 🔴 Bad: {len(session['bad'])} | 🟡 Susp: {len(session['suspended'])}", reply_markup=markup, parse_mode='Markdown')


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    data = call.data
    
    if chat_id not in user_sessions:
        try: bot.answer_callback_query(call.id, "❌ কোনো রানিং সেশন নেই।", show_alert=True)
        except: pass
        return

    session = user_sessions[chat_id]

    if data == "start_auto":
        if session['is_processing']: return
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        threading.Thread(target=auto_processor, args=(chat_id,)).start()
        try: bot.answer_callback_query(call.id)
        except: pass
        return

    if data == "stop_batch":
        if session['is_processing']:
            session['stop_requested'] = True
            try: bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="🛑 *Stopping...*\n(দয়া করে অপেক্ষা করুন, রানিং কাজ সেভ হচ্ছে...)", parse_mode='Markdown')
            except: pass
        try: bot.answer_callback_query(call.id)
        except: pass
        return

    # ম্যাজিক: লাইভ ডাউনলোড (কাজ না থামিয়েই ফাইল নামানো)
    if data == "live_download":
        try: bot.answer_callback_query(call.id, "📦 Preparing Live Backup... Please wait.", show_alert=True)
        except: pass
        send_final_files(chat_id, is_final=False, is_live=True)
        return

    if data == "download_files_pause":
        if session['is_processing']: return
        send_final_files(chat_id, is_final=False)
        try: bot.answer_callback_query(call.id)
        except: pass
        return

    if data == "download_files_finish":
        if session['is_processing']: return
        send_final_files(chat_id, is_final=True)
        try: bot.answer_callback_query(call.id)
        except: pass
        return

def send_final_files(chat_id, is_final=True, is_live=False):
    session = user_sessions.get(chat_id)
    if not session: return

    msg = bot.send_message(chat_id, "📦 *ফাইল তৈরি করা হচ্ছে...*", parse_mode='Markdown')

    def create_and_send(data_list, filename_prefix, caption_text, is_good_file=False):
        if not data_list: return 
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            for res in data_list:
                if is_good_file:
                    ws.append([f"{res[0]}|{res[1]}|{res[2]}"]) 
                else:
                    ws.append([res[0], res[1], res[2]]) 
            filename = f"{filename_prefix}_{chat_id}.xlsx"
            wb.save(filename)
            with open(filename, "rb") as f:
                bot.send_document(chat_id, f, caption=caption_text)
            os.remove(filename)
        except: pass

    create_and_send(session['good'], "Good_Accounts", f"✅ Good Accounts ({len(session['good'])})", is_good_file=True)
    create_and_send(session['bad'], "Bad_Accounts", f"❌ Failed Accounts ({len(session['bad'])})")
    create_and_send(session.get('suspended', []), "Suspended_Accounts", f"⚠️ Suspended/Checkpoint ({len(session.get('suspended', []))})")
    
    # লাইভ ডাউনলোডে রিমেইনিং ফাইল দেওয়ার দরকার নেই, কারণ সেটা অটো চেঞ্জ হচ্ছে
    if not is_live:
        create_and_send(session['remaining'], "Remaining_Accounts", f"📦 Remaining ({len(session['remaining'])})")

    try: bot.delete_message(chat_id, msg.message_id)
    except: pass

    if is_final:
        bot.send_message(chat_id, "🎉 *ফাইল ডেলিভারি করা হয়েছে!*\n(সেশন ক্লিয়ার করা হলো)", parse_mode='Markdown')
        del user_sessions[chat_id] 
    elif is_live:
        bot.send_message(chat_id, "📥 *লাইভ ব্যাকআপ দেওয়া হয়েছে!*\n(অটোমেটিক কাজ ব্যাকগ্রাউন্ডে চলছে...)", parse_mode='Markdown')
    else:
        bot.send_message(chat_id, "⏸ *ব্যাকআপ দেওয়া হয়েছে!*\n(Resume দিয়ে কন্টিনিউ করতে পারবেন)", parse_mode='Markdown')

def start_bot_polling():
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception:
            time.sleep(3)

polling_thread = threading.Thread(target=start_bot_polling)
polling_thread.daemon = True
polling_thread.start()

while True:
    try:
        user_input = input().strip().lower()
        if user_input in ['/stop', 'stop']:
            print("\n\033[1;31m🛑 Shutting down bot... Please wait.\033[0m")
            bot.stop_polling()
            print("\033[1;32m✅ Bot Stopped Successfully!\033[0m")
            sys.exit(0)
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)
