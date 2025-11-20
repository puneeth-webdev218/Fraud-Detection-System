"""
Graph Attention Networks (GAT) for Heterogeneous Graphs
Implements multi-head attention mechanism for fraud detection
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv, HeteroConv, Linear
from typing import Dict, Optional
import logging

from .hetero_gnn import HeteroGNN

logger = logging.getLogger(__name__)


class HeteroGAT(HeteroGNN):
    """
    Graph Attention Network for heterogeneous graphs
    Uses multi-head attention to learn edge importance
    """
    
    def __init__(
        self,
        metadata: tuple,
        in_channels_dict: Dict[str, int],
        hidden_channels: int = 128,
        out_channels: int = 64,
        num_layers: int = 3,
        heads: int = 4,
        dropout: float = 0.2,
        target_node_type: str = 'account',
        concat_heads: bool = True
    ):
        """
        Initialize HeteroGAT
        
        Args:
            metadata: Graph metadata (node_types, edge_types)
            in_channels_dict: Input feature dimensions {node_type: dim}
            hidden_channels: Hidden layer dimension (per head)
            out_channels: Output embedding dimension
            num_layers: Number of GAT layers
            heads: Number of attention heads
            dropout: Dropout probability
            target_node_type: Node type for prediction
            concat_heads: Whether to concatenate attention heads
        """
        super().__init__(
            metadata=metadata,
            hidden_channels=hidden_channels,
            out_channels=out_channels,
            num_layers=num_layers,
            dropout=dropout,
            target_node_type=target_node_type
        )
        
        self.in_channels_dict = in_channels_dict
        self.heads = heads
        self.concat_heads = concat_heads
        
        # Input projection layers
        self.input_projections = nn.ModuleDict()
        for node_type, in_channels in in_channels_dict.items():
            self.input_projections[node_type] = Linear(
                in_channels,
                hidden_channels
            )
        
        # GAT convolutional layers
        self.convs = nn.ModuleList()
        for i in range(num_layers):
            conv_dict = {}
            for edge_type in metadata[1]:
                src_type, _, dst_type = edge_type
                
                # Determine input/output dimensions
                in_ch = hidden_channels if i == 0 else hidden_channels * heads
                
                if i < num_layers - 1:
                    # Hidden layers: concatenate heads
                    out_ch = hidden_channels
                    concat = True
                else:
                    # Output layer
                    out_ch = out_channels
                    concat = False
                
                conv_dict[edge_type] = GATConv(
                    in_ch,
                    out_ch,
                    heads=heads,
                    dropout=dropout,
                    concat=concat,
                    add_self_loops=False  # Handled by HeteroConv
                )
            
            self.convs.append(HeteroConv(conv_dict, aggr='sum'))
        
        # Batch normalization
        self.batch_norms = nn.ModuleList()
        for i in range(num_layers):
            bn_dict = nn.ModuleDict()
            if i < num_layers - 1:
                dim = hidden_channels * heads
            else:
                dim = out_channels
            
            for node_type in metadata[0]:
                bn_dict[node_type] = nn.BatchNorm1d(dim)
            self.batch_norms.append(bn_dict)
        
        logger.info(f"HeteroGAT initialized with {num_layers} layers")
        logger.info(f"  Attention heads: {heads}")
        logger.info(f"  Hidden channels: {hidden_channels} per head")
        logger.info(f"  Node types: {metadata[0]}")
        logger.info(f"  Edge types: {len(metadata[1])}")
    
    def forward(
        self,
        x_dict: Dict[str, torch.Tensor],
        edge_index_dict: Dict[tuple, torch.Tensor],
        edge_attr_dict: Optional[Dict[tuple, torch.Tensor]] = None,
        return_attention_weights: bool = False
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass through GAT layers
        
        Args:
            x_dict: Node features {node_type: [num_nodes, in_channels]}
            edge_index_dict: Edge indices {edge_type: [2, num_edges]}
            edge_attr_dict: Edge attributes (optional)
            return_attention_weights: Whether to return attention weights
            
        Returns:
            Node embeddings {node_type: [num_nodes, out_channels]}
        """
        # Project input features
        x_dict = {
            node_type: self.input_projections[node_type](x)
            for node_type, x in x_dict.items()
        }
        
        # Apply GAT layers
        attention_weights = [] if return_attention_weights else None
        
        for i, conv in enumerate(self.convs):
            # Apply convolution
            if return_attention_weights:
                x_dict_new = {}
                attn_weights_layer = {}
                
                for edge_type in edge_index_dict.keys():
                    src_type, _, dst_type = edge_type
                    edge_index = edge_index_dict[edge_type]
                    
                    # Get source node features
                    x_src = x_dict[src_type]
                    
                    # Apply GAT convolution
                    out, (edge_idx, attn) = conv.convs[edge_type](
                        x_src,
                        edge_index,
                        return_attention_weights=True
                    )
                    
                    if dst_type not in x_dict_new:
                        x_dict_new[dst_type] = out
                    else:
                        x_dict_new[dst_type] += out
                    
                    attn_weights_layer[edge_type] = (edge_idx, attn)
                
                x_dict = x_dict_new
                attention_weights.append(attn_weights_layer)
            else:
                x_dict = conv(x_dict, edge_index_dict)
            
            # Apply batch normalization
            for node_type in x_dict.keys():
                x_dict[node_type] = self.batch_norms[i][node_type](x_dict[node_type])
            
            # Apply activation (except last layer)
            if i < len(self.convs) - 1:
                x_dict = {
                    node_type: F.elu(x)
                    for node_type, x in x_dict.items()
                }
                
                # Apply dropout
                x_dict = {
                    node_type: F.dropout(x, p=self.dropout, training=self.training)
                    for node_type, x in x_dict.items()
                }
        
        if return_attention_weights:
            return x_dict, attention_weights
        return x_dict
    
    def encode(
        self,
        x_dict: Dict[str, torch.Tensor],
        edge_index_dict: Dict[tuple, torch.Tensor]
    ) -> torch.Tensor:
        """
        Get embeddings for target node type
        
        Args:
            x_dict: Node features
            edge_index_dict: Edge indices
            
        Returns:
            Embeddings for target node type
        """
        x_dict = self.forward(x_dict, edge_index_dict)
        return x_dict[self.target_node_type]
    
    def reset_parameters(self):
        """Reset all learnable parameters"""
        for proj in self.input_projections.values():
            proj.reset_parameters()
        
        for conv in self.convs:
            for subconv in conv.convs.values():
                subconv.reset_parameters()
        
        for bn_dict in self.batch_norms:
            for bn in bn_dict.values():
                bn.reset_parameters()


class GATFraudDetector(nn.Module):
    """
    Complete GAT model with fraud classification head
    """
    
    def __init__(
        self,
        metadata: tuple,
        in_channels_dict: Dict[str, int],
        hidden_channels: int = 128,
        out_channels: int = 64,
        num_layers: int = 3,
        heads: int = 4,
        dropout: float = 0.2,
        classifier_hidden: int = 64,
        target_node_type: str = 'account'
    ):
        """
        Initialize GAT fraud detector
        
        Args:
            metadata: Graph metadata
            in_channels_dict: Input dimensions
            hidden_channels: Hidden dimension per attention head
            out_channels: Output embedding dimension
            num_layers: Number of GAT layers
            heads: Number of attention heads
            dropout: Dropout rate
            classifier_hidden: Classifier hidden dimension
            target_node_type: Node type for prediction
        """
        super().__init__()
        
        from .hetero_gnn import FraudClassifier
        
        self.gnn = HeteroGAT(
            metadata=metadata,
            in_channels_dict=in_channels_dict,
            hidden_channels=hidden_channels,
            out_channels=out_channels,
            num_layers=num_layers,
            heads=heads,
            dropout=dropout,
            target_node_type=target_node_type
        )
        
        self.classifier = FraudClassifier(
            in_channels=out_channels,
            hidden_channels=classifier_hidden,
            dropout=dropout
        )
        
        self.target_node_type = target_node_type
    
    def forward(
        self,
        x_dict: Dict[str, torch.Tensor],
        edge_index_dict: Dict[tuple, torch.Tensor],
        return_attention: bool = False
    ) -> torch.Tensor:
        """
        Forward pass: GAT encoding + classification
        
        Args:
            x_dict: Node features
            edge_index_dict: Edge indices
            return_attention: Whether to return attention weights
            
        Returns:
            Fraud logits (and optionally attention weights)
        """
        # Get GNN embeddings
        if return_attention:
            x_dict, attention_weights = self.gnn.forward(
                x_dict, edge_index_dict, return_attention_weights=True
            )
            embeddings = x_dict[self.target_node_type]
            logits = self.classifier(embeddings)
            return logits, attention_weights
        else:
            embeddings = self.gnn.encode(x_dict, edge_index_dict)
            logits = self.classifier(embeddings)
            return logits
    
    def predict_proba(
        self,
        x_dict: Dict[str, torch.Tensor],
        edge_index_dict: Dict[tuple, torch.Tensor]
    ) -> torch.Tensor:
        """
        Get fraud probabilities
        
        Args:
            x_dict: Node features
            edge_index_dict: Edge indices
            
        Returns:
            Fraud probabilities
        """
        logits = self.forward(x_dict, edge_index_dict)
        return torch.sigmoid(logits)
    
    def reset_parameters(self):
        """Reset all parameters"""
        self.gnn.reset_parameters()
        self.classifier.reset_parameters()
