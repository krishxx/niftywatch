"""
Zerodha Broker Implementation
"""
import hashlib
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

import aiohttp
import pyotp
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


class ZerodhaException(Exception):
    """Zerodha specific exception"""
    pass


class Zerodha(BrokerBase):
    """
    Zerodha Broker Implementation
    Uses KiteConnect API v3
    """

    BASE_URL = "https://api.kite.trade"
    MARKET_URL = "https://quote.kite.trade"

    def __init__(self):
        super().__init__("Zerodha")
        self.api_key = None
        self.access_token = None
        self.user_id = None
        self.session = None

    async def connect(
        self,
        api_key: str,
        user_id: str,
        password: str,
        totp_secret: Optional[str] = None,
        access_token: Optional[str] = None,
    ) -> bool:
        """
        Connect to Zerodha using credentials or access token
        
        Args:
            api_key: Zerodha API key
            user_id: Zerodha User ID
            password: Password
            totp_secret: TOTP secret for 2FA
            access_token: If already have access token, use this
            
        Returns:
            True if connection successful
        """
        try:
            self.api_key = api_key
            self.user_id = user_id
            self.session = aiohttp.ClientSession()

            if access_token:
                self.access_token = access_token
                self.connected = True
                logger.info(f"[{self.broker_name}] Connected using access token")
                return True

            # Generate OTP
            if totp_secret:
                totp = pyotp.TOTP(totp_secret)
                otp = totp.now()
            else:
                # For testing, could prompt user
                raise ZerodhaException(
                    "TOTP secret required for 2FA. Provide totp_secret parameter."
                )

            # Get login data
            login_data = {
                "user_id": user_id,
                "password": password,
                "otp": otp,
            }

            async with self.session.post(
                f"{self.BASE_URL}/login", data=login_data
            ) as response:
                if response.status != 200:
                    raise ZerodhaException(f"Login failed: {await response.text()}")

                login_response = await response.json()
                request_id = login_response.get("data", {}).get("request_id")

            # Verify OTP
            verify_data = {
                "request_id": request_id,
                "otp": otp,
            }

            async with self.session.post(
                f"{self.BASE_URL}/auth/validate_otp", data=verify_data
            ) as response:
                if response.status != 200:
                    raise ZerodhaException(f"OTP validation failed: {await response.text()}")

                auth_response = await response.json()
                self.access_token = auth_response.get("data", {}).get("access_token")

            if not self.access_token:
                raise ZerodhaException("Failed to obtain access token")

            self.connected = True
            logger.info(f"[{self.broker_name}] Connected successfully")
            return True

        except Exception as e:
            logger.error(f"[{self.broker_name}] Connection failed: {str(e)}")
            raise

    async def disconnect(self) -> bool:
        """Disconnect from Zerodha"""
        if self.session:
            await self.session.close()
        self.connected = False
        logger.info(f"[{self.broker_name}] Disconnected")
        return True

    async def place_order(self, order_request: OrderRequest) -> OrderResponse:
        """Place an order on Zerodha"""
        if not self.connected:
            raise ZerodhaException("Not connected to broker")

        self._validate_symbol(order_request.symbol)
        self._validate_quantity(order_request.quantity)

        order_data = {
            "variety": "regular",
            "exchange": self._get_exchange(order_request.symbol),
            "tradingsymbol": order_request.symbol,
            "transaction_type": order_request.side.value,
            "order_type": self._map_order_type(order_request.order_type),
            "quantity": order_request.quantity,
            "price": order_request.price or 0,
            "product": order_request.product,
            "validity": order_request.validity,
            "tag": order_request.tag,
        }

        if order_request.trigger_price:
            order_data["trigger_price"] = order_request.trigger_price

        if order_request.disclosed_quantity:
            order_data["iceberg_legs"] = order_request.disclosed_quantity

        try:
            async with self.session.post(
                f"{self.BASE_URL}/orders/regular",
                data=order_data,
                headers=self._get_headers(),
            ) as response:
                if response.status not in [200, 201]:
                    raise ZerodhaException(f"Order placement failed: {await response.text()}")

                result = await response.json()
                order_id = result.get("data", {}).get("order_id")

                logger.info(
                    f"[{self.broker_name}] Order placed: {order_id} - {order_request.symbol}"
                )

                return OrderResponse(
                    order_id=order_id,
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
            raise ZerodhaException("Not connected to broker")

        try:
            cancel_data = {
                "variety": "regular",
                "order_id": order_id,
                "exchange": self._get_exchange(symbol),
            }

            async with self.session.delete(
                f"{self.BASE_URL}/orders/regular/{order_id}",
                data=cancel_data,
                headers=self._get_headers(),
            ) as response:
                if response.status not in [200, 201]:
                    raise ZerodhaException(f"Order cancellation failed: {await response.text()}")

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
            raise ZerodhaException("Not connected to broker")

        # Implementation similar to place_order
        raise NotImplementedError("Modify order not yet implemented for Zerodha")

    async def get_order_status(self, order_id: str, symbol: str) -> OrderResponse:
        """Get order status"""
        if not self.connected:
            raise ZerodhaException("Not connected to broker")

        try:
            async with self.session.get(
                f"{self.BASE_URL}/orders",
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise ZerodhaException(f"Failed to fetch orders: {await response.text()}")

                result = await response.json()
                orders = result.get("data", [])

                for order in orders:
                    if order.get("order_id") == order_id:
                        return self._parse_order(order)

                raise ZerodhaException(f"Order {order_id} not found")

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get order status error: {str(e)}")
            raise

    async def get_all_orders(self) -> List[OrderResponse]:
        """Get all orders"""
        if not self.connected:
            raise ZerodhaException("Not connected to broker")

        try:
            async with self.session.get(
                f"{self.BASE_URL}/orders",
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise ZerodhaException(f"Failed to fetch orders: {await response.text()}")

                result = await response.json()
                orders = result.get("data", [])

                return [self._parse_order(order) for order in orders]

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get all orders error: {str(e)}")
            raise

    async def get_positions(self) -> List[Position]:
        """Get open positions"""
        if not self.connected:
            raise ZerodhaException("Not connected to broker")

        try:
            async with self.session.get(
                f"{self.BASE_URL}/portfolio/positions",
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise ZerodhaException(f"Failed to fetch positions: {await response.text()}")

                result = await response.json()
                positions_data = result.get("data", {})

                positions = []
                for position in positions_data.get("net", []):
                    positions.append(
                        Position(
                            symbol=position.get("tradingsymbol"),
                            quantity=position.get("quantity", 0),
                            average_price=position.get("average_price", 0),
                            current_price=position.get("last_price", 0),
                            pnl=position.get("pnl", 0),
                            pnl_percent=position.get("pnl_percent", 0),
                        )
                    )

                return positions

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get positions error: {str(e)}")
            raise

    async def get_account_details(self) -> Account:
        """Get account details"""
        if not self.connected:
            raise ZerodhaException("Not connected to broker")

        try:
            async with self.session.get(
                f"{self.BASE_URL}/user/profile",
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise ZerodhaException(f"Failed to fetch account details: {await response.text()}")

                result = await response.json()
                account_data = result.get("data", {})

                return Account(
                    balance=account_data.get("equity", {}).get("net", 0),
                    used_margin=account_data.get("equity", {}).get("used", 0),
                    available_margin=account_data.get("equity", {}).get("available", 0),
                    multiplier=account_data.get("equity", {}).get("multiplier", 1),
                )

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get account details error: {str(e)}")
            raise

    async def get_holding(self) -> List[Dict[str, Any]]:
        """Get holdings"""
        if not self.connected:
            raise ZerodhaException("Not connected to broker")

        try:
            async with self.session.get(
                f"{self.BASE_URL}/portfolio/holdings",
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise ZerodhaException(f"Failed to fetch holdings: {await response.text()}")

                result = await response.json()
                return result.get("data", [])

        except Exception as e:
            logger.error(f"[{self.broker_name}] Get holdings error: {str(e)}")
            raise

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get live quote"""
        if not self.connected:
            raise ZerodhaException("Not connected to broker")

        try:
            exchange = self._get_exchange(symbol)
            params = {"mode": "LTP", "i": f"{exchange}:{symbol}"}

            async with self.session.get(
                f"{self.MARKET_URL}/quote",
                params=params,
                headers=self._get_headers(),
            ) as response:
                if response.status != 200:
                    raise ZerodhaException(f"Failed to fetch quote: {await response.text()}")

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
            "Authorization": f"Bearer {self.api_key} {self.access_token}",
            "X-Kite-Version": "3",
        }

    def _get_exchange(self, symbol: str) -> str:
        """Determine exchange from symbol"""
        # Simplified logic - in production, use actual instrument mapping
        if symbol.startswith("NIFTY") or symbol.startswith("BANKNIFTY"):
            return "NFO"
        return "NSE"

    def _map_order_type(self, order_type: OrderType) -> str:
        """Map OrderType enum to Zerodha order type"""
        mapping = {
            OrderType.MARKET: "MKT",
            OrderType.LIMIT: "LIMIT",
            OrderType.STOP_LOSS: "SL",
            OrderType.STOP_LOSS_LIMIT: "SL-M",
        }
        return mapping.get(order_type, "MKT")

    def _parse_order(self, order_data: Dict) -> OrderResponse:
        """Parse Zerodha order response to OrderResponse"""
        return OrderResponse(
            order_id=order_data.get("order_id"),
            symbol=order_data.get("tradingsymbol"),
            side=OrderSide[order_data.get("transaction_type", "BUY").upper()],
            quantity=order_data.get("quantity", 0),
            filled_quantity=order_data.get("filled_quantity", 0),
            price=order_data.get("price", 0),
            filled_price=order_data.get("average_price"),
            order_type=OrderType[order_data.get("order_type", "MARKET").upper()],
            status=self._parse_order_status(order_data.get("status")),
            timestamp=order_data.get("order_timestamp", datetime.now().isoformat()),
            message=order_data.get("status_message"),
        )

    def _parse_order_status(self, status: str) -> OrderStatus:
        """Map Zerodha status to OrderStatus"""
        mapping = {
            "PENDING": OrderStatus.PENDING,
            "OPEN": OrderStatus.OPEN,
            "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED,
            "FILLED": OrderStatus.FILLED,
            "CANCELLED": OrderStatus.CANCELLED,
            "REJECTED": OrderStatus.REJECTED,
            "EXPIRED": OrderStatus.EXPIRED,
        }
        return mapping.get(status, OrderStatus.PENDING)
