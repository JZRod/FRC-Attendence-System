import sys
import csv
import datetime
import os
import json
import webbrowser

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QScrollArea, QGridLayout, QListWidget, QTabWidget, QMessageBox,
    QInputDialog, QFileDialog, QTextEdit, QTableWidget, QTableWidgetItem, QShortcut
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QKeySequence

# Pillow import with backward-friendly fallbacks
try:
    from PIL import Image
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

DATA_FOLDER = "data"
ASSETS_FOLDER = "assets"
DEFAULT_FILENAME = os.path.join(DATA_FOLDER, "attendance.csv")
STUDENTS_FILE = os.path.join(DATA_FOLDER, "students.json")
CONFIG_FILE = os.path.join(DATA_FOLDER, "config.json")
LOGO_FILE = os.path.join(ASSETS_FOLDER, "logo.png")
GUESTS_FILE = os.path.join(DATA_FOLDER, "guests.csv")

DEFAULT_CONFIG = {
    "admin_pin": "1234",
    "header_color": "#5D3FD3",
    "logo_file": LOGO_FILE,
    "csv_file": DEFAULT_FILENAME
}

HEADER_HEIGHT = 150
attendance_data = []
guests_data = []


def get_csv_file():
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
    global attendance_data
    csv_file = get_csv_file()
    attendance_data = []
    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                attendance_data.append(row)
    except FileNotFoundError:
        pass
    except Exception as e:
        print("Error loading attendance data:", e)


def save_attendance_data():
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

    csv_file = get_csv_file()
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
    global attendance_data
    for row in attendance_data:
        if row.get("Date") == date_iso and row.get("Name") == name and row.get("Status") == "Present":
            return True
    return False


def remove_attendance(name, date_iso):
    global attendance_data
    for i, row in enumerate(attendance_data):
        if (row.get("Date") == date_iso and row.get("Name") == name and
                row.get("Status") == "Present"):
            del attendance_data[i]
            save_attendance_data()
            return True
    return False


def get_last_recorded_date():
    global attendance_data
    for row in reversed(attendance_data):
        d = (row.get("Date") or "").strip()
        if d:
            return d
    return None


def append_new_day_section(date_iso):
    global attendance_data
    csv_file = get_csv_file()
    try:
        if not os.path.exists(csv_file):
            os.makedirs(os.path.dirname(csv_file), exist_ok=True) if os.path.dirname(csv_file) else None
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Name", "Status"])

        last = get_last_recorded_date()
        if last == date_iso:
            return True

        attendance_data.append({"Date": date_iso, "Name": "--- NEW DAY ---", "Status": ""})
        save_attendance_data()
        return True
    except Exception as e:
        print("append_new_day_section error:", e)
        return False


def mark_attendance(name, status="Present"):
    today = datetime.date.today().isoformat()
    try:
        last = get_last_recorded_date()
        if last != today:
            append_new_day_section(today)
    except Exception:
        pass
    if status == "Present" and already_checked_in(name, today):
        removed = remove_attendance(name, today)
        if removed:
            return False, f"{name} removed from today's attendance."
        return False, f"{name} is already marked Present today."
    try:
        attendance_data.append({"Date": today, "Name": name, "Status": status})
        save_attendance_data()
        return True, f"Welcome, {name}! You're marked {status}."
    except Exception as e:
        print("mark_attendance error:", e)
        return False, f"Failed to mark attendance: {e}"


class AttendanceAppQt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FRC Attendance System")
        self.setStyleSheet("background-color: black;")

        self.config = load_config()
        self.admin_pin = self.config.get("admin_pin", "1164")
        self.header_color = self.config.get("header_color", "#5D3FD3")
        self.logo_file = self.config.get("logo_file", LOGO_FILE)
        self.csv_file = self.config.get("csv_file", DEFAULT_FILENAME)
        self.backup_location = self.config.get("backup_location", "")
        self.backup_enabled = self.config.get("backup_enabled", False)
        self.last_backup = None

        self.current_date = datetime.date.today().isoformat()
        load_attendance_data()
        load_guests_data()
        self.students = load_students()
        self.filtered_students = self.students.copy()

        self.setup_ui()

        self.daily_check_timer = QTimer(self)
        self.daily_check_timer.timeout.connect(self._daily_check)
        self.daily_check_timer.start(30000)

        self.showMaximized()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.setup_header(layout)

        guest_btn = QPushButton("Guest Sign In — Tap to Enter Your Name")
        guest_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                border: none;
            }
            QPushButton:pressed {
                background-color: #1A1A1A;
            }
        """)
        guest_btn.setMinimumHeight(60)
        guest_btn.clicked.connect(self.guest_sign_in)
        layout.addWidget(guest_btn)

        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(12, 3, 12, 3)

        search_label = QLabel("🔍")
        search_label.setStyleSheet("color: white; font-size: 16px; background-color: #2b2b2b;")

        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Search for a student...")
        self.search_entry.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: white;
                font-size: 14px;
                border: none;
                padding: 4px;
            }
        """)
        self.search_entry.textChanged.connect(self.on_search_change)

        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                font-weight: bold;
                padding: 4px 8px;
                border: none;
            }
        """)
        clear_btn.setMaximumWidth(60)
        clear_btn.clicked.connect(self.clear_search)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_entry)
        search_layout.addWidget(clear_btn)
        search_container.setStyleSheet("background-color: #2b2b2b; border-top: 2px solid #9a9a9a; border-left: 2px solid #9a9a9a;")
        layout.addWidget(search_container)

        self.setup_student_buttons(layout)
        self.setup_keyboard_shortcuts()

    def setup_header(self, layout):
        header = QFrame()
        header.setStyleSheet(f"background-color: {self.header_color};")
        header.setMinimumHeight(HEADER_HEIGHT)
        header.setMaximumHeight(HEADER_HEIGHT)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 12, 12, 12)

        if PIL_AVAILABLE and os.path.exists(self.logo_file):
            try:
                pixmap = QPixmap(self.logo_file)
                logo_label = QLabel()
                max_size = HEADER_HEIGHT - 40
                pixmap = pixmap.scaledToWidth(max_size, Qt.TransformationMode.SmoothTransformation)
                logo_label.setPixmap(pixmap)
                header_layout.addWidget(logo_label)
            except Exception as e:
                print("Logo loading failed:", e)
                logo_label = QLabel("LOGO")
                logo_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
                header_layout.addWidget(logo_label)
        else:
            logo_label = QLabel("LOGO")
            logo_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
            header_layout.addWidget(logo_label)

        title = QLabel("📌 Tap Your Name to Check In")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title, 1)

        admin_btn = QPushButton("⚙ Admin")
        admin_btn.setStyleSheet("""
            QPushButton {
                background-color: inherit;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid white;
                padding: 8px 16px;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        admin_btn.clicked.connect(self.admin_panel)
        header_layout.addWidget(admin_btn)

        layout.addWidget(header)

    def setup_student_buttons(self, layout):
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet("background-color: black; border: none;")
        scroll_area.setWidgetResizable(True)

        self.student_container = QWidget()
        self.student_container.setStyleSheet("background-color: black;")
        self.student_grid = QGridLayout(self.student_container)
        self.student_grid.setSpacing(4)
        self.student_grid.setContentsMargins(12, 15, 12, 12)

        scroll_area.setWidget(self.student_container)
        layout.addWidget(scroll_area, 1)

        self.build_student_buttons()

    def build_student_buttons(self):
        while self.student_grid.count():
            item = self.student_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        today = datetime.date.today().isoformat()
        sorted_students = sorted(self.filtered_students, key=str.lower)
        COLS = 3

        if not sorted_students:
            no_results = QLabel("No students found matching your search")
            no_results.setStyleSheet("color: white; font-size: 16px;")
            no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.student_grid.addWidget(no_results, 0, 0, 1, COLS)
            return

        row, col = 0, 0
        for name in sorted_students:
            checked = already_checked_in(name, today)
            bg_color = "#326B20" if checked else "#333333"
            btn = QPushButton(name)
            btn.setMinimumHeight(90)
            btn.setMaximumWidth(250)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    border: 3px solid #555;
                    padding: 12px;
                    border-radius: 4px;
                }}
                QPushButton:pressed {{
                    background-color: #1A1A1A;
                }}
            """)
            btn.clicked.connect(lambda checked, n=name: self.checkin(n))
            self.student_grid.addWidget(btn, row, col)
            col += 1
            if col >= COLS:
                col, row = 0, row + 1

    def on_search_change(self, text):
        search_text = text.lower().strip()
        if not search_text:
            self.filtered_students = self.students.copy()
        else:
            self.filtered_students = [s for s in self.students if search_text in s.lower()]
        self.build_student_buttons()

    def clear_search(self):
        self.search_entry.clear()
        self.filtered_students = self.students.copy()
        self.build_student_buttons()

    def checkin(self, name):
        mark_attendance(name, "Present")
        self.build_student_buttons()

    def guest_sign_in(self):
        name, ok = QInputDialog.getText(self, "Guest Sign In", "Enter your name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        email, ok = QInputDialog.getText(self, "Guest Email", "Enter email (optional):")
        email = email.strip() if email and ok else ""
        try:
            today = datetime.date.today().isoformat()
            guests_data.append({"Date": today, "Name": name, "Email": email})
            save_guests_data()
        except Exception as e:
            print("Failed to record guest:", e)
        if name not in self.students:
            self.students.append(name)
            save_students(self.students)
            try:
                self.students.sort(key=str.lower)
            except Exception:
                pass
        mark_attendance(name, "Present")
        self.build_student_buttons()

    def _daily_check(self):
        try:
            today = datetime.date.today().isoformat()
            if today != self.current_date:
                self.on_day_change(today)
        except Exception as e:
            print("_daily_check error:", e)

    def on_day_change(self, new_date_iso):
        try:
            self.current_date = new_date_iso
            try:
                append_new_day_section(new_date_iso)
            except Exception:
                pass
            self.build_student_buttons()
            print(f"Day changed to {new_date_iso}. Attendance reset for the new day.")
        except Exception as e:
            print("on_day_change error:", e)

    def admin_panel(self):
        pin, ok = QInputDialog.getText(self, "Admin Login", "Enter Admin PIN:", QInputDialog.EchoMode.Password)
        if not ok or pin != self.admin_pin:
            QMessageBox.critical(self, "Error", "Wrong PIN")
            return

        admin_window = QWidget()
        admin_window.setWindowTitle("Admin Panel")
        admin_window.setStyleSheet("background-color: black;")
        admin_window.resize(900, 700)

        layout = QVBoxLayout(admin_window)
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background-color: black; }
            QTabBar::tab { background-color: #333; color: white; padding: 8px; }
            QTabBar::tab:selected { background-color: #5D3FD3; }
        """)
        self.setup_attendance_tab(tabs)
        self.setup_guests_tab(tabs)
        self.setup_students_tab(tabs)
        self.setup_backup_tab(tabs)
        self.setup_settings_tab(tabs)
        self.setup_help_tab(tabs)
        layout.addWidget(tabs)
        admin_window.setLayout(layout)
        admin_window.show()

    def setup_attendance_tab(self, tabs):
        frame = QWidget()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Date", "Name", "Status"])
        table.setStyleSheet("""
            QTableWidget { background-color: black; color: white; gridline-color: #333; }
            QHeaderView::section { background-color: #5D3FD3; color: white; padding: 5px; }
        """)
        for i, row in enumerate(attendance_data):
            table.insertRow(i)
            table.setItem(i, 0, QTableWidgetItem(row.get("Date", "")))
            table.setItem(i, 1, QTableWidgetItem(row.get("Name", "")))
            table.setItem(i, 2, QTableWidgetItem(row.get("Status", "")))
        layout.addWidget(table)
        btn_layout = QHBoxLayout()
        download_btn = QPushButton("Download CSV")
        download_btn.setStyleSheet("background-color: green; color: white; font-weight: bold; padding: 10px;")
        download_btn.clicked.connect(self.download_csv)
        btn_layout.addWidget(download_btn)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("background-color: blue; color: white; font-weight: bold; padding: 10px;")
        refresh_btn.clicked.connect(lambda: self.refresh_attendance_tab(table))
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)
        tabs.addTab(frame, "Attendance")

    def refresh_attendance_tab(self, table):
        while table.rowCount():
            table.removeRow(0)
        for i, row in enumerate(attendance_data):
            table.insertRow(i)
            table.setItem(i, 0, QTableWidgetItem(row.get("Date", "")))
            table.setItem(i, 1, QTableWidgetItem(row.get("Name", "")))
            table.setItem(i, 2, QTableWidgetItem(row.get("Status", "")))

    def download_csv(self):
        csv_file = get_csv_file()
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Attendance CSV", "", "CSV Files (*.csv);;All Files (*.*)")
            if file_path:
                import shutil
                shutil.copy2(csv_file, file_path)
                QMessageBox.information(self, "Success", f"CSV saved to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save CSV: {e}")

    def setup_guests_tab(self, tabs):
        frame = QWidget()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Date", "Name", "Email"])
        table.setStyleSheet("""
            QTableWidget { background-color: black; color: white; gridline-color: #333; }
            QHeaderView::section { background-color: #5D3FD3; color: white; padding: 5px; }
        """)
        for i, row in enumerate(guests_data):
            table.insertRow(i)
            table.setItem(i, 0, QTableWidgetItem(row.get("Date", "")))
            table.setItem(i, 1, QTableWidgetItem(row.get("Name", "")))
            table.setItem(i, 2, QTableWidgetItem(row.get("Email", "")))
        layout.addWidget(table)
        btn_layout = QHBoxLayout()
        download_btn = QPushButton("Download CSV")
        download_btn.setStyleSheet("background-color: green; color: white; font-weight: bold; padding: 10px;")
        download_btn.clicked.connect(self.download_guests_csv)
        btn_layout.addWidget(download_btn)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("background-color: blue; color: white; font-weight: bold; padding: 10px;")
        refresh_btn.clicked.connect(lambda: self.refresh_guests_tab(table))
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)
        tabs.addTab(frame, "Guests")

    def refresh_guests_tab(self, table):
        load_guests_data()
        while table.rowCount():
            table.removeRow(0)
        for i, row in enumerate(guests_data):
            table.insertRow(i)
            table.setItem(i, 0, QTableWidgetItem(row.get("Date", "")))
            table.setItem(i, 1, QTableWidgetItem(row.get("Name", "")))
            table.setItem(i, 2, QTableWidgetItem(row.get("Email", "")))

    def download_guests_csv(self):
        guests_file = get_guests_file()
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Guests CSV", "", "CSV Files (*.csv);;All Files (*.*)")
            if file_path:
                import shutil
                shutil.copy2(guests_file, file_path)
                QMessageBox.information(self, "Success", f"Guests CSV saved to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save Guests CSV: {e}")

    def setup_students_tab(self, tabs):
        frame = QWidget()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)

        label = QLabel("Current Students:")
        label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        layout.addWidget(label)

        self.students_listbox = QListWidget()
        self.students_listbox.setStyleSheet("""
            QListWidget { background-color: black; color: white; border: none; }
            QListWidget::item:selected { background-color: #5D3FD3; }
        """)
        for student in self.students:
            self.students_listbox.addItem(student)
        layout.addWidget(self.students_listbox)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Student")
        add_btn.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        add_btn.clicked.connect(self.add_student)
        btn_layout.addWidget(add_btn)
        edit_btn = QPushButton("Edit Student")
        edit_btn.setStyleSheet("background-color: orange; color: white; font-weight: bold;")
        edit_btn.clicked.connect(self.edit_student)
        btn_layout.addWidget(edit_btn)
        delete_btn = QPushButton("Delete Student")
        delete_btn.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        delete_btn.clicked.connect(self.delete_student)
        btn_layout.addWidget(delete_btn)
        layout.addLayout(btn_layout)
        tabs.addTab(frame, "Students")

    def add_student(self):
        name, ok = QInputDialog.getText(self, "Add Student", "Enter student name:")
        if ok and name.strip():
            name = name.strip()
            if name not in self.students:
                self.students.append(name)
                save_students(self.students)
                self.students.sort(key=str.lower)
                self.refresh_students_listbox()
                self.build_student_buttons()
                QMessageBox.information(self, "Success", f"Student '{name}' added successfully!")
            else:
                QMessageBox.warning(self, "Warning", f"Student '{name}' already exists!")

    def edit_student(self):
        selected_items = self.students_listbox.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a student to edit")
            return
        old_name = selected_items[0].text()
        new_name, ok = QInputDialog.getText(self, "Edit Student", "Edit name:", text=old_name)
        if ok and new_name.strip() and new_name.strip() != old_name:
            new_name = new_name.strip()
            if new_name not in self.students:
                index = self.students.index(old_name)
                self.students[index] = new_name
                save_students(self.students)
                self.refresh_students_listbox()
                self.build_student_buttons()
                QMessageBox.information(self, "Success", f"Student renamed to '{new_name}'!")
            else:
                QMessageBox.warning(self, "Warning", f"Student '{new_name}' already exists!")

    def delete_student(self):
        selected_items = self.students_listbox.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a student to delete")
            return
        name = selected_items[0].text()
        result = QMessageBox.question(self, "Confirm Delete", f"Delete student '{name}'?\nThis cannot be undone.")
        if result == QMessageBox.StandardButton.Yes:
            self.students.remove(name)
            save_students(self.students)
            self.refresh_students_listbox()
            self.build_student_buttons()
            QMessageBox.information(self, "Success", f"Student '{name}' deleted!")

    def refresh_students_listbox(self):
        self.students_listbox.clear()
        for student in self.students:
            self.students_listbox.addItem(student)

    def setup_backup_tab(self, tabs):
        frame = QWidget()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        label = QLabel("Backup Configuration")
        label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        layout.addWidget(label)
        change_btn = QPushButton("Change Backup Folder")
        change_btn.setStyleSheet("background-color: blue; color: white; font-weight: bold; padding: 10px;")
        change_btn.clicked.connect(self.change_backup_location)
        layout.addWidget(change_btn)
        backup_now_btn = QPushButton("Backup Now")
        backup_now_btn.setStyleSheet("background-color: green; color: white; font-weight: bold; padding: 10px;")
        backup_now_btn.clicked.connect(lambda: self.perform_backup(notify=True))
        layout.addWidget(backup_now_btn)
        layout.addStretch()
        tabs.addTab(frame, "Backup")

    def change_backup_location(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Choose Backup Folder")
        if folder_path:
            try:
                os.makedirs(folder_path, exist_ok=True)
                self.backup_location = folder_path
                self.config["backup_location"] = folder_path
                save_config(self.config)
                QMessageBox.information(self, "Success", f"Backup folder set to:\n{folder_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create folder: {e}")

    def perform_backup(self, notify=False):
        if not self.backup_location:
            if notify:
                QMessageBox.warning(self, "Backup", "Backup folder not configured.")
            return False
        try:
            import shutil
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = os.path.join(self.backup_location, ts)
            os.makedirs(dest, exist_ok=True)
            sources = [get_csv_file(), get_students_file(), get_guests_file(), CONFIG_FILE]
            for s in sources:
                try:
                    if s and os.path.exists(s):
                        shutil.copy2(s, os.path.join(dest, os.path.basename(s)))
                except Exception:
                    pass
            if notify:
                QMessageBox.information(self, "Backup", f"Backup completed:\n{dest}")
            return True
        except Exception as e:
            if notify:
                QMessageBox.critical(self, "Backup Error", f"Backup failed: {e}")
            return False

    def setup_settings_tab(self, tabs):
        frame = QWidget()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        pin_label = QLabel("Admin PIN: " + "*" * len(self.admin_pin))
        pin_label.setStyleSheet("color: white;")
        layout.addWidget(pin_label)
        pin_btn = QPushButton("Change PIN")
        pin_btn.setStyleSheet("background-color: blue; color: white; font-weight: bold; padding: 10px;")
        pin_btn.clicked.connect(self.change_admin_pin)
        layout.addWidget(pin_btn)
        layout.addSpacing(20)
        csv_label = QLabel(f"CSV File: {os.path.basename(self.csv_file)}")
        csv_label.setStyleSheet("color: white;")
        layout.addWidget(csv_label)
        csv_path_label = QLabel(f"Path: {self.csv_file}")
        csv_path_label.setStyleSheet("color: lightgray; font-size: 10px;")
        layout.addWidget(csv_path_label)
        csv_btn = QPushButton("Change CSV Location")
        csv_btn.setStyleSheet("background-color: blue; color: white; font-weight: bold; padding: 10px;")
        csv_btn.clicked.connect(self.change_csv_location)
        layout.addWidget(csv_btn)
        layout.addStretch()
        tabs.addTab(frame, "Settings")

    def change_admin_pin(self):
        new_pin, ok = QInputDialog.getText(self, "Change PIN", "Enter new admin PIN:", QInputDialog.EchoMode.Password)
        if not ok or not new_pin.strip():
            return
        confirm_pin, ok = QInputDialog.getText(self, "Confirm PIN", "Confirm new admin PIN:", QInputDialog.EchoMode.Password)
        if not ok:
            return
        if new_pin == confirm_pin:
            self.config["admin_pin"] = new_pin
            self.admin_pin = new_pin
            if save_config(self.config):
                QMessageBox.information(self, "Success", "Admin PIN changed successfully!")
            else:
                QMessageBox.critical(self, "Error", "Failed to save configuration")
        else:
            QMessageBox.critical(self, "Error", "PINs do not match!")

    def change_csv_location(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Choose CSV Location", os.path.dirname(self.csv_file), "CSV Files (*.csv);;All Files (*.*)")
        if not file_path:
            return
        try:
            csv_dir = os.path.dirname(file_path)
            if csv_dir and not os.path.exists(csv_dir):
                os.makedirs(csv_dir, exist_ok=True)
            if not os.path.exists(file_path):
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Date", "Name", "Status"])
            self.config["csv_file"] = file_path
            self.csv_file = file_path
            if save_config(self.config):
                QMessageBox.information(self, "Success", f"CSV location changed to:\n{file_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to save configuration")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to change CSV location: {e}")

    def setup_help_tab(self, tabs):
        frame = QWidget()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setStyleSheet("background-color: black; color: white;")
        help_content = """How to Use:\nTap a student name to mark them Present\nTap again to remove them from today's attendance\nUse Guest Sign-In for visitors or unlisted students\nPress Escape or F11 to toggle fullscreen mode\n\nAdmin Features:\nView and download attendance records as CSV\nAdd, edit, or remove students from the system\nChange admin PIN for security\nCustomize CSV file location and name\nAccess help and system information\n\nFile Locations:\nAttendance data: Configurable (default: data/attendance.csv)\nStudent list: data/students.json\nConfiguration: data/config.json\nAssets: assets/ folder\n\nPyQt6 Version Features:\nModern Qt-based UI\nFull compatibility with Python 3.8+\nImproved performance over tkinter\nProfessional appearance"""
        help_text.setText(help_content)
        layout.addWidget(help_text)
        github_btn = QPushButton("Open GitHub Repository")
        github_btn.setStyleSheet("background-color: blue; color: white; font-weight: bold; padding: 10px;")
        github_btn.clicked.connect(self.open_github)
        layout.addWidget(github_btn)
        tabs.addTab(frame, "Help")

    def open_github(self):
        try:
            webbrowser.open("https://github.com/JZRod/FRC-Attendence-System")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open browser: {e}")

    def setup_keyboard_shortcuts(self):
        QShortcut(QKeySequence("F11"), self, self.toggle_fullscreen)
        QShortcut(QKeySequence("Escape"), self, self.toggle_fullscreen)

    def toggle_fullscreen(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def closeEvent(self, event):
        if self.daily_check_timer.isActive():
            self.daily_check_timer.stop()
        event.accept()


def main():
    init_files()
    app = QApplication(sys.argv)
    window = AttendanceAppQt()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
