Clean Sheets: Automated Data Cleaning Pipeline
Clean Sheets is a desktop-based data processing application designed to streamline the preparation of messy datasets for SQL injection or analytical workflows. Built with Python and PyQt6, it provides a high-performance, asynchronous environment for standardizing Excel and CSV files.

Core Features
Asynchronous Processing: Utilizes multi-threading to ensure the UI remains responsive during heavy data operations.

Intelligent Null Handling: Automated imputation of missing values using median or mode calculations based on data distribution.

Date Standardization: A dedicated pipeline to convert various date formats into a unified YYYY-MM-DD format for database compatibility.

Multi-Sheet Support: Capability to process individual sheets within complex Excel workbooks.

Local-First Architecture: Designed for privacy and speed by processing all data locally on the user's machine.

Technical Stack
GUI Framework: PyQt6 (Custom Slate Grey and Sunset Orange themes).

Data Engine: Pandas and NumPy.

Distribution: Bundled as a standalone Windows executable using PyInstaller.

Installation and Usage
To use the standalone version of the application:

Navigate to the Releases section of this repository.

Download the CleanSheets.exe file.

Run the executable. No local Python installation is required as all dependencies are bundled within the application 

Performance Considerations

Initial Startup: Users may experience a brief delay (3–5 seconds) when launching the executable. This is an intentional design choice where the application pre-initializes the Pandas and NumPy environments and pre-loads resource paths to ensure near-instantaneous performance once data cleaning operations begin.

👤 Author

Devansh
