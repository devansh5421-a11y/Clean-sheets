import sys
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout,
                             QWidget, QFileDialog, QLabel, QTextEdit, QMessageBox)
from PyQt6.QtCore import Qt

class CleanSheetsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧼 Clean Sheets - Local Data Cleaner")
        self.setMinimumSize(500, 450)
        self.df_raw = None
        self.df_clean = None

        layout = QVBoxLayout()

        self.title = QLabel("Automated pipeline for SQL-ready datasets.")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.title)

        self.btn_upload = QPushButton("📂 Upload CSV or Excel file")
        self.btn_upload.setMinimumHeight(40)
        self.btn_upload.clicked.connect(self.load_file)
        layout.addWidget(self.btn_upload)

        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setText("Waiting for file upload...")
        self.log_console.setStyleSheet("background-color: #f4f4f4; border-radius: 5px;")
        layout.addWidget(self.log_console)

        self.btn_clean = QPushButton("🚀 Run Cleaning Pipeline")
        self.btn_clean.setMinimumHeight(40)
        self.btn_clean.clicked.connect(self.process_data)
        self.btn_clean.setEnabled(False) 
        layout.addWidget(self.btn_clean)

        self.btn_save = QPushButton("📥 Download Cleaned CSV")
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

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Data File", "", "Data Files (*.csv *.xlsx *.xls)")
        if not file_path:
            return

        try:
            if file_path.endswith('.csv'):
                self.df_raw = pd.read_csv(file_path)
            else:
                self.df_raw = pd.read_excel(file_path)

            self.log_console.clear()
            self.log(f"✅ Successfully loaded: {file_path.split('/')[-1]}")
            
            self.log("\n--- Initial Data Summary ---")
            self.log(f"📊 Total Rows: {self.df_raw.shape[0]} | Total Columns: {self.df_raw.shape[1]}")
            self.log(f"⚠️ Missing Values: {self.df_raw.isnull().sum().sum()}")
            self.log(f"⚠️ Duplicate Rows: {self.df_raw.duplicated().sum()}")
            
            self.btn_clean.setEnabled(True)
            self.btn_save.setEnabled(False)
        except Exception as e:
            self.log(f"❌ Error loading file: {str(e)}")

    def process_data(self):
        if self.df_raw is None: return

        self.log("\n--- Starting Cleaning Pipeline ---")
        df = self.df_raw.copy()
        steps = []
        initial_rows = len(df)
        initial_missing = df.isnull().sum().sum()
        initial_dupes = df.duplicated().sum()

        try:
            # 1. Normalize columns
            try:
                new_cols = []
                seen = set()
                for c in df.columns:
                    base_name = str(c).lower().strip().replace(" ", "_")
                    clean_c = "".join(char for char in base_name if char.isalnum() or char == "_")
                    if not clean_c: clean_c = "column"
                    original_clean_c = clean_c
                    counter = 1
                    while clean_c in seen:
                        clean_c = f"{original_clean_c}_{counter}"
                        counter += 1
                    seen.add(clean_c)
                    new_cols.append(clean_c)
                df.columns = new_cols
                steps.append("✅ Normalized column names for SQL")
            except Exception as e: self.log(f"⚠️ Error cleaning columns: {e}")

            # 2 & 3. Drop empty and duplicates
            df = df.dropna(how='all')
            df = df.drop_duplicates()

            # 4. Strip whitespace
            try:
                str_cols = df.select_dtypes(include=['object']).columns
                for col in str_cols:
                    df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
                steps.append("✅ Trimmed whitespace safely")
            except Exception as e: self.log(f"⚠️ Error cleaning strings: {e}")

            # 5. Fill missing
            try:
                for col in df.select_dtypes(include=['number']).columns:
                    if df[col].isnull().any():
                        df[col] = df[col].fillna(df[col].median())
                for col in df.select_dtypes(include=['object']).columns:
                    if df[col].isnull().any():
                        df[col] = df[col].fillna('unknown')
                steps.append("✅ Filled missing values")
            except Exception as e: self.log(f"⚠️ Error filling missing values: {e}")

            self.df_clean = df
            for step in steps:
                self.log(step)

            final_rows = len(df)
            final_missing = df.isnull().sum().sum()
            
            self.log("\n--- Cleaning Summary ---")
            self.log(f"📉 Rows: {initial_rows} ➔ {final_rows}")
            self.log(f"🗑️ Duplicates Removed: {initial_dupes}")
            self.log(f"🩹 Missing Values Fixed: {initial_missing} ➔ {final_missing}")

            self.btn_save.setEnabled(True)

        except Exception as e:
            self.log(f"\n❌ CRITICAL ERROR: {str(e)}")

    def save_file(self):
        if self.df_clean is None: return

        save_path, _ = QFileDialog.getSaveFileName(self, "Save Cleaned Data", "cleaned_dataset.csv", "CSV Files (*.csv)")
        if save_path:
            try:
                self.df_clean.to_csv(save_path, index=False, encoding='utf-8')
                self.log(f"\n💾 Successfully saved to: {save_path}")
                QMessageBox.information(self, "Success", "File saved successfully!")
            except Exception as e:
                self.log(f"❌ Error saving file: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    window = CleanSheetsApp()
    window.show()
    sys.exit(app.exec())
    