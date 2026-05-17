import telebot
import pyotp
import instaloader
import threading
import time

# আপনার দেওয়া বটের টোকেন
TOKEN = '8930208020:AAEeXaX_ETPruf_EcTAqSKimFZJxkxhYSfw'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    welcome_text = (
        "🔥 *Welcome to MASS IG Cookie Extractor* 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "দয়া করে আপনার অ্যাকাউন্টগুলো নিচের নিয়মে দিন:\n\n"
        "`username|password|2fa_secret`\n"
        "`username2|password|2fa_secret`\n\n"
        "আপনি একসাথে অনেকগুলো অ্যাকাউন্ট কপি-পেস্ট করে দিতে পারবেন!"
    )
    bot.send_message(chat_id, welcome_text, parse_mode='Markdown')
    # পরবর্তী মেসেজটি process_accounts ফাংশনে পাঠাবে
    bot.register_next_step_handler(message, process_accounts)

def process_accounts(message):
    chat_id = message.chat.id
    # ইউজারের মেসেজটি লাইন অনুযায়ী ভাগ করে নেওয়া হচ্ছে
    lines = message.text.strip().split('\n')
    
    bot.send_message(chat_id, f"⏳ *Processing {len(lines)} accounts...* মাল্টি-থ্রেডিং চালু করা হয়েছে। দয়া করে অপেক্ষা করুন...", parse_mode='Markdown')
    
    # প্রতিটি লাইনের জন্য লুপ চালানো
    for line in lines:
        parts = line.split('|')
        # চেক করা হচ্ছে ফরম্যাট ঠিক আছে কি না (৩টি অংশ থাকতে হবে)
        if len(parts) == 3:
            username = parts[0].strip()
            password = parts[1].strip()
            two_fa_key = parts[2].strip()
            
            # প্রতিটি অ্যাকাউন্টের জন্য একটি করে আলাদা 'Thread' (ওয়ার্কার) চালু করা হচ্ছে
            # ফলে ১০০টি আইডি দিলেও সবগুলোর কাজ একই সেকেন্ডে শুরু হবে!
            threading.Thread(target=extract_cookies, args=(chat_id, username, password, two_fa_key)).start()
        else:
            bot.send_message(chat_id, f"❌ ভুল ফরম্যাট: `{line}`\nসঠিক নিয়ম: `user|pass|2fa`", parse_mode='Markdown')

def extract_cookies(chat_id, username, password, two_fa_key):
    try:
        # ১. 2FA কোড জেনারেট করা (pyotp ব্যবহার করে)
        totp = pyotp.TOTP(two_fa_key.replace(" ", "")) # স্পেস থাকলে রিমুভ করে দেওয়া হলো
        two_fa_code = totp.now()

        # ২. Instaloader ইনিশিয়ালাইজ করা (প্রতিটি থ্রেডের জন্য আলাদা)
        L = instaloader.Instaloader()

        # ৩. লগইন করার চেষ্টা
        try:
            L.login(username, password)
        except instaloader.exceptions.TwoFactorAuthRequiredException:
            # যদি 2FA চায়, তবে আমাদের জেনারেট করা ৬-ডিজিটের কোড দিয়ে লগইন করবে
            L.two_factor_login(two_fa_code)

        # ৪. কুকিজ (Session Data) বের করে আনা
        session_cookies = L.context._session.cookies
        cookie_dict = session_cookies.get_dict()

        # কুকি ফরম্যাট করা
        sessionid = cookie_dict.get('sessionid', 'N/A')
        csrftoken = cookie_dict.get('csrftoken', 'N/A')
        ds_user_id = cookie_dict.get('ds_user_id', 'N/A')
        ig_did = cookie_dict.get('ig_did', 'N/A')
        mid = cookie_dict.get('mid', 'N/A')

        raw_cookie_string = f"sessionid={sessionid}; csrftoken={csrftoken}; ds_user_id={ds_user_id}; ig_did={ig_did}; mid={mid};"

        # ৫. ইউজারকে আউটপুট দেওয়া
        output_message = (
            f"✅ **Extraction Successful!**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"`{username}|{password}|{raw_cookie_string}`"
        )
        bot.send_message(chat_id, output_message, parse_mode='Markdown')

    except Exception as e:
        error_msg = (
            f"❌ **Failed:** `{username}`\n"
            f"Reason: `{str(e)}`"
        )
        bot.send_message(chat_id, error_msg, parse_mode='Markdown')

# বটকে লাইভ রাখার লুপ
if __name__ == "__main__":
    print("[+] MASS Extractor Bot is running...")
    print("[+] Send multiple accounts in 'user|pass|2fa' format.")
    # নেটওয়ার্ক ড্রপ হলে যেন ক্র্যাশ না করে, তাই ইনফিনিট লুপ
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"[-] Connection Error: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)
