"""
Graph Construction Module
Converts database records into heterogeneous graph structure for GNN training
"""

import numpy as np
import pandas as pd
import networkx as nx
import torch
from torch_geometric.data import HeteroData
from typing import Dict, List, Tuple
import pickle
from pathlib import Path
import logging
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config.config import config
from src.database.connection import db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_PATH / 'graph_construction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    Builds heterogeneous graph from database records
    
    Graph Structure:
        Node Types: Account, Merchant, Device
        Edge Types:
            - Account -> Transaction -> Merchant (transacts_with)
            - Account -> Transaction -> Device (uses_device)
            - Account <-> Device (shared_device)
    """
    
    def __init__(self):
        self.graph_data = HeteroData()
        self.node_mappings = {}
        self.graph_stats = {}
    
    def fetch_account_nodes(self) -> pd.DataFrame:
        """Fetch account node features from database"""
        logger.info("Fetching account nodes...")
        
        query = """
            SELECT 
                account_id,
                risk_score,
                total_transactions,
                total_amount,
                account_age_days,
                CASE WHEN fraud_flag THEN 1 ELSE 0 END as fraud_flag
            FROM account
            ORDER BY account_id
        """
        
        accounts = pd.DataFrame(db.execute_query(query))
        logger.info(f"Loaded {len(accounts):,} account nodes")
        
        return accounts
    
    def fetch_merchant_nodes(self) -> pd.DataFrame:
        """Fetch merchant node features from database"""
        logger.info("Fetching merchant nodes...")
        
        query = """
            SELECT 
                merchant_id,
                fraud_rate,
                total_transactions,
                avg_transaction_amount,
                CASE 
                    WHEN risk_level = 'LOW' THEN 0
                    WHEN risk_level = 'MEDIUM' THEN 1
                    WHEN risk_level = 'HIGH' THEN 2
                    WHEN risk_level = 'CRITICAL' THEN 3
                    ELSE 0
                END as risk_level_encoded
            FROM merchant
            ORDER BY merchant_id
        """
        
        merchants = pd.DataFrame(db.execute_query(query))
        logger.info(f"Loaded {len(merchants):,} merchant nodes")
        
        return merchants
    
    def fetch_device_nodes(self) -> pd.DataFrame:
        """Fetch device node features from database"""
        logger.info("Fetching device nodes...")
        
        query = """
            SELECT 
                device_id,
                fraud_rate,
                total_users,
                total_transactions,
                CASE WHEN is_shared THEN 1 ELSE 0 END as is_shared,
                risk_score
            FROM device
            ORDER BY device_id
        """
        
        devices = pd.DataFrame(db.execute_query(query))
        logger.info(f"Loaded {len(devices):,} device nodes")
        
        return devices
    
    def fetch_transaction_edges(self) -> pd.DataFrame:
        """Fetch transaction edges (account -> merchant and account -> device)"""
        logger.info("Fetching transaction edges...")
        
        query = """
            SELECT 
                account_id,
                merchant_id,
                device_id,
                transaction_amount,
                transaction_hour,
                transaction_day_of_week,
                CASE WHEN is_fraud THEN 1 ELSE 0 END as is_fraud,
                transaction_date
            FROM transaction
            ORDER BY transaction_date
        """
        
        transactions = pd.DataFrame(db.execute_query(query))
        logger.info(f"Loaded {len(transactions):,} transaction edges")
        
        return transactions
    
    def fetch_shared_device_edges(self) -> pd.DataFrame:
        """Fetch shared device edges (account <-> device)"""
        logger.info("Fetching shared device edges...")
        
        query = """
            SELECT 
                device_id,
                account_id,
                transaction_count,
                fraud_count
            FROM shared_device
        """
        
        shared_devices = pd.DataFrame(db.execute_query(query))
        logger.info(f"Loaded {len(shared_devices):,} shared device edges")
        
        return shared_devices
    
    def create_node_mappings(self, accounts: pd.DataFrame, merchants: pd.DataFrame, 
                            devices: pd.DataFrame) -> Dict[str, Dict]:
        """
        Create mappings from node IDs to indices
        
        Returns:
            Dictionary of node type -> {id: index}
        """
        logger.info("Creating node ID mappings...")
        
        mappings = {
            'account': {aid: idx for idx, aid in enumerate(accounts['account_id'])},
            'merchant': {mid: idx for idx, mid in enumerate(merchants['merchant_id'])},
            'device': {did: idx for idx, did in enumerate(devices['device_id'])}
        }
        
        logger.info(f"  Account mapping: {len(mappings['account']):,} nodes")
        logger.info(f"  Merchant mapping: {len(mappings['merchant']):,} nodes")
        logger.info(f"  Device mapping: {len(mappings['device']):,} nodes")
        
        return mappings
    
    def build_account_features(self, accounts: pd.DataFrame) -> torch.Tensor:
        """Build account node feature matrix"""
        logger.info("Building account node features...")
        
        # Select numerical features
        features = accounts[[
            'risk_score',
            'total_transactions',
            'total_amount',
            'account_age_days',
            'fraud_flag'
        ]].fillna(0).values
        
        # Normalize features (except fraud_flag)
        features = features.astype(np.float32)
        
        # Log transform for amount and transactions (to handle large values)
        features[:, 1] = np.log1p(features[:, 1])  # total_transactions
        features[:, 2] = np.log1p(features[:, 2])  # total_amount
        features[:, 3] = np.log1p(features[:, 3])  # account_age_days
        
        # Standardize (mean=0, std=1)
        for i in range(features.shape[1] - 1):  # Exclude fraud_flag
            mean = features[:, i].mean()
            std = features[:, i].std()
            if std > 0:
                features[:, i] = (features[:, i] - mean) / std
        
        logger.info(f"  Feature shape: {features.shape}")
        
        return torch.tensor(features, dtype=torch.float)
    
    def build_merchant_features(self, merchants: pd.DataFrame) -> torch.Tensor:
        """Build merchant node feature matrix"""
        logger.info("Building merchant node features...")
        
        features = merchants[[
            'fraud_rate',
            'total_transactions',
            'avg_transaction_amount',
            'risk_level_encoded'
        ]].fillna(0).values.astype(np.float32)
        
        # Log transform
        features[:, 1] = np.log1p(features[:, 1])  # total_transactions
        features[:, 2] = np.log1p(features[:, 2])  # avg_transaction_amount
        
        # Standardize
        for i in range(features.shape[1] - 1):  # Exclude risk_level
            mean = features[:, i].mean()
            std = features[:, i].std()
            if std > 0:
                features[:, i] = (features[:, i] - mean) / std
        
        logger.info(f"  Feature shape: {features.shape}")
        
        return torch.tensor(features, dtype=torch.float)
    
    def build_device_features(self, devices: pd.DataFrame) -> torch.Tensor:
        """Build device node feature matrix"""
        logger.info("Building device node features...")
        
        features = devices[[
            'fraud_rate',
            'total_users',
            'total_transactions',
            'is_shared',
            'risk_score'
        ]].fillna(0).values.astype(np.float32)
        
        # Log transform
        features[:, 1] = np.log1p(features[:, 1])  # total_users
        features[:, 2] = np.log1p(features[:, 2])  # total_transactions
        
        # Standardize
        for i in range(features.shape[1]):
            if i == 3:  # Skip is_shared (binary)
                continue
            mean = features[:, i].mean()
            std = features[:, i].std()
            if std > 0:
                features[:, i] = (features[:, i] - mean) / std
        
        logger.info(f"  Feature shape: {features.shape}")
        
        return torch.tensor(features, dtype=torch.float)
    
    def build_transaction_edges(self, transactions: pd.DataFrame, 
                               mappings: Dict) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Build edges for account-merchant transactions
        
        Returns:
            edge_index, edge_features, edge_labels
        """
        logger.info("Building transaction edges (account -> merchant)...")
        
        # Filter transactions with valid nodes
        valid_txns = transactions[
            transactions['account_id'].isin(mappings['account']) &
            transactions['merchant_id'].isin(mappings['merchant'])
        ].copy()
        
        logger.info(f"  Valid transactions: {len(valid_txns):,}")
        
        # Map to indices
        src_nodes = valid_txns['account_id'].map(mappings['account']).values
        dst_nodes = valid_txns['merchant_id'].map(mappings['merchant']).values
        
        edge_index = torch.tensor([src_nodes, dst_nodes], dtype=torch.long)
        
        # Edge features
        edge_features = valid_txns[[
            'transaction_amount',
            'transaction_hour',
            'transaction_day_of_week'
        ]].fillna(0).values.astype(np.float32)
        
        # Log transform amount
        edge_features[:, 0] = np.log1p(edge_features[:, 0])
        
        # Standardize
        for i in range(edge_features.shape[1]):
            mean = edge_features[:, i].mean()
            std = edge_features[:, i].std()
            if std > 0:
                edge_features[:, i] = (edge_features[:, i] - mean) / std
        
        edge_features = torch.tensor(edge_features, dtype=torch.float)
        
        # Edge labels (fraud or not)
        edge_labels = torch.tensor(valid_txns['is_fraud'].values, dtype=torch.long)
        
        logger.info(f"  Edge index shape: {edge_index.shape}")
        logger.info(f"  Edge features shape: {edge_features.shape}")
        logger.info(f"  Fraud edges: {edge_labels.sum():,} ({edge_labels.float().mean()*100:.2f}%)")
        
        return edge_index, edge_features, edge_labels
    
    def build_device_edges(self, transactions: pd.DataFrame, 
                          mappings: Dict) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Build edges for account-device usage
        
        Returns:
            edge_index, edge_features
        """
        logger.info("Building device usage edges (account -> device)...")
        
        # Filter transactions with valid device
        valid_txns = transactions[
            transactions['account_id'].isin(mappings['account']) &
            transactions['device_id'].isin(mappings['device']) &
            transactions['device_id'].notna()
        ].copy()
        
        logger.info(f"  Valid device transactions: {len(valid_txns):,}")
        
        # Map to indices
        src_nodes = valid_txns['account_id'].map(mappings['account']).values
        dst_nodes = valid_txns['device_id'].map(mappings['device']).values
        
        edge_index = torch.tensor([src_nodes, dst_nodes], dtype=torch.long)
        
        # Edge features (transaction amount as feature)
        edge_features = valid_txns[['transaction_amount']].fillna(0).values.astype(np.float32)
        edge_features = np.log1p(edge_features)
        edge_features = torch.tensor(edge_features, dtype=torch.float)
        
        logger.info(f"  Edge index shape: {edge_index.shape}")
        
        return edge_index, edge_features
    
    def build_shared_device_edges(self, shared_devices: pd.DataFrame, 
                                  mappings: Dict) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Build edges for shared devices (account -> device only)
        Bidirectional edges added separately in build_hetero_graph
        
        Returns:
            edge_index, edge_features
        """
        logger.info("Building shared device edges (account -> device)...")
        
        # Filter valid edges
        valid_shared = shared_devices[
            shared_devices['account_id'].isin(mappings['account']) &
            shared_devices['device_id'].isin(mappings['device'])
        ].copy()
        
        logger.info(f"  Valid shared device edges: {len(valid_shared):,}")
        
        # Create unidirectional edges (account -> device)
        src_nodes = valid_shared['account_id'].map(mappings['account']).values
        dst_nodes = valid_shared['device_id'].map(mappings['device']).values
        
        edge_index = torch.tensor([src_nodes, dst_nodes], dtype=torch.long)
        
        # Edge features
        edge_features = valid_shared[[
            'transaction_count',
            'fraud_count'
        ]].values.astype(np.float32)
        
        # Log transform
        edge_features = np.log1p(edge_features)
        edge_features = torch.tensor(edge_features, dtype=torch.float)
        
        logger.info(f"  Edge index shape: {edge_index.shape}")
        
        return edge_index, edge_features
    
    def build_hetero_graph(self) -> HeteroData:
        """
        Build complete heterogeneous graph
        
        Returns:
            HeteroData object with all nodes and edges
        """
        logger.info("=" * 70)
        logger.info("Building Heterogeneous Graph")
        logger.info("=" * 70)
        
        # Fetch data from database
        accounts = self.fetch_account_nodes()
        merchants = self.fetch_merchant_nodes()
        devices = self.fetch_device_nodes()
        transactions = self.fetch_transaction_edges()
        shared_devices = self.fetch_shared_device_edges()
        
        # Create node mappings
        self.node_mappings = self.create_node_mappings(accounts, merchants, devices)
        
        # Build node features
        account_features = self.build_account_features(accounts)
        merchant_features = self.build_merchant_features(merchants)
        device_features = self.build_device_features(devices)
        
        # Build edges
        txn_edge_index, txn_edge_features, txn_edge_labels = self.build_transaction_edges(
            transactions, self.node_mappings
        )
        device_edge_index, device_edge_features = self.build_device_edges(
            transactions, self.node_mappings
        )
        shared_edge_index, shared_edge_features = self.build_shared_device_edges(
            shared_devices, self.node_mappings
        )
        
        # Create HeteroData object
        data = HeteroData()
        
        # Add node features
        data['account'].x = account_features
        data['merchant'].x = merchant_features
        data['device'].x = device_features
        
        # Add account labels (for node classification)
        data['account'].y = torch.tensor(accounts['fraud_flag'].values, dtype=torch.long)
        
        # Add edges: account -> merchant
        data['account', 'transacts_with', 'merchant'].edge_index = txn_edge_index
        data['account', 'transacts_with', 'merchant'].edge_attr = txn_edge_features
        data['account', 'transacts_with', 'merchant'].edge_label = txn_edge_labels
        
        # Add reverse edges: merchant -> account (for message passing)
        data['merchant', 'rev_transacts_with', 'account'].edge_index = torch.stack([
            txn_edge_index[1], txn_edge_index[0]
        ])
        
        # Add edges: account -> device
        data['account', 'uses', 'device'].edge_index = device_edge_index
        data['account', 'uses', 'device'].edge_attr = device_edge_features
        
        # Add reverse edges: device -> account (for message passing)
        data['device', 'used_by', 'account'].edge_index = torch.stack([
            device_edge_index[1], device_edge_index[0]
        ])
        
        # Add edges: account <-> device (shared)
        data['account', 'shares', 'device'].edge_index = shared_edge_index
        data['account', 'shares', 'device'].edge_attr = shared_edge_features
        
        # Add reverse shared edges: device -> account
        data['device', 'shared_by', 'account'].edge_index = torch.stack([
            shared_edge_index[1], shared_edge_index[0]
        ])
        data['device', 'shared_by', 'account'].edge_attr = shared_edge_features
        
        # Store statistics
        self.graph_stats = {
            'num_accounts': len(accounts),
            'num_merchants': len(merchants),
            'num_devices': len(devices),
            'num_transactions': len(txn_edge_index[0]),
            'num_device_usage': len(device_edge_index[0]),
            'num_shared_devices': len(shared_edge_index[0]) * 2,  # Bidirectional
            'fraud_rate': txn_edge_labels.float().mean().item(),
            'fraud_accounts': data['account'].y.sum().item()
        }
        
        self.print_graph_stats(data)
        
        return data
    
    def print_graph_stats(self, data: HeteroData) -> None:
        """Print graph statistics"""
        logger.info("\n" + "=" * 70)
        logger.info("Graph Statistics")
        logger.info("=" * 70)
        
        logger.info(f"\nNode Types:")
        logger.info(f"  • Accounts: {self.graph_stats['num_accounts']:,}")
        logger.info(f"  • Merchants: {self.graph_stats['num_merchants']:,}")
        logger.info(f"  • Devices: {self.graph_stats['num_devices']:,}")
        
        logger.info(f"\nEdge Types:")
        logger.info(f"  • Transactions (account→merchant): {self.graph_stats['num_transactions']:,}")
        logger.info(f"  • Device Usage (account→device): {self.graph_stats['num_device_usage']:,}")
        logger.info(f"  • Shared Devices (account↔device): {self.graph_stats['num_shared_devices']:,}")
        
        logger.info(f"\nLabels:")
        logger.info(f"  • Fraud Accounts: {self.graph_stats['fraud_accounts']:,}")
        logger.info(f"  • Transaction Fraud Rate: {self.graph_stats['fraud_rate']*100:.4f}%")
        
        logger.info(f"\nFeature Dimensions:")
        logger.info(f"  • Account features: {data['account'].x.shape[1]}")
        logger.info(f"  • Merchant features: {data['merchant'].x.shape[1]}")
        logger.info(f"  • Device features: {data['device'].x.shape[1]}")
        
        logger.info("=" * 70)
    
    def save_graph(self, data: HeteroData, filename: str = 'fraud_graph.pt') -> None:
        """Save graph to disk"""
        filepath = config.DATA_PROCESSED_PATH / filename
        
        logger.info(f"\nSaving graph to {filepath}...")
        torch.save(data, filepath)
        
        # Save mappings separately
        mappings_file = config.DATA_PROCESSED_PATH / 'node_mappings.pkl'
        with open(mappings_file, 'wb') as f:
            pickle.dump(self.node_mappings, f)
        
        # Save statistics
        stats_file = config.DATA_PROCESSED_PATH / 'graph_stats.pkl'
        with open(stats_file, 'wb') as f:
            pickle.dump(self.graph_stats, f)
        
        logger.info(f"✓ Graph saved successfully")
        logger.info(f"✓ Node mappings saved to {mappings_file.name}")
        logger.info(f"✓ Graph statistics saved to {stats_file.name}")


def main():
    """Main execution"""
    logger.info("Starting graph construction pipeline...")
    
    # Check database connection
    if not db.test_connection():
        logger.error("Cannot connect to database!")
        sys.exit(1)
    
    # Build graph
    builder = GraphBuilder()
    graph_data = builder.build_hetero_graph()
    
    # Save graph
    builder.save_graph(graph_data)
    
    logger.info("\n" + "=" * 70)
    logger.info("✓ Graph construction completed successfully!")
    logger.info("=" * 70)
    logger.info("\nNext steps:")
    logger.info("  1. Train GNN model: python src/training/train.py")
    logger.info("  2. Evaluate model: python src/training/evaluate.py")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
