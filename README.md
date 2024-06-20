# What it is?
Upon analyzing and reversing a malware sample, we sometimes discover that the malware is abusing a Telegram bot for C2 (Command and Control) communication. As analysts, we may want to gain insight into the bot's communication with the infected device. Thus, this script attempts to dump all messages from the Telegram C2. 

The script is inspired by the [Turncoat](https://github.com/DODC/turncoat) project. However, I found that Turncoat does not retrieve the latest messages after brute-forcing all the messages, and we need to perform multi command execution on the script to run against multiple bots. So, this script comes to the rescue.

Features:
1. Perform both bruteforce all messages and retrieve updates for the latest messages.
2. Have option to only retrieve updates for the latest messages.
3. Support multibots by running multi-thread execution for each bots in the given config file.
4. Allow dynamically addition fpr a new bot while the script running.

# What it does?
- The code uses the `copyMessage` API to copy every message (by brute-forcing the message ID from 1 until the end) to our own chat ID.
- It switches to the `getUpdates` API once the brute-force returns many errors for message IDs (indicating there are no more messages). Then it waits/observes for the latest messages using `getUpdates`.
- Multithreading is used to perform the process, as we have multiple bot channels to retrieve messages from.
- `config.txt` contains the bot token ID, attacker chat ID, and my chat ID.
- You might need to install `requests` using `pip install requests` if you don't have it installed.

# How to use it?

1. Extract the bot token ID and attacker chat ID from the malware. Example:
```
7342309939:AAFSgOLG_25mu-QZE8M7bSPufJJNknYj1JY
7043536123
```

2. Go to `https://api.telegram.org/bot<BOT_TOKEN>/getMe` to determine the bot's username. It will return something like this:
```json
{
  "ok": true,
  "result": {
    "id": 7342309939,
    "is_bot": true,
    "first_name": "testbowt!",
    "username": "pocrobot_bot",
    "can_join_groups": true,
    "can_read_all_group_messages": false,
    "supports_inline_queries": false,
    "can_connect_to_business": false
  }
}
```

3. Go to Telegram, find the bot by username and join the bot.
4. Get your chat ID from the bot using https://t.me/chatIDrobot.
5. Open `config.txt` and input all the token IDs, chat IDs of the attacker, and your chat ID.
    - Each line in the file should have the format: `<BOT TOKEN ID> <ATTACKER CHAT ID> <YOUR CHAT ID>`.
    - Example of the config file format:
```
7342309939:AAFSgOLG_25mu-QZE8M7bSPufJJNknYj1JY 467115391 7093134421
1234567890:ABCDeFGH_1ijKlMnOpQrStUvWxYz 987654321 7093134421
```

6. Run the script
```
# Help menu
$ python3 teleC2dump.py -h

# Run the script with default mode
$ python3 teleC2dump.py config.txt
Sit back and relax, TeleC2Dump script is running...

Got a new bot token for the same campaign?
Enter new bot token: XXXXXXXXX:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
Enter attacker chat ID: XXXXXXXX
Enter your chat ID: XXXXXXX


Got a new bot token for the same campaign?
Enter new bot token:

# Running the script with mode updateonly
$ python3 teleC2dump.py config.txt -mode updateonly
```
