import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai

app = Flask(__name__)

# ================= 1. 讀取金鑰 =================
# 這些變數等等會在雲端設定，現在先寫好讀取的邏輯
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# ================= 2. 初始化設定 =================
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
genai.configure(api_key=GEMINI_API_KEY)

# ================= 3. 設定 AI 人設 (Prompt) =================
# 這裡決定了 AI 講話的風格
generation_config = {
    "temperature": 0.9,  # 創意度高一點
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
]

model = genai.GenerativeModel(
    model_name="gemini-pro", # 使用最快最便宜的模型
    generation_config=generation_config,
    safety_settings=safety_settings,
    system_instruction="""
    你是一個超級熱情、極度樂觀的「誇誇大師」。
    你的任務只有一個：無論使用者說什麼，你都要用盡全力稱讚他！
    
    指導原則：
    1. 如果使用者說好事，你要把它誇大十倍來讚美。
    2. 如果使用者說壞事（例如很累、搞砸了），你要稱讚他的努力、堅持或這份經歷的價值。
    3. 絕對不要說教，只要提供滿滿的情緒價值。
    """
)

# ================= 4. 伺服器入口 =================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# ================= 5. 處理訊息邏輯 =================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text
    
    try:
        # 建立聊天對話
        chat = model.start_chat(history=[])
        response = chat.send_message(user_msg)
        reply_text = response.text
        
        # 回傳給 LINE
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    except Exception as e:
        print(f"Error: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="我太激動了說不出話來！(系統忙碌中，請稍後再試)")
        )

if __name__ == "__main__":

    app.run()
