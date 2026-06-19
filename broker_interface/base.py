from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class OrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class InstrumentType(Enum):
    EQUITY = "EQUITY"
    FUTURES = "FUTURES"
    OPTIONS = "OPTIONS"


@dataclass
class OrderRequest:
    symbol: str
    quantity: int
    side: OrderSide
    order_type: OrderType
    price: Optional[float] = None
    trigger_price: Optional[float] = None


@dataclass
class OrderResponse:
    order_id: str
    symbol: str
    quantity: int
    side: OrderSide
    order_type: OrderType
    status: OrderStatus
    price: Optional[float] = None


@dataclass
class Position:
    symbol: str
    quantity: int
    buy_price: float
    current_price: float
    pnl: float


@dataclass
class Account:
    account_id: str
    balance: float
    margin_used: float
    margin_available: float


class BrokerBase(ABC):
    """Abstract base class for all brokers"""
    
    def __init__(self):
        self.broker_name = "Base"
    
    @abstractmethod
    async def connect(self, *args, **kwargs):
        """Connect to broker"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from broker"""
        pass
    
    @abstractmethod
    async def place_buy_order(self, symbol: str, quantity: int, price: Optional[float] = None, order_type: OrderType = OrderType.MARKET, **kwargs) -> OrderResponse:
        pass
    
    @abstractmethod
    async def place_sell_order(self, symbol: str, quantity: int, price: Optional[float] = None, order_type: OrderType = OrderType.MARKET, **kwargs) -> OrderResponse:
        pass
    
    @abstractmethod
    async def place_stoploss_order(self, symbol: str, quantity: int, trigger_price: float, limit_price: Optional[float] = None, side: OrderSide = OrderSide.SELL, **kwargs) -> OrderResponse:
        pass
    
    @abstractmethod
    async def place_target_order(self, symbol: str, quantity: int, target_price: float, side: OrderSide = OrderSide.SELL, **kwargs) -> OrderResponse:
        pass
    
    @abstractmethod
    async def place_order(self, order_request: OrderRequest) -> OrderResponse:
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        pass
    
    @abstractmethod
    async def modify_order(self, order_id: str, symbol: str, quantity: Optional[int] = None, price: Optional[float] = None, trigger_price: Optional[float] = None) -> OrderResponse:
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str, symbol: str) -> OrderResponse:
        pass
    
    @abstractmethod
    async def get_all_orders(self) -> List[OrderResponse]:
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        pass
    
    @abstractmethod
    async def get_account_details(self) -> Account:
        pass
    
    @abstractmethod
    async def get_holding(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        pass
