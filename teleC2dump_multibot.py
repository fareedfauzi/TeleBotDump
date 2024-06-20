import requests
import sys
import time
import threading
import logging
from logging.handlers import RotatingFileHandler

# Error handling logger. Max 1GB size of log.
def setup_logger():
    h = RotatingFileHandler('teleC2dump.log', maxBytes=1*1024*1024*1024, backupCount=1)
    h.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %levelname%- %message%', datefmt='%Y-%m-%d %H:%M:%S')
    h.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)
    logger.addHandler(h)

# Retrieve username of the bot
def get_bot_username(botkey):
    url = f'https://api.telegram.org/bot{botkey}/getMe'
    r = requests.get(url)
    return r.json()

# Use copyMessage API to dump the message. Alternative, use forwardMessage API.
def copy_message(botkey, chatid, attacker_chat_id, message_id):
    url = f'https://api.telegram.org/bot{botkey}/copyMessage'
    req_data = {"from_chat_id": str(attacker_chat_id), "chat_id": str(chatid), "message_id": str(message_id)}
    r = requests.post(url, data=req_data)
    return r

# Get new updates for the latest messages. Use after we have bruteforces all messages.
def get_updates(botkey, offset=None):
    url = f'https://api.telegram.org/bot{botkey}/getUpdates'
    params = {'timeout': 100, 'offset': offset}
    r = requests.get(url, params=params)
    return r.json()

# Get all messages
def brute_force_messages(botkey, botname, chatid, attacker_chat_id, start_id):
    errors_get_messages = 0
    while True:
        try:
            r = copy_message(botkey, chatid, attacker_chat_id, start_id)
            if r.status_code != 200:
                logging.error(f'{botname} - Error retrieving message ID: {start_id} - Status code: {r.status_code}')
                errors_get_messages += 1
                if errors_get_messages > 20000:
                    break # Switch to getUpdates after too many errors. Meaning there's no more messages. Now switch to getUpdates API.
            start_id += 1
        except Exception as e:
            logging.error(f'{botname} - Exception retrieving message ID: {start_id} - Error: {e}')

# Get new and latest updates
def get_new_updates(botkey, botname, chatid, attacker_chat_id, last_update_id):
    while True:
        try:
            updates = get_updates(botkey, last_update_id + 1 if last_update_id else None)
            if 'result' in updates and updates['result']:
                for update in updates['result']:
                    last_update_id = update['update_id']
                    if 'message' in update:
                        new_message_id = update['message']['message_id']
                        response = copy_message(botkey, chatid, attacker_chat_id, new_message_id)
                        if response.status_code != 200:
                            logging.error(f'{botname} - Error retrieving new message ID: {new_message_id} - Status code: {response.status_code}')
            time.sleep(2)
        except Exception as e:
            logging.error(f'{botname} - Exception in get_new_updates - Error: {e}')
            time.sleep(5)

# Processing bot username, messages and updates
def processing_botData(botkey, attacker_chat_id, chatid, mode):
    try:
        # Retrieve bot's username
        bot_info = get_bot_username(botkey)
        if not bot_info.get('ok'):
            return
        botname = bot_info['result']['username']

        # Initialize start message id and update
        start_id = 1
        last_update_id = None

        # Brute force all messages
        if mode == "both":
            brute_force_messages(botkey, botname, chatid, attacker_chat_id, start_id)

        # Retrieve new messages updates
        get_new_updates(botkey, botname, chatid, attacker_chat_id, last_update_id)
    except Exception as e:
        logging.error(f'Error in processing_botData - Bot: {botkey} - Error: {e}')

def main():
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print("Usage: python3 teleC2dump_multibot.py <config_file> [-mode updateonly]")
        sys.exit(1)

    if sys.argv[1] in ('-h', '--help'):
        print("""
                Usage: python3 teleC2dump_multibot.py <config_file> [-mode updateonly]

                Options:
                -h, --help       Show this help message and exit

                Arguments:
                config_file          Configuration file containing bot tokens, attacker chat IDs, and your chat ID.
                                     Each line in the file should have the format: <BOT TOKEN ID> <ATTACKER CHAT ID> <YOUR CHAT ID>
                -mode updateonly     Only perform updates, skip brute force. Use case is when you only want the latest messages.

                Example of config file format:
                7342309939:AAFSgOLG_25mu-QZE8M7bSPufJJNknYj1JY 467115391 7093036821
                1234567890:ABCDeFGH_1ijKlMnOpQrStUvWxYz 987654321 7093036821
            """)
        sys.exit(0)
    
    config_file = sys.argv[1]
    mode = "both"
    
    if len(sys.argv) == 3 and sys.argv[2] == "-mode updateonly":
        mode = "updateonly"
    
    setup_logger()
    print("Sit back and relax, TeleC2Dump script is running...")

    # Perform multithread process for each of the bot in config_file
    threads = []
    with open(config_file, 'r') as file:
        lines = file.readlines()
        for i in lines:
            try:
                botkey, attacker_chat_id, chatid = i.strip().split()
                thread = threading.Thread(target=processing_botData, args=(botkey, attacker_chat_id, chatid, mode))
                threads.append(thread)
                thread.start()
            except ValueError:
                logging.error(f'Invalid format in config file: {i}')
                pass

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
