import requests
import time
import os

# ================== CONFIG ==================
USER_BOT_TOKEN = "8531499027:AAHIu6AMkHAyb9_z1Nnz_7QsIBsZdtGxHrs"#change when being developed on a new phone
DRIVER_BOT_TOKEN = "8796098383:AAEZkBM2Xhy3hFOedEftEBI7XHzvdlZVfXM"#change when being developed on a new phone

USER_API = f"https://api.telegram.org/bot{USER_BOT_TOKEN}"
DRIVER_API = f"https://api.telegram.org/bot{DRIVER_BOT_TOKEN}"

FASTAPI_URL = "http://127.0.0.1:8000/api/predict"

# ================== STORAGE ==================
users = {}
driver_chat_id = None
active_request = None

user_offset = None
driver_offset = None


# ================== COMMON ==================
def get_updates(api, offset):
    try:
        res = requests.get(
            f"{api}/getUpdates",
            params={"timeout": 1, "offset": offset},
            timeout=15
        )
        data = res.json()

        #  Safe return
        if "result" not in data:
            print("Telegram API Error:", data)
            return {"result": []}

        return data

    except Exception as e:
        print("Update error:", e)
        return {"result": []}


def send_message(api, chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = reply_markup
    requests.post(f"{api}/sendMessage", json=data)


def send_photo(api, chat_id, file_id):
    requests.post(f"{api}/sendPhoto", data={
        "chat_id": chat_id,
        "photo": file_id
    })


# ================== DOWNLOAD IMAGE ==================
def download_telegram_image(file_id):
    try:
        res = requests.get(f"{USER_API}/getFile", params={"file_id": file_id})
        file_path = res.json()["result"]["file_path"]

        file_url = f"https://api.telegram.org/file/bot{USER_BOT_TOKEN}/{file_path}"
        img_data = requests.get(file_url).content

        filename = f"temp_{int(time.time())}.jpg"
        with open(filename, "wb") as f:
            f.write(img_data)

        return filename
    except Exception as e:
        print("Download error:", e)
        return None


# ================== SEND TO FASTAPI ==================
def send_to_website(file_path, lat, lon):
    try:
        with open(file_path, "rb") as f:
            response = requests.post(
                FASTAPI_URL,
                files={"file": f},
                data={
                    "latitude": str(lat),
                    "longitude": str(lon)
                }
            )

        result = response.json()
        print("Server response:", result)

        return result
    except Exception as e:
        print("API error:", e)
        return None


# ================== USER BOT ==================
def handle_user(update):
    global active_request

    msg = update.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "")

    if not chat_id:
        return

    if chat_id not in users:
        users[chat_id] = {"state": "start", "photo": None, "location": None}

    user = users[chat_id]

    if user["state"] == "start":
        if text == ".":
            send_message(USER_API, chat_id, "Send accident image to continue")
            user["state"] = "waiting_photo"
        else:
            send_message(USER_API, chat_id, "Type '.' to start")

    elif user["state"] == "waiting_photo":
        if "photo" in msg:
            file_id = msg["photo"][-1]["file_id"]
            user["photo"] = file_id
            send_message(USER_API, chat_id, "Now send location")
            user["state"] = "waiting_location"
        else:
            send_message(USER_API, chat_id, "Please send an image")

    elif user["state"] == "waiting_location":
        if "location" in msg:
            lat = msg["location"]["latitude"]
            lon = msg["location"]["longitude"]
            user["location"] = (lat, lon)

            send_message(USER_API, chat_id, "🚑 Help is on the way!")

            #  SEND EVERYTHING
            send_to_driver(chat_id)

            users[chat_id] = {"state": "start", "photo": None, "location": None}
        else:
            send_message(USER_API, chat_id, "Please send location")


# ================== MAIN LOGIC ==================
def send_to_driver(user_chat_id):
    global driver_chat_id, active_request

    if not driver_chat_id:
        print("No driver connected")
        return

    user = users[user_chat_id]
    lat, lon = user["location"]

    # 1. Download image
    file_path = download_telegram_image(user["photo"])

    if file_path:
        #  2. Send to FastAPI
        result = send_to_website(file_path, lat, lon)

        # #  Send AI result to user
        # if result and "severity" in result:
        #     send_message(USER_API, user_chat_id, f" AI Result: {result['severity']}")

        # os.remove(file_path)

    active_request = user_chat_id

    #  DRIVER ALERT
    send_message(DRIVER_API, driver_chat_id, "🚨 ACCIDENT ALERT 🚨")

    send_photo(DRIVER_API, driver_chat_id, user["photo"])

    maps_link = f"https://maps.google.com/?q={lat},{lon}"
    send_message(DRIVER_API, driver_chat_id, f"📍 Location:\n{maps_link}")

    keyboard = {
        "inline_keyboard": [[
            {"text": "Mark as Reached", "callback_data": "done"}
        ]]
    }

    send_message(DRIVER_API, driver_chat_id, "Respond to this request", keyboard)


# ================== DRIVER BOT ==================
def handle_driver(update):
    global driver_chat_id, active_request

    msg = update.get("message")
    query = update.get("callback_query")

    if msg:
        driver_chat_id = msg["chat"]["id"]
        send_message(DRIVER_API, driver_chat_id, "Driver connected ✅")

    if query:
        callback_id = query["id"]
        data = query["data"]

        if data == "done" and active_request:
            send_message(DRIVER_API, driver_chat_id, "✅ Marked as completed")
            send_message(USER_API, active_request, "🚑 Help has arrived!")

            keyboard = {
                "inline_keyboard": [[
                    {"text": "Completed ✅", "callback_data": "disabled"}
                ]]
            }

            requests.post(f"{DRIVER_API}/editMessageReplyMarkup", json={
                "chat_id": driver_chat_id,
                "message_id": query["message"]["message_id"],
                "reply_markup": keyboard
            })

            active_request = None

        requests.post(f"{DRIVER_API}/answerCallbackQuery", data={
            "callback_query_id": callback_id
        })


# ================== MAIN LOOP ==================
print("Bot running...")

while True:
    user_data = get_updates(USER_API, user_offset)
    for upd in user_data.get("result", []):  # ✅ FIXED
        user_offset = upd["update_id"] + 1
        handle_user(upd)

    driver_data = get_updates(DRIVER_API, driver_offset)
    for upd in driver_data.get("result", []):  # ✅ FIXED
        driver_offset = upd["update_id"] + 1
        handle_driver(upd)

    time.sleep(0.2)