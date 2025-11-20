"""
GraphSAGE Model for Heterogeneous Graphs
Implements GraphSAGE with mean aggregation for fraud detection
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv, HeteroConv, Linear
from typing import Dict, Optional
import logging

from .hetero_gnn import HeteroGNN

logger = logging.getLogger(__name__)


class HeteroGraphSAGE(HeteroGNN):
    """
    GraphSAGE for heterogeneous graphs
    Uses mean aggregation to combine neighbor features
    """
    
    def __init__(
        self,
        metadata: tuple,
        in_channels_dict: Dict[str, int],
        hidden_channels: int = 128,
        out_channels: int = 64,
        num_layers: int = 3,
        dropout: float = 0.2,
        target_node_type: str = 'account',
        aggr: str = 'mean'
    ):
        """
        Initialize HeteroGraphSAGE
        
        Args:
            metadata: Graph metadata (node_types, edge_types)
            in_channels_dict: Input feature dimensions {node_type: dim}
            hidden_channels: Hidden layer dimension
            out_channels: Output embedding dimension
            num_layers: Number of GraphSAGE layers
            dropout: Dropout probability
            target_node_type: Node type for prediction
            aggr: Aggregation method ('mean', 'max', 'sum')
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
        self.aggr = aggr
        
        # Input projection layers for each node type
        self.input_projections = nn.ModuleDict()
        for node_type, in_channels in in_channels_dict.items():
            self.input_projections[node_type] = Linear(
                in_channels,
                hidden_channels
            )
        
        # GraphSAGE convolutional layers
        self.convs = nn.ModuleList()
        for i in range(num_layers):
            conv_dict = {}
            for edge_type in metadata[1]:
                src_type, _, dst_type = edge_type
                
                # Determine input/output dimensions
                in_ch = hidden_channels
                out_ch = hidden_channels if i < num_layers - 1 else out_channels
                
                conv_dict[edge_type] = SAGEConv(
                    (in_ch, in_ch),  # Bipartite graph: (src_channels, dst_channels)
                    out_ch,
                    aggr=aggr,
                    normalize=True
                )
            
            self.convs.append(HeteroConv(conv_dict, aggr='sum'))
        
        # Batch normalization for each node type
        self.batch_norms = nn.ModuleList()
        for i in range(num_layers):
            bn_dict = nn.ModuleDict()
            out_ch = hidden_channels if i < num_layers - 1 else out_channels
            for node_type in metadata[0]:
                bn_dict[node_type] = nn.BatchNorm1d(out_ch)
            self.batch_norms.append(bn_dict)
        
        logger.info(f"HeteroGraphSAGE initialized with {num_layers} layers")
        logger.info(f"  Aggregation: {aggr}")
        logger.info(f"  Node types: {metadata[0]}")
        logger.info(f"  Edge types: {len(metadata[1])}")
    
    def forward(
        self,
        x_dict: Dict[str, torch.Tensor],
        edge_index_dict: Dict[tuple, torch.Tensor],
        edge_attr_dict: Optional[Dict[tuple, torch.Tensor]] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass through GraphSAGE layers
        
        Args:
            x_dict: Node features {node_type: [num_nodes, in_channels]}
            edge_index_dict: Edge indices {edge_type: [2, num_edges]}
            edge_attr_dict: Edge attributes (not used in GraphSAGE)
            
        Returns:
            Node embeddings {node_type: [num_nodes, out_channels]}
        """
        # Project input features to hidden dimension
        x_dict = {
            node_type: self.input_projections[node_type](x)
            for node_type, x in x_dict.items()
        }
        
        # Apply GraphSAGE layers
        for i, conv in enumerate(self.convs):
            # Apply convolution
            x_dict = conv(x_dict, edge_index_dict)
            
            # Apply batch normalization
            for node_type in x_dict.keys():
                x_dict[node_type] = self.batch_norms[i][node_type](x_dict[node_type])
            
            # Apply activation (except last layer)
            if i < len(self.convs) - 1:
                x_dict = {
                    node_type: F.relu(x)
                    for node_type, x in x_dict.items()
                }
                
                # Apply dropout
                x_dict = {
                    node_type: F.dropout(x, p=self.dropout, training=self.training)
                    for node_type, x in x_dict.items()
                }
        
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
            Embeddings for target node type [num_target_nodes, out_channels]
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


class GraphSAGEFraudDetector(nn.Module):
    """
    Complete GraphSAGE model with fraud classification head
    """
    
    def __init__(
        self,
        metadata: tuple,
        in_channels_dict: Dict[str, int],
        hidden_channels: int = 128,
        out_channels: int = 64,
        num_layers: int = 3,
        dropout: float = 0.2,
        classifier_hidden: int = 64,
        target_node_type: str = 'account'
    ):
        """
        Initialize complete fraud detection model
        
        Args:
            metadata: Graph metadata
            in_channels_dict: Input dimensions
            hidden_channels: Hidden dimension
            out_channels: Output embedding dimension
            num_layers: Number of GNN layers
            dropout: Dropout rate
            classifier_hidden: Classifier hidden dimension
            target_node_type: Node type for prediction
        """
        super().__init__()
        
        from .hetero_gnn import FraudClassifier
        
        self.gnn = HeteroGraphSAGE(
            metadata=metadata,
            in_channels_dict=in_channels_dict,
            hidden_channels=hidden_channels,
            out_channels=out_channels,
            num_layers=num_layers,
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
        edge_index_dict: Dict[tuple, torch.Tensor]
    ) -> torch.Tensor:
        """
        Forward pass: GNN encoding + classification
        
        Args:
            x_dict: Node features
            edge_index_dict: Edge indices
            
        Returns:
            Fraud logits for target nodes [num_target_nodes, 1]
        """
        # Get GNN embeddings
        embeddings = self.gnn.encode(x_dict, edge_index_dict)
        
        # Classify
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
            Fraud probabilities [num_target_nodes, 1]
        """
        logits = self.forward(x_dict, edge_index_dict)
        return torch.sigmoid(logits)
    
    def reset_parameters(self):
        """Reset all parameters"""
        self.gnn.reset_parameters()
        self.classifier.reset_parameters()
