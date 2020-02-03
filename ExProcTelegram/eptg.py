# This script establishes the connect to Telegram. It handles sending and receiving of messages.
# Imports
import json
import requests
import time
import urllib.parse
from pathlib import Path
# Some insight for later. All import should be understood as occurring from the main ExProc folder. Thus, even something imported from eptg.py needs to be imported as though from the root directory.
from ExProcTelegram import eptg_responder as responder

# Setup/Import of data, variables, paths
EP_Path = Path(__file__).parents[1]
datastore_folder = Path(EP_Path, "datastore")
telegram_folder = Path(EP_Path, "ExProcTelegram")


# Collecting some config variables
with open(datastore_folder / "ep_config.json", encoding="utf8") as datastore_auth:
    auth_json = json.load(datastore_auth)
    TELEGRAM_TOKEN = auth_json["api_keys"]["TELEGRAM_TOKEN"]

# Setting up other simple local variables
URL = "https://api.telegram.org/bot{}/".format(TELEGRAM_TOKEN)

def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js


def get_updates(offset=None, timeout=3600):  # Todo: Review this, decide if you like this timeout longpolling option
    url = URL + "getUpdates?timeout=" + str(timeout)
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return text, chat_id


def send_message(text, chat_id):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    get_url(url)


def respond_to_all(updates):  # Didn't like the idea of responding to multiple commands at a time. Rewriting to only respond to last update.
    #for update in updates["result"]: The original line
    update = updates["result"][-1]  # With this -1 indexing, only the final update should be responded to
    try:
        command = update["message"]["text"]
        answer = responder.messenger(command)
        chat = update["message"]["chat"]["id"]
        send_message(answer, chat)
    except Exception as e:
        print(e)


def main():
    try:
        with open("ExProcTelegram\\last_msg_id.txt", "r") as read_file:
            last_update_id = read_file.readline()
    except:
        print("Unable to read last update ID")
        last_update_id = None
    print("Last update ID: ", last_update_id)

    while True:
        print("Looped.", last_update_id)
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            with open("ExProcTelegram\\last_msg_id.txt", "w") as write_file:
                write_file.write(str(last_update_id))
            respond_to_all(updates)
        time.sleep(0.5)


if __name__ == '__main__':
    main()
