import os
import json
import datetime
import requests
import yfinance as yf
from datetime import date, timedelta

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# ========== 在这里设置你关注的股票 ==========
WATCHLIST = ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN"]
# =============================================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    })

def check_earnings():
    alerts = []
    today = date.today()
    
    for symbol in WATCHLIST:
        try:
            ticker = yf.Ticker(symbol)
            cal = ticker.calendar
            
            if not cal:
                continue
            
            # 新版yfinance返回字典格式
            earnings_dates = []
            if isinstance(cal, dict):
                if 'Earnings Date' in cal:
                    ed = cal['Earnings Date']
                    if isinstance(ed, list):
                        earnings_dates = ed
                    else:
                        earnings_dates = [ed]
            
            for ed in earnings_dates:
                ed_date = ed.date() if hasattr(ed, 'date') else ed
                days_until = (ed_date - today).days
                
                if 0 <= days_until <= 7:
                    alerts.append(
                        f"📊 <b>{symbol}</b> 财报即将发布！\n"
                        f"📅 日期：{ed_date}\n"
                        f"⏰ 还有 {days_until} 天"
                    )
        except Exception as e:
            print(f"Error checking earnings for {symbol}: {e}")
    
    return alerts

def check_news():
    alerts = []
    
    for symbol in WATCHLIST:
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                continue
            
            # 只看6小时内的新闻
            cutoff = datetime.datetime.now().timestamp() - 6 * 3600
            recent = [n for n in news if n.get('providerPublishTime', 0) > cutoff]
            
            if recent:
                news_lines = []
                for n in recent[:3]:  # 最多3条
                    title = n.get('title', '')
                    link = n.get('link', '')
                    news_lines.append(f"• <a href='{link}'>{title}</a>")
                
                alerts.append(
                    f"📰 <b>{symbol}</b> 最新新闻：\n" + "\n".join(news_lines)
                )
        except Exception as e:
            print(f"Error checking news for {symbol}: {e}")
    
    return alerts

def main():
    print(f"开始监控 {date.today()}...")
    all_alerts = []
    
    earnings_alerts = check_earnings()
    news_alerts = check_news()
    
    all_alerts = earnings_alerts + news_alerts
    
    if all_alerts:
        for alert in all_alerts:
            send_telegram(alert)
            print(f"已发送: {alert[:50]}...")
    else:
        print("暂无新提醒")

if __name__ == "__main__":
    import pandas as pd
    main()
