"""
Base Heterogeneous GNN Model
Wrapper for handling heterogeneous graph neural networks
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import HeteroData
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class HeteroGNN(nn.Module):
    """
    Base class for heterogeneous GNN models
    Handles multi-node-type graphs for fraud detection
    """
    
    def __init__(
        self,
        metadata: tuple,
        hidden_channels: int = 128,
        out_channels: int = 64,
        num_layers: int = 3,
        dropout: float = 0.2,
        target_node_type: str = 'account'
    ):
        """
        Initialize Heterogeneous GNN
        
        Args:
            metadata: Graph metadata (node_types, edge_types)
            hidden_channels: Hidden layer dimension
            out_channels: Output embedding dimension
            num_layers: Number of GNN layers
            dropout: Dropout probability
            target_node_type: Node type for prediction (default: 'account')
        """
        super().__init__()
        
        self.metadata = metadata
        self.hidden_channels = hidden_channels
        self.out_channels = out_channels
        self.num_layers = num_layers
        self.dropout = dropout
        self.target_node_type = target_node_type
        
        logger.info(f"Initializing HeteroGNN:")
        logger.info(f"  Hidden channels: {hidden_channels}")
        logger.info(f"  Output channels: {out_channels}")
        logger.info(f"  Num layers: {num_layers}")
        logger.info(f"  Dropout: {dropout}")
        logger.info(f"  Target node: {target_node_type}")
    
    def forward(self, x_dict: Dict[str, torch.Tensor], 
                edge_index_dict: Dict[tuple, torch.Tensor]) -> torch.Tensor:
        """
        Forward pass - to be implemented by subclasses
        
        Args:
            x_dict: Dictionary of node features {node_type: features}
            edge_index_dict: Dictionary of edge indices {edge_type: edge_index}
            
        Returns:
            Output embeddings for target node type
        """
        raise NotImplementedError("Subclasses must implement forward()")
    
    def reset_parameters(self):
        """Reset all learnable parameters"""
        for module in self.modules():
            if hasattr(module, 'reset_parameters'):
                module.reset_parameters()


class FraudClassifier(nn.Module):
    """
    Fraud classification head for GNN outputs
    """
    
    def __init__(
        self,
        in_channels: int,
        hidden_channels: int = 64,
        dropout: float = 0.3
    ):
        """
        Initialize classifier
        
        Args:
            in_channels: Input feature dimension
            hidden_channels: Hidden layer dimension
            dropout: Dropout probability
        """
        super().__init__()
        
        self.lin1 = nn.Linear(in_channels, hidden_channels)
        self.lin2 = nn.Linear(hidden_channels, hidden_channels // 2)
        self.lin3 = nn.Linear(hidden_channels // 2, 1)
        
        self.batch_norm1 = nn.BatchNorm1d(hidden_channels)
        self.batch_norm2 = nn.BatchNorm1d(hidden_channels // 2)
        
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass
        
        Args:
            x: Input embeddings [num_nodes, in_channels]
            
        Returns:
            Fraud predictions [num_nodes, 1]
        """
        x = self.lin1(x)
        x = self.batch_norm1(x)
        x = F.relu(x)
        x = self.dropout(x)
        
        x = self.lin2(x)
        x = self.batch_norm2(x)
        x = F.relu(x)
        x = self.dropout(x)
        
        x = self.lin3(x)
        
        return x
    
    def reset_parameters(self):
        """Reset all learnable parameters"""
        self.lin1.reset_parameters()
        self.lin2.reset_parameters()
        self.lin3.reset_parameters()
        self.batch_norm1.reset_parameters()
        self.batch_norm2.reset_parameters()


class EdgeClassifier(nn.Module):
    """
    Edge-level fraud classification for transaction edges
    """
    
    def __init__(
        self,
        in_channels: int,
        edge_feat_dim: int = 3,
        hidden_channels: int = 64,
        dropout: float = 0.3
    ):
        """
        Initialize edge classifier
        
        Args:
            in_channels: Node embedding dimension
            edge_feat_dim: Edge feature dimension
            hidden_channels: Hidden layer dimension
            dropout: Dropout probability
        """
        super().__init__()
        
        # Combine source node, dest node, and edge features
        total_dim = 2 * in_channels + edge_feat_dim
        
        self.lin1 = nn.Linear(total_dim, hidden_channels)
        self.lin2 = nn.Linear(hidden_channels, hidden_channels // 2)
        self.lin3 = nn.Linear(hidden_channels // 2, 1)
        
        self.batch_norm1 = nn.BatchNorm1d(hidden_channels)
        self.batch_norm2 = nn.BatchNorm1d(hidden_channels // 2)
        
        self.dropout = nn.Dropout(dropout)
        
    def forward(
        self,
        x_src: torch.Tensor,
        x_dst: torch.Tensor,
        edge_attr: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass
        
        Args:
            x_src: Source node embeddings [num_edges, in_channels]
            x_dst: Destination node embeddings [num_edges, in_channels]
            edge_attr: Edge features [num_edges, edge_feat_dim]
            
        Returns:
            Edge fraud predictions [num_edges, 1]
        """
        # Concatenate source, destination, and edge features
        if edge_attr is not None:
            x = torch.cat([x_src, x_dst, edge_attr], dim=-1)
        else:
            x = torch.cat([x_src, x_dst], dim=-1)
        
        x = self.lin1(x)
        x = self.batch_norm1(x)
        x = F.relu(x)
        x = self.dropout(x)
        
        x = self.lin2(x)
        x = self.batch_norm2(x)
        x = F.relu(x)
        x = self.dropout(x)
        
        x = self.lin3(x)
        
        return x
    
    def reset_parameters(self):
        """Reset all learnable parameters"""
        self.lin1.reset_parameters()
        self.lin2.reset_parameters()
        self.lin3.reset_parameters()
        self.batch_norm1.reset_parameters()
        self.batch_norm2.reset_parameters()
