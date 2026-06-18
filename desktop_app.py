"""
PyQt6 Desktop Application for Multi-Broker Trading
Zero-delay, production-ready trading interface
"""
import sys
import asyncio
import logging
from typing import Optional, Dict, List
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit,
    QSpinBox, QDoubleSpinBox, QComboBox, QLabel, QMessageBox, QStatusBar,
    QDialog, QFormLayout, QDialogButtonBox, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QBrush
from PyQt6.QtCharts import QChart, QChartView, QLineSeries
from PyQt6.QtCore import QPointF

from broker_interface.manager import BrokerManager
from broker_interface.base import OrderType, OrderSide, OrderStatus

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class OrderWorker(QThread):
    """Worker thread for async broker operations"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)

    def __init__(self, coro):
        super().__init__()
        self.coro = coro
        self.loop = None

    def run(self):
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            result = self.loop.run_until_complete(self.coro)
            self.result.emit(result)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            if self.loop:
                self.loop.close()
            self.finished.emit()


class BrokerConnectionDialog(QDialog):
    """Dialog for adding broker connections"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Broker Connection")
        self.setGeometry(100, 100, 600, 400)
        self.broker_type = None
        self.credentials = {}
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        # Broker selection
        self.broker_combo = QComboBox()
        self.broker_combo.addItems(["Zerodha", "Fyers", "Angel One", "Flattrade"])
        self.broker_combo.currentTextChanged.connect(self.on_broker_changed)
        layout.addRow("Broker:", self.broker_combo)

        # Broker alias
        self.alias_input = QLineEdit()
        self.alias_input.setPlaceholderText("e.g., zerodha1")
        layout.addRow("Broker Alias:", self.alias_input)

        # Dynamic credential fields
        self.credential_fields = {}

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                     QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

        self.setLayout(layout)
        self.on_broker_changed("Zerodha")

    def on_broker_changed(self, broker_name):
        """Update credential fields based on broker selection"""
        self.broker_type = broker_name
        
        # Clear previous fields
        for field in self.credential_fields.values():
            field.deleteLater()
        self.credential_fields.clear()

        layout = self.layout()

        # Add broker-specific fields
        if broker_name == "Zerodha":
            self.credential_fields["api_key"] = QLineEdit()
            self.credential_fields["api_key"].setPlaceholderText("API Key")
            layout.insertRow(2, "API Key:", self.credential_fields["api_key"])

            self.credential_fields["user_id"] = QLineEdit()
            self.credential_fields["user_id"].setPlaceholderText("User ID")
            layout.insertRow(3, "User ID:", self.credential_fields["user_id"])

            self.credential_fields["password"] = QLineEdit()
            self.credential_fields["password"].setPlaceholderText("Password")
            self.credential_fields["password"].setEchoMode(QLineEdit.EchoMode.Password)
            layout.insertRow(4, "Password:", self.credential_fields["password"])

            self.credential_fields["totp_secret"] = QLineEdit()
            self.credential_fields["totp_secret"].setPlaceholderText("TOTP Secret (optional)")
            layout.insertRow(5, "TOTP Secret:", self.credential_fields["totp_secret"])

        elif broker_name == "Fyers":
            self.credential_fields["access_token"] = QLineEdit()
            self.credential_fields["access_token"].setPlaceholderText("Access Token")
            layout.insertRow(2, "Access Token:", self.credential_fields["access_token"])

        elif broker_name == "Angel One":
            self.credential_fields["access_token"] = QLineEdit()
            self.credential_fields["access_token"].setPlaceholderText("Access Token")
            layout.insertRow(2, "Access Token:", self.credential_fields["access_token"])

            self.credential_fields["user_id"] = QLineEdit()
            self.credential_fields["user_id"].setPlaceholderText("User ID")
            layout.insertRow(3, "User ID:", self.credential_fields["user_id"])

        elif broker_name == "Flattrade":
            self.credential_fields["auth_token"] = QLineEdit()
            self.credential_fields["auth_token"].setPlaceholderText("Auth Token")
            layout.insertRow(2, "Auth Token:", self.credential_fields["auth_token"])

            self.credential_fields["user_id"] = QLineEdit()
            self.credential_fields["user_id"].setPlaceholderText("User ID")
            layout.insertRow(3, "User ID:", self.credential_fields["user_id"])

    def get_credentials(self):
        """Get entered credentials"""
        self.credentials = {
            "broker": self.broker_type,
            "alias": self.alias_input.text() or self.broker_type.lower(),
        }
        for field_name, field_widget in self.credential_fields.items():
            self.credentials[field_name] = field_widget.text()
        return self.credentials


class OrderPlacementWidget(QWidget):
    """Widget for placing orders"""

    order_placed = pyqtSignal(dict)

    def __init__(self, broker_manager: BrokerManager, parent=None):
        super().__init__(parent)
        self.broker_manager = broker_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Symbol input
        symbol_layout = QHBoxLayout()
        symbol_layout.addWidget(QLabel("Symbol:"))
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("e.g., RELIANCE, BANKNIFTY25JAN24C45000")
        symbol_layout.addWidget(self.symbol_input)
        layout.addLayout(symbol_layout)

        # Quantity input
        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel("Quantity:"))
        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(1)
        self.quantity_input.setValue(1)
        qty_layout.addWidget(self.quantity_input)
        layout.addLayout(qty_layout)

        # Price input
        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel("Price:"))
        self.price_input = QDoubleSpinBox()
        self.price_input.setMinimum(0)
        self.price_input.setValue(0)
        price_layout.addWidget(self.price_input)
        layout.addLayout(price_layout)

        # Order type
        order_type_layout = QHBoxLayout()
        order_type_layout.addWidget(QLabel("Order Type:"))
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItems(["MARKET", "LIMIT", "STOP_LOSS", "STOP_LOSS_LIMIT"])
        order_type_layout.addWidget(self.order_type_combo)
        layout.addLayout(order_type_layout)

        # Trigger price (for stop orders)
        trigger_layout = QHBoxLayout()
        trigger_layout.addWidget(QLabel("Trigger Price:"))
        self.trigger_price_input = QDoubleSpinBox()
        self.trigger_price_input.setMinimum(0)
        self.trigger_price_input.setValue(0)
        trigger_layout.addWidget(self.trigger_price_input)
        layout.addLayout(trigger_layout)

        # Broker selection
        broker_layout = QHBoxLayout()
        broker_layout.addWidget(QLabel("Broker:"))
        self.broker_combo = QComboBox()
        broker_layout.addWidget(self.broker_combo)
        layout.addLayout(broker_layout)

        # Order action buttons
        button_layout = QHBoxLayout()

        self.buy_button = QPushButton("BUY")
        self.buy_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.buy_button.clicked.connect(self.place_buy_order)
        button_layout.addWidget(self.buy_button)

        self.sell_button = QPushButton("SELL")
        self.sell_button.setStyleSheet("background-color: #f44336; color: white;")
        self.sell_button.clicked.connect(self.place_sell_order)
        button_layout.addWidget(self.sell_button)

        self.stoploss_button = QPushButton("STOPLOSS")
        self.stoploss_button.setStyleSheet("background-color: #FF9800; color: white;")
        self.stoploss_button.clicked.connect(self.place_stoploss_order)
        button_layout.addWidget(self.stoploss_button)

        self.target_button = QPushButton("TARGET")
        self.target_button.setStyleSheet("background-color: #2196F3; color: white;")
        self.target_button.clicked.connect(self.place_target_order)
        button_layout.addWidget(self.target_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.update_broker_list()

    def update_broker_list(self):
        """Update available brokers in combo"""
        self.broker_combo.clear()
        brokers = self.broker_manager.list_brokers()
        self.broker_combo.addItems(brokers.keys())

    def place_buy_order(self):
        """Place buy order"""
        self._place_order(OrderSide.BUY, OrderType.MARKET)

    def place_sell_order(self):
        """Place sell order"""
        self._place_order(OrderSide.SELL, OrderType.MARKET)

    def place_stoploss_order(self):
        """Place stop loss order"""
        order_type = OrderType.STOP_LOSS
        if self.price_input.value() > 0:
            order_type = OrderType.STOP_LOSS_LIMIT
        
        symbol = self.symbol_input.text()
        quantity = self.quantity_input.value()
        trigger_price = self.trigger_price_input.value()
        limit_price = self.price_input.value() if self.price_input.value() > 0 else None
        broker_alias = self.broker_combo.currentText()

        worker = OrderWorker(
            self.broker_manager.place_stoploss_order(
                symbol, quantity, trigger_price, limit_price,
                OrderSide.SELL, broker_alias
            )
        )
        worker.result.connect(self.on_order_success)
        worker.error.connect(self.on_order_error)
        worker.start()

    def place_target_order(self):
        """Place target order"""
        symbol = self.symbol_input.text()
        quantity = self.quantity_input.value()
        target_price = self.price_input.value()
        broker_alias = self.broker_combo.currentText()

        worker = OrderWorker(
            self.broker_manager.place_target_order(
                symbol, quantity, target_price, OrderSide.SELL, broker_alias
            )
        )
        worker.result.connect(self.on_order_success)
        worker.error.connect(self.on_order_error)
        worker.start()

    def _place_order(self, side: OrderSide, order_type: OrderType):
        """Internal method to place order"""
        symbol = self.symbol_input.text()
        quantity = self.quantity_input.value()
        price = self.price_input.value() if order_type == OrderType.LIMIT else None
        broker_alias = self.broker_combo.currentText()

        if side == OrderSide.BUY:
            coro = self.broker_manager.place_buy_order(
                symbol, quantity, price, order_type, broker_alias
            )
        else:
            coro = self.broker_manager.place_sell_order(
                symbol, quantity, price, order_type, broker_alias
            )

        worker = OrderWorker(coro)
        worker.result.connect(self.on_order_success)
        worker.error.connect(self.on_order_error)
        worker.start()

    def on_order_success(self, result):
        """Handle successful order"""
        if result:
            self.order_placed.emit({
                "order_id": result.order_id,
                "symbol": result.symbol,
                "status": "SUCCESS"
            })

    def on_order_error(self, error_msg):
        """Handle order error"""
        QMessageBox.critical(self, "Order Error", f"Failed to place order: {error_msg}")


class PositionsWidget(QWidget):
    """Widget displaying open positions"""

    def __init__(self, broker_manager: BrokerManager, parent=None):
        super().__init__(parent)
        self.broker_manager = broker_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Refresh button
        button_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh Positions")
        self.refresh_button.clicked.connect(self.refresh_positions)
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Positions table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Symbol", "Quantity", "Avg Price", "Current Price", "PnL", "PnL %", "Broker"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def refresh_positions(self):
        """Refresh positions from all brokers"""
        worker = OrderWorker(self.broker_manager.get_positions_all_brokers())
        worker.result.connect(self.on_positions_received)
        worker.error.connect(lambda e: QMessageBox.critical(self, "Error", f"Failed to fetch positions: {e}"))
        worker.start()

    def on_positions_received(self, positions_dict):
        """Display received positions"""
        self.table.setRowCount(0)
        row = 0

        for broker_alias, positions in positions_dict.items():
            for position in positions:
                self.table.insertRow(row)

                # Symbol
                self.table.setItem(row, 0, QTableWidgetItem(position.symbol))

                # Quantity
                qty_item = QTableWidgetItem(str(position.quantity))
                self.table.setItem(row, 1, qty_item)

                # Avg Price
                self.table.setItem(row, 2, QTableWidgetItem(f"₹{position.average_price:.2f}"))

                # Current Price
                self.table.setItem(row, 3, QTableWidgetItem(f"₹{position.current_price:.2f}"))

                # PnL
                pnl_item = QTableWidgetItem(f"₹{position.pnl:.2f}")
                pnl_color = QColor(0, 150, 0) if position.pnl >= 0 else QColor(255, 0, 0)
                pnl_item.setForeground(QBrush(pnl_color))
                self.table.setItem(row, 4, pnl_item)

                # PnL %
                pnl_percent_item = QTableWidgetItem(f"{position.pnl_percent:.2f}%")
                pnl_percent_item.setForeground(QBrush(pnl_color))
                self.table.setItem(row, 5, pnl_percent_item)

                # Broker
                self.table.setItem(row, 6, QTableWidgetItem(broker_alias))

                row += 1


class OrdersWidget(QWidget):
    """Widget displaying recent orders"""

    def __init__(self, broker_manager: BrokerManager, parent=None):
        super().__init__(parent)
        self.broker_manager = broker_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Refresh button
        button_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh Orders")
        self.refresh_button.clicked.connect(self.refresh_orders)
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Orders table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Order ID", "Symbol", "Side", "Quantity", "Filled", "Price", "Status", "Time", "Broker"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def refresh_orders(self):
        """Refresh orders from all brokers"""
        worker = OrderWorker(self.broker_manager.get_all_orders_all_brokers())
        worker.result.connect(self.on_orders_received)
        worker.error.connect(lambda e: QMessageBox.critical(self, "Error", f"Failed to fetch orders: {e}"))
        worker.start()

    def on_orders_received(self, orders_dict):
        """Display received orders"""
        self.table.setRowCount(0)
        row = 0

        for broker_alias, orders in orders_dict.items():
            for order in orders:
                self.table.insertRow(row)

                self.table.setItem(row, 0, QTableWidgetItem(order.order_id))
                self.table.setItem(row, 1, QTableWidgetItem(order.symbol))
                self.table.setItem(row, 2, QTableWidgetItem(order.side.value))
                self.table.setItem(row, 3, QTableWidgetItem(str(order.quantity)))
                self.table.setItem(row, 4, QTableWidgetItem(str(order.filled_quantity)))
                self.table.setItem(row, 5, QTableWidgetItem(f"₹{order.price:.2f}"))

                status_item = QTableWidgetItem(order.status.value)
                status_color = {
                    OrderStatus.FILLED: QColor(0, 150, 0),
                    OrderStatus.OPEN: QColor(255, 165, 0),
                    OrderStatus.CANCELLED: QColor(255, 0, 0),
                    OrderStatus.PENDING: QColor(0, 0, 255),
                }.get(order.status, QColor(0, 0, 0))
                status_item.setForeground(QBrush(status_color))
                self.table.setItem(row, 6, status_item)

                self.table.setItem(row, 7, QTableWidgetItem(order.timestamp))
                self.table.setItem(row, 8, QTableWidgetItem(broker_alias))

                row += 1


class TradingApplication(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Broker Trading Interface")
        self.setGeometry(100, 100, 1400, 900)
        self.setFont(QFont("Arial", 10))

        self.broker_manager = BrokerManager()
        self.init_ui()
        self.show()

    def init_ui(self):
        """Initialize UI"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        # Top section: Broker management
        broker_layout = QHBoxLayout()

        add_broker_btn = QPushButton("Add Broker")
        add_broker_btn.clicked.connect(self.add_broker)
        broker_layout.addWidget(add_broker_btn)

        self.broker_label = QLabel("No brokers connected")
        broker_layout.addWidget(self.broker_label)
        broker_layout.addStretch()

        main_layout.addLayout(broker_layout)

        # Tab widget
        self.tabs = QTabWidget()

        # Order placement tab
        self.order_widget = OrderPlacementWidget(self.broker_manager)
        self.order_widget.order_placed.connect(self.on_order_placed)
        self.tabs.addTab(self.order_widget, "Place Order")

        # Positions tab
        self.positions_widget = PositionsWidget(self.broker_manager)
        self.tabs.addTab(self.positions_widget, "Positions")

        # Orders tab
        self.orders_widget = OrdersWidget(self.broker_manager)
        self.tabs.addTab(self.orders_widget, "Orders")

        main_layout.addWidget(self.tabs)

        central_widget.setLayout(main_layout)

        # Status bar
        self.statusBar().showMessage("Ready")

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds

    def add_broker(self):
        """Add new broker connection"""
        dialog = BrokerConnectionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            credentials = dialog.get_credentials()
            self.connect_broker(credentials)

    def connect_broker(self, credentials):
        """Connect to broker with given credentials"""
        broker_type = credentials.get("broker")
        alias = credentials.get("alias", broker_type.lower())

        try:
            if broker_type == "Zerodha":
                worker = OrderWorker(
                    self.broker_manager.add_zerodha(
                        api_key=credentials.get("api_key"),
                        user_id=credentials.get("user_id"),
                        password=credentials.get("password"),
                        totp_secret=credentials.get("totp_secret"),
                        broker_alias=alias,
                    )
                )
            elif broker_type == "Fyers":
                worker = OrderWorker(
                    self.broker_manager.add_fyers(
                        access_token=credentials.get("access_token"),
                        broker_alias=alias,
                    )
                )
            elif broker_type == "Angel One":
                worker = OrderWorker(
                    self.broker_manager.add_angelone(
                        access_token=credentials.get("access_token"),
                        user_id=credentials.get("user_id"),
                        broker_alias=alias,
                    )
                )
            elif broker_type == "Flattrade":
                worker = OrderWorker(
                    self.broker_manager.add_flattrade(
                        auth_token=credentials.get("auth_token"),
                        user_id=credentials.get("user_id"),
                        broker_alias=alias,
                    )
                )

            worker.result.connect(lambda: self.on_broker_connected(alias))
            worker.error.connect(lambda e: self.on_broker_error(alias, e))
            worker.start()

        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect broker: {str(e)}")

    def on_broker_connected(self, alias):
        """Handle successful broker connection"""
        QMessageBox.information(self, "Success", f"Broker '{alias}' connected successfully")
        self.update_broker_display()
        self.order_widget.update_broker_list()
        self.statusBar().showMessage(f"Connected: {alias}")

    def on_broker_error(self, alias, error):
        """Handle broker connection error"""
        QMessageBox.critical(self, "Connection Error", f"Failed to connect '{alias}': {error}")

    def on_order_placed(self, order_info):
        """Handle order placement"""
        self.statusBar().showMessage(f"Order {order_info['order_id']} placed: {order_info['symbol']}")
        QMessageBox.information(
            self, "Order Placed",
            f"Order {order_info['order_id']} placed successfully for {order_info['symbol']}"
        )
        # Refresh orders
        self.orders_widget.refresh_orders()

    def update_broker_display(self):
        """Update broker display label"""
        brokers = self.broker_manager.list_brokers()
        if brokers:
            text = "Connected Brokers: " + ", ".join(f"{k} ({v})" for k, v in brokers.items())
            self.broker_label.setText(text)
        else:
            self.broker_label.setText("No brokers connected")

    def auto_refresh(self):
        """Auto-refresh data"""
        if self.tabs.currentIndex() == 1:  # Positions tab
            self.positions_widget.refresh_positions()
        elif self.tabs.currentIndex() == 2:  # Orders tab
            self.orders_widget.refresh_orders()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    window = TradingApplication()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
