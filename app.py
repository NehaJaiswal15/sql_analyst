# app.py
import streamlit as st
from agent import load_agent, ask
from tools import load_csv_to_db, get_all_tables, get_table_stats
import sqlite3
import pandas as pd
import plotly.express as px

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="SQL Analyst",
    page_icon="🛒",
    layout="wide"
)

st.title("SQL Data Analyst")
st.caption("Ask anything about your data in plain English")

# ── Load Agent ────────────────────────────────────────────────
if "agent" not in st.session_state:
    with st.spinner("🔄 Loading AI agent..."):
        st.session_state.agent = load_agent()
        st.session_state.history = []
        st.session_state.uploaded_tables = []

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:

    # CSV Upload
    st.header("📤 Upload Your CSV")
    uploaded_file = st.file_uploader("Upload any CSV to query it", type=["csv"])

    if uploaded_file:
        custom_name = st.text_input(
            "Table name",
            placeholder="e.g. sales_2024, flipkart_data",
            help="Give your table a clear name. Leave blank to use filename."
        )
        if st.button("Load into Database", use_container_width=True, type="primary"):
            with st.spinner("Loading CSV..."):
                success, table_name, message = load_csv_to_db(uploaded_file, custom_name)
                st.write(message)
                if success:
                    st.session_state.agent = load_agent(get_all_tables())
                    st.session_state.uploaded_tables.append(table_name)
                    st.session_state.active_table = table_name
                    st.success(f"Agent updated! You can now ask about `{table_name}`")

    # Active Tables
    st.divider()
    st.header("🗄️ Active Tables")
    for t in get_all_tables():
        st.badge(t)

    st.divider()

    # Example Questions
    st.header("💡 Try These Questions")
    examples = [
        "How many products are in the database?",
        "What is the highest rated product?",
        "Which main category has the most products?",
        "What is the average discounted price?",
        "Show top 5 most reviewed products",
        "Which products have more than 50% discount?",
        "What is the average rating per main category?",
        "Which product has the highest discount percentage?"
    ]
    for q in examples:
        if st.button(q, use_container_width=True):
            st.session_state.pending_q = q

    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.history = []
        st.rerun()

# ── Table Selector ────────────────────────────────────────────
all_tables = get_all_tables()

if "active_table" not in st.session_state:
    st.session_state.active_table = "products" if "products" in all_tables else all_tables[0]

selected_table = st.selectbox(
    "📋 Showing stats for:",
    options=all_tables,
    index=all_tables.index(st.session_state.active_table)
    if st.session_state.active_table in all_tables else 0
)
st.session_state.active_table = selected_table

# ── Dynamic Stats ─────────────────────────────────────────────
stats = get_table_stats(selected_table)

if "error" not in stats:
    col1, col2 = st.columns(2)
    col1.metric("📦 Total Rows",    stats["rows"])
    col2.metric("📊 Total Columns", stats["columns"])

    if stats["metrics"]:
        metric_cols = st.columns(len(stats["metrics"]))
        for i, (col_name, avg_val) in enumerate(stats["metrics"].items()):
            metric_cols[i].metric(
                f"Avg {col_name.replace('_', ' ').title()}", avg_val
            )
else:
    st.warning(f"Could not load stats: {stats['error']}")

st.divider()

# ── Charts ────────────────────────────────────────────────────
with st.expander("📊 Data Overview Charts", expanded=False):
    conn = sqlite3.connect("data/amazon.db")

    if selected_table == "products":
        c1, c2 = st.columns(2)

        cat_df = pd.read_sql(
            "SELECT main_category, COUNT(*) as count FROM products "
            "GROUP BY main_category ORDER BY count DESC LIMIT 10", conn
        )
        c1.plotly_chart(
            px.bar(cat_df, x="main_category", y="count",
                   title="Products per Category", color="count",
                   color_continuous_scale="Blues"),
            use_container_width=True
        )

        rating_df = pd.read_sql(
            "SELECT main_category, ROUND(AVG(rating),2) as avg_rating FROM products "
            "GROUP BY main_category ORDER BY avg_rating DESC LIMIT 10", conn
        )
        c2.plotly_chart(
            px.bar(rating_df, x="main_category", y="avg_rating",
                   title="Avg Rating per Category", color="avg_rating",
                   color_continuous_scale="Greens"),
            use_container_width=True
        )

    else:
        # Generic charts for any uploaded table
        stats_df = pd.read_sql(f"SELECT * FROM [{selected_table}] LIMIT 500", conn)
        numeric_cols = stats_df.select_dtypes(include='number').columns.tolist()
        text_cols    = stats_df.select_dtypes(include='object').columns.tolist()

        if numeric_cols and text_cols:
            c1, c2 = st.columns(2)

            c1.plotly_chart(
                px.histogram(stats_df, x=numeric_cols[0],
                             title=f"Distribution of {numeric_cols[0]}",
                             color_discrete_sequence=["#636EFA"]),
                use_container_width=True
            )

            grp = stats_df.groupby(text_cols[0])[numeric_cols[0]].mean().reset_index()
            grp = grp.sort_values(numeric_cols[0], ascending=False).head(10)
            c2.plotly_chart(
                px.bar(grp, x=text_cols[0], y=numeric_cols[0],
                       title=f"Avg {numeric_cols[0]} by {text_cols[0]}",
                       color=numeric_cols[0],
                       color_continuous_scale="Purples"),
                use_container_width=True
            )
        else:
            st.info("Upload a CSV with both text and numeric columns for auto charts.")

    conn.close()

# ── Chat History ──────────────────────────────────────────────
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant" and msg.get("sql"):
            with st.expander("🔍 SQL Query Used"):
                st.code(msg["sql"], language="sql")

# ── Chat Input ────────────────────────────────────────────────
question = None

if "pending_q" in st.session_state:
    question = st.session_state.pop("pending_q")

typed_q = st.chat_input("Ask a question about your data...")
if typed_q:
    question = typed_q

# ── Process Question ──────────────────────────────────────────
if question:
    st.session_state.history.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            answer, sql = ask(st.session_state.agent, question)
        st.write(answer)
        if sql:
            with st.expander("🔍 SQL Query Used"):
                st.code(sql, language="sql")

    st.session_state.history.append({
        "role": "assistant",
        "content": answer,
        "sql": sql
    })