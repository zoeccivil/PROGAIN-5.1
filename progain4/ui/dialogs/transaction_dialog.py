"""
Transaction Dialog for PROGAIN 5.1
Dialog for adding and editing transactions with attachment support.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QDateEdit, QDoubleSpinBox, QTextEdit, QPushButton, QListWidget,
    QListWidgetItem, QFileDialog, QMessageBox, QFormLayout, QFrame,
    QDialogButtonBox, QGroupBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class TransactionDialog(QDialog):
    """
    Dialog for creating and editing transactions.
    Supports attachments upload and management.
    """
    
    def __init__(self, parent=None, transaction: Optional[Dict[str, Any]] = None,
                 accounts: List[Dict[str, Any]] = None,
                 categories: List[Dict[str, Any]] = None,
                 subcategories: List[Dict[str, Any]] = None):
        """
        Initialize the transaction dialog.
        
        Args:
            parent: Parent widget
            transaction: Existing transaction to edit (None for new)
            accounts: List of accounts for the current project
            categories: List of categories for the current project
            subcategories: List of subcategories for the current project
        """
        super().__init__(parent)
        self._transaction = transaction or {}
        self._accounts = accounts or []
        self._categories = categories or []
        self._subcategories = subcategories or []
        self._pending_attachments: List[Tuple[str, bytes, str]] = []  # (filename, data, content_type)
        self._existing_attachments: List[Dict[str, str]] = transaction.get('adjuntos', []) if transaction else []
        
        self._is_edit = transaction is not None
        
        self._setup_ui()
        self._populate_data()
        
        if self._is_edit:
            self.setWindowTitle("Editar Transacción")
            self._load_transaction_data()
        else:
            self.setWindowTitle("Nueva Transacción")
        
        logger.info(f"TransactionDialog opened: {'edit' if self._is_edit else 'new'}")
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Main form
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        
        # Date
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Fecha:", self._date_edit)
        
        # Description
        self._description_edit = QLineEdit()
        self._description_edit.setPlaceholderText("Descripción de la transacción")
        form_layout.addRow("Descripción:", self._description_edit)
        
        # Account
        self._account_combo = QComboBox()
        form_layout.addRow("Cuenta:", self._account_combo)
        
        # Transaction type
        self._type_combo = QComboBox()
        self._type_combo.addItems(["Ingreso", "Gasto", "Transferencia Entrada", "Transferencia Salida"])
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        form_layout.addRow("Tipo:", self._type_combo)
        
        # Category
        self._category_combo = QComboBox()
        self._category_combo.currentIndexChanged.connect(self._on_category_changed)
        form_layout.addRow("Categoría:", self._category_combo)
        
        # Subcategory
        self._subcategory_combo = QComboBox()
        form_layout.addRow("Subcategoría:", self._subcategory_combo)
        
        # Amount
        self._amount_spin = QDoubleSpinBox()
        self._amount_spin.setRange(0, 999999999.99)
        self._amount_spin.setDecimals(2)
        self._amount_spin.setPrefix("$ ")
        self._amount_spin.setSingleStep(100)
        form_layout.addRow("Monto:", self._amount_spin)
        
        # Note
        self._note_edit = QTextEdit()
        self._note_edit.setPlaceholderText("Notas adicionales...")
        self._note_edit.setMaximumHeight(80)
        form_layout.addRow("Nota:", self._note_edit)
        
        layout.addLayout(form_layout)
        
        # Attachments section
        attachments_group = QGroupBox("Adjuntos")
        attachments_layout = QVBoxLayout(attachments_group)
        
        # Attachments list
        self._attachments_list = QListWidget()
        self._attachments_list.setMaximumHeight(100)
        attachments_layout.addWidget(self._attachments_list)
        
        # Attachment buttons
        attach_buttons = QHBoxLayout()
        
        self._add_attachment_btn = QPushButton("Agregar adjunto...")
        self._add_attachment_btn.clicked.connect(self._add_attachment)
        attach_buttons.addWidget(self._add_attachment_btn)
        
        self._remove_attachment_btn = QPushButton("Quitar")
        self._remove_attachment_btn.clicked.connect(self._remove_attachment)
        attach_buttons.addWidget(self._remove_attachment_btn)
        
        attach_buttons.addStretch()
        attachments_layout.addLayout(attach_buttons)
        
        layout.addWidget(attachments_group)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        
        # Rename OK button
        ok_btn = button_box.button(QDialogButtonBox.Ok)
        ok_btn.setText("Guardar")
        
        layout.addWidget(button_box)
    
    def _populate_data(self):
        """Populate combo boxes with data."""
        # Accounts
        self._account_combo.clear()
        for acc in self._accounts:
            self._account_combo.addItem(acc.get('nombre', ''), acc.get('id', ''))
        
        # Categories
        self._category_combo.clear()
        for cat in self._categories:
            self._category_combo.addItem(cat.get('nombre', ''), cat.get('id', ''))
        
        # Subcategories will be filtered by category
        self._update_subcategories()
        
        # Existing attachments
        self._refresh_attachments_list()
    
    def _on_category_changed(self, index: int):
        """Handle category change - update subcategories."""
        self._update_subcategories()
    
    def _update_subcategories(self):
        """Update subcategories based on selected category."""
        self._subcategory_combo.clear()
        
        selected_cat_id = self._category_combo.currentData()
        if not selected_cat_id:
            return
        
        for subcat in self._subcategories:
            if subcat.get('categoria_id') == selected_cat_id:
                self._subcategory_combo.addItem(subcat.get('nombre', ''), subcat.get('id', ''))
    
    def _on_type_changed(self, tipo: str):
        """Handle transaction type change."""
        # Show/hide category based on type
        is_transfer = tipo.startswith("Transferencia")
        self._category_combo.setEnabled(not is_transfer)
        self._subcategory_combo.setEnabled(not is_transfer)
    
    def _load_transaction_data(self):
        """Load existing transaction data into the form."""
        tx = self._transaction
        
        # Date
        fecha = tx.get('fecha')
        if fecha:
            if isinstance(fecha, datetime):
                self._date_edit.setDate(QDate(fecha.year, fecha.month, fecha.day))
            elif isinstance(fecha, str):
                try:
                    dt = datetime.fromisoformat(fecha)
                    self._date_edit.setDate(QDate(dt.year, dt.month, dt.day))
                except ValueError:
                    pass
        
        # Description
        self._description_edit.setText(tx.get('descripcion', ''))
        
        # Account
        cuenta_id = tx.get('cuenta_id', '')
        index = self._account_combo.findData(cuenta_id)
        if index >= 0:
            self._account_combo.setCurrentIndex(index)
        
        # Type
        tipo = tx.get('tipo', 'Gasto')
        index = self._type_combo.findText(tipo, Qt.MatchFixedString)
        if index >= 0:
            self._type_combo.setCurrentIndex(index)
        else:
            # Map monto to type
            monto = tx.get('monto', 0)
            if monto >= 0:
                self._type_combo.setCurrentText("Ingreso")
            else:
                self._type_combo.setCurrentText("Gasto")
        
        # Category
        cat_id = tx.get('categoria_id', '')
        index = self._category_combo.findData(cat_id)
        if index >= 0:
            self._category_combo.setCurrentIndex(index)
        
        # Subcategory
        subcat_id = tx.get('subcategoria_id', '')
        self._update_subcategories()
        index = self._subcategory_combo.findData(subcat_id)
        if index >= 0:
            self._subcategory_combo.setCurrentIndex(index)
        
        # Amount (always positive in the form)
        monto = abs(tx.get('monto', 0))
        self._amount_spin.setValue(monto)
        
        # Note
        self._note_edit.setPlainText(tx.get('nota', ''))
    
    def _add_attachment(self):
        """Open file dialog to add an attachment."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar archivo(s)",
            "",
            "Todos los archivos (*);;Imágenes (*.png *.jpg *.jpeg *.gif);;PDFs (*.pdf);;Documentos (*.doc *.docx *.xls *.xlsx)"
        )
        
        for filepath in files:
            try:
                filename = os.path.basename(filepath)
                with open(filepath, 'rb') as f:
                    data = f.read()
                
                # Determine content type
                ext = os.path.splitext(filename)[1].lower()
                content_types = {
                    '.pdf': 'application/pdf',
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif',
                    '.doc': 'application/msword',
                    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    '.xls': 'application/vnd.ms-excel',
                    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                }
                content_type = content_types.get(ext, 'application/octet-stream')
                
                self._pending_attachments.append((filename, data, content_type))
                logger.info(f"Attachment added: {filename}")
                
            except Exception as e:
                logger.error(f"Error reading file {filepath}: {e}")
                QMessageBox.warning(self, "Error", f"No se pudo leer el archivo:\n{filepath}")
        
        self._refresh_attachments_list()
    
    def _remove_attachment(self):
        """Remove the selected attachment."""
        current = self._attachments_list.currentRow()
        if current < 0:
            return
        
        # Check if it's an existing or pending attachment
        existing_count = len(self._existing_attachments)
        
        if current < existing_count:
            # Remove from existing
            removed = self._existing_attachments.pop(current)
            logger.info(f"Existing attachment removed: {removed.get('nombre')}")
        else:
            # Remove from pending
            pending_idx = current - existing_count
            if pending_idx < len(self._pending_attachments):
                removed = self._pending_attachments.pop(pending_idx)
                logger.info(f"Pending attachment removed: {removed[0]}")
        
        self._refresh_attachments_list()
    
    def _refresh_attachments_list(self):
        """Refresh the attachments list display."""
        self._attachments_list.clear()
        
        # Show existing attachments
        for adj in self._existing_attachments:
            item = QListWidgetItem(f"📎 {adj.get('nombre', 'Sin nombre')} (guardado)")
            item.setData(Qt.UserRole, {"type": "existing", "data": adj})
            self._attachments_list.addItem(item)
        
        # Show pending attachments
        for filename, data, content_type in self._pending_attachments:
            size_kb = len(data) / 1024
            item = QListWidgetItem(f"📄 {filename} ({size_kb:.1f} KB)")
            item.setData(Qt.UserRole, {"type": "pending"})
            self._attachments_list.addItem(item)
    
    def _on_accept(self):
        """Validate and accept the dialog."""
        # Validate required fields
        if not self._description_edit.text().strip():
            QMessageBox.warning(self, "Validación", "La descripción es requerida.")
            self._description_edit.setFocus()
            return
        
        if self._account_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Validación", "Debe seleccionar una cuenta.")
            return
        
        if self._amount_spin.value() <= 0:
            QMessageBox.warning(self, "Validación", "El monto debe ser mayor a cero.")
            self._amount_spin.setFocus()
            return
        
        self.accept()
    
    def get_transaction_data(self) -> Dict[str, Any]:
        """
        Get the transaction data from the form.
        
        Returns:
            Dictionary with transaction data.
        """
        qdate = self._date_edit.date()
        fecha = datetime(qdate.year(), qdate.month(), qdate.day())
        
        tipo = self._type_combo.currentText()
        monto = self._amount_spin.value()
        
        # Adjust sign based on type
        if tipo in ["Gasto", "Transferencia Salida"]:
            monto = -abs(monto)
        else:
            monto = abs(monto)
        
        data = {
            "fecha": fecha,
            "descripcion": self._description_edit.text().strip(),
            "cuenta_id": self._account_combo.currentData(),
            "tipo": tipo,
            "monto": monto,
            "nota": self._note_edit.toPlainText().strip(),
            "adjuntos": self._existing_attachments.copy(),
        }
        
        # Add category/subcategory if not a transfer
        if not tipo.startswith("Transferencia"):
            data["categoria_id"] = self._category_combo.currentData()
            data["subcategoria_id"] = self._subcategory_combo.currentData()
        
        return data
    
    def get_pending_attachments(self) -> List[Tuple[str, bytes, str]]:
        """Get the list of pending attachments to upload."""
        return self._pending_attachments.copy()
    
    def is_edit_mode(self) -> bool:
        """Check if dialog is in edit mode."""
        return self._is_edit
    
    def get_transaction_id(self) -> Optional[str]:
        """Get the transaction ID if editing."""
        if self._is_edit:
            return self._transaction.get('id')
        return None
