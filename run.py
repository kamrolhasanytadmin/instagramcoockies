import telebot
import pyotp
import instaloader
import os
import time
import openpyxl
import requests
import random
from concurrent.futures import ThreadPoolExecutor

# আপনার টেলিগ্রাম বট টোকেন দিন
TOKEN = '8930208020:AAEeXaX_ETPruf_EcTAqSKimFZJxkxhYSfw'
bot = telebot.TeleBot(TOKEN)

# ফ্রি প্রক্সি এপিআই (ProxyScrape থেকে অটোমেটিক ফ্রেশ প্রক্সি নেবে)
PROXY_API_URL = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"

def get_proxies():
    proxies = []
    try:
        response = requests.get(PROXY_API_URL, timeout=10)
        if response.status_code == 200:
            proxy_list = response.text.strip().split('\r\n')
            for proxy in proxy_list:
                if proxy:
                    proxies.append(proxy)
    except Exception as e:
        print(f"[-] Proxy fetch error: {e}")
    return proxies

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    welcome_text = (
        "🔥 *MASS IG Cookie Extractor PRO (BATCH SYSTEM)* 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ *অটোমেটিক আইপি রোটেশন চালু আছে!*\n"
        "✅ বড় ফাইল দিলে বট নিজে থেকেই ২০টা করে আইডি চেক করবে এবং আইপি বদলাবে।\n\n"
        "👉 আপনার `.xlsx` (Excel) ফাইলটি আপলোড করুন।\n"
        "• কলাম A = Username\n"
        "• কলাম B = Password\n"
        "• কলাম C = 2FA Key\n"
    )
    bot.send_message(chat_id, welcome_text, parse_mode='Markdown')

@bot.message_handler(content_types=['document'])
def handle_document(message):
    chat_id = message.chat.id
    valid_accounts = []
    
    try:
        file_name = message.document.file_name.lower()
        if not file_name.endswith('.xlsx'):
            bot.send_message(chat_id, "❌ দয়া করে শুধুমাত্র .xlsx (Excel) ফাইল আপলোড করুন!")
            return

        bot.send_message(chat_id, "📥 এক্সেল ফাইল রিসিভ করা হয়েছে! রিডিং শুরু হচ্ছে...")
        
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_filename = f"input_{chat_id}.xlsx"
        with open(input_filename, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        wb = openpyxl.load_workbook(input_filename)
        sheet = wb.active
        
        for row in sheet.iter_rows(values_only=True):
            if len(row) >= 3 and row[0] and row[1] and row[2]:
                user = str(row[0]).strip()
                pwd = str(row[1]).strip()
                twofa = str(row[2]).strip()
                
                # হেডার বাদ দেওয়ার জন্য
                if user.lower() in ['username', 'user', 'id']:
                    continue
                    
                valid_accounts.append((user, pwd, twofa))

        os.remove(input_filename)
        process_accounts_list(chat_id, valid_accounts)
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ ফাইলটি রিড করতে সমস্যা হয়েছে। Error: {e}")

def process_accounts_list(chat_id, valid_accounts):
    if not valid_accounts:
        bot.send_message(chat_id, "❌ কোনো সঠিক অ্যাকাউন্ট পাওয়া যায়নি!")
        return

    # প্রক্সি ডাউনলোড করা হচ্ছে
    bot.send_message(chat_id, f"⏳ *Fetching fresh proxies...*")
    proxy_list = get_proxies()
    proxy_msg = f"✅ *{len(proxy_list)}* proxies loaded!" if proxy_list else "⚠️ Proxy load failed. Using real IP."
    
    # ব্যাচ সাইজ (একসাথে কতগুলো আইডির কাজ করবে)
    BATCH_SIZE = 20
    # ফাইলটিকে ২০টি করে আইডির ছোট ছোট টুকরোতে ভাগ করা হচ্ছে
    chunks = [valid_accounts[i:i + BATCH_SIZE] for i in range(0, len(valid_accounts), BATCH_SIZE)]
    
    bot.send_message(chat_id, f"{proxy_msg}\n⏳ *Total Accounts:* {len(valid_accounts)}\n📦 *Total Batches:* {len(chunks)}\n\nকাজ শুরু হচ্ছে, অপেক্ষা করুন...", parse_mode='Markdown')

    good_results = []
    bad_results = []

    for index, chunk in enumerate(chunks):
        batch_num = index + 1
        
        # এই ব্যাচের জন্য একটি নতুন আইপি সিলেক্ট করা
        current_proxy = random.choice(proxy_list) if proxy_list else None
        
        bot.send_message(chat_id, f"🔄 *Processing Batch {batch_num}/{len(chunks)}* (IP Changed!)", parse_mode='Markdown')
        
        # ওয়ার্কার ফাংশন যা কুকি বের করবে
        def worker(account):
            username, password, two_fa = account
            try:
                totp = pyotp.TOTP(two_fa.replace(" ", ""))
                two_fa_code = totp.now()

                L = instaloader.Instaloader()
                
                # প্রক্সি সেট করা (যদি থাকে)
                if current_proxy:
                    L.context._session.proxies = {
                        "http": f"http://{current_proxy}",
                        "https": f"http://{current_proxy}"
                    }

                try:
                    L.login(username, password)
                except instaloader.exceptions.TwoFactorAuthRequiredException:
                    L.two_factor_login(two_fa_code)

                cookie_items = [f"{cookie.name}={cookie.value}" for cookie in L.context._session.cookies]
                raw_cookie_string = "; ".join(cookie_items)

                good_results.append([username, password, raw_cookie_string])
            except Exception as e:
                bad_results.append([username, password, two_fa])

        # মাল্টি-থ্রেডিং দিয়ে এই ব্যাচের কাজ দ্রুত শেষ করা
        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(worker, chunk)
            
        # একটি ব্যাচ শেষ হওয়ার পর আইপি বদলানোর জন্য ৫ সেকেন্ডের বিরতি
        if batch_num < len(chunks):
            time.sleep(5)

    bot.send_message(chat_id, f"✅ চেকিং কমপ্লিট!\n🟢 Good: {len(good_results)}\n🔴 Bad: {len(bad_results)}\n\nএক্সেল ফাইল আপলোড করা হচ্ছে...")

    if good_results:
        wb_good = openpyxl.Workbook()
        ws_good = wb_good.active
        ws_good.append(["Username", "Password", "Cookies"])
        for res in good_results:
            ws_good.append(res)
            
        good_filename = f"Good_Accounts_{chat_id}.xlsx"
        wb_good.save(good_filename)
        
        with open(good_filename, "rb") as gf:
            bot.send_document(chat_id, gf, caption=f"✅ Here are your Good Accounts ({len(good_results)})")
        os.remove(good_filename)
        
    if bad_results:
        wb_bad = openpyxl.Workbook()
        ws_bad = wb_bad.active
        ws_bad.append(["Username", "Password", "2FA Key"])
        for res in bad_results:
            ws_bad.append(res)
            
        bad_filename = f"Bad_Accounts_{chat_id}.xlsx"
        wb_bad.save(bad_filename)
        
        with open(bad_filename, "rb") as bf:
            bot.send_document(chat_id, bf, caption=f"❌ Failed Accounts ({len(bad_results)})")
        os.remove(bad_filename)

if __name__ == "__main__":
    print("[+] File Processing Bot is LIVE with BATCH SYSTEM!")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"[-] Connection Error: {e}. Reconnecting...")
            time.sleep(5)
