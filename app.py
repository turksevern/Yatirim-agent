
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Yatirim AI Agent", page_icon="📈", layout="wide")

# Basit CSS - tek satirda
st.markdown("<style>.main{padding:0rem 1rem}.stButton>button{width:100%;border-radius:10px;height:3rem;font-size:1.1rem}.metric-card{background:#1e1e1e;padding:1rem;border-radius:10px;margin:0.5rem 0}.buy{color:#00ff88;font-weight:bold;font-size:1.2rem}.sell{color:#ff4444;font-weight:bold;font-size:1.2rem}.hold{color:#ffaa00;font-weight:bold;font-size:1.2rem}.price-big{font-size:2.5rem;font-weight:bold;color:#fff}.change-pos{color:#00ff88;font-size:1.5rem;font-weight:bold}.change-neg{color:#ff4444;font-size:1.5rem;font-weight:bold}.cat{color:#4a9eff;font-size:1.1rem;font-weight:bold;margin-top:1rem}.price-card{background:linear-gradient(135deg,#1e1e1e 0%,#2d2d2d 100%);padding:1.5rem;border-radius:15px;margin:0.5rem 0;border-left:5px solid #4a9eff}.price-up{border-left-color:#00ff88}.price-down{border-left-color:#ff4444}.detail-row{display:flex;justify-content:space-between;margin:0.3rem 0}.detail-label{color:#888;font-size:0.9rem}.detail-value{color:#fff;font-size:1rem;font-weight:bold}</style>", unsafe_allow_html=True)

ALL_ASSETS = {
    "BIST": [
        {"symbol": "XU100.IS", "name": "BIST 100"},
        {"symbol": "THYAO.IS", "name": "THYAO"},
        {"symbol": "GARAN.IS", "name": "Garanti"},
        {"symbol": "ASELS.IS", "name": "Aselsan"},
        {"symbol": "KCHOL.IS", "name": "Koc Holding"},
        {"symbol": "SISE.IS", "name": "Sisecam"},
        {"symbol": "EREGL.IS", "name": "Eregli"},
        {"symbol": "BIMAS.IS", "name": "Bim"},
        {"symbol": "TUPRS.IS", "name": "Tupras"},
        {"symbol": "SAHOL.IS", "name": "Sabanci"},
        {"symbol": "AKBNK.IS", "name": "Akbank"},
        {"symbol": "YKBNK.IS", "name": "Yapi Kredi"},
        {"symbol": "PETKM.IS", "name": "Petkim"},
        {"symbol": "TOASO.IS", "name": "Tofas"},
        {"symbol": "ARCLK.IS", "name": "Arcelik"},
    ],
    "NASDAQ": [
        {"symbol": "SPY", "name": "S and P 500"},
        {"symbol": "QQQ", "name": "Nasdaq 100"},
        {"symbol": "NDX", "name": "Nasdaq Endeks"},
        {"symbol": "DIA", "name": "Dow Jones"},
        {"symbol": "IWM", "name": "Russell 2000"},
        {"symbol": "AAPL", "name": "Apple"},
        {"symbol": "MSFT", "name": "Microsoft"},
        {"symbol": "NVDA", "name": "NVIDIA"},
        {"symbol": "META", "name": "Meta"},
        {"symbol": "GOOGL", "name": "Google"},
        {"symbol": "AMZN", "name": "Amazon"},
        {"symbol": "TSLA", "name": "Tesla"},
        {"symbol": "AVGO", "name": "Broadcom"},
        {"symbol": "AMD", "name": "AMD"},
        {"symbol": "NFLX", "name": "Netflix"},
        {"symbol": "COIN", "name": "Coinbase"},
        {"symbol": "PLTR", "name": "Palantir"},
        {"symbol": "ARKK", "name": "ARKK"},
        {"symbol": "MSTR", "name": "MicroStrategy"},
        {"symbol": "INTC", "name": "Intel"},
        {"symbol": "PYPL", "name": "PayPal"},
        {"symbol": "CRM", "name": "Salesforce"},
        {"symbol": "SNOW", "name": "Snowflake"},
        {"symbol": "DDOG", "name": "Datadog"},
        {"symbol": "NET", "name": "Cloudflare"},
        {"symbol": "ZM", "name": "Zoom"},
        {"symbol": "ROKU", "name": "Roku"},
        {"symbol": "LCID", "name": "Lucid"},
        {"symbol": "RIVN", "name": "Rivian"},
        {"symbol": "MRNA", "name": "Moderna"},
        {"symbol": "REGN", "name": "Regeneron"},
        {"symbol": "ISRG", "name": "Intuitive Surgical"},
        {"symbol": "BKNG", "name": "Booking"},
        {"symbol": "ABNB", "name": "Airbnb"},
        {"symbol": "UBER", "name": "Uber"},
        {"symbol": "LYFT", "name": "Lyft"},
        {"symbol": "MDB", "name": "MongoDB"},
        {"symbol": "AI", "name": "C3.ai"},
        {"symbol": "SOUN", "name": "SoundHound"},
        {"symbol": "ASTS", "name": "AST SpaceMobile"},
        {"symbol": "RKLB", "name": "Rocket Lab"},
        {"symbol": "CELH", "name": "Celsius"},
        {"symbol": "LULU", "name": "Lululemon"},
        {"symbol": "MAR", "name": "Marriott"},
        {"symbol": "DKNG", "name": "DraftKings"},
        {"symbol": "TMUS", "name": "T-Mobile"},
        {"symbol": "ENPH", "name": "Enphase"},
        {"symbol": "FSLR", "name": "First Solar"},
        {"symbol": "PLUG", "name": "Plug Power"},
    ],
    "ALTIN_GUMUS": [
        {"symbol": "GC=F", "name": "Altin"},
        {"symbol": "SI=F", "name": "Gumus"},
        {"symbol": "GLD", "name": "Altin ETF"},
        {"symbol": "SLV", "name": "Gumus ETF"},
        {"symbol": "GDX", "name": "Altin Maden"},
        {"symbol": "IAU", "name": "Altin ETF2"},
        {"symbol": "PPLT", "name": "Platin"},
        {"symbol": "CPER", "name": "Bakir"},
    ],
    "KRIPTO": [
        {"symbol": "BTC-USD", "name": "Bitcoin"},
        {"symbol": "ETH-USD", "name": "Ethereum"},
        {"symbol": "SOL-USD", "name": "Solana"},
        {"symbol": "BNB-USD", "name": "Binance"},
        {"symbol": "XRP-USD", "name": "Ripple"},
        {"symbol": "ADA-USD", "name": "Cardano"},
        {"symbol": "DOGE-USD", "name": "Dogecoin"},
        {"symbol": "DOT-USD", "name": "Polkadot"},
        {"symbol": "AVAX-USD", "name": "Avalanche"},
        {"symbol": "MATIC-USD", "name": "Polygon"},
        {"symbol": "LINK-USD", "name": "Chainlink"},
        {"symbol": "UNI-USD", "name": "Uniswap"},
        {"symbol": "LTC-USD", "name": "Litecoin"},
        {"symbol": "BCH-USD", "name": "Bitcoin Cash"},
        {"symbol": "ETC-USD", "name": "Ethereum Classic"},
    ],
    "FONLAR": [
        {"symbol": "VTI", "name": "Vanguard Stock"},
        {"symbol": "VXUS", "name": "Vanguard Intl"},
        {"symbol": "BND", "name": "Vanguard Bond"},
        {"symbol": "REET", "name": "Global REIT"},
        {"symbol": "USO", "name": "WTI Petrol"},
        {"symbol": "UNG", "name": "Dogal Gaz"},
        {"symbol": "ICLN", "name": "Clean Energy"},
        {"symbol": "ARKQ", "name": "ARK Auto"},
        {"symbol": "ARKW", "name": "ARK Web"},
        {"symbol": "ARKF", "name": "ARK Fintech"},
        {"symbol": "ARKG", "name": "ARK Genomic"},
        {"symbol": "ARKX", "name": "ARK Space"},
        {"symbol": "TQQQ", "name": "3x Nasdaq"},
        {"symbol": "SQQQ", "name": "-3x Nasdaq"},
        {"symbol": "SOXL", "name": "3x Semi"},
        {"symbol": "FNGU", "name": "3x FANG+"},
    ],
}

def calculate_sma(series, window):
    return series.rolling(window=window, min_periods=window).mean()

def calculate_ema(series, window):
    return series.ewm(span=window, adjust=False, min_periods=window).mean()

def calculate_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window, min_periods=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window, min_periods=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series, fast=12, slow=26, signal=9):
    ema_fast = calculate_ema(series, fast)
    ema_slow = calculate_ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    return macd_line, signal_line, macd_line - signal_line

def calculate_bollinger(series, window=20, std_dev=2):
    sma = calculate_sma(series, window)
    std = series.rolling(window=window, min_periods=window).std()
    return sma + (std * std_dev), sma - (std * std_dev), sma

def calculate_atr(high, low, close, window=14):
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=window, min_periods=window).mean()

def calculate_indicators(df):
    if df is None or len(df) < 50:
        return df
    df = df.copy()
    df['SMA_20'] = calculate_sma(df['Close'], 20)
    df['SMA_50'] = calculate_sma(df['Close'], 50)
    df['SMA_200'] = calculate_sma(df['Close'], 200)
    df['RSI_14'] = calculate_rsi(df['Close'], 14)
    macd, signal, hist = calculate_macd(df['Close'])
    df['MACD'] = macd
    df['MACD_Signal'] = signal
    df['MACD_Hist'] = hist
    upper, lower, middle = calculate_bollinger(df['Close'])
    df['BB_Upper'] = upper
    df['BB_Lower'] = lower
    df['ATR_14'] = calculate_atr(df['High'], df['Low'], df['Close'], 14)
    return df

@st.cache_data(ttl=60)
def fetch_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="1m")
        if not data.empty:
            last = data.iloc[-1]
            prev = data.iloc[-2] if len(data) > 1 else last
            change = ((last['Close'] - prev['Close']) / prev['Close'] * 100) if prev['Close'] != 0 else 0
            day_change = ((last['Close'] - data['Open'].iloc[0]) / data['Open'].iloc[0] * 100) if data['Open'].iloc[0] != 0 else 0
            return {
                'price': round(last['Close'], 4),
                'change': round(change, 2),
                'day_change': round(day_change, 2),
                'volume': int(last['Volume']),
                'high': round(data['High'].max(), 4),
                'low': round(data['Low'].min(), 4),
                'open': round(data['Open'].iloc[0], 4),
                'prev_close': round(prev['Close'], 4) if len(data) > 1 else round(last['Close'], 4),
            }
    except:
        pass
    return None

@st.cache_data(ttl=300)
def fetch_history(symbol, period="6mo", interval="1d"):
    try:
        return yf.Ticker(symbol).history(period=period, interval=interval)
    except:
        return None

def generate_signal(df):
    if df is None or len(df) < 50:
        return {'signal': 'BEKLE', 'score': 0, 'reasons': ['Yetersiz veri']}
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last
    score = 0
    reasons = []
    rsi = last['RSI_14'] if 'RSI_14' in last and not pd.isna(last['RSI_14']) else 50
    if rsi < 30:
        score += 25
        reasons.append("RSI asiri satim (" + str(round(rsi, 1)) + ")")
    elif rsi > 70:
        score -= 25
        reasons.append("RSI asiri alim (" + str(round(rsi, 1)) + ")")
    if 'MACD' in last and 'MACD_Signal' in last:
        if last['MACD'] > last['MACD_Signal'] and prev['MACD'] <= prev['MACD_Signal']:
            score += 25
            reasons.append("MACD bullish")
        elif last['MACD'] < last['MACD_Signal'] and prev['MACD'] >= prev['MACD_Signal']:
            score -= 25
            reasons.append("MACD bearish")
        elif last['MACD'] > last['MACD_Signal']:
            score += 10
        else:
            score -= 10
    if 'SMA_50' in last and 'SMA_200' in last:
        if not pd.isna(last['SMA_50']) and not pd.isna(last['SMA_200']):
            if last['SMA_50'] > last['SMA_200']:
                score += 15
                reasons.append("Golden Cross")
            else:
                score -= 15
                reasons.append("Death Cross")
    if 'BB_Upper' in last and 'BB_Lower' in last:
        if last['Close'] < last['BB_Lower']:
            score += 15
            reasons.append("BB alt bandi")
        elif last['Close'] > last['BB_Upper']:
            score -= 15
            reasons.append("BB ust bandi")
    atr = last['ATR_14'] if 'ATR_14' in last and not pd.isna(last['ATR_14']) else 0
    current_price = last['Close']
    if score > 20:
        signal = 'AL'
        sl = round(current_price - (atr * 2), 2) if atr > 0 else None
        tp = round(current_price + (atr * 3), 2) if atr > 0 else None
    elif score < -20:
        signal = 'SAT'
        sl = round(current_price + (atr * 2), 2) if atr > 0 else None
        tp = round(current_price - (atr * 3), 2) if atr > 0 else None
    else:
        signal = 'BEKLE'
        sl = None
        tp = None
    return {'signal': signal, 'score': score, 'reasons': reasons, 'rsi': round(rsi, 1), 'atr': round(atr, 4), 'stop_loss': sl, 'take_profit': tp, 'sma_50': round(last['SMA_50'], 2) if 'SMA_50' in last and not pd.isna(last['SMA_50']) else None, 'sma_200': round(last['SMA_200'], 2) if 'SMA_200' in last and not pd.isna(last['SMA_200']) else None}

# ==================== SIDEBAR ====================

with st.sidebar:
    st.markdown("## Portfoyum")
    st.markdown("---")
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = []
    if 'selected_categories' not in st.session_state:
        st.session_state.selected_categories = []
    st.markdown("### Kategoriler")
    for category in ALL_ASSETS.keys():
        is_selected = st.checkbox(category, value=(category in st.session_state.selected_categories), key="cat_" + category)
        if is_selected and category not in st.session_state.selected_categories:
            st.session_state.selected_categories.append(category)
        elif not is_selected and category in st.session_state.selected_categories:
            st.session_state.selected_categories.remove(category)
    st.markdown("---")
    if st.session_state.selected_categories:
        st.markdown("### Varlik Secimi")
        for category in st.session_state.selected_categories:
            if category in ALL_ASSETS:
                st.markdown("<div class='cat'>" + category + "</div>", unsafe_allow_html=True)
                for asset in ALL_ASSETS[category]:
                    is_in_portfolio = any(p['symbol'] == asset['symbol'] for p in st.session_state.portfolio)
                    is_checked = st.checkbox(asset['symbol'] + " - " + asset['name'], value=is_in_portfolio, key="asset_" + asset['symbol'])
                    if is_checked and not is_in_portfolio:
                        st.session_state.portfolio.append({'symbol': asset['symbol'], 'name': asset['name'], 'type': category})
                    elif not is_checked and is_in_portfolio:
                        st.session_state.portfolio = [p for p in st.session_state.portfolio if p['symbol'] != asset['symbol']]
    st.markdown("---")
    st.markdown("### Manuel Ekle")
    new_symbol = st.text_input("Sembol", placeholder="orn: MSFT", key="new_sym").upper().strip()
    new_name = st.text_input("Isim", placeholder="orn: Microsoft", key="new_name")
    if st.button("Ekle", key="add_btn") and new_symbol:
        exists = any(p['symbol'] == new_symbol for p in st.session_state.portfolio)
        if not exists:
            st.session_state.portfolio.append({'symbol': new_symbol, 'name': new_name if new_name else new_symbol, 'type': 'Manuel'})
            st.success(new_symbol + " eklendi!")
            st.rerun()
        else:
            st.warning("Zaten var!")
    st.markdown("---")
    st.markdown("### Aktif Portfoy (" + str(len(st.session_state.portfolio)) + ")")
    for i, asset in enumerate(st.session_state.portfolio):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**" + asset['symbol'] + "**  " + asset['name'])
        with col2:
            if st.button("Sil", key="del_" + str(i)):
                st.session_state.portfolio.pop(i)
                st.rerun()
    st.markdown("---")
    if st.button("Tumunu Yenile", key="refresh_all"):
        st.cache_data.clear()
        st.rerun()

# ==================== ANA EKRAN ====================

st.markdown("# Yatirim AI Agent - Gercek Zamanli")
st.markdown("### Anlik Fiyatlar + Teknik Analiz + Al/Sat Sinyalleri")
st.markdown("---")

if not st.session_state.portfolio:
    st.info("Sol menuden kategori ve varlik secerek baslayin!")
    st.markdown("**Nasil kullanilir:** 1. Sol menuden **Kategori** secin  2. **Varliklari** secin  3. **Anlik fiyat** ve **sinyaller** gorun")
else:
    # Verileri cek
    price_data = {}
    signal_data = {}
    progress_bar = st.progress(0)
    total = len(st.session_state.portfolio)
    for i, asset in enumerate(st.session_state.portfolio):
        progress_bar.progress((i + 1) / total)
        price_data[asset['symbol']] = fetch_price(asset['symbol'])
        df = fetch_history(asset['symbol'], period="6mo", interval="1d")
        df = calculate_indicators(df)
        signal_data[asset['symbol']] = generate_signal(df)
    progress_bar.empty()

    # ANLIK FIYAT KARTLARI
    st.markdown("## Anlik Fiyatlar")

    positive_assets = []
    negative_assets = []
    neutral_assets = []

    for asset in st.session_state.portfolio:
        symbol = asset['symbol']
        price_info = price_data.get(symbol)
        if price_info:
            if price_info['change'] > 0:
                positive_assets.append((asset, price_info))
            elif price_info['change'] < 0:
                negative_assets.append((asset, price_info))
            else:
                neutral_assets.append((asset, price_info))

    # Pozitifler
    if positive_assets:
        st.markdown("### Yukselenler (Yesil)")
        cols = st.columns(min(4, len(positive_assets)))
        for i, (asset, price_info) in enumerate(positive_assets):
            with cols[i % 4]:
                st.markdown("<div class='price-card price-up'>", unsafe_allow_html=True)
                st.markdown("**" + asset['symbol'] + "**  " + asset['name'])
                st.markdown("<div class='price-big'>$" + str(price_info['price']) + "</div>", unsafe_allow_html=True)
                st.markdown("<div class='change-pos'>+ " + str(price_info['change']) + "% (1m) | + " + str(price_info['day_change']) + "% (gunluk)</div>", unsafe_allow_html=True)
                st.markdown("<div class='detail-row'><span class='detail-label'>Acilis:</span><span class='detail-value'>$" + str(price_info['open']) + "</span></div>", unsafe_allow_html=True)
                st.markdown("<div class='detail-row'><span class='detail-label'>Yuksek:</span><span class='detail-value'>$" + str(price_info['high']) + "</span></div>", unsafe_allow_html=True)
                st.markdown("<div class='detail-row'><span class='detail-label'>Dusuk:</span><span class='detail-value'>$" + str(price_info['low']) + "</span></div>", unsafe_allow_html=True)
                st.markdown("<div class='detail-row'><span class='detail-label'>Hacim:</span><span class='detail-value'>" + str(price_info['volume']) + "</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

    # Negatifler
    if negative_assets:
        st.markdown("### Dusenler (Kirmizi)")
        cols = st.columns(min(4, len(negative_assets)))
        for i, (asset, price_info) in enumerate(negative_assets):
            with cols[i % 4]:
                st.markdown("<div class='price-card price-down'>", unsafe_allow_html=True)
                st.markdown("**" + asset['symbol'] + "**  " + asset['name'])
                st.markdown("<div class='price-big'>$" + str(price_info['price']) + "</div>", unsafe_allow_html=True)
                st.markdown("<div class='change-neg'>- " + str(abs(price_info['change'])) + "% (1m) | - " + str(abs(price_info['day_change'])) + "% (gunluk)</div>", unsafe_allow_html=True)
                st.markdown("<div class='detail-row'><span class='detail-label'>Acilis:</span><span class='detail-value'>$" + str(price_info['open']) + "</span></div>", unsafe_allow_html=True)
                st.markdown("<div class='detail-row'><span class='detail-label'>Yuksek:</span><span class='detail-value'>$" + str(price_info['high']) + "</span></div>", unsafe_allow_html=True)
                st.markdown("<div class='detail-row'><span class='detail-label'>Dusuk:</span><span class='detail-value'>$" + str(price_info['low']) + "</span></div>", unsafe_allow_html=True)
                st.markdown("<div class='detail-row'><span class='detail-label'>Hacim:</span><span class='detail-value'>" + str(price_info['volume']) + "</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

    # Notrler
    if neutral_assets:
        st.markdown("### Notr")
        cols = st.columns(min(4, len(neutral_assets)))
        for i, (asset, price_info) in enume
