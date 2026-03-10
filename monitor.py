import os
import requests
import datetime
from datetime import date

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

WATCHLIST = [
    # 美股七巨头
    "AAPL",   # Apple
    "MSFT",   # Microsoft
    "NVDA",   # NVIDIA
    "AMZN",   # Amazon
    "GOOGL",  # Google
    "META",   # Meta
    "TSLA",   # Tesla

    # AI芯片/硬件
    "AMD",    # AMD
    "INTC",   # Intel
    "QCOM",   # Qualcomm
    "ARM",    # ARM Holdings
    "AVGO",   # Broadcom
    "MRVL",   # Marvell Technology

    # AI软件/云平台
    "CRM",    # Salesforce
    "NOW",    # ServiceNow
    "PLTR",   # Palantir
    "AI",     # C3.ai
    "BBAI",   # BigBear.ai
    "SOUN",   # SoundHound
    "RXRX",   # Recursion

    # AI基础设施/服务器
    "SMCI",   # Super Micro Computer
    "DELL",   # Dell
    "HPE",    # HP Enterprise
    "NET",    # Cloudflare
    "SNOW",   # Snowflake

    # 电力/能源基础设施
    "VST",    # Vistra Energy
    "CEG",    # Constellation Energy
    "NRG",    # NRG Energy
    "ETR",    # Entergy
    "AEE",    # Ameren
    "GEV",    # GE Vernova
    "BE",     # Bloom Energy
    "OKLO",   # Oklo (核能)

    # 储能
    "EOSE",   # Eos Energy

   # 光互联/光纤
    "COHR",   # Coherent
    "LITE",   # Lumentum
    "VIAV",   # Viavi Solutions
    "AAOI",   # Applied Optoelectronics
    "GLW",    # Corning

    # 网络安全
    "CRWD",   # CrowdStrike
    "PANW",   # Palo Alto Networks

    # 数据中心冷却
    "VRT",    # Vertiv

    # 网络/通信基础设施
    "CSCO",   # Cisco
    "ANET",   # Arista Networks

    # 半导体设备/代工
    "ASML",   # ASML
    "TSM",    # Taiwan Semiconductor

    # 储存
    "SNDK",   # SanDisk
    "MU",     # Micron Technology

    # AI应用
    "ORCL",   # Oracle
    "APP",    # AppLovin
    "TEM",    # Tempus AI
    "PATH",   # UiPath
    "DUOL",   # Duolingo
    "SHOP",   # Shopify
    "CRCL",   # Circle

    # AI算力/挖矿
    "IREN",   # Iris Energy

]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    })

def check_earnings():
    import yfinance as yf
    today = date.today()
    alerts = []
    
    for symbol in WATCHLIST:
        try:
            ticker = yf.Ticker(symbol)
            cal = ticker.calendar
            
            if not cal or not isinstance(cal, dict):
                continue
            
            earnings_dates = cal.get('Earnings Date', [])
            if not isinstance(earnings_dates, list):
                earnings_dates = [earnings_dates]
            
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
            print(f"财报检查失败 {symbol}: {e}")
    
    if alerts:
        header = f"🔔 <b>未来7天财报提醒</b>（{today}）\n\n"
        send_telegram(header + "\n\n".join(alerts))
    else:
        print("未来7天无财报")

def check_news():
    try:
        import xml.etree.ElementTree as ET
        
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=35)
        
        for symbol in WATCHLIST:
            url = f"https://finviz.com/rss.ashx?t={symbol}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                continue
            
            root = ET.fromstring(response.content)
            items = root.findall('./channel/item')
            
            for item in items:
                pub_str = item.findtext('pubDate', '')
                title = item.findtext('title', '')
                link = item.findtext('link', '')
                source = item.findtext('source', '')
                
                try:
                    pub = datetime.datetime.strptime(
                        pub_str, "%a, %d %b %Y %H:%M:%S %z"
                    ).replace(tzinfo=None)
                except:
                    continue
                
                if pub > cutoff:
                    send_telegram(
                        f"📰 <b>{symbol}</b> | {source}\n"
                        f"<a href='{link}'>{title}</a>\n"
                        f"🕐 {pub_str}"
                    )
                    
    except Exception as e:
        print(f"新闻检查失败: {e}")
        send_telegram(f"⚠️ 新闻检查失败：{str(e)}")

PRIVATE_COMPANIES = [
    "OpenAI",
    "Anthropic",
    "SpaceX",
    "Stripe",
    "Databricks",
]

def check_private_companies():
    try:
        import xml.etree.ElementTree as ET
        
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=35)
        
        for company in PRIVATE_COMPANIES:
            query = company.replace(" ", "+")
            url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                continue
            
            root = ET.fromstring(response.content)
            items = root.findall('./channel/item')
            
            for item in items[:5]:  # 每家公司最多5条
                pub_str = item.findtext('pubDate', '')
                title = item.findtext('title', '')
                link = item.findtext('link', '')
                
                try:
                    pub = datetime.datetime.strptime(
                        pub_str, "%a, %d %b %Y %H:%M:%S %z"
                    ).replace(tzinfo=None)
                except:
                    continue
                
                if pub > cutoff:
                    send_telegram(
                        f"🏢 <b>{company}</b>\n"
                        f"<a href='{link}'>{title}</a>\n"
                        f"🕐 {pub_str}"
                    )
                    
    except Exception as e:
        print(f"私有公司新闻检查失败: {e}")

import sys

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "news"
    
    if mode == "earnings":
        check_earnings()
    else:
        check_news()
        check_private_companies() 
