"""
Accounts Window for PROGAIN 5.1
Super window for viewing account details and transactions.
"""

import csv
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QListWidget,
    QListWidgetItem, QFrame, QFileDialog, QMessageBox, QSplitter,
    QLineEdit, QMenu, QAction, QAbstractItemView, QComboBox
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from progain4.services.firebase_client import firebase_client

logger = logging.getLogger(__name__)

# Month names
MONTHS = [
    "Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]


class AccountsWindow(QMainWindow):
    """
    Super window for viewing accounts and their transactions.
    Provides detailed view of all account transactions including transfers.
    """
    
    # Signals
    edit_transaction_requested = pyqtSignal(dict)
    view_attachments_requested = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_id: Optional[str] = None
        self._project_name: str = ""
        self._selected_account_id: Optional[str] = None
        self._selected_account_name: str = ""
        
        # Data
        self._accounts: List[Dict[str, Any]] = []
        self._all_transactions: List[Dict[str, Any]] = []
        self._filtered_transactions: List[Dict[str, Any]] = []
        self._categories_map: Dict[str, str] = {}
        self._accounts_map: Dict[str, str] = {}
        
        self._setup_ui()
        logger.info("AccountsWindow initialized")
    
    def _setup_ui(self):
        """Set up the window UI."""
        self.setWindowTitle("Cuentas")
        self.setMinimumSize(1000, 700)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - accounts list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(8, 8, 8, 8)
        
        # Project label
        self._project_label = QLabel("Proyecto: -")
        self._project_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        left_layout.addWidget(self._project_label)
        
        # Accounts header
        accounts_header = QLabel("Cuentas")
        accounts_header.setFont(QFont("Segoe UI", 11, QFont.Bold))
        left_layout.addWidget(accounts_header)
        
        # Accounts list
        self._accounts_list = QListWidget()
        self._accounts_list.itemClicked.connect(self._on_account_selected)
        left_layout.addWidget(self._accounts_list, 1)
        
        # Total balance
        self._total_balance_label = QLabel("Balance Total: $0.00")
        self._total_balance_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        left_layout.addWidget(self._total_balance_label)
        
        left_panel.setMaximumWidth(280)
        left_panel.setMinimumWidth(200)
        splitter.addWidget(left_panel)
        
        # Right panel - transactions
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 8, 8, 8)
        
        # Header
        header_layout = QHBoxLayout()
        
        self._account_title = QLabel("Seleccione una cuenta")
        self._account_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        header_layout.addWidget(self._account_title)
        
        self._account_balance = QLabel("")
        self._account_balance.setFont(QFont("Segoe UI", 12))
        self._account_balance.setStyleSheet("color: gray;")
        header_layout.addWidget(self._account_balance)
        
        header_layout.addStretch()
        right_layout.addLayout(header_layout)
        
        # Filter bar
        filter_frame = QFrame()
        filter_frame.setFrameStyle(QFrame.StyledPanel)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(8, 8, 8, 8)
        
        # Month filter
        filter_layout.addWidget(QLabel("Mes:"))
        self._month_combo = QComboBox()
        self._month_combo.addItems(MONTHS)
        self._month_combo.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self._month_combo)
        
        # Year filter
        filter_layout.addWidget(QLabel("Año:"))
        self._year_combo = QComboBox()
        self._year_combo.addItem("Todos")
        self._year_combo.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self._year_combo)
        
        # Search
        filter_layout.addWidget(QLabel("Buscar:"))
        self._search_field = QLineEdit()
        self._search_field.setPlaceholderText("Buscar en descripción o nota...")
        self._search_field.textChanged.connect(self._apply_filters)
        filter_layout.addWidget(self._search_field, 1)
        
        # Clear button
        self._clear_btn = QPushButton("Limpiar")
        self._clear_btn.clicked.connect(self._clear_filters)
        filter_layout.addWidget(self._clear_btn)
        
        right_layout.addWidget(filter_frame)
        
        # Results label
        self._results_label = QLabel("0 transacciones")
        self._results_label.setStyleSheet("color: gray;")
        right_layout.addWidget(self._results_label)
        
        # Transactions table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "Fecha", "Descripción", "Tipo", "Detalle", "Monto", "Adjuntos"
        ])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSortingEnabled(True)
        
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        # Context menu
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        
        # Double click
        self._table.doubleClicked.connect(self._on_double_click)
        
        right_layout.addWidget(self._table, 1)
        
        # Export buttons
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        
        self._export_csv_btn = QPushButton("Exportar CSV")
        self._export_csv_btn.clicked.connect(self._export_csv)
        export_layout.addWidget(self._export_csv_btn)
        
        right_layout.addLayout(export_layout)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 750])
        
        layout.addWidget(splitter)
    
    def set_project(self, project_id: str, project_name: str):
        """
        Set the project context.
        
        Args:
            project_id: Project ID
            project_name: Project name
        """
        self._project_id = project_id
        self._project_name = project_name
        self._project_label.setText(f"Proyecto: {project_name}")
        self.setWindowTitle(f"Cuentas - {project_name}")
        
        # Load accounts and categories
        self._load_accounts()
        self._load_categories()
        
        logger.info(f"AccountsWindow project set: {project_name} ({project_id})")
    
    def _load_accounts(self):
        """Load accounts for the current project."""
        if not self._project_id:
            return
        
        self._accounts = firebase_client.get_cuentas_by_proyecto(self._project_id)
        self._accounts_map = {acc.get('id', ''): acc.get('nombre', '') for acc in self._accounts}
        
        # Populate list
        self._accounts_list.clear()
        total_balance = 0
        
        for acc in self._accounts:
            item = QListWidgetItem()
            nombre = acc.get('nombre', 'Sin nombre')
            saldo = acc.get('saldo', 0)
            tipo = acc.get('tipo', '')
            
            item.setText(f"{nombre}\n{tipo} • ${saldo:,.2f}")
            item.setData(Qt.UserRole, acc.get('id', ''))
            item.setData(Qt.UserRole + 1, nombre)
            item.setData(Qt.UserRole + 2, saldo)
            
            if saldo < 0:
                item.setForeground(QColor("#F44336"))
            elif saldo > 0:
                item.setForeground(QColor("#4CAF50"))
            
            self._accounts_list.addItem(item)
            total_balance += saldo
        
        # Update total
        if total_balance >= 0:
            self._total_balance_label.setText(f"Balance Total: ${total_balance:,.2f}")
            self._total_balance_label.setStyleSheet("color: #4CAF50;")
        else:
            self._total_balance_label.setText(f"Balance Total: -${abs(total_balance):,.2f}")
            self._total_balance_label.setStyleSheet("color: #F44336;")
    
    def _load_categories(self):
        """Load categories for display."""
        if not self._project_id:
            return
        
        categories = firebase_client.get_categorias_by_proyecto(self._project_id)
        self._categories_map = {cat.get('id', ''): cat.get('nombre', '') for cat in categories}
    
    def select_account(self, cuenta_id: str):
        """
        Select and display a specific account.
        
        Args:
            cuenta_id: Account ID to select
        """
        # Find and select in list
        for i in range(self._accounts_list.count()):
            item = self._accounts_list.item(i)
            if item.data(Qt.UserRole) == cuenta_id:
                self._accounts_list.setCurrentItem(item)
                self._on_account_selected(item)
                break
    
    def _on_account_selected(self, item: QListWidgetItem):
        """Handle account selection."""
        self._selected_account_id = item.data(Qt.UserRole)
        self._selected_account_name = item.data(Qt.UserRole + 1)
        saldo = item.data(Qt.UserRole + 2)
        
        self._account_title.setText(self._selected_account_name)
        
        if saldo >= 0:
            self._account_balance.setText(f"Saldo: ${saldo:,.2f}")
            self._account_balance.setStyleSheet("color: #4CAF50;")
        else:
            self._account_balance.setText(f"Saldo: -${abs(saldo):,.2f}")
            self._account_balance.setStyleSheet("color: #F44336;")
        
        self._load_transactions()
    
    def _load_transactions(self):
        """Load transactions for the selected account."""
        if not self._project_id or not self._selected_account_id:
            return
        
        self._all_transactions = firebase_client.get_transacciones_by_cuenta(
            self._project_id, self._selected_account_id
        )
        
        # Update year filter
        years = set()
        for tx in self._all_transactions:
            fecha = tx.get('fecha')
            if isinstance(fecha, datetime):
                years.add(fecha.year)
        
        self._year_combo.blockSignals(True)
        current = self._year_combo.currentText()
        self._year_combo.clear()
        self._year_combo.addItem("Todos")
        for year in sorted(years, reverse=True):
            self._year_combo.addItem(str(year))
        idx = self._year_combo.findText(current)
        if idx >= 0:
            self._year_combo.setCurrentIndex(idx)
        self._year_combo.blockSignals(False)
        
        self._apply_filters()
    
    def _apply_filters(self):
        """Apply filters and refresh the table."""
        filtered = self._all_transactions.copy()
        
        # Month filter
        month_idx = self._month_combo.currentIndex()
        if month_idx > 0:
            filtered = [
                tx for tx in filtered
                if self._get_tx_month(tx) == month_idx
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
        search = self._search_field.text().strip().lower()
        if search:
            filtered = [
                tx for tx in filtered
                if search in tx.get('descripcion', '').lower() or
                   search in tx.get('nota', '').lower()
            ]
        
        self._filtered_transactions = filtered
        self._refresh_table()
    
    def _get_tx_month(self, tx: Dict) -> int:
        """Get month from transaction."""
        fecha = tx.get('fecha')
        if isinstance(fecha, datetime):
            return fecha.month
        return 0
    
    def _get_tx_year(self, tx: Dict) -> int:
        """Get year from transaction."""
        fecha = tx.get('fecha')
        if isinstance(fecha, datetime):
            return fecha.year
        return 0
    
    def _clear_filters(self):
        """Clear all filters."""
        self._month_combo.setCurrentIndex(0)
        self._year_combo.setCurrentIndex(0)
        self._search_field.clear()
    
    def _refresh_table(self):
        """Refresh the transactions table."""
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)
        
        for tx in self._filtered_transactions:
            row = self._table.rowCount()
            self._table.insertRow(row)
            
            # Fecha
            fecha = tx.get('fecha')
            if isinstance(fecha, datetime):
                fecha_str = fecha.strftime("%d/%m/%Y")
            else:
                fecha_str = str(fecha) if fecha else ""
            fecha_item = QTableWidgetItem(fecha_str)
            fecha_item.setData(Qt.UserRole, tx)
            self._table.setItem(row, 0, fecha_item)
            
            # Descripción
            self._table.setItem(row, 1, QTableWidgetItem(tx.get('descripcion', '')))
            
            # Tipo
            tipo = tx.get('tipo', '')
            tipo_item = QTableWidgetItem(tipo)
            if tipo.startswith('Transferencia'):
                tipo_item.setForeground(QColor("#1976D2"))  # Blue
            self._table.setItem(row, 2, tipo_item)
            
            # Detalle (for transfers show linked account)
            detalle = ""
            if tipo == "Transferencia Salida":
                dest_id = tx.get('cuenta_destino_id', '')
                dest_nombre = self._accounts_map.get(dest_id, dest_id)
                detalle = f"→ {dest_nombre}"
            elif tipo == "Transferencia Entrada":
                orig_id = tx.get('cuenta_origen_id', '')
                orig_nombre = self._accounts_map.get(orig_id, orig_id)
                detalle = f"← {orig_nombre}"
            else:
                cat_id = tx.get('categoria_id', '')
                detalle = self._categories_map.get(cat_id, '')
            
            self._table.setItem(row, 3, QTableWidgetItem(detalle))
            
            # Monto
            monto = tx.get('monto', 0)
            if monto >= 0:
                monto_str = f"${monto:,.2f}"
                monto_item = QTableWidgetItem(monto_str)
                monto_item.setForeground(QColor("#4CAF50"))
            else:
                monto_str = f"-${abs(monto):,.2f}"
                monto_item = QTableWidgetItem(monto_str)
                monto_item.setForeground(QColor("#F44336"))
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
        
        total = len(self._all_transactions)
        shown = len(self._filtered_transactions)
        if shown == total:
            self._results_label.setText(f"{total} transacciones")
        else:
            self._results_label.setText(f"Mostrando {shown} de {total} transacciones")
    
    def _get_selected_transaction(self) -> Optional[Dict]:
        """Get the currently selected transaction."""
        row = self._table.currentRow()
        if row >= 0:
            item = self._table.item(row, 0)
            if item:
                return item.data(Qt.UserRole)
        return None
    
    def _on_double_click(self, index):
        """Handle double click on a row."""
        tx = self._get_selected_transaction()
        if tx:
            logger.debug(f"Transaction double-clicked: {tx.get('id')}")
            self.edit_transaction_requested.emit(tx)
    
    def _show_context_menu(self, position):
        """Show context menu."""
        tx = self._get_selected_transaction()
        if not tx:
            return
        
        menu = QMenu(self)
        
        edit_action = QAction("Editar transacción...", self)
        edit_action.triggered.connect(lambda: self.edit_transaction_requested.emit(tx))
        menu.addAction(edit_action)
        
        adjuntos = tx.get('adjuntos', [])
        if adjuntos:
            attachments_action = QAction(f"Ver adjuntos ({len(adjuntos)})", self)
            attachments_action.triggered.connect(lambda: self.view_attachments_requested.emit(tx))
            menu.addAction(attachments_action)
        
        menu.exec_(self._table.mapToGlobal(position))
    
    def _export_csv(self):
        """Export transactions to CSV."""
        if not self._filtered_transactions:
            QMessageBox.information(self, "Exportar", "No hay transacciones para exportar.")
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar como CSV",
            f"cuenta_{self._selected_account_name or 'transacciones'}_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV (*.csv)"
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Fecha", "Descripción", "Tipo", "Detalle", "Monto"])
                
                for tx in self._filtered_transactions:
                    fecha = tx.get('fecha')
                    if isinstance(fecha, datetime):
                        fecha_str = fecha.strftime("%Y-%m-%d")
                    else:
                        fecha_str = str(fecha) if fecha else ""
                    
                    tipo = tx.get('tipo', '')
                    detalle = ""
                    if tipo == "Transferencia Salida":
                        dest_id = tx.get('cuenta_destino_id', '')
                        detalle = f"A: {self._accounts_map.get(dest_id, dest_id)}"
                    elif tipo == "Transferencia Entrada":
                        orig_id = tx.get('cuenta_origen_id', '')
                        detalle = f"De: {self._accounts_map.get(orig_id, orig_id)}"
                    else:
                        cat_id = tx.get('categoria_id', '')
                        detalle = self._categories_map.get(cat_id, '')
                    
                    writer.writerow([
                        fecha_str,
                        tx.get('descripcion', ''),
                        tipo,
                        detalle,
                        tx.get('monto', 0)
                    ])
            
            QMessageBox.information(
                self, "Exportar",
                f"Datos exportados exitosamente a:\n{filepath}"
            )
            logger.info(f"Account transactions exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            QMessageBox.critical(self, "Error", f"Error al exportar:\n{str(e)}")
    
    def refresh(self):
        """Refresh all data."""
        if self._project_id:
            self._load_accounts()
            self._load_categories()
            if self._selected_account_id:
                self._load_transactions()
