import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from google import genai  # 使用新版官方套件

app = Flask(__name__)

# ================= 1. 讀取金鑰 =================
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# ================= 2. 初始化設定 =================
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 新版 Gemini Client 設定
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
        # 新版發送請求方式
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=user_msg,
            config={
                'temperature': 0.9,
            }
        )
        reply_text = response.text
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    except Exception as e:
        print(f"Error: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="我的大腦還在升級中... (請稍後再試)")
        )

if __name__ == "__main__":
    app.run()
