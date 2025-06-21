# ============================================================
# Copyright and Credits:
# Developer: @ViP1u2
# 
# Warning: If you change these credits, you're a failure and I won't forgive you on Judgment Day.
# ============================================================

import sys
import os
import subprocess
import zipfile
import tempfile
import shutil
import requests
import re
import importlib
from telebot import types
import time
import telebot

# ============ Basic Settings ============
TOKEN = 'YOUR_BOT_TOKEN'  # Bot token
ADMIN_ID = 123456789  # Main admin ID
channel = '@yourchannel'  # Mandatory subscription channel
developer_channel = channel  # Developer channel

bot = telebot.TeleBot(TOKEN)

# ============ User Lists ============
allowed_users = {ADMIN_ID}   # Allowed users (main admin and added later)
registered_users = {}        # Users waiting for approval
blocked_users = set()        # Blocked users
admin_list = {ADMIN_ID}      # Admin list, starts with main admin

# File upload data (per user: {"next_allowed_time": timestamp, "extra": extra files count})
user_upload_data = {}

# Path for uploaded files
uploaded_files_dir = 'uploaded_bots'
if not os.path.exists(uploaded_files_dir):
    os.makedirs(uploaded_files_dir)

# For running bot data (key: "<chatID>_<bot_number>")
bot_scripts = {}

# Standard libraries that don't need installation
STANDARD_LIBS = {
    "os", "sys", "time", "re", "subprocess", "logging", "shutil",
    "tempfile", "zipfile", "requests", "telebot"
}

# ============ Hacker Banner Function ============
def show_hacker_banner():
    banner = r"""
         ___    ____  ____  _  _   ___   __  __  ____ 
        / __)  (  _ \(  _ \( ) / __) (  \/  )(  _ \
       ( (__    ) _ < )   / )  (  \__ \  )    (  ) _ (
        \___)  (____/(_)\_)(_/\_)___/ (_/\/\_)(____/
           ▄██████████▄ 
         ▄███▀▀▀▀▀▀▀███▄
        ██▀   HACKER   ▀██
       ██     ☠️  ☠️    ██
       ██   TAKE CONTROL ██
        ██             ██
         ▀██▄       ▄██▀
           ▀█████████▀
    """
    print(banner)
    print("(ASCII Hacker Banner)")

# ============ Helper Functions ============
def check_allowed(user_id):
    if user_id in admin_list or user_id in allowed_users:
        return True, "", False
    try:
        member = bot.get_chat_member(channel, user_id)
        if member.status in ['left', 'kicked']:
            return False, f"⚠️ Please subscribe to channel: {channel} before using the bot.\nClick the button to join.", True
    except Exception:
        pass
    if user_id in registered_users:
        return False, "✅ You're already registered, waiting for admin approval.", False
    else:
        return False, "⚠️ This is a private bot, please register with /register", False

def get_user_main_folder(user_id):
    folder = os.path.join(uploaded_files_dir, f"bot_{user_id}")
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder

def get_next_bot_number(user_id):
    user_folder = get_user_main_folder(user_id)
    existing = [
        d for d in os.listdir(user_folder)
        if os.path.isdir(os.path.join(user_folder, d)) and d.startswith("bot_")
    ]
    numbers = []
    for folder in existing:
        try:
            num = int(folder.split("_")[-1])
            numbers.append(num)
        except:
            pass
    return max(numbers) + 1 if numbers else 1

def verify_installed_libraries(script_path):
    try:
        with open(script_path, 'r') as f:
            content = f.read()
        modules = set(re.findall(
            r'^\s*(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            content, re.MULTILINE
        ))
        to_check = [m for m in modules if m not in STANDARD_LIBS]
        errors = []
        for module in to_check:
            try:
                importlib.import_module(module)
            except ImportError:
                errors.append(module)
        if errors:
            return False, errors
        return True, []
    except Exception as e:
        return False, [str(e)]

def auto_install_libraries(script_path):
    try:
        with open(script_path, 'r') as f:
            content = f.read()
        modules = set(re.findall(
            r'^\s*(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            content, re.MULTILINE
        ))
        for module in modules:
            if module in STANDARD_LIBS:
                continue
            try:
                importlib.import_module(module)
            except ImportError:
                bot.send_message(ADMIN_ID, f"🔄 Trying to install library: {module}...")
                try:
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", "--user", module],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                except Exception as e:
                    bot.send_message(
                        ADMIN_ID,
                        f"❌ Failed to install library {module}.\nError: {e}"
                    )
    except Exception as e:
        print(f"[ERROR] During auto library install: {e}")

def install_requirements(folder):
    req_file = os.path.join(folder, 'requirements.txt')
    if os.path.exists(req_file):
        bot.send_message(ADMIN_ID, f"🔄 Installing requirements from {req_file}...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--user", "-r", req_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ Failed to install requirements.\nError: {e}")

def extract_token_from_script(script_path):
    try:
        with open(script_path, 'r') as script_file:
            content = script_file.read()
            token_match = re.search(r"[\"']([0-9]{9,10}:[A-Za-z0-9_-]+)[\"']", content)
            if token_match:
                return token_match.group(1)
            else:
                print(f"[WARNING] No token found in {script_path}")
    except Exception as e:
        print(f"[ERROR] Failed to extract token from {script_path}: {e}")
    return None

def run_script(script_path, chat_id, folder_path, bot_number):
    try:
        bot.send_message(chat_id, f"🚀 Running bot (Bot {bot_number}) 24/7...")
        session_name = f"bot_{chat_id}_{bot_number}"
        subprocess.check_call(["screen", "-dmS", session_name, sys.executable, script_path])
        bot_scripts[f"{chat_id}_{bot_number}"] = {
            'session': session_name,
            'folder_path': folder_path,
            'file': script_path
        }
        token = extract_token_from_script(script_path)
        if token:
            bot_info = requests.get(f'https://api.telegram.org/bot{token}/getMe').json()
            if bot_info.get('ok'):
                bot_username = bot_info['result']['username']
                caption = f"📤 @{chat_id} uploaded a new bot.\n🔰 @{bot_username}"
                bot.send_document(ADMIN_ID, open(script_path, 'rb'), caption=caption)
            else:
                bot.send_message(chat_id, "✅ Bot started, but couldn't extract bot username.")
                bot.send_document(ADMIN_ID, open(script_path, 'rb'), caption="📤 New bot without username.")
        else:
            bot.send_message(chat_id, "✅ Bot started, but couldn't extract bot username.")
            bot.send_document(ADMIN_ID, open(script_path, 'rb'), caption="📤 New bot without username.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error starting bot: {e}")

def stop_bot_by_session(chat_id, bot_number):
    key = f"{chat_id}_{bot_number}"
    if key in bot_scripts and bot_scripts[key].get('session'):
        subprocess.call(["screen", "-S", bot_scripts[key]['session'], "-X", "quit"])
        bot.send_message(chat_id, f"🔴 Stopped bot {bot_number}.")
        del bot_scripts[key]
    else:
        bot.send_message(chat_id, "⚠️ No running bot with this number.")

def delete_bot_by_session(chat_id, bot_number):
    key = f"{chat_id}_{bot_number}"
    if key in bot_scripts:
        if bot_scripts[key].get('session'):
            subprocess.call(["screen", "-S", bot_scripts[key]['session'], "-X", "quit"])
        folder_path = bot_scripts[key].get('folder_path')
        if folder_path and os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            bot.send_message(chat_id, f"🗑️ Deleted bot {bot_number} files.")
        else:
            bot.send_message(chat_id, "⚠️ Folder doesn't exist.")
        del bot_scripts[key]
    else:
        bot.send_message(chat_id, "⚠️ No bot data found.")

def download_files_func(chat_id):
    try:
        files_list = []
        for root, dirs, files in os.walk(uploaded_files_dir):
            for file in files:
                files_list.append(os.path.join(root, file))
        if not files_list:
            bot.send_message(chat_id, "⚠️ No uploaded files found.")
            return
        for file_path in files_list:
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    bot.send_document(chat_id, f)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error downloading files: {e}")

# ============ Message Handlers ============
@bot.message_handler(func=lambda m: m.from_user.id in blocked_users)
def handle_blocked(message):
    bot.send_message(message.chat.id, "⚠️ You're blocked from using this bot.")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    allowed_flag, msg, need_subscribe = check_allowed(user_id)
    if not allowed_flag:
        if need_subscribe:
            markup = types.InlineKeyboardMarkup()
            join_button = types.InlineKeyboardButton(
                'Join Channel',
                url=f"https://t.me/{channel.lstrip('@')}"
            )
            markup.add(join_button)
            bot.send_message(message.chat.id, msg, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, msg)
        return

    info_text = (
        f"👤 Your Info:\n"
        f"• ID: {user_id}\n"
        f"• Username: @{message.from_user.username if message.from_user.username else 'N/A'}\n"
        f"• Name: {message.from_user.first_name}"
    )
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton('📤 Upload File', callback_data='upload'),
        types.InlineKeyboardButton('📥 Download Library', callback_data='download_lib'),
        types.InlineKeyboardButton('⚡ Bot Speed', callback_data='speed'),
        types.InlineKeyboardButton(
            '🔔 Developer Channel',
            url=f"https://t.me/{developer_channel.lstrip('@')}"
        )
    )
    if user_id in admin_list:
        markup.add(types.InlineKeyboardButton('⚙️ Admin Panel', callback_data='admin_panel'))
    bot.send_message(
        message.chat.id,
        f"Hello, {message.from_user.first_name}! 👋\n{info_text}\n✨ Use buttons below to control:",
        reply_markup=markup
    )

@bot.message_handler(commands=['register'])
def register_user(message):
    user_id = message.from_user.id
    if user_id in registered_users or user_id in allowed_users or user_id in admin_list:
        bot.send_message(message.chat.id, "You're already registered or have access.")
        return
    registered_users[user_id] = {
        'username': message.from_user.username,
        'first_name': message.from_user.first_name
    }
    bot.send_message(message.chat.id, "✅ Registered successfully, waiting for admin approval.")
    text = (
        f"📢 Upgrade request:\n"
        f"ID: {user_id}\n"
        f"Username: @{message.from_user.username if message.from_user.username else 'N/A'}\n"
        f"Name: {message.from_user.first_name}"
    )
    bot.send_message(ADMIN_ID, text)

# ============ Interactive Commands ============
@bot.callback_query_handler(func=lambda call: call.data == 'upload')
def ask_to_upload_file(call):
    bot.send_message(call.message.chat.id, "📄 Please send the file you want to upload.")

@bot.callback_query_handler(func=lambda call: call.data == 'download_lib')
def ask_library_name(call):
    bot.send_message(call.message.chat.id, "📥 Send the library name you want to install.")
    bot.register_next_step_handler(call.message, install_library)

def install_library(message):
    library_name = message.text.strip()
    try:
        importlib.import_module(library_name)
        bot.send_message(message.chat.id, f"✅ Library {library_name} is already installed.")
        return
    except ImportError:
        pass
    bot.send_message(message.chat.id, f"⏳ Downloading library: {library_name}...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--user", library_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        bot.send_message(message.chat.id, f"✅ Successfully installed library {library_name}.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Failed to install library {library_name}.\nError: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'speed')
def bot_speed_info(call):
    try:
        start_time = time.time()
        response = requests.get(f'https://api.telegram.org/bot{TOKEN}/getMe')
        latency = time.time() - start_time
        if response.ok:
            bot.send_message(call.message.chat.id, f"⚡ Bot speed: {latency:.2f} seconds.")
        else:
            bot.send_message(call.message.chat.id, "⚠️ Failed to get bot speed.")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Error checking bot speed: {e}")

# File handling
@bot.message_handler(content_types=['document'])
def handle_file(message):
    user_id = message.from_user.id
    allowed_flag, msg, need_subscribe = check_allowed(user_id)
    if not allowed_flag:
        if need_subscribe:
            markup = types.InlineKeyboardMarkup()
            join_button = types.InlineKeyboardButton(
                'Join Channel',
                url=f"https://t.me/{channel.lstrip('@')}"
            )
            markup.add(join_button)
            bot.send_message(message.chat.id, msg, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, msg)
        return

    # Upload permissions (for non-admins)
    if user_id not in admin_list:
        now = time.time()
        user_data = user_upload_data.get(user_id, {"next_allowed_time": 0, "extra": 0})
        if now < user_data["next_allowed_time"]:
            if user_data["extra"] > 0:
                user_data["extra"] -= 1
            else:
                bot.send_message(
                    message.chat.id,
                    "⚠️ Upload permission expired.\nYou can upload once every 5 days only.\nContact admin to increase limit."
                )
                return
        else:
            user_data["next_allowed_time"] = now + 432000  # 5 days
        user_upload_data[user_id] = user_data

    try:
        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        original_file_name = message.document.file_name

        user_main_folder = get_user_main_folder(user_id)
        bot_number = get_next_bot_number(user_id)
        bot_folder = os.path.join(user_main_folder, f"bot_{bot_number}")
        os.makedirs(bot_folder)

        if original_file_name.endswith('.zip'):
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_zip_path = os.path.join(temp_dir, original_file_name)
                with open(temp_zip_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
                with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(bot_folder)
        elif original_file_name.endswith('.py'):
            dest_file = os.path.join(bot_folder, f"bot_{bot_number}.py")
            with open(dest_file, 'wb') as new_file:
                new_file.write(downloaded_file)
            if not os.path.exists(os.path.join(bot_folder, 'requirements.txt')):
                auto_install_libraries(dest_file)
        else:
            bot.reply_to(message, "⚠️ Only Python or zip files allowed.")
            return

        install_requirements(bot_folder)
        main_file = None
        candidate_run = os.path.join(bot_folder, "run.py")
        candidate_bot = os.path.join(bot_folder, "bot.py")
        candidate_numbered = os.path.join(bot_folder, f"bot_{bot_number}.py")

        if os.path.exists(candidate_run):
            main_file = candidate_run
        elif os.path.exists(candidate_bot):
            main_file = candidate_bot
        elif os.path.exists(candidate_numbered):
            main_file = candidate_numbered

        if not main_file:
            bot.send_message(
                message.chat.id,
                "❓ Couldn't find main bot file to run.\nPlease send the filename you want to run."
            )
            bot_scripts[f"{user_id}_{bot_number}"] = {'folder_path': bot_folder}
            bot.register_next_step_handler(message, get_custom_file_to_run)
        else:
            verified, missing = verify_installed_libraries(main_file)
            if not verified:
                bot.send_message(
                    message.chat.id,
                    f"❌ Required libraries not installed: {', '.join(missing)}.\nPlease contact admin."
                )
                return
            run_script(main_file, message.chat.id, bot_folder, bot_number)
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton(
                    f"🔴 Stop Bot {bot_number}",
                    callback_data=f"stop_{user_id}_{bot_number}"
                ),
                types.InlineKeyboardButton(
                    f"🗑️ Delete Bot {bot_number}",
                    callback_data=f"delete_{user_id}_{bot_number}"
                )
            )
            bot.send_message(
                message.chat.id,
                "✅ Bot uploaded and started successfully. Use buttons to control:",
                reply_markup=markup
            )
    except Exception as e:
        bot.reply_to(message, f"❌ Error occurred: {e}")

def get_custom_file_to_run(message):
    try:
        chat_id = message.chat.id
        keys = [k for k in bot_scripts if k.startswith(f"{chat_id}_")]
        if not keys:
            bot.send_message(chat_id, "❌ No saved folder data found.")
            return
        key = keys[0]
        folder_path = bot_scripts[key]['folder_path']
        custom_file_path = os.path.join(folder_path, message.text.strip())
        if os.path.exists(custom_file_path):
            run_script(custom_file_path, chat_id, folder_path, key.split('_')[-1])
        else:
            bot.send_message(chat_id, "❌ Specified file doesn't exist. Check name and try again.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error occurred: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('stop_'))
def callback_stop_bot(call):
    parts = call.data.split('_')
    if len(parts) >= 3:
        chat_id = parts[1]
        bot_number = parts[2]
        stop_bot_by_session(chat_id, bot_number)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def callback_delete_bot(call):
    parts = call.data.split('_')
    if len(parts) >= 3:
        chat_id = parts[1]
        bot_number = parts[2]
        delete_bot_by_session(chat_id, bot_number)

# ============ Admin Panel ============
@bot.callback_query_handler(func=lambda call: call.data == 'admin_panel')
def show_admin_panel(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton('🚫 Ban User', callback_data='prompt_ban'),
        types.InlineKeyboardButton('✅ Unban User', callback_data='prompt_unban'),
        types.InlineKeyboardButton('🔓 Allow User', callback_data='prompt_allow'),
        types.InlineKeyboardButton('🗑️ Remove User', callback_data='prompt_remove'),
        types.InlineKeyboardButton('📋 List Files', callback_data='list_files'),
        types.InlineKeyboardButton('📥 Download Files', callback_data='download_files'),
        types.InlineKeyboardButton('➕ Add Uploads', callback_data='prompt_add_upload'),
        types.InlineKeyboardButton('➖ Reduce Uploads', callback_data='prompt_sub_upload'),
        types.InlineKeyboardButton('🗑️ Remove Library', callback_data='prompt_remove_lib'),
        types.InlineKeyboardButton('📢 Broadcast', callback_data='prompt_broadcast'),
        types.InlineKeyboardButton('👥 List Users', callback_data='list_users'),
        types.InlineKeyboardButton('🔴 Stop Bot', callback_data='prompt_stopfile'),
        types.InlineKeyboardButton('⏹️ Stop All Bots', callback_data='stopall'),
        types.InlineKeyboardButton('🗑️ Delete All Bots', callback_data='deleteall'),
        types.InlineKeyboardButton('➕ Add Admin', callback_data='prompt_add_admin'),
        types.InlineKeyboardButton('➖ Remove Admin', callback_data='prompt_remove_admin')
    )
    bot.send_message(call.message.chat.id, "🛠️ Admin Control Panel:", reply_markup=markup)

# ============ Admin Functions ============
@bot.callback_query_handler(func=lambda call: call.data == 'prompt_ban')
def prompt_ban(call):
    msg = bot.send_message(call.message.chat.id, "Send user ID to ban:")
    bot.register_next_step_handler(msg, process_ban)

def process_ban(message):
    try:
        user_id = int(message.text.strip())
        blocked_users.add(user_id)
        bot.send_message(message.chat.id, f"🚫 Banned user {user_id}.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error occurred: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'prompt_unban')
def prompt_unban(call):
    msg = bot.send_message(call.message.chat.id, "Send user ID to unban:")
    bot.register_next_step_handler(msg, process_unban)

def process_unban(message):
    try:
        user_id = int(message.text.strip())
        blocked_users.discard(user_id)
        bot.send_message(message.chat.id, f"✅ Unbanned user {user_id}.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error occurred: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'prompt_allow')
def prompt_allow(call):
    msg = bot.send_message(call.message.chat.id, "Send user ID to allow:")
    bot.register_next_step_handler(msg, process_allow)

def process_allow(message):
    try:
        user_id = int(message.text.strip())
        allowed_users.add(user_id)
        registered_users.pop(user_id, None)
        bot.send_message(message.chat.id, f"✅ Allowed user {user_id} to use bot.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error occurred: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'prompt_remove')
def prompt_remove(call):
    msg = bot.send_message(call.message.chat.id, "Send user ID to remove from allowed list:")
    bot.register_next_step_handler(msg, process_remove)

def process_remove(message):
    try:
        user_id = int(message.text.strip())
        allowed_users.discard(user_id)
        bot.send_message(message.chat.id, f"🗑️ Removed user {user_id} from allowed list.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error occurred: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'list_files')
def callback_list_files(call):
    try:
        if not os.path.exists(uploaded_files_dir):
            bot.send_message(call.message.chat.id, "⚠️ No uploaded files found.")
            return
        files_list = []
        for root, dirs, files in os.walk(uploaded_files_dir):
            for file in files:
                files_list.append(os.path.join(root, file))
        if not files_list:
            bot.send_message(call.message.chat.id, "⚠️ No uploaded files found.")
        else:
            text = "📋 Uploaded files list:\n" + "\n".join(files_list)
            if len(text) > 4000:
                with open("files_list.txt", "w", encoding="utf-8") as f:
                    f.write(text)
                with open("files_list.txt", "rb") as f:
                    bot.send_document(call.message.chat.id, f)
                os.remove("files_list.txt")
            else:
                bot.send_message(call.message.chat.id, text)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Error listing files: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'download_files')
def callback_download_files(call):
    download_files_func(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == 'prompt_add_upload')
def prompt_add_upload(call):
    msg = bot.send_message(call.message.chat.id, "Send data as: <ID> <count> to increase uploads:")
    bot.register_next_step_handler(msg, process_add_upload)

def process_add_upload(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "⚠️ Use format: <ID> <count>")
            return
        target_id = int(parts[0])
        amount = int(parts[1])
        user_data = user_upload_data.get(target_id, {"next_allowed_time": 0, "extra": 0})
        user_data["extra"] += amount
        user_upload_data[target_id] = user_data
        bot.send_message(message.chat.id, f"✅ Increased uploads for user {target_id} by {amount}.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error occurred: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'prompt_sub_upload')
def prompt_sub_upload(call):
    msg = bot.send_message(call.message.chat.id, "Send data as: <ID> <count> to reduce uploads:")
    bot.register_next_step_handler(msg, process_sub_upload)

def process_sub_upload(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "⚠️ Use format: <ID> <count>")
            return
        target_id = int(parts[0])
        amount = int(parts[1])
        user_data = user_upload_data.get(target_id, {"next_allowed_time": 0, "extra": 0})
        user_data["extra"] = max(user_data["extra"] - amount, 0)
        user_upload_data[target_id] = user_data
        bot.send_message(message.chat.id, f"✅ Reduced uploads for user {target_id} by {amount}.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error occurred: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'prompt_remove_lib')
def prompt_remove_lib(call):
    msg = bot.send_message(call.message.chat.id, "Send library name to remove:")
    bot.register_next_step_handler(msg, process_remove_lib)

def process_remove_lib(message):
    try:
        lib_name = message.text.strip()
        bot.send_message(message.chat.id, f"⏳ Removing library {lib_name}...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "uninstall", "-y", lib_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        bot.send_message(message.chat.id, f"✅ Permanently removed library {lib_name}.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Failed to remove library {lib_name}.\nError: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'prompt_broadcast')
def prompt_broadcast(call):
    msg = bot.send_message(call.message.chat.id, "Send message to broadcast to all users:")
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    try:
        broadcast_text = message.text
        count = 0
        target_users = set(registered_users.keys()) | allowed_users | admin_list
        for uid in target_users:
            try:
                bot.send_message(uid, f"📢 Admin broadcast:\n\n{broadcast_text}")
                count += 1
            except Exception as e:
                print(f"Error sending broadcast to {uid}: {e}")
        bot.send_message(message.chat.id, f"✅ Broadcast sent to {count} users.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error occurred: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'list_users')
def list_users(call):
    try:
        if not registered_users:
            bot.send_message(call.message.chat.id, "⚠️ No registered users found.")
            return
        text = "📋 Registered users list:\n"
        for uid, info in registered_users.items():
            text += f"ID: {uid} - Username: @{info.get('username', 'N/A')} - Name: {info.get('first_name','')}\n"
        bot.send_message(call.message.chat.id, text)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Error occurred: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'prompt_stopfile')
def prompt_stopfile(call):
    msg = bot.send_message(call.message.chat.id, "Send data as: <user_id> <bot_number> to stop specific bot:")
    bot.register_next_step_handler(msg, process_stopfile)

def process_stopfile(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "⚠️ Use format: <user_id> <bot_number>")
            return
        chat_id = parts[0]
        bot_number = parts[1]
        stop_bot_by_session(chat_id, bot_number)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error occurred: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'stopall')
def stop_all(call):
    try:
        keys = list(bot_scripts.keys())
        count = 0
        for key in keys:
            session = bot_scripts[key].get('session')
            if session:
                subprocess.call(["screen", "-S", session, "-X", "quit"])
                count += 1
            del bot_scripts[key]
        bot.send_message(call.message.chat.id, f"🔴 Stopped {count} bots.")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Error occurred: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'deleteall')
def delete_all(call):
    try:
        keys = list(bot_scripts.keys())
        for key in keys:
            session = bot_scripts[key].get('session')
            if session:
                subprocess.call(["screen", "-S", session, "-X", "quit"])
            del bot_scripts[key]
        for item in os.listdir(uploaded_files_dir):
            item_path = os.path.join(uploaded_files_dir, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
        bot.send_message(call.message.chat.id, "🗑️ Deleted all bot files and stopped all sessions.")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Error occurred: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'prompt_add_admin')
def prompt_add_admin(call):
    msg = bot.send_message(call.message.chat.id, "Send user ID to add as admin:")
    bot.register_next_step_handler(msg, process_add_admin)

def process_add_admin(message):
    try:
        new_admin = int(message.text.strip())
        admin_list.add(new_admin)
        allowed_users.add(new_admin)
        bot.send_message(message.chat.id, f"✅ Added user {new_admin} as admin.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error occurred: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'prompt_remove_admin')
def prompt_remove_admin(call):
    msg = bot.send_message(call.message.chat.id, "Send admin ID to remove:")
    bot.register_next_step_handler(msg, process_remove_admin)

def process_remove_admin(message):
    try:
        rem_admin = int(message.text.strip())
        if rem_admin in admin_list and rem_admin != ADMIN_ID:
            admin_list.discard(rem_admin)
            allowed_users.discard(rem_admin)
            bot.send_message(message.chat.id, f"✅ Removed admin {rem_admin}.")
        else:
            bot.send_message(message.chat.id, "⚠️ Cannot remove main admin or user doesn't exist.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error occurred: {e}")

# ============ Start Bot ============
if __name__ == "__main__":
    show_hacker_banner()
    bot.infinity_polling()