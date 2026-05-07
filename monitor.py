import os
import requests
import datetime
from datetime import date
import re

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    })

def get_sp500():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

        tickers = re.findall(r'<td><a href="/wiki/[^"]*" title="[^"]*">([A-Z]{1,5})</a></td>', response.text)

        if len(tickers) < 400:
            print(f"第一种方法只抓到{len(tickers)}支，尝试备用方法...")
            tickers = re.findall(r'symbol=([A-Z]{1,5})"', response.text)

        if len(tickers) < 400:
            print(f"第二种方法只抓到{len(tickers)}支，尝试第三种方法...")
            import pandas as pd
            tables = pd.read_html(url)
            for table in tables:
                if 'Symbol' in table.columns:
                    tickers = table['Symbol'].tolist()
                    break

        tickers = [t for t in tickers if t and 1 <= len(t) <= 5]
        tickers = list(set(tickers))
        print(f"S&P500抓取结果: {len(tickers)}支")
        return tickers

    except Exception as e:
        print(f"获取S&P500列表失败: {e}")
        return []

EXTRA_WATCHLIST = [
    # 美股七巨头
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA",
    # AI芯片/硬件
    "AMD", "INTC", "QCOM", "ARM", "AVGO", "MRVL",
    # AI软件/云平台
    "CRM", "NOW", "PLTR", "AI", "BBAI", "SOUN", "RXRX",
    # AI基础设施/服务器
    "SMCI", "DELL", "HPE", "NET", "SNOW",
    # 电力/能源基础设施
    "VST", "CEG", "NRG", "ETR", "AEE", "GEV", "BE", "OKLO",
    # 储能
    "EOSE",
    # 光互联/光纤
    "COHR", "LITE", "VIAV", "AAOI", "GLW",
    # 网络安全
    "CRWD", "PANW",
    # 数据中心冷却
    "VRT",
    # 网络/通信基础设施
    "CSCO", "ANET",
    # 半导体设备/代工
    "ASML", "TSM",
    # 储存
    "SNDK", "MU",
    # AI应用
    "ORCL", "APP", "TEM", "PATH", "DUOL", "SHOP", "CRCL",
    # AI算力/挖矿
    "IREN",
    # 手术机器人/医疗
    "ISRG",
    # 其他高成长
    "MELI", "TTD", "WDAY",
    # 新增
    "OSS", "POET", "NOVT", "TMDX", "ZBRA",
    "SEDG", "PI", "BWXT", "GCT", "HIMX",
]

def get_watchlist():
    sp500 = get_sp500()
    combined = list(set(sp500 + EXTRA_WATCHLIST))
    print(f"总监控股票数: {len(combined)}")
    return combined

def get_earnings_time(symbol):
    """从Earnings Whispers获取财报时间（盘前/盘后）"""
    try:
        url = f"https://www.earningswhispers.com/stocks/{symbol.lower()}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)

        text = response.text.lower()
        if "before open" in text or "before the open" in text:
            return "盘前 🌅（温哥华凌晨 4:00-6:00）"
        elif "after close" in text or "after the close" in text:
            return "盘后 🌙（温哥华下午 1:00-2:00）"
        else:
            return "时间待定 🕐"
    except:
        return "时间待定 🕐"

def check_earnings():
    today = date.today()
    alerts = []
    WATCHLIST = get_watchlist()

    import yfinance as yf
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
                    if days_until <= 1:
                        earnings_time = get_earnings_time(symbol)
                    else:
                        earnings_time = "时间待定 🕐（临近时更新）"
                    alerts.append((ed_date,
                        f"📊 <b>{symbol}</b> 财报即将发布！\n"
                        f"📅 日期：{ed_date}\n"
                        f"🕐 {earnings_time}\n"
                        f"⏰ 还有 {days_until} 天"
                    ))
        except Exception as e:
            print(f"财报检查失败 {symbol}: {e}")

    if alerts:
        valid_alerts = []
        for item in alerts:
            if isinstance(item, tuple) and len(item) == 2:
                valid_alerts.append(item)
            else:
                valid_alerts.append((today, item))

        valid_alerts.sort(key=lambda x: x[0])
        sorted_alerts = [msg for _, msg in valid_alerts]
        header = f"🔔 <b>未来7天财报提醒</b>（{today}）\n\n"
        send_telegram(header + "\n\n".join(sorted_alerts))
    else:
        print("未来7天无财报")

def check_witching_days():
    today = date.today()
    alerts = []

    def get_third_friday(year, month):
        first_day = date(year, month, 1)
        days_until_friday = (4 - first_day.weekday()) % 7
        first_friday = first_day + datetime.timedelta(days=days_until_friday)
        return first_friday + datetime.timedelta(weeks=2)

    for delta_months in range(2):
        check_month = today.month + delta_months
        check_year = today.year
        if check_month > 12:
            check_month -= 12
            check_year += 1

        third_friday = get_third_friday(check_year, check_month)
        days_until = (third_friday - today).days

        if 0 <= days_until <= 7:
            is_quarterly = check_month in [3, 6, 9, 12]

            if is_quarterly:
                witching_type = "⚠️ <b>四巫日（Quadruple Witching）</b>"
                desc = "股指期货、股指期权、个股期货、个股期权同时到期\n历史上市场波动极大，成交量暴增"
            else:
                witching_type = "⚠️ <b>月度期权到期日（Monthly Opex）</b>"
                desc = "月度期权到期，市场可能出现异常波动"

            alerts.append(
                f"{witching_type}\n"
                f"📅 日期：{third_friday}（{days_until}天后）\n"
                f"🕐 温哥华时间：下午 1:00（市场收盘）\n"
                f"📌 {desc}"
            )

    if alerts:
        send_telegram("\n\n".join(alerts))
    else:
        print("未来7天无巫日")

def check_economic_events():
    today = date.today()
    alerts = []

    # FOMC
    try:
        fomc_url = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
        response = requests.get(fomc_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)

        fomc_dates = re.findall(r'(\w+ \d{1,2}(?:-\d{1,2})?),?\s*(\d{4})', response.text)

        months = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }

        for date_str, year in fomc_dates:
            try:
                parts = date_str.split()
                if len(parts) < 2:
                    continue
                month_str = parts[0]
                day_str = parts[1].split('-')[-1]

                if month_str not in months:
                    continue

                event_date = date(int(year), months[month_str], int(day_str))
                days_until = (event_date - today).days

                if 0 <= days_until <= 7:
                    alerts.append(
                        f"🏦 <b>FOMC利率决议</b>\n"
                        f"📅 日期：{event_date}（{days_until}天后）\n"
                        f"🕐 温哥华时间：下午 11:00\n"
                        f"📌 美联储利率决定，市场波动极大"
                    )
            except:
                continue

    except Exception as e:
        print(f"FOMC日期获取失败: {e}")

    # CPI
    try:
        cpi_url = "https://www.bls.gov/schedule/news_release/cpi.htm"
        response = requests.get(cpi_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)

        cpi_dates = re.findall(r'(\w+ \d{1,2},\s*\d{4})', response.text)

        for date_str in cpi_dates:
            try:
                event_date = datetime.datetime.strptime(date_str.strip(), "%B %d, %Y").date()
                days_until = (event_date - today).days

                if 0 <= days_until <= 7:
                    alerts.append(
                        f"📈 <b>CPI通胀数据发布</b>\n"
                        f"📅 日期：{event_date}（{days_until}天后）\n"
                        f"🕐 温哥华时间：早上 5:30\n"
                        f"📌 消费者价格指数，影响美联储政策预期"
                    )
            except:
                continue

    except Exception as e:
        print(f"CPI日期获取失败: {e}")

    # PCE
    try:
        pce_url = "https://www.bea.gov/news/schedule"
        response = requests.get(pce_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)

        pce_dates = re.findall(r'Personal Income[^<]*<[^>]*>([^<]*\d{4}[^<]*)<', response.text)

        if not pce_dates:
            pce_dates = re.findall(r'(\w+ \d{1,2},\s*\d{4})', response.text)

        for date_str in pce_dates:
            try:
                clean = re.search(r'\w+ \d{1,2},\s*\d{4}', date_str)
                if not clean:
                    continue
                event_date = datetime.datetime.strptime(clean.group().strip(), "%B %d, %Y").date()
                days_until = (event_date - today).days

                if 0 <= days_until <= 7:
                    alerts.append(
                        f"💰 <b>PCE物价指数发布</b>\n"
                        f"📅 日期：{event_date}（{days_until}天后）\n"
                        f"🕐 温哥华时间：早上 5:30\n"
                        f"📌 美联储最看重的通胀指标，直接影响利率决策"
                    )
            except:
                continue

    except Exception as e:
        print(f"PCE日期获取失败: {e}")

    if alerts:
        send_telegram("\n\n".join(alerts))
    else:
        print("未来7天无重大经济事件")

import sys

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "earnings"

    if mode == "earnings":
        check_earnings()
        check_witching_days()
        check_economic_events()
