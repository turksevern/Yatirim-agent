
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Yatirim AI Agent", page_icon="📈", layout="wide")

st.markdown("<style>.main{padding:0rem 1rem}.stButton>button{width:100%;border-radius:10px;height:3rem;font-size:1.1rem}.metric-card{background:#1e1e1e;padding:1rem;border-radius:10px;margin:0.5rem 0}.buy{color:#00ff88;font-weight:bold;font-size:1.2rem}.sell{color:#ff4444;font-weight:bold;font-size:1.2rem}.hold{color:#ffaa00;font-weight:bold;font-size:1.2rem}.price-big{font-size:2rem;font-weight:bold;color:#fff}.change-pos{color:#00ff88;font-size:1.2rem;font-weight:bold}.change-neg{color:#ff4444;font-size:1.2rem;font-weight:bold}.cat{color:#4a9eff;font-size:1.1rem;font-weight:bold;margin-top:1rem}.scan-result{background:#1a3a1a;padding:1rem;border-radius:10px;margin:0.5rem 0;border-left:5px solid #00ff88}.scan-header{color:#00ff88;font-size:1.3rem;font-weight:bold}</style>", unsafe_allow_html=True)

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
        {"symbol": "AAPL", "name": "Apple"},
        {"symbol": "MSFT", "name": "Microsoft"},
        {"symbol": "NVDA", "name": "NVIDIA"},
        {"symbol": "META", "name": "Meta"},
        {"symbol": "GOOGL", "name": "Google"},
        {"symbol": "AMZN", "name": "Amazon"},
        {"symbol": "TSLA", "name": "Tesla"},
        {"symbol": "AMD", "name": "AMD"},
        {"symbol": "NFLX", "name": "Netflix"},
        {"symbol": "COIN", "name": "Coinbase"},
        {"symbol": "PLTR", "name": "Palantir"},
        {"symbol": "ARKK", "name": "ARKK"},
        {"symbol": "MSTR", "name": "MicroStrategy"},
    ],
    "ALTIN_GUMUS": [
        {"symbol": "GC=F", "name": "Altin"},
        {"symbol": "SI=F", "name": "Gumus"},
        {"symbol": "GLD", "name": "Altin ETF"},
        {"symbol": "SLV", "name": "Gumus ETF"},
        {"symbol": "GDX", "name": "Altin Maden"},
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
    ],
    "FONLAR": [
        {"symbol": "VTI", "name": "Vanguard Stock"},
        {"symbol": "VXUS", "name": "Vanguard Intl"},
        {"symbol": "BND", "name": "Vanguard Bond"},
        {"symbol": "TQQQ", "name": "3x Nasdaq"},
        {"symbol": "SQQQ", "name": "-3x Nasdaq"},
        {"symbol": "SOXL", "name": "3x Semi"},
        {"symbol": "ARKQ", "name": "ARK Auto"},
        {"symbol": "ARKW", "name": "ARK Web"},
        {"symbol": "ARKF", "name": "ARK Fintech"},
        {"symbol": "ARKG", "name": "ARK Genomic"},
        {"symbol": "ARKX", "name": "ARK Space"},
        {"symbol": "FNGU", "name": "3x FANG+"},
    ],
}

TIMEFRAMES = {
    "Kisa": {"period": "1mo", "interval": "1h", "label": "1-30 gun"},
    "Orta": {"period": "6mo", "interval": "1d", "label": "1-6 ay"},
    "Uzun": {"period": "2y", "interval": "1wk", "label": "6+ ay"},
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

def generate_signal(df, symbol="", asset_type=""):
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

def scan_category(category, timeframe_key):
    """Kategorideki tum varliklari tarar, AL sinyali verenleri dondurur"""
    if category not in ALL_ASSETS:
        return []

    tf = TIMEFRAMES[timeframe_key]
    results = []

    for asset in ALL_ASSETS[category]:
        try:
            df = fetch_history(asset['symbol'], period=tf['period'], interval=tf['interval'])
            df = calculate_indicators(df)
            signal = generate_signal(df, asset['symbol'], category)

            if signal['signal'] == 'AL':
                price_info = fetch_price(asset['symbol'])
                results.append({
                    'symbol': asset['symbol'],
                    'name': asset['name'],
                    'score': signal['score'],
                    'rsi': signal['rsi'],
                    'reasons': signal['reasons'],
                    'price': price_info['price'] if price_info else None,
                    'change': price_info['change'] if price_info else None,
                    'timeframe': timeframe_key,
                })
        except:
            pass

    # Skora gore sirala (en yuksek skor en basta)
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

# ==================== SIDEBAR ====================

with st.sidebar:
    st.markdown("## Portfoyum")
    st.markdown("---")

    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = []
    if 'selected_categories' not in st.session_state:
        st.session_state.selected_categories = []
    if 'scan_results' not in st.session_state:
        st.session_state.scan_results = []
    if 'last_scan' not in st.session_state:
        st.session_state.last_scan = None

    # === OTOMATIK TARAMA ===
    st.markdown("### 🔍 Otomatik Tarama")
    st.markdown("*Kategori secin, vade secin, AL verenleri bulun*")

    scan_category_selected = st.selectbox("Kategori Secin", list(ALL_ASSETS.keys()), key="scan_cat")
    scan_timeframe = st.radio("Vade Secin", list(TIMEFRAMES.keys()), key="scan_tf")

    if st.button("🔍 TARA - AL Sinyali Verenleri Bul", key="scan_btn"):
        with st.spinner("Taraniyor... Bu biraz zaman alabilir"):
            results = scan_category(scan_category_selected, scan_timeframe)
            st.session_state.scan_results = results
            st.session_state.last_scan = {
                'category': scan_category_selected,
                'timeframe': scan_timeframe,
                'count': len(results),
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
        if results:
            st.success(str(len(results)) + " adet AL sinyali bulundu!")
        else:
            st.warning("AL sinyali veren hisse bulunamadi.")
        st.rerun()

    if st.session_state.last_scan:
        st.markdown("---")
        st.markdown("**Son Tarama:**")
        st.markdown("Kategori: " + st.session_state.last_scan['category'])
        st.markdown("Vade: " + st.session_state.last_scan['timeframe'])
        st.markdown("AL Sinyali: " + str(st.session_state.last_scan['count']) + " adet")
        st.markdown("Saat: " + st.session_state.last_scan['timestamp'])

    st.markdown("---")

    # === MANUEL SECIM ===
    st.markdown("### 📁 Kategoriler (Manuel)")
    for category in ALL_ASSETS.keys():
        is_selected = st.checkbox(category, value=(category in st.session_state.selected_categories), key="cat_" + category)
        if is_selected and category not in st.session_state.selected_categories:
            st.session_state.selected_categories.append(category)
        elif not is_selected and category in st.session_state.selected_categories:
            st.session_state.selected_categories.remove(category)

    if st.session_state.selected_categories:
        st.markdown("---")
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

st.markdown("# Yatirim AI Agent - Otomatik Tarama")
st.markdown("### Kategori secin, vade secin, AL sinyali veren hisseleri gorun")
st.markdown("---")

# === TARAMA SONUCLARI ===
if st.session_state.scan_results:
    st.markdown("## 🔍 Tarama Sonuclari")
    st.markdown("**" + str(len(st.session_state.scan_results)) + " adet AL sinyali bulundu** | Kategori: " + st.session_state.last_scan['category'] + " | Vade: " + st.session_state.last_scan['timeframe'] + " | Saat: " + st.session_state.last_scan['timestamp'])
    st.markdown("---")

    for i, result in enumerate(st.session_state.scan_results):
        with st.container():
            st.markdown("<div class='scan-result'>", unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

            with col1:
                st.markdown("<div class='scan-header'>" + str(i+1) + ". " + result['symbol'] + "</div>", unsafe_allow_html=True)
                st.markdown("*" + result['name'] + "*")
                if result['price']:
                    st.markdown("<div class='price-big'>$" + str(result['price']) + "</div>", unsafe_allow_html=True)

            with col2:
                if result['change']:
                    change_class = "change-pos" if result['change'] >= 0 else "change-neg"
                    change_sign = "+" if result['change'] >= 0 else "-"
                    st.markdown("<div class='" + change_class + "'>" + change_sign + " " + str(abs(result['change'])) + "% (1m)</div>", unsafe_allow_html=True)
                st.markdown("Skor: **" + str(result['score']) + "**")
                st.markdown("RSI: " + str(result['rsi']))

            with col3:
                st.markdown("<div class='buy'>AL SINYALI</div>", unsafe_allow_html=True)
                st.markdown("Vade: " + result['timeframe'])
                if result['reasons']:
                    st.markdown("Nedenler:")
                    for reason in result['reasons']:
                        st.markdown("- " + reason)

            with col4:
                if st.button("Portfoye Ekle", key="add_scan_" + result['symbol']):
                    exists = any(p['symbol'] == result['symbol'] for p in st.session_state.portfolio)
                    if not exists:
                        st.session_state.portfolio.append({'symbol': result['symbol'], 'name': result['name'], 'type': st.session_state.last_scan['category']})
                        st.success(result['symbol'] + " portfoye eklendi!")
                        st.rerun()
                    else:
                        st.warning("Zaten portfoyde var!")

            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")

# === MANUEL PORTFOY ANALIZI ===
if st.session_state.portfolio:
    st.markdown("## 📊 Portfoy Analizi")

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
                'Sinyal': signal['signal'],
                'Skor': signal['score'],
                'RSI': signal['rsi'],
            })

    if table_data:
        df_table = pd.DataFrame(table_data)
        st.dataframe(df_table, use_container_width=True, hide_index=True)

    st.markdown("---")
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

if not st.session_state.portfolio and not st.session_state.scan_results:
    st.info("Sol menuden kategori ve vade secip 'TARA' butonuna basin, AL sinyali veren hisseleri otomatik bulun!")
    st.markdown("**Nasil kullanilir:**  1. **Kategori secin** (BIST, NASDAQ, vb.)  2. **Vade secin** (Kisa/Orta/Uzun)  3. **TARA butonuna basin**  4. AL sinyali veren hisseler otomatik listelenecek")

st.markdown("---")
st.markdown("**Son guncelleme:** " + datetime.now().strftime('%H:%M:%S'))
st.markdown("*Bu uygulama egitim amaclidir. Yatirim tavsiyesi degildir.*")
