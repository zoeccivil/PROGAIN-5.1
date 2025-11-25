"""
Transfer Dialog for PROGAIN 5.1
Dialog for creating transfers between accounts.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QDateEdit, QDoubleSpinBox, QTextEdit, QPushButton, QFormLayout,
    QFrame, QDialogButtonBox, QMessageBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class TransferDialog(QDialog):
    """
    Dialog for creating transfers between accounts.
    Creates two linked transactions (one outgoing, one incoming).
    """
    
    def __init__(self, parent=None, accounts: List[Dict[str, Any]] = None):
        """
        Initialize the transfer dialog.
        
        Args:
            parent: Parent widget
            accounts: List of accounts for the current project
        """
        super().__init__(parent)
        self._accounts = accounts or []
        
        self.setWindowTitle("Nueva Transferencia")
        self.setMinimumWidth(450)
        
        self._setup_ui()
        self._populate_accounts()
        
        logger.info("TransferDialog opened")
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("Transferencia entre cuentas")
        header.setFont(QFont("Segoe UI", 12, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Info label
        info = QLabel("Esta operación creará dos transacciones vinculadas:\nuna salida en cuenta origen y una entrada en cuenta destino.")
        info.setStyleSheet("color: gray;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Date
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Fecha:", self._date_edit)
        
        # Source account
        self._source_combo = QComboBox()
        self._source_combo.currentIndexChanged.connect(self._on_account_changed)
        form_layout.addRow("Cuenta origen:", self._source_combo)
        
        # Arrow indicator
        arrow_layout = QHBoxLayout()
        arrow_layout.addStretch()
        arrow_label = QLabel("⬇️  Transferir a  ⬇️")
        arrow_label.setStyleSheet("color: #1976D2; font-weight: bold;")
        arrow_layout.addWidget(arrow_label)
        arrow_layout.addStretch()
        form_layout.addRow("", arrow_layout)
        
        # Destination account
        self._dest_combo = QComboBox()
        self._dest_combo.currentIndexChanged.connect(self._on_account_changed)
        form_layout.addRow("Cuenta destino:", self._dest_combo)
        
        # Amount
        self._amount_spin = QDoubleSpinBox()
        self._amount_spin.setRange(0.01, 999999999.99)
        self._amount_spin.setDecimals(2)
        self._amount_spin.setPrefix("$ ")
        self._amount_spin.setSingleStep(100)
        self._amount_spin.setValue(100.00)
        form_layout.addRow("Monto:", self._amount_spin)
        
        # Note
        self._note_edit = QLineEdit()
        self._note_edit.setPlaceholderText("Nota o descripción (opcional)")
        form_layout.addRow("Nota:", self._note_edit)
        
        layout.addLayout(form_layout)
        
        # Validation message
        self._validation_label = QLabel("")
        self._validation_label.setStyleSheet("color: #F44336;")
        self._validation_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._validation_label)
        
        layout.addStretch()
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator2)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        
        # Rename OK button
        ok_btn = button_box.button(QDialogButtonBox.Ok)
        ok_btn.setText("Transferir")
        
        layout.addWidget(button_box)
    
    def _populate_accounts(self):
        """Populate account combo boxes."""
        self._source_combo.clear()
        self._dest_combo.clear()
        
        for acc in self._accounts:
            nombre = acc.get('nombre', 'Sin nombre')
            saldo = acc.get('saldo', 0)
            display = f"{nombre} (${saldo:,.2f})"
            
            self._source_combo.addItem(display, acc.get('id', ''))
            self._dest_combo.addItem(display, acc.get('id', ''))
        
        # Select different accounts by default if possible
        if len(self._accounts) > 1:
            self._dest_combo.setCurrentIndex(1)
    
    def _on_account_changed(self):
        """Handle account selection changes."""
        source_id = self._source_combo.currentData()
        dest_id = self._dest_combo.currentData()
        
        if source_id and dest_id and source_id == dest_id:
            self._validation_label.setText("⚠️ La cuenta origen y destino no pueden ser iguales")
        else:
            self._validation_label.setText("")
    
    def _get_account_name(self, index: int) -> str:
        """Get the account name for a given index."""
        if 0 <= index < len(self._accounts):
            return self._accounts[index].get('nombre', '')
        return ''
    
    def _on_accept(self):
        """Validate and accept the dialog."""
        source_id = self._source_combo.currentData()
        dest_id = self._dest_combo.currentData()
        
        # Validate source != destination
        if source_id == dest_id:
            QMessageBox.warning(
                self, "Validación",
                "La cuenta origen y destino deben ser diferentes."
            )
            return
        
        # Validate amount
        if self._amount_spin.value() <= 0:
            QMessageBox.warning(
                self, "Validación",
                "El monto debe ser mayor a cero."
            )
            self._amount_spin.setFocus()
            return
        
        # Validate accounts exist
        if not source_id or not dest_id:
            QMessageBox.warning(
                self, "Validación",
                "Debe seleccionar ambas cuentas."
            )
            return
        
        self.accept()
    
    def get_transfer_data(self) -> Dict[str, Any]:
        """
        Get the transfer data from the form.
        
        Returns:
            Dictionary with transfer data including:
            - fecha: datetime
            - cuenta_origen_id: str
            - cuenta_destino_id: str
            - monto: float (positive)
            - nota: str
        """
        qdate = self._date_edit.date()
        fecha = datetime(qdate.year(), qdate.month(), qdate.day())
        
        # Get account names for display
        source_nombre = self._get_account_name(self._source_combo.currentIndex())
        dest_nombre = self._get_account_name(self._dest_combo.currentIndex())
        
        return {
            "fecha": fecha,
            "cuenta_origen_id": self._source_combo.currentData(),
            "cuenta_origen_nombre": source_nombre,
            "cuenta_destino_id": self._dest_combo.currentData(),
            "cuenta_destino_nombre": dest_nombre,
            "monto": abs(self._amount_spin.value()),
            "nota": self._note_edit.text().strip(),
        }
