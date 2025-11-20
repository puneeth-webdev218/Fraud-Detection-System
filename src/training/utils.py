"""
Training utilities and data splitting
"""

import torch
import numpy as np
from typing import Tuple, Dict
import logging

logger = logging.getLogger(__name__)


def create_train_val_test_split(
    num_nodes: int,
    train_ratio: float = 0.6,
    val_ratio: float = 0.2,
    test_ratio: float = 0.2,
    random_seed: int = 42
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Create train/val/test splits
    
    Args:
        num_nodes: Total number of nodes
        train_ratio: Training set ratio
        val_ratio: Validation set ratio
        test_ratio: Test set ratio
        random_seed: Random seed
        
    Returns:
        (train_mask, val_mask, test_mask)
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, \
        "Ratios must sum to 1.0"
    
    # Set random seed
    np.random.seed(random_seed)
    
    # Create random permutation
    indices = np.random.permutation(num_nodes)
    
    # Calculate split points
    train_end = int(num_nodes * train_ratio)
    val_end = train_end + int(num_nodes * val_ratio)
    
    # Create masks
    train_mask = torch.zeros(num_nodes, dtype=torch.bool)
    val_mask = torch.zeros(num_nodes, dtype=torch.bool)
    test_mask = torch.zeros(num_nodes, dtype=torch.bool)
    
    train_mask[indices[:train_end]] = True
    val_mask[indices[train_end:val_end]] = True
    test_mask[indices[val_end:]] = True
    
    logger.info(f"Data split created:")
    logger.info(f"  Train: {train_mask.sum().item()} ({train_ratio*100:.1f}%)")
    logger.info(f"  Val:   {val_mask.sum().item()} ({val_ratio*100:.1f}%)")
    logger.info(f"  Test:  {test_mask.sum().item()} ({test_ratio*100:.1f}%)")
    
    return train_mask, val_mask, test_mask


def create_stratified_split(
    labels: torch.Tensor,
    train_ratio: float = 0.6,
    val_ratio: float = 0.2,
    test_ratio: float = 0.2,
    random_seed: int = 42
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Create stratified train/val/test splits (maintains class distribution)
    
    Args:
        labels: Node labels [num_nodes]
        train_ratio: Training set ratio
        val_ratio: Validation set ratio
        test_ratio: Test set ratio
        random_seed: Random seed
        
    Returns:
        (train_mask, val_mask, test_mask)
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, \
        "Ratios must sum to 1.0"
    
    np.random.seed(random_seed)
    
    num_nodes = len(labels)
    labels_np = labels.cpu().numpy()
    
    # Initialize masks
    train_mask = torch.zeros(num_nodes, dtype=torch.bool)
    val_mask = torch.zeros(num_nodes, dtype=torch.bool)
    test_mask = torch.zeros(num_nodes, dtype=torch.bool)
    
    # Split each class separately
    for label in np.unique(labels_np):
        # Get indices for this class
        class_indices = np.where(labels_np == label)[0]
        np.random.shuffle(class_indices)
        
        # Calculate split points
        n_class = len(class_indices)
        train_end = int(n_class * train_ratio)
        val_end = train_end + int(n_class * val_ratio)
        
        # Assign to splits
        train_mask[class_indices[:train_end]] = True
        val_mask[class_indices[train_end:val_end]] = True
        test_mask[class_indices[val_end:]] = True
    
    # Log distribution
    logger.info(f"Stratified data split created:")
    for split_name, mask in [('Train', train_mask), ('Val', val_mask), ('Test', test_mask)]:
        split_labels = labels[mask]
        fraud_count = (split_labels == 1).sum().item()
        total = len(split_labels)
        fraud_rate = fraud_count / total * 100 if total > 0 else 0
        logger.info(f"  {split_name}: {total} nodes ({fraud_count} fraud, {fraud_rate:.2f}%)")
    
    return train_mask, val_mask, test_mask


class EarlyStopping:
    """
    Early stopping to prevent overfitting
    """
    
    def __init__(
        self,
        patience: int = 10,
        min_delta: float = 0.0,
        mode: str = 'max'
    ):
        """
        Initialize early stopping
        
        Args:
            patience: Number of epochs to wait before stopping
            min_delta: Minimum change to qualify as improvement
            mode: 'max' for metrics to maximize, 'min' for metrics to minimize
        """
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.counter = 0
        self.best_score = None
        self.early_stop = False
        
        if mode == 'max':
            self.is_better = lambda new, best: new > best + min_delta
        else:
            self.is_better = lambda new, best: new < best - min_delta
    
    def __call__(self, score: float) -> bool:
        """
        Check if training should stop
        
        Args:
            score: Current metric score
            
        Returns:
            True if training should stop
        """
        if self.best_score is None:
            self.best_score = score
            return False
        
        if self.is_better(score, self.best_score):
            self.best_score = score
            self.counter = 0
            return False
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
                return True
            return False
    
    def reset(self):
        """Reset early stopping state"""
        self.counter = 0
        self.best_score = None
        self.early_stop = False


def save_checkpoint(
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    metrics: Dict[str, float],
    filepath: str
):
    """
    Save model checkpoint
    
    Args:
        model: Model to save
        optimizer: Optimizer state
        epoch: Current epoch
        metrics: Current metrics
        filepath: Path to save checkpoint
    """
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'metrics': metrics
    }
    
    torch.save(checkpoint, filepath)
    logger.info(f"Checkpoint saved to {filepath}")


def load_checkpoint(
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    filepath: str,
    device: str = 'cpu'
) -> Tuple[torch.nn.Module, torch.optim.Optimizer, int, Dict]:
    """
    Load model checkpoint
    
    Args:
        model: Model to load weights into
        optimizer: Optimizer to load state into
        filepath: Path to checkpoint
        device: Device to load to
        
    Returns:
        (model, optimizer, epoch, metrics)
    """
    checkpoint = torch.load(filepath, map_location=device)
    
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    epoch = checkpoint['epoch']
    metrics = checkpoint['metrics']
    
    logger.info(f"Checkpoint loaded from {filepath} (epoch {epoch})")
    
    return model, optimizer, epoch, metrics


def compute_class_weights(labels: torch.Tensor) -> torch.Tensor:
    """
    Compute class weights for imbalanced datasets
    
    Args:
        labels: Node labels [num_nodes]
        
    Returns:
        Class weights [num_classes]
    """
    # Count classes
    unique, counts = torch.unique(labels, return_counts=True)
    
    # Compute weights inversely proportional to class frequency
    weights = len(labels) / (len(unique) * counts.float())
    
    logger.info(f"Class distribution:")
    for cls, count, weight in zip(unique, counts, weights):
        logger.info(f"  Class {cls}: {count} samples (weight: {weight:.4f})")
    
    return weights
