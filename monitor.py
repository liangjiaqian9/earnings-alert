import os
import requests
import datetime
from datetime import date

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
FMP_KEY = os.environ["FMP_API_KEY"]

WATCHLIST = ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN"]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    })

def check_earnings():
    """每天早上推送未来7天财报"""
    today = date.today()
    end = today + datetime.timedelta(days=7)
    
    url = f"https://financialmodelingprep.com/api/v3/earning_calendar"
    params = {
        "from": today.strftime("%Y-%m-%d"),
        "to": end.strftime("%Y-%m-%d"),
        "apikey": FMP_KEY
    }
    
    try:
        res = requests.get(url, params=params).json()
        alerts = []
        
        for item in res:
            if item.get("symbol") in WATCHLIST:
                symbol = item["symbol"]
                ed = item["date"]
                eps_est = item.get("epsEstimated", "N/A")
                
                alerts.append(
                    f"📊 <b>{symbol}</b> 财报预告\n"
                    f"📅 日期：{ed}\n"
                    f"📈 EPS预期：{eps_est}"
                )
        
        if alerts:
            header = f"🔔 <b>未来7天财报提醒</b>（{today}）\n\n"
            send_telegram(header + "\n\n".join(alerts))
        else:
            print("未来7天无财报")
            
    except Exception as e:
        print(f"财报检查失败: {e}")

def check_news():
    """每30分钟检查一次新闻"""
    for symbol in WATCHLIST:
        try:
            url = f"https://financialmodelingprep.com/api/v3/stock_news"
            params = {
                "tickers": symbol,
                "limit": 5,
                "apikey": FMP_KEY
            }
            news = requests.get(url, params=params).json()
            
            # 只看30分钟内的新闻
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=35)
            recent = []
            
            for n in news:
                pub = datetime.datetime.strptime(
                    n["publishedDate"], "%Y-%m-%d %H:%M:%S"
                )
                if pub > cutoff:
                    recent.append(n)
            
            if recent:
                lines = [f"• <a href='{n['url']}'>{n['title']}</a>" for n in recent[:3]]
                send_telegram(
                    f"📰 <b>{symbol}</b> 最新新闻：\n" + "\n".join(lines)
                )
                    
        except Exception as e:
            print(f"新闻检查失败 {symbol}: {e}")

import sys

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "news"
    
    # 强制发送测试消息
    send_telegram("✅ 机器人运行正常！正在监控：" + ", ".join(WATCHLIST))
    
    if mode == "earnings":
        check_earnings()
    else:
        check_news()
