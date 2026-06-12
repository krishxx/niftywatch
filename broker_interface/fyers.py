"""
Fyers Broker Implementation
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

import aiohttp
from .base import (
    BrokerBase,
    OrderRequest,
    OrderResponse,
    OrderStatus,
    OrderSide,
    OrderType,
    Position,
    Account,
    InstrumentType,
)

logger = logging.getLogger(__name__)


class FyersException(Exception):
    """Fyers specific exception"""
    pass


class Fyers(BrokerBase):
    """
    Fyers Broker Implementation
    Uses Fyers API v2
    """

    BASE_URL = "https://api-t2.fyers.in/api/v2"

    def __init__(self):
        super().__init__("Fyers")
        self.access_token = None
        self.session = None

    async def connect(
        self,
        access_token: str,
    ) -> bool:
        """
        Connect to Fyers using access token
        
        Args:
            access_token: Fyers access token
            
        Returns:
            True if connection successful
        """
        try:
            self.access_token = access_token
            self.session = aiohttp.ClientSession()

            # Verify token by making a simple API call
            async with self.session.get(
                f"{self.BASE_URL}/profile",
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise FyersException(f"Invalid access token: {await response.text()}")

            self.connected = True
            logger.info(f"[{self.broker_name}] Connected successfully")
            return True

        except Exception as e:
            logger.error(f"[{self.broker_name}] Connection failed: {str(e)}")
            raise

    async def disconnect(self) -> bool:
        """Disconnect from Fyers"""
        if self.session:
            await self.session.close()
        self.connected = False
        logger.info(f"[{self.broker_name}] Disconnected")
        return True

    async def place_order(self, order_request: OrderRequest) -> OrderResponse:
        """Place an order on Fyers"""
        if not self.connected:
            raise FyersException("Not connected to broker")

        self._validate_symbol(order_request.symbol)
        self._validate_quantity(order_request.quantity)

        order_data = {
            "symbol": order_request.symbol,
            "qty": order_request.quantity,
            "type": self._map_order_type(order_request.order_type),
            "side": 1 if order_request.side == OrderSide.BUY else -1,
            "productType": self._map_product_type(order_request.product),
            "limitPrice": order_request.price or 0,
            "stopPrice": order_request.trigger_price or 0,
        }

        try:
            async with self.session.post(
                f"{self.BASE_URL}/orders/place",
                json=order_data,
                headers=self._get_headers(),
            ) as response:
                if response.status not in [200, 201]:
                    raise FyersException(f"Order placement failed: {await response.text()}")

                result = await response.json()
                order_id = result.get("orderNum")

                if not order_id:
                    raise FyersException("No order ID returned")

                logger.info(
                    f"[{self.broker_name}] Order placed: {order_id} - {order_request.symbol}"
                )

                return OrderResponse(
                    order_id=str(order_id),
                    symbol=order_request.symbol,
                    side=order_request.side,
                    quantity=order_request.quantity,
                    filled_quantity=0,
                    price=order_request.price or 0,
                    filled_price=None,
                    order_type=order_request.order_type,
                    status=OrderStatus.PENDING,
                    timestamp=datetime.now().isoformat(),
                )

        except Exception as e:
            logger.error(f"[{self.broker_name}] Order placement error: {str(e)}")
            raise

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        if not self.connected:
            raise FyersException("Not connected to broker")

        try:
            cancel_data = {"id": order_id}

            async with self.session.delete(
                f"{self.BASE_URL}/orders/cancel",
                json=cancel_data,
                headers=self._get_headers(),
            ) as response:
                if response.status not in [200, 201]:
                    raise FyersException(f"Order cancellation failed: {await response.text()}")

                logger.info(f"[{self.broker_name}] Order cancelled: {order_id}")
                return True

        except Exception as e:
            logger.error(f"[{self.broker_name}] Order cancellation error: {str(e)}")
            raise

    async def modify_order(
        self,
        order_id: str,
        symbol: str,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
    ) -> OrderResponse:
        """Modify an order"""
        if not self.connected:
            raise FyersException("Not connected to broker")

        raise NotImplementedError("Modify order not yet implemented for Fyers")

    async def get_order_status(self, order_id: str, symbol: str) -> OrderResponse:
        """Get order status"""
        if not self.connected:
            raise FyersException("Not connected to broker")

        try:
            async with self.session.get(
                f"{self.BASE_URL}/orders",
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise FyersException(f"Failed to fetch orders: {await response.text()}")

                result = await response.json()
                orders = result.get("orderBook", [])

                for order in orders:
                    if str(order.get("id")) == order_id:
                        return self._parse_order(order)

                raise FyersException(f"Order {order_id} not found")

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get order status error: {str(e)}")
            raise

    async def get_all_orders(self) -> List[OrderResponse]:
        """Get all orders"""
        if not self.connected:
            raise FyersException("Not connected to broker")

        try:
            async with self.session.get(
                f"{self.BASE_URL}/orders",
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise FyersException(f"Failed to fetch orders: {await response.text()}")

                result = await response.json()
                orders = result.get("orderBook", [])

                return [self._parse_order(order) for order in orders]

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get all orders error: {str(e)}")
            raise

    async def get_positions(self) -> List[Position]:
        """Get open positions"""
        if not self.connected:
            raise FyersException("Not connected to broker")

        try:
            async with self.session.get(
                f"{self.BASE_URL}/positions",
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise FyersException(f"Failed to fetch positions: {await response.text()}")

                result = await response.json()
                positions_data = result.get("netPositions", [])

                positions = []
                for position in positions_data:
                    positions.append(
                        Position(
                            symbol=position.get("symbol"),
                            quantity=position.get("qty", 0),
                            average_price=position.get("avgPrice", 0),
                            current_price=position.get("netPrice", 0),
                            pnl=position.get("pl", 0),
                            pnl_percent=position.get("plpc", 0),
                        )
                    )

                return positions

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get positions error: {str(e)}")
            raise

    async def get_account_details(self) -> Account:
        """Get account details"""
        if not self.connected:
            raise FyersException("Not connected to broker")

        try:
            async with self.session.get(
                f"{self.BASE_URL}/funds",
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise FyersException(f"Failed to fetch account details: {await response.text()}")

                result = await response.json()
                funds = result.get("fund_limit", [{}])[0]

                return Account(
                    balance=funds.get("net", 0),
                    used_margin=funds.get("used", 0),
                    available_margin=funds.get("available", 0),
                    multiplier=1.0,
                )

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get account details error: {str(e)}")
            raise

    async def get_holding(self) -> List[Dict[str, Any]]:
        """Get holdings"""
        if not self.connected:
            raise FyersException("Not connected to broker")

        try:
            async with self.session.get(
                f"{self.BASE_URL}/holdings",
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise FyersException(f"Failed to fetch holdings: {await response.text()}")

                result = await response.json()
                return result.get("holdings", [])

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get holdings error: {str(e)}")
            raise

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get live quote"""
        if not self.connected:
            raise FyersException("Not connected to broker")

        try:
            params = {"symbols": symbol}

            async with self.session.get(
                f"{self.BASE_URL}/quotes",
                params=params,
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise FyersException(f"Failed to fetch quote: {await response.text()}")

                result = await response.json()
                quotes = result.get("d", {})
                return quotes.get(symbol, {})

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get quote error: {str(e)}")
            raise

    async def place_buy_order(
        self,
        symbol: str,
        quantity: int,
        price: Optional[float] = None,
        order_type: OrderType = OrderType.MARKET,
        **kwargs
    ) -> OrderResponse:
        """Place buy order"""
        order_request = OrderRequest(
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=quantity,
            order_type=order_type,
            price=price,
            **kwargs,
        )
        return await self.place_order(order_request)

    async def place_sell_order(
        self,
        symbol: str,
        quantity: int,
        price: Optional[float] = None,
        order_type: OrderType = OrderType.MARKET,
        **kwargs
    ) -> OrderResponse:
        """Place sell order"""
        order_request = OrderRequest(
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=quantity,
            order_type=order_type,
            price=price,
            **kwargs,
        )
        return await self.place_order(order_request)

    async def place_stoploss_order(
        self,
        symbol: str,
        quantity: int,
        trigger_price: float,
        limit_price: Optional[float] = None,
        side: OrderSide = OrderSide.SELL,
        **kwargs
    ) -> OrderResponse:
        """Place stoploss order"""
        order_type = (
            OrderType.STOP_LOSS_LIMIT if limit_price else OrderType.STOP_LOSS
        )

        order_request = OrderRequest(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            trigger_price=trigger_price,
            price=limit_price,
            **kwargs,
        )
        return await self.place_order(order_request)

    async def place_target_order(
        self,
        symbol: str,
        quantity: int,
        target_price: float,
        side: OrderSide = OrderSide.SELL,
        **kwargs
    ) -> OrderResponse:
        """Place target order"""
        order_request = OrderRequest(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=OrderType.LIMIT,
            price=target_price,
            **kwargs,
        )
        return await self.place_order(order_request)

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.access_token}",
        }

    def _map_order_type(self, order_type: OrderType) -> int:
        """Map OrderType enum to Fyers order type"""
        mapping = {
            OrderType.MARKET: 1,
            OrderType.LIMIT: 1,
            OrderType.STOP_LOSS: 2,
            OrderType.STOP_LOSS_LIMIT: 2,
        }
        return mapping.get(order_type, 1)

    def _map_product_type(self, product: str) -> str:
        """Map product type"""
        mapping = {
            "MIS": "MIS",
            "CNC": "CNC",
            "NRML": "NRML",
        }
        return mapping.get(product, "MIS")

    def _parse_order(self, order_data: Dict) -> OrderResponse:
        """Parse Fyers order response to OrderResponse"""
        status_mapping = {
            1: OrderStatus.OPEN,
            2: OrderStatus.FILLED,
            3: OrderStatus.CANCELLED,
            4: OrderStatus.REJECTED,
            5: OrderStatus.PENDING,
        }

        return OrderResponse(
            order_id=str(order_data.get("id")),
            symbol=order_data.get("symbol"),
            side=OrderSide.BUY if order_data.get("side", 1) == 1 else OrderSide.SELL,
            quantity=order_data.get("qty", 0),
            filled_quantity=order_data.get("filledQty", 0),
            price=order_data.get("limitPrice", 0),
            filled_price=order_data.get("avgPrice"),
            order_type=OrderType.LIMIT if order_data.get("type") == 1 else OrderType.STOP_LOSS,
            status=status_mapping.get(order_data.get("orderStatus"), OrderStatus.PENDING),
            timestamp=order_data.get("orderDateTime", datetime.now().isoformat()),
        )
