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
\033[1;33m[+] Version   : \033[1;37m12.0 (Mobile Data & Smart Batch)
\033[1;33m[+] Features  : \033[1;37m100 IDs -> Airplane Mode -> Resume
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
        "🔥 *MASS IG Extractor PRO (Mobile Data)* 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ *সেফ সিস্টেম:* আপনার মোবাইলের রিয়েল আইপি দিয়ে কাজ করবে, কোনো আইডি নষ্ট হবে না!\n"
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
        markup.add(InlineKeyboardButton("▶️ Start 100 Accounts", callback_data="start_batch"))
        
        bot.send_message(
            chat_id, 
            f"✅ *ফাইল রিসিভ হয়েছে!*\n📦 *অ্যাকাউন্ট:* {len(valid_accounts)}\n\n"
            f"👇 কাজ শুরু করতে নিচের বাটনে ক্লিক করুন:", 
            reply_markup=markup, parse_mode='Markdown'
        )
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ ফাইল রিড করতে সমস্যা হয়েছে: {e}")

def batch_processor(chat_id):
    session = user_sessions[chat_id]
    session['is_processing'] = True
    session['stop_requested'] = False
    
    # ঠিক ১০০টা অ্যাকাউন্ট কেটে নেওয়া
    batch = session['remaining'][:100]
    session['remaining'] = session['remaining'][100:]
    unprocessed = []

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🛑 Stop Processing", callback_data="stop_batch"),
        InlineKeyboardButton("📥 Live Download", callback_data="live_download")
    )

    process_msg = bot.send_message(
        chat_id, 
        f"🔄 *Processing {len(batch)} Accounts...*\n(Using Safe Mobile Data)\n\n"
        f"🟢 Good: {len(session['good'])} | 🔴 Bad: {len(session['bad'])} | 🟡 Susp: {len(session['suspended'])}\n\n"
        f"মাঝপথে থামাতে বা ফাইল নামাতে চাইলে নিচের বাটন চাপুন।", 
        reply_markup=markup, parse_mode='Markdown'
    )

    def worker(acc):
        if session['stop_requested']:
            unprocessed.append(acc)
            return
            
        username, password, two_fa = acc
        time.sleep(random.uniform(1.0, 2.5)) # অ্যান্টি-স্প্যাম গ্যাপ (খুব জরুরি)
        
        try:
            totp = pyotp.TOTP(two_fa.replace(" ", ""))
            two_fa_code = totp.now()

            L = instaloader.Instaloader()
            # Tor প্রক্সি বাদ দেওয়া হয়েছে। এখন ডিরেক্ট মোবাইল ডেটা ব্যবহার করবে।
            
            try:
                L.login(username, password)
            except instaloader.exceptions.TwoFactorAuthRequiredException:
                L.two_factor_login(two_fa_code)
            except Exception:
                session['bad'].append(acc)
                return

            try:
                # Live Checker: প্রোফাইল লোড করে দেখা হচ্ছে আইডি ঠিক আছে কি না
                profile = instaloader.Profile.from_username(L.context, username)
                _ = profile.followers
            except instaloader.exceptions.ProfileNotExistsException:
                # যদি প্রোফাইল না থাকে তবে Suspended
                session['suspended'].append(acc)
                return
            except Exception:
                # অন্য কোনো ছোটখাটো এরর (যেমন প্রাইভেট অ্যাকাউন্ট বা নেটওয়ার্ক ড্রপ) হলে
                # সেটাকে Suspended না ধরে Good হিসেবেই কুকি বের করার সুযোগ দেওয়া হবে
                pass

            cookie_dict = {cookie.name: cookie.value for cookie in L.context._session.cookies}
            if 'datr' not in cookie_dict: cookie_dict['datr'] = 'CVTqaVVElLHF6TC46birRObC'
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

    # স্পিড ব্যালেন্স করা হয়েছে (১৫) যাতে মোবাইল ডেটা ক্র্যাশ না করে
    with ThreadPoolExecutor(max_workers=15) as executor:
        executor.map(worker, batch)

    if unprocessed:
        session['remaining'] = unprocessed + session['remaining']

    session['is_processing'] = False
    remaining_count = len(session['remaining'])

    try: bot.delete_message(chat_id, process_msg.message_id)
    except: pass

    markup = InlineKeyboardMarkup()
    if session['stop_requested']:
        if remaining_count > 0:
            markup.row(InlineKeyboardButton("▶️ Resume Auto", callback_data="start_batch"))
        markup.row(InlineKeyboardButton("📥 Download Backup Files", callback_data="download_files_pause"))
        markup.row(InlineKeyboardButton("⏹ Finish & Clear", callback_data="download_files_finish"))
        bot.send_message(chat_id, f"⏸ *কাজ থামানো হয়েছে!*\n🟢 Good: {len(session['good'])} | 🔴 Bad: {len(session['bad'])} | 🟡 Susp: {len(session['suspended'])}\n📦 বাকি আছে: {remaining_count} টি", reply_markup=markup, parse_mode='Markdown')
    elif remaining_count > 0:
        markup.add(InlineKeyboardButton(f"▶️ Resume Next 100", callback_data="start_batch"))
        markup.add(InlineKeyboardButton("📥 Download Backup Files", callback_data="download_files_pause"))
        bot.send_message(chat_id, f"✅ *100 Accounts Done!*\n\n⚠️ *এখন আপনার ফোনের 'ফ্লাইট মোড (Airplane Mode)' ২ সেকেন্ডের জন্য অন-অফ করুন (নতুন আইপি পেতে)।*\n\nএরপর নিচের 'Resume Next 100' বাটনে চাপ দিন:", reply_markup=markup, parse_mode='Markdown')
    else:
        markup.add(InlineKeyboardButton("📥 Download Final Files", callback_data="download_files_finish"))
        bot.send_message(chat_id, f"🎉 *সবগুলোর কাজ শেষ!*\n🟢 Good: {len(session['good'])} | 🔴 Bad: {len(session['bad'])} | 🟡 Susp: {len(session['suspended'])}", reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    data = call.data
    
    if chat_id not in user_sessions:
        try: bot.answer_callback_query(call.id, "❌ কোনো রানিং সেশন নেই।", show_alert=True)
        except: pass
        return

    session = user_sessions[chat_id]

    if data == "start_batch":
        if session['is_processing']: return
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        threading.Thread(target=batch_processor, args=(chat_id,)).start()
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
    
    if not is_live:
        create_and_send(session['remaining'], "Remaining_Accounts", f"📦 Remaining ({len(session['remaining'])})")

    try: bot.delete_message(chat_id, msg.message_id)
    except: pass

    if is_final:
        bot.send_message(chat_id, "🎉 *ফাইল ডেলিভারি করা হয়েছে!*\n(সেশন ক্লিয়ার করা হলো)", parse_mode='Markdown')
        del user_sessions[chat_id] 
    elif is_live:
        bot.send_message(chat_id, "📥 *লাইভ ব্যাকআপ দেওয়া হয়েছে!*\n(কাজ ব্যাকগ্রাউন্ডে চলছে...)", parse_mode='Markdown')
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
