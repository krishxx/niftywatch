"""
Angel One Broker Implementation
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


class AngelOneException(Exception):
    """Angel One specific exception"""
    pass


class AngelOne(BrokerBase):
    """
    Angel One Broker Implementation
    Uses Angel One REST API
    """

    BASE_URL = "https://api.angelbroking.com"

    def __init__(self):
        super().__init__("Angel One")
        self.access_token = None
        self.session = None
        self.user_id = None

    async def connect(
        self,
        access_token: str,
        user_id: str,
    ) -> bool:
        """
        Connect to Angel One using access token
        
        Args:
            access_token: Angel One access token
            user_id: User ID
            
        Returns:
            True if connection successful
        """
        try:
            self.access_token = access_token
            self.user_id = user_id
            self.session = aiohttp.ClientSession()

            # Verify token by making a simple API call
            async with self.session.get(
                f"{self.BASE_URL}/secure/angelbroking/user/v1/getProfile",
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise AngelOneException(f"Invalid access token: {await response.text()}")

            self.connected = True
            logger.info(f"[{self.broker_name}] Connected successfully")
            return True

        except Exception as e:
            logger.error(f"[{self.broker_name}] Connection failed: {str(e)}")
            raise

    async def disconnect(self) -> bool:
        """Disconnect from Angel One"""
        if self.session:
            await self.session.close()
        self.connected = False
        logger.info(f"[{self.broker_name}] Disconnected")
        return True

    async def place_order(self, order_request: OrderRequest) -> OrderResponse:
        """Place an order on Angel One"""
        if not self.connected:
            raise AngelOneException("Not connected to broker")

        self._validate_symbol(order_request.symbol)
        self._validate_quantity(order_request.quantity)

        order_data = {
            "mode": "PLACE",
            "exchangeTokens": order_request.symbol,
            "transactionType": order_request.side.value,
            "orderType": self._map_order_type(order_request.order_type),
            "quantity": str(order_request.quantity),
            "price": str(order_request.price or 0),
            "productType": order_request.product,
            "validity": order_request.validity,
        }

        if order_request.trigger_price:
            order_data["triggerPrice"] = str(order_request.trigger_price)

        if order_request.tag:
            order_data["tag"] = order_request.tag

        try:
            async with self.session.post(
                f"{self.BASE_URL}/secure/angelbroking/order/v1/placeOrder",
                json=order_data,
                headers=self._get_headers(),
            ) as response:
                if response.status not in [200, 201]:
                    raise AngelOneException(f"Order placement failed: {await response.text()}")

                result = await response.json()
                data = result.get("data", {})
                order_id = data.get("orderID")

                if not order_id:
                    raise AngelOneException("No order ID returned")

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
            raise AngelOneException("Not connected to broker")

        try:
            cancel_data = {
                "mode": "CANCEL",
                "orderID": order_id,
            }

            async with self.session.post(
                f"{self.BASE_URL}/secure/angelbroking/order/v1/cancelOrder",
                json=cancel_data,
                headers=self._get_headers(),
            ) as response:
                if response.status not in [200, 201]:
                    raise AngelOneException(f"Order cancellation failed: {await response.text()}")

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
            raise AngelOneException("Not connected to broker")

        raise NotImplementedError("Modify order not yet implemented for Angel One")

    async def get_order_status(self, order_id: str, symbol: str) -> OrderResponse:
        """Get order status"""
        if not self.connected:
            raise AngelOneException("Not connected to broker")

        try:
            params = {"mode": "PENDING"}

            async with self.session.get(
                f"{self.BASE_URL}/secure/angelbroking/order/v1/getOrderBook",
                params=params,
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise AngelOneException(f"Failed to fetch orders: {await response.text()}")

                result = await response.json()
                orders = result.get("data", [])

                for order in orders:
                    if str(order.get("orderID")) == order_id:
                        return self._parse_order(order)

                raise AngelOneException(f"Order {order_id} not found")

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get order status error: {str(e)}")
            raise

    async def get_all_orders(self) -> List[OrderResponse]:
        """Get all orders"""
        if not self.connected:
            raise AngelOneException("Not connected to broker")

        try:
            params = {"mode": "PENDING"}

            async with self.session.get(
                f"{self.BASE_URL}/secure/angelbroking/order/v1/getOrderBook",
                params=params,
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise AngelOneException(f"Failed to fetch orders: {await response.text()}")

                result = await response.json()
                orders = result.get("data", [])

                return [self._parse_order(order) for order in orders]

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get all orders error: {str(e)}")
            raise

    async def get_positions(self) -> List[Position]:
        """Get open positions"""
        if not self.connected:
            raise AngelOneException("Not connected to broker")

        try:
            params = {"mode": "DAY"}

            async with self.session.get(
                f"{self.BASE_URL}/secure/angelbroking/order/v1/getPosition",
                params=params,
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise AngelOneException(f"Failed to fetch positions: {await response.text()}")

                result = await response.json()
                positions_data = result.get("data", [])

                positions = []
                for position in positions_data:
                    if position.get("netQty") != 0:
                        positions.append(
                            Position(
                                symbol=position.get("symbol"),
                                quantity=int(position.get("netQty", 0)),
                                average_price=float(position.get("avgPrice", 0)),
                                current_price=float(position.get("lastPrice", 0)),
                                pnl=float(position.get("pnl", 0)),
                                pnl_percent=float(position.get("pnlPercent", 0)),
                            )
                        )

                return positions

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get positions error: {str(e)}")
            raise

    async def get_account_details(self) -> Account:
        """Get account details"""
        if not self.connected:
            raise AngelOneException("Not connected to broker")

        try:
            async with self.session.get(
                f"{self.BASE_URL}/secure/angelbroking/user/v1/getProfile",
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise AngelOneException(f"Failed to fetch account details: {await response.text()}")

                result = await response.json()
                profile = result.get("data", {})

                return Account(
                    balance=float(profile.get("netAvailableCash", 0)),
                    used_margin=float(profile.get("utilisedMargin", 0)),
                    available_margin=float(profile.get("availableMargin", 0)),
                    multiplier=1.0,
                )

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get account details error: {str(e)}")
            raise

    async def get_holding(self) -> List[Dict[str, Any]]:
        """Get holdings"""
        if not self.connected:
            raise AngelOneException("Not connected to broker")

        try:
            params = {"mode": "NET"}

            async with self.session.get(
                f"{self.BASE_URL}/secure/angelbroking/portfolio/v1/getHolding",
                params=params,
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise AngelOneException(f"Failed to fetch holdings: {await response.text()}")

                result = await response.json()
                return result.get("data", [])

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get holdings error: {str(e)}")
            raise

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get live quote"""
        if not self.connected:
            raise AngelOneException("Not connected to broker")

        try:
            quote_data = {
                "mode": "LTP",
                "exchangeTokens": f"NSE:{symbol}",
            }

            async with self.session.post(
                f"{self.BASE_URL}/secure/angelbroking/market/v1/quote/",
                json=quote_data,
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise AngelOneException(f"Failed to fetch quote: {await response.text()}")

                result = await response.json()
                data = result.get("data", {})
                return data.get("fetched", [{}])[0]

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
            "Content-Type": "application/json",
        }

    def _map_order_type(self, order_type: OrderType) -> str:
        """Map OrderType enum to Angel One order type"""
        mapping = {
            OrderType.MARKET: "MARKET",
            OrderType.LIMIT: "LIMIT",
            OrderType.STOP_LOSS: "STOP",
            OrderType.STOP_LOSS_LIMIT: "STOP",
        }
        return mapping.get(order_type, "MARKET")

    def _parse_order(self, order_data: Dict) -> OrderResponse:
        """Parse Angel One order response to OrderResponse"""
        status_mapping = {
            "PENDING": OrderStatus.PENDING,
            "OPEN": OrderStatus.OPEN,
            "COMPLETE": OrderStatus.FILLED,
            "CANCELLED": OrderStatus.CANCELLED,
            "REJECTED": OrderStatus.REJECTED,
        }

        return OrderResponse(
            order_id=str(order_data.get("orderID")),
            symbol=order_data.get("symbol"),
            side=OrderSide.BUY if order_data.get("transactionType") == "BUY" else OrderSide.SELL,
            quantity=int(order_data.get("quantity", 0)),
            filled_quantity=int(order_data.get("filledQuantity", 0)),
            price=float(order_data.get("price", 0)),
            filled_price=float(order_data.get("averagePrice")) if order_data.get("averagePrice") else None,
            order_type=OrderType.LIMIT if order_data.get("orderType") == "LIMIT" else OrderType.MARKET,
            status=status_mapping.get(order_data.get("orderStatus"), OrderStatus.PENDING),
            timestamp=order_data.get("orderTime", datetime.now().isoformat()),
        )
