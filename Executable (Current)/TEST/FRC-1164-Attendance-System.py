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

# ---------------- Config ----------------
DATA_FOLDER = "data"
ASSETS_FOLDER = "assets"
DEFAULT_FILENAME = os.path.join(DATA_FOLDER, "attendance.csv")
STUDENTS_FILE = os.path.join(DATA_FOLDER, "students.json")
CONFIG_FILE = os.path.join(DATA_FOLDER, "config.json")
LOGO_FILE = os.path.join(ASSETS_FOLDER, "logo.png")
GEAR_FILE = os.path.join(ASSETS_FOLDER, "gear.png")
ICON_FILE = os.path.join(ASSETS_FOLDER, "icon.ico")

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
    try:
        config = load_config()
        csv_path = config.get("csv_file", DEFAULT_FILENAME)
        # Ensure the directory exists
        csv_dir = os.path.dirname(csv_path)
        if csv_dir and not os.path.exists(csv_dir):
            os.makedirs(csv_dir, exist_ok=True)
        return csv_path
    except Exception:
        return DEFAULT_FILENAME

def init_files():
    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(ASSETS_FOLDER, exist_ok=True)

    # Get the current CSV file path
    csv_file = get_csv_file()
    
    # Ensure CSV header contains Member Status column
    if not os.path.exists(csv_file):
        try:
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Name", "Status", "Member Status"])
        except Exception as e:
            print("Could not create attendance CSV:", e)

    if not os.path.exists(STUDENTS_FILE):
        try:
            with open(STUDENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(["placeholder1", "placeholder2", "placeholder3", "placeholder4"], f, indent=2)
        except Exception as e:
            print("Could not create students.json:", e)

    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
        except Exception as e:
            print("Could not create config.json:", e)

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
        with open(STUDENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_students(students):
    try:
        with open(STUDENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(students, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print("save_students error:", e)
        return False

def already_checked_in(name, date_iso):
    csv_file = get_csv_file()
    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                # row keys may be missing if the CSV is malformed; use get()
                if row.get("Date") == date_iso and row.get("Name") == name and row.get("Status") == "Present":
                    return True
    except FileNotFoundError:
        return False
    except Exception as e:
        print("already_checked_in error:", e)
        return False
    return False

def remove_attendance(name, date_iso):
    csv_file = get_csv_file()
    updated_rows = []
    removed = False
    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (row.get("Date") == date_iso and row.get("Name") == name and
                        row.get("Status") == "Present" and not removed):
                    removed = True
                    continue
                updated_rows.append(row)
        # Write header and rows back
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["Date", "Name", "Status", "Member Status"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in updated_rows:
                # ensure all keys exist
                out = {k: r.get(k, "") for k in fieldnames}
                writer.writerow(out)
    except FileNotFoundError:
        return False
    except Exception as e:
        print("remove_attendance error:", e)
        return False
    return removed

def mark_attendance(name, status="Present", member_status="Member"):
    csv_file = get_csv_file()
    today = datetime.date.today().isoformat()
    # Toggle behavior: if already present, remove them and report removed
    if status == "Present" and already_checked_in(name, today):
        removed = remove_attendance(name, today)
        if removed:
            return False, "{0} removed from today's attendance.".format(name)
        else:
            return False, "{0} is already marked Present today.".format(name)
    # Append row with Member Status
    try:
        with open(csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([today, name, status, member_status])
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

        # Admin button (gear)
        self.setup_admin_button()

        # Guest Sign In
        self.guest_frame = tk.Frame(root, bg="black")
        self.guest_frame.pack(fill="x", pady=(10, 0))
        self.guest_btn = tk.Button(self.guest_frame, text="👤  Guest Sign In  —  Tap to Enter Your Name",
                                   command=self.guest_sign_in, bg="#333", fg="white",
                                   font=("Arial", 14, "bold"), height=2, relief="raised")
        self.guest_btn.pack(fill="x", padx=12, pady=12)

        # Search bar
        self.search_frame = tk.Frame(root, bg="black")
        self.search_frame.pack(fill="x", pady=(5, 0))
        search_container = tk.Frame(self.search_frame, bg="#333", relief="raised", bd=2)
        search_container.pack(fill="x", padx=12, pady=5)
        search_inner = tk.Frame(search_container, bg="#333")
        search_inner.pack(fill="x", padx=10, pady=8)
        tk.Label(search_inner, text="🔍", bg="#333", fg="white", font=("Arial", 16)).pack(side="left", padx=(0, 8))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_inner, textvariable=self.search_var,
                                     font=("Arial", 14), bg="white", fg="black",
                                     relief="flat", bd=0)
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.insert(0, "Search for a student...")
        self.clear_btn = tk.Button(search_inner, text="✕", command=self.clear_search,
                                   bg="#555", fg="white", font=("Arial", 12, "bold"),
                                   relief="flat", bd=0, width=3)
        self.clear_btn.pack(side="right", padx=(8, 0))
        self.search_var.trace("w", self.on_search_change)
        self.search_entry.bind("<FocusIn>", self.on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self.on_search_focus_out)

        # Scrollable student list container
        self.container = tk.Frame(root, bg="black")
        self.container.pack(fill="both", expand=True)

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

        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Load students
        self.students = load_students()
        self.filtered_students = self.students.copy()
        self.build_student_buttons()

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
            self.admin_btn = tk.Button(self.header, text="⚙ Admin", command=self.admin_panel,
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
            self.search_entry.configure(fg="black")

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
        COLS = 4

        for c in range(COLS):
            self.student_frame.grid_columnconfigure(c, weight=1)

        if not sorted_students:
            no_results = tk.Label(self.student_frame, text="🔍 No students found matching your search",
                                  bg="black", fg="white", font=("Arial", 16))
            no_results.grid(row=0, column=0, columnspan=COLS, pady=50)
            return

        row, col = 0, 0
        # Choose a slightly smaller height when fullscreen
        btn_height = 3 if self.fullscreen else 2

        for name in sorted_students:
            checked = already_checked_in(name, today)
            text = "🙋 {0}".format(name) + (" ✅" if checked else "")
            btn = tk.Button(self.student_frame, text=text, width=20, height=btn_height,
                            command=lambda n=name: self.checkin(n),
                            bg="#444" if checked else "#333", fg="white",
                            font=("Arial", 14, "bold"), relief="raised", bd=3,
                            activebackground="#555", activeforeground="white",
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
        mark_attendance(name, "Present", "Member")
        self.build_student_buttons()

    def guest_sign_in(self):
        """Handle guest sign-in (no popups)"""
        name = simpledialog.askstring("Guest Sign In", "Enter your name:")
        if name and name.strip():
            mark_attendance(name.strip(), "Present", "Visitor")
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
        admin_win.configure(bg="white")

        # make modal-like
        admin_win.transient(self.root)
        admin_win.grab_set()

        notebook = ttk.Notebook(admin_win)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tabs
        self.setup_attendance_tab(notebook)
        self.setup_students_tab(notebook)
        self.setup_settings_tab(notebook)
        self.setup_help_tab(notebook)

    def setup_attendance_tab(self, notebook):
        frame = tk.Frame(notebook, bg="white")
        notebook.add(frame, text="📊 Attendance")
        admin_window = notebook.master

        # Treeview + scrollbars
        tree_frame = tk.Frame(frame, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("Date", "Name", "Status", "Member Status")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=15)
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
        csv_file = get_csv_file()
        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                r = csv.DictReader(f)
                for row in r:
                    tree.insert("", "end", values=(
                        row.get("Date", ""),
                        row.get("Name", ""),
                        row.get("Status", ""),
                        row.get("Member Status", "")
                    ))
        except Exception as e:
            print("Error loading attendance data:", e)
            tree.insert("", "end", values=("Error", "Could not load data", "Check file", "Error"))

        btn_frame = tk.Frame(frame, bg="white")
        btn_frame.pack(pady=10, fill="x", padx=10)

        tk.Button(btn_frame, text="📥 Download CSV", command=self.download_csv,
                  bg="green", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2).pack(side="left", padx=5)

        tk.Button(btn_frame, text="🔄 Refresh", command=lambda: self.refresh_attendance_tree(tree),
                  bg="blue", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2).pack(side="left", padx=5)

        tk.Button(btn_frame, text="❌ Close", command=lambda: admin_window.destroy(),
                  bg="red", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2).pack(side="right", padx=5)

    def setup_students_tab(self, notebook):
        frame = tk.Frame(notebook, bg="white")
        notebook.add(frame, text="👥 Students")
        admin_window = notebook.master

        list_frame = tk.Frame(frame, bg="white")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(list_frame, text="Current Students:", bg="white", fg="black",
                 font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 5))

        list_container = tk.Frame(list_frame, bg="white")
        list_container.pack(fill="both", expand=True)

        self.students_listbox = tk.Listbox(list_container, font=("Arial", 12),
                                          selectmode=tk.SINGLE, height=15)
        list_scrollbar = ttk.Scrollbar(list_container, orient="vertical",
                                       command=self.students_listbox.yview)
        self.students_listbox.configure(yscrollcommand=list_scrollbar.set)

        self.students_listbox.pack(side="left", fill="both", expand=True)
        list_scrollbar.pack(side="right", fill="y")

        self.refresh_students_listbox()

        btn_frame = tk.Frame(frame, bg="white")
        btn_frame.pack(pady=10, fill="x", padx=10)

        tk.Button(btn_frame, text="➕ Add Student", command=self.add_student,
                  bg="green", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2).pack(side="left", padx=5)
        tk.Button(btn_frame, text="✏ Edit Student", command=self.edit_student,
                  bg="orange", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2).pack(side="left", padx=5)
        tk.Button(btn_frame, text="🗑 Delete Student", command=self.delete_student,
                  bg="red", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2).pack(side="left", padx=5)
        tk.Button(btn_frame, text="❌ Close", command=lambda: admin_window.destroy(),
                  bg="darkred", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2).pack(side="right", padx=5)

    def setup_settings_tab(self, notebook):
        settings_frame = tk.Frame(notebook, bg="white")
        notebook.add(settings_frame, text="⚙ Settings")
        admin_window = notebook.master

        main_container = tk.Frame(settings_frame, bg="white")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        pin_frame = tk.LabelFrame(main_container, text="Admin PIN", bg="white",
                                 font=("Arial", 12, "bold"), fg="navy")
        pin_frame.pack(fill="x", pady=(0, 20))

        tk.Label(pin_frame, text="Current PIN: " + "*" * len(self.admin_pin),
                 bg="white", fg="black", font=("Arial", 11)).pack(pady=10)
        tk.Button(pin_frame, text="🔒 Change PIN", command=self.change_admin_pin,
                  bg="blue", fg="white", font=("Arial", 11, "bold"),
                  relief="raised", bd=2).pack(pady=5)

        # CSV File Location Section
        csv_frame = tk.LabelFrame(main_container, text="CSV File Location", bg="white",
                                 font=("Arial", 12, "bold"), fg="navy")
        csv_frame.pack(fill="x", pady=(0, 20))

        current_csv_label = tk.Label(csv_frame, text="Current CSV: {0}".format(os.path.basename(self.csv_file)),
                                     bg="white", fg="black", font=("Arial", 11))
        current_csv_label.pack(pady=10)
        
        csv_path_label = tk.Label(csv_frame, text="Path: {0}".format(self.csv_file),
                                 bg="white", fg="gray", font=("Arial", 9))
        csv_path_label.pack(pady=(0, 10))
        
        tk.Button(csv_frame, text="📂 Change CSV Location", command=self.change_csv_location,
                  bg="blue", fg="white", font=("Arial", 11, "bold"),
                  relief="raised", bd=2).pack(pady=5)

        logo_frame = tk.LabelFrame(main_container, text="Logo Settings", bg="white",
                                  font=("Arial", 12, "bold"), fg="navy")
        logo_frame.pack(fill="x", pady=(0, 20))

        tk.Label(logo_frame, text="Current logo: {0}".format(os.path.basename(self.logo_file)),
                 bg="white", fg="black", font=("Arial", 11)).pack(pady=10)
        tk.Button(logo_frame, text="🖼 Choose Logo", command=self.change_logo,
                  bg="blue", fg="white", font=("Arial", 11, "bold"),
                  relief="raised", bd=2).pack(pady=5)

        color_frame = tk.LabelFrame(main_container, text="Appearance", bg="white",
                                   font=("Arial", 12, "bold"), fg="navy")
        color_frame.pack(fill="x", pady=(0, 20))

        color_display = tk.Label(color_frame, text="Current header color",
                                 bg=self.header_color, fg="white", font=("Arial", 11, "bold"),
                                 relief="sunken", bd=2, width=20, height=2)
        color_display.pack(pady=10)
        tk.Button(color_frame, text="🎨 Choose Color", command=self.change_header_color,
                  bg="blue", fg="white", font=("Arial", 11, "bold"),
                  relief="raised", bd=2).pack(pady=5)

        close_frame = tk.Frame(main_container, bg="white")
        close_frame.pack(fill="x", pady=(20, 0))
        tk.Button(close_frame, text="❌ Close", command=lambda: admin_window.destroy(),
                  bg="red", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2).pack()

    def setup_help_tab(self, notebook):
        help_frame = tk.Frame(notebook, bg="white")
        notebook.add(help_frame, text="❓ Help")
        admin_window = notebook.master

        title_frame = tk.Frame(help_frame, bg="white")
        title_frame.pack(fill="x", padx=20, pady=(20, 10))

        tk.Label(title_frame, text="📖 Attendance System Help", bg="white", fg="navy",
                 font=("Arial", 18, "bold")).pack()

        text_frame = tk.Frame(help_frame, bg="white")
        text_frame.pack(fill="both", expand=True, padx=20, pady=10)

        text_widget = tk.Text(text_frame, wrap="word", font=("Arial", 11),
                              bg="white", fg="black", relief="flat",
                              borderwidth=0, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        help_text = """🎯 How to Use:
• Tap a student name to mark them Present
• Tap again to remove them from today's attendance
• Use Guest Sign-In for visitors or unlisted students
• Press Escape or F11 to toggle fullscreen mode

👨‍💼 Admin Features:
• View and download attendance records as CSV
• Add, edit, or remove students from the system
• Change admin PIN for security
• Customize CSV file location and name
• Customize logo and header colors
• Access help and system information

📁 File Locations:
• Attendance data: Configurable (default: data/attendance.csv)
• Student list: data/students.json
• Configuration: data/config.json
• Assets: assets/ folder

🔧 Windows 7 & Python 3.8 Compatibility:
• Works with Python 3.8.0 and newer
• Fallback modes for image loading
• Compatible with older tkinter versions
• Handles encoding issues gracefully

⚡ Keyboard Shortcuts:
• Escape: Toggle fullscreen
• F11: Toggle fullscreen"""

        text_widget.insert("1.0", help_text)
        text_widget.configure(state="disabled")

        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        btn_frame = tk.Frame(help_frame, bg="white")
        btn_frame.pack(fill="x", padx=20, pady=20)

        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=0)
        btn_frame.grid_columnconfigure(2, weight=0)
        btn_frame.grid_columnconfigure(3, weight=0)
        btn_frame.grid_columnconfigure(4, weight=1)

        tk.Button(btn_frame, text="🔗 Open GitHub Repository",
                  command=self.open_github,
                  bg="blue", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2, width=25).grid(row=0, column=1, padx=10)

        tk.Button(btn_frame, text="ℹ System Info",
                  command=self.show_system_info,
                  bg="gray", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2).grid(row=0, column=2, padx=10)

        tk.Button(btn_frame, text="❌ Close",
                  command=lambda: admin_window.destroy(),
                  bg="red", fg="white", font=("Arial", 12, "bold"),
                  relief="raised", bd=2).grid(row=0, column=3, padx=10)

    # ---------------- Utilities ----------------
    def refresh_attendance_tree(self, tree):
        for item in tree.get_children():
            tree.delete(item)
        csv_file = get_csv_file()
        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                r = csv.DictReader(f)
                for row in r:
                    tree.insert("", "end", values=(
                        row.get("Date", ""),
                        row.get("Name", ""),
                        row.get("Status", ""),
                        row.get("Member Status", "")
                    ))
        except Exception as e:
            print("refresh_attendance_tree error:", e)
            tree.insert("", "end", values=("Error", "Could not load data", "Check file", "Error"))

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
                    self.refresh_students_listbox()
                    self.build_student_buttons()
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
                        writer.writerow(["Date", "Name", "Status", "Member Status"])
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
