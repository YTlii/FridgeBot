import os
import logging
import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv

# 讀取 .env 檔案
load_dotenv()

# 設定 Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# LINE Bot credentials
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# 冰箱資料檔案
FRIDGE_FILE = 'fridge.json'

def load_fridge():
    try:
        with open(FRIDGE_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_fridge(fridge):
    with open(FRIDGE_FILE, 'w') as f:
        json.dump(fridge, f)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    logger.info("Received body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    fridge = load_fridge()

    if text.startswith('新增'):
        try:
            _, name, qty, expiry = text.split()
            fridge.append({'name': name, 'quantity': qty, 'expiry': expiry})
            save_fridge(fridge)
            reply = f"已新增 {name} {qty}，到期日 {expiry}"
        except:
            reply = "格式錯誤！請用：新增 <名稱> <數量> <到期日>"
    elif text == '查詢':
        if fridge:
            reply = '\n'.join([f"{item['name']} - {item['quantity']} - 到期: {item['expiry']}" for item in fridge])
        else:
            reply = '冰箱是空的！'
    elif text.startswith('刪除'):
        try:
            _, name = text.split()
            fridge = [item for item in fridge if item['name'] != name]
            save_fridge(fridge)
            reply = f"已刪除 {name}"
        except:
            reply = "格式錯誤！請用：刪除 <名稱>"
    else:
        reply = "指令：\n新增 <名稱> <數量> <到期日>\n查詢\n刪除 <名稱>"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)  # 改為 5001