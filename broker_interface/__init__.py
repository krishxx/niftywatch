"""
Multi-Broker Trading Interface
Unified interface for trading across multiple Indian stock brokers
"""

from broker_interface.base import (
    BrokerBase,
    OrderType,
    OrderSide,
    OrderStatus,
    InstrumentType,
    OrderRequest,
    OrderResponse,
    Position,
    Account,
)
from broker_interface.zerodha import Zerodha
from broker_interface.fyers import Fyers
from broker_interface.angelone import AngelOne
from broker_interface.flattrade import Flattrade
from broker_interface.manager import BrokerManager

__version__ = "1.0.0"
__author__ = "Krishna Sadula"
__description__ = "Multi-Broker Trading Interface for Indian Stock Market"

__all__ = [
    "BrokerBase",
    "OrderType",
    "OrderSide",
    "OrderStatus",
    "InstrumentType",
    "OrderRequest",
    "OrderResponse",
    "Position",
    "Account",
    "Zerodha",
    "Fyers",
    "AngelOne",
    "Flattrade",
    "BrokerManager",
]
