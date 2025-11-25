"""
Transactions Widget for PROGAIN 5.1
Displays transactions in a table with filtering and search capabilities.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QComboBox, QLineEdit, QHeaderView, QAbstractItemView, QMenu, QAction,
    QPushButton, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QIcon

logger = logging.getLogger(__name__)

# Month names in Spanish
MONTHS = [
    "Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]


class TransactionsWidget(QWidget):
    """
    Widget for displaying and filtering transactions.
    Supports month/year filtering and text search.
    """
    
    # Signals
    transaction_selected = pyqtSignal(dict)  # Emitted when a transaction is selected
    transaction_double_clicked = pyqtSignal(dict)  # For editing
    edit_transaction_requested = pyqtSignal(dict)  # From context menu
    view_attachments_requested = pyqtSignal(dict)  # From context menu
    delete_transaction_requested = pyqtSignal(dict)  # From context menu
    
    # Column definitions
    COLUMNS = ["Fecha", "Descripción", "Cuenta", "Categoría", "Monto", "Adjuntos"]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_transactions: List[Dict[str, Any]] = []
        self._filtered_transactions: List[Dict[str, Any]] = []
        self._accounts_map: Dict[str, str] = {}  # id -> nombre
        self._categories_map: Dict[str, str] = {}  # id -> nombre
        
        # Debounce timer for search
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._apply_filters)
        
        self._setup_ui()
        logger.info("TransactionsWidget initialized")
    
    def _setup_ui(self):
        """Set up the transactions UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Filter bar
        filter_frame = QFrame()
        filter_frame.setFrameStyle(QFrame.StyledPanel)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(8, 8, 8, 8)
        
        # Month filter
        filter_layout.addWidget(QLabel("Mes:"))
        self._month_combo = QComboBox()
        self._month_combo.addItems(MONTHS)
        self._month_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._month_combo)
        
        filter_layout.addSpacing(16)
        
        # Year filter
        filter_layout.addWidget(QLabel("Año:"))
        self._year_combo = QComboBox()
        self._year_combo.addItem("Todos")
        # Will be populated with detected years
        self._year_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._year_combo)
        
        filter_layout.addSpacing(16)
        
        # Search field
        filter_layout.addWidget(QLabel("Buscar:"))
        self._search_field = QLineEdit()
        self._search_field.setPlaceholderText("Buscar en descripción o nota...")
        self._search_field.setMinimumWidth(200)
        self._search_field.textChanged.connect(self._on_search_text_changed)
        filter_layout.addWidget(self._search_field, 1)
        
        # Clear filters button
        self._clear_btn = QPushButton("Limpiar")
        self._clear_btn.clicked.connect(self._clear_filters)
        filter_layout.addWidget(self._clear_btn)
        
        layout.addWidget(filter_frame)
        
        # Results info
        self._results_label = QLabel("0 transacciones")
        self._results_label.setStyleSheet("color: gray;")
        layout.addWidget(self._results_label)
        
        # Transactions table
        self._table = QTableWidget()
        self._table.setColumnCount(len(self.COLUMNS))
        self._table.setHorizontalHeaderLabels(self.COLUMNS)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSortingEnabled(True)
        
        # Column widths
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Fecha
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Descripción
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Cuenta
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Categoría
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Monto
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Adjuntos
        
        # Enable context menu
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        
        # Double click handler
        self._table.doubleClicked.connect(self._on_double_click)
        
        # Selection changed
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        
        layout.addWidget(self._table, 1)
    
    def set_lookup_data(self, accounts: List[Dict[str, Any]], categories: List[Dict[str, Any]]):
        """
        Set account and category lookup data for display.
        
        Args:
            accounts: List of account dicts with 'id' and 'nombre'
            categories: List of category dicts with 'id' and 'nombre'
        """
        self._accounts_map = {acc.get('id', ''): acc.get('nombre', '') for acc in accounts}
        self._categories_map = {cat.get('id', ''): cat.get('nombre', '') for cat in categories}
        logger.debug(f"Lookup data set: {len(accounts)} accounts, {len(categories)} categories")
    
    def set_transactions(self, transactions: List[Dict[str, Any]]):
        """
        Set the transactions to display.
        
        Args:
            transactions: List of transaction dictionaries
        """
        self._all_transactions = transactions
        
        # Update year filter with detected years
        years = set()
        for tx in transactions:
            fecha = tx.get('fecha')
            if fecha:
                if isinstance(fecha, str):
                    try:
                        fecha = datetime.fromisoformat(fecha)
                    except ValueError:
                        continue
                if isinstance(fecha, datetime):
                    years.add(fecha.year)
        
        # Populate year combo
        current_year = self._year_combo.currentText()
        self._year_combo.blockSignals(True)
        self._year_combo.clear()
        self._year_combo.addItem("Todos")
        for year in sorted(years, reverse=True):
            self._year_combo.addItem(str(year))
        
        # Restore selection if possible
        index = self._year_combo.findText(current_year)
        if index >= 0:
            self._year_combo.setCurrentIndex(index)
        self._year_combo.blockSignals(False)
        
        # Apply filters and refresh display
        self._apply_filters()
        logger.info(f"Set {len(transactions)} transactions")
    
    def _on_filter_changed(self):
        """Handle filter combo changes."""
        self._apply_filters()
    
    def _on_search_text_changed(self, text: str):
        """Handle search text changes with debounce."""
        # Debounce: wait 300ms after last keystroke
        self._search_timer.stop()
        self._search_timer.start(300)
    
    def _clear_filters(self):
        """Clear all filters."""
        self._month_combo.setCurrentIndex(0)  # "Todos"
        self._year_combo.setCurrentIndex(0)  # "Todos"
        self._search_field.clear()
        self._apply_filters()
    
    def _apply_filters(self):
        """Apply all filters and refresh the table."""
        filtered = self._all_transactions.copy()
        
        # Month filter
        month_index = self._month_combo.currentIndex()
        if month_index > 0:  # Not "Todos"
            filtered = [
                tx for tx in filtered
                if self._get_tx_month(tx) == month_index
            ]
        
        # Year filter
        year_text = self._year_combo.currentText()
        if year_text != "Todos":
            try:
                year = int(year_text)
                filtered = [
                    tx for tx in filtered
                    if self._get_tx_year(tx) == year
                ]
            except ValueError:
                pass
        
        # Text search
        search_text = self._search_field.text().strip().lower()
        if search_text:
            filtered = [
                tx for tx in filtered
                if search_text in tx.get('descripcion', '').lower() or
                   search_text in tx.get('nota', '').lower()
            ]
        
        self._filtered_transactions = filtered
        self._refresh_table()
    
    def _get_tx_month(self, tx: Dict[str, Any]) -> int:
        """Get the month (1-12) from a transaction."""
        fecha = tx.get('fecha')
        if fecha:
            if isinstance(fecha, str):
                try:
                    fecha = datetime.fromisoformat(fecha)
                except ValueError:
                    return 0
            if isinstance(fecha, datetime):
                return fecha.month
        return 0
    
    def _get_tx_year(self, tx: Dict[str, Any]) -> int:
        """Get the year from a transaction."""
        fecha = tx.get('fecha')
        if fecha:
            if isinstance(fecha, str):
                try:
                    fecha = datetime.fromisoformat(fecha)
                except ValueError:
                    return 0
            if isinstance(fecha, datetime):
                return fecha.year
        return 0
    
    def _refresh_table(self):
        """Refresh the table with filtered transactions."""
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)
        
        for tx in self._filtered_transactions:
            row = self._table.rowCount()
            self._table.insertRow(row)
            
            # Store transaction data in first cell
            
            # Fecha
            fecha = tx.get('fecha')
            if isinstance(fecha, datetime):
                fecha_str = fecha.strftime("%d/%m/%Y")
            elif isinstance(fecha, str):
                fecha_str = fecha
            else:
                fecha_str = ""
            fecha_item = QTableWidgetItem(fecha_str)
            fecha_item.setData(Qt.UserRole, tx)  # Store full transaction
            self._table.setItem(row, 0, fecha_item)
            
            # Descripción
            desc = tx.get('descripcion', '')
            desc_item = QTableWidgetItem(desc)
            self._table.setItem(row, 1, desc_item)
            
            # Cuenta
            cuenta_id = tx.get('cuenta_id', '')
            cuenta_nombre = self._accounts_map.get(cuenta_id, cuenta_id)
            cuenta_item = QTableWidgetItem(cuenta_nombre)
            self._table.setItem(row, 2, cuenta_item)
            
            # Categoría
            cat_id = tx.get('categoria_id', '')
            cat_nombre = self._categories_map.get(cat_id, cat_id)
            cat_item = QTableWidgetItem(cat_nombre)
            self._table.setItem(row, 3, cat_item)
            
            # Monto
            monto = tx.get('monto', 0)
            if monto >= 0:
                monto_str = f"${monto:,.2f}"
                monto_item = QTableWidgetItem(monto_str)
                monto_item.setForeground(QColor("#4CAF50"))  # Green
            else:
                monto_str = f"-${abs(monto):,.2f}"
                monto_item = QTableWidgetItem(monto_str)
                monto_item.setForeground(QColor("#F44336"))  # Red
            monto_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._table.setItem(row, 4, monto_item)
            
            # Adjuntos
            adjuntos = tx.get('adjuntos', [])
            if adjuntos:
                adj_item = QTableWidgetItem(f"📎 ({len(adjuntos)})")
                adj_item.setTextAlignment(Qt.AlignCenter)
            else:
                adj_item = QTableWidgetItem("")
            self._table.setItem(row, 5, adj_item)
        
        self._table.setSortingEnabled(True)
        
        # Update results label
        total = len(self._all_transactions)
        filtered = len(self._filtered_transactions)
        if filtered == total:
            self._results_label.setText(f"{total} transacciones")
        else:
            self._results_label.setText(f"Mostrando {filtered} de {total} transacciones")
    
    def _get_selected_transaction(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected transaction."""
        current_row = self._table.currentRow()
        if current_row >= 0:
            item = self._table.item(current_row, 0)
            if item:
                return item.data(Qt.UserRole)
        return None
    
    def _on_selection_changed(self):
        """Handle selection changes."""
        tx = self._get_selected_transaction()
        if tx:
            self.transaction_selected.emit(tx)
    
    def _on_double_click(self, index):
        """Handle double click on a row."""
        tx = self._get_selected_transaction()
        if tx:
            logger.debug(f"Transaction double-clicked: {tx.get('id')}")
            self.transaction_double_clicked.emit(tx)
    
    def _show_context_menu(self, position):
        """Show context menu for the table."""
        tx = self._get_selected_transaction()
        if not tx:
            return
        
        menu = QMenu(self)
        
        # Edit action
        edit_action = QAction("Editar transacción...", self)
        edit_action.triggered.connect(lambda: self.edit_transaction_requested.emit(tx))
        menu.addAction(edit_action)
        
        # View attachments (if any)
        adjuntos = tx.get('adjuntos', [])
        if adjuntos:
            attachments_action = QAction(f"Ver adjuntos ({len(adjuntos)})", self)
            attachments_action.triggered.connect(lambda: self.view_attachments_requested.emit(tx))
            menu.addAction(attachments_action)
        
        menu.addSeparator()
        
        # Delete action
        delete_action = QAction("Eliminar transacción", self)
        delete_action.triggered.connect(lambda: self.delete_transaction_requested.emit(tx))
        menu.addAction(delete_action)
        
        menu.exec_(self._table.mapToGlobal(position))
    
    def clear(self):
        """Clear all transactions and filters."""
        self._all_transactions = []
        self._filtered_transactions = []
        self._table.setRowCount(0)
        self._month_combo.setCurrentIndex(0)
        self._year_combo.clear()
        self._year_combo.addItem("Todos")
        self._search_field.clear()
        self._results_label.setText("0 transacciones")
    
    def refresh(self):
        """Refresh the current view."""
        self._apply_filters()
