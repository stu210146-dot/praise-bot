import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from google import genai

app = Flask(__name__)

# ================= 1. 讀取金鑰 =================
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# ================= 2. 初始化設定 =================
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 設定 Google Gemini 新版客戶端
client = genai.Client(api_key=GEMINI_API_KEY)

# ================= 3. 伺服器入口 =================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# ================= 4. 處理訊息邏輯 =================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text
    
    try:
        # 使用新版語法呼叫 AI
        response = client.models.generate_content(
           model='gemini-2.5-flash',
            contents=user_msg,
        )
        reply_text = response.text
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    except Exception as e:
        print(f"Error: {e}")
        # 如果出錯，回傳錯誤訊息方便除錯
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="大腦還在暖身中，請再試一次！")
        )

if __name__ == "__main__":
    app.run()


