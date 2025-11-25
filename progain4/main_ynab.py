#!/usr/bin/env python3
"""
PROGAIN 5.1 - Main Entry Point
Financial management application with PyQt5 and Firebase.
"""

import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the application."""
    logger.info("Starting PROGAIN 5.1")
    
    # Import PyQt5
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
    except ImportError:
        logger.error("PyQt5 not installed. Please install with: pip install PyQt5")
        sys.exit(1)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("PROGAIN 5.1")
    app.setOrganizationName("PROGAIN")
    app.setOrganizationDomain("progain.local")
    
    # Enable high DPI scaling
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Import and apply theme from config
    from progain4.services.config import config
    from progain4.ui.theme_manager import theme_manager
    
    saved_theme = config.get_theme()
    if saved_theme:
        logger.info(f"Restoring saved theme: {saved_theme}")
        theme_manager.set_theme(saved_theme)
    
    # Apply initial stylesheet
    app.setStyleSheet(theme_manager.get_stylesheet())
    
    # Create and show main window
    from progain4.ui.main_window4 import MainWindow
    
    window = MainWindow()
    window.show()
    
    logger.info("Application started successfully")
    
    # Run event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
