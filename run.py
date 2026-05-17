import telebot
import pyotp
import instaloader
import os
import time
from concurrent.futures import ThreadPoolExecutor

# আপনার দেওয়া বটের টোকেন
TOKEN = '8930208020:AAEeXaX_ETPruf_EcTAqSKimFZJxkxhYSfw'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    welcome_text = (
        "🔥 *Welcome to MASS IG Cookie Extractor PRO* 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ *নতুন ফিচার:* এখন আপনি সরাসরি ফাইল আপলোড করতে পারবেন!\n\n"
        "👉 *কীভাবে দেবেন?*\n"
        "১. মেসেজে টাইপ করে দিতে পারেন: `user|pass|2fa`\n"
        "২. অথবা Google Sheet থেকে `.csv` বা `.txt` ফাইল আপলোড করুন (যেখানে কলামগুলো user, pass, 2fa হিসেবে থাকবে)।\n\n"
        "ফাইল দিলে বট গুড এবং ব্যাড অ্যাকাউন্ট আলাদা ফাইলে রিটার্ন করবে!"
    )
    bot.send_message(chat_id, welcome_text, parse_mode='Markdown')

@bot.message_handler(content_types=['document'])
def handle_document(message):
    chat_id = message.chat.id
    try:
        bot.send_message(chat_id, "📥 ফাইল রিসিভ করা হয়েছে! প্রসেসিং শুরু হচ্ছে...")
        
        # টেলিগ্রাম থেকে ফাইল ডাউনলোড করা
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # সাময়িকভাবে ফাইলটি সেভ করা
        input_filename = f"input_{chat_id}.txt"
        with open(input_filename, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        # ফাইল রিড করা (Encoding Error ফিক্স করা হয়েছে)
        try:
            with open(input_filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            # যদি utf-8 সাপোর্ট না করে, তাহলে latin-1 বা Windows encoding দিয়ে রিড করবে
            with open(input_filename, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        
        os.remove(input_filename) # কাজ শেষে ডিলিট করে দেওয়া
        
        # আসল চেকিং ফাংশনে পাঠানো
        process_accounts_list(chat_id, lines)
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ ফাইলটি রিড করতে সমস্যা হয়েছে: {e}")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text.startswith('/'): 
        return
    lines = message.text.strip().split('\n')
    process_accounts_list(message.chat.id, lines)

def process_accounts_list(chat_id, lines):
    valid_accounts = []
    
    # লাইনগুলো থেকে ডেটা আলাদা করা (CSV হলে কমা দিয়ে, সাধারণ টেক্সট হলে | দিয়ে)
    for line in lines:
        line = line.strip()
        if not line: continue
        
        if '|' in line:
            parts = line.split('|')
        elif ',' in line:
            parts = line.split(',')
        else:
            continue
            
        if len(parts) >= 3:
            valid_accounts.append((parts[0].strip(), parts[1].strip(), parts[2].strip()))
    
    if not valid_accounts:
        bot.send_message(chat_id, "❌ কোনো সঠিক অ্যাকাউন্ট পাওয়া যায়নি! ফাইলটি ঠিক আছে কি না চেক করুন।")
        return

    bot.send_message(chat_id, f"⏳ *Processing {len(valid_accounts)} accounts...*\nমাল্টি-থ্রেডিং চালু করা হয়েছে। কাজ শেষে ফাইল দেওয়া হবে, অপেক্ষা করুন...", parse_mode='Markdown')

    # ডেটা সেভ করার লিস্ট
    good_results = []
    bad_results = []

    def worker(account):
        username, password, two_fa = account
        try:
            totp = pyotp.TOTP(two_fa.replace(" ", ""))
            two_fa_code = totp.now()

            L = instaloader.Instaloader()
            
            try:
                L.login(username, password)
            except instaloader.exceptions.TwoFactorAuthRequiredException:
                L.two_factor_login(two_fa_code)

            # সব কুকি একসাথে জোড়া লাগানো
            cookie_items = [f"{cookie.name}={cookie.value}" for cookie in L.context._session.cookies]
            raw_cookie_string = "; ".join(cookie_items)

            # Good Result Format
            good_results.append(f"{username}|{password}|{raw_cookie_string}")
        except Exception as e:
            # Bad Result Format
            bad_results.append(f"{username}|{password}|Failed")

    # মাল্টি-থ্রেডিং (একসাথে সর্বোচ্চ ৫০টি কাজ করবে)
    with ThreadPoolExecutor(max_workers=50) as executor:
        executor.map(worker, valid_accounts)

    bot.send_message(chat_id, f"✅ চেকিং কমপ্লিট!\n🟢 Good: {len(good_results)}\n🔴 Bad: {len(bad_results)}\n\nফাইল আপলোড করা হচ্ছে...")

    # Good ফাইল বানানো এবং পাঠানো
    if good_results:
        good_filename = f"Good_Accounts_{chat_id}.txt"
        with open(good_filename, "w", encoding="utf-8") as gf:
            gf.write("\n".join(good_results))
        
        with open(good_filename, "rb") as gf:
            bot.send_document(chat_id, gf, caption=f"✅ Here are your Good Accounts ({len(good_results)})")
        os.remove(good_filename) # পাঠানো শেষ হলে ডিলিট
        
    # Bad ফাইল বানানো এবং পাঠানো
    if bad_results:
        bad_filename = f"Bad_Accounts_{chat_id}.txt"
        with open(bad_filename, "w", encoding="utf-8") as bf:
            bf.write("\n".join(bad_results))
        
        with open(bad_filename, "rb") as bf:
            bot.send_document(chat_id, bf, caption=f"❌ Failed Accounts ({len(bad_results)})")
        os.remove(bad_filename)

if __name__ == "__main__":
    print("[+] File Processing Bot is LIVE!")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"[-] Connection Error: {e}. Reconnecting...")
            time.sleep(5)
