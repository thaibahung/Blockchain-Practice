from decimal import Decimal

class Edge:
    def __init__(
            self, 
            token0: str, 
            token1: str, 
            pair_address: str, 
            weight: Decimal,
            price: Decimal,
            provider: str,
            fee: Decimal
        ):
        self.u_for_edge = token0
        self.v_for_edge = token1
        self.key = pair_address
        self.weight = weight
        self.price = Decimal(price)
        self.provider = provider   
        self.fee = Decimal(fee)