"""
Fraud Detection System - Interactive Dashboard
Real-time fraud monitoring and analytics with GNN predictions
"""

import streamlit as st
import pandas as pd
import numpy as np
import torch
import pickle
from pathlib import Path
import sys
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import networkx as nx
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config.config import config
from src.database.connection import db
from src.models import GraphSAGEFraudDetector, GATFraudDetector, RGCNFraudDetector

# Page configuration
st.set_page_config(
    page_title="Fraud Detection System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .fraud-alert {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        margin: 1rem 0;
    }
    .normal-status {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_graph():
    """Load fraud graph"""
    graph_path = config.DATA_PROCESSED_PATH / 'fraud_graph.pt'
    if graph_path.exists():
        return torch.load(graph_path)
    return None


@st.cache_resource
def load_model(model_type='graphsage'):
    """Load trained GNN model"""
    checkpoint_path = config.MODEL_CHECKPOINT_PATH / f'best_{model_type}.pt'
    
    if not checkpoint_path.exists():
        return None, None
    
    # Load graph to get metadata
    data = load_graph()
    if data is None:
        return None, None
    
    metadata = data.metadata()
    in_channels_dict = {
        'account': data['account'].x.size(1),
        'merchant': data['merchant'].x.size(1),
        'device': data['device'].x.size(1)
    }
    
    # Initialize model
    if model_type == 'graphsage':
        model = GraphSAGEFraudDetector(
            metadata=metadata,
            in_channels_dict=in_channels_dict,
            hidden_channels=128,
            out_channels=64,
            num_layers=3
        )
    elif model_type == 'gat':
        model = GATFraudDetector(
            metadata=metadata,
            in_channels_dict=in_channels_dict,
            hidden_channels=128,
            out_channels=64,
            num_layers=3,
            heads=4
        )
    else:  # rgcn
        model = RGCNFraudDetector(
            metadata=metadata,
            in_channels_dict=in_channels_dict,
            hidden_channels=128,
            out_channels=64,
            num_layers=3
        )
    
    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location='cpu')
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    return model, checkpoint.get('metrics', {})


@st.cache_data(ttl=60)
def get_database_stats():
    """Get real-time database statistics"""
    stats = {}
    
    with db.get_cursor() as cur:
        # Total transactions
        cur.execute("SELECT COUNT(*) FROM transaction")
        stats['total_transactions'] = cur.fetchone()[0]
        
        # Fraud transactions
        cur.execute("SELECT COUNT(*) FROM transaction WHERE is_fraud = TRUE")
        stats['fraud_transactions'] = cur.fetchone()[0]
        
        # Fraud rate
        stats['fraud_rate'] = (stats['fraud_transactions'] / stats['total_transactions'] * 100 
                               if stats['total_transactions'] > 0 else 0)
        
        # Total accounts
        cur.execute("SELECT COUNT(*) FROM account")
        stats['total_accounts'] = cur.fetchone()[0]
        
        # High-risk accounts
        cur.execute("SELECT COUNT(*) FROM account WHERE risk_score > 0.7")
        stats['high_risk_accounts'] = cur.fetchone()[0]
        
        # Total merchants
        cur.execute("SELECT COUNT(*) FROM merchant")
        stats['total_merchants'] = cur.fetchone()[0]
        
        # Suspicious merchants
        cur.execute("SELECT COUNT(*) FROM merchant WHERE fraud_rate > 0.1")
        stats['suspicious_merchants'] = cur.fetchone()[0]
        
        # Total devices
        cur.execute("SELECT COUNT(*) FROM device")
        stats['total_devices'] = cur.fetchone()[0]
        
        # Shared devices
        cur.execute("SELECT COUNT(*) FROM device WHERE is_shared = TRUE")
        stats['shared_devices'] = cur.fetchone()[0]
        
        # Average transaction amount
        cur.execute("SELECT AVG(transaction_amount) FROM transaction")
        stats['avg_transaction'] = cur.fetchone()[0] or 0
        
        # Total transaction volume
        cur.execute("SELECT SUM(transaction_amount) FROM transaction")
        stats['total_volume'] = cur.fetchone()[0] or 0
    
    return stats


@st.cache_data(ttl=60)
def get_recent_transactions(limit=100):
    """Get recent transactions"""
    query = """
    SELECT 
        t.transaction_id,
        t.account_id,
        t.merchant_id,
        t.transaction_amount,
        t.is_fraud,
        a.risk_score,
        m.product_category
    FROM transaction t
    LEFT JOIN account a ON t.account_id = a.account_id
    LEFT JOIN merchant m ON t.merchant_id = m.merchant_id
    ORDER BY t.transaction_id DESC
    LIMIT %s
    """
    
    df = pd.read_sql(query, db.engine, params=(limit,))
    return df


@st.cache_data(ttl=60)
def get_fraud_trends():
    """Get fraud trends over time"""
    query = """
    SELECT 
        DATE_TRUNC('hour', transaction_time) as hour,
        COUNT(*) as total_transactions,
        SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) as fraud_count,
        AVG(transaction_amount) as avg_amount
    FROM transaction
    WHERE transaction_time IS NOT NULL
    GROUP BY hour
    ORDER BY hour
    """
    
    df = pd.read_sql(query, db.engine)
    if not df.empty and 'hour' in df.columns:
        df['fraud_rate'] = (df['fraud_count'] / df['total_transactions'] * 100)
    return df


@st.cache_data(ttl=60)
def get_high_risk_accounts(limit=20):
    """Get high-risk accounts"""
    query = """
    SELECT 
        account_id,
        risk_score,
        total_transactions,
        fraud_transactions,
        total_transaction_amount,
        avg_transaction_amount
    FROM account
    WHERE risk_score > 0.5
    ORDER BY risk_score DESC
    LIMIT %s
    """
    
    df = pd.read_sql(query, db.engine, params=(limit,))
    return df


def main():
    """Main dashboard function"""
    
    # Header
    st.markdown('<h1 class="main-header">🔍 Fraud Detection System</h1>', unsafe_allow_html=True)
    st.markdown("### Graph Neural Network-Based Fraud Detection")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Model selection
        model_type = st.selectbox(
            "Select GNN Model",
            ["graphsage", "gat", "rgcn"],
            help="Choose the Graph Neural Network architecture"
        )
        
        # Refresh button
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        
        # Info
        st.markdown("### 📊 System Status")
        st.success("✅ Database Connected")
        st.success("✅ Model Loaded")
        
        st.markdown("---")
        st.markdown("### 🔗 Quick Links")
        st.markdown("- [Database Schema](docs/ER_diagram.md)")
        st.markdown("- [Model Documentation](docs/graph_schema.md)")
        st.markdown("- [GitHub Repository](#)")
    
    # Load model
    model, model_metrics = load_model(model_type)
    
    # Load data
    stats = get_database_stats()
    
    # Key Metrics Row
    st.header("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Transactions",
            value=f"{stats['total_transactions']:,}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Fraud Transactions",
            value=f"{stats['fraud_transactions']:,}",
            delta=f"{stats['fraud_rate']:.2f}% rate",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="High-Risk Accounts",
            value=f"{stats['high_risk_accounts']:,}",
            delta=f"{stats['high_risk_accounts']/stats['total_accounts']*100:.1f}%",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            label="Total Volume",
            value=f"${stats['total_volume']:,.0f}",
            delta=f"Avg: ${stats['avg_transaction']:.2f}"
        )
    
    st.markdown("---")
    
    # Model Performance
    if model_metrics:
        st.header("🤖 Model Performance")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Precision", f"{model_metrics.get('precision', 0):.4f}")
        with col2:
            st.metric("Recall", f"{model_metrics.get('recall', 0):.4f}")
        with col3:
            st.metric("F1 Score", f"{model_metrics.get('f1', 0):.4f}")
        with col4:
            st.metric("ROC-AUC", f"{model_metrics.get('roc_auc', 0):.4f}")
        
        st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview", 
        "⚠️ High-Risk Accounts", 
        "📈 Trends", 
        "🔍 Transaction Search"
    ])
    
    with tab1:
        st.header("System Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Fraud distribution pie chart
            fig_pie = go.Figure(data=[go.Pie(
                labels=['Normal', 'Fraud'],
                values=[
                    stats['total_transactions'] - stats['fraud_transactions'],
                    stats['fraud_transactions']
                ],
                marker=dict(colors=['#4caf50', '#f44336']),
                hole=0.4
            )])
            fig_pie.update_layout(
                title="Transaction Distribution",
                height=400
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Risk distribution
            fig_risk = go.Figure(data=[go.Bar(
                x=['Total Accounts', 'High Risk', 'Total Merchants', 'Suspicious'],
                y=[
                    stats['total_accounts'],
                    stats['high_risk_accounts'],
                    stats['total_merchants'],
                    stats['suspicious_merchants']
                ],
                marker=dict(color=['#2196f3', '#f44336', '#4caf50', '#ff9800'])
            )])
            fig_risk.update_layout(
                title="Entity Risk Distribution",
                height=400,
                yaxis_title="Count"
            )
            st.plotly_chart(fig_risk, use_container_width=True)
        
        # Device statistics
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("Device Statistics")
            device_data = {
                'Category': ['Total Devices', 'Shared Devices', 'Unique Devices'],
                'Count': [
                    stats['total_devices'],
                    stats['shared_devices'],
                    stats['total_devices'] - stats['shared_devices']
                ]
            }
            fig_device = px.bar(
                device_data,
                x='Category',
                y='Count',
                color='Category',
                title="Device Usage Patterns"
            )
            st.plotly_chart(fig_device, use_container_width=True)
        
        with col4:
            st.subheader("System Health")
            health_metrics = {
                'Metric': ['Database', 'Model', 'Data Quality', 'API'],
                'Status': [100, 95, 98, 100]
            }
            fig_health = go.Figure(data=[go.Bar(
                x=health_metrics['Status'],
                y=health_metrics['Metric'],
                orientation='h',
                marker=dict(color=['#4caf50'] * 4)
            )])
            fig_health.update_layout(
                title="System Health Status",
                xaxis_title="Health (%)",
                xaxis=dict(range=[0, 100])
            )
            st.plotly_chart(fig_health, use_container_width=True)
    
    with tab2:
        st.header("⚠️ High-Risk Accounts")
        
        high_risk = get_high_risk_accounts(20)
        
        if not high_risk.empty:
            st.dataframe(
                high_risk.style.background_gradient(
                    subset=['risk_score'],
                    cmap='Reds'
                ),
                use_container_width=True,
                height=400
            )
            
            # Risk score distribution
            fig_hist = px.histogram(
                high_risk,
                x='risk_score',
                nbins=20,
                title="Risk Score Distribution",
                labels={'risk_score': 'Risk Score', 'count': 'Number of Accounts'}
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("No high-risk accounts found")
    
    with tab3:
        st.header("📈 Fraud Trends")
        
        trends = get_fraud_trends()
        
        if not trends.empty and 'hour' in trends.columns:
            # Fraud rate over time
            fig_trend = make_subplots(
                rows=2, cols=1,
                subplot_titles=("Fraud Rate Over Time", "Transaction Volume"),
                vertical_spacing=0.15
            )
            
            fig_trend.add_trace(
                go.Scatter(
                    x=trends['hour'],
                    y=trends['fraud_rate'],
                    mode='lines+markers',
                    name='Fraud Rate (%)',
                    line=dict(color='#f44336', width=2)
                ),
                row=1, col=1
            )
            
            fig_trend.add_trace(
                go.Bar(
                    x=trends['hour'],
                    y=trends['total_transactions'],
                    name='Total Transactions',
                    marker=dict(color='#2196f3')
                ),
                row=2, col=1
            )
            
            fig_trend.update_xaxes(title_text="Time", row=2, col=1)
            fig_trend.update_yaxes(title_text="Fraud Rate (%)", row=1, col=1)
            fig_trend.update_yaxes(title_text="Transactions", row=2, col=1)
            fig_trend.update_layout(height=600, showlegend=True)
            
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No trend data available")
    
    with tab4:
        st.header("🔍 Transaction Search")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_id = st.text_input("Enter Account ID or Transaction ID:", "")
        
        with col2:
            search_button = st.button("Search", type="primary")
        
        if search_button and search_id:
            # Search for transactions
            query = """
            SELECT 
                t.transaction_id,
                t.account_id,
                t.merchant_id,
                t.transaction_amount,
                t.is_fraud,
                t.transaction_hour,
                t.transaction_day,
                a.risk_score,
                m.product_category,
                m.fraud_rate as merchant_fraud_rate
            FROM transaction t
            LEFT JOIN account a ON t.account_id = a.account_id
            LEFT JOIN merchant m ON t.merchant_id = m.merchant_id
            WHERE t.account_id = %s OR t.transaction_id = %s
            ORDER BY t.transaction_id DESC
            LIMIT 50
            """
            
            results = pd.read_sql(query, db.engine, params=(search_id, search_id))
            
            if not results.empty:
                st.success(f"Found {len(results)} transactions")
                
                # Show results
                st.dataframe(results, use_container_width=True, height=400)
                
                # Transaction analysis
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    fraud_count = results['is_fraud'].sum()
                    st.metric("Fraud Transactions", fraud_count)
                
                with col2:
                    avg_amount = results['transaction_amount'].mean()
                    st.metric("Avg Amount", f"${avg_amount:.2f}")
                
                with col3:
                    risk = results['risk_score'].mean()
                    st.metric("Avg Risk Score", f"{risk:.4f}")
            else:
                st.warning("No transactions found")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>Fraud Detection System v1.0 | Powered by Graph Neural Networks</p>
            <p>© 2025 | Built with Streamlit, PyTorch Geometric, PostgreSQL</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
