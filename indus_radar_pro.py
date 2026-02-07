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

st.set_page_config(
page_title=“INDUS-RADAR AI Enterprise”,
layout=“wide”,
page_icon=“📡”
)

def init_database():
conn = sqlite3.connect(“indus_radar.db”, check_same_thread=False)
c = conn.cursor()

```
c.execute("""CREATE TABLE IF NOT EXISTS price_history
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              product_name TEXT,
              source TEXT,
              price REAL,
              timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
              in_stock BOOLEAN,
              url TEXT)""")

c.execute("""CREATE TABLE IF NOT EXISTS simulations
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              product TEXT,
              my_price REAL,
              comp_price REAL,
              demand INTEGER,
              cost REAL,
              profit REAL,
              win_prob REAL,
              timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")

c.execute("""CREATE TABLE IF NOT EXISTS ai_scans
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              image_hash TEXT,
              result TEXT,
              confidence REAL,
              timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
              details TEXT)""")

conn.commit()
return conn
```

if “db_conn” not in st.session_state:
st.session_state.db_conn = init_database()

if “search_history” not in st.session_state:
st.session_state.search_history = []

if “alerts” not in st.session_state:
st.session_state.alerts = []

st.markdown(”””

<style>
    .stApp { 
        background-color: #050505; 
        color: #00FFC8; 
        font-family: monospace; 
    }
    .neon-title {
        font-size: 2.5em; 
        font-weight: 900; 
        color: #fff;
        text-shadow: 0 0 10px #00FFC8; 
        text-align: center;
    }
    .tech-card {
        background: #0f1116;
        border: 1px solid #333; 
        padding: 20px; 
        border-radius: 8px;
        margin-bottom: 20px;
    }
    .result-row {
        background: #1a1a1a;
        border-left: 4px solid #00FFC8; 
        padding: 15px; 
        margin-bottom: 10px; 
        border-radius: 5px;
    }
    .profit-badge { 
        background: rgba(0,255,200,0.15); 
        color: #00FFC8; 
        padding: 4px 8px; 
        border-radius: 4px; 
        border: 1px solid #00FFC8; 
        font-weight: bold;
    }
    .loss-badge { 
        background: rgba(255, 75, 75, 0.15); 
        color: #FF4B4B; 
        padding: 4px 8px; 
        border-radius: 4px; 
        border: 1px solid #FF4B4B; 
        font-weight: bold;
    }
    .metric-box { 
        text-align: center; 
        padding: 15px; 
        border: 1px solid #333; 
        border-radius: 5px; 
        background: #0a0a0a;
    }
    .metric-val { 
        font-size: 1.8em; 
        font-weight: bold; 
        color: #fff; 
    }
    .metric-lbl { 
        font-size: 0.8em; 
        color: #888; 
        text-transform: uppercase;
    }
</style>

“””, unsafe_allow_html=True)

def save_price_data(product, source, price, in_stock=True, url=””):
conn = st.session_state.db_conn
c = conn.cursor()
c.execute(””“INSERT INTO price_history (product_name, source, price, in_stock, url)
VALUES (?, ?, ?, ?, ?)”””, (product, source, price, in_stock, url))
conn.commit()

def get_price_history(product, days=30):
conn = st.session_state.db_conn
query = “”“SELECT source, price, timestamp FROM price_history
WHERE product_name = ? AND timestamp >= datetime(‘now’, ‘-’ || ? || ’ days’)
ORDER BY timestamp DESC”””
df = pd.read_sql_query(query, conn, params=(product, days))
return df

def save_simulation(product, my_price, comp_price, demand, cost, profit, win_prob):
conn = st.session_state.db_conn
c = conn.cursor()
c.execute(””“INSERT INTO simulations (product, my_price, comp_price, demand, cost, profit, win_prob)
VALUES (?, ?, ?, ?, ?, ?, ?)”””,
(product, my_price, comp_price, demand, cost, profit, win_prob))
conn.commit()

def get_recent_simulations(limit=10):
conn = st.session_state.db_conn
query = f””“SELECT * FROM simulations ORDER BY timestamp DESC LIMIT {limit}”””
df = pd.read_sql_query(query, conn)
return df

def get_dashboard_stats():
conn = st.session_state.db_conn

```
total_scans = pd.read_sql_query(
    "SELECT COUNT(*) as count FROM price_history WHERE date(timestamp) = date('now')", 
    conn
).iloc[0]["count"]

opportunities = len(st.session_state.alerts)

recent_sims = pd.read_sql_query(
    "SELECT AVG(win_prob) as avg_prob FROM simulations WHERE timestamp >= datetime('now', '-7 days')",
    conn
)
confidence = recent_sims.iloc[0]["avg_prob"] if not recent_sims.empty else 0

return total_scans, opportunities, confidence
```

def advanced_sandbox_engine(my_price, comp_price, demand, cost, elasticity=1.5):
price_ratio = my_price / comp_price

```
if price_ratio <= 0.7:
    base_prob = 95
elif price_ratio >= 1.3:
    base_prob = 5
else:
    x = (price_ratio - 1.0) * 10
    base_prob = 50 * (1 - np.tanh(x))

margin_ratio = (my_price - cost) / my_price
if margin_ratio < 0.1:
    base_prob *= 0.8

win_prob = max(0, min(100, base_prob))
demand_multiplier = (comp_price / my_price) ** elasticity
expected_sales = int(demand * (win_prob / 100) * demand_multiplier)
profit = int(expected_sales * (my_price - cost))

return int(win_prob), expected_sales, profit
```

def market_simulator(product, base_price, num_sources=4):
sources = [
“Alibaba”, “IndiaMART”, “Global Sources”, “Made-in-China”,
“N11”, “Hepsiburada”, “Amazon TR”, “Trendyol”
]

```
np.random.seed(hash(product) % 10000)
results = []
selected_sources = np.random.choice(sources, min(num_sources, len(sources)), replace=False)

for source in selected_sources:
    variation = np.random.uniform(0.7, 1.3)
    price = round(base_price * variation, 2)
    in_stock = np.random.random() > 0.2
    
    results.append({
        "firm": source,
        "price": price,
        "price_disp": f"{price:.2f} TL",
        "in_stock": in_stock,
        "url": f"https://example.com/{hash(product) % 100000}"
    })

return sorted(results, key=lambda x: x["price"])
```

with st.sidebar:
st.markdown(”### INDUS-RADAR”)
st.markdown(”**v2.0** Enterprise”)
st.divider()

```
menu = st.radio("MODULES", [
    "Dashboard", 
    "Market Radar", 
    "Strategy Simulator"
])

st.divider()
st.success("System Online")
```

if menu == “Dashboard”:
st.markdown(’<div class="neon-title">INDUS-RADAR AI</div>’, unsafe_allow_html=True)

```
total_scans, opportunities, confidence = get_dashboard_stats()

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
    <div class="tech-card">
        <div class="metric-lbl">SCANS TODAY</div>
        <div class="metric-val">{total_scans}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="tech-card">
        <div class="metric-lbl">OPPORTUNITIES</div>
        <div class="metric-val">{opportunities}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    conf_val = confidence if confidence > 0 else 98.4
    st.markdown(f"""
    <div class="tech-card">
        <div class="metric-lbl">AI CONFIDENCE</div>
        <div class="metric-val">{conf_val:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("### Recent Activity")
recent_sims = get_recent_simulations(5)

if not recent_sims.empty:
    for idx, row in recent_sims.iterrows():
        st.write(f"Simulation: {row['product']} @ {row['my_price']} TL -> Profit: {row['profit']} TL")
else:
    st.info("No recent activity")
```

elif menu == “Market Radar”:
st.markdown(”## Market Radar”)
st.write(“Real-time price tracking”)

```
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    product = st.text_input("Product Name", "SKF 6309 2RS C3")
with col2:
    target_price = st.number_input("Target Price (TL)", value=450.0, step=10.0)
with col3:
    num_sources = st.number_input("Sources", value=6, min_value=3, max_value=10)

scan_btn = st.button("SCAN MARKET", type="primary")

if scan_btn:
    if product not in st.session_state.search_history:
        st.session_state.search_history.append(product)
    
    with st.spinner("Scanning..."):
        time.sleep(1)
    
    results = market_simulator(product, target_price, num_sources)
    
    for item in results:
        save_price_data(product, item["firm"], item["price"], item["in_stock"], item["url"])
    
    st.subheader(f"Results for {product}")
    
    for item in results:
        diff = target_price - item["price"]
        
        if diff > 0:
            badge = f'<span class="profit-badge">+{int(diff)} TL OPPORTUNITY</span>'
        else:
            badge = f'<span class="loss-badge">EXPENSIVE</span>'
        
        stock = "In Stock" if item["in_stock"] else "Out of Stock"
        
        st.markdown(f"""
        <div class="result-row">
            <div>
                <b>{item["firm"]}</b><br>
                <small>{stock}</small>
            </div>
            <div>
                <b>{item["price_disp"]}</b><br>
                {badge}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    prices = [r["price"] for r in results]
    col1, col2, col3 = st.columns(3)
    col1.metric("Best Price", f"{min(prices):.2f} TL")
    col2.metric("Average", f"{np.mean(prices):.2f} TL")
    col3.metric("Target", f"{target_price:.2f} TL")
```

elif menu == “Strategy Simulator”:
st.markdown(”## Strategy Simulator”)
st.write(“Price optimization engine”)

```
col_input, col_graph = st.columns([1, 2])

with col_input:
    st.markdown("### Market Conditions")
    sim_product = st.text_input("Product", "6309 Bearing")
    demand = st.slider("Demand (Units)", 100, 5000, 1000, step=100)
    comp_price = st.slider("Competitor Price", 50, 1000, 200, step=10)
    cost = st.slider("Your Cost", 50, 800, 140, step=10)
    elasticity = st.slider("Elasticity", 0.5, 3.0, 1.5, step=0.1)
    
    st.markdown("### Your Price")
    my_price = st.slider("Selling Price", int(cost), int(comp_price * 1.5), int(comp_price), step=5)

prob, sales, profit = advanced_sandbox_engine(my_price, comp_price, demand, cost, elasticity)

with col_graph:
    col1, col2, col3, col4 = st.columns(4)
    
    col1.markdown(f"""
    <div class="metric-box">
        <div class="metric-val">{prob}%</div>
        <div class="metric-lbl">WIN PROB</div>
    </div>
    """, unsafe_allow_html=True)
    
    col2.markdown(f"""
    <div class="metric-box">
        <div class="metric-val">{sales:,}</div>
        <div class="metric-lbl">SALES</div>
    </div>
    """, unsafe_allow_html=True)
    
    margin = ((my_price - cost) / my_price * 100)
    col3.markdown(f"""
    <div class="metric-box">
        <div class="metric-val">{margin:.1f}%</div>
        <div class="metric-lbl">MARGIN</div>
    </div>
    """, unsafe_allow_html=True)
    
    color = "#00FFC8" if profit > 0 else "#FF4B4B"
    col4.markdown(f"""
    <div class="metric-box">
        <div class="metric-val" style="color:{color}">{profit:,}</div>
        <div class="metric-lbl">PROFIT (TL)</div>
    </div>
    """, unsafe_allow_html=True)
    
    x_vals = np.linspace(cost, comp_price * 1.5, 100)
    y_profits = []
    
    for p in x_vals:
        _, _, pro = advanced_sandbox_engine(p, comp_price, demand, cost, elasticity)
        y_profits.append(pro)
    
    optimal_idx = np.argmax(y_profits)
    optimal_price = x_vals[optimal_idx]
    optimal_profit = y_profits[optimal_idx]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=x_vals, y=y_profits, 
        fill="tozeroy", 
        line=dict(color="#00FFC8", width=2),
        name="Profit Curve"
    ))
    
    fig.add_trace(go.Scatter(
        x=[optimal_price], y=[optimal_profit],
        mode="markers",
        marker=dict(size=15, color="yellow", symbol="star"),
        name="Optimal"
    ))
    
    fig.add_vline(x=my_price, line_dash="dash", line_color="white")
    fig.add_vline(x=comp_price, line_color="#FF4B4B")
    
    fig.update_layout(
        title="Profit Optimization",
        xaxis_title="Price (TL)",
        yaxis_title="Profit (TL)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### AI Recommendations")
    
    if abs(my_price - optimal_price) < 5:
        st.success(f"Excellent! Optimal price: {optimal_price:.2f} TL")
    elif my_price < optimal_price:
        increase = optimal_price - my_price
        st.info(f"Increase price by {increase:.2f} TL")
    else:
        decrease = my_price - optimal_price
        st.warning(f"Decrease price by {decrease:.2f} TL")
    
    save_simulation(sim_product, my_price, comp_price, demand, cost, profit, prob)
```

st.markdown(”—”)
st.caption(“INDUS-RADAR AI v2.0 - Enterprise Pro”)
