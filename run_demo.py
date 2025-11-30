"""
Fraud Detection System - Interactive Demo
Demonstrates the system components without requiring a live database
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.config.config import Config

# Color codes
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    YELLOW = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print formatted header"""
    width = 80
    print(f"\n{Colors.BOLD}{Colors.OKBLUE}{'='*width}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKBLUE}{text.center(width)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKBLUE}{'='*width}{Colors.ENDC}\n")


def print_section(text):
    """Print section header"""
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}► {text}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'-'*60}{Colors.ENDC}")


def print_success(text):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def demo_1_system_overview():
    """Demo 1: System Overview"""
    print_header("🔍 FRAUD DETECTION SYSTEM - INTERACTIVE DEMO")
    
    print(f"{Colors.BOLD}Project: Graph Neural Network-Based Fraud Detection{Colors.ENDC}")
    print(f"Location: {Path.cwd()}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print_section("SYSTEM OVERVIEW")
    
    print(f"{Colors.BOLD}Architecture Components:{Colors.ENDC}")
    print("""
    1. DATABASE LAYER
       └─ PostgreSQL-based transaction storage
          • Account information & risk profiles
          • Merchant & device data
          • Transaction records with fraud labels
          • Device-sharing patterns
    
    2. PREPROCESSING & FEATURE ENGINEERING
       └─ Data cleaning and transformation
          • Temporal features (time-of-day, day-of-week)
          • Behavioral features (spending patterns)
          • Device fingerprinting
          • Network features (shared devices)
    
    3. GRAPH CONSTRUCTION
       └─ Dynamic fraud detection graph
          • Nodes: Accounts, Merchants, Devices
          • Edges: Transaction relationships
          • Attributes: Amount, time, location, behavior
    
    4. GRAPH NEURAL NETWORKS
       └─ Multiple GNN architectures:
          • GraphSAGE: Aggregates neighborhood information
          • GAT: Attention-based relationship weighting
          • R-GCN: Relational graph convolutional networks
    
    5. PREDICTION & MONITORING
       └─ Real-time fraud risk scoring
          • Transaction flagging
          • Account risk assessment
          • Pattern-based detection
    """)
    
    print_success("System Overview Loaded")


def demo_2_project_structure():
    """Demo 2: Project Structure"""
    print_section("PROJECT STRUCTURE")
    
    structure = {
        'data/': 'Raw and processed datasets',
        'database/': 'Schema definitions and SQL queries',
        'src/config/': 'Configuration management',
        'src/database/': 'Database connections and utilities',
        'src/preprocessing/': 'Data loading and transformation',
        'src/graph/': 'Graph construction modules',
        'src/models/': 'GNN model architectures (GAT, GraphSAGE, R-GCN)',
        'src/training/': 'Training pipelines and metrics',
        'src/visualization/': 'Streamlit dashboard and visualizations',
        'checkpoints/': 'Trained model weights',
        'logs/': 'Training and system logs',
    }
    
    print(f"{Colors.BOLD}Directory Structure:{Colors.ENDC}")
    for path, description in structure.items():
        base_path = Path(__file__).parent / path
        exists = "✓" if base_path.exists() else "✗"
        status = Colors.OKGREEN if base_path.exists() else Colors.FAIL
        print(f"  {status}{exists}{Colors.ENDC} {path:30s} - {description}")
    
    print_success("Project Structure Verified")


def demo_3_configuration():
    """Demo 3: Configuration"""
    print_section("SYSTEM CONFIGURATION")
    
    print(f"{Colors.BOLD}Current Configuration:{Colors.ENDC}\n")
    
    # Database Config
    print(f"  {Colors.BOLD}Database:{Colors.ENDC}")
    print(f"    Host: {Config.DB_HOST}:{Config.DB_PORT}")
    print(f"    Name: {Config.DB_NAME}")
    print(f"    User: {Config.DB_USER}")
    
    # Model Config
    print(f"\n  {Colors.BOLD}Model Training:{Colors.ENDC}")
    print(f"    GNN Type: {Config.GNN_MODEL_TYPE}")
    print(f"    Hidden Dimensions: {Config.HIDDEN_DIM}")
    print(f"    Num Layers: {Config.NUM_LAYERS}")
    print(f"    Dropout: {Config.DROPOUT}")
    print(f"    Learning Rate: {Config.LEARNING_RATE}")
    print(f"    Batch Size: {Config.TRAIN_BATCH_SIZE}")
    print(f"    Epochs: {Config.NUM_EPOCHS}")
    print(f"    Random Seed: {Config.RANDOM_SEED}")
    
    # Paths
    print(f"\n  {Colors.BOLD}Paths:{Colors.ENDC}")
    print(f"    Data Raw: {Config.DATA_RAW_PATH}")
    print(f"    Data Processed: {Config.DATA_PROCESSED_PATH}")
    print(f"    Checkpoints: {Config.MODEL_CHECKPOINT_PATH}")
    print(f"    Logs: {Config.LOG_PATH}")
    
    print_success("Configuration Loaded")


def demo_4_synthetic_data():
    """Demo 4: Synthetic Data Generation & Analysis"""
    print_section("SYNTHETIC TRANSACTION DATA")
    
    print(f"{Colors.BOLD}Generating synthetic transaction dataset...{Colors.ENDC}\n")
    
    # Generate synthetic data
    np.random.seed(Config.RANDOM_SEED)
    torch.manual_seed(Config.RANDOM_SEED)
    
    n_transactions = 1000
    n_accounts = 100
    n_merchants = 50
    n_devices = 75
    
    # Transaction attributes
    transactions = {
        'transaction_id': range(1, n_transactions + 1),
        'account_id': np.random.randint(1, n_accounts + 1, n_transactions),
        'merchant_id': np.random.randint(1, n_merchants + 1, n_transactions),
        'device_id': np.random.randint(1, n_devices + 1, n_transactions),
        'transaction_amount': np.random.lognormal(3.5, 1.5, n_transactions),  # Log-normal distribution
        'transaction_date': [datetime.now() - timedelta(days=np.random.randint(0, 365)) 
                            for _ in range(n_transactions)],
    }
    
    # Fraud labels (5% fraud rate)
    fraud_rate = 0.05
    is_fraud = np.random.binomial(1, fraud_rate, n_transactions).astype(bool)
    
    # Add fraud-specific patterns
    fraud_indices = np.where(is_fraud)[0]
    for idx in fraud_indices:
        # Fraudulent transactions tend to be larger and from different devices
        transactions['transaction_amount'][idx] *= np.random.uniform(2, 5)
        transactions['device_id'][idx] = np.random.randint(1, n_devices + 1)
    
    transactions['is_fraud'] = is_fraud
    
    df = pd.DataFrame(transactions)
    
    print_info(f"Generated {len(df):,} transactions")
    print_info(f"Unique accounts: {df['account_id'].nunique()}")
    print_info(f"Unique merchants: {df['merchant_id'].nunique()}")
    print_info(f"Unique devices: {df['device_id'].nunique()}\n")
    
    # Statistics
    print(f"{Colors.BOLD}Transaction Statistics:{Colors.ENDC}\n")
    
    fraud_count = df['is_fraud'].sum()
    fraud_pct = (fraud_count / len(df)) * 100
    
    stats_df = pd.DataFrame({
        'Metric': ['Total Transactions', 'Fraudulent', 'Legitimate', 'Fraud Rate'],
        'Count': [len(df), fraud_count, len(df) - fraud_count, f'{fraud_pct:.2f}%'],
    })
    
    print(stats_df.to_string(index=False))
    
    print(f"\n{Colors.BOLD}Amount Statistics:{Colors.ENDC}\n")
    print(f"  Mean Amount: ${df['transaction_amount'].mean():.2f}")
    print(f"  Median Amount: ${df['transaction_amount'].median():.2f}")
    print(f"  Min Amount: ${df['transaction_amount'].min():.2f}")
    print(f"  Max Amount: ${df['transaction_amount'].max():.2f}")
    print(f"  Std Dev: ${df['transaction_amount'].std():.2f}")
    
    print(f"\n{Colors.BOLD}Fraud vs Legitimate Average Amount:{Colors.ENDC}\n")
    fraud_avg = df[df['is_fraud']]['transaction_amount'].mean()
    legit_avg = df[~df['is_fraud']]['transaction_amount'].mean()
    print(f"  Fraudulent Avg: ${fraud_avg:.2f}")
    print(f"  Legitimate Avg: ${legit_avg:.2f}")
    print(f"  Difference: {((fraud_avg/legit_avg - 1) * 100):.1f}%")
    
    print(f"\n{Colors.BOLD}Sample Transactions:{Colors.ENDC}\n")
    sample = df.sample(min(5, len(df)))[['transaction_id', 'account_id', 'transaction_amount', 'is_fraud']].copy()
    sample['Status'] = sample['is_fraud'].apply(lambda x: '⚠️ FRAUD' if x else '✓ OK')
    print(sample[['transaction_id', 'account_id', 'transaction_amount', 'Status']].to_string(index=False))
    
    print_success("Synthetic Data Generated")
    
    return df


def demo_5_feature_engineering(df):
    """Demo 5: Feature Engineering"""
    print_section("FEATURE ENGINEERING")
    
    print(f"{Colors.BOLD}Generating transaction features...{Colors.ENDC}\n")
    
    df_features = df.copy()
    
    # Temporal features
    df_features['hour'] = df_features['transaction_date'].dt.hour
    df_features['day_of_week'] = df_features['transaction_date'].dt.dayofweek
    df_features['day_of_month'] = df_features['transaction_date'].dt.day
    
    # Amount-based features
    account_avg_amount = df_features.groupby('account_id')['transaction_amount'].mean()
    df_features['amount_vs_avg'] = df_features.apply(
        lambda row: row['transaction_amount'] / account_avg_amount[row['account_id']]
        if row['account_id'] in account_avg_amount.index else 1.0, axis=1
    )
    
    # Behavioral features
    account_txn_count = df_features['account_id'].value_counts()
    df_features['account_activity'] = df_features['account_id'].map(account_txn_count)
    
    merchant_txn_count = df_features['merchant_id'].value_counts()
    df_features['merchant_popularity'] = df_features['merchant_id'].map(merchant_txn_count)
    
    # Device features
    device_txn_count = df_features['device_id'].value_counts()
    df_features['device_activity'] = df_features['device_id'].map(device_txn_count)
    
    feature_cols = ['hour', 'day_of_week', 'day_of_month', 'amount_vs_avg', 
                   'account_activity', 'merchant_popularity', 'device_activity']
    
    print(f"{Colors.BOLD}Generated Features:{Colors.ENDC}\n")
    for feature in feature_cols:
        print(f"  • {feature}")
    
    print(f"\n{Colors.BOLD}Feature Statistics (Sample):{Colors.ENDC}\n")
    feature_stats = df_features[feature_cols].describe().loc[['mean', 'std', 'min', 'max']].T
    print(feature_stats.to_string())
    
    print_success("Features Generated")
    
    return df_features


def demo_6_graph_construction(df):
    """Demo 6: Graph Construction"""
    print_section("GRAPH CONSTRUCTION")
    
    print(f"{Colors.BOLD}Building heterogeneous fraud detection graph...{Colors.ENDC}\n")
    
    # Node counts
    n_accounts = df['account_id'].nunique()
    n_merchants = df['merchant_id'].nunique()
    n_devices = df['device_id'].nunique()
    
    print(f"{Colors.BOLD}Graph Nodes:{Colors.ENDC}\n")
    print(f"  Account Nodes: {n_accounts}")
    print(f"  Merchant Nodes: {n_merchants}")
    print(f"  Device Nodes: {n_devices}")
    print(f"  Total Nodes: {n_accounts + n_merchants + n_devices}")
    
    # Edge construction
    print(f"\n{Colors.BOLD}Graph Edges:{Colors.ENDC}\n")
    
    # Account-Merchant edges (transactions)
    account_merchant_edges = df[['account_id', 'merchant_id']].drop_duplicates()
    print(f"  Account-Merchant edges: {len(account_merchant_edges)}")
    
    # Account-Device edges (device usage)
    account_device_edges = df[['account_id', 'device_id']].drop_duplicates()
    print(f"  Account-Device edges: {len(account_device_edges)}")
    
    # Merchant-Device edges (merchant access via devices)
    merchant_device_edges = df[['merchant_id', 'device_id']].drop_duplicates()
    print(f"  Merchant-Device edges: {len(merchant_device_edges)}")
    
    total_edges = (len(account_merchant_edges) + len(account_device_edges) + 
                   len(merchant_device_edges))
    print(f"  Total Edges: {total_edges}")
    
    # Edge attributes
    print(f"\n{Colors.BOLD}Edge Attributes:{Colors.ENDC}\n")
    print("""
  • Transaction Amount
  • Transaction Count
  • Average Amount
  • Fraud Probability
  • Temporal Features (hour, day)
  • Behavioral Indicators
    """)
    
    # Graph statistics
    print(f"{Colors.BOLD}Graph Statistics:{Colors.ENDC}\n")
    density = total_edges / (n_accounts + n_merchants + n_devices) ** 2
    print(f"  Graph Density: {density:.6f}")
    print(f"  Avg Connections per Node: {total_edges / (n_accounts + n_merchants + n_devices):.2f}")
    print(f"  Graph Type: Heterogeneous Directed Multigraph")
    
    print_success("Graph Constructed")


def demo_7_model_architectures():
    """Demo 7: GNN Model Architectures"""
    print_section("GRAPH NEURAL NETWORK MODELS")
    
    print(f"{Colors.BOLD}Available Model Architectures:{Colors.ENDC}\n")
    
    models = {
        'GraphSAGE': {
            'description': 'Sample and Aggregate (neighborhood sampling)',
            'features': [
                'Neighborhood aggregation via sampling',
                'Scalable to large graphs',
                'Inductive learning capability',
                'Flexible aggregator functions'
            ],
            'use_case': 'Large-scale fraud detection with new accounts'
        },
        'GAT': {
            'description': 'Graph Attention Networks',
            'features': [
                'Attention-based edge weighting',
                'Learns importance of neighbors',
                'Multi-head attention mechanism',
                'Interpretable attention weights'
            ],
            'use_case': 'Understanding key fraud relationships'
        },
        'R-GCN': {
            'description': 'Relational Graph Convolutional Networks',
            'features': [
                'Handles multiple edge types',
                'Type-specific transformations',
                'Basis decomposition for efficiency',
                'Supports heterogeneous graphs'
            ],
            'use_case': 'Multi-relation fraud detection networks'
        }
    }
    
    for model_name, info in models.items():
        print(f"  {Colors.BOLD}{Colors.OKGREEN}► {model_name}{Colors.ENDC}")
        print(f"    Description: {info['description']}")
        print(f"    Key Features:")
        for feature in info['features']:
            print(f"      • {feature}")
        print(f"    Best For: {info['use_case']}\n")
    
    # Model configuration
    print(f"{Colors.BOLD}Model Configuration:{Colors.ENDC}\n")
    print(f"  Selected Model: {Config.GNN_MODEL_TYPE}")
    print(f"  Hidden Dimensions: {Config.HIDDEN_DIM}")
    print(f"  Number of Layers: {Config.NUM_LAYERS}")
    print(f"  Dropout Rate: {Config.DROPOUT}")
    print(f"  Learning Rate: {Config.LEARNING_RATE}")
    print(f"  Batch Size: {Config.TRAIN_BATCH_SIZE}")
    print(f"  Maximum Epochs: {Config.NUM_EPOCHS}")
    print(f"  Early Stopping Patience: {Config.EARLY_STOPPING_PATIENCE}")
    
    print_success("Model Architectures Overview")


def demo_8_fraud_detection_demo(df):
    """Demo 8: Simulated Fraud Detection"""
    print_section("SIMULATED FRAUD DETECTION")
    
    print(f"{Colors.BOLD}Running fraud risk assessment on sample transactions...{Colors.ENDC}\n")
    
    # Simulate GNN predictions
    np.random.seed(Config.RANDOM_SEED)
    
    # Generate fraud probabilities (biased towards actual labels)
    df_pred = df.copy()
    df_pred['fraud_amount_ratio'] = df_pred['transaction_amount'] / df_pred['transaction_amount'].quantile(0.75)
    
    # Generate initial fraud probabilities
    fraud_probs = np.random.random(len(df_pred))
    df_pred['fraud_probability'] = np.clip(fraud_probs, 0, 1)
    
    # Adjust probabilities based on transaction characteristics
    for i in range(len(df_pred)):
        base_prob = fraud_probs[i]
        
        # Higher probability for larger transactions
        if df_pred.iloc[i]['fraud_amount_ratio'] > 1.5:
            base_prob *= 1.3
        
        # Higher probability for devices with unusual patterns
        device_fraud_rate = df[df['device_id'] == df_pred.iloc[i]['device_id']]['is_fraud'].mean()
        if device_fraud_rate > 0.1:
            base_prob *= 1.2
        
        df_pred.at[i, 'fraud_probability'] = min(base_prob, 1.0)
    
    # Adjust based on patterns
    for i in range(len(df_pred)):
        base_prob = df_pred.at[i, 'fraud_probability']
        # Increase for transactions with unusual amount
        if df_pred.iloc[i]['transaction_amount'] > df['transaction_amount'].quantile(0.95):
            base_prob = min(base_prob + 0.15, 1.0)
        # Increase for accounts with fraud history
        account_fraud_rate = df[df['account_id'] == df_pred.iloc[i]['account_id']]['is_fraud'].mean()
        if account_fraud_rate > 0.05:
            base_prob = min(base_prob + 0.1, 1.0)
        
        df_pred.at[i, 'fraud_probability'] = base_prob
    
    # Create predictions
    df_pred['predicted_fraud'] = (df_pred['fraud_probability'] > 0.5).astype(bool)
    
    # Evaluation metrics
    tp = ((df_pred['predicted_fraud']) & (df_pred['is_fraud'])).sum()
    tn = ((~df_pred['predicted_fraud']) & (~df_pred['is_fraud'])).sum()
    fp = ((df_pred['predicted_fraud']) & (~df_pred['is_fraud'])).sum()
    fn = ((~df_pred['predicted_fraud']) & (df_pred['is_fraud'])).sum()
    
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"{Colors.BOLD}Model Performance Metrics:{Colors.ENDC}\n")
    metrics_df = pd.DataFrame({
        'Metric': ['Accuracy', 'Precision', 'Recall', 'F1-Score'],
        'Score': [f'{accuracy:.4f}', f'{precision:.4f}', f'{recall:.4f}', f'{f1:.4f}']
    })
    print(metrics_df.to_string(index=False))
    
    print(f"\n{Colors.BOLD}Confusion Matrix:{Colors.ENDC}\n")
    print(f"  True Positives (Fraud Detected): {tp}")
    print(f"  True Negatives (Legitimate): {tn}")
    print(f"  False Positives (False Alarms): {fp}")
    print(f"  False Negatives (Missed Fraud): {fn}")
    
    # High-risk transactions
    print(f"\n{Colors.BOLD}High-Risk Transactions (Fraud Probability > 0.7):{Colors.ENDC}\n")
    high_risk = df_pred[df_pred['fraud_probability'] > 0.7].head(10)
    if len(high_risk) > 0:
        display = high_risk[['transaction_id', 'account_id', 'transaction_amount', 
                            'fraud_probability', 'is_fraud']].copy()
        display['Pred'] = display['fraud_probability'].apply(lambda x: f'{x:.2%}')
        display['Actual'] = display['is_fraud'].apply(lambda x: '⚠️ FRAUD' if x else '✓ OK')
        print(display[['transaction_id', 'account_id', 'transaction_amount', 'Pred', 'Actual']].to_string(index=False))
    else:
        print_info("No high-risk transactions detected")
    
    print_success("Fraud Detection Demo Complete")
    
    return df_pred


def demo_9_dashboard_info():
    """Demo 9: Dashboard Information"""
    print_section("INTERACTIVE DASHBOARD")
    
    print(f"{Colors.BOLD}Streamlit-Based Analytics Dashboard{Colors.ENDC}\n")
    
    print("""
  The system includes a real-time Streamlit dashboard with:
  
  📊 DASHBOARD FEATURES:
  
  1. Overview Metrics
     • Total Transactions & Fraud Rate
     • Risk Score Distribution
     • Fraud Trend Analysis
  
  2. Account Analysis
     • High-Risk Account Detection
     • Account Transaction History
     • Risk Score Progression
     • Device Association Patterns
  
  3. Merchant Insights
     • Merchant Fraud Statistics
     • Transaction Volume by Merchant
     • Risk Category Distribution
  
  4. Device Intelligence
     • Device Fingerprinting Data
     • Suspicious Device Patterns
     • Multi-Account Device Usage
  
  5. Graph Visualization
     • Account-Merchant Network
     • Device Sharing Patterns
     • Fraud Relationship Networks
  
  6. Prediction Analysis
     • Model Confidence Scores
     • Feature Importance
     • Risk Factor Analysis
  
  To run the dashboard:
  $ streamlit run src/visualization/simple_dashboard.py
    """)
    
    print_info(f"Dashboard runs on http://{Config.DASHBOARD_HOST}:{Config.DASHBOARD_PORT}")
    print_success("Dashboard Overview")


def demo_10_summary():
    """Demo 10: Summary & Next Steps"""
    print_section("SUMMARY & NEXT STEPS")
    
    print(f"{Colors.BOLD}Project Capabilities:{Colors.ENDC}\n")
    
    capabilities = [
        "Graph Neural Network-based fraud detection",
        "Multi-architecture support (GraphSAGE, GAT, R-GCN)",
        "Real-time transaction analysis",
        "Account risk profiling",
        "Merchant and device intelligence",
        "Interactive Streamlit dashboard",
        "Comprehensive logging and monitoring",
        "PostgreSQL-based data persistence"
    ]
    
    for i, cap in enumerate(capabilities, 1):
        print(f"  {i}. {cap}")
    
    print(f"\n{Colors.BOLD}Next Steps to Deploy:{Colors.ENDC}\n")
    
    steps = [
        ("1", "Configure Database", "Create .env file with PostgreSQL credentials"),
        ("2", "Setup Database", "Run: python src/database/setup_db.py"),
        ("3", "Load Data", "Run: python src/preprocessing/load_data.py"),
        ("4", "Train Models", "Run: python src/training/train.py"),
        ("5", "Launch Dashboard", "Run: streamlit run src/visualization/simple_dashboard.py"),
    ]
    
    for step, title, cmd in steps:
        print(f"  {Colors.BOLD}{step}{Colors.ENDC} {title}")
        print(f"     └─ {cmd}\n")
    
    print(f"{Colors.BOLD}Key Files:{Colors.ENDC}\n")
    print(f"  • src/models/graphsage.py - GraphSAGE implementation")
    print(f"  • src/models/gat.py - Graph Attention Network")
    print(f"  • src/models/rgcn.py - Relational GCN")
    print(f"  • src/training/train.py - Training pipeline")
    print(f"  • src/visualization/simple_dashboard.py - Analytics dashboard")
    print(f"  • database/queries/analytical_queries.sql - Analysis queries")
    
    print(f"\n{Colors.BOLD}Documentation:{Colors.ENDC}\n")
    print(f"  • README.md - Project overview")
    print(f"  • QUICKSTART.md - Quick setup guide")
    print(f"  • COMPLETE_DOCS.md - Comprehensive documentation")
    print(f"  • docs/ER_diagram.md - Database schema")
    print(f"  • docs/graph_schema.md - Graph structure")
    
    print_success("Demo Complete!")


def main():
    """Run all demos"""
    try:
        # Ensure directories exist
        Config.ensure_directories()
        
        # Run all demos
        demo_1_system_overview()
        input(f"\n{Colors.YELLOW}[Press Enter to continue...]{Colors.ENDC}")
        
        demo_2_project_structure()
        input(f"\n{Colors.YELLOW}[Press Enter to continue...]{Colors.ENDC}")
        
        demo_3_configuration()
        input(f"\n{Colors.YELLOW}[Press Enter to continue...]{Colors.ENDC}")
        
        df = demo_4_synthetic_data()
        input(f"\n{Colors.YELLOW}[Press Enter to continue...]{Colors.ENDC}")
        
        df_features = demo_5_feature_engineering(df)
        input(f"\n{Colors.YELLOW}[Press Enter to continue...]{Colors.ENDC}")
        
        demo_6_graph_construction(df)
        input(f"\n{Colors.YELLOW}[Press Enter to continue...]{Colors.ENDC}")
        
        demo_7_model_architectures()
        input(f"\n{Colors.YELLOW}[Press Enter to continue...]{Colors.ENDC}")
        
        df_pred = demo_8_fraud_detection_demo(df)
        input(f"\n{Colors.YELLOW}[Press Enter to continue...]{Colors.ENDC}")
        
        demo_9_dashboard_info()
        input(f"\n{Colors.YELLOW}[Press Enter to continue...]{Colors.ENDC}")
        
        demo_10_summary()
        
        print(f"\n{Colors.BOLD}{Colors.OKGREEN}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKGREEN}Thank you for exploring the Fraud Detection System!{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKGREEN}{'='*80}{Colors.ENDC}\n")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Demo interrupted by user{Colors.ENDC}\n")
        sys.exit(0)
    except Exception as e:
        print_error(f"Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
