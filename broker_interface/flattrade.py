"""
Flattrade Broker Implementation
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


class FlattradeException(Exception):
    """Flattrade specific exception"""
    pass


class Flattrade(BrokerBase):
    """
    Flattrade Broker Implementation
    Uses Flattrade REST API
    """

    BASE_URL = "https://api.flattrade.in"

    def __init__(self):
        super().__init__("Flattrade")
        self.auth_token = None
        self.user_id = None
        self.session = None

    async def connect(
        self,
        auth_token: str,
        user_id: str,
    ) -> bool:
        """
        Connect to Flattrade using auth token
        
        Args:
            auth_token: Flattrade auth token
            user_id: User ID
            
        Returns:
            True if connection successful
        """
        try:
            self.auth_token = auth_token
            self.user_id = user_id
            self.session = aiohttp.ClientSession()

            # Verify token by making a simple API call
            async with self.session.get(
                f"{self.BASE_URL}/V2/UserProfile",
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise FlattradeException(f"Invalid auth token: {await response.text()}")

            self.connected = True
            logger.info(f"[{self.broker_name}] Connected successfully")
            return True

        except Exception as e:
            logger.error(f"[{self.broker_name}] Connection failed: {str(e)}")
            raise

    async def disconnect(self) -> bool:
        """Disconnect from Flattrade"""
        if self.session:
            await self.session.close()
        self.connected = False
        logger.info(f"[{self.broker_name}] Disconnected")
        return True

    async def place_order(self, order_request: OrderRequest) -> OrderResponse:
        """Place an order on Flattrade"""
        if not self.connected:
            raise FlattradeException("Not connected to broker")

        self._validate_symbol(order_request.symbol)
        self._validate_quantity(order_request.quantity)

        order_data = {
            "exch": self._get_exchange(order_request.symbol),
            "symbol": order_request.symbol,
            "side": order_request.side.value,
            "quantity": order_request.quantity,
            "price": order_request.price or 0,
            "pricetype": self._map_order_type(order_request.order_type),
            "product": order_request.product,
        }

        if order_request.trigger_price:
            order_data["triggerprice"] = order_request.trigger_price

        try:
            async with self.session.post(
                f"{self.BASE_URL}/V2/PlaceOrder",
                json=order_data,
                headers=self._get_headers(),
            ) as response:
                if response.status not in [200, 201]:
                    raise FlattradeException(f"Order placement failed: {await response.text()}")

                result = await response.json()
                order_id = result.get("data", {}).get("orderid")

                if not order_id:
                    raise FlattradeException("No order ID returned")

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
            raise FlattradeException("Not connected to broker")

        try:
            cancel_data = {
                "orderid": order_id,
            }

            async with self.session.post(
                f"{self.BASE_URL}/V2/CancelOrder",
                json=cancel_data,
                headers=self._get_headers(),
            ) as response:
                if response.status not in [200, 201]:
                    raise FlattradeException(f"Order cancellation failed: {await response.text()}")

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
            raise FlattradeException("Not connected to broker")

        raise NotImplementedError("Modify order not yet implemented for Flattrade")

    async def get_order_status(self, order_id: str, symbol: str) -> OrderResponse:
        """Get order status"""
        if not self.connected:
            raise FlattradeException("Not connected to broker")

        try:
            async with self.session.get(
                f"{self.BASE_URL}/V2/OrderList",
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise FlattradeException(f"Failed to fetch orders: {await response.text()}")

                result = await response.json()
                orders = result.get("data", [])

                for order in orders:
                    if str(order.get("orderid")) == order_id:
                        return self._parse_order(order)

                raise FlattradeException(f"Order {order_id} not found")

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get order status error: {str(e)}")
            raise

    async def get_all_orders(self) -> List[OrderResponse]:
        """Get all orders"""
        if not self.connected:
            raise FlattradeException("Not connected to broker")

        try:
            async with self.session.get(
                f"{self.BASE_URL}/V2/OrderList",
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise FlattradeException(f"Failed to fetch orders: {await response.text()}")

                result = await response.json()
                orders = result.get("data", [])

                return [self._parse_order(order) for order in orders]

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get all orders error: {str(e)}")
            raise

    async def get_positions(self) -> List[Position]:
        """Get open positions"""
        if not self.connected:
            raise FlattradeException("Not connected to broker")

        try:
            async with self.session.get(
                f"{self.BASE_URL}/V2/PositionList",
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise FlattradeException(f"Failed to fetch positions: {await response.text()}")

                result = await response.json()
                positions_data = result.get("data", [])

                positions = []
                for position in positions_data:
                    if position.get("netqty") != 0:
                        positions.append(
                            Position(
                                symbol=position.get("symbol"),
                                quantity=int(position.get("netqty", 0)),
                                average_price=float(position.get("avgprice", 0)),
                                current_price=float(position.get("ltp", 0)),
                                pnl=float(position.get("pnl", 0)),
                                pnl_percent=float(position.get("pnlpercent", 0)),
                            )
                        )

                return positions

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get positions error: {str(e)}")
            raise

    async def get_account_details(self) -> Account:
        """Get account details"""
        if not self.connected:
            raise FlattradeException("Not connected to broker")

        try:
            async with self.session.get(
                f"{self.BASE_URL}/V2/UserProfile",
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise FlattradeException(f"Failed to fetch account details: {await response.text()}")

                result = await response.json()
                data = result.get("data", {})

                return Account(
                    balance=float(data.get("cash", 0)),
                    used_margin=float(data.get("marginused", 0)),
                    available_margin=float(data.get("marginleft", 0)),
                    multiplier=1.0,
                )

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get account details error: {str(e)}")
            raise

    async def get_holding(self) -> List[Dict[str, Any]]:
        """Get holdings"""
        if not self.connected:
            raise FlattradeException("Not connected to broker")

        try:
            async with self.session.get(
                f"{self.BASE_URL}/V2/HoldingList",
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise FlattradeException(f"Failed to fetch holdings: {await response.text()}")

                result = await response.json()
                return result.get("data", [])

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get holdings error: {str(e)}")
            raise

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get live quote"""
        if not self.connected:
            raise FlattradeException("Not connected to broker")

        try:
            params = {
                "mode": "LTP",
                "symbol": symbol,
            }

            async with self.session.get(
                f"{self.BASE_URL}/V2/QuoteData",
                params=params,
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise FlattradeException(f"Failed to fetch quote: {await response.text()}")

                result = await response.json()
                return result.get("data", {})

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
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

    def _get_exchange(self, symbol: str) -> str:
        """Determine exchange from symbol"""
        if symbol.startswith("NIFTY") or symbol.startswith("BANKNIFTY"):
            return "NFO"
        return "NSE"

    def _map_order_type(self, order_type: OrderType) -> str:
        """Map OrderType enum to Flattrade order type"""
        mapping = {
            OrderType.MARKET: "MKT",
            OrderType.LIMIT: "LMT",
            OrderType.STOP_LOSS: "SL",
            OrderType.STOP_LOSS_LIMIT: "SL-M",
        }
        return mapping.get(order_type, "MKT")

    def _parse_order(self, order_data: Dict) -> OrderResponse:
        """Parse Flattrade order response to OrderResponse"""
        status_mapping = {
            "open": OrderStatus.OPEN,
            "filled": OrderStatus.FILLED,
            "cancelled": OrderStatus.CANCELLED,
            "rejected": OrderStatus.REJECTED,
            "pending": OrderStatus.PENDING,
        }

        return OrderResponse(
            order_id=str(order_data.get("orderid")),
            symbol=order_data.get("symbol"),
            side=OrderSide.BUY if order_data.get("side") == "BUY" else OrderSide.SELL,
            quantity=int(order_data.get("quantity", 0)),
            filled_quantity=int(order_data.get("filledqty", 0)),
            price=float(order_data.get("price", 0)),
            filled_price=float(order_data.get("avgprice")) if order_data.get("avgprice") else None,
            order_type=OrderType.LIMIT if order_data.get("pricetype") == "LMT" else OrderType.MARKET,
            status=status_mapping.get(order_data.get("orderstatus", "").lower(), OrderStatus.PENDING),
            timestamp=order_data.get("ordertimestamp", datetime.now().isoformat()),
        )
