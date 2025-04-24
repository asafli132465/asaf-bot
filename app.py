from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
import telegram
import requests
import openai
import os
import json
from datetime import datetime

app = Flask(__name__)
log_file = "log.json"

# הגדרות טלגרם ו-API
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")
FINNHUB_TOKEN = os.getenv("FINNHUB_TOKEN", "YOUR_FINNHUB_API_KEY")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY", "YOUR_ALPHA_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_KEY")

bot = telegram.Bot(token=TELEGRAM_TOKEN)
openai.api_key = OPENAI_KEY

def send_telegram_message(text):
    try:
        bot.send_message(chat_id=CHAT_ID, text=text)
    except Exception as e:
        print("שגיאה בשליחת הודעת טלגרם:", e)

def log_recommendation(data):
    log = []
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            log = json.load(f)
    log.append(data)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

def fetch_stock_price(symbol="AAPL"):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_TOKEN}"
    r = requests.get(url)
    data = r.json()
    return data.get("c", 0)

def analyze_and_notify():
    price = fetch_stock_price()
    message = f"המחיר הנוכחי של AAPL הוא: {price} דולר."
    send_telegram_message(message)
    log_recommendation({
        "symbol": "AAPL",
        "price": price,
        "time": str(datetime.now())
    })

@app.route("/")
def index():
    return "בוט השקעות של אסף פועל!"

@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.json.get("question", "")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": user_input}]
    )
    answer = response["choices"][0]["message"]["content"]
    return {"answer": answer}

# הגדרת התראות כל 20 דקות
scheduler = BackgroundScheduler()
scheduler.add_job(analyze_and_notify, 'interval', minutes=20)
scheduler.start()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)