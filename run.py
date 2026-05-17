import telebot
import pyotp
import instaloader
import threading
import time

# আপনার দেওয়া বটের টোকেন
TOKEN = '8930208020:AAEeXaX_ETPruf_EcTAqSKimFZJxkxhYSfw'
bot = telebot.TeleBot(TOKEN)

# ইউজারদের ডেটা সাময়িকভাবে সেভ রাখার জন্য একটি ডিকশনারি
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    welcome_text = (
        "🔥 *Welcome to IG Cookie Extractor Bot* 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "দয়া করে আপনার ইনস্টাগ্রাম Username দিন:"
    )
    bot.send_message(chat_id, welcome_text, parse_mode='Markdown')
    # পরবর্তী মেসেজটি process_username ফাংশনে পাঠাবে
    bot.register_next_step_handler(message, process_username)

def process_username(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'username': message.text}
    bot.send_message(chat_id, "✅ Username সেভ হয়েছে!\n\nএবার আপনার Password দিন:")
    bot.register_next_step_handler(message, process_password)

def process_password(message):
    chat_id = message.chat.id
    user_data[chat_id]['password'] = message.text
    bot.send_message(chat_id, "✅ Password সেভ হয়েছে!\n\nসবশেষে, আপনার 2FA Secret Key দিন:")
    bot.register_next_step_handler(message, process_2fa)

def process_2fa(message):
    chat_id = message.chat.id
    user_data[chat_id]['2fa_key'] = message.text
    
    bot.send_message(chat_id, "⏳ *Processing...* রিকোয়েস্ট পাঠানো হচ্ছে। দয়া করে ১৫-২০ সেকেন্ড অপেক্ষা করুন...", parse_mode='Markdown')
    
    # মাল্টি-থ্রেডিং চালু করা হলো, যাতে বট ফ্রিজ না হয় এবং অন্য ইউজাররাও কাজ করতে পারে
    threading.Thread(target=extract_cookies, args=(chat_id,)).start()

def extract_cookies(chat_id):
    data = user_data.get(chat_id)
    if not data:
        return

    username = data['username']
    password = data['password']
    two_fa_key = data['2fa_key']

    try:
        # ১. 2FA কোড জেনারেট করা (pyotp ব্যবহার করে)
        totp = pyotp.TOTP(two_fa_key.replace(" ", "")) # স্পেস থাকলে রিমুভ করে দেওয়া হলো
        two_fa_code = totp.now()

        # ২. Instaloader ইনিশিয়ালাইজ করা
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
            f"❌ **Extraction Failed!**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Reason: `{str(e)}`\n\n"
            f"💡 *টিপস:* আইপি ব্লক হলে Termux-এ ফ্লাইট মোড অন-অফ করে আবার চেষ্টা করুন।"
        )
        bot.send_message(chat_id, error_msg, parse_mode='Markdown')

# বটকে লাইভ রাখার লুপ
if __name__ == "__main__":
    print("[+] Bot is running with token: " + TOKEN[:15] + "...")
    print("[+] Auto-reconnect enabled. Waiting for commands...")
    # নেটওয়ার্ক ড্রপ হলে যেন ক্র্যাশ না করে, তাই ইনফিনিট লুপ
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"[-] Connection Error: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)
