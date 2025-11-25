"""
Cashflow Window for PROGAIN 5.1
Independent window for displaying cash flow reports by project.
"""

import csv
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QGroupBox,
    QFrame, QFileDialog, QMessageBox, QSplitter, QTabWidget
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor

from progain4.services.firebase_client import firebase_client

logger = logging.getLogger(__name__)


class CashflowWindow(QMainWindow):
    """
    Independent window for cash flow analysis by project.
    Shows summaries by account and by month.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_id: Optional[str] = None
        self._project_name: str = ""
        self._fecha_inicio: Optional[datetime] = None
        self._fecha_fin: Optional[datetime] = None
        
        # Data
        self._cashflow_por_cuenta: List[Dict[str, Any]] = []
        self._cashflow_mensual: List[Dict[str, Any]] = []
        
        self._setup_ui()
        
        # Set default period (current year)
        today = datetime.now()
        self._fecha_inicio = datetime(today.year, 1, 1)
        self._fecha_fin = datetime(today.year, 12, 31)
        self._update_date_controls()
        
        logger.info("CashflowWindow initialized")
    
    def _setup_ui(self):
        """Set up the window UI."""
        self.setWindowTitle("Flujo de Caja")
        self.setMinimumSize(900, 600)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Header
        header_layout = QHBoxLayout()
        
        self._title_label = QLabel("Flujo de Caja")
        self._title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header_layout.addWidget(self._title_label)
        
        self._project_label = QLabel("")
        self._project_label.setStyleSheet("color: gray;")
        header_layout.addWidget(self._project_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Date range controls
        date_frame = QFrame()
        date_frame.setFrameStyle(QFrame.StyledPanel)
        date_layout = QHBoxLayout(date_frame)
        
        date_layout.addWidget(QLabel("Desde:"))
        self._start_date = QDateEdit()
        self._start_date.setCalendarPopup(True)
        self._start_date.setDisplayFormat("dd/MM/yyyy")
        self._start_date.dateChanged.connect(self._on_date_changed)
        date_layout.addWidget(self._start_date)
        
        date_layout.addWidget(QLabel("Hasta:"))
        self._end_date = QDateEdit()
        self._end_date.setCalendarPopup(True)
        self._end_date.setDisplayFormat("dd/MM/yyyy")
        self._end_date.dateChanged.connect(self._on_date_changed)
        date_layout.addWidget(self._end_date)
        
        date_layout.addSpacing(20)
        
        # Quick period buttons
        self._this_month_btn = QPushButton("Este Mes")
        self._this_month_btn.clicked.connect(self._set_this_month)
        date_layout.addWidget(self._this_month_btn)
        
        self._this_year_btn = QPushButton("Este Año")
        self._this_year_btn.clicked.connect(self._set_this_year)
        date_layout.addWidget(self._this_year_btn)
        
        self._last_year_btn = QPushButton("Año Anterior")
        self._last_year_btn.clicked.connect(self._set_last_year)
        date_layout.addWidget(self._last_year_btn)
        
        date_layout.addStretch()
        
        # Refresh button
        self._refresh_btn = QPushButton("Actualizar")
        self._refresh_btn.clicked.connect(self.refresh)
        date_layout.addWidget(self._refresh_btn)
        
        layout.addWidget(date_frame)
        
        # Tab widget for different views
        tabs = QTabWidget()
        
        # Tab 1: Summary by Account
        accounts_tab = QWidget()
        accounts_layout = QVBoxLayout(accounts_tab)
        
        self._accounts_table = QTableWidget()
        self._accounts_table.setColumnCount(5)
        self._accounts_table.setHorizontalHeaderLabels([
            "Cuenta", "Total Ingresos", "Total Gastos", "Balance", "% del Total"
        ])
        self._accounts_table.setAlternatingRowColors(True)
        self._accounts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        header = self._accounts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        accounts_layout.addWidget(self._accounts_table)
        
        # Account totals
        self._accounts_totals_label = QLabel("")
        self._accounts_totals_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self._accounts_totals_label.setAlignment(Qt.AlignRight)
        accounts_layout.addWidget(self._accounts_totals_label)
        
        tabs.addTab(accounts_tab, "Por Cuenta")
        
        # Tab 2: Monthly breakdown
        monthly_tab = QWidget()
        monthly_layout = QVBoxLayout(monthly_tab)
        
        self._monthly_table = QTableWidget()
        self._monthly_table.setColumnCount(4)
        self._monthly_table.setHorizontalHeaderLabels([
            "Período", "Ingresos", "Gastos", "Balance"
        ])
        self._monthly_table.setAlternatingRowColors(True)
        self._monthly_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        header = self._monthly_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        monthly_layout.addWidget(self._monthly_table)
        
        # Monthly totals
        self._monthly_totals_label = QLabel("")
        self._monthly_totals_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self._monthly_totals_label.setAlignment(Qt.AlignRight)
        monthly_layout.addWidget(self._monthly_totals_label)
        
        tabs.addTab(monthly_tab, "Por Mes")
        
        layout.addWidget(tabs, 1)
        
        # Export buttons
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        
        self._export_csv_btn = QPushButton("Exportar CSV")
        self._export_csv_btn.clicked.connect(self._export_csv)
        export_layout.addWidget(self._export_csv_btn)
        
        layout.addLayout(export_layout)
    
    def _update_date_controls(self):
        """Update date edit controls with current period."""
        if self._fecha_inicio:
            self._start_date.setDate(QDate(
                self._fecha_inicio.year,
                self._fecha_inicio.month,
                self._fecha_inicio.day
            ))
        if self._fecha_fin:
            self._end_date.setDate(QDate(
                self._fecha_fin.year,
                self._fecha_fin.month,
                self._fecha_fin.day
            ))
    
    def _on_date_changed(self):
        """Handle date changes."""
        start = self._start_date.date()
        end = self._end_date.date()
        
        self._fecha_inicio = datetime(start.year(), start.month(), start.day())
        self._fecha_fin = datetime(end.year(), end.month(), end.day())
    
    def _set_this_month(self):
        """Set period to current month."""
        today = datetime.now()
        self._fecha_inicio = datetime(today.year, today.month, 1)
        # Last day of month
        if today.month == 12:
            self._fecha_fin = datetime(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            self._fecha_fin = datetime(today.year, today.month + 1, 1) - timedelta(days=1)
        self._update_date_controls()
        self.refresh()
    
    def _set_this_year(self):
        """Set period to current year."""
        today = datetime.now()
        self._fecha_inicio = datetime(today.year, 1, 1)
        self._fecha_fin = datetime(today.year, 12, 31)
        self._update_date_controls()
        self.refresh()
    
    def _set_last_year(self):
        """Set period to last year."""
        today = datetime.now()
        self._fecha_inicio = datetime(today.year - 1, 1, 1)
        self._fecha_fin = datetime(today.year - 1, 12, 31)
        self._update_date_controls()
        self.refresh()
    
    def set_project(self, project_id: str, project_name: str):
        """
        Set the project context.
        
        Args:
            project_id: Project ID
            project_name: Project display name
        """
        self._project_id = project_id
        self._project_name = project_name
        self.setWindowTitle(f"Flujo de Caja - {project_name}")
        self._project_label.setText(f"Proyecto: {project_name}")
        logger.info(f"Cashflow project set: {project_name} ({project_id})")
    
    def set_period(self, fecha_inicio: datetime, fecha_fin: datetime):
        """
        Set the analysis period.
        
        Args:
            fecha_inicio: Start date
            fecha_fin: End date
        """
        self._fecha_inicio = fecha_inicio
        self._fecha_fin = fecha_fin
        self._update_date_controls()
        logger.debug(f"Cashflow period set: {fecha_inicio} to {fecha_fin}")
    
    def refresh(self):
        """Refresh the cash flow data and display."""
        if not self._project_id:
            logger.warning("No project set for cashflow")
            return
        
        if not self._fecha_inicio or not self._fecha_fin:
            logger.warning("No period set for cashflow")
            return
        
        logger.info(f"Refreshing cashflow for project {self._project_id}")
        
        # Get data from Firebase
        self._cashflow_por_cuenta = firebase_client.calcular_flujo_caja_por_cuenta(
            self._project_id, self._fecha_inicio, self._fecha_fin
        )
        self._cashflow_mensual = firebase_client.calcular_flujo_caja_mensual(
            self._project_id, self._fecha_inicio, self._fecha_fin
        )
        
        # Update tables
        self._refresh_accounts_table()
        self._refresh_monthly_table()
    
    def _refresh_accounts_table(self):
        """Refresh the accounts summary table."""
        self._accounts_table.setRowCount(0)
        
        total_ingresos = 0
        total_gastos = 0
        
        for data in self._cashflow_por_cuenta:
            total_ingresos += data.get('total_ingresos', 0)
            total_gastos += data.get('total_gastos', 0)
        
        total_balance = total_ingresos - total_gastos
        
        for data in self._cashflow_por_cuenta:
            row = self._accounts_table.rowCount()
            self._accounts_table.insertRow(row)
            
            # Cuenta
            self._accounts_table.setItem(row, 0, QTableWidgetItem(data.get('cuenta_nombre', '')))
            
            # Ingresos
            ingresos = data.get('total_ingresos', 0)
            ing_item = QTableWidgetItem(f"${ingresos:,.2f}")
            ing_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            ing_item.setForeground(QColor("#4CAF50"))
            self._accounts_table.setItem(row, 1, ing_item)
            
            # Gastos
            gastos = data.get('total_gastos', 0)
            gas_item = QTableWidgetItem(f"${gastos:,.2f}")
            gas_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            gas_item.setForeground(QColor("#F44336"))
            self._accounts_table.setItem(row, 2, gas_item)
            
            # Balance
            balance = data.get('balance', 0)
            bal_item = QTableWidgetItem(f"${balance:,.2f}")
            bal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if balance >= 0:
                bal_item.setForeground(QColor("#4CAF50"))
            else:
                bal_item.setForeground(QColor("#F44336"))
            self._accounts_table.setItem(row, 3, bal_item)
            
            # Percentage
            if total_ingresos + total_gastos > 0:
                pct = (ingresos + gastos) / (total_ingresos + total_gastos) * 100
            else:
                pct = 0
            pct_item = QTableWidgetItem(f"{pct:.1f}%")
            pct_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._accounts_table.setItem(row, 4, pct_item)
        
        # Update totals label
        self._accounts_totals_label.setText(
            f"Totales: Ingresos ${total_ingresos:,.2f} | Gastos ${total_gastos:,.2f} | "
            f"Balance {'$' if total_balance >= 0 else '-$'}{abs(total_balance):,.2f}"
        )
    
    def _refresh_monthly_table(self):
        """Refresh the monthly breakdown table."""
        self._monthly_table.setRowCount(0)
        
        total_ingresos = 0
        total_gastos = 0
        
        # Month names for display
        month_names = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        
        for data in self._cashflow_mensual:
            row = self._monthly_table.rowCount()
            self._monthly_table.insertRow(row)
            
            # Período
            periodo = data.get('periodo', '')
            try:
                year, month = periodo.split('-')
                display_periodo = f"{month_names.get(int(month), month)} {year}"
            except (ValueError, KeyError):
                display_periodo = periodo
            self._monthly_table.setItem(row, 0, QTableWidgetItem(display_periodo))
            
            # Ingresos
            ingresos = data.get('ingresos', 0)
            total_ingresos += ingresos
            ing_item = QTableWidgetItem(f"${ingresos:,.2f}")
            ing_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            ing_item.setForeground(QColor("#4CAF50"))
            self._monthly_table.setItem(row, 1, ing_item)
            
            # Gastos
            gastos = data.get('gastos', 0)
            total_gastos += gastos
            gas_item = QTableWidgetItem(f"${gastos:,.2f}")
            gas_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            gas_item.setForeground(QColor("#F44336"))
            self._monthly_table.setItem(row, 2, gas_item)
            
            # Balance
            balance = data.get('balance', 0)
            bal_item = QTableWidgetItem(f"${balance:,.2f}")
            bal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if balance >= 0:
                bal_item.setForeground(QColor("#4CAF50"))
            else:
                bal_item.setForeground(QColor("#F44336"))
            self._monthly_table.setItem(row, 3, bal_item)
        
        # Update totals label
        total_balance = total_ingresos - total_gastos
        self._monthly_totals_label.setText(
            f"Totales: Ingresos ${total_ingresos:,.2f} | Gastos ${total_gastos:,.2f} | "
            f"Balance {'$' if total_balance >= 0 else '-$'}{abs(total_balance):,.2f}"
        )
    
    def _export_csv(self):
        """Export current data to CSV."""
        if not self._cashflow_por_cuenta and not self._cashflow_mensual:
            QMessageBox.information(self, "Exportar", "No hay datos para exportar.")
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar como CSV",
            f"flujo_caja_{self._project_name or 'proyecto'}_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV (*.csv)"
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write accounts summary
                writer.writerow(["RESUMEN POR CUENTA"])
                writer.writerow(["Cuenta", "Total Ingresos", "Total Gastos", "Balance"])
                
                for data in self._cashflow_por_cuenta:
                    writer.writerow([
                        data.get('cuenta_nombre', ''),
                        data.get('total_ingresos', 0),
                        data.get('total_gastos', 0),
                        data.get('balance', 0)
                    ])
                
                writer.writerow([])
                writer.writerow(["RESUMEN MENSUAL"])
                writer.writerow(["Período", "Ingresos", "Gastos", "Balance"])
                
                for data in self._cashflow_mensual:
                    writer.writerow([
                        data.get('periodo', ''),
                        data.get('ingresos', 0),
                        data.get('gastos', 0),
                        data.get('balance', 0)
                    ])
            
            QMessageBox.information(
                self, "Exportar",
                f"Datos exportados exitosamente a:\n{filepath}"
            )
            logger.info(f"Cashflow exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            QMessageBox.critical(
                self, "Error",
                f"Error al exportar:\n{str(e)}"
            )
