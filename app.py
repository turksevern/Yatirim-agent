
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# Sayfa yapılandırması
st.set_page_config(
    page_title="Yatırım AI Agent - Gerçek Zamanlı",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS ile mobil uyumlu tasarım
st.markdown("""
<style>
    .main {padding: 0rem 1rem;}
    .stButton>button {width: 100%; border-radius: 10px; height: 3rem; font-size: 1.1rem;}
    .metric-card {background: #1e1e1e; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;}
    .buy-signal {color: #00ff88; font-weight: bold; font-size: 1.2rem;}
    .sell-signal {color: #ff4444; font-weight: bold; font-size: 1.2rem;}
    .hold-signal {color: #ffaa00; font-weight: bold; font-size: 1.2rem;}
    .price-big {font-size: 2rem; font-weight: bold; color: #ffffff;}
    .change-positive {color: #00ff88; font-size: 1.2rem;}
    .change-negative {color: #ff4444; font-size: 1.2rem;}
    @media (max-width: 768px) {
        .price-big {font-size: 1.5rem;}
        .stButton>button {height: 2.5rem; font-size: 1rem;}
    }
</style>
""", unsafe_allow_html=True)

# ==================== VERI CEKME FONKSIYONLARI ====================

@st.cache_data(ttl=60)
def fetch_price(symbol):
    """Anlık fiyat çek"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="1m")
        if not data.empty:
            last = data.iloc[-1]
            prev = data.iloc[-2] if len(data) > 1 else last
            change = ((last['Close'] - prev['Close']) / prev['Close'] * 100) if prev['Close'] != 0 else 0
            return {
                'price': round(last['Close'], 4),
                'change': round(change, 2),
                'volume': int(last['Volume']),
                'high': round(data['High'].max(), 4),
                'low': round(data['Low'].min(), 4),
                'open': round(data['Open'].iloc[0], 4),
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
    except:
        pass
    return None

@st.cache_data(ttl=300)
def fetch_history(symbol, period="1mo", interval="1d"):
    """Tarihsel veri çek"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        return df
    except:
        return None

def calculate_indicators(df):
    """Teknik göstergeleri hesapla"""
    if df is None or len(df) < 50:
        return df
    df = df.copy()
    df['SMA_20'] = ta.sma(df['Close'], length=20)
    df['SMA_50'] = ta.sma(df['Close'], length=50)
    df['SMA_200'] = ta.sma(df['Close'], length=200)
    df['RSI_14'] = ta.rsi(df['Close'], length=14)
    macd = ta.macd(df['Close'], fast=12, slow=26, signal=9)
    df['MACD'] = macd['MACD_12_26_9']
    df['MACD_Signal'] = macd['MACDs_12_26_9']
    bbands = ta.bbands(df['Close'], length=20, std=2)
    df['BB_Upper'] = bbands['BBU_20_2.0']
    df['BB_Lower'] = bbands['BBL_20_2.0']
    df['ATR_14'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    return df

def generate_signal(df, symbol, asset_type):
    """Sinyal üret"""
    if df is None or len(df) < 50:
        return {'signal': 'BEKLE', 'score': 0, 'reason': 'Yetersiz veri'}

    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last

    score = 0
    reasons = []

    # RSI
    rsi = last['RSI_14'] if 'RSI_14' in last and not pd.isna(last['RSI_14']) else 50
    if rsi < 30:
        score += 25
        reasons.append("RSI aşırı satım (" + str(round(rsi, 1)) + ")")
    elif rsi > 70:
        score -= 25
        reasons.append("RSI aşırı alım (" + str(round(rsi, 1)) + ")")

    # MACD
    if 'MACD' in last and 'MACD_Signal' in last:
        if last['MACD'] > last['MACD_Signal'] and prev['MACD'] <= prev['MACD_Signal']:
            score += 25
            reasons.append("MACD bullish crossover")
        elif last['MACD'] < last['MACD_Signal'] and prev['MACD'] >= prev['MACD_Signal']:
            score -= 25
            reasons.append("MACD bearish crossover")
        elif last['MACD'] > last['MACD_Signal']:
            score += 10
        else:
            score -= 10

    # Trend
    if 'SMA_50' in last and 'SMA_200' in last:
        if not pd.isna(last['SMA_50']) and not pd.isna(last['SMA_200']):
            if last['SMA_50'] > last['SMA_200']:
                score += 15
                reasons.append("Golden Cross (SMA50 > SMA200)")
            else:
                score -= 15
                reasons.append("Death Cross (SMA50 < SMA200)")

    # Bollinger
    if 'BB_Upper' in last and 'BB_Lower' in last:
        if last['Close'] < last['BB_Lower']:
            score += 15
            reasons.append("Fiyat BB alt bandında")
        elif last['Close'] > last['BB_Upper']:
            score -= 15
            reasons.append("Fiyat BB üst bandında")

    # ATR bazlı stop-loss
    atr = last['ATR_14'] if 'ATR_14' in last and not pd.isna(last['ATR_14']) else 0
    current_price = last['Close']

    if score > 20:
        signal = 'AL'
        stop_loss = round(current_price - (atr * 2), 2) if atr > 0 else None
        take_profit = round(current_price + (atr * 3), 2) if atr > 0 else None
    elif score < -20:
        signal = 'SAT'
        stop_loss = round(current_price + (atr * 2), 2) if atr > 0 else None
        take_profit = round(current_price - (atr * 3), 2) if atr > 0 else None
    else:
        signal = 'BEKLE'
        stop_loss = None
        take_profit = None

    return {
        'signal': signal,
        'score': score,
        'reasons': reasons,
        'rsi': round(rsi, 1),
        'atr': round(atr, 4),
        'stop_loss': stop_loss,
        'take_profit': take_profit,
        'sma_50': round(last['SMA_50'], 2) if 'SMA_50' in last and not pd.isna(last['SMA_50']) else None,
        'sma_200': round(last['SMA_200'], 2) if 'SMA_200' in last and not pd.isna(last['SMA_200']) else None
    }

# ==================== STREAMLIT ARAYUZ ====================

def main():
    # Sidebar - Portföy Yönetimi
    with st.sidebar:
        st.markdown("## 📊 Portföyüm")
        st.markdown("---")

        # Varsayılan varlıklar
        if 'portfolio' not in st.session_state:
            st.session_state.portfolio = [
                {'symbol': 'XU100.IS', 'type': 'BIST', 'name': 'BIST 100'},
                {'symbol': 'THYAO.IS', 'type': 'BIST', 'name': 'THY'},
                {'symbol': 'GARAN.IS', 'type': 'BIST', 'name': 'Garanti'},
                {'symbol': 'SPY', 'type': 'US', 'name': 'S&P 500'},
                {'symbol': 'QQQ', 'type': 'US', 'name': 'Nasdaq 100'},
                {'symbol': 'AAPL', 'type': 'US', 'name': 'Apple'},
                {'symbol': 'NVDA', 'type': 'US', 'name': 'NVIDIA'},
                {'symbol': 'TSLA', 'type': 'US', 'name': 'Tesla'},
                {'symbol': 'META', 'type': 'US', 'name': 'Meta'},
                {'symbol': 'AMD', 'type': 'US', 'name': 'AMD'},
                {'symbol': 'COIN', 'type': 'US', 'name': 'Coinbase'},
                {'symbol': 'PLTR', 'type': 'US', 'name': 'Palantir'},
                {'symbol': 'ARKK', 'type': 'US', 'name': 'ARKK'},
                {'symbol': 'GC=F', 'type': 'Emtia', 'name': 'Altın'},
                {'symbol': 'SI=F', 'type': 'Emtia', 'name': 'Gümüş'},
                {'symbol': 'BTC-USD', 'type': 'Kripto', 'name': 'Bitcoin'},
                {'symbol': 'ETH-USD', 'type': 'Kripto', 'name': 'Ethereum'},
                {'symbol': 'SOL-USD', 'type': 'Kripto', 'name': 'Solana'},
            ]

        # Yeni varlık ekle
        st.markdown("### ➕ Varlık Ekle")
        new_symbol = st.text_input("Sembol", placeholder="örn: MSFT", key="new_sym").upper().strip()
        new_name = st.text_input("İsim (opsiyonel)", placeholder="örn: Microsoft", key="new_name")
        new_type = st.selectbox("Tür", ['BIST', 'US', 'Emtia', 'Kripto', 'Fon'], key="new_type")

        if st.button("✅ Ekle", key="add_btn"):
            if new_symbol:
                exists = any(a['symbol'] == new_symbol for a in st.session_state.portfolio)
                if not exists:
                    st.session_state.portfolio.append({
                        'symbol': new_symbol,
                        'type': new_type,
                        'name': new_name if new_name else new_symbol
                    })
                    st.success(new_symbol + " eklendi!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.warning("Bu sembol zaten var!")

        st.markdown("---")

        # Varlık listesi
        st.markdown("### 📋 Varlıklarım")
        for i, asset in enumerate(st.session_state.portfolio):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("**" + asset['symbol'] + "**  " + asset['name'])
            with col2:
                if st.button("🗑️", key="del_" + str(i)):
                    st.session_state.portfolio.pop(i)
                    st.rerun()

        st.markdown("---")

        # Yenile butonu
        if st.button("🔄 Tümünü Yenile", key="refresh_all"):
            st.cache_data.clear()
            st.rerun()

        # Otomatik yenileme
        auto_refresh = st.checkbox("⏱️ Otomatik yenileme (60s)", value=False)
        if auto_refresh:
            st.markdown("<meta http-equiv="refresh" content="60">", unsafe_allow_html=True)

    # Ana ekran
    st.markdown("# 📈 Yatırım AI Agent - Gerçek Zamanlı")
    st.markdown("### Teknik Analiz + Al/Sat Sinyalleri")
    st.markdown("---")

    # Portföy özet kartları
    st.markdown("## 📊 Portföy Özeti")

    # Tüm varlıkların fiyatlarını çek
    price_data = {}
    signal_data = {}

    progress_bar = st.progress(0)
    total = len(st.session_state.portfolio)

    for i, asset in enumerate(st.session_state.portfolio):
        progress_bar.progress((i + 1) / total)

        # Anlık fiyat
        price_info = fetch_price(asset['symbol'])
        price_data[asset['symbol']] = price_info

        # Tarihsel veri ve sinyal
        df = fetch_history(asset['symbol'], period="6mo", interval="1d")
        df = calculate_indicators(df)
        signal = generate_signal(df, asset['symbol'], asset['type'])
        signal_data[asset['symbol']] = signal

    progress_bar.empty()

    # Özet metrikler
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        buy_count = sum(1 for s in signal_data.values() if s['signal'] == 'AL')
        st.metric("🟢 AL Sinyali", buy_count)
    with col2:
        sell_count = sum(1 for s in signal_data.values() if s['signal'] == 'SAT')
        st.metric("🔴 SAT Sinyali", sell_count)
    with col3:
        hold_count = sum(1 for s in signal_data.values() if s['signal'] == 'BEKLE')
        st.metric("🟡 BEKLE", hold_count)
    with col4:
        total_assets = len(st.session_state.portfolio)
        st.metric("📊 Toplam Varlık", total_assets)

    st.markdown("---")

    # Detaylı kartlar
    st.markdown("## 📋 Detaylı Analiz")

    for asset in st.session_state.portfolio:
        symbol = asset['symbol']
        price_info = price_data.get(symbol)
        signal = signal_data.get(symbol, {'signal': 'BEKLE', 'score': 0, 'reasons': []})

        with st.container():
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)

            # Üst satır: Sembol + Fiyat + Sinyal
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

            with col1:
                st.markdown("**" + symbol + "**")
                st.markdown("*" + asset['name'] + "*  " + asset['type'])

            with col2:
                if price_info:
                    price = price_info['price']
                    change = price_info['change']
                    change_class = "change-positive" if change >= 0 else "change-negative"
                    change_icon = "▲" if change >= 0 else "▼"
                    st.markdown("<div class='price-big'>$" + str(price) + "</div>", unsafe_allow_html=True)
                    st.markdown("<div class='" + change_class + "'>" + change_icon + " " + str(change) + "%</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='price-big'>-</div>", unsafe_allow_html=True)

            with col3:
                sig = signal['signal']
                if sig == 'AL':
                    st.markdown("<div class='buy-signal'>🟢 AL</div>", unsafe_allow_html=True)
                elif sig == 'SAT':
                    st.markdown("<div class='sell-signal'>🔴 SAT</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='hold-signal'>🟡 BEKLE</div>", unsafe_allow_html=True)
                st.markdown("Skor: " + str(signal['score']))

            with col4:
                if signal['stop_loss'] and signal['take_profit']:
                    st.markdown("🛡️ SL: $" + str(signal['stop_loss']))
                    st.markdown("🎯 TP: $" + str(signal['take_profit']))
                if signal['rsi']:
                    st.markdown("RSI: " + str(signal['rsi']))

            # Nedenler
            if signal['reasons']:
                st.markdown("**Nedenler:** " + " | ".join(signal['reasons']))

            # Grafik
            df = fetch_history(symbol, period="3mo", interval="1d")
            if df is not None and not df.empty:
                df = calculate_indicators(df)

                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                   vertical_spacing=0.03, row_heights=[0.7, 0.3])

                # Mum grafiği
                fig.add_trace(go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name=symbol
                ), row=1, col=1)

                # SMA'lar
                if 'SMA_20' in df.columns:
                    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], 
                                           name='SMA20', line=dict(color='orange', width=1)), row=1, col=1)
                if 'SMA_50' in df.columns:
                    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], 
                                           name='SMA50', line=dict(color='blue', width=1)), row=1, col=1)

                # Hacim
                fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Hacim', 
                                   marker_color='gray', opacity=0.3), row=2, col=1)

                fig.update_layout(
                    title=symbol + " - 3 Aylık Grafik",
                    xaxis_title="Tarih",
                    yaxis_title="Fiyat",
                    height=400,
                    template="plotly_dark",
                    showlegend=True,
                    xaxis_rangeslider_visible=False
                )

                st.plotly_chart(fig, use_container_width=True)

            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")

    # Alt bilgi
    st.markdown("---")
    st.markdown("**⏰ Son güncelleme:** " + datetime.now().strftime('%H:%M:%S'))
    st.markdown("*⚠️ Bu uygulama eğitim amaçlıdır. Yatırım tavsiyesi değildir.*")

if __name__ == "__main__":
    main()
