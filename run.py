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
\033[1;33m[+] Version   : \033[1;37m4.0 (Interactive VPN & Live Check)
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
        "✅ *সুপার ফাস্ট স্পিড:* একসাথে ৫০টি আইডির কাজ চোখের পলকে!\n"
        "✅ *স্মার্ট ট্র্যাকিং:* আনচেকড (Remaining) আইডিগুলো আলাদা ফাইলে পাবেন।\n\n"
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
                text="🛑 *Stopping...*\n(দয়া করে কয়েক সেকেন্ড অপেক্ষা করুন, কাজ থামানো হচ্ছে...)",
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
        
        # ৫০টি আইডি নেওয়া
        batch = session['remaining'][:50]

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🛑 Stop Processing", callback_data="stop_batch"))

        process_msg = bot.send_message(
            chat_id, 
            f"🔄 *Processing {len(batch)} Accounts...*\n(মাঝপথে থামাতে চাইলে 'Stop' বাটনে চাপ দিন)", 
            reply_markup=markup, parse_mode='Markdown'
        )

        def worker(acc):
            if session['stop_requested']:
                return
                
            username, password, two_fa = acc
            try:
                # 2FA জেনারেট
                totp = pyotp.TOTP(two_fa.replace(" ", ""))
                two_fa_code = totp.now()

                L = instaloader.Instaloader()
                
                try:
                    L.login(username, password)
                except instaloader.exceptions.TwoFactorAuthRequiredException:
                    L.two_factor_login(two_fa_code)
                except Exception as e:
                    # পাসওয়ার্ড ভুল বা নেটওয়ার্ক এরর
                    session['bad'].append((username, password, two_fa))
                    if acc in session['remaining']: session['remaining'].remove(acc)
                    return

                # --- LIVE CHECKER (অ্যাকাউন্ট সাসপেন্ড কি না চেক করা) ---
                try:
                    profile = instaloader.Profile.from_username(L.context, username)
                    _ = profile.followers # প্রোফাইল লোড হলে এটি লাইভ
                except Exception:
                    # প্রোফাইল লোড না হলে সেটি সাসপেন্ড বা চেকপয়েন্ট
                    session['suspended'].append((username, password, two_fa))
                    if acc in session['remaining']: session['remaining'].remove(acc)
                    return

                # --- PERFECT COOKIE FORMATTING ---
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
                if acc in session['remaining']: session['remaining'].remove(acc)

            except Exception as e:
                session['bad'].append((username, password, two_fa))
                if acc in session['remaining']: session['remaining'].remove(acc)

        with ThreadPoolExecutor(max_workers=50) as executor:
            executor.map(worker, batch)

        session['is_processing'] = False
        remaining_count = len(session['remaining'])

        try:
            bot.delete_message(chat_id, process_msg.message_id)
        except: pass

        markup = InlineKeyboardMarkup()
        
        if session['stop_requested']:
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

    good_data = session['good']
    bad_data = session['bad']
    susp_data = session.get('suspended', [])
    rem_data = session['remaining']

    # Good File (1 Column: user|pass|cookies)
    if good_data:
        wb_good = openpyxl.Workbook()
        ws_good = wb_good.active
        for res in good_data:
            combo_string = f"{res[0]}|{res[1]}|{res[2]}"
            ws_good.append([combo_string])
        good_filename = f"Good_Accounts_{chat_id}.xlsx"
        wb_good.save(good_filename)
        with open(good_filename, "rb") as gf:
            bot.send_document(chat_id, gf, caption=f"✅ Good Accounts ({len(good_data)})\n(Format: user|pass|cookies)")
        os.remove(good_filename)
        
    # Bad File (1 Column: user|pass|2fa)
    if bad_data:
        wb_bad = openpyxl.Workbook()
        ws_bad = wb_bad.active
        for res in bad_data:
            combo_string = f"{res[0]}|{res[1]}|{res[2]}"
            ws_bad.append([combo_string])
        bad_filename = f"Bad_Accounts_{chat_id}.xlsx"
        wb_bad.save(bad_filename)
        with open(bad_filename, "rb") as bf:
            bot.send_document(chat_id, bf, caption=f"❌ Failed Accounts ({len(bad_data)})\n(Format: user|pass|2fa)")
        os.remove(bad_filename)
        
    # Suspended File (1 Column: user|pass|2fa)
    if susp_data:
        wb_susp = openpyxl.Workbook()
        ws_susp = wb_susp.active
        for res in susp_data:
            combo_string = f"{res[0]}|{res[1]}|{res[2]}"
            ws_susp.append([combo_string])
        susp_filename = f"Suspended_Accounts_{chat_id}.xlsx"
        wb_susp.save(susp_filename)
        with open(susp_filename, "rb") as sf:
            bot.send_document(chat_id, sf, caption=f"⚠️ Suspended/Checkpoint ({len(susp_data)})\n(Format: user|pass|2fa)")
        os.remove(susp_filename)
        
    # Remaining File (1 Column: user|pass|2fa)
    if rem_data:
        wb_rem = openpyxl.Workbook()
        ws_rem = wb_rem.active
        for res in rem_data:
            combo_string = f"{res[0]}|{res[1]}|{res[2]}"
            ws_rem.append([combo_string])
        rem_filename = f"Remaining_Accounts_{chat_id}.xlsx"
        wb_rem.save(rem_filename)
        with open(rem_filename, "rb") as rf:
            bot.send_document(chat_id, rf, caption=f"📦 Remaining (Unchecked) Accounts ({len(rem_data)})\n(Format: user|pass|2fa)")
        os.remove(rem_filename)

    bot.send_message(chat_id, "🎉 *আপনার সবগুলো ফাইল সফলভাবে ডেলিভারি করা হয়েছে!*", parse_mode='Markdown')
    del user_sessions[chat_id] # সেশন ডিলিট

if __name__ == "__main__":
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            time.sleep(5)
