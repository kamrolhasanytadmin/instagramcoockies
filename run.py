import telebot
import pyotp
import instaloader
import os
import time
import openpyxl
import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from concurrent.futures import ThreadPoolExecutor

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner():
    clear_screen()
    banner = """
\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
\033[1;32m      🔥 MASS IG COOKIE EXTRACTOR PRO 🔥
\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
\033[1;33m[+] Developer : \033[1;37mKamrol
\033[1;33m[+] Version   : \033[1;37m5.0 (Fail-Safe Batch & Perfect Files)
\033[1;33m[+] Speed     : \033[1;37mMAX (50 IDs / Batch)
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
    print("\033[1;36m[*] Bot is running... Go to Telegram and send /start\033[0m")
except Exception as e:
    print("\n\033[1;31m❌ Invalid Token! Please check your token and run the script again.\033[0m")
    exit()

# ইউজারের ডেটা এবং সেশন সেভ রাখার ডিকশনারি
user_sessions = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    welcome_text = (
        "🔥 *MASS IG Extractor PRO (Interactive & Safe)* 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ *সেফ মোড অন:* নিজে ভিপিএন বদলে সেফলি কাজ করুন!\n"
        "✅ *স্মার্ট ট্র্যাকিং:* Good, Bad, Suspended এবং Remaining ফাইল আলাদা পাবেন!\n\n"
        "👉 আপনার `.xlsx` (Excel) ফাইলটি আপলোড করুন।\n"
        "• কলাম A = Username\n"
        "• কলাম B = Password\n"
        "• কলাম C = 2FA Key\n"
    )
    bot.send_message(chat_id, welcome_text, parse_mode='Markdown')

@bot.message_handler(content_types=['document'])
def handle_document(message):
    chat_id = message.chat.id
    
    if chat_id in user_sessions and user_sessions[chat_id].get('is_processing'):
        bot.send_message(chat_id, "⚠️ আপনার একটি কাজ রানিং আছে! নতুন ফাইল দেওয়ার আগে সেটি Stop করুন।")
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
            
        # Excel ফাইল রিড করা
        wb = openpyxl.load_workbook(input_filename)
        sheet = wb.active
        
        valid_accounts = []
        for row in sheet.iter_rows(values_only=True):
            if len(row) >= 3 and row[0] and row[1] and row[2]:
                user = str(row[0]).strip()
                pwd = str(row[1]).strip()
                twofa = str(row[2]).strip()
                
                # হেডার স্কিপ করা
                if user.lower() in ['username', 'user', 'id']:
                    continue
                    
                valid_accounts.append((user, pwd, twofa))

        os.remove(input_filename)

        if not valid_accounts:
            bot.send_message(chat_id, "❌ ফাইলে কোনো সঠিক ডেটা পাওয়া যায়নি!")
            return

        # ইউজারের জন্য নতুন সেশন তৈরি করা
        user_sessions[chat_id] = {
            'remaining': valid_accounts.copy(),
            'good': [],
            'bad': [],
            'suspended': [],            
            'is_processing': False,
            'stop_requested': False
        }

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("▶️ Start First 50", callback_data="process_next"))
        
        bot.send_message(
            chat_id, 
            f"✅ *ফাইল সফলভাবে রিসিভ হয়েছে!*\n📦 *সর্বমোট অ্যাকাউন্ট:* {len(valid_accounts)}\n\n"
            f"👇 প্রথম ৫০টি অ্যাকাউন্টের কাজ শুরু করতে নিচের বাটনে ক্লিক করুন:", 
            reply_markup=markup, parse_mode='Markdown'
        )
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ ফাইল রিড করতে সমস্যা হয়েছে: {e}")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    data = call.data
    
    bot.answer_callback_query(call.id)

    if chat_id not in user_sessions:
        bot.send_message(chat_id, "❌ কোনো রানিং সেশন নেই। দয়া করে এক্সেল ফাইলটি আবার আপলোড করুন।")
        return

    session = user_sessions[chat_id]

    if data == "stop_batch":
        if session['is_processing']:
            session['stop_requested'] = True
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text="🛑 *Stopping...*\n(দয়া করে কয়েক সেকেন্ড অপেক্ষা করুন, রানিং কাজগুলো সেভ হচ্ছে...)",
                parse_mode='Markdown'
            )
        return

    if data == "download_files":
        if session['is_processing']:
            bot.send_message(chat_id, "⚠️ কাজ রানিং অবস্থায় ফাইল ডাউনলোড করা যাবে না। আগে Stop করুন।")
            return
        send_final_files(chat_id)
        return

    if data == "process_next":
        if session['is_processing']:
            return
            
        session['is_processing'] = True
        session['stop_requested'] = False
        
        # একদম নিখুঁত ব্যাচিং সিস্টেম (৫০টি কেটে নেওয়া হবে)
        batch = session['remaining'][:50]
        session['remaining'] = session['remaining'][50:] 
        
        unprocessed = [] # যেগুলো স্টপ করার কারণে চেক হবে না

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🛑 Stop Processing", callback_data="stop_batch"))

        process_msg = bot.send_message(
            chat_id, 
            f"🔄 *Processing {len(batch)} Accounts...*\n(মাঝপথে থামাতে চাইলে 'Stop' বাটনে চাপ দিন)", 
            reply_markup=markup, parse_mode='Markdown'
        )

        def worker(acc):
            if session['stop_requested']:
                unprocessed.append(acc)
                return
                
            username, password, two_fa = acc
            # অ্যান্টি-ব্লক ডিলে (ইন্সটাগ্রাম যাতে সন্দেহ না করে)
            time.sleep(random.uniform(0.5, 2.0))
            
            try:
                # 2FA জেনারেট
                totp = pyotp.TOTP(two_fa.replace(" ", ""))
                two_fa_code = totp.now()

                L = instaloader.Instaloader()
                
                try:
                    L.login(username, password)
                except instaloader.exceptions.TwoFactorAuthRequiredException:
                    L.two_factor_login(two_fa_code)

                # --- LIVE CHECKER ---
                try:
                    profile = instaloader.Profile.from_username(L.context, username)
                    _ = profile.followers
                except Exception:
                    session['suspended'].append((username, password, two_fa))
                    return

                # --- PERFECT COOKIES ---
                cookie_dict = {cookie.name: cookie.value for cookie in L.context._session.cookies}
                if 'datr' not in cookie_dict:
                    cookie_dict['datr'] = 'HS3naU6ORdMLlg8ma6NYa3hy'
                if 'wd' not in cookie_dict:
                    cookie_dict['wd'] = f"{random.randint(360, 501)}x{random.randint(700, 954)}"
                if 'dpr' not in cookie_dict:
                    cookie_dict['dpr'] = '2.15625'
                
                keys_order = ['datr', 'ig_did', 'mid', 'dpr', 'csrftoken', 'ds_user_id', 'sessionid', 'wd', 'rur']
                final_cookies = []
                for k in keys_order:
                    if k in cookie_dict:
                        final_cookies.append(f"{k}={cookie_dict[k]}")
                for k, v in cookie_dict.items():
                    if k not in keys_order:
                        final_cookies.append(f"{k}={v}")
                        
                raw_cookie_string = "; ".join(final_cookies)
                session['good'].append((username, password, raw_cookie_string))

            except Exception as e:
                session['bad'].append((username, password, two_fa))

        # স্পিড ৩০ रखा হয়েছে যাতে ড্রপ না হয়
        with ThreadPoolExecutor(max_workers=30) as executor:
            executor.map(worker, batch)

        # যেগুলো চেক হয়নি সেগুলো আবার রিমেইনিংয়ে ফেরত দেওয়া
        if unprocessed:
            session['remaining'] = unprocessed + session['remaining']

        session['is_processing'] = False
        remaining_count = len(session['remaining'])

        try:
            bot.delete_message(chat_id, process_msg.message_id)
        except: pass

        markup = InlineKeyboardMarkup()
        
        if session['stop_requested']:
            if remaining_count > 0:
                markup.row(InlineKeyboardButton("▶️ Resume (Start Next)", callback_data="process_next"))
            markup.row(InlineKeyboardButton("📥 Download Files", callback_data="download_files"))
            bot.send_message(
                chat_id,
                f"⏸ *কাজ ম্যানুয়ালি থামানো হয়েছে!*\n"
                f"🟢 Good: {len(session['good'])} | 🔴 Bad: {len(session['bad'])} | 🟡 Suspended: {len(session['suspended'])}\n"
                f"📦 আনচেকড বাকি আছে: {remaining_count} টি\n\n"
                f"👇 ফাইল ডাউনলোড করুন অথবা আইপি চেঞ্জ করে Resume করুন:",
                reply_markup=markup, parse_mode='Markdown'
            )
            
        elif remaining_count == 0:
            markup.add(InlineKeyboardButton("📥 Download Files", callback_data="download_files"))
            bot.send_message(
                chat_id, 
                f"✅ *সবগুলো অ্যাকাউন্টের কাজ শেষ!*\n"
                f"🟢 Good: {len(session['good'])} | 🔴 Bad: {len(session['bad'])} | 🟡 Suspended: {len(session['suspended'])}\n\n"
                f"ফাইল পেতে নিচের বাটনে ক্লিক করুন:", 
                reply_markup=markup, parse_mode='Markdown'
            )
            
        else:
            markup.row(InlineKeyboardButton("▶️ Start Next 50", callback_data="process_next"))
            markup.row(InlineKeyboardButton("📥 Download Files (Pause)", callback_data="download_files"))
            bot.send_message(
                chat_id,
                f"⏸ *Batch Finished!*\n"
                f"🟢 Good: {len(session['good'])} | 🔴 Bad: {len(session['bad'])} | 🟡 Suspended: {len(session['suspended'])}\n"
                f"📦 আনচেকড বাকি আছে: {remaining_count} টি\n\n"
                f"⚠️ *এখন আপনার ভিপিএন চেঞ্জ করুন বা Flight Mode অন-অফ করুন।*\n"
                f"নতুন আইপি পেলে নিচের বাটনে ক্লিক করুন:",
                reply_markup=markup, parse_mode='Markdown'
            )

def send_final_files(chat_id):
    session = user_sessions.get(chat_id)
    if not session: return

    bot.send_message(chat_id, "📦 *ফাইল তৈরি করা হচ্ছে, একটু অপেক্ষা করুন...*", parse_mode='Markdown')

    def create_and_send(data_list, filename_prefix, caption_text, is_good_file=False):
        if not data_list: return # ডেটা না থাকলে ফাইল বানাবে না
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            for res in data_list:
                if is_good_file:
                    combo_string = f"{res[0]}|{res[1]}|{res[2]}"
                    ws.append([combo_string]) # গুড ফাইলে এক কলামেই সব ডেটা
                else:
                    ws.append([res[0], res[1], res[2]]) # অন্যান্য ফাইলে কলাম A, B, C তে আলাদা আলাদা
            
            filename = f"{filename_prefix}_{chat_id}.xlsx"
            wb.save(filename)
            with open(filename, "rb") as f:
                bot.send_document(chat_id, f, caption=caption_text)
            os.remove(filename)
        except Exception as e:
            bot.send_message(chat_id, f"❌ {filename_prefix} ফাইল তৈরিতে এরর: {e}")

    # ৪টি ফাইল নিখুঁতভাবে ডেলিভারি দেওয়া (শুধুমাত্র গুড ফাইলে is_good_file=True পাঠানো হলো)
    create_and_send(session['good'], "Good_Accounts", f"✅ Good Accounts ({len(session['good'])})\n(Format: user|pass|cookies)", is_good_file=True)
    create_and_send(session['bad'], "Bad_Accounts", f"❌ Failed Accounts ({len(session['bad'])})\n(Format: Col A=User, Col B=Pass, Col C=2FA)")
    create_and_send(session.get('suspended', []), "Suspended_Accounts", f"⚠️ Suspended/Checkpoint ({len(session.get('suspended', []))})\n(Format: Col A=User, Col B=Pass, Col C=2FA)")
    create_and_send(session['remaining'], "Remaining_Accounts", f"📦 Remaining (Unchecked) Accounts ({len(session['remaining'])})\n(Format: Col A=User, Col B=Pass, Col C=2FA)")

    bot.send_message(chat_id, "🎉 *আপনার সবগুলো ফাইল সফলভাবে ডেলিভারি করা হয়েছে!*", parse_mode='Markdown')
    del user_sessions[chat_id] # কাজ শেষে সেশন ক্লিয়ার

if __name__ == "__main__":
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            time.sleep(5)
