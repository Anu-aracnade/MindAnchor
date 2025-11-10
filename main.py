# main.py
# Entry point for MindAnchor AI Desktop App

import database
import gui

if __name__ == "__main__":
    # Initialize database before starting GUI
    database.init_db()
    gui.start_app()