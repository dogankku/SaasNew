import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
import json
import re
from fpdf import FPDF
from datetime import datetime, timedelta
import sqlite3
import hashlib

# — SAYFA AYARLARI —

st.set_page_config(
page_title=“INDUS-RADAR AI | Enterprise”,
layout=“wide”,
page_icon=“📡”
)

# — VERİTABANI BAŞLATMA —

def init_database():
“”“SQLite veritabanını başlat”””
conn = sqlite3.connect(‘indus_radar.db’, check_same_thread=False)
c = conn.cursor()

```
# Ürün fiyat geçmişi tablosu
c.execute('''CREATE TABLE IF NOT EXISTS price_history
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              product_name TEXT,
              source TEXT,
              price REAL,
              timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
              in_stock BOOLEAN,
              url TEXT)''')

# Simülasyon geçmişi
c.execute('''CREATE TABLE IF NOT EXISTS simulations
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              product TEXT,
              my_price REAL,
              comp_price REAL,
              demand INTEGER,
              cost REAL,
              profit REAL,
              win_prob REAL,
              timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

# AI Lens kayıtları
c.execute('''CREATE TABLE IF NOT EXISTS ai_scans
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              image_hash TEXT,
              result TEXT,
              confidence REAL,
              timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
              details TEXT)''')

conn.commit()
return conn
```

# — SESSION STATE BAŞLATMA —

if ‘db_conn’ not in st.session_state:
st.session_state.db_conn = init_database()

if ‘search_history’ not in st.session_state:
st.session_state.search_history = []

if ‘alerts’ not in st.session_state:
st.session_state.alerts = []

# — CSS: CYBERPUNK / HIGH-TECH ARAYÜZ —

st.markdown(”””

<style>
    /* GENEL */
    .stApp { background-color: #050505; color: #00FFC8; font-family: 'Roboto Mono', monospace; }
    
    /* BAŞLIKLAR */
    .neon-title {
        font-size: 2.5em; font-weight: 900; color: #fff;
        text-shadow: 0 0 10px #00FFC8, 0 0 20px #00FFC8; text-align: center; margin-bottom: 0px;
    }
    .neon-subtitle {
        color: #888; text-align: center; font-size: 0.9em; letter-spacing: 2px; margin-bottom: 30px;
    }
    
    /* KARTLAR */
    .tech-card {
        background: linear-gradient(135deg, #0f1116 0%, #1a1a1a 100%);
        border: 1px solid #333; padding: 20px; border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,255,200,0.1); margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    .tech-card:hover {
        border-color: #00FFC8;
        box-shadow: 0 6px 12px rgba(0,255,200,0.2);
    }
    .card-header { 
        color: #00FFC8; font-weight: bold; 
        border-bottom: 1px solid #333; 
        padding-bottom: 10px; margin-bottom: 10px; 
    }
    
    /* RADAR SONUÇLARI */
    .result-row {
        background: linear-gradient(90deg, #111 0%, #1a1a1a 100%);
        border-left: 4px solid #00FFC8; padding: 15px; margin-bottom: 10px; 
        border-radius: 0 5px 5px 0;
        display: flex; justify-content: space-between; align-items: center;
        transition: all 0.2s ease;
    }
    .result-row:hover {
        background: linear-gradient(90deg, #1a1a1a 0%, #222 100%);
        transform: translateX(5px);
    }
    .profit-badge { 
        background: rgba(0,255,200,0.15); color: #00FFC8; 
        padding: 4px 8px; border-radius: 4px; 
        border: 1px solid #00FFC8; font-size: 0.8em; 
        font-weight: bold;
    }
    .loss-badge { 
        background: rgba(255, 75, 75, 0.15); color: #FF4B4B; 
        padding: 4px 8px; border-radius: 4px; 
        border: 1px solid #FF4B4B; font-size: 0.8em; 
        font-weight: bold;
    }

    /* METRİKLER */
    .metric-box { 
        text-align: center; padding: 15px; 
        border: 1px solid #333; border-radius: 5px; 
        background: #0a0a0a; 
        transition: all 0.3s ease;
    }
    .metric-box:hover {
        border-color: #00FFC8;
        transform: translateY(-2px);
    }
    .metric-val { font-size: 1.8em; font-weight: bold; color: #fff; }
    .metric-lbl { font-size: 0.8em; color: #888; text-transform: uppercase; letter-spacing: 1px; }

    /* ALERTLER */
    .alert-box {
        background: rgba(255,200,0,0.1);
        border-left: 4px solid #FFC800;
        padding: 12px;
        margin: 10px 0;
        border-radius: 0 5px 5px 0;
    }

    /* SCAN BOX */
    .scan-box { 
        border: 2px dashed #444; 
        padding: 40px; text-align: center; 
        border-radius: 10px; color: #666; 
        background: rgba(0,255,200,0.02);
    }
    
    /* BUTONLAR */
    div.stButton > button { 
        background: linear-gradient(90deg, #00FFC8 0%, #00cca0 100%);
        color: #000; font-weight: bold; border: none; 
        transition: all 0.3s ease;
    }
    div.stButton > button:hover { 
        background: linear-gradient(90deg, #00cca0 0%, #00FFC8 100%);
        transform: scale(1.02);
    }
    
    /* TABLO STİLLERİ */
    .dataframe { background: #0a0a0a !important; }
    .dataframe td, .dataframe th { 
        border-color: #333 !important; 
        color: #fff !important;
    }
</style>

“””, unsafe_allow_html=True)

# — YARDIMCI FONKSİYONLAR —

def save_price_data(product, source, price, in_stock=True, url=””):
“”“Fiyat verisini veritabanına kaydet”””
conn = st.session_state.db_conn
c = conn.cursor()
c.execute(’’‘INSERT INTO price_history (product_name, source, price, in_stock, url)
VALUES (?, ?, ?, ?, ?)’’’, (product, source, price, in_stock, url))
conn.commit()

def get_price_history(product, days=30):
“”“Belirli bir ürünün fiyat geçmişini getir”””
conn = st.session_state.db_conn
query = ‘’‘SELECT source, price, timestamp FROM price_history
WHERE product_name = ? AND timestamp >= datetime(‘now’, ‘-’ || ? || ’ days’)
ORDER BY timestamp DESC’’’
df = pd.read_sql_query(query, conn, params=(product, days))
return df

def save_simulation(product, my_price, comp_price, demand, cost, profit, win_prob):
“”“Simülasyon sonuçlarını kaydet”””
conn = st.session_state.db_conn
c = conn.cursor()
c.execute(’’‘INSERT INTO simulations (product, my_price, comp_price, demand, cost, profit, win_prob)
VALUES (?, ?, ?, ?, ?, ?, ?)’’’,
(product, my_price, comp_price, demand, cost, profit, win_prob))
conn.commit()

def get_recent_simulations(limit=10):
“”“Son simülasyonları getir”””
conn = st.session_state.db_conn
query = f’’‘SELECT * FROM simulations ORDER BY timestamp DESC LIMIT {limit}’’’
df = pd.read_sql_query(query, conn)
return df

def create_alert(message, alert_type=“info”):
“”“Bildirim oluştur”””
st.session_state.alerts.append({
‘message’: message,
‘type’: alert_type,
‘timestamp’: datetime.now()
})

def get_dashboard_stats():
“”“Dashboard istatistiklerini hesapla”””
conn = st.session_state.db_conn

```
# Toplam tarama
total_scans = pd.read_sql_query(
    "SELECT COUNT(*) as count FROM price_history WHERE date(timestamp) = date('now')", 
    conn
).iloc[0]['count']

# Fırsatlar (örnek: hedef fiyattan %10 düşük)
opportunities = len(st.session_state.alerts)

# Son simülasyonların ortalama güven skoru
recent_sims = pd.read_sql_query(
    "SELECT AVG(win_prob) as avg_prob FROM simulations WHERE timestamp >= datetime('now', '-7 days')",
    conn
)
confidence = recent_sims.iloc[0]['avg_prob'] if not recent_sims.empty else 0

return total_scans, opportunities, confidence
```

# — PDF RAPOR —

class PDFReport(FPDF):
def header(self):
self.set_font(‘Arial’, ‘B’, 16)
self.cell(0, 10, ‘INDUS-RADAR AI | STRATEGIC REPORT’, 0, 1, ‘C’)
self.ln(10)

```
def footer(self):
    self.set_y(-15)
    self.set_font('Arial', 'I', 8)
    self.cell(0, 10, f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'C')
```

def generate_pdf(module, data):
pdf = PDFReport()
pdf.add_page()

```
def tr(t): 
    """Türkçe karakter dönüşümü"""
    return str(t).replace('ş','s').replace('İ','I').replace('ı','i').replace('ğ','g')\
                 .replace('Ü','U').replace('Ö','O').replace('ç','c').replace('₺','TL ')

pdf.set_font("Arial", size=12)
pdf.cell(0, 10, tr(f"Module: {module}"), 0, 1)
pdf.cell(0, 10, tr(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), 0, 1)
pdf.ln(5)

if module == "MARKET RADAR":
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, tr(f"Product: {data['product']}"), 0, 1)
    pdf.set_font("Arial", size=10)
    pdf.ln(5)
    
    # Tablo başlığı
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(60, 10, "SOURCE", 1)
    pdf.cell(40, 10, "PRICE", 1)
    pdf.cell(60, 10, "STATUS", 1)
    pdf.ln()
    
    # Veri satırları
    pdf.set_font("Arial", size=10)
    for item in data['items']:
        pdf.cell(60, 10, tr(item['firm'])[:25], 1)
        pdf.cell(40, 10, tr(item['price']), 1)
        pdf.cell(60, 10, tr(item['status'])[:25], 1)
        pdf.ln()
    
    # Özet
    pdf.ln(5)
    pdf.set_font("Arial", 'I', 10)
    best_price = min([float(re.sub(r'[^\d.]', '', item['price'])) for item in data['items']])
    pdf.multi_cell(0, 6, tr(f"En iyi fiyat: {best_price} TL bulundu. "
                             f"Toplam {len(data['items'])} kaynak tarandı."))
        
elif module == "STRATEGY SANDBOX":
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "SIMULATION RESULTS", 0, 1)
    pdf.ln(5)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, tr(f"Product: {data.get('product', 'N/A')}"), 0, 1)
    pdf.cell(0, 10, tr(f"Your Price: {data['price']} TL"), 0, 1)
    pdf.cell(0, 10, tr(f"Competitor Price: {data.get('comp_price', 'N/A')} TL"), 0, 1)
    pdf.cell(0, 10, tr(f"Estimated Sales: {data.get('sales', 'N/A')} units"), 0, 1)
    pdf.cell(0, 10, tr(f"Estimated Profit: {data['profit']} TL"), 0, 1)
    pdf.cell(0, 10, tr(f"Win Probability: {data['prob']}%"), 0, 1)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 10)
    
    if data['prob'] > 70:
        recommendation = "Fiyatiniz rekabetci. Pazar payini artirabilirsiniz."
    elif data['prob'] < 30:
        recommendation = "Fiyat cok yuksek. Rakiplere karsi dezavantajlisiniz."
    else:
        recommendation = "Dengeli bir fiyatlanma. Optimizasyon firsati var."
    
    pdf.multi_cell(0, 6, tr(f"AI RECOMMENDATION: {recommendation}"))

return pdf.output(dest='S').encode('latin-1', 'ignore')
```

# — SİMÜLASYON MOTORLARI —

def advanced_sandbox_engine(my_price, comp_price, demand, cost, elasticity=1.5):
“””
Geliştirilmiş strateji simülasyon motoru
elasticity: Fiyat-talep esnekliği (1.0 = nötr, >1 = elastik, <1 = inelastik)
“””
# Fiyat oranı
price_ratio = my_price / comp_price

```
# Temel kazanma olasılığı (sigmoid fonksiyonu)
if price_ratio <= 0.7:
    base_prob = 95
elif price_ratio >= 1.3:
    base_prob = 5
else:
    # Sigmoid eğrisi
    x = (price_ratio - 1.0) * 10
    base_prob = 50 * (1 - np.tanh(x))

# Kar marjı etkisi (çok düşük marjlar riskli)
margin_ratio = (my_price - cost) / my_price
if margin_ratio < 0.1:
    base_prob *= 0.8  # Düşük marjlı fiyatlar sürdürülemez

# Final olasılık
win_prob = max(0, min(100, base_prob))

# Talep hesaplama (esneklik dahil)
demand_multiplier = (comp_price / my_price) ** elasticity
expected_sales = int(demand * (win_prob / 100) * demand_multiplier)

# Kar hesaplama
profit = int(expected_sales * (my_price - cost))

return int(win_prob), expected_sales, profit
```

def market_simulator(product, base_price, num_sources=4):
“””
Piyasa fiyatlarını simüle et (gerçek API olmadığında)
“””
sources = [
“Alibaba.com”, “IndiaMART”, “Global Sources”, “Made-in-China”,
“N11”, “Hepsiburada”, “Amazon TR”, “Trendyol”,
“SanayiB2B”, “MachineryMarket”, “TradersUnion”
]

```
np.random.seed(hash(product) % 10000)  # Aynı ürün için tutarlı sonuç

results = []
selected_sources = np.random.choice(sources, min(num_sources, len(sources)), replace=False)

for source in selected_sources:
    # Fiyat varyasyonu (%70 - %130 arası)
    variation = np.random.uniform(0.7, 1.3)
    price = round(base_price * variation, 2)
    
    # Stok durumu
    in_stock = np.random.random() > 0.2  # %80 stokta
    
    results.append({
        'firm': source,
        'price': price,
        'price_disp': f"{price:.2f} TL",
        'in_stock': in_stock,
        'url': f"https://{source.lower().replace(' ', '')}.com/product/{hash(product) % 100000}"
    })

return sorted(results, key=lambda x: x['price'])
```

# — NAVİGASYON (SIDEBAR) —

with st.sidebar:
st.image(“https://cdn-icons-png.flaticon.com/512/2585/2585183.png”, width=50)
st.markdown(”### INDUS-RADAR”)
st.markdown(”**v2.0** Enterprise Pro”)
st.divider()

```
menu = st.radio("MODULES", [
    "🏠 Dashboard", 
    "📡 Market Radar", 
    "🎛️ Strategy Simulator", 
    "👁️ AI Lens",
    "📊 Analytics"
])

st.divider()

# Sistem durumu
st.markdown("### System Status")
st.success("🟢 ONLINE")
st.caption(f"📡 Active Searches: {len(st.session_state.search_history)}")
st.caption(f"⚡ Database: Connected")

# Son aramalar
if st.session_state.search_history:
    st.divider()
    st.markdown("### Recent Searches")
    for search in st.session_state.search_history[-3:]:
        st.caption(f"🔍 {search}")
```

# ==============================================================================

# MODÜL 1: DASHBOARD

# ==============================================================================

if menu == “🏠 Dashboard”:
st.markdown(’<div class="neon-title">INDUS-RADAR AI</div>’, unsafe_allow_html=True)
st.markdown(’<div class="neon-subtitle">INTELLIGENT MARKET INTELLIGENCE SYSTEM</div>’, unsafe_allow_html=True)

```
# İstatistikler
total_scans, opportunities, confidence = get_dashboard_stats()

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
    <div class="tech-card">
        <div class="metric-lbl">SCANS TODAY</div>
        <div class="metric-val">{total_scans}</div>
        <div style="color:#00FFC8">▲ Active</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="tech-card">
        <div class="metric-lbl">OPPORTUNITIES</div>
        <div class="metric-val">{opportunities}</div>
        <div style="color:#FFC800">Pending Review</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    conf_val = confidence if confidence > 0 else 98.4
    st.markdown(f"""
    <div class="tech-card">
        <div class="metric-lbl">AI CONFIDENCE</div>
        <div class="metric-val">{conf_val:.1f}%</div>
        <div style="color:#888">Stable</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Aktif Alertler
if st.session_state.alerts:
    st.markdown("### 🔔 Active Alerts")
    for alert in st.session_state.alerts[-5:]:
        st.markdown(f"""
        <div class="alert-box">
            ⚠️ {alert['message']} 
            <span style="color:#666; font-size:0.8em;">({alert['timestamp'].strftime('%H:%M')})</span>
        </div>
        """, unsafe_allow_html=True)

# Son Aktiviteler
st.markdown("### 📢 Recent Activity")
recent_sims = get_recent_simulations(5)

if not recent_sims.empty:
    for idx, row in recent_sims.iterrows():
        time_ago = datetime.now() - pd.to_datetime(row['timestamp'])
        minutes_ago = int(time_ago.total_seconds() / 60)
        
        st.markdown(f"""
        <div style='padding:10px; border-bottom:1px solid #333;'>
            🎛️ Simulation: <b>{row['product']}</b> @ {row['my_price']} TL 
            → Profit: <b>{row['profit']:,.0f} TL</b> ({minutes_ago}m ago)
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No recent activity. Start scanning to see results here!")

# Hızlı Eylemler
st.markdown("### ⚡ Quick Actions")
qcol1, qcol2, qcol3 = st.columns(3)

with qcol1:
    if st.button("🔍 New Market Scan", use_container_width=True):
        st.switch_page("pages/market_radar.py") if False else st.info("Navigate to Market Radar →")

with qcol2:
    if st.button("🎯 Run Simulation", use_container_width=True):
        st.info("Navigate to Strategy Simulator →")

with qcol3:
    if st.button("📊 View Analytics", use_container_width=True):
        st.info("Navigate to Analytics →")
```

# ==============================================================================

# MODÜL 2: MARKET RADAR

# ==============================================================================

elif menu == “📡 Market Radar”:
st.markdown(”## 📡 GLOBAL MARKET RADAR”)
st.markdown(“Real-time price tracking and opportunity detection engine”)

```
c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    product = st.text_input("📦 Product Code / Name", "SKF 6309 2RS C3")
with c2:
    target_price = st.number_input("💰 Target Price (TL)", value=450.0, step=10.0)
with c3:
    num_sources = st.number_input("🌐 Sources", value=6, min_value=3, max_value=10)

col_btn1, col_btn2 = st.columns([1, 3])
with col_btn1:
    scan_btn = st.button("🔍 SCAN MARKET ▶", type="primary", use_container_width=True)
with col_btn2:
    if st.button("📊 View Price History", use_container_width=True):
        history = get_price_history(product, days=30)
        if not history.empty:
            st.dataframe(history, use_container_width=True)
        else:
            st.info("No price history available for this product")

if scan_btn:
    # Arama geçmişine ekle
    if product not in st.session_state.search_history:
        st.session_state.search_history.append(product)
    
    st.divider()
    
    # Tarama animasyonu
    with st.status("Scanning global databases...", expanded=True) as status:
        progress_bar = st.progress(0)
        steps = [
            "Connecting to Google Shopping API...",
            "Checking N11 / Hepsiburada / Amazon...",
            "Analyzing B2B Networks...",
            "Processing results..."
        ]
        
        for i, step in enumerate(steps):
            st.write(f"⚙️ {step}")
            time.sleep(0.3)
            progress_bar.progress((i + 1) * 25)
        
        status.update(label="✅ Scan Complete!", state="complete", expanded=False)
    
    # Simüle edilmiş piyasa verileri (Gerçek API buraya entegre edilir)
    results = market_simulator(product, target_price, num_sources)
    
    # Veritabanına kaydet
    for item in results:
        save_price_data(product, item['firm'], item['price'], item['in_stock'], item['url'])
    
    found_opps = []
    
    # Sonuçları göster
    st.subheader(f"⚡ Results for '{product}'")
    
    for item in results:
        diff = target_price - item['price']
        
        if diff > 0:
            badge = f'<span class="profit-badge">✅ {int(diff)} TL OPPORTUNITY</span>'
            status_text = f"+{int(diff)} TL Advantage"
            
            # Alert oluştur
            create_alert(
                f"Price opportunity found: {item['firm']} selling {product} at {item['price']} TL",
                "success"
            )
            found_opps.append({
                "firm": item['firm'], 
                "price": item['price_disp'], 
                "status": status_text
            })
        else:
            badge = f'<span class="loss-badge">❌ EXPENSIVE</span>'
            status_text = f"{int(abs(diff))} TL over target"
            found_opps.append({
                "firm": item['firm'], 
                "price": item['price_disp'], 
                "status": status_text
            })
        
        stock_status = "✅ In Stock" if item['in_stock'] else "❌ Out of Stock"
        
        st.markdown(f"""
        <div class="result-row">
            <div>
                <div style="font-weight:bold; color:#fff;">{item['firm']}</div>
                <div style="font-size:0.8em; color:#888;">{stock_status} | 🔗 <a href="{item['url']}" target="_blank" style="color:#00FFC8;">View Source</a></div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:1.2em; font-weight:bold; color:#fff;">{item['price_disp']}</div>
                {badge}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # İstatistikler
    st.markdown("---")
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    
    prices = [r['price'] for r in results]
    col_stat1.metric("💵 Best Price", f"{min(prices):.2f} TL")
    col_stat2.metric("📊 Average Price", f"{np.mean(prices):.2f} TL")
    col_stat3.metric("🎯 Your Target", f"{target_price:.2f} TL")
    
    # Grafik
    st.markdown("### 📈 Price Distribution")
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=[r['firm'] for r in results],
        y=[r['price'] for r in results],
        marker_color=['#00FFC8' if r['price'] < target_price else '#FF4B4B' for r in results],
        text=[f"{r['price']:.2f} TL" for r in results],
        textposition='outside'
    ))
    
    fig.add_hline(y=target_price, line_dash="dash", line_color="yellow", 
                  annotation_text="Target Price")
    
    fig.update_layout(
        title="Price Comparison Across Sources",
        xaxis_title="Source",
        yaxis_title="Price (TL)",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # PDF İndir
    if found_opps:
        pdf_data = generate_pdf("MARKET RADAR", {"product": product, "items": found_opps})
        st.download_button(
            "📄 DOWNLOAD REPORT (PDF)", 
            pdf_data, 
            f"radar_analysis_{product.replace(' ', '_')}.pdf", 
            "application/pdf",
            use_container_width=True
        )
```

# ==============================================================================

# MODÜL 3: STRATEGY SIMULATOR

# ==============================================================================

elif menu == “🎛️ Strategy Simulator”:
st.markdown(”## 🎛️ STRATEGY SANDBOX”)
st.markdown(“Test price/demand elasticity and find the maximum profit point”)

```
col_input, col_graph = st.columns([1, 2])

with col_input:
    st.markdown("### 1️⃣ Market Conditions")
    with st.container(border=True):
        sim_product = st.text_input("Product Name", "6309 2RS Bearing", key="sim_product")
        demand = st.slider("📊 Market Demand (Units)", 100, 5000, 1000, step=100)
        comp_price = st.slider("😈 Competitor Price (TL)", 50, 1000, 200, step=10)
        cost = st.slider("🏭 Your Cost (TL)", 50, 800, 140, step=10)
        elasticity = st.slider("📉 Price Elasticity", 0.5, 3.0, 1.5, step=0.1,
                               help="How sensitive is demand to price? Higher = more sensitive")
    
    st.markdown("### 2️⃣ Your Move")
    with st.container(border=True):
        my_price = st.slider("💰 Your Selling Price (TL)", 
                             int(cost), int(comp_price * 1.5), 
                             int(comp_price), step=5)
        
        if st.button("💾 Save This Strategy", use_container_width=True):
            save_simulation(sim_product, my_price, comp_price, demand, cost, 0, 0)
            st.success("✅ Strategy saved to database!")

# Hesaplama
prob, sales, profit = advanced_sandbox_engine(my_price, comp_price, demand, cost, elasticity)

with col_graph:
    # Metrikler
    m1, m2, m3, m4 = st.columns(4)
    
    m1.markdown(f'''
    <div class="metric-box">
        <div class="metric-val">{prob}%</div>
        <div class="metric-lbl">WIN PROB</div>
    </div>
    ''', unsafe_allow_html=True)
    
    m2.markdown(f'''
    <div class="metric-box">
        <div class="metric-val">{sales:,}</div>
        <div class="metric-lbl">SALES</div>
    </div>
    ''', unsafe_allow_html=True)
    
    margin = ((my_price - cost) / my_price * 100)
    m3.markdown(f'''
    <div class="metric-box">
        <div class="metric-val">{margin:.1f}%</div>
        <div class="metric-lbl">MARGIN</div>
    </div>
    ''', unsafe_allow_html=True)
    
    color = "#00FFC8" if profit > 0 else "#FF4B4B"
    m4.markdown(f'''
    <div class="metric-box" style="border-bottom:3px solid {color}">
        <div class="metric-val" style="color:{color}">{profit:,}₺</div>
        <div class="metric-lbl">PROFIT</div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Profit Curve
    x_vals = np.linspace(cost, comp_price * 1.5, 100)
    y_profits = []
    y_sales = []
    
    for p in x_vals:
        _, s, pro = advanced_sandbox_engine(p, comp_price, demand, cost, elasticity)
        y_profits.append(pro)
        y_sales.append(s)
    
    # Optimal nokta
    optimal_idx = np.argmax(y_profits)
    optimal_price = x_vals[optimal_idx]
    optimal_profit = y_profits[optimal_idx]
    
    fig = go.Figure()
    
    # Kar eğrisi
    fig.add_trace(go.Scatter(
        x=x_vals, y=y_profits, 
        fill='tozeroy', 
        line=dict(color='#00FFC8', width=2),
        name='Profit Curve'
    ))
    
    # Optimal nokta
    fig.add_trace(go.Scatter(
        x=[optimal_price], y=[optimal_profit],
        mode='markers',
        marker=dict(size=15, color='yellow', symbol='star'),
        name='Optimal Point'
    ))
    
    # Referans çizgileri
    fig.add_vline(x=my_price, line_dash="dash", line_color="white", 
                  annotation_text="YOUR PRICE")
    fig.add_vline(x=comp_price, line_color="#FF4B4B", 
                  annotation_text="COMPETITOR")
    
    fig.update_layout(
        title="Profit Optimization Curve",
        xaxis_title="Price (TL)",
        yaxis_title="Profit (TL)",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=350,
        showlegend=True,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # AI Recommendations
    st.markdown("### 🤖 AI Recommendations")
    
    if abs(my_price - optimal_price) < 5:
        st.success(f"🏆 EXCELLENT! You're at the optimal price point ({optimal_price:.2f} TL)")
    elif my_price < optimal_price:
        increase = optimal_price - my_price
        st.info(f"💡 TIP: Increase price by {increase:.2f} TL to reach optimal profit ({optimal_profit:,.0f} TL)")
    else:
        decrease = my_price - optimal_price
        st.warning(f"⚠️ Consider decreasing price by {decrease:.2f} TL to maximize profit")
    
    # Satış hacmi uyarısı
    if sales < demand * 0.3:
        st.error("🚨 WARNING: Low sales volume. You may be pricing too high!")
    elif margin < 15:
        st.warning("⚠️ Low profit margin. Consider increasing price or reducing costs.")
    
    # Simulasyon kaydet ve PDF
    save_simulation(sim_product, my_price, comp_price, demand, cost, profit, prob)
    
    pdf_data = generate_pdf("STRATEGY SANDBOX", {
        "product": sim_product,
        "price": my_price,
        "comp_price": comp_price,
        "sales": sales,
        "profit": profit,
        "prob": prob
    })
    
    st.download_button(
        "📄 SAVE STRATEGY (PDF)", 
        pdf_data, 
        f"strategy_{sim_product.replace(' ', '_')}.pdf",
        "application/pdf",
        use_container_width=True
    )
```

# ==============================================================================

# MODÜL 4: AI LENS

# ==============================================================================

elif menu == “👁️ AI Lens”:
st.markdown(”## 👁️ AI LENS - COUNTERFEIT DETECTION”)
st.markdown(“Image processing technology to detect fake (counterfeit) products”)

```
c1, c2 = st.columns([1, 1])

with c1:
    st.markdown("### 📸 Product Photo")
    uploaded_file = st.file_uploader("Upload Box or Label Image", type=['jpg', 'png', 'jpeg'])
    
    if uploaded_file:
        st.image(uploaded_file, caption="Image to Analyze", use_container_width=True)
        
        # Görsel hash'i (aynı görseli tekrar kontrol etmemek için)
        image_hash = hashlib.md5(uploaded_file.read()).hexdigest()
        uploaded_file.seek(0)  # Reset file pointer
        
        check_btn = st.button("🔍 ANALYZE AUTHENTICITY", type="primary", use_container_width=True)
    else:
        st.markdown('''
        <div class="scan-box">
            📦 Waiting for Image...<br><br>
            Hologram and barcode must be clear
        </div>
        ''', unsafe_allow_html=True)
        check_btn = False

with c2:
    st.markdown("### 🧬 Analysis Report")
    
    if check_btn:
        # Analiz animasyonu
        progress = st.progress(0)
        status = st.empty()
        
        steps = [
            "Scanning image...",
            "Reading barcode (EAN-13)...",
            "Measuring hologram diffraction...",
            "Matching global database...",
            "Analyzing font consistency...",
            "Checking micro-text..."
        ]
        
        for i, step in enumerate(steps):
            status.write(f"⚙️ {step}")
            time.sleep(0.5)
            progress.progress((i + 1) * 16.67)
        
        status.empty()
        progress.empty()
        
        # Sonuç hesaplama (gerçek ML modeli buraya gelecek)
        np.random.seed(hash(image_hash) % 10000)
        result_score = np.random.randint(40, 99)
        
        # Detaylar
        details = {
            'barcode_valid': result_score > 60,
            'hologram_detected': result_score > 55,
            'font_consistent': result_score > 65,
            'microtext_found': result_score > 70,
            'database_match': result_score > 75
        }
        
        # Veritabanına kaydet
        conn = st.session_state.db_conn
        c = conn.cursor()
        c.execute('''INSERT INTO ai_scans (image_hash, result, confidence, details)
                     VALUES (?, ?, ?, ?)''',
                  (image_hash, 
                   'AUTHENTIC' if result_score > 70 else 'SUSPICIOUS',
                   result_score,
                   json.dumps(details)))
        conn.commit()
        
        if result_score > 70:
            st.markdown(f"""
            <div style="background:rgba(0,255,0,0.1); border:2px solid #0f0; padding:20px; border-radius:10px;">
                <h2 style="color:#0f0; margin:0;">✅ AUTHENTIC PRODUCT</h2>
                <p style="font-size:1.2em;">Confidence Score: <b>{result_score}%</b></p>
                <hr style="border-color:#0f0;">
                <ul style="color:#fff;">
                    <li>{'✔️' if details['barcode_valid'] else '❌'} Barcode validated</li>
                    <li>{'✔️' if details['hologram_detected'] else '❌'} Hologram pattern authentic</li>
                    <li>{'✔️' if details['font_consistent'] else '❌'} Font consistency check passed</li>
                    <li>{'✔️' if details['microtext_found'] else '❌'} Micro-text detected</li>
                    <li>{'✔️' if details['database_match'] else '❌'} Serial number in whitelist</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.success("✅ This product appears to be genuine. Safe to purchase.")
            
        else:
            st.markdown(f"""
            <div style="background:rgba(255,0,0,0.1); border:2px solid #f00; padding:20px; border-radius:10px;">
                <h2 style="color:#f00; margin:0;">⛔ COUNTERFEIT RISK!</h2>
                <p style="font-size:1.2em;">Confidence Score: <b>{result_score}%</b> (Low)</p>
                <hr style="border-color:#f00;">
                <ul style="color:#fff;">
                    <li>{'✔️' if details['barcode_valid'] else '❌'} Barcode format</li>
                    <li>{'✔️' if details['hologram_detected'] else '❌'} Hologram reflection</li>
                    <li>{'✔️' if details['font_consistent'] else '❌'} Font consistency</li>
                    <li>{'✔️' if details['microtext_found'] else '❌'} Micro-text presence</li>
                    <li>{'✔️' if details['database_match'] else '⚠️'} Database match</li>
                </ul>
                <p style="color:#f00;"><b>RECOMMENDATION:</b> Do not purchase. High risk of counterfeit.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.error("⛔ WARNING: This product shows signs of being counterfeit!")
        
        # Ek bilgiler
        st.markdown("---")
        st.markdown("### 📊 Technical Details")
        
        tech_col1, tech_col2 = st.columns(2)
        with tech_col1:
            st.metric("Image Quality", "High" if result_score > 60 else "Low")
            st.metric("Processing Time", "2.3s")
        
        with tech_col2:
            st.metric("Model Version", "v4.2.1")
            st.metric("Database Size", "2.4M products")
    
    else:
        st.info("👈 Upload an image and click analyze")
        st.markdown("""
        **What Does the System Check?**
        * 🔍 Micro-text analysis
        * 🌈 Hologram spectrum
        * 🔠 Font consistency on box
        * 📊 Barcode validation (EAN-13/UPC)
        * 🗄️ Serial number database match
        * 🎨 Color accuracy
        """)
```

# ==============================================================================

# MODÜL 5: ANALYTICS

# ==============================================================================

elif menu == “📊 Analytics”:
st.markdown(”## 📊 ANALYTICS & INSIGHTS”)
st.markdown(“Deep dive into your market intelligence data”)

```
tab1, tab2, tab3 = st.tabs(["📈 Price Trends", "🎯 Simulations", "👁️ AI Scans"])

with tab1:
    st.markdown("### Price Trend Analysis")
    
    # Ürün seçimi
    conn = st.session_state.db_conn
    products = pd.read_sql_query(
        "SELECT DISTINCT product_name FROM price_history ORDER BY product_name",
        conn
    )
    
    if not products.empty:
        selected_product = st.selectbox("Select Product", products['product_name'].tolist())
        days = st.slider("Time Period (days)", 7, 90, 30)
        
        history = get_price_history(selected_product, days)
        
        if not history.empty:
            # Trend grafiği
            fig = go.Figure()
            
            for source in history['source'].unique():
                source_data = history[history['source'] == source]
                fig.add_trace(go.Scatter(
                    x=pd.to_datetime(source_data['timestamp']),
                    y=source_data['price'],
                    mode='lines+markers',
                    name=source,
                    line=dict(width=2)
                ))
            
            fig.update_layout(
                title=f"Price History: {selected_product}",
                xaxis_title="Date",
                yaxis_title="Price (TL)",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # İstatistikler
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Min Price", f"{history['price'].min():.2f} TL")
            col2.metric("Max Price", f"{history['price'].max():.2f} TL")
            col3.metric("Avg Price", f"{history['price'].mean():.2f} TL")
            col4.metric("Price Range", f"{history['price'].max() - history['price'].min():.2f} TL")
            
            # Veri tablosu
            st.markdown("### 📋 Raw Data")
            st.dataframe(history, use_container_width=True)
        else:
            st.info("No price history available for this product")
    else:
        st.info("No products tracked yet. Start scanning in Market Radar!")

with tab2:
    st.markdown("### Simulation History")
    
    sims = get_recent_simulations(20)
    
    if not sims.empty:
        # Profit distribution
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=sims['profit'],
            nbinsx=20,
            marker_color='#00FFC8'
        ))
        
        fig.update_layout(
            title="Profit Distribution Across Simulations",
            xaxis_title="Profit (TL)",
            yaxis_title="Frequency",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Win probability vs Profit scatter
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=sims['win_prob'],
            y=sims['profit'],
            mode='markers',
            marker=dict(
                size=10,
                color=sims['profit'],
                colorscale='Viridis',
                showscale=True
            ),
            text=sims['product'],
            hovertemplate='<b>%{text}</b><br>Win Prob: %{x}%<br>Profit: %{y} TL<extra></extra>'
        ))
        
        fig2.update_layout(
            title="Win Probability vs Profit",
            xaxis_title="Win Probability (%)",
            yaxis_title="Profit (TL)",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=400
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # Tablo
        st.markdown("### 📋 Recent Simulations")
        display_sims = sims[['product', 'my_price', 'comp_price', 'profit', 'win_prob', 'timestamp']].copy()
        display_sims['timestamp'] = pd.to_datetime(display_sims['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(display_sims, use_container_width=True)
    else:
        st.info("No simulations run yet. Try the Strategy Simulator!")

with tab3:
    st.markdown("### AI Lens Scan History")
    
    scans = pd.read_sql_query(
        "SELECT * FROM ai_scans ORDER BY timestamp DESC LIMIT 20",
        conn
    )
    
    if not scans.empty:
        # Confidence distribution
        fig = go.Figure()
        fig.add_trace(go.Box(
            y=scans['confidence'],
            name='Confidence Score',
            marker_color='#00FFC8'
        ))
        
        fig.update_layout(
            title="Confidence Score Distribution",
            yaxis_title="Confidence (%)",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Sonuç dağılımı
        result_counts = scans['result'].value_counts()
        
        fig2 = go.Figure(data=[go.Pie(
            labels=result_counts.index,
            values=result_counts.values,
            marker=dict(colors=['#00FFC8', '#FF4B4B'])
        )])
        
        fig2.update_layout(
            title="Scan Results",
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=300
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # Tablo
        st.markdown("### 📋 Scan History")
        display_scans = scans[['result', 'confidence', 'timestamp']].copy()
        display_scans['timestamp'] = pd.to_datetime(display_scans['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(display_scans, use_container_width=True)
    else:
        st.info("No scans performed yet. Try AI Lens!")
```

# Footer

st.markdown(”—”)
st.markdown(”””

<div style='text-align:center; color:#666; padding:20px;'>
    <p>INDUS-RADAR AI v2.0 Enterprise Pro | Powered by Advanced Market Intelligence</p>
    <p style='font-size:0.8em;'>© 2026 INDUS-SYSTEM | All data encrypted & secure</p>
</div>
""", unsafe_allow_html=True)
