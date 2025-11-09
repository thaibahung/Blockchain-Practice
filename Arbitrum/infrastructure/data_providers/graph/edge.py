from decimal import Decimal

class Edge:
    def __init__(
            self, 
            pool: str,
            fee: int,
            version: str
        ):
        self.pool = pool   
        self.fee = fee
        self.version = version
    
        