"""
Relational Graph Convolutional Network (R-GCN) for Heterogeneous Graphs
Handles multiple edge types with separate weight matrices
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import RGCNConv, Linear
from typing import Dict, List, Optional
import logging

from .hetero_gnn import HeteroGNN

logger = logging.getLogger(__name__)


class HeteroRGCN(HeteroGNN):
    """
    R-GCN for heterogeneous graphs
    Uses relation-specific transformations for different edge types
    """
    
    def __init__(
        self,
        metadata: tuple,
        in_channels_dict: Dict[str, int],
        hidden_channels: int = 128,
        out_channels: int = 64,
        num_layers: int = 3,
        num_bases: Optional[int] = None,
        dropout: float = 0.2,
        target_node_type: str = 'account'
    ):
        """
        Initialize HeteroRGCN
        
        Args:
            metadata: Graph metadata (node_types, edge_types)
            in_channels_dict: Input feature dimensions {node_type: dim}
            hidden_channels: Hidden layer dimension
            out_channels: Output embedding dimension
            num_layers: Number of R-GCN layers
            num_bases: Number of bases for basis decomposition (None = no decomposition)
            dropout: Dropout probability
            target_node_type: Node type for prediction
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
        self.num_bases = num_bases
        self.num_relations = len(metadata[1])
        
        # Use basis decomposition if num_bases specified
        if num_bases is None:
            num_bases = self.num_relations
        
        # Input projection layers for each node type
        self.input_projections = nn.ModuleDict()
        for node_type, in_channels in in_channels_dict.items():
            self.input_projections[node_type] = Linear(
                in_channels,
                hidden_channels
            )
        
        # Create unified node feature tensor and edge index
        # R-GCN works on homogeneous graphs with typed edges
        
        # R-GCN convolutional layers
        self.convs = nn.ModuleList()
        for i in range(num_layers):
            in_ch = hidden_channels
            out_ch = hidden_channels if i < num_layers - 1 else out_channels
            
            self.convs.append(
                RGCNConv(
                    in_ch,
                    out_ch,
                    num_relations=self.num_relations,
                    num_bases=num_bases,
                    aggr='mean'
                )
            )
        
        # Batch normalization
        self.batch_norms = nn.ModuleList()
        for i in range(num_layers):
            out_ch = hidden_channels if i < num_layers - 1 else out_channels
            self.batch_norms.append(nn.BatchNorm1d(out_ch))
        
        # Store node type information for reconstruction
        self.node_types = metadata[0]
        self.edge_types = metadata[1]
        
        # Create edge type to relation ID mapping
        self.edge_type_to_relation = {
            edge_type: i for i, edge_type in enumerate(metadata[1])
        }
        
        logger.info(f"HeteroRGCN initialized with {num_layers} layers")
        logger.info(f"  Relations: {self.num_relations}")
        logger.info(f"  Bases: {num_bases}")
        logger.info(f"  Node types: {metadata[0]}")
    
    def _hetero_to_homo(
        self,
        x_dict: Dict[str, torch.Tensor],
        edge_index_dict: Dict[tuple, torch.Tensor]
    ):
        """
        Convert heterogeneous graph to homogeneous with edge types
        
        Args:
            x_dict: Node features {node_type: features}
            edge_index_dict: Edge indices {edge_type: edge_index}
            
        Returns:
            x: Unified node features [total_nodes, channels]
            edge_index: Unified edge index [2, total_edges]
            edge_type: Edge type indices [total_edges]
            node_type_offsets: Starting index for each node type
        """
        # Concatenate all node features
        x_list = []
        node_type_offsets = {}
        offset = 0
        
        for node_type in self.node_types:
            if node_type in x_dict:
                x_list.append(x_dict[node_type])
                node_type_offsets[node_type] = offset
                offset += x_dict[node_type].size(0)
        
        x = torch.cat(x_list, dim=0)
        
        # Concatenate all edges and create edge type tensor
        edge_index_list = []
        edge_type_list = []
        
        for edge_type, edge_index in edge_index_dict.items():
            src_type, _, dst_type = edge_type
            
            # Adjust indices based on offsets
            src_offset = node_type_offsets[src_type]
            dst_offset = node_type_offsets[dst_type]
            
            adjusted_edge_index = edge_index.clone()
            adjusted_edge_index[0] += src_offset
            adjusted_edge_index[1] += dst_offset
            
            edge_index_list.append(adjusted_edge_index)
            
            # Get relation ID
            relation_id = self.edge_type_to_relation[edge_type]
            edge_type_tensor = torch.full(
                (edge_index.size(1),),
                relation_id,
                dtype=torch.long,
                device=edge_index.device
            )
            edge_type_list.append(edge_type_tensor)
        
        edge_index = torch.cat(edge_index_list, dim=1)
        edge_type = torch.cat(edge_type_list, dim=0)
        
        return x, edge_index, edge_type, node_type_offsets
    
    def _homo_to_hetero(
        self,
        x: torch.Tensor,
        node_type_offsets: Dict[str, int],
        node_counts: Dict[str, int]
    ) -> Dict[str, torch.Tensor]:
        """
        Convert homogeneous node features back to heterogeneous
        
        Args:
            x: Unified node features [total_nodes, channels]
            node_type_offsets: Starting index for each node type
            node_counts: Number of nodes for each type
            
        Returns:
            x_dict: Node features {node_type: features}
        """
        x_dict = {}
        
        for node_type in self.node_types:
            if node_type in node_type_offsets:
                start = node_type_offsets[node_type]
                end = start + node_counts[node_type]
                x_dict[node_type] = x[start:end]
        
        return x_dict
    
    def forward(
        self,
        x_dict: Dict[str, torch.Tensor],
        edge_index_dict: Dict[tuple, torch.Tensor],
        edge_attr_dict: Optional[Dict[tuple, torch.Tensor]] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass through R-GCN layers
        
        Args:
            x_dict: Node features {node_type: [num_nodes, in_channels]}
            edge_index_dict: Edge indices {edge_type: [2, num_edges]}
            edge_attr_dict: Edge attributes (not used in R-GCN)
            
        Returns:
            Node embeddings {node_type: [num_nodes, out_channels]}
        """
        # Project input features
        x_dict = {
            node_type: self.input_projections[node_type](x)
            for node_type, x in x_dict.items()
        }
        
        # Store node counts for reconstruction
        node_counts = {
            node_type: x.size(0) for node_type, x in x_dict.items()
        }
        
        # Convert to homogeneous graph
        x, edge_index, edge_type, node_type_offsets = self._hetero_to_homo(
            x_dict, edge_index_dict
        )
        
        # Apply R-GCN layers
        for i, conv in enumerate(self.convs):
            # Apply convolution
            x = conv(x, edge_index, edge_type)
            
            # Apply batch normalization
            x = self.batch_norms[i](x)
            
            # Apply activation (except last layer)
            if i < len(self.convs) - 1:
                x = F.relu(x)
                x = F.dropout(x, p=self.dropout, training=self.training)
        
        # Convert back to heterogeneous
        x_dict = self._homo_to_hetero(x, node_type_offsets, node_counts)
        
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
            conv.reset_parameters()
        
        for bn in self.batch_norms:
            bn.reset_parameters()


class RGCNFraudDetector(nn.Module):
    """
    Complete R-GCN model with fraud classification head
    """
    
    def __init__(
        self,
        metadata: tuple,
        in_channels_dict: Dict[str, int],
        hidden_channels: int = 128,
        out_channels: int = 64,
        num_layers: int = 3,
        num_bases: Optional[int] = None,
        dropout: float = 0.2,
        classifier_hidden: int = 64,
        target_node_type: str = 'account'
    ):
        """
        Initialize R-GCN fraud detector
        
        Args:
            metadata: Graph metadata
            in_channels_dict: Input dimensions
            hidden_channels: Hidden dimension
            out_channels: Output embedding dimension
            num_layers: Number of R-GCN layers
            num_bases: Number of bases for decomposition
            dropout: Dropout rate
            classifier_hidden: Classifier hidden dimension
            target_node_type: Node type for prediction
        """
        super().__init__()
        
        from .hetero_gnn import FraudClassifier
        
        self.gnn = HeteroRGCN(
            metadata=metadata,
            in_channels_dict=in_channels_dict,
            hidden_channels=hidden_channels,
            out_channels=out_channels,
            num_layers=num_layers,
            num_bases=num_bases,
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
        Forward pass: R-GCN encoding + classification
        
        Args:
            x_dict: Node features
            edge_index_dict: Edge indices
            
        Returns:
            Fraud logits for target nodes
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
            Fraud probabilities
        """
        logits = self.forward(x_dict, edge_index_dict)
        return torch.sigmoid(logits)
    
    def reset_parameters(self):
        """Reset all parameters"""
        self.gnn.reset_parameters()
        self.classifier.reset_parameters()
