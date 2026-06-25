"""
Streamlit Dashboard — ราคาเศษเหล็กจาก LINE
รัน: streamlit run dashboard.py
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import hashlib
import os


# ══════════════════════════════════════════
# Password Protection
# ══════════════════════════════════════════

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def check_login():
    # รหัสผ่านจาก secrets หรือ environment variable
    try:
        correct_password = st.secrets["DASHBOARD_PASSWORD"]
    except Exception:
        correct_password = os.getenv("DASHBOARD_PASSWORD", "scrap2024")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        return True

    # หน้า Login
    st.set_page_config(page_title="Login — เศษเหล็ก Tracker", page_icon="🔒", layout="centered")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        st.markdown("## 🏗️ เศษเหล็ก Price Tracker")
        st.markdown("### 🔒 กรุณาใส่รหัสผ่าน")

        password = st.text_input("รหัสผ่าน", type="password", placeholder="ใส่รหัสผ่านที่นี่")

        if st.button("เข้าสู่ระบบ", use_container_width=True, type="primary"):
            if password == correct_password:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ รหัสผ่านไม่ถูกต้อง")

        st.markdown("---")
        st.caption("ระบบติดตามราคาเศษเหล็กจาก LINE")

    return False

if not check_login():
    st.stop()
from database import (
    add_alert, add_demo_data, delete_alert,
    get_alerts, get_categories, get_grades, get_companies,
    get_latest_prices, get_price_history,
    init_db, toggle_alert,
)

st.set_page_config(page_title="เศษเหล็ก Price Tracker", page_icon="🏗️", layout="wide")
init_db()

# ══════════════════════════════════════════
# Sidebar
# ══════════════════════════════════════════
with st.sidebar:
    st.title("🏗️ เศษเหล็ก Tracker")
    st.divider()

    # ── Alert management ──────────────────
    st.subheader("🔔 ตั้งการแจ้งเตือน")
    categories = get_grades()  # ใช้เกรดมาตรฐาน (normalize แล้ว) สำหรับตั้ง alert
    cat_options = ["(ทุกหมวด)"] + categories

    with st.form("alert_form"):
        a_label = st.text_input("ชื่อ alert", placeholder="เช่น ปั้มราคาสูง")
        a_cat = st.selectbox("หมวดราคา", cat_options)
        a_thresh = st.number_input("ราคา threshold (บาท/กก.)", min_value=0.0, value=10.0, step=0.1, format="%.2f")
        a_dir = st.selectbox("เงื่อนไข", ["above", "below"],
                             format_func=lambda x: "สูงกว่า ↑" if x == "above" else "ต่ำกว่า ↓")
        if st.form_submit_button("➕ เพิ่ม Alert"):
            if a_label:
                add_alert(a_label, "" if a_cat == "(ทุกหมวด)" else a_cat, a_thresh, a_dir)
                st.success("เพิ่ม alert แล้ว!")
                st.rerun()

    st.subheader("Alerts ที่ตั้งไว้")
    alerts = get_alerts()
    if not alerts:
        st.caption("ยังไม่มี alert")
    for alert in alerts:
        c1, c2, c3 = st.columns([4, 1, 1])
        icon = "↑" if alert["direction"] == "above" else "↓"
        cat_label = alert["category"] or "ทุกหมวด"
        c1.markdown(f"**{alert['label']}**  \n{cat_label} {icon} {alert['threshold']:.2f}")
        new_state = c2.toggle("", value=alert["active"], key=f"t_{alert['id']}")
        if new_state != alert["active"]:
            toggle_alert(alert["id"], new_state)
            st.rerun()
        if c3.button("🗑️", key=f"d_{alert['id']}"):
            delete_alert(alert["id"])
            st.rerun()

    st.divider()
    if st.button("📥 โหลดข้อมูลตัวอย่าง"):
        add_demo_data()
        st.success("โหลดแล้ว! (90 วัน)")
        st.rerun()

# ══════════════════════════════════════════
# Load data
# ══════════════════════════════════════════
history = get_price_history(limit=2000)
latest = get_latest_prices()

if not history:
    st.title("🏗️ เศษเหล็ก Price Tracker")
    st.info("ยังไม่มีข้อมูล — กด **โหลดข้อมูลตัวอย่าง** ที่ sidebar ก่อนครับ")
    st.stop()

df = pd.DataFrame(history)
df["recorded_at"] = pd.to_datetime(df["recorded_at"])
df_latest = pd.DataFrame(latest)

# ══════════════════════════════════════════
# Header KPIs — ราคาล่าสุดแต่ละหมวด
# ══════════════════════════════════════════
st.title("🏗️ เศษเหล็ก Price Tracker")

if not df_latest.empty:
    cols = st.columns(len(df_latest))
    for col, (_, row) in zip(cols, df_latest.iterrows()):
        # หาราคาก่อนหน้า
        hist_cat = df[df["grade"] == row["grade"]]["price"]
        prev = hist_cat.iloc[-2] if len(hist_cat) > 1 else row["price"]
        delta = row["price"] - prev
        col.metric(
            label=row["grade"],
            value=f"{row['price']:.2f} ฿/กก.",
            delta=f"{delta:+.2f}",
            delta_color="inverse",   # ราคาลงสีเขียว (ดีสำหรับผู้ซื้อ)
        )

st.divider()

# ══════════════════════════════════════════
# Filters
# ══════════════════════════════════════════
f1, f2, f3 = st.columns([2, 2, 2])
all_cats = sorted(df["grade"].unique())
sel_cats = f1.multiselect("หมวดราคา", all_cats, default=all_cats)

all_companies = ["ทั้งหมด"] + sorted(df["company"].dropna().unique().tolist())
sel_company = f2.selectbox("บริษัท/แหล่ง", all_companies)

date_range = f3.date_input(
    "ช่วงวันที่",
    value=(df["recorded_at"].min().date(), df["recorded_at"].max().date()),
)

# apply filters
dff = df.copy()
if sel_cats:
    dff = dff[dff["grade"].isin(sel_cats)]
if sel_company != "ทั้งหมด":
    dff = dff[dff["company"] == sel_company]
if len(date_range) == 2:
    dff = dff[
        (dff["recorded_at"].dt.date >= date_range[0]) &
        (dff["recorded_at"].dt.date <= date_range[1])
    ]

# ══════════════════════════════════════════
# Charts
# ══════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs(["📉 แนวโน้มราคา", "📊 เปรียบเทียบหมวด", "🕯️ OHLC", "🗂️ ข้อมูลดิบ"])

with tab1:
    view_mode = st.radio(
        "มุมมอง",
        ["แยกตามโรงหลอม", "แยกตามเกรด", "รวมทุกเกรดทุกเตาหลอม"],
        horizontal=True,
        key="trend_view_mode",
    )

    if dff.empty:
        st.info("ไม่มีข้อมูลตามตัวกรองที่เลือก")
    elif view_mode == "แยกตามโรงหลอม":
        n_companies = dff["company"].dropna().nunique() or 1
        fig = px.line(
            dff.dropna(subset=["company"]), x="recorded_at", y="price", color="grade",
            facet_col="company", facet_col_wrap=2,
            title="แนวโน้มราคา แยกตามโรงหลอม",
            labels={"recorded_at": "วันที่", "price": "ราคา (฿/กก.)", "grade": "เกรด"},
            markers=True,
        )
        fig.update_yaxes(matches=None)
        fig.update_layout(height=320 * ((n_companies + 1) // 2), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    elif view_mode == "แยกตามเกรด":
        n_grades = dff["grade"].nunique() or 1
        fig = px.line(
            dff, x="recorded_at", y="price", color="company",
            facet_col="grade", facet_col_wrap=2,
            title="แนวโน้มราคา แยกตามเกรด",
            labels={"recorded_at": "วันที่", "price": "ราคา (฿/กก.)", "company": "โรงหลอม"},
            markers=True,
        )
        fig.update_yaxes(matches=None)
        fig.update_layout(height=320 * ((n_grades + 1) // 2), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    else:  # รวมทุกเกรดทุกเตาหลอม
        fig = px.line(
            dff, x="recorded_at", y="price", color="grade",
            title="แนวโน้มราคา รวมทุกเกรดทุกเตาหลอม",
            labels={"recorded_at": "วันที่", "price": "ราคา (฿/กก.)", "grade": "เกรด"},
            markers=True,
        )
        # วาดเส้น alert threshold
        for alert in get_alerts():
            if alert["active"] and (not alert["category"] or alert["category"] in sel_cats):
                color = "red" if alert["direction"] == "above" else "orange"
                fig.add_hline(
                    y=alert["threshold"], line_dash="dash", line_color=color,
                    annotation_text=alert["label"], annotation_position="top right",
                )
        fig.update_layout(height=480, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    # Bar chart ราคาล่าสุดเปรียบเทียบทุกหมวด
    if not df_latest.empty:
        df_bar = df_latest[df_latest["grade"].isin(sel_cats)] if sel_cats else df_latest
        fig2 = px.bar(
            df_bar.sort_values("price", ascending=True),
            x="price", y="grade", orientation="h",
            color="price", color_continuous_scale="RdYlGn_r",
            title="ราคาล่าสุด — เปรียบเทียบทุกเกรด",
            labels={"price": "ราคา (฿/กก.)", "grade": "เกรด"},
            text="price",
        )
        fig2.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig2.update_layout(height=380, coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    # Box plot การกระจายราคา
    fig3 = px.box(
        dff, x="grade", y="price", color="grade",
        title="การกระจายราคา (Box Plot)",
        labels={"price": "ราคา (฿/กก.)", "grade": "เกรด"},
    )
    fig3.update_layout(height=380, showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

with tab3:
    if sel_cats:
        cat_ohlc = st.selectbox("เลือกหมวดสำหรับ OHLC", sel_cats, key="ohlc_cat")
        df_ohlc = dff[dff["grade"] == cat_ohlc].set_index("recorded_at")["price"]
        ohlc = df_ohlc.resample("1D").ohlc().dropna()
        if ohlc.empty:
            st.info("ข้อมูลไม่เพียงพอ")
        else:
            fig4 = go.Figure(go.Candlestick(
                x=ohlc.index,
                open=ohlc["open"], high=ohlc["high"],
                low=ohlc["low"],  close=ohlc["close"],
                name=cat_ohlc,
            ))
            fig4.update_layout(
                title=f"OHLC รายวัน — {cat_ohlc}",
                xaxis_title="วันที่", yaxis_title="ราคา (฿/กก.)",
                height=450,
            )
            st.plotly_chart(fig4, use_container_width=True)

with tab4:
    show_df = dff[["recorded_at", "company", "price_date", "grade", "category", "price", "sender"]].copy()
    show_df.columns = ["บันทึกเมื่อ", "โรงหลอม", "วันที่ในข้อความ", "เกรด (มาตรฐาน)", "ชื่อที่โรงเรียก", "ราคา (฿/กก.)", "ผู้ส่ง"]
    show_df = show_df.sort_values("บันทึกเมื่อ", ascending=False).head(300)
    st.dataframe(show_df, use_container_width=True, hide_index=True)

    csv = show_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("⬇️ ดาวน์โหลด CSV", csv, "scrap_prices.csv", "text/csv")

st.caption("🔄 กด R หรือรีโหลดหน้าเพื่ออัปเดตข้อมูลล่าสุด")
