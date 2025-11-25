"""
Theme Manager for PROGAIN 5.1
Handles application theming with multiple color schemes.
"""

import logging
from typing import Dict, Optional, Callable, List

logger = logging.getLogger(__name__)


class ThemeManager:
    """
    Manages application themes and styling.
    Supports multiple predefined themes and custom themes.
    """
    
    _instance = None
    
    # Predefined themes
    THEMES: Dict[str, Dict[str, str]] = {
        "Claro": {
            "background": "#FFFFFF",
            "surface": "#F5F5F5",
            "primary": "#1976D2",
            "primary_dark": "#1565C0",
            "secondary": "#424242",
            "text": "#212121",
            "text_secondary": "#757575",
            "border": "#E0E0E0",
            "success": "#4CAF50",
            "warning": "#FF9800",
            "error": "#F44336",
            "income": "#4CAF50",
            "expense": "#F44336",
        },
        "Oscuro": {
            "background": "#121212",
            "surface": "#1E1E1E",
            "primary": "#2196F3",
            "primary_dark": "#1976D2",
            "secondary": "#B0BEC5",
            "text": "#FFFFFF",
            "text_secondary": "#B0BEC5",
            "border": "#333333",
            "success": "#66BB6A",
            "warning": "#FFA726",
            "error": "#EF5350",
            "income": "#66BB6A",
            "expense": "#EF5350",
        },
        "Azul Profesional": {
            "background": "#ECEFF1",
            "surface": "#FFFFFF",
            "primary": "#0D47A1",
            "primary_dark": "#0A3D91",
            "secondary": "#37474F",
            "text": "#263238",
            "text_secondary": "#546E7A",
            "border": "#B0BEC5",
            "success": "#2E7D32",
            "warning": "#EF6C00",
            "error": "#C62828",
            "income": "#2E7D32",
            "expense": "#C62828",
        },
        "Verde Natural": {
            "background": "#E8F5E9",
            "surface": "#FFFFFF",
            "primary": "#2E7D32",
            "primary_dark": "#1B5E20",
            "secondary": "#33691E",
            "text": "#1B5E20",
            "text_secondary": "#558B2F",
            "border": "#A5D6A7",
            "success": "#2E7D32",
            "warning": "#F57C00",
            "error": "#D32F2F",
            "income": "#2E7D32",
            "expense": "#D32F2F",
        },
        "Alto Contraste": {
            "background": "#000000",
            "surface": "#1A1A1A",
            "primary": "#FFFF00",
            "primary_dark": "#CCCC00",
            "secondary": "#FFFFFF",
            "text": "#FFFFFF",
            "text_secondary": "#CCCCCC",
            "border": "#FFFFFF",
            "success": "#00FF00",
            "warning": "#FFFF00",
            "error": "#FF0000",
            "income": "#00FF00",
            "expense": "#FF0000",
        },
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._current_theme = "Claro"
        self._theme_change_callbacks: List[Callable[[str], None]] = []
        logger.info("ThemeManager initialized")
    
    def get_available_themes(self) -> List[str]:
        """Get list of available theme names."""
        return list(self.THEMES.keys())
    
    def get_current_theme_name(self) -> str:
        """Get the name of the currently active theme."""
        return self._current_theme
    
    def get_current_theme(self) -> Dict[str, str]:
        """Get the current theme's color dictionary."""
        return self.THEMES.get(self._current_theme, self.THEMES["Claro"])
    
    def get_theme(self, theme_name: str) -> Optional[Dict[str, str]]:
        """Get a specific theme by name."""
        return self.THEMES.get(theme_name)
    
    def set_theme(self, theme_name: str) -> bool:
        """
        Set the active theme.
        
        Args:
            theme_name: Name of the theme to activate
            
        Returns:
            True if theme was set successfully, False otherwise.
        """
        if theme_name not in self.THEMES:
            logger.warning(f"Theme '{theme_name}' not found")
            return False
        
        self._current_theme = theme_name
        logger.info(f"Theme changed to: {theme_name}")
        
        # Notify listeners
        for callback in self._theme_change_callbacks:
            try:
                callback(theme_name)
            except Exception as e:
                logger.error(f"Error in theme change callback: {e}")
        
        return True
    
    def add_theme_change_listener(self, callback: Callable[[str], None]) -> None:
        """Register a callback to be called when theme changes."""
        self._theme_change_callbacks.append(callback)
    
    def remove_theme_change_listener(self, callback: Callable[[str], None]) -> None:
        """Remove a theme change callback."""
        if callback in self._theme_change_callbacks:
            self._theme_change_callbacks.remove(callback)
    
    def get_stylesheet(self, theme_name: Optional[str] = None) -> str:
        """
        Generate a Qt stylesheet for the specified or current theme.
        
        Args:
            theme_name: Theme name, or None for current theme
            
        Returns:
            Qt stylesheet string
        """
        theme = self.THEMES.get(theme_name or self._current_theme, self.THEMES["Claro"])
        
        stylesheet = f"""
        /* Main Window and Widgets */
        QMainWindow, QDialog, QWidget {{
            background-color: {theme['background']};
            color: {theme['text']};
        }}
        
        /* Labels */
        QLabel {{
            color: {theme['text']};
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {theme['primary']};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background-color: {theme['primary_dark']};
        }}
        
        QPushButton:pressed {{
            background-color: {theme['secondary']};
        }}
        
        QPushButton:disabled {{
            background-color: {theme['border']};
            color: {theme['text_secondary']};
        }}
        
        /* ComboBox */
        QComboBox {{
            background-color: {theme['surface']};
            color: {theme['text']};
            border: 1px solid {theme['border']};
            padding: 6px 12px;
            border-radius: 4px;
            min-width: 100px;
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {theme['surface']};
            color: {theme['text']};
            selection-background-color: {theme['primary']};
            selection-color: white;
        }}
        
        /* LineEdit */
        QLineEdit {{
            background-color: {theme['surface']};
            color: {theme['text']};
            border: 1px solid {theme['border']};
            padding: 6px 12px;
            border-radius: 4px;
        }}
        
        QLineEdit:focus {{
            border: 2px solid {theme['primary']};
        }}
        
        /* TextEdit */
        QTextEdit, QPlainTextEdit {{
            background-color: {theme['surface']};
            color: {theme['text']};
            border: 1px solid {theme['border']};
            border-radius: 4px;
        }}
        
        /* Tables */
        QTableWidget, QTableView {{
            background-color: {theme['surface']};
            color: {theme['text']};
            gridline-color: {theme['border']};
            selection-background-color: {theme['primary']};
            selection-color: white;
            border: 1px solid {theme['border']};
        }}
        
        QTableWidget::item, QTableView::item {{
            padding: 8px;
        }}
        
        QHeaderView::section {{
            background-color: {theme['secondary']};
            color: white;
            padding: 8px;
            border: none;
            font-weight: bold;
        }}
        
        /* Toolbar */
        QToolBar {{
            background-color: {theme['surface']};
            border: none;
            spacing: 8px;
            padding: 4px;
        }}
        
        /* Menu */
        QMenuBar {{
            background-color: {theme['surface']};
            color: {theme['text']};
        }}
        
        QMenuBar::item:selected {{
            background-color: {theme['primary']};
            color: white;
        }}
        
        QMenu {{
            background-color: {theme['surface']};
            color: {theme['text']};
            border: 1px solid {theme['border']};
        }}
        
        QMenu::item:selected {{
            background-color: {theme['primary']};
            color: white;
        }}
        
        /* Sidebar / List Widget */
        QListWidget {{
            background-color: {theme['surface']};
            color: {theme['text']};
            border: 1px solid {theme['border']};
        }}
        
        QListWidget::item {{
            padding: 10px;
        }}
        
        QListWidget::item:selected {{
            background-color: {theme['primary']};
            color: white;
        }}
        
        QListWidget::item:hover {{
            background-color: {theme['border']};
        }}
        
        /* Tree Widget */
        QTreeWidget {{
            background-color: {theme['surface']};
            color: {theme['text']};
            border: 1px solid {theme['border']};
        }}
        
        QTreeWidget::item:selected {{
            background-color: {theme['primary']};
            color: white;
        }}
        
        /* Scroll Bars */
        QScrollBar:vertical {{
            background: {theme['background']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background: {theme['border']};
            border-radius: 6px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {theme['secondary']};
        }}
        
        QScrollBar:horizontal {{
            background: {theme['background']};
            height: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background: {theme['border']};
            border-radius: 6px;
            min-width: 30px;
        }}
        
        /* Tab Widget */
        QTabWidget::pane {{
            border: 1px solid {theme['border']};
            background-color: {theme['surface']};
        }}
        
        QTabBar::tab {{
            background-color: {theme['background']};
            color: {theme['text']};
            padding: 8px 16px;
            border: 1px solid {theme['border']};
            border-bottom: none;
        }}
        
        QTabBar::tab:selected {{
            background-color: {theme['surface']};
            border-color: {theme['primary']};
            border-bottom: 2px solid {theme['primary']};
        }}
        
        /* GroupBox */
        QGroupBox {{
            border: 1px solid {theme['border']};
            border-radius: 4px;
            margin-top: 12px;
            padding-top: 12px;
            font-weight: bold;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            color: {theme['text']};
        }}
        
        /* DateEdit */
        QDateEdit {{
            background-color: {theme['surface']};
            color: {theme['text']};
            border: 1px solid {theme['border']};
            padding: 6px 12px;
            border-radius: 4px;
        }}
        
        /* SpinBox */
        QSpinBox, QDoubleSpinBox {{
            background-color: {theme['surface']};
            color: {theme['text']};
            border: 1px solid {theme['border']};
            padding: 6px 12px;
            border-radius: 4px;
        }}
        
        /* CheckBox */
        QCheckBox {{
            color: {theme['text']};
            spacing: 8px;
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
        }}
        
        /* StatusBar */
        QStatusBar {{
            background-color: {theme['surface']};
            color: {theme['text_secondary']};
            border-top: 1px solid {theme['border']};
        }}
        
        /* ProgressBar */
        QProgressBar {{
            background-color: {theme['border']};
            border-radius: 4px;
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background-color: {theme['primary']};
            border-radius: 4px;
        }}
        """
        
        return stylesheet


# Singleton instance
theme_manager = ThemeManager()
