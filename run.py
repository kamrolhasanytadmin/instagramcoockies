# ... existing code ...
import json

# ========== LOCAL DATA STORAGE (MongoDB-এর বিকল্প) ==========
DATA_FILE = "bot_data.json"

def load_local_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"authorized_users": [ADMIN_ID], "good_accounts": []}

def save_local_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_local_data()

# `db` অবজেক্টের বদলে এখন `data` ডিকশনারি দিয়ে কাজ হবে
def is_authorized(user_id):
    if user_id == ADMIN_ID: return True
    return user_id in data.get("authorized_users", [])

# উদাহরণস্বরূপ: Add user ফাংশন এভাবে হবে
def add_user_step(message):
    try:
        uid = int(message.text.strip())
        if uid not in data["authorized_users"]:
            data["authorized_users"].append(uid)
            save_local_data(data)
            bot.send_message(ADMIN_ID, f"✅ User `{uid}` is authorized!")
    except:
        bot.send_message(ADMIN_ID, "❌ Invalid ID!")
# ... বাকি ফাংশনগুলোতে একইভাবে যেখানে `db` ব্যবহার করেছিলেন, সেখানে `data` লিস্ট বা ডিকশনারি ব্যবহার করবেন ...
```

### কেন এই পদ্ধতিটি সেরা?
১. **কোনো ডিএনএস বা নেটওয়ার্ক ইস্যু নেই:** আপনার ফোনে বা সার্ভারে ডিএনএস ঠিক আছে কি না তা নিয়ে আর মাথা ঘামাতে হবে না।
২. **অফলাইন কাজ করবে:** ইন্টারনেট থাকলেও ডেটা লোকাল ফাইলে থাকবে, তাই কানেকশন লস হওয়ার ভয় নেই।
৩. **দ্রুত:** লোকাল ফাইলে ডেটা সেভ করা মঙ্গোডিবির চেয়ে অনেক বেশি দ্রুত।

### আপনার যদি MongoDB-ই প্রয়োজন হয়:
যদি আপনার অনেক ইউজারের ডেটা অনলাইন সিঙ্ক করার জন্য মঙ্গোডিবি একান্তই দরকার হয়, তবে:
*   আপনার ফোনে যদি **Termux** ব্যবহার করেন, তবে এই কমান্ডটি দিন: `termux-fix-shebang` এবং তারপর টার্মাক্সটি রিস্টার্ট করুন। অনেক সময় এটি পারমিশন ইস্যু ঠিক করে দেয়।
*   অথবা, `pymongo` এর জায়গায় `requests` ব্যবহার করে MongoDB Atlas API কল করতে পারেন, যা `srv` প্রোটোকল ব্যবহার করে না। তবে এটি অনেক জটিল।

**আমার পরামর্শ:** আপনার যদি কুকি এক্সট্রাক্ট করা মূল উদ্দেশ্য হয়, তবে **Local JSON ফাইল** পদ্ধতিটি ব্যবহার করুন। আপনার বর্তমান সমস্যার জন্য এটিই সবথেকে কার্যকর সমাধান। আপনি কি চান আমি পুরো কোডটি লোকাল ডেটাবেজ দিয়ে কনভার্ট করে দেই?
