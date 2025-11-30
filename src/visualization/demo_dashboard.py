"""
Fraud Detection System - Interactive Dashboard
Real-time fraud monitoring and analytics with demo data
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta

# Page configuration with sidebar
st.set_page_config(
    page_title="Fraud Detection Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced styling
st.markdown("""
<style>
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1a1a1a;
        color: white;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: white;
    }
    
    /* Main content styling */
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 0.8rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Section styling */
    .section-header {
        font-size: 1.8rem;
        color: #1f77b4;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    
    /* Alert styling */
    .alert-high {
        background-color: #ffebee;
        color: #c62828;
        padding: 1rem;
        border-left: 4px solid #c62828;
        border-radius: 0.4rem;
    }
    
    .alert-medium {
        background-color: #fff3e0;
        color: #e65100;
        padding: 1rem;
        border-left: 4px solid #e65100;
        border-radius: 0.4rem;
    }
    
    .alert-low {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 1rem;
        border-left: 4px solid #2e7d32;
        border-radius: 0.4rem;
    }
</style>
""", unsafe_allow_html=True)


# Generate synthetic data for demo
@st.cache_data
def generate_demo_data(n_transactions=5000):
    """
    Generate realistic demo data
    
    Args:
        n_transactions: Total number of transactions to generate
    """
    np.random.seed(42)
    
    n_accounts = min(200, max(10, n_transactions // 25))  # ~25 txn per account
    n_merchants = min(100, max(10, n_transactions // 50))  # ~50 txn per merchant
    n_devices = min(150, max(10, n_transactions // 33))    # ~33 txn per device
    
    # Transactions
    dates = [datetime.now() - timedelta(days=np.random.randint(0, 365)) 
             for _ in range(n_transactions)]
    
    transactions = pd.DataFrame({
        'transaction_id': range(1, n_transactions + 1),
        'account_id': np.random.randint(1, n_accounts + 1, n_transactions),
        'merchant_id': np.random.randint(1, n_merchants + 1, n_transactions),
        'device_id': np.random.randint(1, n_devices + 1, n_transactions),
        'transaction_amount': np.random.lognormal(3.5, 1.5, n_transactions),
        'transaction_date': dates,
    })
    
    # Fraud labels (5% fraud rate)
    is_fraud = np.random.binomial(1, 0.05, n_transactions).astype(bool)
    
    # Fraudulent transactions tend to be larger
    fraud_indices = np.where(is_fraud)[0]
    for idx in fraud_indices:
        transactions.loc[idx, 'transaction_amount'] *= np.random.uniform(2, 5)
    
    transactions['is_fraud'] = is_fraud
    
    return transactions


@st.cache_data
def generate_full_demo_data():
    """Generate full demo dataset (5000 transactions)"""
    return generate_demo_data(n_transactions=5000)


def get_overview_stats(df):
    """Calculate overview statistics"""
    return {
        'total_transactions': len(df),
        'fraud_transactions': df['is_fraud'].sum(),
        'fraud_rate': (df['is_fraud'].sum() / len(df)) * 100,
        'total_accounts': df['account_id'].nunique(),
        'total_amount': df['transaction_amount'].sum(),
        'avg_amount': df['transaction_amount'].mean(),
    }


def get_high_risk_accounts(df):
    """Identify high-risk accounts"""
    account_stats = df.groupby('account_id').agg({
        'transaction_id': 'count',
        'is_fraud': ['sum', 'mean'],
        'transaction_amount': ['sum', 'mean']
    }).round(2)
    
    account_stats.columns = ['total_transactions', 'fraud_transactions', 
                            'fraud_rate', 'total_amount', 'avg_amount']
    
    # Calculate risk score
    account_stats['risk_score'] = (
        account_stats['fraud_rate'] * 0.5 + 
        (account_stats['avg_amount'] / account_stats['avg_amount'].max()) * 0.3 +
        (account_stats['fraud_transactions'] / account_stats['fraud_transactions'].max()) * 0.2
    )
    
    return account_stats.sort_values('risk_score', ascending=False)


def get_fraud_trends(df):
    """Get fraud trends over time"""
    daily_stats = df.groupby(df['transaction_date'].dt.date).agg({
        'transaction_id': 'count',
        'is_fraud': 'sum',
        'transaction_amount': 'sum'
    }).reset_index()
    
    daily_stats.columns = ['date', 'total_transactions', 'fraud_count', 'total_amount']
    daily_stats['fraud_rate'] = (daily_stats['fraud_count'] / daily_stats['total_transactions'] * 100).round(2)
    
    return daily_stats.sort_values('date')


def get_merchant_analysis(df):
    """Get merchant statistics"""
    merchant_stats = df.groupby('merchant_id').agg({
        'transaction_id': 'count',
        'is_fraud': ['sum', 'mean'],
        'transaction_amount': ['sum', 'mean']
    }).round(2)
    
    merchant_stats.columns = ['total_transactions', 'fraud_transactions', 
                             'fraud_rate', 'total_amount', 'avg_amount']
    
    return merchant_stats.sort_values('fraud_rate', ascending=False)


def get_device_analysis(df):
    """Get device statistics"""
    device_stats = df.groupby('device_id').agg({
        'account_id': 'nunique',
        'transaction_id': 'count',
        'is_fraud': ['sum', 'mean'],
        'transaction_amount': 'mean'
    }).round(2)
    
    device_stats.columns = ['num_accounts', 'total_transactions', 
                           'fraud_transactions', 'fraud_rate', 'avg_amount']
    
    device_stats['is_suspicious'] = device_stats['num_accounts'] > 3
    
    return device_stats.sort_values('fraud_rate', ascending=False)


# Load demo data
transactions = generate_demo_data()

# Main header
st.markdown('<h1 class="main-header">🔍 Fraud Detection System</h1>', unsafe_allow_html=True)
st.markdown("**Real-time Fraud Monitoring & Analytics**")
st.markdown("---")

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================
st.sidebar.image("https://via.placeholder.com/300x100/667eea/ffffff?text=Fraud+Detection", 
                 use_column_width=True)
st.sidebar.title("📍 Navigation")
st.sidebar.markdown("---")

# ============================================================================
# DATA LOADING CONTROLS
# ============================================================================
st.sidebar.markdown("### 📊 Data Loading")
st.sidebar.markdown("**Select number of transactions to load:**")

# Create columns for input and button
col_input, col_info = st.sidebar.columns([3, 1])

with col_input:
    # Preset options
    preset_selected = st.selectbox(
        "Quick Load Options:",
        ["Custom", "100 Transactions", "500 Transactions", "1,000 Transactions", 
         "5,000 Transactions (Full)", "10,000 Transactions"],
        label_visibility="collapsed"
    )
    
    # Map preset to number
    preset_map = {
        "100 Transactions": 100,
        "500 Transactions": 500,
        "1,000 Transactions": 1000,
        "5,000 Transactions (Full)": 5000,
        "10,000 Transactions": 10000
    }
    
    if preset_selected in preset_map:
        n_transactions = preset_map[preset_selected]
    else:
        # Custom input
        n_transactions = st.number_input(
            "Enter custom count:",
            min_value=10,
            max_value=50000,
            value=1000,
            step=100,
            label_visibility="collapsed"
        )

# Load button
if st.sidebar.button("🔄 Load Transactions", use_container_width=True):
    st.session_state.n_transactions = n_transactions
    st.session_state.loaded_data = generate_demo_data(n_transactions)
    st.session_state.data_loaded_at = datetime.now()

# Initialize session state
if 'n_transactions' not in st.session_state:
    st.session_state.n_transactions = 1000
    st.session_state.loaded_data = generate_demo_data(1000)
    st.session_state.data_loaded_at = datetime.now()

# Use loaded data
transactions = st.session_state.loaded_data
n_loaded = st.session_state.n_transactions
loaded_at = st.session_state.data_loaded_at

# Display loading info
st.sidebar.markdown("---")
st.sidebar.info(
    f"""
    ✅ **Data Status**
    
    📦 Loaded: {n_loaded:,} transactions
    
    🕐 Last loaded: {loaded_at.strftime('%H:%M:%S')}
    
    📈 Unique accounts: {transactions['account_id'].nunique()}
    
    🏪 Unique merchants: {transactions['merchant_id'].nunique()}
    
    🖥️ Unique devices: {transactions['device_id'].nunique()}
    """
)

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Select a page:",
    [
        "📊 Dashboard Overview",
        "⚠️ High-Risk Accounts",
        "📈 Fraud Trends",
        "🏪 Merchant Analysis",
        "🖥️ Device Intelligence",
        "🔎 Transaction Search",
        "⚙️ Settings & Help"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔧 Dashboard Settings")

# Settings
refresh_interval = st.sidebar.selectbox(
    "Auto-refresh interval",
    ["Disabled", "30 seconds", "1 minute", "5 minutes"]
)

show_advanced = st.sidebar.checkbox("Show Advanced Metrics", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Quick Stats")
stats = get_overview_stats(transactions)
st.sidebar.metric("Total Transactions", f"{stats['total_transactions']:,}")
st.sidebar.metric("Fraud Cases", f"{stats['fraud_transactions']:,}")
st.sidebar.metric("Fraud Rate", f"{stats['fraud_rate']:.2f}%")
st.sidebar.metric("Total Accounts", f"{stats['total_accounts']:,}")

st.sidebar.markdown("---")
st.sidebar.markdown("**Last Updated:** " + datetime.now().strftime("%H:%M:%S"))

# ============================================================================
# PAGE CONTENT
# ============================================================================

if page == "📊 Dashboard Overview":
    st.markdown('<div class="section-header">📊 System Overview</div>', unsafe_allow_html=True)
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Transactions</div>
            <div class="metric-value">{stats['total_transactions']:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <div class="metric-label">Fraud Cases</div>
            <div class="metric-value">{stats['fraud_transactions']:,}</div>
            <div class="metric-label">{stats['fraud_rate']:.2f}% Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <div class="metric-label">Total Accounts</div>
            <div class="metric-value">{stats['total_accounts']:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
            <div class="metric-label">Total Amount</div>
            <div class="metric-value">${stats['total_amount']/1000:.1f}K</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Transaction Distribution")
        fraud_dist = pd.DataFrame({
            'Type': ['Legitimate', 'Fraudulent'],
            'Count': [
                stats['total_transactions'] - stats['fraud_transactions'],
                stats['fraud_transactions']
            ]
        })
        fig = px.pie(fraud_dist, values='Count', names='Type',
                    color_discrete_sequence=['#2ecc71', '#e74c3c'],
                    hole=0.4)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Transaction Amount Distribution")
        fig = px.histogram(transactions, x='transaction_amount',
                          nbins=50, color='is_fraud',
                          color_discrete_map={True: '#e74c3c', False: '#2ecc71'},
                          labels={'is_fraud': 'Fraudulent'})
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent transactions
    st.markdown("---")
    st.subheader("Recent Transactions")
    recent = transactions.nlargest(10, 'transaction_date')[
        ['transaction_id', 'account_id', 'merchant_id', 'transaction_amount', 'is_fraud']
    ].copy()
    recent['Status'] = recent['is_fraud'].apply(lambda x: '⚠️ FRAUD' if x else '✓ OK')
    st.dataframe(
        recent[['transaction_id', 'account_id', 'merchant_id', 'transaction_amount', 'Status']],
        use_container_width=True
    )


elif page == "⚠️ High-Risk Accounts":
    st.markdown('<div class="section-header">⚠️ High-Risk Accounts</div>', unsafe_allow_html=True)
    
    account_stats = get_high_risk_accounts(transactions)
    high_risk = account_stats[account_stats['risk_score'] > account_stats['risk_score'].quantile(0.5)]
    
    st.info(f"📊 Found {len(high_risk)} high-risk accounts out of {len(account_stats)} total accounts")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Risk Score Distribution")
        fig = px.histogram(account_stats, x='risk_score',
                          nbins=30, color_discrete_sequence=['#667eea'],
                          labels={'risk_score': 'Risk Score'})
        fig.add_vline(x=account_stats['risk_score'].quantile(0.5),
                     line_dash="dash", line_color="red",
                     annotation_text="Median Risk")
        st.plotly_chart(fig, use_container_width=True)
    
    with col1:
        st.subheader("Top 10 Riskiest Accounts")
        top_risk = account_stats.head(10).reset_index()
        fig = px.bar(top_risk, x='account_id', y='risk_score',
                    color='fraud_rate',
                    color_continuous_scale='Reds',
                    labels={'account_id': 'Account ID', 'risk_score': 'Risk Score'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Risk Breakdown")
        st.metric("Average Risk Score", f"{account_stats['risk_score'].mean():.3f}")
        st.metric("Max Risk Score", f"{account_stats['risk_score'].max():.3f}")
        st.metric("High-Risk Accounts", len(high_risk))
        st.metric("Avg Fraud Rate", f"{account_stats['fraud_rate'].mean():.2%}")
    
    # High-risk accounts table
    st.markdown("---")
    st.subheader("High-Risk Accounts Details")
    st.dataframe(
        high_risk.head(20).style.background_gradient(subset=['risk_score'], cmap='Reds'),
        use_container_width=True
    )


elif page == "📈 Fraud Trends":
    st.markdown('<div class="section-header">📈 Fraud Trends Over Time</div>', unsafe_allow_html=True)
    
    daily_stats = get_fraud_trends(transactions)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Daily Fraud Statistics")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Scatter(x=daily_stats['date'], y=daily_stats['fraud_rate'],
                      name="Fraud Rate (%)", line=dict(color='#e74c3c', width=3)),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Bar(x=daily_stats['date'], y=daily_stats['total_transactions'],
                   name="Total Transactions", marker=dict(color='#667eea', opacity=0.5)),
            secondary_y=True
        )
        
        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="Fraud Rate (%)", secondary_y=False)
        fig.update_yaxes(title_text="Total Transactions", secondary_y=True)
        fig.update_layout(height=400, hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Trend Metrics")
        st.metric("Avg Fraud Rate", f"{daily_stats['fraud_rate'].mean():.2f}%")
        st.metric("Max Fraud Rate", f"{daily_stats['fraud_rate'].max():.2f}%")
        st.metric("Days Tracked", len(daily_stats))
        st.metric("Peak Fraud Count", f"{daily_stats['fraud_count'].max():.0f}")
    
    # Fraud rate trend
    st.subheader("Fraud Rate Trend")
    fig = px.line(daily_stats, x='date', y='fraud_rate',
                 markers=True, title="Fraud Rate Progression",
                 color_discrete_sequence=['#e74c3c'])
    fig.update_layout(height=300, hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)


elif page == "🏪 Merchant Analysis":
    st.markdown('<div class="section-header">🏪 Merchant Analysis</div>', unsafe_allow_html=True)
    
    merchant_stats = get_merchant_analysis(transactions)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Merchant Fraud Rates")
        top_merchants = merchant_stats.head(15).reset_index()
        fig = px.bar(top_merchants, x='merchant_id', y='fraud_rate',
                    color='fraud_rate',
                    color_continuous_scale='Reds',
                    labels={'merchant_id': 'Merchant ID', 'fraud_rate': 'Fraud Rate'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Merchant Stats")
        st.metric("Total Merchants", len(merchant_stats))
        st.metric("High-Risk Merchants", len(merchant_stats[merchant_stats['fraud_rate'] > 0.1]))
        st.metric("Avg Fraud Rate", f"{merchant_stats['fraud_rate'].mean():.2%}")
        st.metric("Max Fraud Rate", f"{merchant_stats['fraud_rate'].max():.2%}")
    
    # Merchant transactions
    st.subheader("Merchant Transaction Volume")
    fig = px.scatter(merchant_stats.reset_index(), x='total_transactions', y='fraud_rate',
                    size='total_amount', color='fraud_transactions',
                    hover_name='merchant_id',
                    color_continuous_scale='Viridis',
                    labels={'total_transactions': 'Total Transactions',
                           'fraud_rate': 'Fraud Rate'})
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed merchant table
    st.markdown("---")
    st.subheader("Merchant Details")
    st.dataframe(merchant_stats.head(25), use_container_width=True)


elif page == "🖥️ Device Intelligence":
    st.markdown('<div class="section-header">🖥️ Device Intelligence</div>', unsafe_allow_html=True)
    
    device_stats = get_device_analysis(transactions)
    suspicious_devices = device_stats[device_stats['is_suspicious']]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Device Fraud Analysis")
        fig = px.scatter(device_stats.reset_index(), x='total_transactions', y='fraud_rate',
                        size='num_accounts', color='num_accounts',
                        color_continuous_scale='Purples',
                        labels={'total_transactions': 'Total Transactions',
                               'fraud_rate': 'Fraud Rate',
                               'num_accounts': 'Accounts Used'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Device Stats")
        st.metric("Total Devices", len(device_stats))
        st.metric("Suspicious Devices", len(suspicious_devices))
        st.metric("Avg Fraud Rate", f"{device_stats['fraud_rate'].mean():.2%}")
        st.metric("Max Fraud Rate", f"{device_stats['fraud_rate'].max():.2%}")
    
    # Device-sharing insights
    st.subheader("Multi-Account Devices (Suspicious)")
    if len(suspicious_devices) > 0:
        fig = px.bar(suspicious_devices.head(20).reset_index(), x='device_id', y='num_accounts',
                    color='fraud_rate',
                    color_continuous_scale='Reds',
                    labels={'device_id': 'Device ID', 'num_accounts': 'Account Count'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No suspicious multi-account devices found.")
    
    # Device table
    st.markdown("---")
    st.subheader("Device Details")
    st.dataframe(device_stats.head(25), use_container_width=True)


elif page == "🔎 Transaction Search":
    st.markdown('<div class="section-header">🔎 Transaction Search</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_type = st.selectbox("Search by:", ["Account ID", "Merchant ID", "Device ID", "Transaction ID"])
    
    with col2:
        search_value = st.number_input("Enter ID:", min_value=1)
    
    with col3:
        st.write("")
        search_button = st.button("🔍 Search", use_container_width=True)
    
    if search_button:
        if search_type == "Account ID":
            results = transactions[transactions['account_id'] == search_value]
            st.subheader(f"Transactions for Account {search_value}")
        elif search_type == "Merchant ID":
            results = transactions[transactions['merchant_id'] == search_value]
            st.subheader(f"Transactions for Merchant {search_value}")
        elif search_type == "Device ID":
            results = transactions[transactions['device_id'] == search_value]
            st.subheader(f"Transactions for Device {search_value}")
        else:
            results = transactions[transactions['transaction_id'] == search_value]
            st.subheader(f"Transaction {search_value}")
        
        if len(results) > 0:
            results_display = results.copy()
            results_display['Status'] = results_display['is_fraud'].apply(
                lambda x: '⚠️ FRAUD' if x else '✓ OK'
            )
            st.dataframe(
                results_display[['transaction_id', 'account_id', 'merchant_id', 
                               'device_id', 'transaction_amount', 'Status']],
                use_container_width=True
            )
            
            # Stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Transactions", len(results))
            with col2:
                st.metric("Fraud Count", results['is_fraud'].sum())
            with col3:
                st.metric("Total Amount", f"${results['transaction_amount'].sum():.2f}")
            with col4:
                st.metric("Avg Amount", f"${results['transaction_amount'].mean():.2f}")
        else:
            st.warning(f"No transactions found for {search_type.lower()} {search_value}")


elif page == "⚙️ Settings & Help":
    st.markdown('<div class="section-header">⚙️ Settings & Help</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Help", "About", "Technical Info"])
    
    with tab1:
        st.markdown("""
        ### 📖 Help & Guide
        
        **Dashboard Features:**
        
        1. **Dashboard Overview** - High-level metrics and transaction distribution
        2. **High-Risk Accounts** - Identify accounts with suspicious activity
        3. **Fraud Trends** - Monitor fraud patterns over time
        4. **Merchant Analysis** - Analyze fraud by merchant
        5. **Device Intelligence** - Detect device-sharing fraud patterns
        6. **Transaction Search** - Search transactions by various criteria
        
        **How to Use:**
        
        - Use the **left sidebar** to navigate between pages
        - Charts are interactive - hover for details, click legend items to toggle
        - All metrics update in real-time
        - Use Transaction Search to investigate specific accounts, merchants, or devices
        """)
    
    with tab2:
        st.markdown("""
        ### 🔍 About This System
        
        **Fraud Detection System** uses Graph Neural Networks (GNNs) to detect fraudulent transactions.
        
        **Technology Stack:**
        - **Database**: PostgreSQL
        - **ML Framework**: PyTorch, PyTorch Geometric
        - **Visualization**: Streamlit, Plotly
        - **Models**: GraphSAGE, GAT, R-GCN
        
        **Key Features:**
        - Real-time fraud detection
        - Account risk profiling
        - Merchant analysis
        - Device fingerprinting
        - Network intelligence
        
        **Project**: DRAGNN-FraudDB
        **Version**: 1.0.0
        """)
    
    with tab3:
        st.markdown(f"""
        ### 🔧 Technical Information
        
        **System Status**: ✅ Operational
        
        **Data Summary:**
        - Total Transactions: {len(transactions):,}
        - Total Accounts: {transactions['account_id'].nunique():,}
        - Total Merchants: {transactions['merchant_id'].nunique():,}
        - Total Devices: {transactions['device_id'].nunique():,}
        - Fraud Rate: {(transactions['is_fraud'].sum() / len(transactions) * 100):.2f}%
        
        **Performance:**
        - Data loaded: ✅
        - All models available: ✅
        - Dashboard operational: ✅
        
        **Last Update**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.85rem; padding-top: 20px;">
    🔍 Fraud Detection System | Powered by Streamlit | 
    <a href="https://github.com/3015pavan/DRAGNN-FraudDB" target="_blank">GitHub</a>
</div>
""", unsafe_allow_html=True)
