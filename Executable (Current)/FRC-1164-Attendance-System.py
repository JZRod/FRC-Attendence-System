import sys
import os
import csv
import datetime
import json
import webbrowser
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QScrollArea, QFrame, QTabWidget,
    QTableWidget, QTableWidgetItem, QListWidget, QListWidgetItem, QHeaderView,
    QMessageBox, QInputDialog, QFileDialog, QColorDialog, QGroupBox, QSplitter,
    QTreeWidget, QTreeWidgetItem, QProgressBar, QStatusBar, QMenuBar, QMenu,
    QDialog, QDialogButtonBox, QFormLayout, QComboBox, QCheckBox, QSpinBox,
    QDoubleSpinBox, QRadioButton, QButtonGroup, QTextBrowser, QPlainTextEdit, QSizePolicy
)
from PyQt6.QtGui import (
    QPixmap, QIcon, QFont, QColor, QPalette, QPainter, QBrush, QPen,
    QAction, QKeySequence, QImage, QTransform
)
from PyQt6.QtCore import (
    Qt, QTimer, QDateTime, QThread, pyqtSignal, QRect, QSize, QPoint,
    QPropertyAnimation, QEasingCurve, QUrl, QMimeData, QEvent
)
import requests  # for potential web features

# Pillow import with backward-friendly fallbacks
try:
    from PIL import Image, ImageQt
    PIL_AVAILABLE = True
    try:
        RESAMPLE_METHOD = Image.LANCZOS
    except Exception:
        try:
            RESAMPLE_METHOD = Image.ANTIALIAS
        except Exception:
            RESAMPLE_METHOD = None
except Exception:
    Image = None
    ImageQt = None
    PIL_AVAILABLE = False
    RESAMPLE_METHOD = None

# ---------------- Global Variables ----------------
attendance_data = []  # List of dicts: [{'Date': '', 'Name': '', 'Status': ''}, ...]
guests_data = []  # List of dicts for guests
DATA_FOLDER = "data"
ASSETS_FOLDER = "assets"
DEFAULT_FILENAME = os.path.join(DATA_FOLDER, "attendance.csv")
STUDENTS_FILE = os.path.join(DATA_FOLDER, "students.json")
CONFIG_FILE = os.path.join(DATA_FOLDER, "config.json")
LOGO_FILE = os.path.join(ASSETS_FOLDER, "logo.png")
GEAR_FILE = os.path.join(ASSETS_FOLDER, "gear.png")
ICON_FILE = os.path.join(ASSETS_FOLDER, "icon.ico")
GUESTS_FILE = os.path.join(DATA_FOLDER, "guests.csv")

DEFAULT_CONFIG = {
    "admin_pin": "1234",
    "header_color": "#5D3FD3",
    "logo_file": LOGO_FILE,
    "csv_file": DEFAULT_FILENAME,
    "backup_retention_days": 30,
    "backup_interval_hours": 1
}

HEADER_HEIGHT = 50

# ---------------- Storage Helpers ----------------
def get_csv_file():
    """Get the current CSV file path from config, with fallback to default"""
    test_csv = os.environ.get("TEST_CSV_FILE")
    if test_csv:
        return test_csv
    try:
        config = load_config()
        csv_path = config.get("csv_file", DEFAULT_FILENAME)
        csv_dir = os.path.dirname(csv_path)
        if csv_dir and not os.path.exists(csv_dir):
            os.makedirs(csv_dir, exist_ok=True)
        return csv_path
    except Exception:
        return DEFAULT_FILENAME


def get_students_file():
    """Get current students.json path from config with fallback"""
    try:
        config = load_config()
        path = config.get("students_file", STUDENTS_FILE)
        dirn = os.path.dirname(path)
        if dirn and not os.path.exists(dirn):
            os.makedirs(dirn, exist_ok=True)
        return path
    except Exception:
        return STUDENTS_FILE


def get_guests_file():
    """Get current guests.csv path from config with fallback"""
    try:
        config = load_config()
        path = config.get("guests_file", GUESTS_FILE)
        dirn = os.path.dirname(path)
        if dirn and not os.path.exists(dirn):
            os.makedirs(dirn, exist_ok=True)
        return path
    except Exception:
        return GUESTS_FILE

def load_attendance_data():
    """Load attendance data from CSV into global list"""
    global attendance_data
    csv_file = get_csv_file()
    attendance_data = []
    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                attendance_data.append(row)
    except FileNotFoundError:
        pass  # File doesn't exist yet
    except Exception as e:
        print("Error loading attendance data:", e)

def save_attendance_data():
    """Save global attendance data to CSV"""
    global attendance_data
    csv_file = get_csv_file()
    try:
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            if attendance_data:
                writer = csv.DictWriter(f, fieldnames=["Date", "Name", "Status"])
                writer.writeheader()
                writer.writerows(attendance_data)
    except Exception as e:
        print("Error saving attendance data:", e)

def load_guests_data():
    """Load guests data from CSV into global list"""
    global guests_data
    guests_file = get_guests_file()
    guests_data = []
    try:
        with open(guests_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                guests_data.append(row)
    except FileNotFoundError:
        pass
    except Exception as e:
        print("Error loading guests data:", e)

def save_guests_data():
    """Save global guests data to CSV"""
    global guests_data
    guests_file = get_guests_file()
    try:
        with open(guests_file, "w", newline="", encoding="utf-8") as f:
            if guests_data:
                writer = csv.DictWriter(f, fieldnames=["Date", "Name", "Email"])
                writer.writeheader()
                writer.writerows(guests_data)
    except Exception as e:
        print("Error saving guests data:", e)

def init_files():
    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(ASSETS_FOLDER, exist_ok=True)

    # --- Migration: if user has students/guests in Documents, copy into data/ and update config ---
    try:
        cfg = load_config()
        user_home = os.path.expanduser("~")
        docs_path = os.path.join(user_home, "Documents")

        def _should_migrate(path):
            try:
                if not path:
                    return False
                ap = os.path.abspath(path)
                return os.path.exists(ap) and os.path.commonpath([ap, os.path.abspath(docs_path)]) == os.path.abspath(docs_path)
            except Exception:
                return False

        migrated = False
        # Students
        students_cfg = cfg.get("students_file")
        if _should_migrate(students_cfg):
            try:
                dest = STUDENTS_FILE
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                import shutil
                shutil.copy2(os.path.abspath(students_cfg), dest)
                cfg["students_file"] = dest
                migrated = True
            except Exception:
                pass

        # Guests
        guests_cfg = cfg.get("guests_file")
        if _should_migrate(guests_cfg):
            try:
                dest = GUESTS_FILE
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                import shutil
                shutil.copy2(os.path.abspath(guests_cfg), dest)
                cfg["guests_file"] = dest
                migrated = True
            except Exception:
                pass

        if migrated:
            try:
                save_config(cfg)
            except Exception:
                pass
    except Exception:
        pass

    # Get the current CSV file path
    csv_file = get_csv_file()
    
    # Ensure CSV header contains Status column
    if not os.path.exists(csv_file):
        try:
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Name", "Status"])
        except Exception as e:
            print("Could not create attendance CSV:", e)

    students_file = get_students_file()
    if not os.path.exists(students_file):
        try:
            os.makedirs(os.path.dirname(students_file), exist_ok=True) if os.path.dirname(students_file) else None
            with open(students_file, "w", encoding="utf-8") as f:
                json.dump(["placeholder1", "placeholder2", "placeholder3", "placeholder4"], f, indent=2)
        except Exception as e:
            print("Could not create students.json:", e)

    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
        except Exception as e:
            print("Could not create config.json:", e)
    # Ensure guests CSV exists
    guests_file = get_guests_file()
    if not os.path.exists(guests_file):
        try:
            os.makedirs(os.path.dirname(guests_file), exist_ok=True) if os.path.dirname(guests_file) else None
            with open(guests_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Name", "Email"])
        except Exception as e:
            print("Could not create guests CSV:", e)

def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Ensure csv_file is in config for backward compatibility
            if "csv_file" not in config:
                config["csv_file"] = DEFAULT_FILENAME
            return config
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print("save_config error:", e)
        return False

def load_students():
    try:
        sf = get_students_file()
        with open(sf, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_students(students):
    try:
        sf = get_students_file()
        os.makedirs(os.path.dirname(sf), exist_ok=True) if os.path.dirname(sf) else None
        with open(sf, "w", encoding="utf-8") as f:
            json.dump(students, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print("save_students error:", e)
        return False

def already_checked_in(name, date_iso):
    """
    Check if a person is already marked present for a SPECIFIC DATE.
    This ensures daily attendance is tracked independently - each day has its own records.
    Previous days' attendance will never be affected by checking today's attendance.
    """
    global attendance_data
    for row in attendance_data:
        if row.get("Date") == date_iso and row.get("Name") == name and row.get("Status") == "Present":
            return True
    return False

def remove_attendance(name, date_iso):
    """
    Remove attendance for a person on a SPECIFIC DATE only.
    This preserves all other dates' attendance records - only the matching
    date + name combination is removed. Previous days remain unchanged.
    """
    global attendance_data
    for i, row in enumerate(attendance_data):
        if (row.get("Date") == date_iso and row.get("Name") == name and
                row.get("Status") == "Present"):
            del attendance_data[i]
            save_attendance_data()
            return True
    return False


def get_last_recorded_date():
    """
    Return the last non-empty Date value recorded in the CSV, or None if no records.
    """
    global attendance_data
    for row in reversed(attendance_data):
        d = (row.get("Date") or "").strip()
        if d:
            return d
    return None


def append_new_day_section(date_iso):
    """
    Append a small marker/section row for a new day in the CSV. This makes it easy
    to visually separate days inside one CSV file while still keeping all data.

    The marker row will look like: [date_iso, '--- NEW DAY ---', '', '']
    """
    global attendance_data
    csv_file = get_csv_file()
    try:
        # Ensure file exists with header
        if not os.path.exists(csv_file):
            os.makedirs(os.path.dirname(csv_file), exist_ok=True) if os.path.dirname(csv_file) else None
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Name", "Status"])

        # Only append the marker if the last recorded date isn't already this date
        last = get_last_recorded_date()
        if last == date_iso:
            return True

        new_row = {"Date": date_iso, "Name": "--- NEW DAY ---", "Status": ""}
        attendance_data.append(new_row)
        save_attendance_data()
        return True
    except Exception as e:
        print("append_new_day_section error:", e)
        return False

def mark_attendance(name, status="Present"):
    """
    Mark attendance for TODAY only. Each day's attendance is completely independent.
    - Uses today's date (datetime.date.today().isoformat()) 
    - Only checks and modifies today's records
    - Previous days' attendance is never touched
    Toggle behavior: clicking again removes today's attendance only.
    """
    csv_file = get_csv_file()
    today = datetime.date.today().isoformat()
    # Ensure the CSV has a new-day section when the date changes so each day is separated
    try:
        last = get_last_recorded_date()
        if last != today:
            append_new_day_section(today)
    except Exception:
        pass
    if status == "Present" and already_checked_in(name, today):
        removed = remove_attendance(name, today)
        if removed:
            return False, "{0} removed from today's attendance.".format(name)
        else:
            return False, "{0} is already marked Present today.".format(name)
    try:
        new_row = {"Date": today, "Name": name, "Status": status}
        attendance_data.append(new_row)
        save_attendance_data()
        return True, "Welcome, {0}! You're marked {1}.".format(name, status)
    except Exception as e:
        print("mark_attendance error:", e)
        return False, "Failed to mark attendance: {0}".format(e)

# ---------------- GUI App ----------------
class AttendanceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FRC Attendance System")
        self.setMinimumSize(800, 600)

        # Load configuration
        self.config = load_config()
        self.admin_pin = self.config.get("admin_pin", "1164")
        self.header_color = self.config.get("header_color", "#5D3FD3")
        self.logo_file = self.config.get("logo_file", LOGO_FILE)
        self.csv_file = self.config.get("csv_file", DEFAULT_FILENAME)
        # Backup settings
        self.backup_location = self.config.get("backup_location", "")
        self.backup_enabled = self.config.get("backup_enabled", False)
        self.backup_retention_days = self.config.get("backup_retention_days", 30)
        self.backup_interval_hours = self.config.get("backup_interval_hours", 1)
        self.backup_job = None
        self.last_backup = None

        # Fullscreen toggle
        self.fullscreen = False

        self.setup_ui()
        self.setup_fullscreen()
        self.setup_logo()

        # Track current date so we can detect day changes while the app is running
        self.current_date = datetime.date.today().isoformat()
        # Show the current date in the header
        try:
            self.update_title_with_date()
        except Exception:
            pass

        # Load data
        load_attendance_data()
        load_guests_data()

        # Load students
        self.students = load_students()
        self.filtered_students = self.students.copy()

        self.build_student_buttons()

        # Start periodic daily check (runs every 30 seconds) to detect day changes
        try:
            self.schedule_daily_check()
        except Exception:
            pass

        # If backups were enabled in config, start them
        try:
            if self.backup_enabled and self.backup_location:
                self.start_backups()
        except Exception:
            pass

    def setup_ui(self):
        """Setup the main user interface"""
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: black;
                color: white;
            }
            QWidget {
                background-color: black;
                color: white;
            }
            QPushButton {
                background-color: #333333;
                color: white;
                border: 2px solid #555555;
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1A1A1A;
            }
            QPushButton:pressed {
                background-color: #000000;
            }
            QLineEdit {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #555555;
                padding: 4px;
                font-size: 14px;
            }
            QLabel {
                color: white;
            }
        """)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        self.setup_header(main_layout)

        # Guest Sign In
        self.setup_guest_section(main_layout)

        # Search bar
        self.setup_search_section(main_layout)

        # Student list
        self.setup_student_section(main_layout)

        # Setup keyboard shortcuts
        self.setup_shortcuts()

    def setup_header(self, parent_layout):
        """Setup the header section"""
        self.header_widget = QWidget()
        self.header_widget.setFixedHeight(HEADER_HEIGHT)
        self.header_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.header_widget.setStyleSheet(f"background-color: {self.header_color};")

        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(12, 0, 12, 0)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Logo placeholder
        self.logo_label = QLabel()
        logo_size = HEADER_HEIGHT
        self.logo_label.setFixedSize(logo_size, logo_size)
        header_layout.addWidget(self.logo_label)

        # Title
        self.title_label = QLabel("Tap Your Name to Check In")
        self.title_label.setStyleSheet(f"""
            color: white;
            font-size: 20px;
            font-weight: bold;
            background-color: {self.header_color};
        """)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.title_label, 1)

        # Admin button
        self.setup_admin_button(header_layout)

        parent_layout.addWidget(self.header_widget)

    def setup_guest_section(self, parent_layout):
        """Setup the guest sign-in section"""
        guest_widget = QWidget()
        guest_layout = QHBoxLayout(guest_widget)
        guest_layout.setContentsMargins(12, 10, 12, 0)

        self.guest_btn = QPushButton("Guest Sign In — Tap to Enter Your Name")
        self.guest_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                border: 2px solid #555555;
            }
            QPushButton:hover {
                background-color: #1A1A1A;
            }
        """)
        self.guest_btn.clicked.connect(self.guest_sign_in)
        guest_layout.addWidget(self.guest_btn)

        parent_layout.addWidget(guest_widget)

    def setup_search_section(self, parent_layout):
        """Setup the search section"""
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(12, 3, 12, 3)

        # Search icon
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 16px; padding: 4px;")
        search_layout.addWidget(search_icon)

        # Search input
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Search for a student...")
        self.search_entry.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: white;
                border: 2px solid #9a9a9a;
                border-top: 2px solid #9a9a9a;
                border-left: 2px solid #9a9a9a;
                border-right: none;
                border-bottom: none;
                padding: 8px;
                font-size: 14px;
            }
        """)
        self.search_entry.textChanged.connect(self.on_search_change)
        search_layout.addWidget(self.search_entry, 1)

        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFixedWidth(80)
        self.clear_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(self.clear_btn)

        parent_layout.addWidget(search_widget)

    def setup_student_section(self, parent_layout):
        """Setup the scrollable student list section"""
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: black;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 16px;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 8px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #777777;
            }
        """)

        # Container for student buttons
        self.student_widget = QWidget()
        self.student_layout = QGridLayout(self.student_widget)
        self.student_layout.setContentsMargins(12, 15, 12, 12)
        self.student_layout.setSpacing(4)

        self.scroll_area.setWidget(self.student_widget)
        parent_layout.addWidget(self.scroll_area)

    def setup_admin_button(self, header_layout):
        """Setup the admin button"""
        self.admin_btn = QPushButton("Admin")
        self.admin_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.header_color};
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid white;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: #1A1A1A;
            }}
        """)
        self.admin_btn.clicked.connect(self.admin_panel)
        header_layout.addWidget(self.admin_btn)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Escape to toggle fullscreen
        escape_action = QAction(self)
        escape_action.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        escape_action.triggered.connect(self.toggle_fullscreen)
        self.addAction(escape_action)

        # F11 to toggle fullscreen
        f11_action = QAction(self)
        f11_action.setShortcut(QKeySequence(Qt.Key.Key_F11))
        f11_action.triggered.connect(self.toggle_fullscreen)
        self.addAction(f11_action)

    def update_title_with_date(self):
        """Update the title label to include the current date for clarity."""
        try:
            d = self.current_date or datetime.date.today().isoformat()
            self.title_label.setText("📌 Tap Your Name to Check In")
        except Exception:
            pass

    def schedule_daily_check(self):
        """Schedule the next daily check (non-blocking)."""
        # Check every 30 seconds using QTimer
        self.daily_timer = QTimer(self)
        self.daily_timer.timeout.connect(self._daily_check)
        self.daily_timer.start(30 * 1000)  # 30 seconds

    def _daily_check(self):
        """Check whether the date has rolled over; if so, handle it."""
        try:
            today = datetime.date.today().isoformat()
            if today != self.current_date:
                self.on_day_change(today)
        except Exception as e:
            print("_daily_check error:", e)

    def on_day_change(self, new_date_iso):
        """
        Handle rollover to a new day while the app is running:
        - Append a new-day marker to the CSV
        - Update in-memory current_date and the header
        - Rebuild the student buttons so today's attendance appears reset
        """
        try:
            self.current_date = new_date_iso
            # append a new day section to CSV so data is visually separated
            try:
                append_new_day_section(new_date_iso)
            except Exception:
                pass
            # Update header and UI to reflect the new day
            try:
                self.update_title_with_date()
            except Exception:
                pass
            # Rebuild buttons so checked marks for previous day are not shown
            try:
                self.build_student_buttons()
            except Exception:
                pass
            print("Day changed to {0}. Attendance reset for the new day.".format(new_date_iso))
        except Exception as e:
            print("on_day_change error:", e)

    # ---------------- Helpers ----------------
    def setup_fullscreen(self):
        """Setup fullscreen with cross-platform compatibility"""
        try:
            # Start in fullscreen mode
            self.showFullScreen()
            self.fullscreen = True
        except Exception as e:
            print("Fullscreen setup warning:", e)

    def setup_logo(self):
        """Setup logo with PIL fallback"""
        try:
            if PIL_AVAILABLE and Image and os.path.exists(self.logo_file):
                max_logo = HEADER_HEIGHT
                img = Image.open(self.logo_file)
                if RESAMPLE_METHOD:
                    img.thumbnail((max_logo, max_logo), RESAMPLE_METHOD)
                else:
                    img = img.resize((max_logo, max_logo))
                qt_img = ImageQt.ImageQt(img)
                pixmap = QPixmap.fromImage(qt_img)
                self.logo_label.setPixmap(pixmap)
            else:
                raise Exception("Logo not available")
        except Exception as e:
            print("Logo loading failed:", e)
            self.logo_label.setText("LOGO")
            self.logo_label.setStyleSheet(f"""
                color: white;
                font-size: 24px;
                font-weight: bold;
                background-color: {self.header_color};
                border: 2px solid white;
            """)
            self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _on_mousewheel_windows(self, event):
        try:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showMaximized()
            self.fullscreen = False
        else:
            self.showFullScreen()
            self.fullscreen = True

    # ---------------- Search ----------------
    def on_search_change(self):
        """Handle search text changes"""
        search_text = self.search_entry.text().lower().strip()
        if not search_text or search_text == "search for a student...":
            self.filtered_students = self.students.copy()
        else:
            self.filtered_students = [s for s in self.students if search_text in s.lower()]
        self.build_student_buttons()

    def clear_search(self):
        """Clear search and show all students"""
        self.search_entry.clear()
        self.search_entry.setPlaceholderText("Search for a student...")
        self.filtered_students = self.students.copy()
        self.build_student_buttons()

    # ---------------- Student Buttons ----------------
    def build_student_buttons(self):
        """Build student buttons grid using filtered students list"""
        # Clear existing buttons
        for i in reversed(range(self.student_layout.count())):
            widget = self.student_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        today = datetime.date.today().isoformat()
        sorted_students = sorted(self.filtered_students, key=str.lower)
        COLS = 3

        if not sorted_students:
            no_results = QLabel("No students found matching your search")
            no_results.setStyleSheet("""
                color: white;
                font-size: 16px;
                padding: 50px;
            """)
            no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.student_layout.addWidget(no_results, 0, 0, 1, COLS)
            return

        row, col = 0, 0
        # Choose a slightly smaller height when fullscreen
        btn_height = 80 if self.fullscreen else 60

        for name in sorted_students:
            checked = already_checked_in(name, today)
            # plain name (no emoji/checkmark). When checked, persistently show #326B20
            bg_color = "#326B20" if checked else "#333333"
            btn = QPushButton(name)
            btn.setFixedHeight(btn_height)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    border: 3px solid #555555;
                    padding: 8px;
                }}
                QPushButton:hover {{
                    background-color: #1A1A1A;
                }}
                QPushButton:pressed {{
                    background-color: #000000;
                }}
            """)
            btn.clicked.connect(lambda checked, n=name: self.checkin(n))
            self.student_layout.addWidget(btn, row, col)
            col += 1
            if col >= COLS:
                col, row = 0, row + 1

    def checkin(self, name):
        """Handle student check-in (toggle) without popups"""
        # Toggle attendance for the given student name
        mark_attendance(name, "Present")
        self.build_student_buttons()

    def guest_sign_in(self):
        """Handle guest sign-in (no popups)"""
        name, ok = QInputDialog.getText(self, "Guest Sign In", "Enter your name:")
        if not ok or not name or not name.strip():
            return
        name = name.strip()
        email, ok = QInputDialog.getText(self, "Guest Email (optional)", "Enter email (optional):")
        if not ok:
            email = ""
        email = (email.strip() if email and email.strip() else "")

        # Append to guests CSV
        try:
            today = datetime.date.today().isoformat()
            new_guest = {"Date": today, "Name": name, "Email": email}
            guests_data.append(new_guest)
            save_guests_data()
        except Exception as e:
            print("Failed to record guest:", e)

        # Optionally add to students list so they can be checked in easily next time
        # Update in-memory student list and persist.
        if name not in self.students:
            self.students.append(name)
            try:
                save_students(self.students)
            except Exception as e:
                print("Failed to save new student to students.json:", e)

            # Keep the master list sorted so any view built from it is alphabetical
            try:
                self.students.sort(key=str.lower)
            except Exception:
                pass

            # If the admin Students tab/listbox exists, refresh it (safe check).
            try:
                if hasattr(self, 'students_listbox') and self.students_listbox:
                    self.refresh_students_listbox()
            except Exception:
                # Non-fatal; continue to update the main view below
                pass

            # Reapply the current search filter so the new student appears in the buttons.
            try:
                self.on_search_change()
            except Exception:
                # fallback to showing all students
                self.filtered_students = self.students.copy()

            # filtered_students is re-computed by on_search_change(); don't force-insert
            # the new student because build_student_buttons() sorts alphabetically.

        # Mark attendance in main CSV and refresh buttons
        mark_attendance(name, "Present")
        # Rebuild buttons (uses filtered_students which was updated above)
        self.build_student_buttons()

    # ---------------- Admin Panel ----------------
    def admin_panel(self):
        """Open admin panel"""
        pin, ok = QInputDialog.getText(self, "Admin Login", "Enter Admin PIN:", QLineEdit.EchoMode.Password)
        if not ok or pin != self.admin_pin:
            QMessageBox.critical(self, "Error", "Wrong PIN")
            return

        # Create admin dialog
        self.admin_dialog = QDialog(self)
        self.admin_dialog.setWindowTitle("Admin Panel")
        self.admin_dialog.setFixedSize(900, 700)
        self.admin_dialog.setStyleSheet("background-color: black; color: white;")

        layout = QVBoxLayout(self.admin_dialog)

        # Create tab widget
        self.admin_tabs = QTabWidget()
        self.admin_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: black;
            }
            QTabBar::tab {
                background-color: #333333;
                color: white;
                padding: 8px 16px;
                border: 1px solid #555555;
            }
            QTabBar::tab:selected {
                background-color: #5D3FD3;
            }
        """)
        layout.addWidget(self.admin_tabs)

        # Setup tabs
        self.setup_attendance_tab()
        self.setup_guests_tab()
        self.setup_students_tab()
        self.setup_backup_tab()
        self.setup_settings_tab()
        self.update_settings_labels()
        self.update_backup_labels()

        self.admin_dialog.exec()

    def update_backup_labels(self):
        """Update backup tab labels"""
        if hasattr(self, 'backup_path_label'):
            self.backup_path_label.setText(self.backup_location or "Not set")
        if hasattr(self, 'backup_status_label'):
            self.backup_status_label.setText(f"Last backup: {self.last_backup}" if self.last_backup else "Last backup: Never")

    def update_settings_labels(self):
        """Update settings tab labels with current paths"""
        if hasattr(self, 'csv_path_label'):
            self.csv_path_label.setText(get_csv_file())
        if hasattr(self, 'students_path_label'):
            self.students_path_label.setText(get_students_file())
        if hasattr(self, 'guests_path_label'):
            self.guests_path_label.setText(get_guests_file())

    def setup_attendance_tab(self):
        """Setup the attendance tab with a table view"""
        frame = QWidget()
        self.admin_tabs.addTab(frame, "Attendance")

        layout = QVBoxLayout(frame)

        # Table widget
        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(3)
        self.attendance_table.setHorizontalHeaderLabels(["Date", "Name", "Status"])
        self.attendance_table.setStyleSheet("""
            QTableWidget {
                background-color: black;
                color: white;
                gridline-color: #555555;
            }
            QHeaderView::section {
                background-color: #5D3FD3;
                color: white;
                padding: 4px;
                border: 1px solid #555555;
            }
            QTableWidget::item {
                background-color: black;
                color: white;
                border: 1px solid #555555;
            }
            QTableWidget::item:selected {
                background-color: #5D3FD3;
            }
        """)
        self.attendance_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.attendance_table)

        # Load attendance data
        self.refresh_attendance_table()

        # Buttons
        btn_layout = QHBoxLayout()

        download_btn = QPushButton("Download CSV")
        download_btn.clicked.connect(self.download_csv)
        btn_layout.addWidget(download_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_attendance_table)
        btn_layout.addWidget(refresh_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.admin_dialog.close)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def setup_guests_tab(self):
        """Setup the guests tab with a table view"""
        frame = QWidget()
        self.admin_tabs.addTab(frame, "Guests")

        layout = QVBoxLayout(frame)

        # Table widget
        self.guests_table = QTableWidget()
        self.guests_table.setColumnCount(3)
        self.guests_table.setHorizontalHeaderLabels(["Date", "Name", "Email"])
        self.guests_table.setStyleSheet("""
            QTableWidget {
                background-color: black;
                color: white;
                gridline-color: #555555;
            }
            QHeaderView::section {
                background-color: #5D3FD3;
                color: white;
                padding: 4px;
                border: 1px solid #555555;
            }
            QTableWidget::item {
                background-color: black;
                color: white;
                border: 1px solid #555555;
            }
            QTableWidget::item:selected {
                background-color: #5D3FD3;
            }
        """)
        self.guests_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.guests_table)

        # Load guest data
        self.refresh_guests_table()

        # Buttons
        btn_layout = QHBoxLayout()

        download_btn = QPushButton("Download CSV")
        download_btn.clicked.connect(self.download_guests_csv)
        btn_layout.addWidget(download_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_guests_table)
        btn_layout.addWidget(refresh_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.admin_dialog.close)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    # ---------------- Utilities ----------------
    def refresh_attendance_table(self):
        """Refresh the attendance table with current data"""
        global attendance_data
        self.attendance_table.setRowCount(len(attendance_data))
        for row_idx, row_data in enumerate(reversed(attendance_data)):
            self.attendance_table.setItem(row_idx, 0, QTableWidgetItem(row_data.get("Date", "")))
            self.attendance_table.setItem(row_idx, 1, QTableWidgetItem(row_data.get("Name", "")))
            self.attendance_table.setItem(row_idx, 2, QTableWidgetItem(row_data.get("Status", "")))

    def refresh_guests_table(self):
        """Refresh the guests table with current data"""
        global guests_data
        self.guests_table.setRowCount(len(guests_data))
        for row_idx, row_data in enumerate(guests_data):
            self.guests_table.setItem(row_idx, 0, QTableWidgetItem(row_data.get("Date", "")))
            self.guests_table.setItem(row_idx, 1, QTableWidgetItem(row_data.get("Name", "")))
            self.guests_table.setItem(row_idx, 2, QTableWidgetItem(row_data.get("Email", "")))

    def download_guests_csv(self):
        """Download guests CSV file"""
        guests_file = get_guests_file()
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Guests CSV",
                "",
                "CSV files (*.csv);;All files (*.*)"
            )
            if file_path:
                import shutil
                shutil.copy2(guests_file, file_path)
                QMessageBox.information(self, "Success", f"Guests CSV saved to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save Guests CSV: {e}")

    def refresh_guests_tree(self, tree):
        """Populate a Treeview with guest sign-in rows from the guests CSV"""
        global guests_data
        for item in tree.get_children():
            tree.delete(item)
        for row in guests_data:
            tree.insert("", "end", values=(
                row.get("Date", ""),
                row.get("Name", ""),
                row.get("Email", "")
            ))

    def setup_students_tab(self):
        """Setup the students tab"""
        frame = QWidget()
        self.admin_tabs.addTab(frame, "Students")
        layout = QVBoxLayout(frame)

        # List widget for students
        self.students_list = QListWidget()
        self.students_list.setStyleSheet("""
            QListWidget {
                background-color: black;
                color: white;
                border: 1px solid #555555;
            }
            QListWidget::item {
                background-color: black;
                color: white;
                padding: 4px;
            }
            QListWidget::item:selected {
                background-color: #5D3FD3;
            }
        """)
        layout.addWidget(self.students_list)

        # Load students
        self.refresh_students_list()

        # Buttons
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("Add Student")
        add_btn.clicked.connect(self.add_student_pyqt)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton("Edit Student")
        edit_btn.clicked.connect(self.edit_student_pyqt)
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete Student")
        delete_btn.clicked.connect(self.delete_student_pyqt)
        btn_layout.addWidget(delete_btn)

        import_btn = QPushButton("Import Students")
        import_btn.clicked.connect(self.import_students_data_pyqt)
        btn_layout.addWidget(import_btn)

        layout.addLayout(btn_layout)

    def refresh_students_list(self):
        """Refresh the students list widget"""
        self.students_list.clear()
        for student in sorted(self.students, key=str.lower):
            self.students_list.addItem(student)

    def add_student_pyqt(self):
        """Add a new student using PyQt dialogs"""
        name, ok = QInputDialog.getText(self, "Add Student", "Enter student name:")
        if ok and name and name.strip():
            name = name.strip()
            if name not in self.students:
                self.students.append(name)
                if save_students(self.students):
                    self.students.sort(key=str.lower)
                    self.refresh_students_list()
                    self.on_search_change()  # Update main view
                    QMessageBox.information(self, "Success", f"Student '{name}' added successfully!")
                else:
                    QMessageBox.critical(self, "Error", "Failed to save student data")
            else:
                QMessageBox.warning(self, "Warning", f"Student '{name}' already exists!")

    def edit_student_pyqt(self):
        """Edit selected student"""
        current_item = self.students_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a student to edit")
            return

        old_name = current_item.text()
        new_name, ok = QInputDialog.getText(self, "Edit Student", "Edit name:", text=old_name)
        if ok and new_name and new_name.strip() and new_name.strip() != old_name:
            new_name = new_name.strip()
            if new_name not in self.students:
                index = self.students.index(old_name)
                self.students[index] = new_name
                if save_students(self.students):
                    self.refresh_students_list()
                    self.on_search_change()  # Update main view
                    QMessageBox.information(self, "Success", f"Student renamed to '{new_name}'!")
                else:
                    QMessageBox.critical(self, "Error", "Failed to save student data")
            else:
                QMessageBox.warning(self, "Warning", f"Student '{new_name}' already exists!")

    def delete_student_pyqt(self):
        """Delete selected student"""
        current_item = self.students_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a student to delete")
            return

        name = current_item.text()
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Delete student '{name}'?\nThis cannot be undone.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.students.remove(name)
            if save_students(self.students):
                self.refresh_students_list()
                self.on_search_change()  # Update main view
                QMessageBox.information(self, "Success", f"Student '{name}' deleted!")
            else:
                QMessageBox.critical(self, "Error", "Failed to save student data")

    def import_students_data_pyqt(self):
        """Import students data from a JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Students JSON to Import",
            "",
            "JSON files (*.json);;All files (*.*)"
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                imported_students = json.load(f)
            
            if not isinstance(imported_students, list):
                QMessageBox.critical(self, "Error", "Invalid JSON format. Expected a list of students.")
                return
            
            reply = QMessageBox.question(self, "Confirm Import", 
                                       f"Import {len(imported_students)} students? This will replace current student list.",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                if save_students(imported_students):
                    self.students = imported_students
                    self.refresh_students_list()
                    self.on_search_change()  # Update main view
                    QMessageBox.information(self, "Success", "Students data imported successfully!")
                else:
                    QMessageBox.critical(self, "Error", "Failed to save students data")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import students data:\n{e}")

    def setup_backup_tab(self):
        """Setup the backup tab"""
        frame = QWidget()
        self.admin_tabs.addTab(frame, "Backup")
        layout = QVBoxLayout(frame)

        # Backup location
        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("Backup Folder:"))
        self.backup_path_label = QLabel(self.backup_location or "Not set")
        self.backup_path_label.setStyleSheet("color: white; border: 1px solid #555555; padding: 4px;")
        location_layout.addWidget(self.backup_path_label)

        change_btn = QPushButton("Change Folder")
        change_btn.clicked.connect(lambda: self.change_backup_location(self.backup_path_label))
        location_layout.addWidget(change_btn)
        layout.addLayout(location_layout)

        # Backup status
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Last Backup:"))
        self.backup_status_label = QLabel(self.last_backup or "Never")
        self.backup_status_label.setStyleSheet("color: white; border: 1px solid #555555; padding: 4px;")
        status_layout.addWidget(self.backup_status_label)
        layout.addLayout(status_layout)

        # Retention settings
        retention_layout = QHBoxLayout()
        retention_layout.addWidget(QLabel("Retention (days):"))
        self.retention_spin = QSpinBox()
        self.retention_spin.setMinimum(1)
        self.retention_spin.setMaximum(365)
        self.retention_spin.setValue(self.backup_retention_days)
        self.retention_spin.valueChanged.connect(self.change_retention_days)
        retention_layout.addWidget(self.retention_spin)
        layout.addLayout(retention_layout)

        # Interval settings
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Interval (hours):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setMinimum(1)
        self.interval_spin.setMaximum(24)
        self.interval_spin.setValue(self.backup_interval_hours)
        self.interval_spin.valueChanged.connect(self.change_backup_interval)
        interval_layout.addWidget(self.interval_spin)
        layout.addLayout(interval_layout)

        # Backup controls
        control_layout = QHBoxLayout()

        backup_now_btn = QPushButton("Backup Now")
        backup_now_btn.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        backup_now_btn.clicked.connect(lambda: self.perform_backup(notify=True))
        control_layout.addWidget(backup_now_btn)

        if self.backup_enabled:
            toggle_btn = QPushButton("Stop Auto Backup")
            toggle_btn.clicked.connect(self.stop_backups_pyqt)
        else:
            toggle_btn = QPushButton("Start Auto Backup")
            toggle_btn.clicked.connect(self.start_backups_pyqt)
        control_layout.addWidget(toggle_btn)

        layout.addLayout(control_layout)

        # Info
        info_label = QLabel("Auto backup runs hourly when enabled.\nBacks up: attendance.csv, students.json, guests.csv, config.json, assets/")
        info_label.setStyleSheet("color: white; font-size: 12px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

    def change_retention_days(self, value):
        """Update backup retention days"""
        self.backup_retention_days = value
        self.config["backup_retention_days"] = value
        save_config(self.config)

    def change_backup_interval(self, value):
        """Update backup interval hours"""
        self.backup_interval_hours = value
        self.config["backup_interval_hours"] = value
        save_config(self.config)

        # If auto backups are enabled, restart the timer with new interval
        if self.backup_enabled:
            try:
                if hasattr(self, 'backup_timer') and self.backup_timer:
                    self.backup_timer.stop()
                self.backup_timer = QTimer(self)
                self.backup_timer.timeout.connect(self._backup_worker)
                self.backup_timer.start(self.backup_interval_hours * 60 * 60 * 1000)
            except Exception:
                pass

    def start_backups_pyqt(self):
        """Start auto backups"""
        if not self.backup_location:
            QMessageBox.warning(self, "Backup", "Choose a backup folder first")
            return
        if self.start_backups():
            QMessageBox.information(self, "Backup", "Auto backup started (hourly)")
            # Refresh the tab to update button
            self.setup_backup_tab()

    def stop_backups_pyqt(self):
        """Stop auto backups"""
        self.stop_backups()
        QMessageBox.information(self, "Backup", "Auto backup stopped")
        # Refresh the tab to update button
        self.setup_backup_tab()

    def setup_settings_tab(self):
        """Setup the settings tab"""
        frame = QWidget()
        self.admin_tabs.addTab(frame, "Settings")
        layout = QVBoxLayout(frame)

        # Admin PIN
        pin_layout = QHBoxLayout()
        pin_layout.addWidget(QLabel("Admin PIN:"))
        change_pin_btn = QPushButton("Change PIN")
        change_pin_btn.clicked.connect(self.change_admin_pin_pyqt)
        pin_layout.addWidget(change_pin_btn)
        pin_layout.addStretch()
        layout.addLayout(pin_layout)

        # File locations
        files_group = QGroupBox("File Locations")
        files_layout = QVBoxLayout(files_group)

        csv_layout = QHBoxLayout()
        csv_layout.addWidget(QLabel("Attendance CSV:"))
        self.csv_path_label = QLabel(get_csv_file())
        self.csv_path_label.setStyleSheet("color: white; border: 1px solid #555555; padding: 4px;")
        csv_layout.addWidget(self.csv_path_label)
        change_csv_btn = QPushButton("Change")
        change_csv_btn.clicked.connect(self.change_csv_location_pyqt)
        csv_layout.addWidget(change_csv_btn)
        files_layout.addLayout(csv_layout)

        students_layout = QHBoxLayout()
        students_layout.addWidget(QLabel("Students JSON:"))
        self.students_path_label = QLabel(get_students_file())
        self.students_path_label.setStyleSheet("color: white; border: 1px solid #555555; padding: 4px;")
        students_layout.addWidget(self.students_path_label)
        change_students_btn = QPushButton("Change")
        change_students_btn.clicked.connect(self.change_students_location_pyqt)
        students_layout.addWidget(change_students_btn)
        files_layout.addLayout(students_layout)

        guests_layout = QHBoxLayout()
        guests_layout.addWidget(QLabel("Guests CSV:"))
        self.guests_path_label = QLabel(get_guests_file())
        self.guests_path_label.setStyleSheet("color: white; border: 1px solid #555555; padding: 4px;")
        guests_layout.addWidget(self.guests_path_label)
        change_guests_btn = QPushButton("Change")
        change_guests_btn.clicked.connect(self.change_guests_location_pyqt)
        guests_layout.addWidget(change_guests_btn)
        files_layout.addLayout(guests_layout)

        layout.addWidget(files_group)

        # Appearance
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QVBoxLayout(appearance_group)

        logo_layout = QHBoxLayout()
        logo_layout.addWidget(QLabel("Logo:"))
        change_logo_btn = QPushButton("Change Logo")
        change_logo_btn.clicked.connect(self.change_logo_pyqt)
        logo_layout.addWidget(change_logo_btn)
        logo_layout.addStretch()
        appearance_layout.addLayout(logo_layout)

        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Header Color:"))
        change_color_btn = QPushButton("Change Color")
        change_color_btn.clicked.connect(self.change_header_color_pyqt)
        color_layout.addWidget(change_color_btn)
        color_layout.addStretch()
        appearance_layout.addLayout(color_layout)

        layout.addWidget(appearance_group)

        # Import Data
        import_group = QGroupBox("Import Data")
        import_layout = QVBoxLayout(import_group)

        import_attendance_btn = QPushButton("Import Attendance CSV")
        import_attendance_btn.clicked.connect(self.import_attendance_data_pyqt)
        import_layout.addWidget(import_attendance_btn)

        layout.addWidget(import_group)

    def change_admin_pin_pyqt(self):
        """Change admin PIN"""
        new_pin, ok = QInputDialog.getText(self, "Change PIN", "Enter new admin PIN:", QLineEdit.EchoMode.Password)
        if ok and new_pin and new_pin.strip():
            confirm_pin, ok2 = QInputDialog.getText(self, "Confirm PIN", "Confirm new admin PIN:", QLineEdit.EchoMode.Password)
            if ok2 and new_pin == confirm_pin:
                self.config["admin_pin"] = new_pin
                self.admin_pin = new_pin
                if save_config(self.config):
                    QMessageBox.information(self, "Success", "Admin PIN changed successfully!")
                else:
                    QMessageBox.critical(self, "Error", "Failed to save configuration")
            else:
                QMessageBox.critical(self, "Error", "PINs do not match!")

    def change_csv_location_pyqt(self):
        """Change CSV file location"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Choose CSV File Location and Name",
            get_csv_file(),
            "CSV files (*.csv);;All files (*.*)"
        )
        if not file_path:
            return
        
        try:
            csv_dir = os.path.dirname(file_path)
            if csv_dir and not os.path.exists(csv_dir):
                os.makedirs(csv_dir, exist_ok=True)
            
            old_csv = get_csv_file()
            if os.path.exists(old_csv) and not os.path.exists(file_path):
                reply = QMessageBox.question(self, "Copy Existing Data?", 
                                           "Would you like to copy existing attendance data to the new file?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    shutil.copy2(old_csv, file_path)
            
            if not os.path.exists(file_path):
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Date", "Name", "Status"])
            
            with open(file_path, "a", encoding="utf-8"):
                pass
            
            self.config["csv_file"] = file_path
            self.csv_file = file_path
            if save_config(self.config):
                self.csv_path_label.setText(file_path)
                self.build_student_buttons()
                QMessageBox.information(self, "Success", f"CSV file location changed successfully!\n\nNew location:\n{file_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to save configuration")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to change CSV location:\n{e}")

    def change_students_location_pyqt(self):
        """Change students.json location"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Choose Students JSON Location and Name",
            get_students_file(),
            "JSON files (*.json);;All files (*.*)"
        )
        if not file_path:
            return
        try:
            dirn = os.path.dirname(file_path)
            if dirn and not os.path.exists(dirn):
                os.makedirs(dirn, exist_ok=True)

            old = get_students_file()
            if os.path.exists(old) and not os.path.exists(file_path):
                reply = QMessageBox.question(self, "Copy Existing Students?", 
                                           "Copy existing students data to new file?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    shutil.copy2(old, file_path)

            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump([], f)

            self.config["students_file"] = file_path
            if save_config(self.config):
                self.students = load_students()
                self.refresh_students_list()
                self.build_student_buttons()
                self.students_path_label.setText(file_path)
                QMessageBox.information(self, "Success", f"Students file changed to:\n{file_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to save configuration")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to change students file:\n{e}")

    def change_guests_location_pyqt(self):
        """Change guests.csv location"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Choose Guests CSV Location and Name",
            get_guests_file(),
            "CSV files (*.csv);;All files (*.*)"
        )
        if not file_path:
            return
        try:
            dirn = os.path.dirname(file_path)
            if dirn and not os.path.exists(dirn):
                os.makedirs(dirn, exist_ok=True)

            old = get_guests_file()
            if os.path.exists(old) and not os.path.exists(file_path):
                reply = QMessageBox.question(self, "Copy Existing Guests?", 
                                           "Copy existing guests data to new file?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    shutil.copy2(old, file_path)

            if not os.path.exists(file_path):
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Date", "Name", "Email"])

            self.config["guests_file"] = file_path
            if save_config(self.config):
                self.guests_path_label.setText(file_path)
                QMessageBox.information(self, "Success", f"Guests file changed to:\n{file_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to save configuration")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to change guests file:\n{e}")

    def change_logo_pyqt(self):
        """Change logo image"""
        if not PIL_AVAILABLE:
            QMessageBox.critical(self, "Error", "Image support not available (PIL/Pillow not installed)")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Logo Image",
            "",
            "Image files (*.png *.jpg *.jpeg *.gif *.bmp);;All files (*.*)"
        )
        if file_path:
            try:
                if Image:
                    test_img = Image.open(file_path)
                    test_img.close()
                else:
                    raise Exception("PIL/Pillow not available")

                self.config["logo_file"] = file_path
                self.logo_file = file_path
                if save_config(self.config):
                    self.setup_logo()
                    QMessageBox.information(self, "Success", "Logo changed successfully!")
                else:
                    QMessageBox.critical(self, "Error", "Failed to save configuration")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Invalid image file: {e}")

    def change_header_color_pyqt(self):
        """Change header color"""
        color = QColorDialog.getColor(QColor(self.header_color), self, "Choose Header Color")
        if color.isValid():
            color_hex = color.name()
            self.config["header_color"] = color_hex
            self.header_color = color_hex
            if save_config(self.config):
                # Update header colors
                self.header_widget.setStyleSheet(f"background-color: {self.header_color};")
                self.title_label.setStyleSheet(f"""
                    color: white;
                    font-size: 20px;
                    font-weight: bold;
                    background-color: {self.header_color};
                """)
                self.admin_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.header_color};
                        color: white;
                        font-size: 14px;
                        font-weight: bold;
                        border: 2px solid white;
                        padding: 8px 16px;
                    }}
                    QPushButton:hover {{
                        background-color: #1A1A1A;
                    }}
                """)
                QMessageBox.information(self, "Success", "Header color changed successfully!")
            else:
                QMessageBox.critical(self, "Error", "Failed to save configuration")

    def import_attendance_data_pyqt(self):
        """Import attendance data from CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Attendance CSV to Import",
            "",
            "CSV files (*.csv);;All files (*.*)"
        )
        if not file_path:
            return
        try:
            imported_data = []
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if "Date" in row and "Name" in row and "Status" in row:
                        imported_data.append(row)
                    else:
                        QMessageBox.warning(self, "Warning", "CSV file format may be incorrect. Expected columns: Date, Name, Status")
                        return
            
            reply = QMessageBox.question(self, "Confirm Import", 
                                       f"Import {len(imported_data)} attendance records? This will replace current data.",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                global attendance_data
                attendance_data = imported_data
                save_attendance_data()
                self.refresh_attendance_table()
                QMessageBox.information(self, "Success", "Attendance data imported successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import attendance data:\n{e}")

    # ---------------- Utilities ----------------

    def add_student(self):
        name = simpledialog.askstring("Add Student", "Enter student name:")
        if name and name.strip():
            name = name.strip()
            if name not in self.students:
                self.students.append(name)
                ok = save_students(self.students)
                if ok:
                    # Keep master list sorted and refresh admin UI
                    try:
                        self.students.sort(key=str.lower)
                    except Exception:
                        pass

                    try:
                        if hasattr(self, 'students_listbox') and self.students_listbox:
                            self.refresh_students_listbox()
                    except Exception:
                        pass

                    # Reapply current search filter so the new student appears in the main buttons
                    try:
                        self.on_search_change()
                    except Exception:
                        self.filtered_students = self.students.copy()

                    # filtered_students is re-computed by on_search_change(); don't force-insert
                    # the new student because build_student_buttons() sorts alphabetically.

                    # Rebuild main grid
                    try:
                        self.build_student_buttons()
                    except Exception:
                        pass

                    messagebox.showinfo("Success", "Student '{0}' added successfully!".format(name))
                else:
                    messagebox.showerror("Error", "Failed to save student data")
            else:
                messagebox.showwarning("Warning", "Student '{0}' already exists!".format(name))

    def edit_student(self):
        try:
            selection = self.students_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a student to edit")
                return

            old_name = self.students[selection[0]]
            new_name = simpledialog.askstring("Edit Student", "Edit name:", initialvalue=old_name)

            if new_name and new_name.strip() and new_name.strip() != old_name:
                new_name = new_name.strip()
                if new_name not in self.students:
                    self.students[selection[0]] = new_name
                    ok = save_students(self.students)
                    if ok:
                        self.refresh_students_listbox()
                        self.build_student_buttons()
                        messagebox.showinfo("Success", "Student renamed to '{0}'!".format(new_name))
                    else:
                        messagebox.showerror("Error", "Failed to save student data")
                else:
                    messagebox.showwarning("Warning", "Student '{0}' already exists!".format(new_name))
        except IndexError:
            messagebox.showerror("Error", "Invalid selection")

    def delete_student(self):
        try:
            selection = self.students_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a student to delete")
                return

            name = self.students[selection[0]]
            if messagebox.askyesno("Confirm Delete", "Delete student '{0}'?\nThis cannot be undone.".format(name)):
                self.students.pop(selection[0])
                ok = save_students(self.students)
                if ok:
                    self.refresh_students_listbox()
                    self.build_student_buttons()
                    messagebox.showinfo("Success", "Student '{0}' deleted!".format(name))
                else:
                    messagebox.showerror("Error", "Failed to save student data")
        except IndexError:
            messagebox.showerror("Error", "Invalid selection")

    def open_github(self):
        try:
            webbrowser.open("https://github.com/JZRod/FRC-Attendence-System")
        except Exception as e:
            messagebox.showerror("Error", "Could not open browser: {0}".format(e))

    def show_system_info(self):
        info = """System Information:

Python Version: {0}
Platform: {1}
PIL Available: {2}
Current Directory: {3}

Configuration:
Admin PIN: {4}
Header Color: {5}
Logo File: {6}
CSV File: {7}

Data Files:
Students: {8} registered
Attendance File: {9}
Students File: {10}
Config File: {11}
""".format(
            sys.version,
            sys.platform,
            PIL_AVAILABLE,
            os.getcwd(),
            '*' * len(self.admin_pin),
            self.header_color,
            self.logo_file,
            self.csv_file,
            len(self.students),
            get_csv_file(),
            STUDENTS_FILE,
            CONFIG_FILE
        )
        messagebox.showinfo("System Information", info)

    # ---------------- Admin helper functions ----------------
    def download_csv(self):
        csv_file = get_csv_file()
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save Attendance CSV"
            )
            if file_path:
                import shutil
                shutil.copy2(csv_file, file_path)
                messagebox.showinfo("Success", "CSV saved to:\n{0}".format(file_path))
        except Exception as e:
            messagebox.showerror("Error", "Failed to save CSV: {0}".format(e))

    def change_admin_pin(self):
        new_pin = simpledialog.askstring("Change PIN", "Enter new admin PIN:", show="*")
        if new_pin and new_pin.strip():
            confirm_pin = simpledialog.askstring("Confirm PIN", "Confirm new admin PIN:", show="*")
            if new_pin == confirm_pin:
                self.config["admin_pin"] = new_pin
                self.admin_pin = new_pin
                if save_config(self.config):
                    messagebox.showinfo("Success", "Admin PIN changed successfully!")
                else:
                    messagebox.showerror("Error", "Failed to save configuration")
            else:
                messagebox.showerror("Error", "PINs do not match!")

    def change_csv_location(self):
        """Allow user to change the CSV file location and name"""
        # Ask user to select or create a new CSV file location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Choose CSV File Location and Name",
            initialfile=os.path.basename(self.csv_file),
            initialdir=os.path.dirname(self.csv_file)
        )
        
        if not file_path:
            return  # User cancelled
        
        # Validate the path
        try:
            # Check if we can write to the directory
            csv_dir = os.path.dirname(file_path)
            if csv_dir and not os.path.exists(csv_dir):
                try:
                    os.makedirs(csv_dir, exist_ok=True)
                except Exception as e:
                    messagebox.showerror("Error", "Cannot create directory:\n{0}".format(e))
                    return
            
            # Check if file exists and ask about copying data
            old_csv = self.csv_file
            if os.path.exists(old_csv) and not os.path.exists(file_path):
                if messagebox.askyesno("Copy Existing Data?", 
                                      "Would you like to copy existing attendance data to the new file?"):
                    try:
                        import shutil
                        shutil.copy2(old_csv, file_path)
                    except Exception as e:
                        messagebox.showerror("Error", "Failed to copy data:\n{0}".format(e))
                        return
            
            # If file doesn't exist and user didn't copy, create a new one with headers
            if not os.path.exists(file_path):
                try:
                    with open(file_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(["Date", "Name", "Status"])
                except Exception as e:
                    messagebox.showerror("Error", "Cannot create CSV file:\n{0}".format(e))
                    return
            
            # Test if we can write to the file
            try:
                with open(file_path, "a", encoding="utf-8") as f:
                    pass
            except Exception as e:
                messagebox.showerror("Error", "Cannot write to file:\n{0}".format(e))
                return
            
            # Update configuration
            self.config["csv_file"] = file_path
            self.csv_file = file_path
            if save_config(self.config):
                messagebox.showinfo("Success", 
                                   "CSV file location changed successfully!\n\nNew location:\n{0}".format(file_path))
                # Refresh the attendance view if open
                self.build_student_buttons()
            else:
                messagebox.showerror("Error", "Failed to save configuration")
                
        except Exception as e:
            messagebox.showerror("Error", "Failed to change CSV location:\n{0}".format(e))

    def change_students_location(self):
        """Change students.json location and optionally copy existing data"""
        current = get_students_file()
        file_path = filedialog.asksaveasfilename(defaultextension=".json",
                                                 filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                                                 title="Choose Students JSON Location and Name",
                                                 initialfile=os.path.basename(current),
                                                 initialdir=os.path.dirname(current))
        if not file_path:
            return
        try:
            dirn = os.path.dirname(file_path)
            if dirn and not os.path.exists(dirn):
                os.makedirs(dirn, exist_ok=True)

            old = current
            if os.path.exists(old) and not os.path.exists(file_path):
                if messagebox.askyesno("Copy Existing Students?", "Copy existing students data to new file?"):
                    try:
                        import shutil
                        shutil.copy2(old, file_path)
                    except Exception as e:
                        messagebox.showerror("Error", "Failed to copy data:\n{0}".format(e))
                        return

            # Create if missing
            if not os.path.exists(file_path):
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump([], f)
                except Exception as e:
                    messagebox.showerror("Error", "Cannot create students file:\n{0}".format(e))
                    return

            # Update config and reload
            self.config["students_file"] = file_path
            if save_config(self.config):
                self.students = load_students()
                self.refresh_students_listbox()
                self.build_student_buttons()
                messagebox.showinfo("Success", "Students file changed to:\n{0}".format(file_path))
            else:
                messagebox.showerror("Error", "Failed to save configuration")
        except Exception as e:
            messagebox.showerror("Error", "Failed to change students file:\n{0}".format(e))

    def change_guests_location(self):
        """Change guests.csv location and optionally copy existing data"""
        current = get_guests_file()
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                                                 title="Choose Guests CSV Location and Name",
                                                 initialfile=os.path.basename(current),
                                                 initialdir=os.path.dirname(current))
        if not file_path:
            return
        try:
            dirn = os.path.dirname(file_path)
            if dirn and not os.path.exists(dirn):
                os.makedirs(dirn, exist_ok=True)

            old = current
            if os.path.exists(old) and not os.path.exists(file_path):
                if messagebox.askyesno("Copy Existing Guests?", "Copy existing guests data to new file?"):
                    try:
                        import shutil
                        shutil.copy2(old, file_path)
                    except Exception as e:
                        messagebox.showerror("Error", "Failed to copy data:\n{0}".format(e))
                        return

            # Create if missing with header
            if not os.path.exists(file_path):
                try:
                    with open(file_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(["Date", "Name", "Email"])
                except Exception as e:
                    messagebox.showerror("Error", "Cannot create guests file:\n{0}".format(e))
                    return

            # Update config
            self.config["guests_file"] = file_path
            if save_config(self.config):
                messagebox.showinfo("Success", "Guests file changed to:\n{0}".format(file_path))
            else:
                messagebox.showerror("Error", "Failed to save configuration")
        except Exception as e:
            messagebox.showerror("Error", "Failed to change guests file:\n{0}".format(e))

    def change_logo(self):
        if not PIL_AVAILABLE:
            messagebox.showerror("Error", "Image support not available (PIL/Pillow not installed)")
            return

        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")],
            title="Select Logo Image"
        )
        if file_path:
            try:
                if Image:
                    test_img = Image.open(file_path)
                    test_img.close()
                else:
                    raise Exception("PIL/Pillow not available")

                self.config["logo_file"] = file_path
                self.logo_file = file_path
                if save_config(self.config):
                    # update logo in header immediately
                    self.setup_logo()
                    messagebox.showinfo("Success", "Logo changed successfully!")
                else:
                    messagebox.showerror("Error", "Failed to save configuration")
            except Exception as e:
                messagebox.showerror("Error", "Invalid image file: {0}".format(e))

    def change_header_color(self):
        try:
            color_result = colorchooser.askcolor(title="Choose Header Color",
                                                color=self.header_color)
            if color_result and color_result[1]:
                color = color_result[1]
                self.config["header_color"] = color
                self.header_color = color
                if save_config(self.config):
                    self.header.configure(bg=color)
                    self.title_label.configure(bg=color)
                    self.admin_btn.configure(bg=color)
                    messagebox.showinfo("Success", "Header color changed successfully!")
                else:
                    messagebox.showerror("Error", "Failed to save configuration")
        except Exception as e:
            messagebox.showerror("Error", "Failed to change color: {0}".format(e))

    def import_attendance_data(self):
        """Import attendance data from a CSV file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Select Attendance CSV to Import"
        )
        if not file_path:
            return
        try:
            # Load the CSV data
            imported_data = []
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Validate required fields
                    if "Date" in row and "Name" in row and "Status" in row:
                        imported_data.append(row)
                    else:
                        messagebox.showwarning("Warning", "CSV file format may be incorrect. Expected columns: Date, Name, Status")
                        return
            
            # Confirm import
            if messagebox.askyesno("Confirm Import", 
                                  "Import {0} attendance records? This will replace current data.".format(len(imported_data))):
                global attendance_data
                attendance_data = imported_data
                save_attendance_data()
                messagebox.showinfo("Success", "Attendance data imported successfully!")
        except Exception as e:
            messagebox.showerror("Error", "Failed to import attendance data:\n{0}".format(e))

    def import_students_data(self):
        """Import students data from a JSON file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Select Students JSON to Import"
        )
        if not file_path:
            return
        try:
            # Load the JSON data
            with open(file_path, "r", encoding="utf-8") as f:
                imported_students = json.load(f)
            
            # Validate it's a list
            if not isinstance(imported_students, list):
                messagebox.showerror("Error", "Invalid JSON format. Expected a list of students.")
                return
            
            # Confirm import
            if messagebox.askyesno("Confirm Import", 
                                  "Import {0} students? This will replace current student list.".format(len(imported_students))):
                save_students(imported_students)
                self.students = imported_students
                self.refresh_students_listbox()
                self.build_student_buttons()
                messagebox.showinfo("Success", "Students data imported successfully!")
        except Exception as e:
            messagebox.showerror("Error", "Failed to import students data:\n{0}".format(e))

    # ---------------- Backup functions ----------------
    def change_backup_location(self, path_label=None):
        """Ask user for backup folder and save to config."""
        file_path = QFileDialog.getExistingDirectory(self, "Choose Backup Folder")
        if not file_path:
            return
        try:
            os.makedirs(file_path, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not create folder: {e}")
            return
        self.backup_location = file_path
        self.config["backup_location"] = file_path
        save_config(self.config)
        if path_label:
            try:
                path_label.setText(f"Path: {self.backup_location}")
            except Exception:
                pass

    def perform_backup(self, notify=False):
        """Perform an immediate backup of data/config/assets into the backup folder."""
        if not self.backup_location:
            if notify:
                messagebox.showwarning("Backup", "Backup folder not configured.")
            return False

        try:
            import shutil
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = os.path.join(self.backup_location, ts)
            os.makedirs(dest, exist_ok=True)

            # Files to copy
            sources = [get_csv_file(), get_students_file(), get_guests_file(), CONFIG_FILE]
            for s in sources:
                try:
                    if s and os.path.exists(s):
                        shutil.copy2(s, os.path.join(dest, os.path.basename(s)))
                except Exception:
                    # non-fatal per-file
                    pass

            # Copy assets folder if present
            try:
                if os.path.exists(ASSETS_FOLDER):
                    target_assets = os.path.join(dest, os.path.basename(ASSETS_FOLDER))
                    # Python 3.8+: dirs_exist_ok parameter
                    try:
                        shutil.copytree(ASSETS_FOLDER, target_assets, dirs_exist_ok=True)
                    except TypeError:
                        # older fallback: try copytree to non-existing target
                        if os.path.exists(target_assets):
                            shutil.rmtree(target_assets)
                        shutil.copytree(ASSETS_FOLDER, target_assets)
            except Exception:
                pass

            self.last_backup = datetime.datetime.now().isoformat()
            try:
                if hasattr(self, 'backup_status_label') and self.backup_status_label:
                    self.backup_status_label.setText(f"Last backup: {self.last_backup}")
            except Exception:
                pass

            if notify:
                QMessageBox.information(self, "Backup", f"Backup completed: {dest}")
            self.cleanup_old_backups()
            return True
        except Exception as e:
            if notify:
                QMessageBox.critical(self, "Backup Error", f"Backup failed: {e}")
            return False

    def cleanup_old_backups(self):
        """Delete backup folders older than retention days"""
        if not self.backup_location or not os.path.exists(self.backup_location):
            return
        try:
            import shutil
            now = datetime.datetime.now()
            cutoff = now - datetime.timedelta(days=self.backup_retention_days)
            for item in os.listdir(self.backup_location):
                item_path = os.path.join(self.backup_location, item)
                if os.path.isdir(item_path):
                    try:
                        # Parse timestamp from folder name YYYYMMDD_HHMMSS
                        ts_str = item
                        ts = datetime.datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                        if ts < cutoff:
                            shutil.rmtree(item_path)
                            print(f"Deleted old backup: {item_path}")
                    except ValueError:
                        # Not a timestamp folder, skip
                        pass
        except Exception as e:
            print(f"Backup cleanup error: {e}")

    def _backup_worker(self):
        """Internal worker invoked by QTimer; performs backup."""
        try:
            self.perform_backup(notify=False)
        except Exception:
            pass

    def start_backups(self):
        """Start hourly backups (immediate run + schedule)."""
        if not self.backup_location:
            QMessageBox.warning(self, "Backup", "Choose a backup folder first")
            return False
        # Save enabled flag
        self.backup_enabled = True
        self.config["backup_enabled"] = True
        save_config(self.config)
        # perform immediate backup and schedule next
        try:
            self.perform_backup(notify=False)
        except Exception:
            pass
        try:
            self.backup_timer = QTimer(self)
            self.backup_timer.timeout.connect(self._backup_worker)
            self.backup_timer.start(self.backup_interval_hours * 60 * 60 * 1000)  # Configurable hours
        except Exception:
            self.backup_timer = None
        return True

    def stop_backups(self):
        """Stop scheduled hourly backups."""
        try:
            if hasattr(self, 'backup_timer') and self.backup_timer:
                self.backup_timer.stop()
        except Exception:
            pass
        self.backup_job = None
        self.backup_enabled = False
        self.config["backup_enabled"] = False
        save_config(self.config)

# ---------------- Main Application ----------------
def main():
    init_files()

    app = QApplication(sys.argv)

    try:
        if os.path.exists(ICON_FILE) and PIL_AVAILABLE:
            try:
                app.setWindowIcon(QIcon(ICON_FILE))
            except Exception:
                pass
    except Exception as e:
        print("Icon setup warning:", e)

    window = AttendanceApp()
    window.show()

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("Application terminated by user")
    except Exception as e:
        print("Application error:", e)
        QMessageBox.critical(None, "Application Error", f"An error occurred: {e}")

if __name__ == "__main__":
    main()
