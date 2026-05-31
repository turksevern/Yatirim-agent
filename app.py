
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Yatirim AI Agent", page_icon="📈", layout="wide")

st.markdown("<style>.main{padding:0rem 1rem}.stButton>button{width:100%;border-radius:10px;height:3rem;font-size:1.1rem}.metric-card{background:#1e1e1e;padding:1rem;border-radius:10px;margin:0.5rem 0}.buy{color:#00ff88;font-weight:bold;font-size:1.2rem}.sell{color:#ff4444;font-weight:bold;font-size:1.2rem}.hold{color:#ffaa00;font-weight:bold;font-size:1.2rem}.price-big{font-size:2rem;font-weight:bold;color:#fff}.change-pos{color:#00ff88;font-size:1.2rem;font-weight:bold}.change-neg{color:#ff4444;font-size:1.2rem;font-weight:bold}.cat{color:#4a9eff;font-size:1.1rem;font-weight:bold;margin-top:1rem}</style>", unsafe_allow_html=True)

ALL_ASSETS = {
    "BIST": [
        {"symbol": "XU100.IS", "name": "BIST 100"},
        {"symbol": "THYAO.IS", "name": "THYAO"},
        {"symbol": "GARAN.IS", "name": "Garanti"},
        {"symbol": "ASELS.IS", "name": "Aselsan"},
        {"symbol": "KCHOL.IS", "name": "Koc Holding"},
    ],
    "NASDAQ": [
        {"symbol": "SPY", "name": "S and P 500"},
        {"symbol": "QQQ", "name": "Nasdaq 100"},
        {"symbol": "AAPL", "name": "Apple"},
        {"symbol": "MSFT", "name": "Microsoft"},
        {"symbol": "NVDA", "name": "NVIDIA"},
        {"symbol": "META", "name": "Meta"},
        {"symbol": "GOOGL", "name": "Google"},
        {"symbol": "AMZN", "name": "Amazon"},
        {"symbol": "TSLA", "name": "Tesla"},
        {"symbol": "AMD", "name": "AMD"},
    ],
    "ALTIN_GUMUS": [
        {"symbol": "GC=F", "name": "Altin"},
        {"symbol": "SI=F", "name": "Gumus"},
        {"symbol": "GLD", "name": "Altin ETF"},
        {"symbol": "SLV", "name": "Gumus ETF"},
    ],
    "KRIPTO": [
        {"symbol": "BTC-USD", "name": "Bitcoin"},
        {"symbol": "ETH-USD", "name": "Ethereum"},
        {"symbol": "SOL-USD", "name": "Solana"},
        {"symbol": "BNB-USD", "name": "Binance"},
        {"symbol": "XRP-USD", "name": "Ripple"},
    ],
    "FONLAR": [
        {"symbol": "VTI", "name": "Vanguard Stock"},
        {"symbol": "VXUS", "name": "Vanguard Intl"},
        {"symbol": "BND", "name": "Vanguard Bond"},
        {"symbol": "TQQQ", "name": "3x Nasdaq"},
        {"symbol": "ARKK", "name": "ARKK"},
    ],
}

def calculate_sma(series, window):
    return series.rolling(window=window, min_periods=window).mean()

def calculate_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window, min_periods=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window, min_periods=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_indicators(df):
    if df is None or len(df) < 50:
        return df
    df = df.copy()
    df['SMA_20'] = calculate_sma(df['Close'], 20)
    df['SMA_50'] = calculate_sma(df['Close'], 50)
    df['RSI_14'] = calculate_rsi(df['Close'], 14)
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
    if 'SMA_20' in last and 'SMA_50' in last:
        if not pd.isna(last['SMA_20']) and not pd.isna(last['SMA_50']):
            if last['SMA_20'] > last['SMA_50']:
                score += 15
                reasons.append("SMA20 > SMA50")
            else:
                score -= 15
                reasons.append("SMA20 < SMA50")
    if score > 20:
        signal = 'AL'
    elif score < -20:
        signal = 'SAT'
    else:
        signal = 'BEKLE'
    return {'signal': signal, 'score': score, 'reasons': reasons, 'rsi': round(rsi, 1)}

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

    # ANLIK FIYAT TABLOSU
    st.markdown("## Anlik Fiyatlar")

    table_data = []
    for asset in st.session_state.portfolio:
        symbol = asset['symbol']
        price_info = price_data.get(symbol)
        signal = signal_data.get(symbol, {'signal': 'BEKLE', 'score': 0, 'reasons': []})
        if price_info:
            table_data.append({
                'Sembol': symbol,
                'Isim': asset['name'],
                'Fiyat': "$" + str(price_info['price']),
                '1m Degisim': str(price_info['change']) + "%",
                'Gunluk': str(price_info['day_change']) + "%",
                'Acilis': "$" + str(price_info['open']),
                'Yuksek': "$" + str(price_info['high']),
                'Dusuk': "$" + str(price_info['low']),
                'Hacim': str(price_info['volume']),
                'Sinyal': signal['signal'],
                'Skor': signal['score'],
                'RSI': signal['rsi'],
            })

    if table_data:
        df_table = pd.DataFrame(table_data)
        st.dataframe(df_table, use_container_width=True, hide_index=True)

    st.markdown("---")

    # SINYAL OZETI
    st.markdown("## Sinyal Ozeti")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        buy_count = sum(1 for s in signal_data.values() if s['signal'] == 'AL')
        st.metric("AL", buy_count)
    with col2:
        sell_count = sum(1 for s in signal_data.values() if s['signal'] == 'SAT')
        st.metric("SAT", sell_count)
    with col3:
        hold_count = sum(1 for s in signal_data.values() if s['signal'] == 'BEKLE')
        st.metric("BEKLE", hold_count)
    with col4:
        st.metric("Toplam", len(st.session_state.portfolio))

    st.markdown("---")
    st.markdown("## Detayli Analiz ve Grafikler")

    for asset in st.session_state.portfolio:
        symbol = asset['symbol']
        price_info = price_data.get(symbol)
        signal = signal_data.get(symbol, {'signal': 'BEKLE', 'score': 0, 'reasons': []})

        with st.expander(symbol + " - " + asset['name'] + " (" + signal['signal'] + ")"):
            col1, col2, col3 = st.columns([2, 2, 2])

            with col1:
                st.markdown("**" + symbol + "**")
                st.markdown("*" + asset['name'] + "*  " + asset['type'])
                if price_info:
                    st.markdown("Fiyat: $" + str(price_info['price']))
                    st.markdown("Degisim: " + str(price_info['change']) + "% (1m)")
                    st.markdown("Gunluk: " + str(price_info['day_change']) + "%")
                    st.markdown("Acilis: $" + str(price_info['open']))
                    st.markdown("Yuksek: $" + str(price_info['high']))
                    st.markdown("Dusuk: $" + str(price_info['low']))
                    st.markdown("Hacim: " + str(price_info['volume']))

            with col2:
                sig = signal['signal']
                if sig == 'AL':
                    st.markdown("<div class='buy'>AL</div>", unsafe_allow_html=True)
                elif sig == 'SAT':
                    st.markdown("<div class='sell'>SAT</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='hold'>BEKLE</div>", unsafe_allow_html=True)
                st.markdown("Skor: " + str(signal['score']))
                if signal['rsi']:
                    st.markdown("RSI: " + str(signal['rsi']))

            with col3:
                if signal['reasons']:
                    st.markdown("**Nedenler:**")
                    for reason in signal['reasons']:
                        st.markdown("- " + reason)

            # BASIT GRAFIK - st.line_chart
            df = fetch_history(symbol, period="3mo", interval="1d")
            if df is not None and not df.empty:
                df = calculate_indicators(df)
                chart_data = pd.DataFrame({
                    'Fiyat': df['Close'],
                    'SMA20': df['SMA_20'],
                    'SMA50': df['SMA_50'],
                })
                st.line_chart(chart_data, use_container_width=True)

st.markdown("---")
st.markdown("**Son guncelleme:** " + datetime.now().strftime('%H:%M:%S'))
st.markdown("*Bu uygulama egitim amaclidir. Yatirim tavsiyesi degildir.*")
