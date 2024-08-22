import sys
import os
import subprocess
import tempfile
import glob
import re
import hashlib
import requests

def check_jadx_installed():
    try:
        subprocess.run(['jadx', '-v'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("Error: 'jadx' is not installed or not found in your PATH.")
        print("Please install JADX from https://github.com/skylot/jadx before running this script.")
        sys.exit(1)

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_bot_username(token):
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                return data["result"]["username"]
            else:
                return "Failed to retrieve bot username"
        else:
            return "Failed to connect to Telegram API"
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

def extract_telegram_data_from_apk(apk_path):
    print(f"[*] Processing {apk_path}")
    md5_hash = calculate_md5(apk_path)

    print("[*] Decompiling APK...")
    with tempfile.TemporaryDirectory() as temp_dir:
        result = subprocess.run(['jadx', '-v', '--no-res', '-d', temp_dir, apk_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Check if the decompilation encountered "No dex files found"
        if b'No dex files found' in result.stdout:
            print(f"[x] MD5: {md5_hash}")
            print(f"Decompilation failed. Reason: No dex files found in the APK.")
            print(f"Please run `jadx -v` for more information.")
            print(f"Tips: Proceed using GDA for manual extraction.\n")
            return
        
        print("[*] Finding Telegram bot tokens and chat IDs...")
        java_files = glob.glob(os.path.join(temp_dir, '**', '*.java'), recursive=True)
        bot_tokens = set()
        chat_ids = set()

        for file_path in java_files:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

                # Search for Telegram bot token in the form of "bot<digits>:<alphanumeric>"
                bot_token_matches = re.findall(r'https://api\.telegram\.org/bot(\d+:[\w-]+)', content)
                bot_tokens.update(bot_token_matches)

                # Search for Telegram chat IDs in the form of "chat_id=<digits>"
                chat_id_matches = re.findall(r'chat_id=(\d+)', content)
                chat_ids.update(chat_id_matches)

        if bot_tokens or chat_ids:
            print(f"[/] MD5: {md5_hash}")
            for token in bot_tokens:
                bot_username = get_bot_username(token)
                print(f"Found Telegram Bot Token: {token} (Username: {bot_username})")
            for chat_id in chat_ids:
                print(f"Found Telegram Chat ID: {chat_id}")
            print()
        else:
            print(f"[{md5_hash}] No Telegram Bot Token or Chat ID found.\n")

def main():
    check_jadx_installed()

    if len(sys.argv) != 2:
        print('Usage: python apk_telebotinfo_extractor.py /path/to/folder')
        sys.exit(1)
    folder_path = sys.argv[1]
    if not os.path.isdir(folder_path):
        print('Invalid directory path')
        sys.exit(1)
    
    # Collect all files in the folder
    files = glob.glob(os.path.join(folder_path, '*'))

    for file_path in files:
        extract_telegram_data_from_apk(file_path)

if __name__ == '__main__':
    main()
