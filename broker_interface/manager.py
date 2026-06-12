"""
Multi-Broker Manager
Handles connections to multiple brokers and provides unified interface
"""
import logging
from typing import Dict, List, Optional, Any
from .base import (
    BrokerBase,
    OrderRequest,
    OrderResponse,
    OrderSide,
    OrderType,
    Position,
    Account,
)
from .zerodha import Zerodha
from .fyers import Fyers
from .angelone import AngelOne
from .flattrade import Flattrade

logger = logging.getLogger(__name__)


class BrokerManager:
    """
    Manages multiple broker connections
    Provides unified interface for trading across brokers
    """

    def __init__(self):
        self.brokers: Dict[str, BrokerBase] = {}
        self.active_broker: Optional[str] = None

    async def add_zerodha(
        self,
        api_key: str,
        user_id: str,
        password: str,
        totp_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        broker_alias: str = "zerodha",
    ) -> bool:
        """Add Zerodha broker"""
        try:
            zerodha = Zerodha()
            await zerodha.connect(api_key, user_id, password, totp_secret, access_token)
            self.brokers[broker_alias] = zerodha
            
            if not self.active_broker:
                self.active_broker = broker_alias
            
            logger.info(f"Zerodha broker added as '{broker_alias}'")
            return True
        except Exception as e:
            logger.error(f"Failed to add Zerodha broker: {str(e)}")
            raise

    async def add_fyers(
        self,
        access_token: str,
        broker_alias: str = "fyers",
    ) -> bool:
        """Add Fyers broker"""
        try:
            fyers = Fyers()
            await fyers.connect(access_token)
            self.brokers[broker_alias] = fyers
            
            if not self.active_broker:
                self.active_broker = broker_alias
            
            logger.info(f"Fyers broker added as '{broker_alias}'")
            return True
        except Exception as e:
            logger.error(f"Failed to add Fyers broker: {str(e)}")
            raise

    async def add_angelone(
        self,
        access_token: str,
        user_id: str,
        broker_alias: str = "angelone",
    ) -> bool:
        """Add Angel One broker"""
        try:
            angelone = AngelOne()
            await angelone.connect(access_token, user_id)
            self.brokers[broker_alias] = angelone
            
            if not self.active_broker:
                self.active_broker = broker_alias
            
            logger.info(f"Angel One broker added as '{broker_alias}'")
            return True
        except Exception as e:
            logger.error(f"Failed to add Angel One broker: {str(e)}")
            raise

    async def add_flattrade(
        self,
        auth_token: str,
        user_id: str,
        broker_alias: str = "flattrade",
    ) -> bool:
        """Add Flattrade broker"""
        try:
            flattrade = Flattrade()
            await flattrade.connect(auth_token, user_id)
            self.brokers[broker_alias] = flattrade
            
            if not self.active_broker:
                self.active_broker = broker_alias
            
            logger.info(f"Flattrade broker added as '{broker_alias}'")
            return True
        except Exception as e:
            logger.error(f"Failed to add Flattrade broker: {str(e)}")
            raise

    def set_active_broker(self, broker_alias: str) -> bool:
        """Set active broker for trading"""
        if broker_alias not in self.brokers:
            raise ValueError(f"Broker '{broker_alias}' not found")
        
        self.active_broker = broker_alias
        logger.info(f"Active broker set to '{broker_alias}'")
        return True

    def get_active_broker(self) -> Optional[BrokerBase]:
        """Get active broker instance"""
        if not self.active_broker:
            raise RuntimeError("No active broker set")
        return self.brokers.get(self.active_broker)

    def get_broker(self, broker_alias: str) -> BrokerBase:
        """Get specific broker instance"""
        if broker_alias not in self.brokers:
            raise ValueError(f"Broker '{broker_alias}' not found")
        return self.brokers[broker_alias]

    def list_brokers(self) -> Dict[str, str]:
        """List all connected brokers"""
        return {alias: broker.broker_name for alias, broker in self.brokers.items()}

    async def disconnect_broker(self, broker_alias: str) -> bool:
        """Disconnect a specific broker"""
        if broker_alias not in self.brokers:
            raise ValueError(f"Broker '{broker_alias}' not found")
        
        await self.brokers[broker_alias].disconnect()
        
        if self.active_broker == broker_alias:
            # Set another broker as active
            remaining = [b for b in self.brokers.keys() if b != broker_alias]
            self.active_broker = remaining[0] if remaining else None
        
        del self.brokers[broker_alias]
        logger.info(f"Broker '{broker_alias}' disconnected")
        return True

    async def disconnect_all(self) -> bool:
        """Disconnect all brokers"""
        for alias in list(self.brokers.keys()):
            await self.brokers[alias].disconnect()
        
        self.brokers.clear()
        self.active_broker = None
        logger.info("All brokers disconnected")
        return True

    # ==================== UNIFIED TRADING INTERFACE ====================

    async def place_buy_order(
        self,
        symbol: str,
        quantity: int,
        price: Optional[float] = None,
        order_type: OrderType = OrderType.MARKET,
        broker_alias: Optional[str] = None,
        **kwargs
    ) -> OrderResponse:
        """Place buy order on active or specified broker"""
        broker = self._get_broker_for_order(broker_alias)
        return await broker.place_buy_order(symbol, quantity, price, order_type, **kwargs)

    async def place_sell_order(
        self,
        symbol: str,
        quantity: int,
        price: Optional[float] = None,
        order_type: OrderType = OrderType.MARKET,
        broker_alias: Optional[str] = None,
        **kwargs
    ) -> OrderResponse:
        """Place sell order on active or specified broker"""
        broker = self._get_broker_for_order(broker_alias)
        return await broker.place_sell_order(symbol, quantity, price, order_type, **kwargs)

    async def place_stoploss_order(
        self,
        symbol: str,
        quantity: int,
        trigger_price: float,
        limit_price: Optional[float] = None,
        side: OrderSide = OrderSide.SELL,
        broker_alias: Optional[str] = None,
        **kwargs
    ) -> OrderResponse:
        """Place stoploss order on active or specified broker"""
        broker = self._get_broker_for_order(broker_alias)
        return await broker.place_stoploss_order(
            symbol, quantity, trigger_price, limit_price, side, **kwargs
        )

    async def place_target_order(
        self,
        symbol: str,
        quantity: int,
        target_price: float,
        side: OrderSide = OrderSide.SELL,
        broker_alias: Optional[str] = None,
        **kwargs
    ) -> OrderResponse:
        """Place target order on active or specified broker"""
        broker = self._get_broker_for_order(broker_alias)
        return await broker.place_target_order(symbol, quantity, target_price, side, **kwargs)

    async def place_order(
        self,
        order_request: OrderRequest,
        broker_alias: Optional[str] = None,
    ) -> OrderResponse:
        """Place order on active or specified broker"""
        broker = self._get_broker_for_order(broker_alias)
        return await broker.place_order(order_request)

    async def cancel_order(
        self,
        order_id: str,
        symbol: str,
        broker_alias: Optional[str] = None,
    ) -> bool:
        """Cancel order on active or specified broker"""
        broker = self._get_broker_for_order(broker_alias)
        return await broker.cancel_order(order_id, symbol)

    async def modify_order(
        self,
        order_id: str,
        symbol: str,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        broker_alias: Optional[str] = None,
    ) -> OrderResponse:
        """Modify order on active or specified broker"""
        broker = self._get_broker_for_order(broker_alias)
        return await broker.modify_order(order_id, symbol, quantity, price, trigger_price)

    async def get_order_status(
        self,
        order_id: str,
        symbol: str,
        broker_alias: Optional[str] = None,
    ) -> OrderResponse:
        """Get order status from active or specified broker"""
        broker = self._get_broker_for_order(broker_alias)
        return await broker.get_order_status(order_id, symbol)

    async def get_all_orders(self, broker_alias: Optional[str] = None) -> List[OrderResponse]:
        """Get all orders from active or specified broker"""
        broker = self._get_broker_for_order(broker_alias)
        return await broker.get_all_orders()

    async def get_positions(self, broker_alias: Optional[str] = None) -> List[Position]:
        """Get positions from active or specified broker"""
        broker = self._get_broker_for_order(broker_alias)
        return await broker.get_positions()

    async def get_account_details(self, broker_alias: Optional[str] = None) -> Account:
        """Get account details from active or specified broker"""
        broker = self._get_broker_for_order(broker_alias)
        return await broker.get_account_details()

    async def get_holdings(self, broker_alias: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get holdings from active or specified broker"""
        broker = self._get_broker_for_order(broker_alias)
        return await broker.get_holding()

    async def get_quote(self, symbol: str, broker_alias: Optional[str] = None) -> Dict[str, Any]:
        """Get quote from active or specified broker"""
        broker = self._get_broker_for_order(broker_alias)
        return await broker.get_quote(symbol)

    async def get_positions_all_brokers(self) -> Dict[str, List[Position]]:
        """Get positions from all brokers"""
        result = {}
        for alias, broker in self.brokers.items():
            try:
                result[alias] = await broker.get_positions()
            except Exception as e:
                logger.error(f"Error fetching positions from {alias}: {str(e)}")
                result[alias] = []
        return result

    async def get_all_orders_all_brokers(self) -> Dict[str, List[OrderResponse]]:
        """Get all orders from all brokers"""
        result = {}
        for alias, broker in self.brokers.items():
            try:
                result[alias] = await broker.get_all_orders()
            except Exception as e:
                logger.error(f"Error fetching orders from {alias}: {str(e)}")
                result[alias] = []
        return result

    async def get_account_summary(self) -> Dict[str, Account]:
        """Get account summary from all brokers"""
        result = {}
        for alias, broker in self.brokers.items():
            try:
                result[alias] = await broker.get_account_details()
            except Exception as e:
                logger.error(f"Error fetching account details from {alias}: {str(e)}")
                result[alias] = None
        return result

    def _get_broker_for_order(self, broker_alias: Optional[str] = None) -> BrokerBase:
        """Get broker instance for order placement"""
        if broker_alias:
            return self.get_broker(broker_alias)
        return self.get_active_broker()
