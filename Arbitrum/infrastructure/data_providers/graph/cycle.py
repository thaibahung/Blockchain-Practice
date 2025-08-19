from typing import List, Optional, Dict, Any, Set, Tuple
from decimal import Decimal
import networkx as nx
import math

from infrastructure.data_providers.graph.edge import Edge
from domain.entities.models import DexTradingPair

class Cycle:
    def __init__(self, cycle: List[Edge], profit: Decimal):
        self.cycle = cycle
        self.profit = profit
