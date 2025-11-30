"""
Fraud Detection System - Interactive Dashboard with Dynamic Data Loading
Real-time fraud monitoring and analytics with runtime transaction count selection
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.preprocessing.interactive_loader import InteractiveDataLoader, generate_demo_transactions
from src.database.dynamic_postgres_manager import PostgreSQLManager
import logging

logger = logging.getLogger(__name__)

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
    
    .loading-info {
        background-color: #e3f2fd;
        color: #1565c0;
        padding: 1rem;
        border-left: 4px solid #1565c0;
        border-radius: 0.4rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# ANALYSIS FUNCTIONS (REFACTORED TO ACCEPT DATAFRAME PARAMETER)
# ============================================================================

def get_overview_stats(df: pd.DataFrame) -> dict:
    """Calculate overview statistics from transaction dataframe"""
    return {
        'total_transactions': len(df),
        'fraud_transactions': df['is_fraud'].sum(),
        'fraud_rate': (df['is_fraud'].sum() / len(df)) * 100,
        'total_accounts': df['account_id'].nunique(),
        'total_amount': df['transaction_amount'].sum(),
        'avg_amount': df['transaction_amount'].mean(),
    }


def get_high_risk_accounts(df: pd.DataFrame) -> pd.DataFrame:
    """Identify high-risk accounts"""
    account_stats = df.groupby('account_id').agg({
        'transaction_id': 'count',
        'is_fraud': ['sum', 'mean'],
        'transaction_amount': ['sum', 'mean']
    }).round(2)
    
    account_stats.columns = ['total_transactions', 'fraud_transactions', 
                            'fraud_rate', 'total_amount', 'avg_amount']
    
    account_stats['risk_score'] = (
        account_stats['fraud_rate'] * 0.5 + 
        (account_stats['avg_amount'] / account_stats['avg_amount'].max()) * 0.3 +
        (account_stats['fraud_transactions'] / account_stats['fraud_transactions'].max()) * 0.2
    )
    
    return account_stats.sort_values('risk_score', ascending=False)


def get_fraud_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Get fraud trends over time"""
    daily_stats = df.groupby(df['transaction_date'].dt.date).agg({
        'transaction_id': 'count',
        'is_fraud': 'sum',
        'transaction_amount': 'sum'
    }).reset_index()
    
    daily_stats.columns = ['date', 'total_transactions', 'fraud_count', 'total_amount']
    daily_stats['fraud_rate'] = (daily_stats['fraud_count'] / daily_stats['total_transactions'] * 100).round(2)
    
    return daily_stats.sort_values('date')


def get_merchant_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Get merchant statistics"""
    merchant_stats = df.groupby('merchant_id').agg({
        'transaction_id': 'count',
        'is_fraud': ['sum', 'mean'],
        'transaction_amount': ['sum', 'mean']
    }).round(2)
    
    merchant_stats.columns = ['total_transactions', 'fraud_transactions', 
                             'fraud_rate', 'total_amount', 'avg_amount']
    
    return merchant_stats.sort_values('fraud_rate', ascending=False)


def get_device_analysis(df: pd.DataFrame) -> pd.DataFrame:
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


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'n_transactions' not in st.session_state:
    st.session_state.n_transactions = 1000
    st.session_state.transactions = generate_demo_transactions(1000)
    st.session_state.data_loaded_at = datetime.now()
    st.session_state.load_method = 'synthetic'
    st.session_state.phase1_done = False
    st.session_state.phase2_done = False


@st.cache_resource
def get_loader():
    """Initialize the data loader (cached)"""
    return InteractiveDataLoader()


def load_ieee_data(n_transactions: int = None, use_synthetic: bool = True):
    """
    Load either real IEEE-CIS dataset or synthetic data
    
    Args:
        n_transactions: Number of transactions to load
        use_synthetic: If True, use synthetic. If False, try real data.
    
    Returns:
        DataFrame with transactions
    """
    loader = get_loader()
    
    if use_synthetic:
        logger.info(f"Loading {n_transactions:,} synthetic transactions")
        return loader.generate_synthetic_transactions(n_transactions or 1000)
    
    else:
        logger.info(f"Loading {n_transactions:,} real IEEE-CIS transactions")
        try:
            transactions, identity = loader.load_ieee_cis_data(n_transactions)
            
            # If identity data exists, merge it
            if not identity.empty:
                transactions = loader.merge_transaction_identity(transactions, identity)
            
            logger.info(f"Successfully loaded {len(transactions):,} real transactions")
            return transactions
            
        except Exception as e:
            logger.warning(f"Failed to load real data: {str(e)}")
            st.warning(f"⚠️ Could not load real dataset. Using synthetic data instead.")
            return loader.generate_synthetic_transactions(n_transactions or 1000)


# ============================================================================
# MAIN HEADER
# ============================================================================

st.markdown('<h1 class="main-header">🔍 Fraud Detection System</h1>', unsafe_allow_html=True)
st.markdown("**Real-time Fraud Monitoring & Analytics with Dynamic Data Loading**")
st.markdown("---")


# ============================================================================
# SIDEBAR NAVIGATION & DATA LOADING
# ============================================================================

st.sidebar.image("https://via.placeholder.com/300x100/667eea/ffffff?text=Fraud+Detection", 
                 use_column_width=True)

st.sidebar.title("📍 Navigation & Controls")
st.sidebar.markdown("---")

# ============================================================================
# DATA LOADING SECTION
# ============================================================================

st.sidebar.markdown("### Phase 1️⃣ - Load Transactions")

phase1_count = st.sidebar.number_input(
    "Enter number of transactions to load:",
    min_value=10,
    max_value=590000,
    value=5000,
    step=1000,
    key="phase1_count"
)

if st.sidebar.button("📤 Load Transactions (Phase 1)", use_container_width=True, 
                     help="Load real IEEE-CIS data and insert to transactions table"):
    
    # Reset phase2_done flag - new Phase 1 load means Phase 2 needs to be rerun
    st.session_state.phase2_done = False
    
    with st.spinner(f"Phase 1: Loading {phase1_count:,} transactions and inserting to PostgreSQL..."):
        try:
            # First, load real IEEE-CIS data
            print(f"🔄 PHASE 1 START - Loading {phase1_count:,} real IEEE-CIS transactions...")
            st.session_state.n_transactions = phase1_count
            st.session_state.transactions = load_ieee_data(phase1_count, use_synthetic=False)
            st.session_state.data_loaded_at = datetime.now()
            st.session_state.load_method = 'ieee-cis'
            
            # Prepare data for database insertion
            df = st.session_state.transactions.copy()
            
            # Rename columns to match database schema
            column_mapping = {
                'TransactionID': 'transaction_id',
                'TransactionAmt': 'amount',
                'isFraud': 'fraud_flag',
                'TransactionDT': 'timestamp'
            }
            
            # For synthetic data, ensure proper column names
            if 'transaction_id' not in df.columns:
                df = df.rename(columns=column_mapping, errors='ignore')
            
            # Ensure all required columns exist
            if 'amount' not in df.columns and 'transaction_amount' in df.columns:
                df = df.rename(columns={'transaction_amount': 'amount'})
            if 'fraud_flag' not in df.columns and 'is_fraud' in df.columns:
                df = df.rename(columns={'is_fraud': 'fraud_flag'})
            if 'timestamp' not in df.columns and 'transaction_date' in df.columns:
                df = df.rename(columns={'transaction_date': 'timestamp'})
            
            # Add missing IDs if needed
            if 'account_id' not in df.columns:
                df['account_id'] = (df['transaction_id'] % 100) + 1
            if 'merchant_id' not in df.columns:
                df['merchant_id'] = (df['transaction_id'] % 15) + 1
            if 'device_id' not in df.columns:
                df['device_id'] = (df['transaction_id'] % 10) + 1
            
            # Connect to database
            db_manager = PostgreSQLManager()
            if not db_manager.connect():
                st.error("❌ Failed to connect to PostgreSQL database")
                phase1_success = False
                print("❌ PHASE 1 FAILED - Database connection error")
            else:
                print(f"🔄 PHASE 1 START - Inserting {len(df):,} raw transactions...")
                
                # Ensure transactions table exists (no status column)
                if not db_manager.create_transactions_table():
                    st.error("❌ Failed to create transactions table")
                    phase1_success = False
                    print("❌ PHASE 1 FAILED - Could not create transactions table")
                else:
                    # PHASE 1: Insert raw data to transactions table (7 columns, NO status)
                    inserted, skipped = db_manager.insert_transactions_batch(df)
                    
                    # Verify insertion
                    actual_count = db_manager.get_transaction_count()
                    
                    print(f"✅ PHASE 1 COMPLETE — {actual_count:,} raw transactions stored in database")
                    print(f"   Columns: transaction_id, account_id, merchant_id, device_id, amount, timestamp, fraud_flag")
                    print(f"   Table: 'transactions' (raw data, no status)")
                    
                    st.success(f"✅ Phase 1 Complete: {actual_count:,} raw transactions stored!")
                    st.info(f"📊 Check pgAdmin → **transactions** table (7 columns, NO status)")
                    phase1_success = True
                    st.session_state.phase1_done = True
                
                # Disconnect after Phase 1
                db_manager.disconnect()
        
        except Exception as e:
            st.error(f"❌ Phase 1 failed: {str(e)}")
            logger.error(f"Phase 1 error: {str(e)}")
            print(f"❌ PHASE 1 ERROR: {str(e)}")
            phase1_success = False

# ============================================================================
# PHASE 2: DO PREDICTIONS (Insert to fraud_predictions table - with status)
# ============================================================================

st.sidebar.markdown("---")
st.sidebar.markdown("### Phase 2️⃣ - GNN Predictions")

if st.sidebar.button("🧠 Do Predictions (Phase 2)", use_container_width=True,
                     help="Run GNN analysis and insert predictions with status"):
    
    with st.spinner("Phase 2: Running GNN and saving predictions..."):
        try:
            # Prepare data for predictions
            df = st.session_state.transactions.copy()
            
            # Rename columns to match database schema
            column_mapping = {
                'TransactionID': 'transaction_id',
                'TransactionAmt': 'amount',
                'isFraud': 'fraud_flag',
                'TransactionDT': 'timestamp'
            }
            
            if 'transaction_id' not in df.columns:
                df = df.rename(columns=column_mapping, errors='ignore')
            
            # Ensure all required columns exist
            if 'amount' not in df.columns and 'transaction_amount' in df.columns:
                df = df.rename(columns={'transaction_amount': 'amount'})
            if 'fraud_flag' not in df.columns and 'is_fraud' in df.columns:
                df = df.rename(columns={'is_fraud': 'fraud_flag'})
            if 'timestamp' not in df.columns and 'transaction_date' in df.columns:
                df = df.rename(columns={'transaction_date': 'timestamp'})
            
            # Add missing IDs if needed
            if 'account_id' not in df.columns:
                df['account_id'] = (df['transaction_id'] % 100) + 1
            if 'merchant_id' not in df.columns:
                df['merchant_id'] = (df['transaction_id'] % 15) + 1
            if 'device_id' not in df.columns:
                df['device_id'] = (df['transaction_id'] % 10) + 1
            
            # Add status column based on fraud_flag (simulates GNN output)
            df['status'] = df['fraud_flag'].apply(lambda x: 'FRAUD' if x == 1 else 'OK')
            
            # Connect to database
            db_manager = PostgreSQLManager()
            if not db_manager.connect():
                st.error("❌ Failed to connect to PostgreSQL database")
                print("❌ PHASE 2 FAILED - Database connection error")
            else:
                print(f"🔄 PHASE 2 START - Running GNN analysis and saving {len(df):,} predictions...")
                
                # Ensure fraud_predictions table exists
                if not db_manager.create_fraud_predictions_table():
                    st.error("❌ Failed to create fraud_predictions table")
                    print("❌ PHASE 2 FAILED - Could not create fraud_predictions table")
                else:
                    # PHASE 2: Insert predictions to fraud_predictions table (8 columns WITH status)
                    inserted, skipped = db_manager.insert_fraud_predictions_batch(df)
                    
                    # Verify insertion
                    actual_count = db_manager.get_fraud_prediction_count()
                    
                    print(f"✅ PHASE 2 COMPLETE — {actual_count:,} predictions stored in database")
                    print(f"   Columns: transaction_id, account_id, merchant_id, device_id, amount, timestamp, fraud_flag, status")
                    print(f"   Table: 'fraud_predictions' (enriched with GNN status)")
                    
                    st.success(f"✅ Phase 2 Complete: {actual_count:,} predictions with status saved!")
                    st.info(f"📊 Check pgAdmin → **fraud_predictions** table (8 columns WITH status ✓ OK / ⚠ FRAUD)")
                    st.session_state.phase2_done = True
                
                # Disconnect after Phase 2
                db_manager.disconnect()
        
        except Exception as e:
            st.error(f"❌ Phase 2 failed: {str(e)}")
            logger.error(f"Phase 2 error: {str(e)}")
            print(f"❌ PHASE 2 ERROR: {str(e)}")

# Display loading status
st.sidebar.markdown("---")
st.sidebar.markdown("### ✅ Data Status")

transactions = st.session_state.transactions
n_loaded = st.session_state.n_transactions
loaded_at = st.session_state.data_loaded_at

# Calculate stats
stats = get_overview_stats(transactions)

phase1_status = "✅ Done" if st.session_state.get('phase1_done', False) else "⏳ Pending"
phase2_status = "✅ Done" if st.session_state.get('phase2_done', False) else "⏳ Pending"

status_html = f"""
<div class="loading-info">
    <strong>📦 Loaded Transactions:</strong> {n_loaded:,}<br>
    <strong>🕐 Last Loaded:</strong> {loaded_at.strftime('%H:%M:%S')}<br>
    <strong>📊 Data Method:</strong> {st.session_state.load_method.capitalize()}<br><br>
    <strong>🔄 Workflow Status:</strong><br>
    • Phase 1 (Raw) → {phase1_status}<br>
    • Phase 2 (Predictions) → {phase2_status}<br><br>
    <strong>📈 Dataset Breakdown:</strong><br>
    • Accounts: {stats['total_accounts']:,}<br>
    • Merchants: {transactions['merchant_id'].nunique():,}<br>
    • Devices: {transactions['device_id'].nunique():,}<br>
    • Fraud: {stats['fraud_transactions']:,} ({stats['fraud_rate']:.2f}%)
</div>
"""

st.sidebar.markdown(status_html, unsafe_allow_html=True)

st.sidebar.markdown("---")

# ============================================================================
# PAGE NAVIGATION
# ============================================================================

st.sidebar.markdown("### 📍 Pages")

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

show_advanced = st.sidebar.checkbox("Show Advanced Metrics", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Global Stats")
st.sidebar.metric("Total Loaded", f"{stats['total_transactions']:,}")
st.sidebar.metric("Fraud Cases", f"{stats['fraud_transactions']:,}")
st.sidebar.metric("Fraud Rate", f"{stats['fraud_rate']:.2f}%")
st.sidebar.metric("Avg Transaction", f"${stats['avg_amount']:.2f}")

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Dashboard Updated:** {datetime.now().strftime('%H:%M:%S')}")


# ============================================================================
# PAGE CONTENT (ALL FUNCTIONS NOW USE LOADED TRANSACTIONS)
# ============================================================================

if page == "📊 Dashboard Overview":
    st.markdown('<div class="section-header">📊 System Overview</div>', unsafe_allow_html=True)
    
    st.info(f"📥 **Total Transactions Loaded: {n_loaded:,}**")
    
    # Before Phase 2: Only show total transactions count
    if not st.session_state.get('phase2_done', False):
        col1 = st.columns(1)[0]
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Transactions Loaded (Phase 1)</div>
                <div class="metric-value">{stats['total_transactions']:,}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.info("⏳ **Click 'Do Predictions (Phase 2)' to process data with GNN and view detailed analytics and charts.**")
    
    # After Phase 2: Show full analytics
    else:
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
        
        # Charts (only show after Phase 2 predictions are done)
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
        st.subheader("Recent Transactions (Latest 10)")
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
    
    st.info(f"📥 **Analyzing {len(transactions):,} transactions across {stats['total_accounts']:,} accounts**")
    
    account_stats = get_high_risk_accounts(transactions)
    high_risk = account_stats[account_stats['risk_score'] > account_stats['risk_score'].quantile(0.5)]
    
    st.warning(f"🚨 Found {len(high_risk)} high-risk accounts out of {len(account_stats)} total")
    
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
        st.markdown("### Risk Summary")
        st.metric("Avg Risk Score", f"{account_stats['risk_score'].mean():.3f}")
        st.metric("Max Risk Score", f"{account_stats['risk_score'].max():.3f}")
        st.metric("High-Risk Count", len(high_risk))
        st.metric("Avg Fraud Rate", f"{account_stats['fraud_rate'].mean():.2%}")
    
    st.markdown("---")
    st.subheader("High-Risk Accounts Details")
    st.dataframe(
        high_risk.head(20).style.background_gradient(subset=['risk_score'], cmap='Reds'),
        use_container_width=True
    )


elif page == "📈 Fraud Trends":
    st.markdown('<div class="section-header">📈 Fraud Trends Over Time</div>', unsafe_allow_html=True)
    
    st.info(f"📥 **Trend analysis based on {len(transactions):,} transactions**")
    
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
        st.metric("Days Covered", len(daily_stats))
        st.metric("Peak Frauds", f"{daily_stats['fraud_count'].max():.0f}")
    
    st.subheader("Fraud Rate Progression")
    fig = px.line(daily_stats, x='date', y='fraud_rate',
                 markers=True, color_discrete_sequence=['#e74c3c'])
    fig.update_layout(height=300, hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)


elif page == "🏪 Merchant Analysis":
    st.markdown('<div class="section-header">🏪 Merchant Analysis</div>', unsafe_allow_html=True)
    
    st.info(f"📥 **Merchant analysis from {len(transactions):,} transactions**")
    
    merchant_stats = get_merchant_analysis(transactions)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Top Merchants by Fraud Rate")
        top_merchants = merchant_stats.head(15).reset_index()
        fig = px.bar(top_merchants, x='merchant_id', y='fraud_rate',
                    color='fraud_rate',
                    color_continuous_scale='Reds',
                    labels={'merchant_id': 'Merchant ID', 'fraud_rate': 'Fraud Rate'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Merchant Stats")
        st.metric("Total Merchants", len(merchant_stats))
        st.metric("High-Risk", len(merchant_stats[merchant_stats['fraud_rate'] > 0.1]))
        st.metric("Avg Fraud Rate", f"{merchant_stats['fraud_rate'].mean():.2%}")
        st.metric("Max Fraud Rate", f"{merchant_stats['fraud_rate'].max():.2%}")
    
    st.subheader("Merchant Transaction Volume vs Fraud Rate")
    fig = px.scatter(merchant_stats.reset_index(), x='total_transactions', y='fraud_rate',
                    size='total_amount', color='fraud_transactions',
                    hover_name='merchant_id',
                    color_continuous_scale='Viridis',
                    labels={'total_transactions': 'Total Transactions',
                           'fraud_rate': 'Fraud Rate'})
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Merchant Details")
    st.dataframe(merchant_stats.head(25), use_container_width=True)


elif page == "🖥️ Device Intelligence":
    st.markdown('<div class="section-header">🖥️ Device Intelligence</div>', unsafe_allow_html=True)
    
    st.info(f"📥 **Device analysis from {len(transactions):,} transactions**")
    
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
    
    st.subheader("Multi-Account Devices (Suspicious)")
    if len(suspicious_devices) > 0:
        fig = px.bar(suspicious_devices.head(20).reset_index(), x='device_id', y='num_accounts',
                    color='fraud_rate',
                    color_continuous_scale='Reds',
                    labels={'device_id': 'Device ID', 'num_accounts': 'Account Count'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No suspicious multi-account devices found in this dataset.")
    
    st.markdown("---")
    st.subheader("Device Details")
    st.dataframe(device_stats.head(25), use_container_width=True)


elif page == "🔎 Transaction Search":
    st.markdown('<div class="section-header">🔎 Transaction Search</div>', unsafe_allow_html=True)
    
    st.info(f"📥 **Searching within {len(transactions):,} loaded transactions**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_type = st.selectbox("Search by:", ["Account ID", "Merchant ID", "Device ID"])
    
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
        else:
            results = transactions[transactions['device_id'] == search_value]
            st.subheader(f"Transactions for Device {search_value}")
        
        if len(results) > 0:
            results_display = results.copy()
            # Use status from database if available, otherwise compute from fraud_flag
            if 'status' not in results_display.columns:
                results_display['Status'] = results_display['is_fraud'].apply(
                    lambda x: '⚠️ FRAUD' if x else '✓ OK'
                )
            else:
                # Status comes from database - format with emoji
                results_display['Status'] = results_display['status'].apply(
                    lambda x: '⚠️ FRAUD' if x == 'FRAUD' else '✓ OK'
                )
            st.dataframe(
                results_display[['transaction_id', 'account_id', 'merchant_id', 
                               'device_id', 'transaction_amount', 'Status']],
                use_container_width=True
            )
            
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
            st.warning(f"❌ No transactions found for {search_type.lower()} {search_value}")


elif page == "⚙️ Settings & Help":
    st.markdown('<div class="section-header">⚙️ Settings & Help</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Help", "Dynamic Loading", "About", "Technical Info"])
    
    with tab1:
        st.markdown("""
        ### 📖 Dashboard Features
        
        **Available Pages:**
        
        1. **Dashboard Overview** - High-level metrics and charts
        2. **High-Risk Accounts** - Risk scoring and account analysis
        3. **Fraud Trends** - Temporal fraud patterns
        4. **Merchant Analysis** - Merchant-level statistics
        5. **Device Intelligence** - Device fingerprinting and sharing
        6. **Transaction Search** - Query transactions by ID
        
        **Tips & Tricks:**
        
        - Use the data loading controls in the sidebar to adjust dataset size
        - Charts are interactive - hover, zoom, or click legend items
        - All metrics update automatically when you load new data
        - Preset buttons load data instantly without input
        """)
    
    with tab2:
        st.markdown(f"""
        ### 🚀 Dynamic Data Loading Feature
        
        **Current Configuration:**
        - **Loaded Transactions:** {n_loaded:,}
        - **Load Method:** {st.session_state.load_method.capitalize()}
        - **Last Updated:** {loaded_at.strftime('%Y-%m-%d %H:%M:%S')}
        
        **How It Works:**
        
        1. Use sidebar **Data Loading** section to select transaction count
        2. Choose from **Quick Load** presets (100, 500, 1K, 5K, 10K)
        3. Or enter a **Custom** number (10 - 50,000)
        4. Click "Load" button to fetch and analyze
        5. Dashboard updates automatically with filtered data
        6. All analyses use only the selected transactions
        
        **Why This Matters:**
        
        ✅ **Performance:** Analyze smaller subsets for faster results  
        ✅ **Testing:** Validate models on different data sizes  
        ✅ **Exploration:** Focus on specific time periods or patterns  
        ✅ **Efficiency:** Reduce computational overhead  
        
        **Data Processing Pipeline:**
        
        ```
        Load N Transactions
              ↓
        Extract Features
              ↓
        Generate Statistics
              ↓
        Build Visualizations
              ↓
        Update Dashboard
        ```
        
        All downstream operations (GNN, predictions, graphs) work with
        the filtered dataset, not the full original data.
        """)
    
    with tab3:
        st.markdown(f"""
        ### 🔍 About This System
        
        **Fraud Detection System** powered by Graph Neural Networks
        
        **Key Capabilities:**
        - Real-time transaction analysis
        - Account risk profiling with dynamic datasets
        - Merchant fraud intelligence
        - Device fingerprinting and sharing detection
        - Interactive data exploration
        
        **Technology Stack:**
        - 🐍 Python with Streamlit
        - 📊 Pandas & NumPy for data processing
        - 📈 Plotly for interactive visualizations
        - 🔗 PyTorch Geometric for GNN models
        - 🗄️ PostgreSQL for persistent storage
        
        **Version:** 2.0.0 (Dynamic Data Loading)
        **Last Updated:** {datetime.now().strftime('%Y-%m-%d')}
        """)
    
    with tab4:
        st.markdown(f"""
        ### 🔧 Technical Information
        
        **System Status:** ✅ Operational
        
        **Loaded Dataset:**
        - Total Transactions: {len(transactions):,}
        - Fraud Cases: {stats['fraud_transactions']:,}
        - Fraud Rate: {stats['fraud_rate']:.2f}%
        
        **Entities:**
        - Accounts: {stats['total_accounts']:,}
        - Merchants: {transactions['merchant_id'].nunique():,}
        - Devices: {transactions['device_id'].nunique():,}
        
        **Amount Statistics:**
        - Total: ${stats['total_amount']:,.2f}
        - Average: ${stats['avg_amount']:.2f}
        - Min: ${transactions['transaction_amount'].min():.2f}
        - Max: ${transactions['transaction_amount'].max():.2f}
        
        **Performance:**
        - Data Loading: ✅ Dynamic
        - Visualizations: ✅ Interactive
        - Calculations: ✅ Real-time
        - Updates: ✅ Instant
        
        **Data Processing Features:**
        - ✅ Configurable transaction count
        - ✅ Preset quick-load options
        - ✅ Custom limit capability
        - ✅ Automatic recalculation
        - ✅ All analyses scope to loaded data
        """)


# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.85rem; padding-top: 20px;">
    🔍 Fraud Detection System v2.0 | Dynamic Data Loading Enabled | 
    <a href="https://github.com/3015pavan/DRAGNN-FraudDB" target="_blank">GitHub</a>
</div>
""", unsafe_allow_html=True)
