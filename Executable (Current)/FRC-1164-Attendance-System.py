import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, filedialog, colorchooser
import csv
import datetime
import os
import json
import sys
import webbrowser

# Pillow import with backward-friendly fallbacks
try:
    from PIL import Image, ImageTk
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
    ImageTk = None
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
    "csv_file": DEFAULT_FILENAME
}

HEADER_HEIGHT = 150

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
class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FRC Attendance System")
        self.root.configure(bg="black")

        # Load configuration
        self.config = load_config()
        self.admin_pin = self.config.get("admin_pin", "1164")
        self.header_color = self.config.get("header_color", "#5D3FD3")
        self.logo_file = self.config.get("logo_file", LOGO_FILE)
        self.csv_file = self.config.get("csv_file", DEFAULT_FILENAME)
        # Backup settings
        self.backup_location = self.config.get("backup_location", "")
        self.backup_enabled = self.config.get("backup_enabled", False)
        self.backup_job = None
        self.last_backup = None

        # Fullscreen toggle
        self.fullscreen = True
        self.setup_fullscreen()
        self.root.bind("<Escape>", self.toggle_fullscreen)
        self.root.bind("<F11>", self.toggle_fullscreen)

        # Header
        self.header = tk.Frame(root, bg=self.header_color, height=HEADER_HEIGHT)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        self.header.rowconfigure(0, weight=1)
        self.header.columnconfigure(0, minsize=HEADER_HEIGHT)
        self.header.columnconfigure(1, weight=1)
        self.header.columnconfigure(2, minsize=120)

        # Logo
        self.setup_logo()

        # Title
        self.title_label = tk.Label(self.header, text="📌 Tap Your Name to Check In",
                                    bg=self.header_color, fg="white", font=("Arial", 20, "bold"))
        self.title_label.grid(row=0, column=1, sticky="nsew")

        # Track current date so we can detect day changes while the app is running
        self.current_date = datetime.date.today().isoformat()
        # Show the current date in the header
        try:
            self.update_title_with_date()
        except Exception:
            pass

        # Admin button (gear)
        self.setup_admin_button()

        # Guest Sign In
        self.guest_frame = tk.Frame(root, bg="black")
        self.guest_frame.pack(fill="x", pady=(10, 0))
        self.guest_btn = tk.Button(
            self.guest_frame,
            text="Guest Sign In — Tap to Enter Your Name",
            command=self.guest_sign_in,
            bg="#333333",
            fg="white",
            font=("Arial", 14, "bold"),
            height=2,
            relief="raised",
            activebackground="#1A1A1A",
            activeforeground="white",
        )
        self.guest_btn.pack(fill="x", padx=12, pady=12)

        # Search bar
        self.search_frame = tk.Frame(root, bg="black")
        # Slightly reduce vertical gap around the search bar
        self.search_frame.pack(fill="x", pady=(3, 0))

        # Build a top+left outline using separate border frames so the outline
        # appears only on the top and left sides. The inner search area uses a
        # slightly darker gray than the buttons.
        outline_color = "#9a9a9a"  # gray outline
        inner_bg = "#2b2b2b"       # darker inner background

        search_outer = tk.Frame(self.search_frame, bg="black", relief="flat", bd=0)
        search_outer.pack(fill="x", padx=12, pady=3)

        # Top border
        top_border = tk.Frame(search_outer, bg=outline_color, height=2)
        top_border.pack(side="top", fill="x")

        # Content area holds left border + inner search area
        # Use the same inner background for the content area so there's no
        # visible black gap between the outline and the search element.
        content_area = tk.Frame(search_outer, bg=inner_bg)
        content_area.pack(side="top", fill="both", expand=True)

        left_border = tk.Frame(content_area, bg=outline_color, width=2)
        left_border.pack(side="left", fill="y")

        # Pack search_inner immediately adjacent to the left border so there
        # is no black gap; small internal padding is handled inside search_inner
        search_inner = tk.Frame(content_area, bg=inner_bg)
        search_inner.pack(side="left", fill="x", expand=True, padx=0, pady=4)

        tk.Label(search_inner, text="🔍", bg=inner_bg, fg="white", font=("Arial", 16)).pack(side="left", padx=(8, 8))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_inner,
            textvariable=self.search_var,
            font=("Arial", 14),
            bg=inner_bg,
            fg="white",
            relief="flat",
            bd=0,
            insertbackground="white",
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.insert(0, "Search for a student...")
        # Placeholder should appear gray until the user focuses and types
        self.search_entry.configure(fg="gray")
        self.clear_btn = tk.Button(
            search_inner,
            text="Clear",
            command=self.clear_search,
            bg="#555",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            bd=0,
            width=6,
            activebackground="#1A1A1A",
        )
        self.clear_btn.pack(side="right", padx=(8, 12))
        self.search_var.trace("w", self.on_search_change)
        self.search_entry.bind("<FocusIn>", self.on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self.on_search_focus_out)

        # Scrollable student list container
        self.container = tk.Frame(root, bg="black")
        # Add top padding so the gap between the bottom of the search bar and
        # the top of the student area matches the gap between the guest sign-in
        # and the top of the search bar (guest bottom 12 + search top 3 = 15px).
        self.container.pack(fill="both", expand=True, pady=(15, 0))

        self.canvas = tk.Canvas(self.container, bg="black", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.v_scrollbar = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.v_scrollbar.pack(side="right", fill="y")

        self.student_frame = tk.Frame(self.canvas, bg="black")
        self.student_frame_id = self.canvas.create_window((0, 0), window=self.student_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)

        # Dynamic resize and scroll behavior
        def _resize_inner(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            try:
                self.canvas.itemconfigure(self.student_frame_id, width=self.canvas.winfo_width())
            except Exception:
                pass
            bbox = self.canvas.bbox("all")
            if bbox:
                content_height = bbox[3] - bbox[1]
                canvas_height = self.canvas.winfo_height()
                if content_height > canvas_height:
                    self.v_scrollbar.pack(side="right", fill="y")
                else:
                    self.v_scrollbar.pack_forget()

        self.student_frame.bind("<Configure>", _resize_inner)

        # Mousewheel scrolling
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        # Bind mousewheel only to the main canvas and its internal frame so that
        # other windows (like the Admin panel) can handle scrolling independently.
        # Previously bind_all caused the admin window mousewheel to scroll the main app.
        try:
            self.canvas.bind("<MouseWheel>", _on_mousewheel)
            self.student_frame.bind("<MouseWheel>", _on_mousewheel)
        except Exception:
            # Fallback to the old behavior only if necessary
            try:
                self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
            except Exception:
                pass

        # Also ensure scrolling works when the cursor is over a button inside
        # the student_frame: bind/unbind the global wheel events when the
        # pointer enters/leaves the student area. This lets buttons receive
        # clicks normally but preserves scrolling while hovering them.
        def _bind_main_mousewheel(event):
            try:
                self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
            except Exception:
                pass

        def _unbind_main_mousewheel(event):
            try:
                self.canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass

        try:
            # Bind enter/leave on the student_frame so hovering any child (buttons)
            # will activate scrolling.
            self.student_frame.bind("<Enter>", _bind_main_mousewheel)
            self.student_frame.bind("<Leave>", _unbind_main_mousewheel)
            # Also bind on the canvas itself as a fallback
            self.canvas.bind("<Enter>", _bind_main_mousewheel)
            self.canvas.bind("<Leave>", _unbind_main_mousewheel)
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

    def update_title_with_date(self):
        """Update the title label to include the current date for clarity."""
        try:
            d = self.current_date or datetime.date.today().isoformat()
            self.title_label.configure(text=("Tap Your Name to Check In"))
        except Exception:
            pass

    def schedule_daily_check(self):
        """Schedule the next daily check (non-blocking)."""
        # Check every 30 seconds; using after keeps it on the main thread safely
        self.root.after(30 * 1000, self._daily_check)

    def _daily_check(self):
        """Check whether the date has rolled over; if so, handle it and reschedule."""
        try:
            today = datetime.date.today().isoformat()
            if today != self.current_date:
                self.on_day_change(today)
        except Exception as e:
            print("_daily_check error:", e)
        finally:
            # Always reschedule
            try:
                self.schedule_daily_check()
            except Exception:
                pass

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
        """Setup fullscreen with Windows 7 compatibility"""
        try:
            # Try modern fullscreen first
            self.root.attributes("-fullscreen", True)
        except tk.TclError:
            try:
                # Fallback to zoomed state for Windows 7
                self.root.state('zoomed')
            except tk.TclError:
                # Final fallback - maximize window manually
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                self.root.geometry("{0}x{1}+0+0".format(screen_width, screen_height))

    def setup_logo(self):
        """Setup logo with PIL fallback for Windows 7"""
        try:
            if PIL_AVAILABLE and Image and ImageTk and os.path.exists(self.logo_file):
                max_logo = HEADER_HEIGHT - 40
                img = Image.open(self.logo_file)
                if RESAMPLE_METHOD:
                    img.thumbnail((max_logo, max_logo), RESAMPLE_METHOD)
                else:
                    img = img.resize((max_logo, max_logo))
                self.logo = ImageTk.PhotoImage(img)
                logo_label = tk.Label(self.header, image=self.logo, bg=self.header_color)
                logo_label.grid(row=0, column=0, padx=12, sticky="ns")
            else:
                raise Exception("Logo not available")
        except Exception as e:
            print("Logo loading failed: {0}".format(e))
            logo_label = tk.Label(self.header, text="LOGO", bg=self.header_color, fg="white",
                                  font=("Arial", 24, "bold"), relief="raised", bd=2)
            logo_label.grid(row=0, column=0, padx=12, sticky="ns")

    def setup_admin_button(self):
        """Setup admin button with gear icon fallback"""
        try:
            if PIL_AVAILABLE and Image and ImageTk and os.path.exists(GEAR_FILE):
                gear_icon = Image.open(GEAR_FILE)
                gear_icon = gear_icon.convert("RGBA")
                if RESAMPLE_METHOD:
                    gear_icon.thumbnail((25, 25), RESAMPLE_METHOD)
                else:
                    gear_icon = gear_icon.resize((25, 25))
                self.gear_icon = ImageTk.PhotoImage(gear_icon)
                self.admin_btn = tk.Button(self.header, image=self.gear_icon, text=" Admin",
                                           compound="left", command=self.admin_panel,
                                           bg=self.header_color, fg="white",
                                           font=("Arial", 14, "bold"), borderwidth=2,
                                           relief="raised", highlightthickness=2,
                                           highlightbackground="white")
            else:
                raise Exception("Gear icon not available")
        except Exception as e:
            print("Gear icon loading failed: {0}".format(e))
            self.admin_btn = tk.Button(self.header, text="Admin", command=self.admin_panel,
                                       bg=self.header_color, fg="white",
                                       font=("Arial", 14, "bold"), borderwidth=2,
                                       relief="raised", highlightthickness=2,
                                       highlightbackground="white")
        self.admin_btn.grid(row=0, column=2, padx=10, sticky="e")

    def _on_mousewheel_windows(self, event):
        try:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen with Windows 7 compatibility"""
        self.fullscreen = not self.fullscreen
        try:
            self.root.attributes("-fullscreen", self.fullscreen)
        except tk.TclError:
            try:
                if self.fullscreen:
                    self.root.state('zoomed')
                else:
                    self.root.state('normal')
            except tk.TclError:
                if self.fullscreen:
                    screen_width = self.root.winfo_screenwidth()
                    screen_height = self.root.winfo_screenheight()
                    self.root.geometry("{0}x{1}+0+0".format(screen_width, screen_height))
                else:
                    self.root.geometry("1024x768+100+100")

    # ---------------- Search ----------------
    def on_search_change(self, *args):
        """Handle search text changes"""
        search_text = self.search_var.get().lower().strip()
        if not search_text or search_text == "search for a student...":
            self.filtered_students = self.students.copy()
        else:
            self.filtered_students = [s for s in self.students if search_text in s.lower()]
        self.build_student_buttons()

    def on_search_focus_in(self, event):
        """Handle search entry focus in"""
        if self.search_entry.get() == "Search for a student...":
            self.search_entry.delete(0, tk.END)
            # Use white text when the user types
            self.search_entry.configure(fg="white")

    def on_search_focus_out(self, event):
        """Handle search entry focus out"""
        if not self.search_entry.get():
            self.search_entry.insert(0, "Search for a student...")
            self.search_entry.configure(fg="gray")

    def clear_search(self):
        """Clear search and show all students"""
        self.search_var.set("")
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, "Search for a student...")
        self.search_entry.configure(fg="gray")
        self.filtered_students = self.students.copy()
        self.build_student_buttons()

    # ---------------- Student Buttons ----------------
    def build_student_buttons(self):
        """Build student buttons grid using filtered students list"""
        for widget in self.student_frame.winfo_children():
            widget.destroy()

        today = datetime.date.today().isoformat()
        sorted_students = sorted(self.filtered_students, key=str.lower)
        COLS = 3

        for c in range(COLS):
            self.student_frame.grid_columnconfigure(c, weight=1)

        if not sorted_students:
            no_results = tk.Label(self.student_frame, text="No students found matching your search",
                                  bg="black", fg="white", font=("Arial", 16))
            no_results.grid(row=0, column=0, columnspan=COLS, pady=50)
            return

        row, col = 0, 0
        # Choose a slightly smaller height when fullscreen
        btn_height = 3 if self.fullscreen else 2

        for name in sorted_students:
            checked = already_checked_in(name, today)
            # plain name (no emoji/checkmark). When checked, persistently show #326B20
            bg_color = "#326B20" if checked else "#333333"
            btn = tk.Button(self.student_frame, text=name, width=20, height=btn_height,
                            command=lambda n=name: self.checkin(n),
                            bg=bg_color, fg="white",
                            font=("Arial", 14, "bold"), relief="raised", bd=3,
                            activebackground="#1A1A1A", activeforeground="white",
                            wraplength=150)
            btn.grid(row=row, column=col, padx=12, pady=4, sticky="nsew")
            self.student_frame.grid_rowconfigure(row, weight=1)
            col += 1
            if col >= COLS:
                col, row = 0, row + 1

        # After building buttons, update scrollregion
        try:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except Exception:
            pass

    def checkin(self, name):
        """Handle student check-in (toggle) without popups"""
        # Toggle attendance for the given student name
        mark_attendance(name, "Present")
        self.build_student_buttons()

    def guest_sign_in(self):
        """Handle guest sign-in (no popups)"""
        name = simpledialog.askstring("Guest Sign In", "Enter your name:")
        if not name or not name.strip():
            return
        name = name.strip()
        email = simpledialog.askstring("Guest Email (optional)", "Enter email (optional):")
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
        pin = simpledialog.askstring("Admin Login", "Enter Admin PIN:", show="*")
        if pin != self.admin_pin:
            messagebox.showerror("Error", "Wrong PIN")
            return

        admin_win = tk.Toplevel(self.root)
        admin_win.title("Admin Panel")
        admin_win.geometry("900x700")
        admin_win.configure(bg="black")

        # make modal-like
        admin_win.transient(self.root)
        admin_win.grab_set()

        notebook = ttk.Notebook(admin_win)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tabs
        self.setup_attendance_tab(notebook)
        # Guests admin tab (shows guest sign-ins)
        self.setup_guests_tab(notebook)
        self.setup_students_tab(notebook)
        # Backup settings now live in their own tab
        self.setup_backup_tab(notebook)
        self.setup_settings_tab(notebook)
        self.setup_help_tab(notebook)

    def setup_attendance_tab(self, notebook):
        # Use a dark background for the attendance viewer
        frame = tk.Frame(notebook, bg="black")
        notebook.add(frame, text="Attendance")
        admin_window = notebook.master

        # Treeview + scrollbars (container uses black to match request)
        tree_frame = tk.Frame(frame, bg="black")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Configure a Treeview style for dark background rows/fields
        try:
            style = ttk.Style()
            try:
                style.theme_use('default')
            except Exception:
                pass
            style.configure("Black.Treeview", background="black", fieldbackground="black", foreground="white")
            style.configure("Black.Treeview.Heading", background=self.header_color, foreground="white")
            style.map("Black.Treeview", background=[('selected', self.header_color)], foreground=[('selected', 'white')])
        except Exception:
            # If style setup fails, continue with defaults
            pass

        cols = ("Date", "Name", "Status")
        # Apply the dark style if available
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=15, style="Black.Treeview")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")

        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Load attendance data
        global attendance_data
        for row in attendance_data:
            tree.insert("", "end", values=(
                row.get("Date", ""),
                row.get("Name", ""),
                row.get("Status", "")
            ))

        btn_frame = tk.Frame(frame, bg="black")
        btn_frame.pack(pady=10, fill="x", padx=10)

        tk.Button(btn_frame, text="Download CSV", command=self.download_csv,
                  bg="green", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2).pack(side="left", padx=5)

        tk.Button(btn_frame, text="Refresh", command=lambda: self.refresh_attendance_tree(tree),
                  bg="blue", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2).pack(side="left", padx=5)

        tk.Button(btn_frame, text="Close", command=lambda: admin_window.destroy(),
                  bg="red", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2).pack(side="right", padx=5)

    def setup_guests_tab(self, notebook):
        """Admin tab to view guest sign-ins (Date, Name, Email)"""
        frame = tk.Frame(notebook, bg="black")
        notebook.add(frame, text="Guests")
        admin_window = notebook.master

        tree_frame = tk.Frame(frame, bg="black")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        try:
            style = ttk.Style()
            try:
                style.theme_use('default')
            except Exception:
                pass
            style.configure("Black.Treeview", background="black", fieldbackground="black", foreground="white")
            style.configure("Black.Treeview.Heading", background=self.header_color, foreground="white")
            style.map("Black.Treeview", background=[('selected', self.header_color)], foreground=[('selected', 'white')])
        except Exception:
            pass

        cols = ("Date", "Name", "Email")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=15, style="Black.Treeview")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")

        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Load guest data
        try:
            self.refresh_guests_tree(tree)
        except Exception as e:
            print("Error loading guests data:", e)
            tree.insert("", "end", values=("Error", "Could not load data", "Check file"))

        btn_frame = tk.Frame(frame, bg="black")
        btn_frame.pack(pady=10, fill="x", padx=10)

        def download_guests():
            guests_file = get_guests_file()
            try:
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                    title="Save Guests CSV"
                )
                if file_path:
                    import shutil
                    shutil.copy2(guests_file, file_path)
                    messagebox.showinfo("Success", "Guests CSV saved to:\n{0}".format(file_path))
            except Exception as e:
                messagebox.showerror("Error", "Failed to save Guests CSV: {0}".format(e))

        tk.Button(btn_frame, text="Download CSV", command=download_guests,
                  bg="green", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2).pack(side="left", padx=5)

        tk.Button(btn_frame, text="Refresh", command=lambda: self.refresh_guests_tree(tree),
                  bg="blue", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2).pack(side="left", padx=5)

        tk.Button(btn_frame, text="Close", command=lambda: admin_window.destroy(),
                  bg="red", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2).pack(side="right", padx=5)

    def setup_students_tab(self, notebook):
        frame = tk.Frame(notebook, bg="black")
        notebook.add(frame, text="Students")
        admin_window = notebook.master

        list_frame = tk.Frame(frame, bg="black")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(list_frame, text="Current Students:", bg="black", fg="white",
                 font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 5))

        list_container = tk.Frame(list_frame, bg="black")
        list_container.pack(fill="both", expand=True)

        # Dark-themed listbox so the Students admin tab matches the Attendance viewer
        self.students_listbox = tk.Listbox(list_container, font=("Arial", 12),
                                          selectmode=tk.SINGLE, height=15,
                                          bg="black", fg="white",
                                          selectbackground=self.header_color,
                                          selectforeground="white",
                                          highlightthickness=0, bd=0)
        list_scrollbar = ttk.Scrollbar(list_container, orient="vertical",
                                       command=self.students_listbox.yview)
        self.students_listbox.configure(yscrollcommand=list_scrollbar.set)

        self.students_listbox.pack(side="left", fill="both", expand=True)
        list_scrollbar.pack(side="right", fill="y")

        self.refresh_students_listbox()

        btn_frame = tk.Frame(frame, bg="black")
        btn_frame.pack(pady=10, fill="x", padx=10)

        tk.Button(btn_frame, text="Add Student", command=self.add_student,
                  bg="green", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Edit Student", command=self.edit_student,
                  bg="orange", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete Student", command=self.delete_student,
                  bg="red", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Close", command=lambda: admin_window.destroy(),
                  bg="darkred", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2).pack(side="right", padx=5)

    def setup_backup_tab(self, notebook):
        """Separate Backup tab so backup controls have their own page."""
        frame = tk.Frame(notebook, bg="black")
        notebook.add(frame, text="Backup")
        admin_window = notebook.master

        main_frame = tk.Frame(frame, bg="black")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Backup folder section
        folder_frame = tk.LabelFrame(main_frame, text="Backup Folder", bg="black",
                                     font=("Arial", 12, "bold"), fg="#5D3FD3")
        folder_frame.pack(fill="x", pady=(0, 20))

        cur_name = os.path.basename(self.backup_location) if self.backup_location else "Not set"
        tk.Label(folder_frame, text="Current Backup Folder: {0}".format(cur_name),
                 bg="black", fg="white", font=("Arial", 11)).pack(pady=6)

        self._backup_path_label = tk.Label(folder_frame, text="Path: {0}".format(self.backup_location or "(not configured)"),
                                           bg="black", fg="lightgray", font=("Arial", 9), wraplength=700, justify="left")
        self._backup_path_label.pack(pady=(0, 8))

        tk.Button(folder_frame, text="Change Backup Folder", command=lambda: self.change_backup_location(self._backup_path_label),
                  bg="blue", fg="white", font=("Arial", 11, "bold"), relief="raised", bd=2).pack(pady=5)

        # Backup now section
        now_frame = tk.LabelFrame(main_frame, text="Backup Now", bg="black",
                                  font=("Arial", 12, "bold"), fg="#5D3FD3")
        now_frame.pack(fill="x", pady=(0, 20))

        tk.Label(now_frame, text="Run an immediate backup of attendance, students, guests, config and assets.",
                 bg="black", fg="lightgray", font=("Arial", 10), wraplength=700, justify="left").pack(pady=(6, 8))

        tk.Button(now_frame, text="Backup Now", command=lambda: self.perform_backup(notify=True),
                  bg="green", fg="white", font=("Arial", 11, "bold"), relief="raised", bd=2).pack(pady=5)

        # Hourly backups section
        hourly_frame = tk.LabelFrame(main_frame, text="Hourly Backups", bg="black",
                                     font=("Arial", 12, "bold"), fg="#5D3FD3")
        hourly_frame.pack(fill="x", pady=(0, 20))

        self.backup_status_label = tk.Label(hourly_frame, text=("Last backup: None" if not self.last_backup else str(self.last_backup)),
                                            bg="black", fg="white", font=("Arial", 10))
        self.backup_status_label.pack(anchor="w", pady=(6, 8), padx=6)

        def _toggle_backups():
            if getattr(self, 'backup_job', None):
                self.stop_backups()
                toggle_btn.configure(text="Start Hourly Backups")
                try:
                    self.backup_status_label.configure(text="Backups stopped")
                except Exception:
                    pass
            else:
                if not self.backup_location:
                    messagebox.showwarning("Backup", "Please choose a backup folder first")
                    return
                self.start_backups()
                toggle_btn.configure(text="Stop Hourly Backups")
                try:
                    self.backup_status_label.configure(text=("Last backup: {0}".format(self.last_backup) if self.last_backup else "Backups running"))
                except Exception:
                    pass

        toggle_btn = tk.Button(hourly_frame, text=("Stop Hourly Backups" if self.backup_enabled else "Start Hourly Backups"),
                               command=_toggle_backups,
                               bg="orange", fg="white", font=("Arial", 11, "bold"), relief="raised", bd=2)
        toggle_btn.pack(pady=5)

        # Close button
        close_frame = tk.Frame(main_frame, bg="black")
        close_frame.pack(fill="x", pady=(10, 0))
        tk.Button(close_frame, text="Close", command=lambda: admin_window.destroy(),
                  bg="red", fg="white", font=("Arial", 12, "bold"), relief="raised", bd=2).pack()

    def setup_settings_tab(self, notebook):
       settings_frame = tk.Frame(notebook, bg="black")
       notebook.add(settings_frame, text="Settings")
       admin_window = notebook.master

       # Scrollable settings area: canvas + inner frame so long settings pages can scroll
       container_canvas = tk.Canvas(settings_frame, bg="black", highlightthickness=0)
       vsb = ttk.Scrollbar(settings_frame, orient="vertical", command=container_canvas.yview)
       container_canvas.configure(yscrollcommand=vsb.set)
       vsb.pack(side="right", fill="y")
       container_canvas.pack(side="left", fill="both", expand=True, padx=0, pady=0)

       inner_frame = tk.Frame(container_canvas, bg="black")
       # create window to hold inner_frame with a small left padding
       left_pad = 10
       win_id = container_canvas.create_window((left_pad, 0), window=inner_frame, anchor="nw")

       # ensure inner_frame width follows the canvas width (so content stretches and sits close to scrollbar)
       def _on_canvas_configure(event):
           try:
               # reduce width by scrollbar width + left padding + small margin
               sb_width = vsb.winfo_width() if vsb.winfo_ismapped() else 16
               new_w = max(100, event.width - sb_width - left_pad - 4)
               container_canvas.itemconfig(win_id, width=new_w)
           except Exception:
               pass

       container_canvas.bind("<Configure>", _on_canvas_configure)

       # expose inner_frame as main_container so existing code can use it
       main_container = inner_frame

       # keep canvas scrollregion updated when inner content changes
       def _on_configure(event):
           try:
               container_canvas.configure(scrollregion=container_canvas.bbox("all"))
           except Exception:
               pass

       inner_frame.bind("<Configure>", _on_configure)

       # Mouse wheel scrolling when pointer is over the canvas
       def _on_mousewheel(event):
           # Windows: event.delta is multiple of 120
           try:
               container_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
           except Exception:
               pass

       container_canvas.bind("<MouseWheel>", _on_mousewheel)
       # For Linux systems with button 4/5 wheel events
       container_canvas.bind("<Button-4>", lambda e: container_canvas.yview_scroll(-1, "units"))
       container_canvas.bind("<Button-5>", lambda e: container_canvas.yview_scroll(1, "units"))

       # Bind mouse wheel when the pointer is over the settings inner frame
       # This mirrors the Help tab behavior: scrolling works while the cursor
       # is over the content area and stops when it leaves.
       def _bind_mousewheel(event):
           try:
               container_canvas.bind_all("<MouseWheel>", _on_mousewheel)
               container_canvas.bind_all("<Button-4>", lambda e: container_canvas.yview_scroll(-1, "units"))
               container_canvas.bind_all("<Button-5>", lambda e: container_canvas.yview_scroll(1, "units"))
           except Exception:
               pass

       def _unbind_mousewheel(event):
           try:
               container_canvas.unbind_all("<MouseWheel>")
               container_canvas.unbind_all("<Button-4>")
               container_canvas.unbind_all("<Button-5>")
           except Exception:
               pass

       inner_frame.bind("<Enter>", _bind_mousewheel)
       inner_frame.bind("<Leave>", _unbind_mousewheel)

       pin_frame = tk.LabelFrame(main_container, text="Admin PIN", bg="black",
                           font=("Arial", 12, "bold"), fg="#5D3FD3")
       pin_frame.pack(fill="x", pady=(0, 20))

       tk.Label(pin_frame, text="Current PIN: " + "*" * len(self.admin_pin),
              bg="black", fg="white", font=("Arial", 11)).pack(pady=10)
       tk.Button(pin_frame, text="Change PIN", command=self.change_admin_pin,
               bg="blue", fg="white", font=("Arial", 11, "bold"),
               relief="raised", bd=2).pack(pady=5)

       # CSV File Location Section
       csv_frame = tk.LabelFrame(main_container, text="CSV File Location", bg="black",
                           font=("Arial", 12, "bold"), fg="#5D3FD3")
       csv_frame.pack(fill="x", pady=(0, 20))

       current_csv_label = tk.Label(csv_frame, text="Current CSV: {0}".format(os.path.basename(self.csv_file)),
                              bg="black", fg="white", font=("Arial", 11))
       current_csv_label.pack(pady=10)

       csv_path_label = tk.Label(csv_frame, text="Path: {0}".format(self.csv_file),
                           bg="black", fg="lightgray", font=("Arial", 9))
       csv_path_label.pack(pady=(0, 10))

       tk.Button(csv_frame, text="Change CSV Location", command=self.change_csv_location,
               bg="blue", fg="white", font=("Arial", 11, "bold"),
               relief="raised", bd=2).pack(pady=5)

       tk.Button(csv_frame, text="Import Attendance Data", command=self.import_attendance_data,
               bg="green", fg="white", font=("Arial", 11, "bold"),
               relief="raised", bd=2).pack(pady=5)

       # Students File Location Section
       students_frame = tk.LabelFrame(main_container, text="Students File Location", bg="black",
                                font=("Arial", 12, "bold"), fg="#5D3FD3")
       students_frame.pack(fill="x", pady=(0, 20))

       students_path = get_students_file()
       tk.Label(students_frame, text="Current Students: {0}".format(os.path.basename(students_path)),
              bg="black", fg="white", font=("Arial", 11)).pack(pady=6)
       tk.Label(students_frame, text="Path: {0}".format(students_path),
              bg="black", fg="lightgray", font=("Arial", 9)).pack(pady=(0, 8))
       tk.Button(students_frame, text="Change Students Location", command=self.change_students_location,
               bg="blue", fg="white", font=("Arial", 11, "bold"), relief="raised", bd=2).pack(pady=5)

       tk.Button(students_frame, text="Import Students Data", command=self.import_students_data,
               bg="green", fg="white", font=("Arial", 11, "bold"), relief="raised", bd=2).pack(pady=5)

       # Guests File Location Section
       guests_frame = tk.LabelFrame(main_container, text="Guests File Location", bg="black",
                              font=("Arial", 12, "bold"), fg="#5D3FD3")
       guests_frame.pack(fill="x", pady=(0, 20))

       guests_path = get_guests_file()
       tk.Label(guests_frame, text="Current Guests CSV: {0}".format(os.path.basename(guests_path)),
              bg="black", fg="white", font=("Arial", 11)).pack(pady=6)
       tk.Label(guests_frame, text="Path: {0}".format(guests_path),
              bg="black", fg="lightgray", font=("Arial", 9)).pack(pady=(0, 8))
       tk.Button(guests_frame, text="Change Guests Location", command=self.change_guests_location,
               bg="blue", fg="white", font=("Arial", 11, "bold"), relief="raised", bd=2).pack(pady=5)



       logo_frame = tk.LabelFrame(main_container, text="Logo Settings", bg="black",
                            font=("Arial", 12, "bold"), fg="#5D3FD3")
       logo_frame.pack(fill="x", pady=(0, 20))

       tk.Label(logo_frame, text="Current logo: {0}".format(os.path.basename(self.logo_file)),
              bg="black", fg="white", font=("Arial", 11)).pack(pady=10)
       tk.Button(logo_frame, text="Choose Logo", command=self.change_logo,
               bg="blue", fg="white", font=("Arial", 11, "bold"),
               relief="raised", bd=2).pack(pady=5)

       color_frame = tk.LabelFrame(main_container, text="Appearance", bg="black",
                            font=("Arial", 12, "bold"), fg="#5D3FD3")
       color_frame.pack(fill="x", pady=(0, 20))

       color_display = tk.Label(color_frame, text="Current header color",
                           bg=self.header_color, fg="white", font=("Arial", 11, "bold"),
                           relief="sunken", bd=2, width=20, height=2)
       color_display.pack(pady=10)
       tk.Button(color_frame, text="Choose Color", command=self.change_header_color,
               bg="blue", fg="white", font=("Arial", 11, "bold"),
               relief="raised", bd=2).pack(pady=5)

       close_frame = tk.Frame(main_container, bg="black")
       close_frame.pack(fill="x", pady=(20, 0))
       tk.Button(close_frame, text="Close", command=lambda: admin_window.destroy(),
               bg="red", fg="white", font=("Arial", 12, "bold"),
               relief="raised", bd=2).pack()

    def setup_help_tab(self, notebook):
      help_frame = tk.Frame(notebook, bg="black")
      notebook.add(help_frame, text="Help")
      admin_window = notebook.master

      title_frame = tk.Frame(help_frame, bg="black")
      title_frame.pack(fill="x", padx=20, pady=(20, 10))

      tk.Label(title_frame, text="Attendance System Help", bg="black", fg="white",
           font=("Arial", 18, "bold")).pack()

      text_frame = tk.Frame(help_frame, bg="black")
      text_frame.pack(fill="both", expand=True, padx=20, pady=10)

      text_widget = tk.Text(text_frame, wrap="word", font=("Arial", 11),
                bg="black", fg="white", relief="flat",
                borderwidth=0, padx=10, pady=10)
      scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
      text_widget.configure(yscrollcommand=scrollbar.set)

      help_text = """How to Use:
Tap a student name to mark them Present
Tap again to remove them from today's attendance
Use Guest Sign-In for visitors or unlisted students
Press Escape or F11 to toggle fullscreen mode

Admin Features:
View and download attendance records as CSV
Add, edit, or remove students from the system
Change admin PIN for security
Customize CSV file location and name
Customize logo and header colors
Access help and system information

File Locations:
Attendance data: Configurable (default: data/attendance.csv)
Student list: data/students.json
Configuration: data/config.json
Assets: assets/ folder

Windows 7 & Python 3.8 Compatibility:
Works with Python 3.8.0 and newer
Fallback modes for image loading
Compatible with older tkinter versions
Handles encoding issues gracefully

Keyboard Shortcuts:
Escape: Toggle fullscreen
F11: Toggle fullscreen"""

      text_widget.insert("1.0", help_text)
      text_widget.configure(state="disabled")

      text_widget.pack(side="left", fill="both", expand=True)
      scrollbar.pack(side="right", fill="y")

      btn_frame = tk.Frame(help_frame, bg="black")
      btn_frame.pack(fill="x", padx=20, pady=20)

      btn_frame.grid_columnconfigure(0, weight=1)
      btn_frame.grid_columnconfigure(1, weight=0)
      btn_frame.grid_columnconfigure(2, weight=0)
      btn_frame.grid_columnconfigure(3, weight=0)
      btn_frame.grid_columnconfigure(4, weight=1)

      tk.Button(btn_frame, text="Open GitHub Repository",
          command=self.open_github,
          bg="blue", fg="white", font=("Arial", 12, "bold"),
          relief="raised", bd=2, width=25).grid(row=0, column=1, padx=10)

      tk.Button(btn_frame, text="System Info",
          command=self.show_system_info,
          bg="gray", fg="white", font=("Arial", 12, "bold"),
          relief="raised", bd=2).grid(row=0, column=2, padx=10)

      tk.Button(btn_frame, text="Close",
          command=lambda: admin_window.destroy(),
          bg="red", fg="white", font=("Arial", 12, "bold"),
          relief="raised", bd=2).grid(row=0, column=3, padx=10)

    # ---------------- Utilities ----------------
    def refresh_attendance_tree(self, tree):
        global attendance_data
        for item in tree.get_children():
            tree.delete(item)
        for row in attendance_data:
            tree.insert("", "end", values=(
                row.get("Date", ""),
                row.get("Name", ""),
                row.get("Status", "")
            ))

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

    def refresh_students_listbox(self):
        self.students_listbox.delete(0, tk.END)
        for student in self.students:
            self.students_listbox.insert(tk.END, student)

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
        file_path = filedialog.askdirectory(title="Choose Backup Folder")
        if not file_path:
            return
        try:
            os.makedirs(file_path, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", "Could not create folder: {0}".format(e))
            return
        self.backup_location = file_path
        self.config["backup_location"] = file_path
        save_config(self.config)
        if path_label:
            try:
                path_label.configure(text="Path: {0}".format(self.backup_location))
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
                    self.backup_status_label.configure(text=("Last backup: {0}".format(self.last_backup)))
            except Exception:
                pass

            if notify:
                messagebox.showinfo("Backup", "Backup completed: {0}".format(dest))
            return True
        except Exception as e:
            if notify:
                messagebox.showerror("Backup Error", "Backup failed: {0}".format(e))
            return False

    def _backup_worker(self):
        """Internal worker invoked by Tk after scheduling; performs backup and reschedules."""
        try:
            self.perform_backup(notify=False)
        except Exception:
            pass
        # schedule next run in one hour
        try:
            self.backup_job = self.root.after(60 * 60 * 1000, self._backup_worker)
        except Exception:
            self.backup_job = None

    def start_backups(self):
        """Start hourly backups (immediate run + schedule)."""
        if not self.backup_location:
            messagebox.showwarning("Backup", "Choose a backup folder first")
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
            self.backup_job = self.root.after(60 * 60 * 1000, self._backup_worker)
        except Exception:
            self.backup_job = None
        return True

    def stop_backups(self):
        """Stop scheduled hourly backups."""
        try:
            if getattr(self, 'backup_job', None):
                self.root.after_cancel(self.backup_job)
        except Exception:
            pass
        self.backup_job = None
        self.backup_enabled = False
        self.config["backup_enabled"] = False
        save_config(self.config)

# ---------------- Main Application ----------------
def main():
    init_files()
    root = tk.Tk()

    try:
        root.minsize(800, 600)
        if os.path.exists(ICON_FILE) and PIL_AVAILABLE:
            try:
                root.iconbitmap(default=ICON_FILE)
            except Exception:
                pass
    except Exception as e:
        print("Window setup warning: {0}".format(e))

    app = AttendanceApp(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application terminated by user")
    except Exception as e:
        print("Application error: {0}".format(e))
        try:
            messagebox.showerror("Application Error", "An error occurred: {0}".format(e))
        except:
            print("Could not display error message")

if __name__ == "__main__":
    main()
