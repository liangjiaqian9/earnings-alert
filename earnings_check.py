import requests
import datetime
import os

API_KEY = os.getenv("FMP_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

stocks = [
"AAPL","MSFT","NVDA","GOOGL","META",
"TSLA","AMZN","AMD","NFLX","INTC",
"PLTR","COIN","CRM","SHOP","BABA",
"PYPL","UBER","DIS","ORCL","ADBE",
"SNOW","SQ","BA","JPM","GS",
"XOM","CVX","PFE","NKE","MRNA"
]

today = datetime.date.today()
target_date = today + datetime.timedelta(days=3)

url = f"https://financialmodelingprep.com/api/v3/earning_calendar?from={today}&to={target_date}&apikey={API_KEY}"

response = requests.get(url)
data = response.json()

alerts = []

for item in data:
    if item["symbol"] in stocks:
        alerts.append(f"{item['symbol']} earnings on {item['date']}")

if alerts:
    message = "📢 Earnings in 3 days:\n" + "\n".join(alerts)
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(telegram_url, data={
        "chat_id": CHAT_ID,
        "text": message
    })
