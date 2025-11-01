import os, json

CFG = os.path.join("data", "config.json")
user_home = os.path.expanduser("~")
docs_dir = os.path.join(user_home, "Documents", "FRC-Attendence-System")

if not os.path.exists(CFG):
    print("No config file found at:", CFG)
    raise SystemExit(0)

with open(CFG, "r", encoding="utf-8") as f:
    cfg = json.load(f)

changed = False
students_docs = os.path.join(docs_dir, "students.json")
guests_docs = os.path.join(docs_dir, "guests.csv")

# If the Documents copies exist, point config back to them (do not overwrite)
if os.path.exists(students_docs):
    cfg["students_file"] = students_docs
    changed = True

if os.path.exists(guests_docs):
    cfg["guests_file"] = guests_docs
    changed = True

if changed:
    with open(CFG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    print("Updated config to point to Documents files:")
    print(json.dumps(cfg, indent=2))
else:
    print("No students/guests files found in Documents at:", docs_dir)

print("data/students.json exists:", os.path.exists("data/students.json"))
print("data/guests.csv exists:", os.path.exists("data/guests.csv"))
print("config saved to:", CFG)
