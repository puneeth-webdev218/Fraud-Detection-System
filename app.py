"""
Fraud Detection System - Standalone Demo Dashboard
No database required - uses synthetic data for demonstration
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

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
        border-left: 4px solid #1f77b4;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        margin-top: 0.5rem;
    }
    .fraud-alert {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #ffe6e6;
        border-left: 4px solid #ff0000;
        color: #cc0000;
        margin-bottom: 1rem;
    }
    .success-badge {
        padding: 0.3rem 0.6rem;
        border-radius: 0.3rem;
        background-color: #d4edda;
        color: #155724;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def generate_synthetic_data():
    """Generate realistic synthetic transaction data"""
    np.random.seed(42)
    
    # Generate base data
    n_transactions = 5000
    n_accounts = 200
    n_merchants = 100
    n_devices = 150
    
    dates = [datetime.now() - timedelta(days=x) for x in range(30)]
    
    transactions = {
        'transaction_id': range(1, n_transactions + 1),
        'account_id': np.random.randint(1, n_accounts + 1, n_transactions),
        'merchant_id': np.random.randint(1, n_merchants + 1, n_transactions),
        'device_id': np.random.randint(1, n_devices + 1, n_transactions),
        'transaction_amount': np.random.lognormal(3.5, 1.5, n_transactions),
        'transaction_date': [dates[np.random.randint(0, len(dates))] for _ in range(n_transactions)],
        'merchant_category': np.random.choice(['Grocery', 'Gas Station', 'Restaurant', 'Online', 'Retail'], n_transactions),
        'location': np.random.choice(['NYC', 'LA', 'Chicago', 'Houston', 'Phoenix'], n_transactions),
    }
    
    # Fraud labels (5% fraud rate)
    is_fraud = np.random.binomial(1, 0.05, n_transactions).astype(bool)
    
    # Add fraud patterns
    for idx in np.where(is_fraud)[0]:
        transactions['transaction_amount'][idx] *= np.random.uniform(2, 5)
    
    transactions['is_fraud'] = is_fraud
    
    df = pd.DataFrame(transactions)
    df['fraud_probability'] = np.random.random(n_transactions)
    
    # Bias fraud probability towards actual fraud
    df.loc[df['is_fraud'], 'fraud_probability'] = np.random.uniform(0.6, 1.0, sum(is_fraud))
    df.loc[~df['is_fraud'], 'fraud_probability'] = np.random.uniform(0.0, 0.4, sum(~is_fraud))
    
    return df


@st.cache_data(ttl=60)
def load_overview_stats(df):
    """Load overview statistics"""
    total_transactions = len(df)
    fraud_transactions = df['is_fraud'].sum()
    fraud_rate = (fraud_transactions / total_transactions) * 100
    total_amount = df['transaction_amount'].sum()
    avg_amount = df['transaction_amount'].mean()
    high_risk_accounts = len(df[df['fraud_probability'] > 0.6]['account_id'].unique())
    
    return {
        'total_transactions': total_transactions,
        'fraud_transactions': fraud_transactions,
        'fraud_rate': fraud_rate,
        'total_amount': total_amount,
        'avg_amount': avg_amount,
        'high_risk_accounts': high_risk_accounts,
    }


@st.cache_data(ttl=60)
def load_high_risk_accounts(df):
    """Load high risk accounts"""
    account_fraud = df.groupby('account_id').agg({
        'transaction_id': 'count',
        'is_fraud': 'sum',
        'transaction_amount': ['sum', 'mean'],
        'fraud_probability': 'mean'
    }).reset_index()
    
    account_fraud.columns = ['account_id', 'total_transactions', 'fraud_count', 
                            'total_amount', 'avg_amount', 'avg_fraud_prob']
    account_fraud['fraud_rate'] = (account_fraud['fraud_count'] / account_fraud['total_transactions'] * 100).round(2)
    
    return account_fraud.nlargest(20, 'avg_fraud_prob')


@st.cache_data(ttl=60)
def load_fraud_trends(df):
    """Load fraud trends over time"""
    daily_fraud = df.groupby(df['transaction_date'].dt.date).agg({
        'transaction_id': 'count',
        'is_fraud': 'sum',
        'transaction_amount': 'sum'
    }).reset_index()
    
    daily_fraud.columns = ['date', 'total_transactions', 'fraud_count', 'total_amount']
    daily_fraud['fraud_rate'] = (daily_fraud['fraud_count'] / daily_fraud['total_transactions'] * 100).round(2)
    
    return daily_fraud


@st.cache_data(ttl=60)
def load_merchant_stats(df):
    """Load merchant statistics"""
    merchant_fraud = df.groupby('merchant_id').agg({
        'transaction_id': 'count',
        'is_fraud': 'sum',
        'transaction_amount': 'sum',
        'fraud_probability': 'mean'
    }).reset_index()
    
    merchant_fraud.columns = ['merchant_id', 'transaction_count', 'fraud_count', 'total_amount', 'avg_fraud_prob']
    merchant_fraud['fraud_rate'] = (merchant_fraud['fraud_count'] / merchant_fraud['transaction_count'] * 100).round(2)
    
    return merchant_fraud.nlargest(15, 'fraud_rate')


@st.cache_data(ttl=60)
def load_category_stats(df):
    """Load category statistics"""
    category_fraud = df.groupby('merchant_category').agg({
        'transaction_id': 'count',
        'is_fraud': 'sum',
        'transaction_amount': ['sum', 'mean']
    }).reset_index()
    
    category_fraud.columns = ['category', 'count', 'fraud_count', 'total_amount', 'avg_amount']
    category_fraud['fraud_rate'] = (category_fraud['fraud_count'] / category_fraud['count'] * 100).round(2)
    
    return category_fraud


# Main app
def main():
    # Title
    st.markdown("## 🔍 Fraud Detection System - Analytics Dashboard")
    st.markdown("---")
    
    # Load data
    df = generate_synthetic_data()
    stats = load_overview_stats(df)
    
    # Overview Metrics
    st.subheader("📊 Overview Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="Total Transactions",
            value=f"{stats['total_transactions']:,}",
            delta="All Time"
        )
    
    with col2:
        st.metric(
            label="Fraudulent Transactions",
            value=f"{stats['fraud_transactions']:,}",
            delta=f"{stats['fraud_rate']:.2f}%",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="Fraud Rate",
            value=f"{stats['fraud_rate']:.2f}%",
            delta=None
        )
    
    with col4:
        st.metric(
            label="Total Amount",
            value=f"${stats['total_amount']:,.0f}",
            delta=None
        )
    
    with col5:
        st.metric(
            label="High-Risk Accounts",
            value=f"{stats['high_risk_accounts']}",
            delta="Above 60% Risk"
        )
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📈 Fraud Trends", "🚨 High-Risk Accounts", "🏪 Merchant Analysis", "📍 Location Insights", "🎯 Recent Alerts"]
    )
    
    with tab1:
        st.subheader("Fraud Trends Over Time")
        
        fraud_trends = load_fraud_trends(df)
        
        # Create fraud trend chart
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Scatter(
                x=fraud_trends['date'],
                y=fraud_trends['total_transactions'],
                name='Total Transactions',
                mode='lines',
                line=dict(color='#1f77b4', width=2),
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=fraud_trends['date'],
                y=fraud_trends['fraud_rate'],
                name='Fraud Rate (%)',
                mode='lines+markers',
                line=dict(color='#ff7f0e', width=2),
                marker=dict(size=6)
            ),
            secondary_y=True
        )
        
        fig.update_layout(
            title="Transaction Volume and Fraud Rate Trends",
            hovermode='x unified',
            height=400,
        )
        
        fig.update_yaxes(title_text="Total Transactions", secondary_y=False)
        fig.update_yaxes(title_text="Fraud Rate (%)", secondary_y=True)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistics table
        st.subheader("Daily Statistics")
        st.dataframe(
            fraud_trends.sort_values('date', ascending=False),
            use_container_width=True,
            hide_index=True
        )
    
    with tab2:
        st.subheader("High-Risk Accounts (Sorted by Fraud Risk)")
        
        high_risk = load_high_risk_accounts(df)
        
        # Display high-risk accounts
        for idx, row in high_risk.head(10).iterrows():
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            
            with col1:
                st.metric(f"Account {int(row['account_id'])}", 
                         f"{row['avg_fraud_prob']:.1%}",
                         "Risk Score")
            
            with col2:
                st.metric("Transactions", int(row['total_transactions']))
            
            with col3:
                st.metric("Fraud Count", int(row['fraud_count']))
            
            with col4:
                st.metric("Fraud Rate", f"{row['fraud_rate']:.1f}%")
        
        st.subheader("All High-Risk Accounts")
        st.dataframe(
            high_risk,
            use_container_width=True,
            hide_index=True
        )
    
    with tab3:
        st.subheader("Merchant Fraud Statistics")
        
        merchant_stats = load_merchant_stats(df)
        
        # Merchant fraud rate chart
        fig = px.bar(
            merchant_stats,
            x='merchant_id',
            y='fraud_rate',
            color='fraud_rate',
            color_continuous_scale='Reds',
            title='Fraud Rate by Merchant',
            labels={'merchant_id': 'Merchant ID', 'fraud_rate': 'Fraud Rate (%)'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Category analysis
        st.subheader("Fraud by Category")
        
        category_stats = load_category_stats(df)
        
        fig = px.pie(
            category_stats,
            values='count',
            names='category',
            title='Transaction Distribution by Category',
            hole=0.4
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Category fraud rates
        st.subheader("Category Fraud Rates")
        st.dataframe(
            category_stats.sort_values('fraud_rate', ascending=False),
            use_container_width=True,
            hide_index=True
        )
    
    with tab4:
        st.subheader("Geographic Analysis")
        
        # Location fraud stats
        location_fraud = df.groupby('location').agg({
            'transaction_id': 'count',
            'is_fraud': 'sum',
            'transaction_amount': 'sum',
            'fraud_probability': 'mean'
        }).reset_index()
        
        location_fraud.columns = ['location', 'transaction_count', 'fraud_count', 'total_amount', 'avg_fraud_prob']
        location_fraud['fraud_rate'] = (location_fraud['fraud_count'] / location_fraud['transaction_count'] * 100).round(2)
        
        # Fraud by location
        fig = px.bar(
            location_fraud,
            x='location',
            y='fraud_rate',
            color='fraud_count',
            title='Fraud Rate by Location',
            labels={'location': 'Location', 'fraud_rate': 'Fraud Rate (%)'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Location statistics
        st.subheader("Location Statistics")
        st.dataframe(
            location_fraud.sort_values('fraud_rate', ascending=False),
            use_container_width=True,
            hide_index=True
        )
    
    with tab5:
        st.subheader("Recent Fraud Alerts")
        
        # Get recent high-risk transactions
        recent_alerts = df[df['fraud_probability'] > 0.7].sort_values('transaction_date', ascending=False).head(20)
        
        if len(recent_alerts) > 0:
            for idx, row in recent_alerts.iterrows():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    alert_text = f"🚨 **Transaction #{int(row['transaction_id'])}** - Account {int(row['account_id'])} → {row['merchant_category']}"
                    if row['is_fraud']:
                        st.markdown(f"<div style='background-color: #ffe6e6; padding: 0.5rem; border-radius: 0.3rem; color: #cc0000;'>{alert_text} ⚠️ CONFIRMED FRAUD</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='background-color: #fff3cd; padding: 0.5rem; border-radius: 0.3rem; color: #856404;'>{alert_text}</div>", unsafe_allow_html=True)
                
                with col2:
                    st.metric("Amount", f"${row['transaction_amount']:.2f}")
                
                with col3:
                    st.metric("Risk", f"{row['fraud_probability']:.1%}")
                
                with col4:
                    st.metric("Date", row['transaction_date'].strftime('%m/%d'))
        else:
            st.info("No high-risk transactions detected recently.")


if __name__ == "__main__":
    main()
