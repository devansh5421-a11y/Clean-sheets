import sys
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout,
                             QWidget, QFileDialog, QLabel, QTextEdit, QMessageBox,
                             QComboBox, QLineEdit, QHBoxLayout, QDialog, QProgressBar, QCheckBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import os

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# ==========================================
# 1. THE DATA CLEANER LOGIC
# ==========================================
class DataCleaner:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def standardize_dates(self):
        """Detects date-like object columns and converts them to YYYY-MM-DD."""
        for col in self.df.columns:
            if self.df[col].dtype == 'object':
                orig_valid = self.df[col].notna().sum()
                if orig_valid == 0: continue
                
                # Attempt to parse. 'mixed' handles varying formats (MM/DD, DD/MM)
                temp = pd.to_datetime(self.df[col], format='mixed', errors='coerce')
                new_valid = temp.notna().sum()
                
                # Heuristic: If >50% of the non-null strings parsed into dates, it's a date column
                if (new_valid / orig_valid) > 0.5:
                    self.df[col] = temp.dt.strftime('%Y-%m-%d')
        return self.df

    def handle_missing_values(self, strategy: str, custom_value=None):
        """Safely handles missing values, respecting column data types."""
        for col in self.df.columns:
            if not self.df[col].isnull().any():
                continue

            if strategy == 'Fill with 0':
                self.df[col] = self.df[col].fillna(0)
            
            elif strategy == 'Custom Value' and custom_value is not None:
                val = custom_value
                if pd.api.types.is_numeric_dtype(self.df[col]):
                    try: val = float(custom_value)
                    except ValueError: pass # Keep as string if cast fails
                self.df[col] = self.df[col].fillna(val)
                
            elif strategy == 'Auto (Median/Mode)':
                # Safely detect numeric vs text
                if pd.api.types.is_numeric_dtype(self.df[col]):
                    self.df[col] = self.df[col].fillna(self.df[col].median())
                else:
                    mode_val = self.df[col].mode()
                    if not mode_val.empty:
                        self.df[col] = self.df[col].fillna(mode_val[0])
        return self.df

# ==========================================
# 2. THE BACKGROUND WORKER (QThread)
# ==========================================
class CleaningWorker(QThread):
    progress_update = pyqtSignal(int, str) # Emits (Progress %, Log Message)
    finished_success = pyqtSignal(dict, str) # Emits (Cleaned Data Dict, Summary message)
    error_occurred = pyqtSignal(str)

    def __init__(self, file_path, sheet_selection, strategy, custom_val, clean_dates):
        super().__init__()
        self.file_path = file_path
        self.sheet_selection = sheet_selection
        self.strategy = strategy
        self.custom_val = custom_val
        self.clean_dates = clean_dates

    def run(self):
        try:
            self.progress_update.emit(10, "Reading file into memory...")
            raw_data = {}
            
            # Load Data (CSV vs Excel)
            if self.file_path.endswith('.csv'):
                raw_data['Dataset'] = pd.read_csv(self.file_path)
            else:
                if self.sheet_selection == "All Sheets":
                    raw_data = pd.read_excel(self.file_path, sheet_name=None)
                else:
                    raw_data[self.sheet_selection] = pd.read_excel(self.file_path, sheet_name=self.sheet_selection)

            cleaned_data = {}
            total_sheets = len(raw_data)
            current_sheet = 0

            # Process each sheet
            for sheet_name, df in raw_data.items():
                self.progress_update.emit(30 + int((current_sheet/total_sheets)*40), f"Cleaning sheet: {sheet_name}...")
                
                cleaner = DataCleaner(df)
                
                # Standardize Dates
                if self.clean_dates:
                    cleaner.standardize_dates()
                    
                # Handle Missing Values
                cleaner.handle_missing_values(self.strategy, self.custom_val)
                
                # Drop all-empty rows/cols & duplicates (Standard SQL prep)
                df = cleaner.df.dropna(how='all', axis=0).dropna(how='all', axis=1)
                df = df.drop_duplicates()
                
                cleaned_data[sheet_name] = df
                current_sheet += 1

            self.progress_update.emit(100, "✅ Pipeline finished successfully!")
            
            summary = f"Processed {total_sheets} sheet(s) successfully."
            self.finished_success.emit(cleaned_data, summary)

        except Exception as e:
            self.error_occurred.emit(str(e))

# ==========================================
# 3. THE LOADING DIALOG
# ==========================================
class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing...")
        self.setFixedSize(300, 100)
        self.setModal(True) # Blocks input to main window while processing
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        
        layout = QVBoxLayout()
        self.label = QLabel("Processing data, please wait...")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.progress = QProgressBar()
        self.progress.setValue(0)
        
        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        self.setLayout(layout)
        
        self.setStyleSheet("""
            QDialog { background-color: white; border: 2px solid #ff8c42; border-radius: 8px;}
            QLabel { font-weight: bold; color: #333; }
            QProgressBar { border: 1px solid #bbb; border-radius: 4px; text-align: center; }
            QProgressBar::chunk { background-color: #10B981; }
        """)

    def update_progress(self, val, msg):
        self.progress.setValue(val)
        self.label.setText(msg)

# ==========================================
# 4. THE MAIN APPLICATION
# ==========================================
from PyQt6.QtGui import QIcon 
class CleanSheetsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        icon_path= get_resource_path("icon.ico") 
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("🧼 Clean Sheets - Local Data Cleaner")
        self.setMinimumSize(550, 600)
        self.file_path = None
        self.cleaned_data = None

        layout = QVBoxLayout()

        self.title = QLabel("Automated pipeline for SQL-ready datasets.")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.title)

        # Upload
        self.btn_upload = QPushButton("📂 Upload CSV or Excel file")
        self.btn_upload.setMinimumHeight(40)
        self.btn_upload.clicked.connect(self.load_file)
        layout.addWidget(self.btn_upload)

        # Excel Sheet Selector (Hidden by default)
        self.sheet_layout = QHBoxLayout()
        self.sheet_combo = QComboBox()
        self.sheet_combo.setVisible(False)
        self.sheet_layout.addWidget(QLabel("Select Sheet:"))
        self.sheet_layout.addWidget(self.sheet_combo)
        layout.addLayout(self.sheet_layout)

        # Settings
        self.settings_layout = QHBoxLayout()
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(["Auto (Median/Mode)", "Fill with 0", "Custom Value"])
        self.strategy_combo.currentTextChanged.connect(self.toggle_custom_input)
        
        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("Custom value...")
        self.custom_input.setEnabled(False)

        self.chk_dates = QCheckBox("Standardize Dates to YYYY-MM-DD")
        self.chk_dates.setChecked(True)

        self.settings_layout.addWidget(QLabel("Missing Value:"))
        self.settings_layout.addWidget(self.strategy_combo)
        self.settings_layout.addWidget(self.custom_input)
        layout.addLayout(self.settings_layout)
        layout.addWidget(self.chk_dates)

        # Console
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setText("Waiting for file upload...")
        layout.addWidget(self.log_console)

        # Action Buttons
        self.btn_clean = QPushButton("🚀 Run Cleaning Pipeline")
        self.btn_clean.setMinimumHeight(40)
        self.btn_clean.clicked.connect(self.start_processing)
        self.btn_clean.setEnabled(False) 
        layout.addWidget(self.btn_clean)

        self.btn_save = QPushButton("📥 Download Cleaned Data")
        self.btn_save.setMinimumHeight(40)
        self.btn_save.setStyleSheet("background-color: #10B981; color: white; font-weight: bold;")
        self.btn_save.clicked.connect(self.save_file)
        self.btn_save.setEnabled(False)
        layout.addWidget(self.btn_save)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def log(self, message):
        self.log_console.append(message)

    def toggle_custom_input(self, text):
        self.custom_input.setEnabled(text == "Custom Value")

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Data File", "", "Data Files (*.csv *.xlsx *.xls)")
        if not file_path: return

        self.file_path = file_path
        self.log_console.clear()
        self.log(f"✅ Loaded: {file_path.split('/')[-1]}")

        # Handle Excel Sheets dynamically
        if file_path.endswith(('.xlsx', '.xls')):
            try:
                xls = pd.ExcelFile(self.file_path)
                self.sheet_combo.clear()
                self.sheet_combo.addItem("All Sheets")
                self.sheet_combo.addItems(xls.sheet_names)
                self.sheet_combo.setVisible(True)
            except Exception as e:
                self.log(f"❌ Error reading Excel file: {e}")
                return
        else:
            self.sheet_combo.setVisible(False)

        self.btn_clean.setEnabled(True)
        self.btn_save.setEnabled(False)

    def start_processing(self):
        if not self.file_path: return

        self.btn_clean.setEnabled(False)
        self.log("\n--- Starting Cleaning Pipeline ---")
        
        # 1. Setup Loading Dialog
        self.loading_dialog = LoadingDialog(self)
        self.loading_dialog.show()

        # 2. Initialize QThread Worker
        sheet_sel = self.sheet_combo.currentText() if self.sheet_combo.isVisible() else None
        strategy = self.strategy_combo.currentText()
        custom_val = self.custom_input.text()
        clean_dates = self.chk_dates.isChecked()

        self.worker = CleaningWorker(self.file_path, sheet_sel, strategy, custom_val, clean_dates)
        
        # 3. Connect Signals
        self.worker.progress_update.connect(self.update_progress)
        self.worker.finished_success.connect(self.processing_complete)
        self.worker.error_occurred.connect(self.processing_error)

        # 4. Start Thread
        self.worker.start()

    def update_progress(self, val, msg):
        self.loading_dialog.update_progress(val, msg)
        self.log(msg)

    def processing_complete(self, data, summary_msg):
        self.cleaned_data = data
        self.loading_dialog.accept() # Closes the modal
        self.log(f"\n{summary_msg}")
        self.btn_clean.setEnabled(True)
        self.btn_save.setEnabled(True)
        QMessageBox.information(self, "Success", "Data cleaning complete!")

    def processing_error(self, err_msg):
        self.loading_dialog.reject()
        self.log(f"\n❌ CRITICAL ERROR: {err_msg}")
        self.btn_clean.setEnabled(True)
        QMessageBox.critical(self, "Error", f"An error occurred:\n{err_msg}")

    def save_file(self):
        if not self.cleaned_data: return

        # If it's a single dataframe, save as CSV. If multiple sheets, save as Excel.
        if len(self.cleaned_data) == 1:
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Cleaned Data", "cleaned_dataset.csv", "CSV Files (*.csv)")
            if save_path:
                try:
                    list(self.cleaned_data.values())[0].to_csv(save_path, index=False)
                    self.log(f"\n💾 Saved to: {save_path}")
                except Exception as e: self.log(f"❌ Error: {e}")
        else:
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Cleaned Data", "cleaned_workbook.xlsx", "Excel Files (*.xlsx)")
            if save_path:
                try:
                    with pd.ExcelWriter(save_path) as writer:
                        for sheet_name, df in self.cleaned_data.items():
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                    self.log(f"\n💾 Saved all sheets to: {save_path}")
                except Exception as e: self.log(f"❌ Error: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
app.setStyleSheet("""
    QWidget {
        background-color: #1e293b;   /* Deep Slate */
        color: #f8fafc;              /* Off-white text */
    }

    QPushButton {
        background-color: #334155;   /* Lighter Slate */
        color: #f8fafc;
        border: 1px solid #475569;
        border-radius: 6px;
        padding: 6px;
        font-weight: bold;
    }

    QPushButton:hover {
        background-color: #475569;
    }

    /* The 'Download' button stays green for that 'Success' feel */
    QPushButton#btn_save { 
        background-color: #059669; 
        color: white;
    }

    QTextEdit, QLineEdit, QComboBox {
        background-color: #0f172a;   /* Darker Slate */
        color: #e2e8f0;
        border: 1px solid #334155;
        border-radius: 5px;
        padding: 4px;
    }

    QProgressBar {
        border: 1px solid #334155;
        border-radius: 5px;
        text-align: center;
        background-color: #0f172a;
    }

    QProgressBar::chunk {
        background-color: #10b981;   /* Emerald Green */
    }
    
    QCheckBox {
        color: #cbd5e1;
    }
""") 
window = CleanSheetsApp()
window.show()
sys.exit(app.exec())