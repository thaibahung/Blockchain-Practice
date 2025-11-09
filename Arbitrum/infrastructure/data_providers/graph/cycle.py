from typing import List, Optional, Dict, Any, Set, Tuple
from decimal import Decimal
import networkx as nx
import math
from infrastructure.data_providers.graph.edge import Edge
from domain.entities.models import DexTradingPair

class Cycle_3:
    def __init__(self, token1: str, token2: str, token3: str, 
                       edge1: Edge, edge2: Edge, edge3: Edge):
        self.token1 = token1
        self.token2 = token2
        self.token3 = token3
        self.edge1 = edge1
        self.edge2 = edge2
        self.edge3 = edge3

class Cycle_2:
    def __init__(self, token1: str, token2: str, 
                       edge1: Edge, edge2: Edge):
        self.token1 = token1
        self.token2 = token2
        self.edge1 = edge1
        self.edge2 = edge2