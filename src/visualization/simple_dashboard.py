"""
Fraud Detection System - Simple Dashboard
Real-time fraud monitoring and analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.database.connection import db

# Page configuration
st.set_page_config(
    page_title="Fraud Detection Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def load_overview_stats():
    """Load overview statistics"""
    query = """
    SELECT 
        COUNT(*) as total_transactions,
        SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) as fraud_transactions,
        COUNT(DISTINCT account_id) as total_accounts,
        SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END)::FLOAT / COUNT(*)::FLOAT * 100 as fraud_rate,
        SUM(transaction_amount) as total_amount,
        AVG(transaction_amount) as avg_amount
    FROM transaction
    """
    return db.execute_query(query)[0]


@st.cache_data(ttl=60)
def load_high_risk_accounts():
    """Load high risk accounts"""
    query = """
    SELECT 
        a.account_id,
        a.total_transactions,
        COUNT(CASE WHEN t.is_fraud THEN 1 END) as fraud_transactions,
        a.total_amount,
        COALESCE(SUM(CASE WHEN t.is_fraud THEN t.transaction_amount ELSE 0 END), 0) as fraud_amount,
        COALESCE(COUNT(CASE WHEN t.is_fraud THEN 1 END)::FLOAT / NULLIF(a.total_transactions, 0), 0) as fraud_rate,
        a.risk_score
    FROM account a
    LEFT JOIN transaction t ON a.account_id = t.account_id
    WHERE a.risk_score > 0.5
    GROUP BY a.account_id, a.total_transactions, a.total_amount, a.risk_score
    ORDER BY a.risk_score DESC
    LIMIT 20
    """
    return pd.DataFrame(db.execute_query(query))


@st.cache_data(ttl=60)
def load_fraud_trends():
    """Load fraud trends over time"""
    query = """
    SELECT 
        transaction_date::date as date,
        COUNT(*) as total_transactions,
        SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) as fraud_transactions,
        SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END)::FLOAT / COUNT(*)::FLOAT * 100 as fraud_rate
    FROM transaction
    GROUP BY transaction_date::date
    ORDER BY transaction_date::date
    """
    return pd.DataFrame(db.execute_query(query))


@st.cache_data(ttl=60)
def load_merchant_stats():
    """Load merchant statistics"""
    query = """
    SELECT 
        m.merchant_id,
        m.total_transactions,
        m.total_fraud_transactions as fraud_transactions,
        COALESCE(SUM(t.transaction_amount), 0) as total_amount,
        COALESCE(SUM(CASE WHEN t.is_fraud THEN t.transaction_amount ELSE 0 END), 0) as fraud_amount,
        m.fraud_rate
    FROM merchant m
    LEFT JOIN transaction t ON m.merchant_id = t.merchant_id
    GROUP BY m.merchant_id, m.total_transactions, m.total_fraud_transactions, m.fraud_rate
    ORDER BY m.fraud_rate DESC
    """
    return pd.DataFrame(db.execute_query(query))


@st.cache_data(ttl=60)
def load_device_sharing():
    """Load device sharing statistics"""
    query = """
    SELECT 
        d.device_id,
        d.total_users as shared_accounts,
        d.total_transactions,
        d.fraud_transactions,
        d.fraud_rate,
        d.is_shared as is_suspicious
    FROM device d
    WHERE d.total_users > 1
    ORDER BY d.fraud_rate DESC
    LIMIT 20
    """
    return pd.DataFrame(db.execute_query(query))


def load_transaction_details(account_id=None, transaction_id=None):
    """Load transaction details"""
    if transaction_id:
        query = f"""
        SELECT 
            t.*,
            a.total_transactions as account_total_txn,
            a.fraud_rate as account_fraud_rate,
            a.risk_score,
            m.fraud_rate as merchant_fraud_rate
        FROM transaction t
        JOIN account a ON t.account_id = a.account_id
        JOIN merchant m ON t.merchant_id = m.merchant_id
        WHERE t.transaction_id = {transaction_id}
        """
    elif account_id:
        query = f"""
        SELECT 
            t.*,
            m.fraud_rate as merchant_fraud_rate
        FROM transaction t
        JOIN merchant m ON t.merchant_id = m.merchant_id
        WHERE t.account_id = {account_id}
        ORDER BY t.transaction_date DESC
        LIMIT 50
        """
    else:
        return pd.DataFrame()
    
    return pd.DataFrame(db.execute_query(query))


# Main header
st.markdown('<h1 class="main-header">🔍 Fraud Detection System</h1>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Page", [
    "📊 Overview",
    "⚠️ High-Risk Accounts",
    "📈 Fraud Trends",
    "🏪 Merchant Analysis",
    "🖥️ Device Sharing",
    "🔎 Transaction Search"
])

st.sidebar.markdown("---")
st.sidebar.markdown("### Settings")
auto_refresh = st.sidebar.checkbox("Auto Refresh (60s)", value=False)

if auto_refresh:
    import time
    time.sleep(1)
    st.rerun()


# Page routing
if page == "📊 Overview":
    st.header("System Overview")
    
    # Load data
    stats = load_overview_stats()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Transactions", f"{stats['total_transactions']:,}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Fraud Cases", f"{stats['fraud_transactions']:,}", 
                 delta=f"{stats['fraud_rate']:.2f}% fraud rate", delta_color="inverse")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Accounts", f"{stats['total_accounts']:,}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Amount", f"${stats['total_amount']:,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Transaction Distribution")
        fig = go.Figure(data=[go.Pie(
            labels=['Legitimate', 'Fraud'],
            values=[stats['total_transactions'] - stats['fraud_transactions'], 
                   stats['fraud_transactions']],
            hole=0.4,
            marker=dict(colors=['#2ecc71', '#e74c3c'])
        )])
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Amount Statistics")
        amounts = pd.DataFrame({
            'Metric': ['Total Amount', 'Average Amount'],
            'Value': [stats['total_amount'], stats['avg_amount']]
        })
        fig = px.bar(amounts, x='Metric', y='Value', 
                    color='Metric', color_discrete_sequence=['#3498db', '#9b59b6'])
        fig.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig, use_container_width=True)


elif page == "⚠️ High-Risk Accounts":
    st.header("High-Risk Accounts")
    
    df = load_high_risk_accounts()
    
    if not df.empty:
        st.dataframe(
            df.style.background_gradient(subset=['risk_score'], cmap='Reds'),
            use_container_width=True,
            height=500
        )
        
        # Risk score distribution
        st.subheader("Risk Score Distribution")
        fig = px.histogram(df, x='risk_score', nbins=20,
                          title="Distribution of Risk Scores",
                          labels={'risk_score': 'Risk Score'},
                          color_discrete_sequence=['#e74c3c'])
        st.plotly_chart(fig, use_container_width=True)
        
        # Top risky accounts
        st.subheader("Top 10 Riskiest Accounts")
        top10 = df.head(10)
        fig = px.bar(top10, x='account_id', y='risk_score',
                    color='fraud_rate',
                    labels={'account_id': 'Account ID', 'risk_score': 'Risk Score'},
                    color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No high-risk accounts found.")


elif page == "📈 Fraud Trends":
    st.header("Fraud Trends Over Time")
    
    df = load_fraud_trends()
    
    if not df.empty:
        # Fraud rate over time
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['fraud_rate'],
                      name="Fraud Rate (%)", line=dict(color='#e74c3c', width=3)),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Bar(x=df['date'], y=df['total_transactions'],
                  name="Total Transactions", marker=dict(color='#3498db', opacity=0.5)),
            secondary_y=True
        )
        
        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="Fraud Rate (%)", secondary_y=False)
        fig.update_yaxes(title_text="Total Transactions", secondary_y=True)
        fig.update_layout(height=500, hovermode='x unified')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Average Fraud Rate", f"{df['fraud_rate'].mean():.2f}%")
        with col2:
            st.metric("Max Fraud Rate", f"{df['fraud_rate'].max():.2f}%")
        with col3:
            st.metric("Total Days", len(df))
    else:
        st.info("No trend data available.")


elif page == "🏪 Merchant Analysis":
    st.header("Merchant Analysis")
    
    df = load_merchant_stats()
    
    if not df.empty:
        st.dataframe(
            df.style.background_gradient(subset=['fraud_rate'], cmap='Reds'),
            use_container_width=True,
            height=400
        )
        
        # Merchant fraud comparison
        st.subheader("Merchant Fraud Comparison")
        fig = px.scatter(df, x='total_transactions', y='fraud_rate',
                        size='total_amount', hover_data=['merchant_id'],
                        labels={'total_transactions': 'Total Transactions',
                               'fraud_rate': 'Fraud Rate (%)'},
                        color='fraud_rate',
                        color_continuous_scale='Reds')
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No merchant data available.")


elif page == "🖥️ Device Sharing":
    st.header("Suspicious Device Sharing")
    
    df = load_device_sharing()
    
    if not df.empty:
        st.dataframe(
            df.style.background_gradient(subset=['fraud_rate'], cmap='Reds'),
            use_container_width=True,
            height=400
        )
        
        # Device sharing visualization
        st.subheader("Device Sharing vs Fraud Rate")
        fig = px.scatter(df, x='shared_accounts', y='fraud_rate',
                        size='total_transactions',
                        hover_data=['device_id'],
                        labels={'shared_accounts': 'Number of Shared Accounts',
                               'fraud_rate': 'Fraud Rate (%)'},
                        color='is_suspicious',
                        color_discrete_map={True: '#e74c3c', False: '#3498db'})
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No device sharing data available.")


elif page == "🔎 Transaction Search":
    st.header("Transaction Search")
    
    search_type = st.radio("Search by:", ["Account ID", "Transaction ID"])
    
    if search_type == "Account ID":
        account_id = st.number_input("Enter Account ID:", min_value=1, step=1)
        if st.button("Search"):
            df = load_transaction_details(account_id=account_id)
            if not df.empty:
                st.subheader(f"Transactions for Account {account_id}")
                st.dataframe(
                    df.style.apply(lambda x: ['background-color: #ffebee' 
                                              if x['is_fraud'] else '' for i in x], axis=1),
                    use_container_width=True,
                    height=500
                )
                
                # Account summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Transactions", len(df))
                with col2:
                    st.metric("Fraud Count", df['is_fraud'].sum())
                with col3:
                    st.metric("Total Amount", f"${df['transaction_amount'].sum():,.2f}")
            else:
                st.warning(f"No transactions found for Account ID {account_id}")
    
    else:
        transaction_id = st.number_input("Enter Transaction ID:", min_value=1, step=1)
        if st.button("Search"):
            df = load_transaction_details(transaction_id=transaction_id)
            if not df.empty:
                st.subheader("Transaction Details")
                
                row = df.iloc[0]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### Basic Information")
                    st.write(f"**Transaction ID:** {row['transaction_id']}")
                    st.write(f"**Account ID:** {row['account_id']}")
                    st.write(f"**Merchant ID:** {row['merchant_id']}")
                    st.write(f"**Device ID:** {row['device_id']}")
                    st.write(f"**Date:** {row['transaction_date']}")
                    
                with col2:
                    st.markdown("### Transaction Details")
                    st.write(f"**Amount:** ${row['transaction_amount']:,.2f}")
                    st.write(f"**Fraud Status:** {'⚠️ FRAUD' if row['is_fraud'] else '✅ Legitimate'}")
                    st.write(f"**Account Risk Score:** {row['risk_score']:.4f}")
                    st.write(f"**Account Fraud Rate:** {row['account_fraud_rate']*100:.2f}%")
                    st.write(f"**Merchant Fraud Rate:** {row['merchant_fraud_rate']*100:.2f}%")
                
                if row['is_fraud']:
                    st.error("⚠️ This transaction is flagged as FRAUD")
                else:
                    st.success("✅ This transaction appears legitimate")
            else:
                st.warning(f"Transaction ID {transaction_id} not found")


# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d;'>
    <p>Fraud Detection System | Powered by Graph Neural Networks</p>
</div>
""", unsafe_allow_html=True)
