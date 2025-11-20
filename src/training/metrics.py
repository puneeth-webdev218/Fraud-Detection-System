"""
Evaluation Metrics for Fraud Detection
Implements precision, recall, F1, ROC-AUC, PR-AUC
"""

import torch
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report
)
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FraudMetrics:
    """
    Comprehensive metrics for fraud detection evaluation
    """
    
    @staticmethod
    def compute_metrics(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_prob: Optional[np.ndarray] = None,
        threshold: float = 0.5
    ) -> Dict[str, float]:
        """
        Compute all evaluation metrics
        
        Args:
            y_true: True labels [N]
            y_pred: Predicted labels [N]
            y_prob: Prediction probabilities [N] (optional, for AUC metrics)
            threshold: Classification threshold
            
        Returns:
            Dictionary of metrics
        """
        metrics = {}
        
        # Basic metrics
        metrics['accuracy'] = accuracy_score(y_true, y_pred)
        metrics['precision'] = precision_score(y_true, y_pred, zero_division=0)
        metrics['recall'] = recall_score(y_true, y_pred, zero_division=0)
        metrics['f1'] = f1_score(y_true, y_pred, zero_division=0)
        
        # Confusion matrix
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        metrics['true_negatives'] = int(tn)
        metrics['false_positives'] = int(fp)
        metrics['false_negatives'] = int(fn)
        metrics['true_positives'] = int(tp)
        
        # Additional metrics
        metrics['specificity'] = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        metrics['fpr'] = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        metrics['fnr'] = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        
        # AUC metrics (if probabilities provided)
        if y_prob is not None:
            try:
                metrics['roc_auc'] = roc_auc_score(y_true, y_prob)
                metrics['pr_auc'] = average_precision_score(y_true, y_prob)
            except ValueError as e:
                logger.warning(f"Could not compute AUC metrics: {e}")
                metrics['roc_auc'] = 0.0
                metrics['pr_auc'] = 0.0
        
        return metrics
    
    @staticmethod
    def compute_threshold_metrics(
        y_true: np.ndarray,
        y_prob: np.ndarray,
        thresholds: np.ndarray = None
    ) -> Dict[str, np.ndarray]:
        """
        Compute metrics at different thresholds
        
        Args:
            y_true: True labels
            y_prob: Prediction probabilities
            thresholds: Thresholds to evaluate (default: 0.1 to 0.9)
            
        Returns:
            Dictionary of metrics at each threshold
        """
        if thresholds is None:
            thresholds = np.arange(0.1, 1.0, 0.1)
        
        results = {
            'thresholds': thresholds,
            'precision': [],
            'recall': [],
            'f1': [],
            'accuracy': []
        }
        
        for threshold in thresholds:
            y_pred = (y_prob >= threshold).astype(int)
            
            results['precision'].append(
                precision_score(y_true, y_pred, zero_division=0)
            )
            results['recall'].append(
                recall_score(y_true, y_pred, zero_division=0)
            )
            results['f1'].append(
                f1_score(y_true, y_pred, zero_division=0)
            )
            results['accuracy'].append(
                accuracy_score(y_true, y_pred)
            )
        
        # Convert to numpy arrays
        for key in ['precision', 'recall', 'f1', 'accuracy']:
            results[key] = np.array(results[key])
        
        return results
    
    @staticmethod
    def find_best_threshold(
        y_true: np.ndarray,
        y_prob: np.ndarray,
        metric: str = 'f1'
    ) -> Tuple[float, float]:
        """
        Find optimal threshold based on metric
        
        Args:
            y_true: True labels
            y_prob: Prediction probabilities
            metric: Metric to optimize ('f1', 'precision', 'recall')
            
        Returns:
            (best_threshold, best_metric_value)
        """
        threshold_metrics = FraudMetrics.compute_threshold_metrics(
            y_true, y_prob
        )
        
        metric_values = threshold_metrics[metric]
        best_idx = np.argmax(metric_values)
        
        best_threshold = threshold_metrics['thresholds'][best_idx]
        best_value = metric_values[best_idx]
        
        return best_threshold, best_value
    
    @staticmethod
    def print_metrics(
        metrics: Dict[str, float],
        prefix: str = ""
    ):
        """
        Print metrics in formatted way
        
        Args:
            metrics: Dictionary of metrics
            prefix: Prefix for print statements
        """
        print(f"\n{prefix}Evaluation Metrics:")
        print(f"{prefix}{'='*50}")
        
        # Main metrics
        print(f"{prefix}Accuracy:  {metrics['accuracy']:.4f}")
        print(f"{prefix}Precision: {metrics['precision']:.4f}")
        print(f"{prefix}Recall:    {metrics['recall']:.4f}")
        print(f"{prefix}F1 Score:  {metrics['f1']:.4f}")
        
        if 'roc_auc' in metrics:
            print(f"{prefix}ROC-AUC:   {metrics['roc_auc']:.4f}")
            print(f"{prefix}PR-AUC:    {metrics['pr_auc']:.4f}")
        
        # Confusion matrix
        print(f"\n{prefix}Confusion Matrix:")
        print(f"{prefix}  TN: {metrics['true_negatives']:6d}  FP: {metrics['false_positives']:6d}")
        print(f"{prefix}  FN: {metrics['false_negatives']:6d}  TP: {metrics['true_positives']:6d}")
        
        # Additional metrics
        print(f"\n{prefix}Additional Metrics:")
        print(f"{prefix}  Specificity: {metrics['specificity']:.4f}")
        print(f"{prefix}  FPR:         {metrics['fpr']:.4f}")
        print(f"{prefix}  FNR:         {metrics['fnr']:.4f}")
        
        print(f"{prefix}{'='*50}\n")
    
    @staticmethod
    def classification_report_dict(
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Dict:
        """
        Get detailed classification report as dictionary
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            
        Returns:
            Classification report dictionary
        """
        return classification_report(
            y_true,
            y_pred,
            target_names=['Normal', 'Fraud'],
            output_dict=True,
            zero_division=0
        )


def evaluate_model(
    model: torch.nn.Module,
    data,
    mask: torch.Tensor,
    device: str = 'cpu',
    threshold: float = 0.5
) -> Dict[str, float]:
    """
    Evaluate model on given data split
    
    Args:
        model: GNN model
        data: HeteroData graph
        mask: Boolean mask for evaluation nodes
        device: Device to use
        threshold: Classification threshold
        
    Returns:
        Dictionary of evaluation metrics
    """
    model.eval()
    
    with torch.no_grad():
        # Get predictions
        logits = model(data.x_dict, data.edge_index_dict)
        probs = torch.sigmoid(logits).cpu().numpy().flatten()
        preds = (probs >= threshold).astype(int)
        
        # Get ground truth
        labels = data['account'].y.cpu().numpy()[mask]
        probs = probs[mask]
        preds = preds[mask]
        
        # Compute metrics
        metrics = FraudMetrics.compute_metrics(
            y_true=labels,
            y_pred=preds,
            y_prob=probs,
            threshold=threshold
        )
    
    return metrics


def evaluate_model_all_splits(
    model: torch.nn.Module,
    data,
    train_mask: torch.Tensor,
    val_mask: torch.Tensor,
    test_mask: torch.Tensor,
    device: str = 'cpu',
    threshold: float = 0.5
) -> Dict[str, Dict[str, float]]:
    """
    Evaluate model on all data splits
    
    Args:
        model: GNN model
        data: HeteroData graph
        train_mask: Training mask
        val_mask: Validation mask
        test_mask: Test mask
        device: Device to use
        threshold: Classification threshold
        
    Returns:
        Dictionary with metrics for each split
    """
    results = {}
    
    splits = {
        'train': train_mask,
        'val': val_mask,
        'test': test_mask
    }
    
    for split_name, mask in splits.items():
        if mask.sum() > 0:
            results[split_name] = evaluate_model(
                model, data, mask, device, threshold
            )
        else:
            logger.warning(f"Empty {split_name} mask, skipping evaluation")
            results[split_name] = {}
    
    return results
