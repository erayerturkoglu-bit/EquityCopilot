import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google import genai
from google.genai.errors import ServerError, ClientError
import pypdf
import requests
import xml.etree.ElementTree as ET
import urllib.parse
import time
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="EquityCopilot | Buy-Side Terminal", page_icon="🏛️", layout="wide")

# -------------------------------------------------------------
# GLOBAL MULTILINGUAL LOCALIZATION (i18n: EN / TR / CZ)
# -------------------------------------------------------------
TRANSLATIONS = {
    "EN": {
        "title": "🏛️ EquityCopilot: Buy-Side Research & Valuation Terminal",
        "subtitle": "Institutional Equity Intelligence • Real-Time News & Sentiment • Reverse DCF • Valuation Sensitivity • Powered by Gemini",
        "lang_select": "Language / Jazyk / Dil:",
        "terminal_config": "⚙️ Terminal Config",
        "gemini_key": "Gemini API Key",
        "primary_ticker": "Primary Ticker",
        "market_resolved_bist": "📍 Market Resolved: Borsa Istanbul",
        "market_resolved_global": "🌍 Market Resolved: Global / US",
        "peer_config": "Peer Group Configuration",
        "domestic_peers": "Domestic Peers (Same Exchange/Market)",
        "global_peers": "Global Peers (Worldwide Sector Leaders)",
        "upload_pdf": "Filing / 10-K / Transcripts (PDF)",
        "currency_unit": "Currency Display Unit:",
        "price": "Market Price",
        "trailing_pe": "Trailing P/E",
        "ev_ebitda": "EV / EBITDA",
        "gross_margin": "Gross Margin",
        "roe": "Return on Equity (ROE)",
        "tabs": [
            "📈 Price & Technical Structure",
            "📰 Live Intelligence & News Feed",
            "📊 Peer Comps (Domestic vs Global)",
            "📜 Historical Multiples & Ratios",
            "🎯 Reverse DCF & Expectations",
            "🎲 Scenario & Sensitivity Matrix",
            "💰 Dividends & Capital Actions",
            "🌐 Catalysts & Macro Developments",
            "🔬 Fundamental Health & Forensics",
            "🏛️ Material Filings & Disclosures",
            "📑 Disclosure Forensics (PDF)",
            "🐻 Bear-Case Stress Test",
            "📝 1-Click IC Memo & Export"
        ],
        "run_comps": "Run Multi-Tier Valuation Comps",
        "wacc": "Cost of Capital / WACC (%)",
        "term_growth": "Terminal Growth Rate g (%)",
        "horizon": "Forecast Horizon (Years)",
        "implied_growth": "Implied 5-Year FCF Growth CAGR Needed",
        "bear_case": "🐻 Bear Case (Downturn/Compression)",
        "base_case": "🎯 Base Case (Current Trajectory)",
        "bull_case": "🚀 Bull Case (High Velocity Expansion)",
        "gen_memo": "Generate IC One-Pager",
        "download_memo": "📥 Download IC Memo as Printable HTML / PDF",
        "enter_key_warn": "Enter your Gemini API key in the sidebar.",
        "fetch_news_btn": "Refresh Live News & Audit Market Sentiment",
        "news_empty": "No recent news articles detected for this ticker."
    },
    "TR": {
        "title": "🏛️ EquityCopilot: Kurumsal Araştırma ve Değerleme Terminali",
        "subtitle": "Kurumsal Hisse İstihbaratı • Canlı Haber & Piyasa Duyarlılığı • Ters DCF • Değerleme Duyarlılığı • Gemini Destekli",
        "lang_select": "Dil / Language / Jazyk:",
        "terminal_config": "⚙️ Terminal Ayarları",
        "gemini_key": "Gemini API Anahtarı",
        "primary_ticker": "Analiz Edilecek Hisse",
        "market_resolved_bist": "📍 Piyasa Eşleşti: Borsa İstanbul",
        "market_resolved_global": "🌍 Piyasa Eşleşti: Küresel / ABD",
        "peer_config": "Sektörel Akran Yapılandırması",
        "domestic_peers": "Yerel Akranlar (Aynı Borsa / Pazar)",
        "global_peers": "Küresel Akranlar (Dünya Liderleri)",
        "upload_pdf": "Faaliyet Raporu / Sunum / Finansal Tablo (PDF)",
        "currency_unit": "Para Birimi Göstergesi:",
        "price": "Piyasa Fiyatı",
        "trailing_pe": "F/K Çarpanı",
        "ev_ebitda": "FD / FAVÖK",
        "gross_margin": "Brüt Kâr Marjı",
        "roe": "Özkaynak Kârlılığı (ROE)",
        "tabs": [
            "📈 Fiyat & Teknik Yapı",
            "📰 Canlı Haber & Piyasa Algısı",
            "📊 Akran Karşılaştırması (Yerel & Küresel)",
            "📜 Tarihsel Çarpanlar & Rasyolar",
            "🎯 Ters DCF & Piyasa Beklentileri",
            "🎲 Senaryo & Duyarlılık Matrisi",
            "💰 Temettü & Sermaye Hareketleri",
            "🌐 Katalizör & Makro Gelişmeler",
            "🔬 Temel Sağlık & Adli Muhasebe",
            "🏛️ Maddi Bildirimler (KAP / SEC)",
            "📑 Rapor Adli İnceleme (PDF)",
            "🐻 Ayı Senaryosu Stres Testi",
            "📝 1-Tıkla Yatırım Komitesi Notu"
        ],
        "run_comps": "Çok Katmanlı Akran Analizini Çalıştır",
        "wacc": "Sermaye Maliyeti / WACC (%)",
        "term_growth": "Terminal Büyüme Oranı g (%)",
        "horizon": "Tahmin Ufku (Yıl)",
        "implied_growth": "Fiyatın İma Ettiği 5 Yıllık FCF Büyüme Hızı (CAGR)",
        "bear_case": "🐻 Kötü Senaryo (Daralma / Baskı)",
        "base_case": "🎯 Baz Senaryo (Mevcut Trend)",
        "bull_case": "🚀 İyimser Senaryo (Yüksek Büyüme)",
        "gen_memo": "Yatırım Komitesi Notu Üret",
        "download_memo": "📥 Yatırım Komitesi Notunu İndir (HTML / PDF)",
        "enter_key_warn": "Yan panelden Gemini API anahtarınızı girin.",
        "fetch_news_btn": "Canlı Haberleri Tara & Piyasa Algısını Değerlendir",
        "news_empty": "Bu hisse için yakın tarihli haber bulunamadı."
    },
    "CZ": {
        "title": "🏛️ EquityCopilot: Výzkumný a Valuační Buy-Side Terminál",
        "subtitle": "Institucionální analýza akcií • Zprávy & Tržní Sentiment • Reverzní DCF • Matice citlivosti • Poháněno Gemini",
        "lang_select": "Jazyk / Language / Dil:",
        "terminal_config": "⚙️ Konfigurace Terminálu",
        "gemini_key": "Gemini API Klíč",
        "primary_ticker": "Primární Ticker",
        "market_resolved_bist": "📍 Trh identifikován: Borsa Istanbul",
        "market_resolved_global": "🌍 Trh identifikován: Globální / USA",
        "peer_config": "Konfigurace Skupiny Konkurentů",
        "domestic_peers": "Domácí Konkurenti (Stejná burza)",
        "global_peers": "Globální Konkurenti (Světoví lídři)",
        "upload_pdf": "Výroční zpráva / Prezentace (PDF)",
        "currency_unit": "Zobrazovaná Měna:",
        "price": "Tržní Cena",
        "trailing_pe": "P/E Poměr",
        "ev_ebitda": "EV / EBITDA",
        "gross_margin": "Hrubá Marže",
        "roe": "Návratnost Vlastního Kapitálu (ROE)",
        "tabs": [
            "📈 Cena & Technická Struktura",
            "📰 Živé Zprávy & Tržní Sentiment",
            "📊 Porovnání Konkurentů (Domácí vs Globální)",
            "📜 Historické Násobky & Poměrové Ukazatele",
            "🎯 Reverzní DCF & Tržní Očekávání",
            "🎲 Matice Scénářů a Citlivosti",
            "💰 Dividendy & Kapitálové Operace",
            "🌐 Katalyzátory & Makro Vývoj",
            "🔬 Fundamentální Zdraví & Forenzní Analýza",
            "🏛️ Regulatorní Zprávy (KAP / SEC)",
            "📑 Forenzní Analýza Zpráv (PDF)",
            "🐻 Zátěžový Test (Medvědí Scénář)",
            "📝 1-Klik Generátor Zprávy pro Investiční Výbor"
        ],
        "run_comps": "Spustit Valuační Porovnání",
        "wacc": "Náklady na Kapitál / WACC (%)",
        "term_growth": "Terminální Míra Růstu g (%)",
        "horizon": "Prognózovaný Horizont (Roky)",
        "implied_growth": "Implikovaná 5letá Míra Růstu FCF (CAGR)",
        "bear_case": "🐻 Medvědí Scénář (Pokles / Komprese)",
        "base_case": "🎯 Základní Scénář (Současný Trend)",
        "bull_case": "🚀 Býčí Scénář (Expanze)",
        "gen_memo": "Generovat Zprávu pro Výbor",
        "download_memo": "📥 Stáhnout Zprávu (HTML / PDF)",
        "enter_key_warn": "Zadejte svůj Gemini API klíč v bočním panelu.",
        "fetch_news_btn": "Načíst Aktuální Zprávy & Analyzovat Sentiment",
        "news_empty": "Nebyly nalezeny žádné aktuální zprávy pro tento ticker."
    }
}

# -------------------------------------------------------------
# TOP BAR: LANGUAGE SELECTOR & HEADER
# -------------------------------------------------------------
col_h_left, col_h_right = st.columns([4, 1])

with col_h_right:
    selected_lang = st.radio(
        "🌐 Language / Dil / Jazyk",
        ["EN", "TR", "CZ"],
        horizontal=True,
        index=0,
        label_visibility="collapsed"
    )

T = TRANSLATIONS[selected_lang]

with col_h_left:
    st.title(T["title"])
    st.caption(T["subtitle"])

# Known BIST Symbol Registry
KNOWN_BIST_SYMBOLS = {
    "ASELS", "THYAO", "TUPRS", "GARAN", "AKBNK", "YKBNK", "ISCTR", "KCHOL", "SAHOL",
    "EREGL", "KRDMD", "SISE", "BIMAS", "FROTO", "TOASO", "ARCLK", "TCELL", "TTKOM",
    "PETKM", "KOZAL", "KOZAA", "IPEKE", "PGSUS", "TAVHL", "ENKAI", "OYAKC", "HEKTS",
    "GUBRF", "VESTL", "VESBE", "SASA", "ALARK", "EKGYO", "SOKM", "MGROS", "MAVI",
    "OTKAR", "SDTTR", "PAPIL", "CANTE", "ASTOR", "KONTR", "SMRTG", "EUPWR", "CWENE",
    "MIATK", "REEDR", "TABGD", "CIMSA", "AKSEN", "ODAS", "ISMEN", "BRSAN", "DOAS"
}

# Sidebar
with st.sidebar:
    st.header(T["terminal_config"])
    default_key = st.secrets.get("GEMINI_API_KEY", "")
    api_key = st.text_input(T["gemini_key"], value=default_key, type="password")
    
    raw_user_input = st.text_input(T["primary_ticker"], value="asels").strip()
    
    def resolve_ticker(input_sym: str):
        clean = input_sym.upper().strip()
        if not clean:
            return "ASELS.IS", "ASELS", True
        if "." in clean:
            base = clean.split(".")[0]
            is_bist = clean.endswith(".IS")
            return clean, base, is_bist
        if clean in KNOWN_BIST_SYMBOLS:
            return f"{clean}.IS", clean, True
        return clean, clean, False

    resolved_yf_ticker, clean_symbol, is_bist_ticker = resolve_ticker(raw_user_input)
    
    if is_bist_ticker:
        st.caption(f"{T['market_resolved_bist']} (`{resolved_yf_ticker}`)")
    else:
        st.caption(f"{T['market_resolved_global']} (`{resolved_yf_ticker}`)")

    curated_peers = {
        "NVDA": {"domestic": "AMD, INTC, AVGO, QCOM", "global": "TSM, ASML, 005930.KS"},
        "ASELS": {"domestic": "OTKAR, SDTTR, PAPIL", "global": "LMT, RTX, RHM.DE, BA.L"},
        "THYAO": {"domestic": "PGSUS, TAVHL", "global": "LHA.DE, AF.PA, DAL, UAL"},
        "TUPRS": {"domestic": "PETKM, AYGAZ", "global": "NESTE.HE, VLO, MPC, REP.MC"},
        "AAPL": {"domestic": "MSFT, GOOGL, AMZN, META", "global": "005930.KS, 6758.T"},
        "GARAN": {"domestic": "AKBNK, YKBNK, ISCTR", "global": "JPM, BAC, SAN, BBVA"}
    }
    
    peer_info = curated_peers.get(clean_symbol, curated_peers.get(resolved_yf_ticker, {}))
    default_domestic = peer_info.get("domestic", "OTKAR, SDTTR" if is_bist_ticker else "AMD, INTC")
    default_global = peer_info.get("global", "LMT, RTX, RHM.DE" if is_bist_ticker else "TSM, ASML")
    
    st.markdown("---")
    st.subheader(T["peer_config"])
    domestic_input = st.text_input(T["domestic_peers"], value=default_domestic)
    global_input = st.text_input(T["global_peers"], value=default_global)
    
    st.markdown("---")
    uploaded_pdf = st.file_uploader(T["upload_pdf"], type=["pdf"])

active_api_key = api_key.strip() if api_key else st.secrets.get("GEMINI_API_KEY", "").strip()

client = genai.Client(api_key=active_api_key) if active_api_key else None

# Resilient Generation Helper with gemini-3.6-flash
def generate_content_resilient(client, prompt, target_lang="EN"):
    candidate_models = ["gemini-3.6-flash"]
    last_err = None
    
    lang_instructions = {
        "EN": "CRITICAL LANGUAGE DIRECTIVE: The entire response MUST be written strictly in professional, institutional English. Use Wall Street / London equity research terminology.",
        "TR": "KRİTİK DİL TALİMATI: Tüm yanıt kesinlikle kurumsal ve profesyonel Türkçe ile yazılmalıdır. Yatırım bankacılığı ve hisse senedi araştırma terminolojisine sadık kalın.",
        "CZ": "KRITICKÝ JAZYKOVÝ POKYN: Celá odpověď MUSÍ být napsána v profesionální, institucionální češtině s použitím přesné finanční a investiční terminologie pro akciový výzkum."
    }
    
    final_prompt = prompt + f"\n\n{lang_instructions.get(target_lang, lang_instructions['EN'])}\n"
    
    for model_name in candidate_models:
        for attempt in range(3):
            try:
                res = client.models.generate_content(model=model_name, contents=final_prompt)
                return res.text
            except ServerError:
                time.sleep(1.5 * (attempt + 1))
            except ClientError as ce:
                last_err = ce
                break
            except Exception as e:
                last_err = e
                break
                
    st.error(f"Gemini API error: {last_err}")
    return None

# FX Rate Helper
@st.cache_data(ttl=600)
def get_fx_conversion_factor(base_currency, target_currency):
    if not base_currency or base_currency == target_currency or target_currency == "Local":
        return 1.0, base_currency
    pair = f"{base_currency}{target_currency}=X"
    inv_pair = f"{target_currency}{base_currency}=X"
    try:
        data = yf.Ticker(pair).history(period="1d")
        if not data.empty:
            return float(data['Close'].iloc[-1]), target_currency
    except Exception:
        pass
    try:
        inv_data = yf.Ticker(inv_pair).history(period="1d")
        if not inv_data.empty:
            return 1.0 / float(inv_data['Close'].iloc[-1]), target_currency
    except Exception:
        pass
    return 1.0, base_currency

def format_timestamp_date(val):
    if not val or val == "N/A":
        return "N/A"
    try:
        if isinstance(val, (int, float)):
            return datetime.fromtimestamp(val).strftime("%Y-%m-%d")
        return pd.to_datetime(val).strftime("%Y-%m-%d")
    except Exception:
        return str(val)

# Dual-Source Automated News Fetcher
@st.cache_data(ttl=900)
def fetch_ticker_news_feed(symbol: str, is_bist: bool):
    news_items = []
    
    if is_bist:
        try:
            q = urllib.parse.quote(f"{symbol} hisse borsa")
            rss_url = f"https://news.google.com/rss/search?q={q}&hl=tr&gl=TR&ceid=TR:tr"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(rss_url, headers=headers, timeout=8)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall('./channel/item')[:10]:
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    pub_elem = item.find('pubDate')
                    source_elem = item.find('source')
                    
                    title = title_elem.text if title_elem is not None else ""
                    link = link_elem.text if link_elem is not None else "#"
                    pub = pub_elem.text[:16] if pub_elem is not None else "Recent"
                    source = source_elem.text if source_elem is not None else "Market Wire"
                    
                    if title:
                        news_items.append({
                            "title": title,
                            "link": link,
                            "published": pub,
                            "source": source
                        })
        except Exception:
            pass
    
    if not news_items:
        try:
            raw_yf = yf.Ticker(symbol).news
            if raw_yf and isinstance(raw_yf, list):
                for item in raw_yf[:10]:
                    content = item.get('content', item)
                    t = content.get('title', '')
                    l = content.get('canonicalUrl', {}).get('url', content.get('link', '#'))
                    p = content.get('pubDate', '')[:16]
                    s = content.get('provider', {}).get('displayName', 'Global Financial Wire')
                    if t:
                        news_items.append({
                            "title": t,
                            "link": l,
                            "published": p if p else "Recent",
                            "source": s
                        })
        except Exception:
            pass
            
    return news_items

# Data Fetching Layer (Market Data)
ticker_input = resolved_yf_ticker

if ticker_input:
    stock = yf.Ticker(ticker_input)
    try:
        info = stock.info
        hist = stock.history(period="1y")
        base_curr = info.get('currency', 'TRY' if is_bist_ticker else 'USD')
        
        curr_col1, curr_col2 = st.columns([1, 4])
        with curr_col1:
            selected_curr = st.radio(
                T["currency_unit"],
                ["Local", "USD", "EUR"],
                horizontal=True
            )
            
        fx_factor, display_curr = get_fx_conversion_factor(base_curr, selected_curr)
        raw_price = info.get('currentPrice', info.get('regularMarketPrice', np.nan))
        conv_price = raw_price * fx_factor if pd.notnull(raw_price) else np.nan
        
        # KPI Ribbon
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        pe_ratio = info.get('trailingPE', 'N/A')
        ev_ebitda = info.get('enterpriseToEbitda', 'N/A')
        gross_margin = f"{round(info.get('grossMargins', 0)*100, 2)}%" if info.get('grossMargins') else 'N/A'
        roe = f"{round(info.get('returnOnEquity', 0)*100, 2)}%" if info.get('returnOnEquity') else 'N/A'
        
        kpi1.metric(T["price"], f"{round(conv_price, 2) if pd.notnull(conv_price) else 'N/A'} {display_curr}")
        kpi2.metric(T["trailing_pe"], f"{pe_ratio}")
        kpi3.metric(T["ev_ebitda"], f"{ev_ebitda}")
        kpi4.metric(T["gross_margin"], gross_margin)
        kpi5.metric(T["roe"], roe)
        
    except Exception:
        st.error(f"Failed to retrieve ticker metadata for {ticker_input}.")

# Dynamic Tabs Assignment
tabs = st.tabs(T["tabs"])
tab_overview, tab_news, tab_comps, tab_ratios, tab_valuation, tab_sensitivity, tab_dividends, tab_catalysts, tab_forensics, tab_regulatory, tab_filing, tab_redteam, tab_memo = tabs

# TAB 1: Charting & Momentum
with tab_overview:
    st.subheader(f"1-Year Price Momentum & Volume ({display_curr})")
    if not hist.empty:
        adj_hist = hist.copy()
        adj_hist['Open'] *= fx_factor
        adj_hist['High'] *= fx_factor
        adj_hist['Low'] *= fx_factor
        adj_hist['Close'] *= fx_factor
        
        adj_hist['SMA50'] = adj_hist['Close'].rolling(window=50).mean()
        adj_hist['SMA200'] = adj_hist['Close'].rolling(window=200).mean()
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.75, 0.25])
        fig.add_trace(go.Candlestick(
            x=adj_hist.index, open=adj_hist['Open'], high=adj_hist['High'],
            low=adj_hist['Low'], close=adj_hist['Close'], name=f'Price ({display_curr})'
        ), row=1, col=1)
        fig.add_trace(go.Scatter(x=adj_hist.index, y=adj_hist['SMA50'], line=dict(color='orange', width=1.5), name='50 SMA'), row=1, col=1)
        fig.add_trace(go.Scatter(x=adj_hist.index, y=adj_hist['SMA200'], line=dict(color='blue', width=1.5), name='200 SMA'), row=1, col=1)
        fig.add_trace(go.Bar(x=adj_hist.index, y=adj_hist['Volume'], name='Volume', marker_color='dimgray'), row=2, col=1)
        
        dt_all = pd.date_range(start=adj_hist.index[0], end=adj_hist.index[-1], freq='D')
        dt_obs = [d.strftime("%Y-%m-%d") for d in adj_hist.index]
        holidays = [d.strftime("%Y-%m-%d") for d in dt_all if d.strftime("%Y-%m-%d") not in dt_obs]
        
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"]), dict(values=holidays)])
        fig.update_layout(height=540, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False, template="plotly_white", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Price history not available.")

# TAB 2: Live Intelligence & Automated News Feed
with tab_news:
    st.subheader(f"📰 Automated News Wire & Market Sentiment: {clean_symbol}")
    st.caption("Live financial news wire integration with buy-side sentiment scoring and market impact forensics.")
    
    col_nw1, col_nw2 = st.columns([1, 2])
    with col_nw1:
        run_news_scan = st.button(T["fetch_news_btn"])
        
    news_feed = fetch_ticker_news_feed(clean_symbol if is_bist_ticker else ticker_input, is_bist=is_bist_ticker)
    
    if news_feed:
        st.markdown("##### 📡 Real-Time Wire Feed")
        for item in news_feed[:6]:
            st.markdown(f"""
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-left: 3px solid #0284c7; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; font-size: 11px; color: #64748b;">
                    <span><strong>{item['source']}</strong></span>
                    <span>{item['published']}</span>
                </div>
                <div style="font-size: 13px; font-weight: 600; color: #0f172a; margin-top: 4px;">
                    <a href="{item['link']}" target="_blank" style="text-decoration: none; color: #0f172a;">{item['title']}</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        if client and run_news_scan:
            with st.spinner(f"Synthesizing market pulse and sentiment for {clean_symbol}..."):
                news_blob = "\n".join([f"- [{n['source']} | {n['published']}] {n['title']}" for n in news_feed])
                
                pulse_prompt = f"""
                You are a Managing Director of Buy-Side Trading & Equity Intelligence.
                Analyze the following recent news wire flow for {clean_symbol} ({ticker_input}):
                
                {news_blob}
                
                Deliver a crisp, highly structured institutional sentiment memo:
                
                1. COMPOSITE SENTIMENT PULSE:
                   - Provide an explicit Sentiment Score from -100 (Extremely Bearish) to +100 (Extremely Bullish).
                   - One-sentence executive verdict on what the market is currently pricing in.
                
                2. PRIMARY VALUE DRIVERS & CATALYSTS IN THE NEWS:
                   - Categorize events into (Revenue/Backlog, Margins, Regulatory/Legal, M&A, FX).
                   - Distinguish between meaningful structural developments vs. routine market noise.
                
                3. IMMEDIATE TRADING / VALUATION IMPLICATION:
                   - Will this flow drive near-term multiple expansion, multiple derating, or neutral drift?
                
                No fluff. Professional institutional formatting.
                """
                sentiment_analysis = generate_content_resilient(client, pulse_prompt, target_lang=selected_lang)
                if sentiment_analysis:
                    st.markdown("---")
                    st.markdown(sentiment_analysis)
        elif not client and run_news_scan:
            st.warning(T["enter_key_warn"])
    else:
        st.info(T["news_empty"])

# Helper for Comps Table Extraction with Auto-Suffix Normalization
def build_comps_dataframe(ticker_list, include_exchange_info=False, auto_is=False):
    comps_data = []
    for t in ticker_list:
        clean_t = t.strip().upper()
        if not clean_t:
            continue
        eval_ticker = f"{clean_t}.IS" if (auto_is and "." not in clean_t and clean_t in KNOWN_BIST_SYMBOLS) else clean_t
        try:
            s_info = yf.Ticker(eval_ticker).info
            row = {
                "Ticker": eval_ticker,
                "Company": s_info.get("shortName", s_info.get("longName", "N/A"))[:20],
            }
            if include_exchange_info:
                row["Country"] = s_info.get("country", "N/A")
                row["Exchange"] = s_info.get("exchange", "N/A")
                
            row.update({
                "Market Cap ($B)": round(s_info.get("marketCap", 0) / 1e9, 2) if s_info.get("marketCap") else "N/A",
                "Trailing P/E": round(s_info.get("trailingPE", 0), 2) if s_info.get("trailingPE") else "N/A",
                "Forward P/E": round(s_info.get("forwardPE", 0), 2) if s_info.get("forwardPE") else "N/A",
                "EV/EBITDA": round(s_info.get("enterpriseToEbitda", 0), 2) if s_info.get("enterpriseToEbitda") else "N/A",
                "Gross Margin (%)": f"{round(s_info.get('grossMargins', 0)*100, 2)}%" if s_info.get("grossMargins") else "N/A",
                "Operating Margin (%)": f"{round(s_info.get('operatingMargins', 0)*100, 2)}%" if s_info.get("operatingMargins") else "N/A",
                "ROE (%)": f"{round(s_info.get('returnOnEquity', 0)*100, 2)}%" if s_info.get("returnOnEquity") else "N/A"
            })
            comps_data.append(row)
        except Exception:
            pass
    return pd.DataFrame(comps_data)

# TAB 3: Domestic vs Global Peer Comps
with tab_comps:
    st.subheader(f"Relative Valuation Matrix: {clean_symbol}")
    dom_peers = [p.strip() for p in domestic_input.split(",") if p.strip()]
    glob_peers = [p.strip() for p in global_input.split(",") if p.strip()]
    
    if st.button(T["run_comps"]):
        with st.spinner("Fetching comparative fundamentals..."):
            dom_tickers = [ticker_input] + dom_peers
            df_dom = build_comps_dataframe(dom_tickers, include_exchange_info=False, auto_is=is_bist_ticker)
            
            glob_tickers = [ticker_input] + glob_peers
            df_glob = build_comps_dataframe(glob_tickers, include_exchange_info=True, auto_is=False)
            
            st.markdown("#### 🏢 Domestic Peers")
            st.dataframe(df_dom, use_container_width=True)
            
            st.markdown("---")
            st.markdown("#### 🌍 Global Industry Peers")
            st.dataframe(df_glob, use_container_width=True)

# TAB 4: Historical Multiples & Financial Ratios Compendium
with tab_ratios:
    st.subheader(f"📜 Multi-Year Historical Financial Ratios & Multiples ({clean_symbol})")
    try:
        bs_hist = stock.balance_sheet
        fin_hist = stock.financials
        cf_hist = stock.cashflow
        
        if not bs_hist.empty and not fin_hist.empty and not cf_hist.empty:
            common_cols = [col for col in fin_hist.columns if col in bs_hist.columns and col in cf_hist.columns]
            common_cols = sorted(common_cols, reverse=True)[:5]
            year_labels = [pd.to_datetime(c).strftime("FY %Y") for c in common_cols]
            
            def safe_div(num, den):
                if pd.notnull(num) and pd.notnull(den) and den != 0:
                    return num / den
                return np.nan

            def fmt_pct(val):
                return f"{round(val * 100, 2)}%" if pd.notnull(val) else "N/A"
            
            def fmt_mult(val):
                return f"{round(val, 2)}x" if pd.notnull(val) else "N/A"
                
            def fmt_days(val):
                return f"{round(val, 1)} d" if pd.notnull(val) else "N/A"

            years_data = {}
            for col in common_cols:
                f_yr = fin_hist[col]
                b_yr = bs_hist[col]
                c_yr = cf_hist[col]
                
                rev = f_yr.get('Total Revenue', np.nan)
                gp = f_yr.get('Gross Profit', np.nan)
                ebit = f_yr.get('Operating Income', f_yr.get('EBIT', np.nan))
                ni = f_yr.get('Net Income', np.nan)
                cogs = f_yr.get('Cost Of Revenue', np.nan)
                interest_exp = f_yr.get('Interest Expense', np.nan)
                
                depr = c_yr.get('Depreciation And Amortization', c_yr.get('Depreciation & Amortization', 0))
                ebitda = (ebit + depr) if (pd.notnull(ebit) and pd.notnull(depr)) else f_yr.get('EBITDA', np.nan)
                
                ta = b_yr.get('Total Assets', np.nan)
                eq = b_yr.get('Stockholders Equity', b_yr.get('Total Equity Gross Minority Interest', np.nan))
                ca = b_yr.get('Current Assets', np.nan)
                cl = b_yr.get('Current Liabilities', np.nan)
                inv = b_yr.get('Inventory', np.nan)
                rec = b_yr.get('Receivables', b_yr.get('Accounts Receivable', np.nan))
                pay = b_yr.get('Payables', b_yr.get('Accounts Payable', np.nan))
                
                tot_debt = b_yr.get('Total Debt', 0)
                cash_equiv = b_yr.get('Cash And Cash Equivalents', b_yr.get('Cash Cash Equivalents And Short Term Investments', 0))
                net_debt = tot_debt - cash_equiv
                
                ocf = c_yr.get('Operating Cash Flow', np.nan)
                capex = c_yr.get('Capital Expenditure', 0)
                fcf = (ocf + capex) if pd.notnull(ocf) and pd.notnull(capex) else np.nan
                
                years_data[col] = {
                    "gross_margin": safe_div(gp, rev),
                    "ebit_margin": safe_div(ebit, rev),
                    "ebitda_margin": safe_div(ebitda, rev),
                    "net_margin": safe_div(ni, rev),
                    "roe": safe_div(ni, eq),
                    "roa": safe_div(ni, ta),
                    "roic": safe_div(ebit * (1 - 0.25), (eq + tot_debt - cash_equiv)) if pd.notnull(ebit) else np.nan,
                    "net_debt_ebitda": safe_div(net_debt, ebitda),
                    "debt_to_equity": safe_div(tot_debt, eq),
                    "financial_leverage": safe_div(ta, eq),
                    "interest_coverage": safe_div(ebit, abs(interest_exp)) if pd.notnull(interest_exp) and interest_exp != 0 else np.nan,
                    "current_ratio": safe_div(ca, cl),
                    "quick_ratio": safe_div(ca - inv if pd.notnull(ca) and pd.notnull(inv) else np.nan, cl),
                    "dso": safe_div(rec, rev) * 365 if pd.notnull(rec) and pd.notnull(rev) else np.nan,
                    "dio": safe_div(inv, cogs) * 365 if pd.notnull(inv) and pd.notnull(cogs) else np.nan,
                    "dpo": safe_div(pay, cogs) * 365 if pd.notnull(pay) and pd.notnull(cogs) else np.nan,
                    "asset_turnover": safe_div(rev, ta),
                    "ocf_to_ni": safe_div(ocf, ni),
                    "fcf_conversion": safe_div(fcf, ebitda),
                }

            ratio_definitions = [
                ("1. PROFITABILITY & RETURNS", "Gross Profit Margin", "gross_margin", fmt_pct),
                ("1. PROFITABILITY & RETURNS", "EBITDA Margin", "ebitda_margin", fmt_pct),
                ("1. PROFITABILITY & RETURNS", "Operating (EBIT) Margin", "ebit_margin", fmt_pct),
                ("1. PROFITABILITY & RETURNS", "Net Profit Margin", "net_margin", fmt_pct),
                ("1. PROFITABILITY & RETURNS", "Return on Equity (ROE)", "roe", fmt_pct),
                ("1. PROFITABILITY & RETURNS", "Return on Assets (ROA)", "roa", fmt_pct),
                ("1. PROFITABILITY & RETURNS", "Return on Invested Capital (ROIC)", "roic", fmt_pct),
                ("2. LEVERAGE & SOLVENCY", "Net Debt / EBITDA", "net_debt_ebitda", fmt_mult),
                ("2. LEVERAGE & SOLVENCY", "Debt-to-Equity (D/E)", "debt_to_equity", fmt_mult),
                ("2. LEVERAGE & SOLVENCY", "Financial Leverage (Assets/Equity)", "financial_leverage", fmt_mult),
                ("2. LEVERAGE & SOLVENCY", "Interest Coverage Ratio", "interest_coverage", fmt_mult),
                ("3. LIQUIDITY & EFFICIENCY", "Current Ratio", "current_ratio", fmt_mult),
                ("3. LIQUIDITY & EFFICIENCY", "Quick Ratio (Acid-Test)", "quick_ratio", fmt_mult),
                ("3. LIQUIDITY & EFFICIENCY", "Days Sales Outstanding (DSO)", "dso", fmt_days),
                ("3. LIQUIDITY & EFFICIENCY", "Days Inventory Outstanding (DIO)", "dio", fmt_days),
                ("3. LIQUIDITY & EFFICIENCY", "Days Payable Outstanding (DPO)", "dpo", fmt_days),
                ("3. LIQUIDITY & EFFICIENCY", "Total Asset Turnover", "asset_turnover", fmt_mult),
                ("4. CASH FLOW QUALITY", "OCF / Net Income Ratio", "ocf_to_ni", fmt_mult),
                ("4. CASH FLOW QUALITY", "FCF / EBITDA Conversion", "fcf_conversion", fmt_pct),
            ]

            table_rows = []
            for category, label, key, formatter in ratio_definitions:
                row = {"Category": category, "Metric / Ratio": label}
                for i, col in enumerate(common_cols):
                    row[year_labels[i]] = formatter(years_data[col][key])
                table_rows.append(row)
                
            df_historical_ratios = pd.DataFrame(table_rows)
            st.dataframe(df_historical_ratios, use_container_width=True, hide_index=True)
        else:
            st.warning("Multi-year financial statements are not fully populated in yfinance.")
    except Exception as e:
        st.error(f"Error compiling historical ratios: {e}")

# TAB 5: Reverse DCF & Expectations Investing
with tab_valuation:
    st.subheader(f"🎯 Reverse DCF & Expectations ({clean_symbol})")
    
    mkt_cap_native = info.get('marketCap', np.nan)
    total_debt_native = info.get('totalDebt', 0)
    total_cash_native = info.get('totalCash', 0)
    net_debt_native = total_debt_native - total_cash_native
    
    cf_data = stock.cashflow
    base_fcf_native = np.nan
    if not cf_data.empty:
        try:
            recent_cf = cf_data.iloc[:, 0]
            ocf = recent_cf.get('Operating Cash Flow', np.nan)
            capex = recent_cf.get('Capital Expenditure', 0)
            if pd.notnull(ocf) and pd.notnull(capex):
                base_fcf_native = ocf + capex
        except Exception:
            pass
            
    if pd.isnull(base_fcf_native) or base_fcf_native <= 0:
        base_fcf_native = max(info.get('operatingCashflow', 1e8) * 0.7, 1e7)
        
    mkt_cap_disp = mkt_cap_native * fx_factor if pd.notnull(mkt_cap_native) else np.nan
    base_fcf_disp = base_fcf_native * fx_factor
    
    col_dcf_p1, col_dcf_p2 = st.columns([1, 2])
    with col_dcf_p1:
        wacc = st.slider(T["wacc"], min_value=7.0, max_value=25.0, value=12.5, step=0.5) / 100.0
        terminal_growth = st.slider(T["term_growth"], min_value=1.0, max_value=8.0, value=3.5, step=0.5) / 100.0
        projection_years = st.slider(T["horizon"], min_value=5, max_value=10, value=5)
        
        st.write(f"**Baseline FCF:** {round(base_fcf_disp / 1e9, 2)}B {display_curr}")
        st.write(f"**Target Market Cap:** {round(mkt_cap_disp / 1e9, 2)}B {display_curr}")

    def calculate_dcf_ev(growth_rate, base_fcf, wacc_val, g_val, n_years):
        pv_fcf = 0.0
        current_fcf = base_fcf
        for yr in range(1, n_years + 1):
            current_fcf *= (1.0 + growth_rate)
            pv_fcf += current_fcf / ((1.0 + wacc_val) ** yr)
        terminal_value = (current_fcf * (1.0 + g_val)) / (wacc_val - g_val) if (wacc_val > g_val) else 0.0
        pv_tv = terminal_value / ((1.0 + wacc_val) ** n_years)
        return pv_fcf + pv_tv

    with col_dcf_p2:
        if wacc <= terminal_growth:
            st.error("WACC must be strictly greater than the Terminal Growth Rate.")
        else:
            target_val = mkt_cap_disp
            low, high = -0.30, 1.00
            implied_growth = None
            for _ in range(50):
                mid = (low + high) / 2.0
                est_val = calculate_dcf_ev(mid, base_fcf_disp, wacc, terminal_growth, projection_years)
                if abs(est_val - target_val) < 1e6:
                    implied_growth = mid
                    break
                elif est_val < target_val:
                    low = mid
                else:
                    high = mid
            implied_growth = mid

            st.metric(
                label=T["implied_growth"],
                value=f"{round(implied_growth * 100, 2)}%"
            )

            years_proj = [f"Yr {i}" for i in range(1, projection_years + 1)]
            projected_fcfs = [base_fcf_disp * ((1.0 + implied_growth) ** i) / 1e9 for i in range(1, projection_years + 1)]
            
            fig_proj = go.Figure()
            fig_proj.add_trace(go.Bar(x=years_proj, y=projected_fcfs, marker_color="#0284c7", name="Implied FCF Path"))
            fig_proj.update_layout(
                title=f"Implied FCF Trajectory ({display_curr} Billions)",
                template="plotly_white",
                height=310,
                margin=dict(l=10, r=10, t=35, b=10)
            )
            st.plotly_chart(fig_proj, use_container_width=True)

# TAB 6: Scenario & Sensitivity Matrix
with tab_sensitivity:
    st.subheader(f"🎲 Scenario & Sensitivity Matrix ({clean_symbol})")
    current_rev_native = info.get('totalRevenue', 1e9)
    current_shares = info.get('sharesOutstanding', 1e8)
    curr_ev_ebitda = info.get('enterpriseToEbitda', 12.0)
    if not curr_ev_ebitda or curr_ev_ebitda <= 0 or curr_ev_ebitda > 50:
        curr_ev_ebitda = 12.0
        
    s_col1, s_col2 = st.columns([1, 2])
    with s_col1:
        base_rev_g = st.slider("Base Revenue Growth Rate (%)", min_value=-30, max_value=50, value=10, step=5) / 100.0
        base_ebitda_m = st.slider("Base EBITDA Margin (%)", min_value=5, max_value=45, value=25, step=1) / 100.0
        target_multiple = st.number_input("Target Exit EV/EBITDA Multiple", value=float(round(curr_ev_ebitda, 1)), step=1.0)
        
    growth_shifts = np.array([-0.10, -0.05, 0.0, 0.05, 0.10]) + base_rev_g
    margin_shifts = np.array([-0.04, -0.02, 0.0, 0.02, 0.04]) + base_ebitda_m
    matrix_prices = np.zeros((len(margin_shifts), len(growth_shifts)))
    
    for i, m in enumerate(margin_shifts):
        for j, g in enumerate(growth_shifts):
            fwd_rev = current_rev_native * (1.0 + g)
            fwd_ebitda = fwd_rev * max(m, 0.01)
            implied_ev = fwd_ebitda * target_multiple
            implied_equity_native = implied_ev - net_debt_native
            implied_share_price_native = max(implied_equity_native / current_shares, 0.0)
            matrix_prices[i, j] = round(implied_share_price_native * fx_factor, 2)
            
    with s_col2:
        x_labels = [f"Rev: {round(g*100, 1)}%" for g in growth_shifts]
        y_labels = [f"Margin: {round(m*100, 1)}%" for m in margin_shifts]
        
        fig_heat = go.Figure(data=go.Heatmap(
            z=matrix_prices, x=x_labels, y=y_labels, text=matrix_prices,
            texttemplate="%{text}", textfont={"size": 13}, colorscale="RdYlGn",
            colorbar=dict(title=f"Price ({display_curr})")
        ))
        fig_heat.update_layout(height=360, template="plotly_white", margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig_heat, use_container_width=True)
        
    st.markdown("---")
    sc1, sc2, sc3 = st.columns(3)
    bear_price = matrix_prices[0, 0]
    base_price = matrix_prices[2, 2]
    bull_price = matrix_prices[-1, -1]
    
    sc1.metric(T["bear_case"], f"{bear_price} {display_curr}", delta=f"{round(((bear_price / conv_price) - 1)*100, 1)}%")
    sc2.metric(T["base_case"], f"{base_price} {display_curr}", delta=f"{round(((base_price / conv_price) - 1)*100, 1)}%")
    sc3.metric(T["bull_case"], f"{bull_price} {display_curr}", delta=f"{round(((bull_price / conv_price) - 1)*100, 1)}%")

# TAB 7: Dividends & Corporate Actions
with tab_dividends:
    st.subheader(f"💰 Dividends & Capital Actions ({clean_symbol})")
    div_yield = info.get("dividendYield")
    payout_ratio = info.get("payoutRatio")
    five_yr_avg_yield = info.get("fiveYearAvgDividendYield")
    raw_last_div = info.get("lastDividendDate")
    
    div_c1, div_c2, div_c3, div_c4 = st.columns(4)
    div_c1.metric("Dividend Yield", f"{round(div_yield * 100, 2)}%" if div_yield else "0.00%")
    div_c2.metric("Payout Ratio", f"{round(payout_ratio * 100, 2)}%" if payout_ratio else "N/A")
    div_c3.metric("5-Yr Avg Yield", f"{round(five_yr_avg_yield, 2)}%" if five_yr_avg_yield else "N/A")
    div_c4.metric("Last Dividend Date", format_timestamp_date(raw_last_div))
    
    st.markdown("---")
    div_series = stock.dividends
    split_series = stock.splits
    col_d1, col_d2 = st.columns(2)
    
    with col_d1:
        st.markdown(f"#### 💵 Cash Dividends ({display_curr})")
        if not div_series.empty:
            dates_clean = [pd.to_datetime(d).strftime("%Y-%m-%d") for d in div_series.index]
            div_values = [val * fx_factor for val in div_series.values]
            df_div = pd.DataFrame({"Payment Date": dates_clean, f"Dividend ({display_curr})": div_values}).sort_values(by="Payment Date", ascending=False)
            st.dataframe(df_div.head(15), use_container_width=True)
        else:
            st.info("No dividend records found.")
            
    with col_d2:
        st.markdown("#### 🍰 Stock Splits & Bonus Issues")
        if not split_series.empty:
            split_dates = [pd.to_datetime(d).strftime("%Y-%m-%d") for d in split_series.index]
            df_split = pd.DataFrame({"Execution Date": split_dates, "Multiplier": split_series.values}).sort_values(by="Execution Date", ascending=False)
            st.dataframe(df_split, use_container_width=True)
        else:
            st.info("No stock splits recorded.")

# TAB 8: Catalysts & Macro Developments
with tab_catalysts:
    st.subheader(f"🌐 Catalysts & Geopolitical Horizon ({clean_symbol})")
    st.markdown(f"""
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #0284c7; border-radius: 8px; padding: 18px 22px; margin-bottom: 22px;">
        <div style="font-size: 11px; font-weight: 700; color: #0284c7; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 12px;">
            Strategic Macro Overview • {clean_symbol}
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
            <div>
                <div style="font-size: 13px; font-weight: 600; color: #0f172a;">🛡️ Sovereign Policy & Market Mandates</div>
                <div style="font-size: 12px; color: #64748b; margin-top: 3px; line-height: 1.4;">
                    Government procurement priorities, system integration roles, and domestic supply quotas.
                </div>
            </div>
            <div>
                <div style="font-size: 13px; font-weight: 600; color: #0f172a;">📈 Budget Trajectory & Industry Outlays</div>
                <div style="font-size: 12px; color: #64748b; margin-top: 3px; line-height: 1.4;">
                    Expanding sovereign/sector allocations, multi-year spending programs, and localization thresholds.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if client and st.button(f"Generate Catalyst Intelligence for {clean_symbol}"):
        with st.spinner("Synthesizing forward-looking catalysts..."):
            cat_prompt = f"Conduct a forward-looking strategic catalyst and macro audit for {clean_symbol} ({ticker_input}). Structure into: 1. OPERATIONAL ROADMAP 2. SOVEREIGN POLICY 3. PLATFORM DRIVERS 4. GEOPOLITICAL MACRO 5. VALUATION RE-RATING VERDICT. Avoid ASCII boxes."
            res = generate_content_resilient(client, cat_prompt, target_lang=selected_lang)
            if res:
                st.markdown(res)
    elif not client:
        st.warning(T["enter_key_warn"])

# TAB 9: Fundamental Health & Forensics
with tab_forensics:
    st.subheader(f"Forensic Accounting & Efficiency ({display_curr})")
    try:
        bs = stock.balance_sheet
        fin = stock.financials
        cf = stock.cashflow
        if not bs.empty and not fin.empty and not cf.empty:
            recent_fin = fin.iloc[:, 0]
            recent_bs = bs.iloc[:, 0]
            recent_cf = cf.iloc[:, 0]
            
            net_income = recent_fin.get('Net Income', np.nan)
            total_rev = recent_fin.get('Total Revenue', np.nan)
            total_assets = recent_bs.get('Total Assets', np.nan)
            total_equity = recent_bs.get('Stockholders Equity', recent_bs.get('Total Equity Gross Minority Interest', np.nan))
            operating_cf = recent_cf.get('Operating Cash Flow', np.nan)
            
            net_margin = (net_income / total_rev) if pd.notnull(net_income) and pd.notnull(total_rev) and total_rev != 0 else np.nan
            asset_turnover = (total_rev / total_assets) if pd.notnull(total_rev) and pd.notnull(total_assets) and total_assets != 0 else np.nan
            equity_multiplier = (total_assets / total_equity) if pd.notnull(total_assets) and pd.notnull(total_equity) and total_equity != 0 else np.nan
            dupont_roe = net_margin * asset_turnover * equity_multiplier if pd.notnull(net_margin) and pd.notnull(asset_turnover) and pd.notnull(equity_multiplier) else np.nan
            
            dp_col1, dp_col2, dp_col3, dp_col4 = st.columns(4)
            dp_col1.metric("Net Profit Margin", f"{round(net_margin * 100, 2)}%" if pd.notnull(net_margin) else "N/A")
            dp_col2.metric("Asset Turnover", f"{round(asset_turnover, 2)}x" if pd.notnull(asset_turnover) else "N/A")
            dp_col3.metric("Equity Multiplier", f"{round(equity_multiplier, 2)}x" if pd.notnull(equity_multiplier) else "N/A")
            dp_col4.metric("Decomposed ROE", f"{round(dupont_roe * 100, 2)}%" if pd.notnull(dupont_roe) else "N/A")
        else:
            st.info("Financial statements not available.")
    except Exception as e:
        st.error(f"Error computing forensics: {e}")
# SEC 8-K Item Code Translator & Retrieval
SEC_ITEM_MAP = {
    "1.01": "Material Definitive Agreement",
    "1.02": "Termination of Material Agreement",
    "2.01": "Acquisition/Disposition of Assets",
    "2.02": "Results of Operations (Earnings)",
    "2.03": "Creation of Direct Financial Obligation",
    "3.02": "Unregistered Equity Sales",
    "4.01": "Changes in Certifying Accountant",
    "5.01": "Changes in Control",
    "5.02": "Departure/Election of Directors or Officers",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Material Events",
    "9.01": "Financial Statements & Exhibits"
}

def decode_sec_items(raw_items_str):
    if not raw_items_str or not isinstance(raw_items_str, str):
        return ""
    codes = [c.strip() for c in raw_items_str.split(",") if c.strip()]
    decoded = [f"{c} ({SEC_ITEM_MAP.get(c, 'Event')})" for c in codes]
    return ", ".join(decoded)

@st.cache_data(ttl=86400)
def load_sec_ticker_map():
    """Fetches official SEC ticker-to-CIK mapping."""
    headers = {"User-Agent": "EquityCopilot erturkoglueray@gmail.com"}
    try:
        resp = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers, timeout=10)
        if resp.status_code == 200:
            raw = resp.json()
            return {v["ticker"].upper(): str(v["cik_str"]).zfill(10) for v in raw.values()}
    except Exception:
        pass
    return {}

@st.cache_data(ttl=1800)
def fetch_sec_recent_filings(ticker_symbol: str, lookback_days: int = 365, forms=("8-K", "10-Q", "10-K")):
    """Pulls real, structured filing metadata directly from SEC EDGAR JSON API."""
    cik_map = load_sec_ticker_map()
    cik = cik_map.get(ticker_symbol.upper())
    if not cik:
        return pd.DataFrame()
    
    headers = {"User-Agent": "EquityCopilot erturkoglueray@gmail.com"}
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return pd.DataFrame()
        
        data = resp.json()
        recent = data.get("filings", {}).get("recent", {})
        cutoff = datetime.now() - timedelta(days=lookback_days)
        items_list = recent.get("items", [""] * len(recent.get("form", [])))
        
        rows = []
        for i in range(len(recent.get("form", []))):
            form = recent["form"][i]
            if form not in forms:
                continue
            filed = recent["filingDate"][i]
            if pd.to_datetime(filed) < cutoff:
                continue
            
            raw_item = items_list[i] if i < len(items_list) else ""
            acc_num = recent["accessionNumber"][i]
            acc_no_dash = acc_num.replace("-", "")
            doc_name = recent["primaryDocument"][i]
            cik_clean = str(int(cik))  # SEC URL'lerinde baştaki sıfırlar olmaz
            doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{acc_no_dash}/{doc_name}"

            rows.append({
                "Date": filed,
                "Form": form,
                "Event / Item": decode_sec_items(raw_item) if form in ("8-K", "6-K") else form,
                "Filing Link": doc_url
            })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()
# Resilient KAP Extraction Function (BIST)
@st.cache_data(ttl=1800)
def fetch_kap_disclosures(clean_code, years_back=3):
    today = datetime.now()
    from_date = today - timedelta(days=365 * years_back)
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.kap.org.tr",
        "Referer": "https://www.kap.org.tr/tr/bildirim-sorgu"
    })
    try:
        session.get("https://www.kap.org.tr/tr/bildirim-sorgu", timeout=8)
    except Exception:
        pass
    url = "https://www.kap.org.tr/tr/api/disclosure/search"
    payload = {"fromDate": from_date.strftime("%Y-%m-%d"), "toDate": today.strftime("%Y-%m-%d"), "stockCodes": [clean_code], "disclosureTypes": ["ODA", "FR", "DG"]}
    try:
        res = session.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list) and len(data) > 0:
                rows = []
                for item in data:
                    rows.append({"Date": item.get("publishDate", "")[:10], "Title": item.get("title", ""), "Category": item.get("disclosureCategory", item.get("summary", "N/A")), "ID": item.get("disclosureId", "")})
                return pd.DataFrame(rows)
    except Exception:
        pass
    return pd.DataFrame()

# TAB 10: Dual-Engine Regulatory Filings
with tab_regulatory:
    if is_bist_ticker:
        st.subheader(f"Deterministic KAP Material Disclosures ({clean_symbol})")
        col_k1, col_k2 = st.columns([1, 2])
        with col_k1:
            years = st.slider("Lookback Window (Years)", min_value=1, max_value=3, value=3)
            load_kap = st.button("Fetch Direct KAP Filings")
        if load_kap:
            with st.spinner("Querying KAP servers..."):
                df_kap = fetch_kap_disclosures(clean_symbol, years_back=years)
                st.session_state['df_kap'] = df_kap
                
        if 'df_kap' in st.session_state:
            df_kap = st.session_state['df_kap']
            if not df_kap.empty:
                st.dataframe(df_kap, use_container_width=True)
                if client and st.button("Analyze KAP Disclosures with Gemini"):
                    with st.spinner("Synthesizing filings..."):
                        p = f"Analyze these KAP disclosures for {clean_symbol}: {df_kap.head(50).to_string()}. Structure: 1. BACKLOG INTAKE 2. CAPEX & CAPACITY 3. REGULATORY RISKS."
                        o = generate_content_resilient(client, p, target_lang=selected_lang)
                        if o: st.markdown(o)
            else:
                st.warning("Direct KAP endpoint query was blocked or returned no records.")
    else:
        st.subheader(f"🏛️ SEC EDGAR & Global Regulatory Filings ({clean_symbol})")
        col_s1, col_s2 = st.columns([1, 2])
        with col_s1:
            sec_years = st.slider("Lookback Window (Years)", min_value=1, max_value=3, value=1, key="sec_lookback")
            load_sec = st.button("Fetch Direct SEC EDGAR Filings")

        if load_sec:
            with st.spinner("Querying SEC EDGAR..."):
                df_sec = fetch_sec_recent_filings(clean_symbol, lookback_days=365 * sec_years)
                st.session_state['df_sec'] = df_sec

        if 'df_sec' in st.session_state:
            df_sec = st.session_state['df_sec']
            if not df_sec.empty:
                st.dataframe(
    df_sec,
    column_config={
        "Filing Link": st.column_config.LinkColumn(
            "Official SEC Filing",
            help="Click to open the raw SEC EDGAR disclosure",
            display_text="Open Document ↗"
        )
    },
    use_container_width=True,
    hide_index=True
)
                if client and st.button("Analyze SEC Filings with Gemini"):
                    with st.spinner("Synthesizing filing history..."):
                        filings_blob = df_sec.to_string(index=False)
                        sec_p = (
                            f"Here is the ACTUAL SEC EDGAR filing history for {clean_symbol}, pulled "
                            f"directly from SEC.gov (form type, filing date, 8-K item codes decoded). "
                            f"Do NOT invent any filing, date, or monetary value not present below:\n\n"
                            f"{filings_blob}\n\n"
                            f"Summarize the material disclosure pattern: which item categories dominate, "
                            f"filing cadence, and any notable gaps or clusters. Structure: "
                            f"1. DISCLOSURE PATTERN SUMMARY  2. NOTABLE EVENTS  3. WHAT'S ABSENT / WORTH WATCHING."
                        )
                        sec_res = generate_content_resilient(client, sec_p, target_lang=selected_lang)
                        if sec_res:
                            st.markdown("---")
                            st.markdown(sec_res)
            else:
                st.warning("No SEC EDGAR filings found, or CIK could not be resolved for this ticker.")

        if not client and 'df_sec' in st.session_state and not st.session_state['df_sec'].empty:
            st.info("Add a Gemini API key in the sidebar to synthesize a summary — the filing table above is already live SEC data.")

# TAB 11: Filing Intelligence (PDF Reader)
with tab_filing:
    st.subheader(T["tabs"][10])
    st.caption("Upload annual reports (10-K / 20-F), investor presentations, or earnings call transcripts for forensic parsing.")
    
    uploaded_pdf = st.file_uploader(T["upload_pdf"], type=["pdf"], key="tab_pdf_uploader")
    
    if uploaded_pdf:
        st.success(f"Loaded filing: {uploaded_pdf.name}")
        query = st.text_input(
            "Custom Forensic Query:", 
            value="Detail backlog evolution, export concentration, supply chain bottlenecks, and cash burn."
        )
        
        if client and st.button("Extract Filing Forensics"):
            with st.spinner("Parsing PDF and extracting material disclosures..."):
                pdf_reader = pypdf.PdfReader(uploaded_pdf)
                pdf_text = "".join([p.extract_text() or "" for p in pdf_reader.pages[:30]])[:40000]
                
                p = (
                    f"You are a Senior Buy-Side Forensic Analyst. Analyze this raw corporate filing excerpt:\n\n"
                    f"{pdf_text}\n\n"
                    f"User Inquiry: {query}\n\n"
                    f"Structure your findings into:\n"
                    f"1. CORE FINDINGS & DISCLOSURE HIGHLIGHTS\n"
                    f"2. RISKS, COVENANTS & FOOTNOTE ANOMALIES\n"
                    f"3. ANALYST TAKEAWAY & THESIS IMPACT\n"
                    f"Avoid generic summaries; cite specific numbers and management commentary."
                )
                o = generate_content_resilient(client, p, target_lang=selected_lang)
                if o:
                    st.markdown("---")
                    st.markdown(o)
        elif not client:
            st.warning(T["enter_key_warn"])
    else:
        st.info("Drag and drop an official PDF report above to begin forensic extraction.")

# TAB 12: Hostile Bear-Case
with tab_redteam:
    st.subheader(T["tabs"][11])
    if client and st.button("Execute Short-Seller Stress Test"):
        with st.spinner("Simulating activist attack..."):
            p = f"Act as an activist hedge fund short-seller. Deconstruct {clean_symbol} based on live multiples (P/E: {pe_ratio}, EV/EBITDA: {ev_ebitda}). Deliver a 3-pillar attack: 1. Working capital trap, 2. Multiple derating trigger, 3. Balance sheet obfuscation."
            o = generate_content_resilient(client, p, target_lang=selected_lang)
            if o: st.markdown(o)
    elif not client:
        st.warning(T["enter_key_warn"])

# TAB 13: 1-Click IC Memo & One-Pager Export
with tab_memo:
    st.subheader(T["tabs"][12])
    if client and st.button(T["gen_memo"]):
        with st.spinner("Synthesizing IC note..."):
            memo_p = f"""
            Draft an institutional 1-page Investment Committee Recommendation Memo for {clean_symbol} ({ticker_input}).
            Price: {round(conv_price, 2) if pd.notnull(conv_price) else 'N/A'} {display_curr} | P/E: {pe_ratio} | EV/EBITDA: {ev_ebitda} | ROE: {roe}
            Structure:
            1. EXECUTIVE RECOMMENDATION (Actionable verdict, Target Multiple, Time Horizon)
            2. CORE INVESTMENT THESIS (3 distinct moats & catalysts)
            3. VALUATION & CAPITAL EFFICIENCY
            4. KEY RISKS & THESIS KILL CRITERIA
            """
            memo_out = generate_content_resilient(client, memo_p, target_lang=selected_lang)
            if memo_out:
                st.session_state['latest_ic_memo'] = memo_out

    if 'latest_ic_memo' in st.session_state:
        st.markdown("---")
        memo_content = st.session_state['latest_ic_memo']
        st.markdown(memo_content)
        
        memo_html_body = memo_content.replace("\n", "<br>")
        html_report = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>IC Memo - {clean_symbol}</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 40px; color: #0f172a; line-height: 1.6; }}
                .header {{ border-bottom: 2px solid #0284c7; padding-bottom: 12px; margin-bottom: 20px; }}
                .header h1 {{ margin: 0; font-size: 22px; color: #0f172a; text-transform: uppercase; }}
                .kpi-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; margin-bottom: 25px; }}
                .kpi-box {{ text-align: center; }}
                .kpi-title {{ font-size: 10px; font-weight: 600; color: #64748b; text-transform: uppercase; }}
                .kpi-val {{ font-size: 15px; font-weight: 700; color: #0284c7; margin-top: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Equity Research Investment Committee Memo</h1>
                <div>Company: <strong>{clean_symbol}</strong> | Currency: {display_curr} | Language: {selected_lang}</div>
            </div>
            <div class="kpi-grid">
                <div class="kpi-box"><div class="kpi-title">Price</div><div class="kpi-val">{round(conv_price, 2) if pd.notnull(conv_price) else 'N/A'}</div></div>
                <div class="kpi-box"><div class="kpi-title">P/E</div><div class="kpi-val">{pe_ratio}</div></div>
                <div class="kpi-box"><div class="kpi-title">EV/EBITDA</div><div class="kpi-val">{ev_ebitda}</div></div>
                <div class="kpi-box"><div class="kpi-title">Margin</div><div class="kpi-val">{gross_margin}</div></div>
                <div class="kpi-box"><div class="kpi-title">ROE</div><div class="kpi-val">{roe}</div></div>
            </div>
            <div>{memo_html_body}</div>
        </body>
        </html>
        """
        st.markdown("---")
        st.download_button(
            label=T["download_memo"],
            data=html_report,
            file_name=f"IC_Memo_{clean_symbol}_{selected_lang}_{datetime.now().strftime('%Y%m%d')}.html",
            mime="text/html"
        )
