# What it is?
This script attempts to dump all messages from the C2 hosted in Telegram bot channels. 

Features:
1. Dumped all messages (increase speed too) and retrieve updates for the latest messages.
2. Have option to only retrieve updates for the latest messages.
3. Support multibots by running multi-thread execution for each bots in the given config file.
4. Allow dynamically addition for a new bot while the script running.
   
# How to use it?

## Get bot information
Extract the bot token ID and attacker chat ID from the malware. For example:
```
Bot token => 123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ
Chat ID => 123456789
```

Then, go to `https://api.telegram.org/bot<BOT_TOKEN>/getMe` to determine the bot's username. It will return something like this:
```json
{
  "ok": true,
  "result": {
    "id": 123456789,
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

## Join the bot channel
Go to Telegram, search the bot by username in the search bar and join the bot channel by click "/start" button.

## Get your chat ID
Get your chat ID from the bot using https://t.me/chatIDrobot to be use in config file.

## Setup config file
Open `config.txt` and input all the token IDs, chat IDs of the attacker, and your chat ID.
- Each line in the file should have the format: `<BOT TOKEN ID> <ATTACKER CHAT ID> <YOUR CHAT ID>`.
- Example of the config file format:
```
1234567890:AAFSgOABCDeFGH_1ijKlMnOpQrStUvWxYz 123415391 123456789
1234567890:ABCDeFGH_1ijKlMnOpQrStUvWxYz 987654321 123456789
```

## Usage of the script
### Help menu
```bash
$ python3 telebotdump.py -h
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
        1234567890:AAFSgOABCDeFGH_1ijKlMnOpQrStUvWxYz 123415391 123456789
        1234567890:ABCDeFGH_1ijKlMnOpQrStUvWxYz 987654321 123456789
```

### Run the script with default mode
```
$ python3 telebotdump.py config.txt
[*] Dumping your messages...
[*] Please check telebotdump.log for any issues
[*] To add more bot tokens ↓
NEW BOT TOKEN (ex. 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11): XXXXXXXXX:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
ATTACKER CHAT ID (ex. 987654321): XXXXXXXX
YOUR CHAT ID (ex. 1234567890): XXXXXXX

[*] To add more bot tokens ↓
NEW BOT TOKEN (ex. 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11):
```

### Running the script with mode updateonly
```
$ python3 telebotdump.py config.txt -mode updateonly
[*] MODE = updateonly
[*] Dumping your messages...
[*] Please check telebotdump.log for any issues
[*] To add more bot tokens ↓
NEW BOT TOKEN (ex. 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11):
```
