"""
Main Window for PROGAIN 5.1
Main application window with project selector, transactions view, and toolbar.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import webbrowser

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QToolBar, QPushButton, QAction, QSplitter, QMessageBox, QStatusBar,
    QMenu, QMenuBar
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon

from progain4.services.firebase_client import firebase_client
from progain4.services.config import config
from progain4.ui.theme_manager import theme_manager
from progain4.ui.widgets.sidebar_widget import SidebarWidget
from progain4.ui.widgets.transactions_widget import TransactionsWidget
from progain4.ui.widgets.cashflow_window import CashflowWindow
from progain4.ui.widgets.accounts_window import AccountsWindow
from progain4.ui.dialogs.transaction_dialog import TransactionDialog
from progain4.ui.dialogs.transfer_dialog import TransferDialog

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window for PROGAIN 5.1.
    Provides project selection, transaction management, and access to all features.
    """
    
    def __init__(self):
        super().__init__()
        
        # Current state
        self.proyecto_id: Optional[str] = None
        self.proyecto_nombre_actual: str = ""
        self._cuentas: List[Dict[str, Any]] = []
        self._categorias: List[Dict[str, Any]] = []
        self._subcategorias: List[Dict[str, Any]] = []
        
        # Child windows
        self._cashflow_window: Optional[CashflowWindow] = None
        self._accounts_window: Optional[AccountsWindow] = None
        
        self._setup_ui()
        self._setup_menus()
        self._apply_saved_theme()
        
        # Initialize Firebase and load data
        self._initialize_app()
        
        logger.info("MainWindow initialized")
    
    def _setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle("PROGAIN 5.1")
        self.setMinimumSize(1200, 800)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Main toolbar
        self._setup_toolbar()
        
        # Content area with splitter
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Sidebar
        self._sidebar = SidebarWidget()
        self._sidebar.account_clicked.connect(self._on_sidebar_account_clicked)
        self._sidebar.account_double_clicked.connect(self._on_sidebar_account_double_clicked)
        content_splitter.addWidget(self._sidebar)
        
        # Transactions widget
        self._transactions_widget = TransactionsWidget()
        self._transactions_widget.transaction_double_clicked.connect(self._on_transaction_double_clicked)
        self._transactions_widget.edit_transaction_requested.connect(self._edit_transaction)
        self._transactions_widget.view_attachments_requested.connect(self._view_attachments)
        self._transactions_widget.delete_transaction_requested.connect(self._delete_transaction)
        content_splitter.addWidget(self._transactions_widget)
        
        content_splitter.setSizes([250, 950])
        main_layout.addWidget(content_splitter, 1)
        
        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Listo")
    
    def _setup_toolbar(self):
        """Set up the main toolbar."""
        toolbar = QToolBar("Principal")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # Project selector
        toolbar.addWidget(QLabel("  Proyecto:  "))
        self._project_combo = QComboBox()
        self._project_combo.setMinimumWidth(200)
        self._project_combo.currentIndexChanged.connect(self._on_project_selected)
        toolbar.addWidget(self._project_combo)
        
        toolbar.addSeparator()
        
        # Action buttons
        self._refresh_btn = QPushButton("🔄 Actualizar")
        self._refresh_btn.clicked.connect(self._refresh_data)
        toolbar.addWidget(self._refresh_btn)
        
        self._new_tx_btn = QPushButton("➕ Nueva Transacción")
        self._new_tx_btn.clicked.connect(self._new_transaction)
        toolbar.addWidget(self._new_tx_btn)
        
        self._transfer_btn = QPushButton("↔️ Transferencia")
        self._transfer_btn.clicked.connect(self._new_transfer)
        toolbar.addWidget(self._transfer_btn)
        
        toolbar.addSeparator()
        
        # Window buttons
        self._cashflow_btn = QPushButton("📊 Flujo de Caja")
        self._cashflow_btn.clicked.connect(self._show_cashflow_window)
        toolbar.addWidget(self._cashflow_btn)
        
        self._accounts_btn = QPushButton("🏦 Cuentas")
        self._accounts_btn.clicked.connect(self._show_accounts_window)
        toolbar.addWidget(self._accounts_btn)
    
    def _setup_menus(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("Archivo")
        
        refresh_action = QAction("Actualizar", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._refresh_data)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Salir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Transactions menu
        tx_menu = menubar.addMenu("Transacciones")
        
        new_tx_action = QAction("Nueva Transacción...", self)
        new_tx_action.setShortcut("Ctrl+N")
        new_tx_action.triggered.connect(self._new_transaction)
        tx_menu.addAction(new_tx_action)
        
        transfer_action = QAction("Nueva Transferencia...", self)
        transfer_action.setShortcut("Ctrl+T")
        transfer_action.triggered.connect(self._new_transfer)
        tx_menu.addAction(transfer_action)
        
        # View menu
        view_menu = menubar.addMenu("Ver")
        
        cashflow_action = QAction("Flujo de Caja", self)
        cashflow_action.triggered.connect(self._show_cashflow_window)
        view_menu.addAction(cashflow_action)
        
        accounts_action = QAction("Ventana de Cuentas", self)
        accounts_action.triggered.connect(self._show_accounts_window)
        view_menu.addAction(accounts_action)
        
        view_menu.addSeparator()
        
        # Theme submenu
        theme_menu = view_menu.addMenu("Tema")
        for theme_name in theme_manager.get_available_themes():
            action = QAction(theme_name, self)
            action.triggered.connect(lambda checked, tn=theme_name: self._change_theme(tn))
            theme_menu.addAction(action)
        
        # Help menu
        help_menu = menubar.addMenu("Ayuda")
        
        about_action = QAction("Acerca de...", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _apply_saved_theme(self):
        """Apply the theme saved in configuration."""
        saved_theme = config.get_theme()
        if saved_theme:
            logger.info(f"Applying saved theme: {saved_theme}")
            if theme_manager.set_theme(saved_theme):
                self.setStyleSheet(theme_manager.get_stylesheet())
        else:
            # Apply default theme
            self.setStyleSheet(theme_manager.get_stylesheet())
    
    def _change_theme(self, theme_name: str):
        """Change the application theme."""
        logger.info(f"Changing theme to: {theme_name}")
        if theme_manager.set_theme(theme_name):
            self.setStyleSheet(theme_manager.get_stylesheet())
            config.set_theme(theme_name)  # Persist the theme choice
            self._status_bar.showMessage(f"Tema cambiado a: {theme_name}", 3000)
    
    def _initialize_app(self):
        """Initialize the application after Firebase is ready."""
        # Initialize Firebase
        firebase_client.initialize()
        
        if firebase_client.is_initialized():
            self._load_projects()
        else:
            logger.warning("Firebase not initialized")
            self._status_bar.showMessage("Modo demo - Firebase no disponible")
    
    def _load_projects(self):
        """Load projects into the combo box."""
        logger.info("Loading projects")
        
        projects = firebase_client.get_proyectos()
        
        self._project_combo.blockSignals(True)
        self._project_combo.clear()
        
        for proj in projects:
            # Handle both dict and DocumentSnapshot
            if hasattr(proj, 'to_dict'):
                data = proj.to_dict()
                proj_id = proj.id
            else:
                data = proj
                proj_id = proj.get('id', '')
            
            nombre = data.get('nombre', 'Sin nombre')
            self._project_combo.addItem(nombre, proj_id)
        
        self._project_combo.blockSignals(False)
        
        # Restore last project or select first
        last_project_id = config.get_last_project_id()
        if last_project_id:
            index = self._project_combo.findData(last_project_id)
            if index >= 0:
                self._project_combo.setCurrentIndex(index)
                return
        
        # Select first project if available
        if self._project_combo.count() > 0:
            self._project_combo.setCurrentIndex(0)
            self._on_project_selected(0)
        
        logger.info(f"Loaded {len(projects)} projects")
    
    def _on_project_selected(self, index: int):
        """Handle project selection."""
        if index < 0:
            return
        
        project_id = self._project_combo.currentData()
        project_name = self._project_combo.currentText()
        
        if not project_id:
            return
        
        logger.info(f"Project selected: {project_name} ({project_id})")
        
        self.proyecto_id = project_id
        self.proyecto_nombre_actual = project_name
        
        # Update window title
        self.setWindowTitle(f"PROGAIN 5.1 - {project_name}")
        
        # Save last project
        config.set_last_project_id(project_id)
        
        # Load project data
        self._load_project_data()
    
    def _load_project_data(self):
        """Load all data for the current project."""
        if not self.proyecto_id:
            return
        
        self._status_bar.showMessage("Cargando datos del proyecto...")
        
        # Load accounts
        self._cuentas = firebase_client.get_cuentas_by_proyecto(self.proyecto_id)
        
        # Load categories
        self._categorias = firebase_client.get_categorias_by_proyecto(self.proyecto_id)
        
        # Load subcategories
        self._subcategorias = firebase_client.get_subcategorias_by_proyecto(self.proyecto_id)
        
        # Load transactions
        transactions = firebase_client.get_transacciones_by_proyecto(self.proyecto_id)
        
        # Update sidebar
        self._sidebar.set_project(self.proyecto_id, self.proyecto_nombre_actual)
        self._sidebar.set_accounts(self._cuentas)
        
        # Update transactions widget
        self._transactions_widget.set_lookup_data(self._cuentas, self._categorias)
        self._transactions_widget.set_transactions(transactions)
        
        self._status_bar.showMessage(
            f"Proyecto cargado: {len(self._cuentas)} cuentas, {len(transactions)} transacciones",
            5000
        )
    
    def _refresh_data(self):
        """Refresh all project data."""
        logger.info("Refreshing data")
        self._load_project_data()
    
    def _new_transaction(self):
        """Open dialog to create a new transaction."""
        if not self.proyecto_id:
            QMessageBox.warning(self, "Aviso", "Seleccione un proyecto primero.")
            return
        
        dialog = TransactionDialog(
            self,
            transaction=None,
            accounts=self._cuentas,
            categories=self._categorias,
            subcategories=self._subcategorias
        )
        
        if dialog.exec_():
            data = dialog.get_transaction_data()
            pending_attachments = dialog.get_pending_attachments()
            
            # Upload attachments if any
            if pending_attachments:
                fecha = data.get('fecha', datetime.now())
                adjuntos = firebase_client.upload_adjuntos_transaccion(
                    self.proyecto_id, fecha, pending_attachments
                )
                data['adjuntos'] = adjuntos
            
            # Create transaction
            tx_id = firebase_client.agregar_transaccion_a_proyecto(self.proyecto_id, data)
            
            if tx_id:
                logger.info(f"Transaction created: {tx_id}")
                self._status_bar.showMessage("Transacción creada exitosamente", 3000)
                self._refresh_data()
            else:
                QMessageBox.critical(self, "Error", "No se pudo crear la transacción.")
    
    def _edit_transaction(self, tx: Dict[str, Any]):
        """Open dialog to edit an existing transaction."""
        if not self.proyecto_id:
            return
        
        dialog = TransactionDialog(
            self,
            transaction=tx,
            accounts=self._cuentas,
            categories=self._categorias,
            subcategories=self._subcategorias
        )
        
        if dialog.exec_():
            data = dialog.get_transaction_data()
            tx_id = dialog.get_transaction_id()
            pending_attachments = dialog.get_pending_attachments()
            
            # Upload new attachments if any
            if pending_attachments:
                fecha = data.get('fecha', datetime.now())
                new_adjuntos = firebase_client.upload_adjuntos_transaccion(
                    self.proyecto_id, fecha, pending_attachments
                )
                data['adjuntos'] = data.get('adjuntos', []) + new_adjuntos
            
            # Update transaction
            if firebase_client.actualizar_transaccion(self.proyecto_id, tx_id, data):
                logger.info(f"Transaction updated: {tx_id}")
                self._status_bar.showMessage("Transacción actualizada", 3000)
                self._refresh_data()
            else:
                QMessageBox.critical(self, "Error", "No se pudo actualizar la transacción.")
    
    def _on_transaction_double_clicked(self, tx: Dict[str, Any]):
        """Handle transaction double click - edit it."""
        self._edit_transaction(tx)
    
    def _view_attachments(self, tx: Dict[str, Any]):
        """View attachments for a transaction."""
        adjuntos = tx.get('adjuntos', [])
        if not adjuntos:
            QMessageBox.information(self, "Adjuntos", "Esta transacción no tiene adjuntos.")
            return
        
        # For now, just list the attachments
        msg = "Adjuntos:\n\n"
        for adj in adjuntos:
            nombre = adj.get('nombre', 'Sin nombre')
            url = adj.get('url', '')
            msg += f"• {nombre}\n"
        
        msg += "\n¿Desea abrir el primero en el navegador?"
        
        reply = QMessageBox.question(
            self, "Adjuntos", msg,
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            url = adjuntos[0].get('url', '')
            if url:
                webbrowser.open(url)
    
    def _delete_transaction(self, tx: Dict[str, Any]):
        """Delete a transaction."""
        tx_id = tx.get('id')
        if not tx_id or not self.proyecto_id:
            return
        
        reply = QMessageBox.question(
            self, "Confirmar",
            f"¿Está seguro de eliminar esta transacción?\n\n{tx.get('descripcion', '')}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if firebase_client.eliminar_transaccion(self.proyecto_id, tx_id):
                logger.info(f"Transaction deleted: {tx_id}")
                self._status_bar.showMessage("Transacción eliminada", 3000)
                self._refresh_data()
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar la transacción.")
    
    def _new_transfer(self):
        """Open dialog to create a transfer between accounts."""
        if not self.proyecto_id:
            QMessageBox.warning(self, "Aviso", "Seleccione un proyecto primero.")
            return
        
        if len(self._cuentas) < 2:
            QMessageBox.warning(self, "Aviso", "Necesita al menos 2 cuentas para hacer una transferencia.")
            return
        
        dialog = TransferDialog(self, accounts=self._cuentas)
        
        if dialog.exec_():
            data = dialog.get_transfer_data()
            
            # Create transfer (two linked transactions)
            id_salida, id_entrada = firebase_client.crear_transferencia(
                self.proyecto_id,
                data['cuenta_origen_id'],
                data['cuenta_destino_id'],
                data['monto'],
                data['fecha'],
                data['nota']
            )
            
            if id_salida and id_entrada:
                logger.info(f"Transfer created: {id_salida} -> {id_entrada}")
                self._status_bar.showMessage("Transferencia creada exitosamente", 3000)
                self._refresh_data()
            else:
                QMessageBox.critical(self, "Error", "No se pudo crear la transferencia.")
    
    def _show_cashflow_window(self):
        """Show the cash flow window."""
        if not self.proyecto_id:
            QMessageBox.warning(self, "Aviso", "Seleccione un proyecto primero.")
            return
        
        if not self._cashflow_window:
            self._cashflow_window = CashflowWindow(self)
        
        self._cashflow_window.set_project(self.proyecto_id, self.proyecto_nombre_actual)
        self._cashflow_window.refresh()
        self._cashflow_window.show()
        self._cashflow_window.raise_()
        self._cashflow_window.activateWindow()
    
    def _show_accounts_window(self):
        """Show the accounts window."""
        if not self.proyecto_id:
            QMessageBox.warning(self, "Aviso", "Seleccione un proyecto primero.")
            return
        
        if not self._accounts_window:
            self._accounts_window = AccountsWindow(self)
            self._accounts_window.edit_transaction_requested.connect(self._edit_transaction)
            self._accounts_window.view_attachments_requested.connect(self._view_attachments)
        
        self._accounts_window.set_project(self.proyecto_id, self.proyecto_nombre_actual)
        self._accounts_window.show()
        self._accounts_window.raise_()
        self._accounts_window.activateWindow()
    
    def _on_sidebar_account_clicked(self, cuenta_id: str, cuenta_nombre: str):
        """Handle sidebar account click - open accounts window."""
        logger.debug(f"Sidebar account clicked: {cuenta_nombre} ({cuenta_id})")
        
        if not self._accounts_window:
            self._accounts_window = AccountsWindow(self)
            self._accounts_window.edit_transaction_requested.connect(self._edit_transaction)
            self._accounts_window.view_attachments_requested.connect(self._view_attachments)
        
        self._accounts_window.set_project(self.proyecto_id, self.proyecto_nombre_actual)
        self._accounts_window.select_account(cuenta_id)
        self._accounts_window.show()
        self._accounts_window.raise_()
        self._accounts_window.activateWindow()
    
    def _on_sidebar_account_double_clicked(self, cuenta_id: str, cuenta_nombre: str):
        """Handle sidebar account double click - same as single click."""
        self._on_sidebar_account_clicked(cuenta_id, cuenta_nombre)
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "Acerca de PROGAIN 5.1",
            """<h2>PROGAIN 5.1</h2>
            <p>Sistema de Gestión Financiera</p>
            <p>Versión 5.1.0</p>
            <hr>
            <p>Características:</p>
            <ul>
                <li>Gestión de proyectos y cuentas</li>
                <li>Transacciones con adjuntos</li>
                <li>Transferencias entre cuentas</li>
                <li>Flujo de caja y reportes</li>
                <li>Temas personalizables</li>
            </ul>
            """
        )
    
    def closeEvent(self, event):
        """Handle window close."""
        # Close child windows
        if self._cashflow_window:
            self._cashflow_window.close()
        if self._accounts_window:
            self._accounts_window.close()
        
        logger.info("Main window closed")
        event.accept()
