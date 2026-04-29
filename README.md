🧼 Clean Sheets — Data Cleaner App

A simple desktop app that cleans messy CSV or Excel files automatically.

---

🚀 What it does

- Upload CSV or Excel file
- Cleans the data:
  - Fixes column names (lowercase, no spaces)
  - Removes empty rows
  - Removes duplicates
  - Trims extra spaces in text
  - Fills missing values
- Download cleaned file as CSV

---

▶️ How to run (Python version)

1. Install required libraries:

pip install pandas PyQt6 openpyxl

2. Run the app:

python clean_sheets.py

---

💻 How to use

1. Click Upload CSV or Excel file
2. Click Run Cleaning Pipeline
3. Click Download Cleaned CSV

---

⚙️ Make it an .exe (Windows app)

1. Install PyInstaller:

pip install pyinstaller

2. Build the app:

python -m PyInstaller --onefile --windowed clean_sheets.py

3. Your app will be here:

dist/clean_sheets.exe

You can now run it like a normal app 👍

---

📌 Notes

- Works locally (no internet needed)
- Excel files need "openpyxl"
- File size may increase when converted to .exe

---

🧠 Future improvements

- Better data fixing (like wrong values in columns)
- Preview table before download
- More smart cleaning

---

👤 Author

Devansh
