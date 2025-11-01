import importlib.util
import json
import os

p = r"d:/Python Project/NEW/FRC-Attendence-System/Executable (Current)/FRC-1164-Attendance-System.py"
spec = importlib.util.spec_from_file_location("attmod", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

m.init_files()
print("init_files run")
cfg = m.load_config()
print("config:", json.dumps(cfg))
print("students_exists:", os.path.exists(m.get_students_file()))
print("students_path:", m.get_students_file())
print("guests_exists:", os.path.exists(m.get_guests_file()))
print("guests_path:", m.get_guests_file())
