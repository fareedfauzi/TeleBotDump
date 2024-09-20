#!/usr/bin/env python3
import argparse
import requests
import subprocess
import tempfile
import glob
import os
import re
import hashlib
import sys

# Helper functions for APK processing
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

def extract_telegram_data_from_apk(apk_path):
    print(f"[*] Processing {apk_path}")
    md5_hash = calculate_md5(apk_path)

    print("[*] Decompiling APK...")
    with tempfile.TemporaryDirectory() as temp_dir:
        result = subprocess.run(['jadx', '-v', '--no-res', '-d', temp_dir, apk_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if b'No dex files found' in result.stdout:
            print(f"[x] MD5: {md5_hash}")
            print(f"Decompilation failed. Reason: No dex files found in the APK.")
            print(f"Tips: Proceed using GDA for manual extraction.\n")
            return None, None
        
        print("[*] Finding Telegram bot tokens and chat IDs...")
        java_files = glob.glob(os.path.join(temp_dir, '**', '*.java'), recursive=True)
        bot_tokens = set()
        chat_ids = set()

        bot_token_patterns = re.compile(r'\d{9,10}:[A-Za-z0-9_-]{35,}')
        
        for file_path in java_files:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

                # Search for bot tokens in the form of "digits:alphanumeric"
                bot_token_matches = bot_token_patterns.findall(content)
                bot_tokens.update(bot_token_matches)

        for file_path in java_files:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

                # Search for chat_id, sendMessage, or api.telegram.org and extract chat ID
                relevant_sections = re.finditer(r'(chat_id|sendMessage|api\.telegram\.org)[^0-9-]*(-?\d{9,10})', content)
                
                for match in relevant_sections:
                    chat_id = match.group(2)
                    if not any(chat_id == bot_token.split(':')[0] for bot_token in bot_tokens):
                        chat_ids.add(chat_id)

        # Return found bot tokens and chat IDs
        return bot_tokens, chat_ids

# OSINT Analysis functions
def analyze_telegram(token, chat_id):
    print(f"\nAnalysis of token: {token} and chat ID: {chat_id}\n")

    # Get Bot Info
    url = f"https://api.telegram.org/bot{token}/getMe"
    response = requests.get(url)
    telegram_get_me = response.json().get('result')

    if telegram_get_me:
        print(f"Bot First Name: {telegram_get_me['first_name']}")
        print(f"Bot Username: {telegram_get_me['username']}")
        print(f"Bot User ID: {telegram_get_me['id']}")
        if 'can_read_all_group_messages' in telegram_get_me:
            print(f"Bot Can Read Group Messages: {telegram_get_me['can_read_all_group_messages']}")

        # Get Bot Status in Chat
        url = f"https://api.telegram.org/bot{token}/getChatMember?chat_id={chat_id}&user_id={telegram_get_me['id']}"
        response = requests.get(url)
        if response.json().get('result'):
            telegram_get_chat_member = response.json().get('result')
            print(f"Bot In The Chat Is An: {telegram_get_chat_member['status']}")
        elif response.json().get('description'):
            if response.json().get('parameters') and 'migrate_to_chat_id' in response.json().get('parameters'): 
                print(f"ATTENTION: {response.json().get('description')} - Migrated to: {response.json().get('parameters')['migrate_to_chat_id']}")
            else:
                print(f"ATTENTION: {response.json().get('description')}")

        # Get Chat Info
        url = f"https://api.telegram.org/bot{token}/getChat?chat_id={chat_id}"
        response = requests.get(url)
        telegram_get_chat = response.json().get('result')

        if 'title' in telegram_get_chat: print(f"Chat Title: {telegram_get_chat['title']}")
        print(f"Chat Type: {telegram_get_chat['type']}")
        print(f"Chat ID: {telegram_get_chat['id']}")
        if 'has_visible_history' in telegram_get_chat: print(f"Chat has Visible History: {telegram_get_chat['has_visible_history']}")
        if 'username' in telegram_get_chat: print(f"Chat Username: {telegram_get_chat['username']}")
        if 'invite_link' in telegram_get_chat: print(f"Chat Invite Link: {telegram_get_chat['invite_link']}")

        # Export Chat Invite Link
        url = f"https://api.telegram.org/bot{token}/exportChatInviteLink?chat_id={chat_id}"
        response = requests.get(url)
        telegram_chat_invite_link = response.json().get("result")
        print(f"Chat Invite Link (exported): {telegram_chat_invite_link}")

        # Create Chat Invite Link
        url = f"https://api.telegram.org/bot{token}/createChatInviteLink?chat_id={chat_id}"
        response = requests.get(url)
        telegram_chat_invite_link = response.json().get('result')
        if telegram_chat_invite_link and "invite_link" in telegram_chat_invite_link:
            print(f"Chat Invite Link (created): {telegram_chat_invite_link['invite_link']}")

        # Get Chat Member Count
        url = f"https://api.telegram.org/bot{token}/getChatMemberCount?chat_id={chat_id}"
        response = requests.get(url)
        telegram_chat_members_count = response.json().get('result')
        print(f"Number of users in the chat: {telegram_chat_members_count}")

        # Get Chat Administrators
        url = f"https://api.telegram.org/bot{token}/getChatAdministrators?chat_id={chat_id}"
        response = requests.get(url)
        telegram_get_chat_administrators = response.json().get('result')
        if telegram_get_chat_administrators:
            print(f"Administrators in the chat:")
            for user in telegram_get_chat_administrators:
                print(user['user'])
    else:
        print('Telegram token is invalid or revoked.')

def main():
    # Initialize argument parser
    parser = argparse.ArgumentParser(description='OSINT analysis for Telegram bots and APK extraction from multiple files.')
    parser.add_argument('-f', '--folder', type=str, help='Folder path containing APK files for extraction', required=False)
    parser.add_argument('-t', '--token', type=str, help='Telegram bot token (optional)', required=False)
    parser.add_argument('-c', '--chat_id', type=str, help='Telegram chat ID (optional)', required=False)
    args = parser.parse_args()

    # If both token and chat ID are provided, use them for analysis
    if args.token and args.chat_id:
        analyze_telegram(args.token, args.chat_id)
        return

    # Ensure JADX is installed if APK processing is required
    if args.folder:
        check_jadx_installed()

        # Get list of APK files in the folder
        folder_path = args.folder
        apk_files = glob.glob(os.path.join(folder_path, '*'))  # Match all files in the folder

        if not apk_files:
            print("No files found in the folder.")
            return

        for apk_path in apk_files:
            bot_tokens, chat_ids = extract_telegram_data_from_apk(apk_path)
            if bot_tokens and chat_ids:
                print(f"Extracted Bot Tokens: {bot_tokens}")
                print(f"Extracted Chat IDs: {chat_ids}")
                # Use the first bot token and chat ID for analysis if not supplied manually
                analyze_telegram(next(iter(bot_tokens)), next(iter(chat_ids)))
            else:
                print(f"No valid bot tokens or chat IDs found in the file: {apk_path}")
    else:
        print("Please provide a folder of APK files or supply a bot token and chat ID for analysis.")

if __name__ == '__main__':
    main()
