"""
Sidebar Widget for PROGAIN 5.1
Displays project information and accounts list with navigation.
"""

import logging
from typing import Any, Dict, List, Optional, Callable

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QFrame, QHBoxLayout, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

logger = logging.getLogger(__name__)


class SidebarWidget(QWidget):
    """
    Sidebar widget showing project info and accounts list.
    Emits signals when accounts are clicked for navigation.
    """
    
    # Signals
    account_clicked = pyqtSignal(str, str)  # cuenta_id, cuenta_nombre
    account_double_clicked = pyqtSignal(str, str)  # cuenta_id, cuenta_nombre
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._proyecto_id: Optional[str] = None
        self._proyecto_nombre: str = ""
        self._cuentas: List[Dict[str, Any]] = []
        self._setup_ui()
        logger.info("SidebarWidget initialized")
    
    def _setup_ui(self):
        """Set up the sidebar UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        
        # Project info section
        self._project_frame = QFrame()
        self._project_frame.setFrameStyle(QFrame.StyledPanel)
        project_layout = QVBoxLayout(self._project_frame)
        
        self._project_label = QLabel("Proyecto:")
        self._project_label.setFont(QFont("Segoe UI", 9))
        self._project_label.setStyleSheet("color: gray;")
        
        self._project_name_label = QLabel("Sin proyecto seleccionado")
        self._project_name_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self._project_name_label.setWordWrap(True)
        
        project_layout.addWidget(self._project_label)
        project_layout.addWidget(self._project_name_label)
        
        layout.addWidget(self._project_frame)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Accounts section header
        accounts_header = QHBoxLayout()
        
        self._accounts_label = QLabel("Cuentas")
        self._accounts_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        
        self._accounts_count_label = QLabel("(0)")
        self._accounts_count_label.setStyleSheet("color: gray;")
        
        accounts_header.addWidget(self._accounts_label)
        accounts_header.addWidget(self._accounts_count_label)
        accounts_header.addStretch()
        
        layout.addLayout(accounts_header)
        
        # Accounts list
        self._accounts_list = QListWidget()
        self._accounts_list.setAlternatingRowColors(True)
        self._accounts_list.setSpacing(2)
        self._accounts_list.itemClicked.connect(self._on_account_clicked)
        self._accounts_list.itemDoubleClicked.connect(self._on_account_double_clicked)
        
        layout.addWidget(self._accounts_list, 1)  # Stretch to fill
        
        # Total balance
        self._balance_frame = QFrame()
        self._balance_frame.setFrameStyle(QFrame.StyledPanel)
        balance_layout = QVBoxLayout(self._balance_frame)
        
        self._balance_title_label = QLabel("Balance Total:")
        self._balance_title_label.setFont(QFont("Segoe UI", 9))
        self._balance_title_label.setStyleSheet("color: gray;")
        
        self._balance_value_label = QLabel("$0.00")
        self._balance_value_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self._balance_value_label.setAlignment(Qt.AlignRight)
        
        balance_layout.addWidget(self._balance_title_label)
        balance_layout.addWidget(self._balance_value_label)
        
        layout.addWidget(self._balance_frame)
        
        # Set minimum width
        self.setMinimumWidth(200)
        self.setMaximumWidth(300)
    
    def set_project(self, proyecto_id: str, proyecto_nombre: str):
        """
        Set the current project.
        
        Args:
            proyecto_id: Project ID
            proyecto_nombre: Project name
        """
        self._proyecto_id = proyecto_id
        self._proyecto_nombre = proyecto_nombre
        self._project_name_label.setText(proyecto_nombre or "Sin nombre")
        logger.info(f"Sidebar project set: {proyecto_nombre} ({proyecto_id})")
    
    def set_accounts(self, cuentas: List[Dict[str, Any]]):
        """
        Set the accounts list.
        
        Args:
            cuentas: List of account dictionaries with 'id', 'nombre', 'saldo', 'tipo' fields
        """
        self._cuentas = cuentas
        self._accounts_list.clear()
        
        total_balance = 0.0
        
        for cuenta in cuentas:
            item = QListWidgetItem()
            cuenta_id = cuenta.get('id', '')
            nombre = cuenta.get('nombre', 'Sin nombre')
            saldo = cuenta.get('saldo', 0)
            tipo = cuenta.get('tipo', '')
            
            # Format display text
            saldo_str = f"${saldo:,.2f}"
            display_text = f"{nombre}\n{tipo} • {saldo_str}"
            
            item.setText(display_text)
            item.setData(Qt.UserRole, cuenta_id)
            item.setData(Qt.UserRole + 1, nombre)
            item.setData(Qt.UserRole + 2, saldo)
            
            # Set color based on balance
            if saldo < 0:
                item.setForeground(QColor("#F44336"))  # Red for negative
            elif saldo > 0:
                item.setForeground(QColor("#4CAF50"))  # Green for positive
            
            self._accounts_list.addItem(item)
            total_balance += saldo
        
        # Update counts and totals
        self._accounts_count_label.setText(f"({len(cuentas)})")
        
        # Format total balance
        if total_balance >= 0:
            self._balance_value_label.setText(f"${total_balance:,.2f}")
            self._balance_value_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self._balance_value_label.setText(f"-${abs(total_balance):,.2f}")
            self._balance_value_label.setStyleSheet("color: #F44336; font-weight: bold;")
        
        logger.debug(f"Loaded {len(cuentas)} accounts, total balance: {total_balance}")
    
    def _on_account_clicked(self, item: QListWidgetItem):
        """Handle single click on an account."""
        cuenta_id = item.data(Qt.UserRole)
        cuenta_nombre = item.data(Qt.UserRole + 1)
        logger.debug(f"Account clicked: {cuenta_nombre} ({cuenta_id})")
        self.account_clicked.emit(cuenta_id, cuenta_nombre)
    
    def _on_account_double_clicked(self, item: QListWidgetItem):
        """Handle double click on an account."""
        cuenta_id = item.data(Qt.UserRole)
        cuenta_nombre = item.data(Qt.UserRole + 1)
        logger.debug(f"Account double-clicked: {cuenta_nombre} ({cuenta_id})")
        self.account_double_clicked.emit(cuenta_id, cuenta_nombre)
    
    def clear(self):
        """Clear all sidebar data."""
        self._proyecto_id = None
        self._proyecto_nombre = ""
        self._cuentas = []
        self._project_name_label.setText("Sin proyecto seleccionado")
        self._accounts_list.clear()
        self._accounts_count_label.setText("(0)")
        self._balance_value_label.setText("$0.00")
        self._balance_value_label.setStyleSheet("")
    
    def get_selected_account_id(self) -> Optional[str]:
        """Get the currently selected account ID."""
        current = self._accounts_list.currentItem()
        if current:
            return current.data(Qt.UserRole)
        return None
