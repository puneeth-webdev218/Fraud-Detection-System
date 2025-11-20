"""
Main Training Script for Fraud Detection GNN Models
Supports GraphSAGE, GAT, and R-GCN architectures
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import HeteroData
import numpy as np
import pickle
import argparse
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import logging
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config.config import config
from src.models import (
    GraphSAGEFraudDetector,
    GATFraudDetector,
    RGCNFraudDetector
)
from src.training.metrics import FraudMetrics, evaluate_model_all_splits
from src.training.utils import (
    create_stratified_split,
    EarlyStopping,
    save_checkpoint,
    compute_class_weights
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FraudDetectionTrainer:
    """
    Trainer for fraud detection GNN models
    """
    
    def __init__(
        self,
        model_type: str = 'graphsage',
        hidden_channels: int = 128,
        out_channels: int = 64,
        num_layers: int = 3,
        heads: int = 4,  # For GAT
        num_bases: int = None,  # For R-GCN
        dropout: float = 0.2,
        learning_rate: float = 0.001,
        weight_decay: float = 5e-4,
        batch_size: int = 128,
        num_epochs: int = 100,
        patience: int = 10,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
        random_seed: int = 42
    ):
        """
        Initialize trainer
        
        Args:
            model_type: 'graphsage', 'gat', or 'rgcn'
            hidden_channels: Hidden dimension
            out_channels: Output embedding dimension
            num_layers: Number of GNN layers
            heads: Number of attention heads (GAT only)
            num_bases: Number of bases (R-GCN only)
            dropout: Dropout rate
            learning_rate: Learning rate
            weight_decay: L2 regularization
            batch_size: Batch size (not used for full-batch training)
            num_epochs: Maximum epochs
            patience: Early stopping patience
            device: Device to use
            random_seed: Random seed
        """
        self.model_type = model_type.lower()
        self.hidden_channels = hidden_channels
        self.out_channels = out_channels
        self.num_layers = num_layers
        self.heads = heads
        self.num_bases = num_bases
        self.dropout = dropout
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.batch_size = batch_size
        self.num_epochs = num_epochs
        self.patience = patience
        self.device = device
        self.random_seed = random_seed
        
        # Set random seeds
        torch.manual_seed(random_seed)
        np.random.seed(random_seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(random_seed)
        
        self.model = None
        self.optimizer = None
        self.criterion = None
        self.data = None
        self.train_mask = None
        self.val_mask = None
        self.test_mask = None
        
        logger.info(f"Trainer initialized:")
        logger.info(f"  Model: {model_type}")
        logger.info(f"  Device: {device}")
        logger.info(f"  Hidden channels: {hidden_channels}")
        logger.info(f"  Num layers: {num_layers}")
    
    def load_graph(self, graph_path: str):
        """
        Load graph data
        
        Args:
            graph_path: Path to fraud_graph.pt
        """
        logger.info(f"Loading graph from {graph_path}...")
        
        self.data = torch.load(graph_path)
        self.data = self.data.to(self.device)
        
        logger.info(f"Graph loaded successfully:")
        logger.info(f"  Accounts: {self.data['account'].x.size(0)}")
        logger.info(f"  Merchants: {self.data['merchant'].x.size(0)}")
        logger.info(f"  Devices: {self.data['device'].x.size(0)}")
        logger.info(f"  Transaction edges: {self.data['account', 'transacts_with', 'merchant'].edge_index.size(1)}")
    
    def create_splits(
        self,
        train_ratio: float = 0.6,
        val_ratio: float = 0.2,
        test_ratio: float = 0.2
    ):
        """
        Create train/val/test splits
        
        Args:
            train_ratio: Training set ratio
            val_ratio: Validation set ratio
            test_ratio: Test set ratio
        """
        labels = self.data['account'].y
        
        self.train_mask, self.val_mask, self.test_mask = create_stratified_split(
            labels=labels,
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
            random_seed=self.random_seed
        )
        
        # Move masks to device
        self.train_mask = self.train_mask.to(self.device)
        self.val_mask = self.val_mask.to(self.device)
        self.test_mask = self.test_mask.to(self.device)
    
    def build_model(self):
        """Build GNN model based on model_type"""
        metadata = self.data.metadata()
        
        in_channels_dict = {
            'account': self.data['account'].x.size(1),
            'merchant': self.data['merchant'].x.size(1),
            'device': self.data['device'].x.size(1)
        }
        
        logger.info(f"Building {self.model_type} model...")
        
        if self.model_type == 'graphsage':
            self.model = GraphSAGEFraudDetector(
                metadata=metadata,
                in_channels_dict=in_channels_dict,
                hidden_channels=self.hidden_channels,
                out_channels=self.out_channels,
                num_layers=self.num_layers,
                dropout=self.dropout,
                target_node_type='account'
            )
        elif self.model_type == 'gat':
            self.model = GATFraudDetector(
                metadata=metadata,
                in_channels_dict=in_channels_dict,
                hidden_channels=self.hidden_channels,
                out_channels=self.out_channels,
                num_layers=self.num_layers,
                heads=self.heads,
                dropout=self.dropout,
                target_node_type='account'
            )
        elif self.model_type == 'rgcn':
            self.model = RGCNFraudDetector(
                metadata=metadata,
                in_channels_dict=in_channels_dict,
                hidden_channels=self.hidden_channels,
                out_channels=self.out_channels,
                num_layers=self.num_layers,
                num_bases=self.num_bases,
                dropout=self.dropout,
                target_node_type='account'
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        self.model = self.model.to(self.device)
        
        # Count parameters
        num_params = sum(p.numel() for p in self.model.parameters())
        logger.info(f"Model built with {num_params:,} parameters")
    
    def setup_training(self, use_class_weights: bool = True):
        """
        Setup optimizer and loss function
        
        Args:
            use_class_weights: Whether to use class weights for imbalanced data
        """
        self.optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=self.learning_rate,
            weight_decay=self.weight_decay
        )
        
        # Compute class weights if requested
        if use_class_weights:
            labels = self.data['account'].y[self.train_mask]
            class_weights = compute_class_weights(labels)
            pos_weight = class_weights[1] / class_weights[0]
            pos_weight = pos_weight.to(self.device)
            
            self.criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
            logger.info(f"Using weighted loss with pos_weight={pos_weight:.4f}")
        else:
            self.criterion = nn.BCEWithLogitsLoss()
            logger.info("Using unweighted loss")
    
    def train_epoch(self) -> float:
        """
        Train for one epoch
        
        Returns:
            Training loss
        """
        self.model.train()
        self.optimizer.zero_grad()
        
        # Forward pass
        logits = self.model(self.data.x_dict, self.data.edge_index_dict)
        
        # Compute loss on training nodes
        loss = self.criterion(
            logits[self.train_mask].squeeze(),
            self.data['account'].y[self.train_mask].float()
        )
        
        # Backward pass
        loss.backward()
        self.optimizer.step()
        
        return loss.item()
    
    @torch.no_grad()
    def evaluate_epoch(self, mask: torch.Tensor) -> dict:
        """
        Evaluate on given split
        
        Args:
            mask: Node mask for evaluation
            
        Returns:
            Dictionary of metrics
        """
        self.model.eval()
        
        logits = self.model(self.data.x_dict, self.data.edge_index_dict)
        probs = torch.sigmoid(logits).cpu().numpy().flatten()
        preds = (probs >= 0.5).astype(int)
        
        labels = self.data['account'].y.cpu().numpy()
        
        # Filter by mask
        mask_np = mask.cpu().numpy()
        labels = labels[mask_np]
        probs = probs[mask_np]
        preds = preds[mask_np]
        
        metrics = FraudMetrics.compute_metrics(
            y_true=labels,
            y_pred=preds,
            y_prob=probs
        )
        
        return metrics
    
    def train(self, save_best: bool = True):
        """
        Complete training loop with early stopping
        
        Args:
            save_best: Whether to save best model
        """
        logger.info("="*70)
        logger.info("Starting training...")
        logger.info("="*70)
        
        early_stopping = EarlyStopping(
            patience=self.patience,
            mode='max',
            min_delta=0.001
        )
        
        best_val_f1 = 0
        best_epoch = 0
        history = {
            'train_loss': [],
            'train_f1': [],
            'val_f1': [],
            'val_roc_auc': []
        }
        
        for epoch in range(1, self.num_epochs + 1):
            # Train
            train_loss = self.train_epoch()
            
            # Evaluate
            train_metrics = self.evaluate_epoch(self.train_mask)
            val_metrics = self.evaluate_epoch(self.val_mask)
            
            # Record history
            history['train_loss'].append(train_loss)
            history['train_f1'].append(train_metrics['f1'])
            history['val_f1'].append(val_metrics['f1'])
            history['val_roc_auc'].append(val_metrics.get('roc_auc', 0))
            
            # Print progress
            if epoch % 5 == 0 or epoch == 1:
                logger.info(
                    f"Epoch {epoch:03d} | "
                    f"Loss: {train_loss:.4f} | "
                    f"Train F1: {train_metrics['f1']:.4f} | "
                    f"Val F1: {val_metrics['f1']:.4f} | "
                    f"Val AUC: {val_metrics.get('roc_auc', 0):.4f}"
                )
            
            # Save best model
            if val_metrics['f1'] > best_val_f1:
                best_val_f1 = val_metrics['f1']
                best_epoch = epoch
                
                if save_best:
                    checkpoint_path = config.MODEL_CHECKPOINT_PATH / f'best_{self.model_type}.pt'
                    save_checkpoint(
                        self.model,
                        self.optimizer,
                        epoch,
                        val_metrics,
                        str(checkpoint_path)
                    )
            
            # Early stopping
            if early_stopping(val_metrics['f1']):
                logger.info(f"\nEarly stopping triggered at epoch {epoch}")
                break
        
        logger.info("="*70)
        logger.info(f"Training completed!")
        logger.info(f"Best epoch: {best_epoch} with Val F1: {best_val_f1:.4f}")
        logger.info("="*70)
        
        return history
    
    def evaluate_final(self):
        """Evaluate on all splits and print detailed results"""
        logger.info("\n" + "="*70)
        logger.info("FINAL EVALUATION")
        logger.info("="*70)
        
        splits = {
            'Train': self.train_mask,
            'Validation': self.val_mask,
            'Test': self.test_mask
        }
        
        for split_name, mask in splits.items():
            logger.info(f"\n{split_name} Set Results:")
            logger.info("-" * 50)
            
            metrics = self.evaluate_epoch(mask)
            FraudMetrics.print_metrics(metrics, prefix="  ")


def main():
    """Main training function"""
    parser = argparse.ArgumentParser(description='Train Fraud Detection GNN')
    
    # Model arguments
    parser.add_argument('--model', type=str, default='graphsage',
                        choices=['graphsage', 'gat', 'rgcn'],
                        help='GNN model type')
    parser.add_argument('--hidden-dim', type=int, default=128,
                        help='Hidden dimension')
    parser.add_argument('--out-dim', type=int, default=64,
                        help='Output dimension')
    parser.add_argument('--num-layers', type=int, default=3,
                        help='Number of GNN layers')
    parser.add_argument('--heads', type=int, default=4,
                        help='Number of attention heads (GAT only)')
    parser.add_argument('--num-bases', type=int, default=None,
                        help='Number of bases (R-GCN only)')
    parser.add_argument('--dropout', type=float, default=0.2,
                        help='Dropout rate')
    
    # Training arguments
    parser.add_argument('--lr', type=float, default=0.001,
                        help='Learning rate')
    parser.add_argument('--weight-decay', type=float, default=5e-4,
                        help='Weight decay')
    parser.add_argument('--epochs', type=int, default=100,
                        help='Maximum epochs')
    parser.add_argument('--patience', type=int, default=10,
                        help='Early stopping patience')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed')
    
    # Data arguments
    parser.add_argument('--graph-path', type=str,
                        default=None,
                        help='Path to graph file')
    parser.add_argument('--train-ratio', type=float, default=0.6,
                        help='Training set ratio')
    parser.add_argument('--val-ratio', type=float, default=0.2,
                        help='Validation set ratio')
    
    args = parser.parse_args()
    
    # Set graph path
    if args.graph_path is None:
        args.graph_path = str(config.DATA_PROCESSED_PATH / 'fraud_graph.pt')
    
    # Create trainer
    trainer = FraudDetectionTrainer(
        model_type=args.model,
        hidden_channels=args.hidden_dim,
        out_channels=args.out_dim,
        num_layers=args.num_layers,
        heads=args.heads,
        num_bases=args.num_bases,
        dropout=args.dropout,
        learning_rate=args.lr,
        weight_decay=args.weight_decay,
        num_epochs=args.epochs,
        patience=args.patience,
        random_seed=args.seed
    )
    
    # Load data
    trainer.load_graph(args.graph_path)
    
    # Create splits
    trainer.create_splits(
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=1.0 - args.train_ratio - args.val_ratio
    )
    
    # Build model
    trainer.build_model()
    
    # Setup training
    trainer.setup_training(use_class_weights=True)
    
    # Train
    history = trainer.train(save_best=True)
    
    # Final evaluation
    trainer.evaluate_final()
    
    logger.info("\nTraining complete!")


if __name__ == '__main__':
    main()
