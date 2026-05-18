import telebot
import pyotp
import instaloader
import os
import time
import openpyxl
import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from concurrent.futures import ThreadPoolExecutor

# আপনার টেলিগ্রাম বট টোকেন
TOKEN = '8930208020:AAEeXaX_ETPruf_EcTAqSKimFZJxkxhYSfw'
bot = telebot.TeleBot(TOKEN)

# ইউজারদের ডেটা এবং সেশন সেভ রাখার ডিকশনারি
user_sessions = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    welcome_text = (
        "🔥 *MASS IG Extractor PRO (Interactive & Safe)* 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ *সেফ মোড অন:* নিজে ভিপিএন বদলে সেফলি কাজ করুন!\n"
        "✅ *লাইভ কন্ট্রোল:* কাজ চলাকালীন যেকোনো সময় Stop করতে পারবেন।\n"
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
    
    # আগের কাজ চলমান থাকলে নতুন ফাইল নেওয়া বন্ধ
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
            
        wb = openpyxl.load_workbook(input_filename)
        sheet = wb.active
        
        valid_accounts = []
        for row in sheet.iter_rows(values_only=True):
            if len(row) >= 3 and row[0] and row[1] and row[2]:
                user = str(row[0]).strip()
                pwd = str(row[1]).strip()
                twofa = str(row[2]).strip()
                
                if user.lower() in ['username', 'user', 'id']:
                    continue
                    
                valid_accounts.append((user, pwd, twofa))

        os.remove(input_filename)

        if not valid_accounts:
            bot.send_message(chat_id, "❌ ফাইলে কোনো সঠিক ডেটা পাওয়া যায়নি!")
            return

        # প্রো-লেভেলের সেশন ট্র্যাকিং
        user_sessions[chat_id] = {
            'remaining': valid_accounts.copy(), # যেগুলো বাকি আছে
            'good': [],
            'bad': [],
            'suspended': [],            'is_processing': False,
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

    # Stop Button Logic
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

    # Download Button Logic
    if data == "download_files":
        if session['is_processing']:
            bot.send_message(chat_id, "⚠️ কাজ রানিং অবস্থায় ফাইল ডাউনলোড করা যাবে না। আগে Stop করুন।")
            return
        send_final_files(chat_id)
        return

    # Process Next Logic
    if data == "process_next":
        if session['is_processing']:
            return
            
        session['is_processing'] = True
        session['stop_requested'] = False # রিসেট
        
        # বাকি থাকা লিস্ট থেকে প্রথম ৫০টি নেওয়া
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
                totp = pyotp.TOTP(two_fa.replace(" ", ""))
                two_fa_code = totp.now()

                L = instaloader.Instaloader()
                
                # --- ১. লগইন চেক (Bad Account Filtering) ---
                try:
                    L.login(username, password)
                except instaloader.exceptions.TwoFactorAuthRequiredException:
                    L.two_factor_login(two_fa_code)
                except Exception as e:
                    # পাসওয়ার্ড ভুল বা আইপি ব্লক হলে এখানে আসবে
                    session['bad'].append((username, password, two_fa))
                    if acc in session['remaining']: session['remaining'].remove(acc)
                    return

                # --- ২. লাইভ/সাসপেন্ড চেক (Suspended Account Filtering) ---
                try:
                    profile = instaloader.Profile.from_username(L.context, username)
                    _ = profile.followers
                except Exception:
                    # লগইন হয়েছে কিন্তু প্রোফাইল লোড হয়নি মানে সাসপেন্ড/চেকপয়েন্ট
                    session['suspended'].append((username, password, two_fa))
                    if acc in session['remaining']: session['remaining'].remove(acc)
                    return

                # --- ৩. সাকসেসফুল অ্যাকাউন্ট (Good Account) ---
                cookie_items = [f"{cookie.name}={cookie.value}" for cookie in L.context._session.cookies]
                raw_cookie_string = "; ".join(cookie_items)
                session['good'].append((username, password, raw_cookie_string))
                if acc in session['remaining']: session['remaining'].remove(acc)

            except Exception as e:
                # অন্য কোনো অপ্রত্যাশিত এরর
                session['bad'].append((username, password, two_fa))
                if acc in session['remaining']: session['remaining'].remove(acc)

        with ThreadPoolExecutor(max_workers=15) as executor:
            executor.map(worker, batch)

        session['is_processing'] = False
        remaining_count = len(session['remaining'])

        # UI Update
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
                f"👇 আপনি চাইলে ফাইলগুলো এখনই ডাউনলোড করতে পারেন, অথবা আইপি চেঞ্জ করে আবার Resume করতে পারেন:",
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
                f"নতুন আইপি পেলে নিচের 'Start Next 50' বাটনে ক্লিক করুন:",
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

    # ১. Good File
    if good_data:
        wb_good = openpyxl.Workbook()
        ws_good = wb_good.active
        ws_good.append(["Username", "Password", "Cookies"])
        for res in good_data:
            ws_good.append(res)
        good_filename = f"Good_Accounts_{chat_id}.xlsx"
        wb_good.save(good_filename)
        with open(good_filename, "rb") as gf:
            bot.send_document(chat_id, gf, caption=f"✅ Good Accounts ({len(good_data)})")
        os.remove(good_filename)
        
    # ২. Bad File
    if bad_data:
        wb_bad = openpyxl.Workbook()
        ws_bad = wb_bad.active
        ws_bad.append(["Username", "Password", "2FA Key"])
        for res in bad_data:
            ws_bad.append(res)
        bad_filename = f"Bad_Accounts_{chat_id}.xlsx"
        wb_bad.save(bad_filename)
        with open(bad_filename, "rb") as bf:
            bot.send_document(chat_id, bf, caption=f"❌ Failed Accounts ({len(bad_data)})")
        os.remove(bad_filename)
        
    # ৩. Suspended File
    if susp_data:
        wb_susp = openpyxl.Workbook()
        ws_susp = wb_susp.active
        ws_susp.append(["Username", "Password", "2FA Key"])
        for res in susp_data:
            ws_susp.append(res)
        susp_filename = f"Suspended_Accounts_{chat_id}.xlsx"
        wb_susp.save(susp_filename)
        with open(susp_filename, "rb") as sf:
            bot.send_document(chat_id, sf, caption=f"⚠️ Suspended/Checkpoint ({len(susp_data)})")
        os.remove(susp_filename)

    bot.send_message(chat_id, "🎉 *আপনার সবগুলো ফাইল সফলভাবে ডেলিভারি করা হয়েছে!*", parse_mode='Markdown')
    
    # কাজ শেষে সেশন মুছে ফেলা
    del user_sessions[chat_id]

if __name__ == "__main__":
    print("[+] Advanced Interactive Bot is LIVE!")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"[-] Error: {e}. Reconnecting...")
            time.sleep(5)
