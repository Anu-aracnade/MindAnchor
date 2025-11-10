# gui.py (v2.0: Modern UI Overhaul)
# Full rewrite of styles and layout for a "Duolingo/Gemini" feel.
# All functionality (camera, chatbot, DB) is preserved.

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading, time, os, random, sqlite3
from datetime import datetime

# Pillow for preview conversion
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# optional libs
try:
    import pygetwindow as gw
    PGW_AVAILABLE = True
except Exception:
    PGW_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except Exception:
    CV2_AVAILABLE = False

try:
    from pynput import mouse, keyboard
    PYNPUT_AVAILABLE = True
except Exception:
    PYNPUT_AVAILABLE = False

# local DB helper
import database

# --- NEW: Import the ChatbotManager ---
from chatbot_manager import ChatbotManager
# --- END NEW ---

# ------------- CONFIG -------------
# (All your existing config values are unchanged)
INACTIVITY_THRESHOLD = 25       # secs
ACTIVE_WINDOW_POLL = 7          # secs
FACE_POLL_INTERVAL = 0.35        # how often we grab a camera frame (secs)
FACE_MISSING_THRESHOLD = 4      # secs of continuous absence before flagging
INITIAL_FACE_TIMEOUT = 6        # secs to try find face at session start
FREEZE_COOLDOWN = 6             # cooldown after freeze
PREVIEW_SIZE = (320, 240)       # small preview window size

# ------------- NEW: COLOR & FONT PALETTE -------------
COLORS = {
    "BG_MAIN": "#F7F9FC",       # Main app background (light, clean)
    "BG_CARD": "#FFFFFF",       # Background for "cards"
    "TEXT": "#333333",          # Main text
    "TEXT_LIGHT": "#555555",    # Lighter text
    "PRIMARY": "#2A8CFF",       # A bright, modern blue
    "ACCENT_GREEN": "#00A877",  # A strong, positive green
    "DANGER_RED": "#E74C3C",    # A clear, modern red
    "DISABLED": "#BDBDBD",      # Disabled buttons/text
    "BORDER": "#E0E0E0"         # Subtle borders
}

FONTS = {
    "TITLE": ("Segoe UI", 32, "bold"),
    "H1": ("Segoe UI", 22, "bold"),
    "H2": ("Segoe UI", 16, "bold"),
    "SUBTITLE": ("Segoe UI", 11, "normal"),
    "BODY": ("Segoe UI", 10, "normal"),
    "BODY_BOLD": ("Segoe UI", 10, "bold"),
    "TIMER": ("Segoe UI Semibold", 36, "bold"),
    "CHAT_TEXT": ("Segoe UI", 9, "normal")
}
# ------------- END NEW PALETTE -------------


# ------------- static lists -------------
SUBJECT_SUGGESTIONS = ["Mathematics","Physics","Chemistry","Data Structures","C Programming",
                       "C++","Python","AI/ML","Web Development","Databases","Operating Systems",
                       "Electronics","Robotics","Assignments","Revision","Reading","Practice Problems"]

ENCOURAGEMENTS = ["Nice! Keep the focus 🔥","You're doing great — stay steady 💪",
                  "Small wins add up — keep going!","Breathe. One minute at a time.",
                  "Discipline beats motivation — you're building it!","Eyes on the goal — you got this!",
                  "Stay honest with yourself — every click counts.","Focus is a muscle — you're training it!"]

# ------------- app state -------------
class AppState:
    # (Unchanged)
    def __init__(self):
        self.root = None
        self.container = None
        self.style = None
        self.current_user_id = None
        self.total_sessions = 2
        self.current_session_index = 0
        self.current_session_results = []
        # runtime
        self._stop_event = None
        self._last_activity = None
        self._session_row_id = None
        self._freeze_shown = False
        self._last_freeze_time = 0

        # camera shared state
        self._cam = None
        self._cam_thread = None
        self._latest_frame = None      # BGR numpy array
        self._last_face_time = 0
        self._preview_win = None
        self._preview_label = None
        
        # --- NEW: Add chat_manager to app state ---
        self.chat_manager = None
        # --- END NEW ---

app_state = AppState()

# ------------- NEW: MODERN STYLES (THE CORE)-------------
def apply_styles(root):
    style = ttk.Style(root)
    
    # Use 'clam' for more styling control
    try:
        style.theme_use('clam')
    except Exception:
        pass

    # --- General App ---
    style.configure(".", 
        background=COLORS["BG_MAIN"],
        foreground=COLORS["TEXT"],
        font=FONTS["BODY"])
    
    style.configure("TFrame", 
        background=COLORS["BG_MAIN"])
    
    # --- "Card" Style (for centered content) ---
    style.configure("Card.TFrame", 
        background=COLORS["BG_CARD"],
        relief="solid",
        borderwidth=1,
        bordercolor=COLORS["BORDER"])
    
    # --- Labels ---
    style.configure("Title.TLabel", 
        font=FONTS["TITLE"], 
        foreground=COLORS["PRIMARY"], 
        background=COLORS["BG_CARD"])
    style.configure("Subtitle.TLabel", 
        font=FONTS["SUBTITLE"], 
        foreground=COLORS["TEXT_LIGHT"], 
        background=COLORS["BG_CARD"])
    style.configure("H1.TLabel", 
        font=FONTS["H1"], 
        foreground=COLORS["TEXT"], 
        background=COLORS["BG_CARD"])
    style.configure("H2.TLabel", 
        font=FONTS["H2"], 
        foreground=COLORS["TEXT"], 
        background=COLORS["BG_MAIN"]) # Note: Main BG
    style.configure("TLabel", 
        background=COLORS["BG_CARD"],
        foreground=COLORS["TEXT"],
        font=FONTS["BODY"])
    
    # --- Buttons (Modern, Flat, Duolingo-style) ---
    style.configure("TButton", 
        font=FONTS["BODY_BOLD"],
        relief="flat",
        borderwidth=0,
        padding=(14, 10))
    
    # Accent Button (Green)
    style.configure("Accent.TButton", 
        background=COLORS["ACCENT_GREEN"], 
        foreground="#FFFFFF")
    style.map("Accent.TButton",
        background=[('active', '#007A55'), ('disabled', COLORS["DISABLED"])])

    # Danger Button (Red)
    style.configure("Danger.TButton", 
        background=COLORS["DANGER_RED"], 
        foreground="#FFFFFF")
    style.map("Danger.TButton",
        background=[('active', '#C0392B'), ('disabled', COLORS["DISABLED"])])
    
    # Standard Button (White card)
    style.configure("Card.TButton", 
        background=COLORS["BG_CARD"], 
        foreground=COLORS["PRIMARY"],
        relief="solid",
        bordercolor=COLORS["BORDER"],
        borderwidth=1)
    style.map("Card.TButton",
        background=[('active', '#F0F0F0')])

    # --- Inputs ---
    style.configure("TEntry", 
        font=FONTS["BODY"],
        padding=8,
        relief="solid",
        fieldbackground=COLORS["BG_CARD"],
        bordercolor=COLORS["BORDER"],
        borderwidth=1)
    style.map("TEntry",
        bordercolor=[('focus', COLORS["PRIMARY"])])

    style.configure("TCombobox", 
        font=FONTS["BODY"],
        padding=8,
        relief="flat",
        fieldbackground=COLORS["BG_CARD"],
        bordercolor=COLORS["BORDER"],
        borderwidth=1)
    style.map("TCombobox",
        bordercolor=[('focus', COLORS["PRIMARY"])],
        background=[('readonly', COLORS["BG_CARD"])])
    
    # --- Progress Bar ---
    style.configure("green.Horizontal.TProgressbar",
        troughcolor=COLORS["BORDER"],
        background=COLORS["ACCENT_GREEN"],
        thickness=10)

    return style
# ------------- END NEW STYLES -------------


# --- Helper for layout transitions ---
def show_centered_card(container):
    """Destroys old widgets and shows a new centered 'Card' frame."""
    for w in container.winfo_children():
        w.destroy()
    
    # This frame fills the *whole* container, giving us the main BG color
    base_frame = ttk.Frame(container, style="TFrame")
    base_frame.pack(expand=True, fill="both")

    # This is the "card" that floats in the middle
    card = ttk.Frame(base_frame, style="Card.TFrame", padding=40)
    card.place(relx=0.5, rely=0.5, anchor="center")
    
    return card

# ---------- UI: welcome (NEW GEMINI/DUOLINGO LAYOUT) ----------
def show_welcome_frame(root, container, style):
    frame = show_centered_card(container) # Use the new card layout

    ttk.Label(frame, text="🧭 MindAnchor", style="Title.TLabel").pack(pady=(10, 5))
    ttk.Label(frame, text="Anchor your mind. Reduce distractions. Study smarter.", 
              style="Subtitle.TLabel").pack(pady=(0, 25))
    
    ttk.Label(frame, 
              text="A minimal full-screen focus app: track sessions, auto-detect distractions, and get actionable suggestions.",
              wraplength=450, 
              justify="center", 
              font=FONTS["BODY"],
              style="TLabel").pack(pady=(0, 30))
    
    ttk.Button(frame, text="Get Started", 
               style="Accent.TButton", 
               command=lambda: show_user_details_frame(root, container, style)).pack(pady=10, ipady=4, ipadx=10)
    
    ttk.Label(frame, text="Press Esc to exit fullscreen", 
              style="Subtitle.TLabel", 
              font=FONTS["SUBTITLE"]).pack(side="bottom", pady=(30, 0))

# ---------- user details (NEW CARD LAYOUT) ----------
def show_user_details_frame(root, container, style):
    frame = show_centered_card(container) # Use the new card layout

    ttk.Label(frame, text="Tell us about yourself", style="H1.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 30))

    ttk.Label(frame, text="Full name:").grid(row=1, column=0, sticky="e", padx=(10,5), pady=8)
    name_var = tk.StringVar()
    name_entry = ttk.Entry(frame, textvariable=name_var, width=40)
    name_entry.grid(row=1, column=1, sticky="w", pady=8)
    name_entry.focus()

    ttk.Label(frame, text="Country:").grid(row=2, column=0, sticky="e", padx=(10,5), pady=8)
    country_var = tk.StringVar()
    country_cb = ttk.Combobox(frame, textvariable=country_var, 
                                values=["India","United States","United Kingdom","Canada","Australia","Other"], width=37)
    country_cb.grid(row=2, column=1, sticky="w", pady=8); country_cb.set("India")

    ttk.Label(frame, text="Age:").grid(row=3, column=0, sticky="e", padx=(10,5), pady=8)
    age_var = tk.StringVar()
    age_entry = ttk.Entry(frame, textvariable=age_var, width=10)
    age_entry.grid(row=3, column=1, sticky="w", pady=8)

    ttk.Label(frame, text="Gender:").grid(row=4, column=0, sticky="e", padx=(10,5), pady=8)
    gender_var = tk.StringVar()
    gender_cb = ttk.Combobox(frame, textvariable=gender_var, 
                               values=["Male","Female","Other","Prefer not to say"], width=20)
    gender_cb.grid(row=4, column=1, sticky="w", pady=8); gender_cb.set("Prefer not to say")

    ttk.Label(frame, text="Primary interest:").grid(row=5, column=0, sticky="e", padx=(10,5), pady=8)
    interest_var = tk.StringVar()
    interest_cb = ttk.Combobox(frame, textvariable=interest_var, 
                                   values=["Studying","Programming","AI/ML","Music","Sports","Reading"], width=37)
    interest_cb.grid(row=5, column=1, sticky="w", pady=8); interest_cb.set("Studying")

    def on_save():
        name = name_var.get().strip(); country = country_var.get().strip(); age_text = age_var.get().strip()
        gender = gender_var.get().strip(); interest = interest_var.get().strip()
        if not name: messagebox.showwarning("Validation","Please enter your full name"); return
        if not age_text.isdigit(): messagebox.showwarning("Validation","Please enter a numeric age"); return
        age = int(age_text)
        if age <=0 or age > 120: messagebox.showwarning("Validation","Please enter a realistic age"); return
        uid = database.save_user(name, country, age, gender, interest)
        if uid:
            app_state.current_user_id = uid
            messagebox.showinfo("Saved", f"Welcome, {name.split()[0]}! Your profile is saved.")
            show_session_planner(root, container, app_state.style)
        else:
            messagebox.showerror("DB", "Could not save user.")

    ttk.Button(frame, text="Save & Continue", style="Accent.TButton", command=on_save).grid(row=6, column=0, columnspan=2, pady=(25,6), ipady=4, ipadx=10)
    frame.grid_columnconfigure(0, weight=1); frame.grid_columnconfigure(1, weight=2)

# ---------- session planner (NEW CARD LAYOUT) ----------
def show_session_planner(root, container, style):
    frame = show_centered_card(container) # Use the new card layout

    ttk.Label(frame, text="Create your session", style="H1.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 25))

    ttk.Label(frame, text="Session name (what are you studying?):").grid(row=1, column=0, sticky="e", padx=(10,5), pady=8)
    sess_name_var = tk.StringVar()
    sess_cb = ttk.Combobox(frame, textvariable=sess_name_var, values=SUBJECT_SUGGESTIONS, width=40)
    sess_cb.grid(row=1, column=1, sticky="w", pady=8); sess_cb.set(SUBJECT_SUGGESTIONS[0])

    ttk.Label(frame, text="Duration (minutes):").grid(row=2, column=0, sticky="e", padx=(10,5), pady=8)
    duration_var = tk.StringVar()
    duration_entry = ttk.Entry(frame, textvariable=duration_var, width=10)
    duration_entry.grid(row=2, column=1, sticky="w", pady=8); duration_var.set("25")

    ttk.Label(frame, text="Allowed apps (comma-separated, optional):").grid(row=3, column=0, sticky="e", padx=(10,5), pady=8)
    allowed_var = tk.StringVar()
    allowed_entry = ttk.Entry(frame, textvariable=allowed_var, width=40)
    allowed_entry.grid(row=3, column=1, sticky="w", pady=8)

    def start_session_clicked():
        name = sess_name_var.get().strip(); duration_text = duration_var.get().strip(); allowed_text = allowed_var.get().strip()
        if not name: messagebox.showwarning("Validation","Please enter a session name"); return
        if not (duration_text.replace(".","",1).isdigit()): messagebox.showwarning("Validation","Enter duration in minutes (numbers)"); return
        minutes = float(duration_text)
        if minutes <= 0: messagebox.showwarning("Validation","Enter positive duration"); return
        allowed_apps = [a.strip().lower() for a in allowed_text.split(",") if a.strip()] if allowed_text else []
        start_focus_session(root, container, name, minutes, style, allowed_apps)

    ttk.Button(frame, text="Start your first session", style="Accent.TButton", command=start_session_clicked).grid(row=4, column=0, columnspan=2, pady=(25,6), ipady=4, ipadx=10)
    ttk.Label(frame, text="We will run 5 continuous sessions in this demo. You can stop anytime.",
              style="Subtitle.TLabel").grid(row=5, column=0, columnspan=2, pady=(15,0))
    frame.grid_columnconfigure(0, weight=1); frame.grid_columnconfigure(1, weight=2)

# ---------- core session (NEW FULL-SCREEN LAYOUT) ----------
def start_focus_session(root, container, session_name, minutes, style, allowed_apps=None):
    if allowed_apps is None: allowed_apps = []
    
    # This screen fills the whole area, no card
    for w in container.winfo_children(): w.destroy()
    frame = ttk.Frame(container, padding=40, style="TFrame")
    frame.pack(expand=True, fill="both")
    
    # Use pack for a simpler, centered vertical layout
    content_frame = ttk.Frame(frame, style="TFrame")
    content_frame.pack(expand=True, fill="x")

    ttk.Label(content_frame, text=f"Session {app_state.current_session_index + 1} of {app_state.total_sessions}", 
              style="H2.TLabel", background=COLORS["BG_MAIN"]).pack(anchor="center")
    ttk.Label(content_frame, text=f"Topic: {session_name}", 
              font=FONTS["H1"], background=COLORS["BG_MAIN"], foreground=COLORS["TEXT"]).pack(anchor="center", pady=(10, 6))

    total_seconds = int(minutes * 60 + 0.5)
    remaining = {"sec": total_seconds}
    distractions = {"count": 0}
    completed_flag = {"val": True}

    progress_var = tk.DoubleVar(value=100.0)
    progress = ttk.Progressbar(content_frame, 
                               style="green.Horizontal.TProgressbar", 
                               mode="determinate", 
                               maximum=100.0, 
                               variable=progress_var, 
                               length=800)
    progress.pack(pady=(20, 15))
    
    time_label_var = tk.StringVar(value=format_time(remaining["sec"]))
    time_label = ttk.Label(content_frame, 
                           textvariable=time_label_var, 
                           font=FONTS["TIMER"], 
                           background=COLORS["BG_MAIN"],
                           foreground=COLORS["TEXT"])
    time_label.pack(pady=(15, 15))

    blink_label = ttk.Label(content_frame, text="", 
                            font=FONTS["H2"], 
                            background=COLORS["BG_MAIN"])
    blink_label.pack()
    
    encourage_var = tk.StringVar(value=random.choice(ENCOURAGEMENTS))
    encourage_label = ttk.Label(content_frame, 
                                textvariable=encourage_var, 
                                font=FONTS["SUBTITLE"], 
                                foreground=COLORS["ACCENT_GREEN"],
                                background=COLORS["BG_MAIN"])
    encourage_label.pack(pady=(15, 6))

    controls = ttk.Frame(content_frame, style="TFrame")
    controls.pack(pady=(10, 20))

    def log_distraction():
        # (Function unchanged)
        distractions["count"] += 1
        encourage_var.set(f"Logged distraction. Stay honest — distractions: {distractions['count']}")
        if app_state._session_row_id:
            try:
                conn = sqlite3.connect(database.DB_PATH); cur = conn.cursor()
                cur.execute("UPDATE sessions SET distractions = ? WHERE id = ?", (distractions["count"], app_state._session_row_id))
                conn.commit(); conn.close()
            except Exception as e:
                print("DB update error:", e)
    
    # Use the new "Card.TButton" style for a "secondary" button
    btn_log = ttk.Button(controls, text="I got distracted (Log)", 
                         style="Card.TButton", 
                         command=log_distraction)
    btn_log.grid(row=0, column=0, padx=10)

    def end_session_early():
        # (Function unchanged)
        completed_flag["val"] = False
        ans = simpledialog.askinteger("Distractions", "Enter total number of distractions for this session (approx):", initialvalue=distractions["count"], minvalue=0)
        if ans is not None:
            distractions["count"] = ans
            if app_state._session_row_id:
                try:
                    conn = sqlite3.connect(database.DB_PATH); cur = conn.cursor()
                    cur.execute("UPDATE sessions SET distractions = ? WHERE id = ?", (distractions["count"], app_state._session_row_id))
                    conn.commit(); conn.close()
                except Exception as e:
                    print("DB update error:", e)
        finish_session()

    btn_end = ttk.Button(controls, text="End Session", 
                         style="Danger.TButton", 
                         command=end_session_early)
    btn_end.grid(row=0, column=1, padx=10)

    # --- NEW STYLED CHAT UI ---
    chat_frame = ttk.Frame(content_frame, style="Card.TFrame", padding=10)
    chat_frame.pack(pady=(15, 6), fill="x", expand=False, ipadx=100) # Use ipadx to constrain width
    
    # Chat display area
    chat_display = tk.Text(chat_frame, 
                           height=5, 
                           width=80, 
                           state="disabled", 
                           font=FONTS["CHAT_TEXT"],
                           background=COLORS["BG_CARD"],
                           foreground=COLORS["TEXT"],
                           borderwidth=0,
                           padx=5, pady=5,
                           relief="flat")
    chat_display.pack(pady=(4,4), fill="x", expand=True)
    
    # Add a subtle border
    chat_border = ttk.Separator(chat_frame, orient="horizontal")
    chat_border.pack(fill="x", expand=True, pady=(0, 5))

    # Input frame
    chat_input_frame = ttk.Frame(chat_frame, style="Card.TFrame") # White BG
    chat_input_frame.pack(fill="x", expand=True)
    
    chat_var = tk.StringVar()
    chat_entry = ttk.Entry(chat_input_frame, textvariable=chat_var, width=70, font=FONTS["CHAT_TEXT"])
    chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

    def add_to_chat(sender, message):
        """Helper to add text to the chat box"""
        chat_display.config(state="normal")
        chat_display.insert("end", f"{sender}: {message}\n")
        chat_display.config(state="disabled")
        chat_display.see("end") # Auto-scroll

    def get_response_threaded(prompt):
        """Runs the AI in a thread to prevent GUI freezing"""
        try:
            response = app_state.chat_manager.get_response(prompt)
            app_state.root.after(0, lambda: add_to_chat("Bot", response))
        except Exception as e:
            app_state.root.after(0, lambda: add_to_chat("Error", f"Could not get response: {e}"))

    def send_chat_message():
        prompt = chat_var.get().strip()
        if not prompt: return
        
        add_to_chat("You", prompt)
        chat_var.set("") # Clear the entry box
        
        add_to_chat("Bot", "...") # Show "thinking..."
        threading.Thread(target=get_response_threaded, args=(prompt,), daemon=True).start()

    chat_button = ttk.Button(chat_input_frame, text="Ask", 
                             style="Accent.TButton", 
                             command=send_chat_message)
    chat_button.pack(side="right")
    
    chat_entry.bind("<Return>", lambda event: send_chat_message())
    add_to_chat("Bot", f"Hi! I'm Anchor. Ask me for a tip or about your stats!")
    
    # --- END NEW CHAT UI ---

    def update_ui_each_second():
        sec = remaining["sec"]
        time_label_var.set(format_time(sec))
        pct = (sec / total_seconds) * 100 if total_seconds > 0 else 0
        progress_var.set(pct)
        if sec <= 10:
            blink_label.config(text="Ending soon! Stay focused!", foreground=COLORS["DANGER_RED"])
        else:
            blink_label.config(text="")

    # (All other functions: rotate_encouragements, DB creation, 
    #  listeners, monitors, camera_thread_func, etc. are
    #  100% UNCHANGED and are just copied below for completeness)
    
    # --- All remaining functions in start_focus_session ---
    
    enc_index = {"i": 0}
    def rotate_encouragements():
        enc_index["i"] = (enc_index["i"] + 1) % len(ENCOURAGEMENTS)
        encourage_var.set(ENCOURAGEMENTS[enc_index["i"]])
        app_state.root.after(15000, rotate_encouragements)

    # create DB session row at start
    try:
        conn = sqlite3.connect(database.DB_PATH); cur = conn.cursor()
        cur.execute("INSERT INTO sessions (user_id, session_name, duration_sec, distractions, completed, start_time) VALUES (?, ?, ?, ?, ?, ?)",
                    (app_state.current_user_id, session_name, total_seconds, 0, 0, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit(); app_state._session_row_id = cur.lastrowid; conn.close()
    except Exception as e:
        print("Could not create session row:", e); app_state._session_row_id = None

    # detection control
    stop_event = threading.Event()
    app_state._stop_event = stop_event
    app_state._last_activity = time.time()
    app_state._freeze_shown = False
    app_state._last_freeze_time = 0
    app_state._latest_frame = None
    app_state._last_face_time = time.time()

    # input listeners
    keyboard_listener = None; mouse_listener = None
    def on_any_activity(*args, **kwargs): app_state._last_activity = time.time()

    def start_input_listeners():
        nonlocal keyboard_listener, mouse_listener
        if not PYNPUT_AVAILABLE: return
        try:
            keyboard_listener = keyboard.Listener(on_press=lambda k: on_any_activity())
            mouse_listener = mouse.Listener(on_move=lambda x,y: on_any_activity(), on_click=lambda x,y,b,m: on_any_activity())
            keyboard_listener.daemon = True; mouse_listener.daemon = True
            keyboard_listener.start(); mouse_listener.start()
        except Exception as e:
            print("pynput start error:", e)

    def stop_input_listeners():
        try:
            if keyboard_listener and PYNPUT_AVAILABLE: keyboard_listener.stop()
            if mouse_listener and PYNPUT_AVAILABLE: mouse_listener.stop()
        except Exception:
            pass

    # active-window monitor
    def active_window_monitor():
        if not PGW_AVAILABLE or not allowed_apps:
            return
        while not stop_event.is_set() and remaining["sec"] > 0:
            try:
                aw = gw.getActiveWindow()
                win_title = aw.title.lower() if aw and aw.title else ""
                if allowed_apps and win_title:
                    if not any(keyword in win_title for keyword in allowed_apps):
                        app_state.root.after(0, lambda: handle_distraction("switched_app"))
                        time.sleep(5)
                time.sleep(ACTIVE_WINDOW_POLL)
            except Exception as e:
                print("active_window_monitor error:", e); time.sleep(ACTIVE_WINDOW_POLL)

    # CAMERA THREAD + FACE DETECTION (single camera instance)
    def camera_thread_func():
        # only run if cv2 available
        if not CV2_AVAILABLE:
            return
        try:
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # try directshow on Windows
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
        except Exception:
            try:
                cap = cv2.VideoCapture(0)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_FPS, 30)
            except Exception:
                cap = None
        if not cap or not cap.isOpened():
            print("Camera not available or cannot be opened.")
            return
        app_state._cam = cap
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)
        # initial face detection window
        initial_deadline = time.time() + INITIAL_FACE_TIMEOUT
        found_initial = False
        while not stop_event.is_set() and time.time() < initial_deadline:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.2); continue
            app_state._latest_frame = frame.copy()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60,60))
            if len(faces) > 0:
                found_initial = True
                app_state._last_face_time = time.time()
                break
            time.sleep(FACE_POLL_INTERVAL)
        if not found_initial:
            app_state._last_face_time = time.time()
        # continuous monitoring
        while not stop_event.is_set() and remaining["sec"] > 0:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.2); continue
            app_state._latest_frame = frame.copy()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60,60))
            if len(faces) > 0:
                h, w = frame.shape[:2]
                max_area = 0
                for (x,y,fw,fh) in faces:
                    area = fw*fh
                    if area > max_area: max_area = area
                if max_area >= (0.01 * w * h):
                    app_state._last_face_time = time.time()
                    app_state._last_activity = time.time()
            else:
                pass
            # absence check
            if time.time() - app_state._last_face_time > FACE_MISSING_THRESHOLD:
                app_state.root.after(0, lambda: handle_distraction("no_face"))
                time.sleep(FREEZE_COOLDOWN)
            time.sleep(FACE_POLL_INTERVAL)
        try:
            cap.release()
        except Exception:
            pass
        app_state._cam = None

    # preview updater (Tk label) - uses latest_frame -> PIL -> PhotoImage
    def start_preview_window():
        if not CV2_AVAILABLE or not PIL_AVAILABLE:
            return
        if app_state._preview_win:
            return
        win = tk.Toplevel(app_state.root)
        win.title("Camera Preview")
        win.geometry(f"{PREVIEW_SIZE[0]}x{PREVIEW_SIZE[1]}")
        win.attributes("-topmost", True)
        # Remove title bar
        win.overrideredirect(True) 
        lbl = tk.Label(win)
        lbl.pack()
        app_state._preview_win = win
        app_state._preview_label = lbl
        
        # Make window draggable
        def move_window(event):
            win.geometry(f'+{event.x_root}+{event.y_root}')
        lbl.bind('<B1-Motion>', move_window)

        def update_preview():
            if app_state._latest_frame is not None:
                try:
                    frame = app_state._latest_frame.copy()
                    frame = frame[:, :, ::-1]  # BGR -> RGB
                    img = Image.fromarray(frame)
                    img = img.resize(PREVIEW_SIZE)
                    photo = ImageTk.PhotoImage(img)
                    lbl.config(image=photo)
                    lbl.image = photo
                except Exception as e:
                    pass
            if win.winfo_exists():
                win.after(int(FACE_POLL_INTERVAL*1000), update_preview)
            else:
                app_state._preview_win = None
                app_state._preview_label = None
        update_preview()

    def stop_preview_window():
        if app_state._preview_win:
            try:
                app_state._preview_win.destroy()
            except Exception:
                pass
            app_state._preview_win = None
            app_state._preview_label = None

    # central distraction handler (main thread)
    def handle_distraction(reason="inactivity"):
        if app_state._freeze_shown and (time.time() - app_state._last_freeze_time) < FREEZE_COOLDOWN:
            return
        app_state._freeze_shown = True
        app_state._last_freeze_time = time.time()
        
        distractions["count"] += 1
        if app_state._session_row_id:
            try:
                conn = sqlite3.connect(database.DB_PATH); cur = conn.cursor()
                cur.execute("UPDATE sessions SET distractions = ? WHERE id = ?", (distractions["count"], app_state._session_row_id))
                conn.commit(); conn.close()
            except Exception as e:
                print("DB update error:", e)
        
        # --- NEW STYLED POPUP ---
        freeze = tk.Toplevel(app_state.root)
        freeze.attributes("-fullscreen", True)
        freeze.configure(bg=COLORS["DANGER_RED"]) # Use new color
        
        lbl = tk.Label(freeze, text="🚫 Distraction Detected", 
                       fg="white", bg=COLORS["DANGER_RED"], 
                       font=FONTS["TITLE"])
        lbl.pack(expand=True, pady=(0, 20))
        
        lbl2 = tk.Label(freeze, text="Please verify to continue", 
                       fg="white", bg=COLORS["DANGER_RED"], 
                       font=FONTS["H1"])
        lbl2.pack(expand=True, pady=(0, 40))

        btn_frame = tk.Frame(freeze, bg=COLORS["DANGER_RED"])
        btn_frame.pack(pady=30)
        
        # Re-create ttk styles for this Toplevel
        s = ttk.Style(freeze)
        s.configure("Popup.TButton", 
                    font=FONTS["BODY_BOLD"], 
                    background="#FFFFFF", 
                    foreground=COLORS["DANGER_RED"],
                    padding=(20, 10))
        s.map("Popup.TButton", background=[('active', '#E0E0E0')])

        def verify_and_close():
            if CV2_AVAILABLE and app_state._latest_frame is not None:
                try:
                    frame = app_state._latest_frame.copy()
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                    fc = cv2.CascadeClassifier(cascade_path)
                    faces = fc.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60,60))
                    if len(faces) > 0:
                        freeze.destroy(); app_state._freeze_shown = False; app_state._last_activity = time.time(); app_state._last_face_time = time.time()
                        return
                    else:
                        messagebox.showwarning("Verification", "Face not detected. Please look at the camera.")
                        return
                except Exception as e:
                    print("verify error:", e)
                    messagebox.showwarning("Camera", "Verification failed due to camera error.")
                    freeze.destroy(); app_state._freeze_shown = False; app_state._last_activity = time.time(); return
            else:
                freeze.destroy(); app_state._freeze_shown = False; app_state._last_activity = time.time(); return

        def im_back_close():
            freeze.destroy(); app_state._freeze_shown = False; app_state._last_activity = time.time(); return

        vbtn = ttk.Button(btn_frame, text="Verify via Camera", 
                          style="Popup.TButton",
                          command=verify_and_close)
        vbtn.grid(row=0, column=0, padx=15)
        
        sbtn = ttk.Button(btn_frame, text="I'm back (resume)", 
                          style="Popup.TButton",
                          command=im_back_close)
        sbtn.grid(row=0, column=1, padx=15)
        # --- END NEW POPUP ---

    # stop monitors & camera
    def stop_all_monitors():
        try:
            stop_event.set()
            stop_input_listeners()
            stop_preview_window()
        except Exception:
            pass

    def finish_session():
        stop_all_monitors()
        elapsed = total_seconds - remaining["sec"]
        completed = completed_flag["val"] and (remaining["sec"] == 0)
        # finalize DB row
        if app_state._session_row_id:
            try:
                conn = sqlite3.connect(database.DB_PATH); cur = conn.cursor()
                cur.execute("UPDATE sessions SET duration_sec = ?, completed = ?, end_time = ? WHERE id = ?",
                            (elapsed, int(bool(completed)), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), app_state._session_row_id))
                conn.commit(); conn.close()
            except Exception as e:
                print("DB finalize error:", e)
        show_session_result(root, container, session_name, elapsed, distractions["count"], completed, style)

    def countdown_tick():
        if remaining["sec"] <= 0:
            finish_session(); return
        if app_state._stop_event.is_set(): # Check if session was stopped early
            return
        remaining["sec"] -= 1
        update_ui_each_second()
        app_state.root.after(1000, countdown_tick)

    # ... (start_input_listeners and stop_input_listeners are defined above) ...

    # start camera thread + preview if available
    if CV2_AVAILABLE:
        t = threading.Thread(target=camera_thread_func, daemon=True)
        t.start()
        app_state._cam_thread = t
        time.sleep(0.4) # small delay
        if PIL_AVAILABLE:
            start_preview_window()

    # start other monitors
    start_input_listeners()
    if PGW_AVAILABLE and allowed_apps:
        threading.Thread(target=active_window_monitor, daemon=True).start()

    # start UI loops
    rotate_encouragements()
    update_ui_each_second()
    app_state.root.after(1000, countdown_tick)


# ---------- remaining functions (NEW STYLES) ----------
def format_time(total_seconds):
    m = total_seconds // 60; s = total_seconds % 60; return f"{int(m):02d}:{int(s):02d}"

def show_session_result(root, container, session_name, elapsed_sec, distractions, completed, style):
    app_state.current_session_index += 1
    app_state.current_session_results.append({"session_name": session_name, "elapsed_sec": elapsed_sec, "distractions": distractions, "completed": bool(completed)})
    
    frame = show_centered_card(container) # Use card layout

    if completed and distractions == 0:
        title_text = "🎉 Perfect Focus!"; subtitle = "You completed the session distraction-free. Amazing work!"
    elif completed:
        title_text = "Nice Work!"; subtitle = f"You finished the session. Distractions: {distractions}."
    else:
        title_text = "Good Effort"; subtitle = f"You ended the session early. Distractions: {distractions} — that's okay, learn & try again."
    
    ttk.Label(frame, text=title_text, style="H1.TLabel").pack(pady=(10, 6))
    ttk.Label(frame, text=subtitle, style="Subtitle.TLabel", font=FONTS["SUBTITLE"]).pack(pady=(6, 20))
    ttk.Label(frame, text=f"Session: {session_name} | Time: {elapsed_sec//60} min {elapsed_sec%60} sec | Distractions: {distractions}",
              style="TLabel", font=FONTS["BODY"]).pack(pady=(6, 25))
    
    if app_state.current_session_index < app_state.total_sessions:
        ttk.Button(frame, text="Start Next Session", style="Accent.TButton", 
                   command=lambda: show_session_planner_next(root, container, style)).pack(pady=6, ipady=4, ipadx=10)
    else:
        ttk.Button(frame, text="Show Final Report", style="Accent.TButton", 
                   command=lambda: show_final_report(root, container, style)).pack(pady=6, ipady=4, ipadx=10)
    
    quote = random.choice(["Focus is the new superpower ⚡","Consistency compounds — keep going.","Progress > Perfection."])
    ttk.Label(frame, text=quote, font=FONTS["SUBTITLE"], foreground=COLORS["TEXT_LIGHT"], 
              style="Subtitle.TLabel").pack(pady=(30, 6))

def show_session_planner_next(root, container, style):
    frame = show_centered_card(container) # Use card layout
    
    prev = app_state.current_session_results[-1] if app_state.current_session_results else {}
    suggested = prev.get("session_name", "") if prev else ""
    
    ttk.Label(frame, text=f"Start Session {app_state.current_session_index + 1} of {app_state.total_sessions}", 
              style="H1.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 25))
    
    ttk.Label(frame, text="Session name:").grid(row=1, column=0, sticky="e", padx=(10,5), pady=8)
    sess_var = tk.StringVar()
    sess_cb = ttk.Combobox(frame, textvariable=sess_var, values=SUBJECT_SUGGESTIONS, width=40)
    sess_cb.grid(row=1, column=1, sticky="w", pady=8)
    if suggested: sess_cb.set(suggested)
    
    ttk.Label(frame, text="Duration (minutes):").grid(row=2, column=0, sticky="e", padx=(10,5), pady=8)
    dur_var = tk.StringVar()
    dur_entry = ttk.Entry(frame, textvariable=dur_var, width=10)
    dur_entry.grid(row=2, column=1, sticky="w", pady=8); dur_var.set("25")
    
    def start_next():
        name = sess_var.get().strip()
        if not name: messagebox.showwarning("Validation","Please enter a session name"); return
        try: minutes = float(dur_var.get())
        except: messagebox.showwarning("Validation","Enter valid duration in minutes"); return
        start_focus_session(root, container, name, minutes, style, allowed_apps=[])
    
    ttk.Button(frame, text="Start Session", style="Accent.TButton", 
               command=start_next).grid(row=3, column=0, columnspan=2, pady=(25, 6), ipady=4, ipadx=10)
    
    frame.grid_columnconfigure(0, weight=1); frame.grid_columnconfigure(1, weight=2)

def show_final_report(root, container, style):
    frame = show_centered_card(container) # Use card layout
    frame.config(padding=20) # smaller padding for this one
    
    ttk.Label(frame, text="Session Summary", style="H1.TLabel").pack(anchor="w", pady=(0,15))
    
    rows = database.fetch_sessions_for_user(app_state.current_user_id, limit=app_state.total_sessions)
    rows = rows[::-1]
    total_focus = sum(r[2] for r in rows) if rows else 0
    total_distractions = sum(r[3] for r in rows) if rows else 0
    completed_count = sum(1 for r in rows if r[4] == 1) if rows else 0
    avg_distractions = total_distractions / len(rows) if rows else 0
    
    ttk.Label(frame, 
              text=f"Total Focus Time: {total_focus//60} min | Avg Distractions: {avg_distractions:.2f} | Completed: {completed_count}/{len(rows)}",
              style="TLabel", font=FONTS["BODY_BOLD"]).pack(pady=(8,12), anchor="w")
    
    # --- STYLED CHART ---
    try:
        import matplotlib.pyplot as plt; import matplotlib
        matplotlib.use('Agg')
        plt.style.use('ggplot') # Use a clean style
        
        sess_names = [r[1] for r in rows]; durations = [r[2]/60.0 for r in rows]; distractions = [r[3] for r in rows]
        
        fig, ax1 = plt.subplots(figsize=(7,3))
        # Style the chart to match the app
        fig.patch.set_facecolor(COLORS["BG_CARD"])
        ax1.set_facecolor(COLORS["BG_CARD"])
        
        # Plot data
        ax1.bar(range(len(durations)), durations, label='Duration (min)', color=COLORS["PRIMARY"], alpha=0.8)
        ax1.set_xticks(range(len(durations))); ax1.set_xticklabels(sess_names, rotation=20, fontsize=8, ha="right")
        ax1.set_ylabel('Duration (min)', color=COLORS["TEXT_LIGHT"])
        
        ax2 = ax1.twinx()
        ax2.plot(range(len(distractions)), distractions, color=COLORS["ACCENT_GREEN"], marker='o', label='Distractions')
        ax2.set_ylabel('Distractions', color=COLORS["TEXT_LIGHT"])
        
        # Style ticks
        ax1.tick_params(axis='x', colors=COLORS["TEXT_LIGHT"])
        ax1.tick_params(axis='y', colors=COLORS["TEXT_LIGHT"])
        ax2.tick_params(axis='y', colors=COLORS["TEXT_LIGHT"])
        
        fig.tight_layout(); reports_dir = "reports"; os.makedirs(reports_dir, exist_ok=True)
        img_path = os.path.join(reports_dir, "focus_report.png"); fig.savefig(img_path, facecolor=fig.get_facecolor()); plt.close(fig)
        
        if PIL_AVAILABLE:
            img = Image.open(img_path); img = img.resize((700,300), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            img_lbl = ttk.Label(frame, image=photo, background=COLORS["BG_CARD"])
            img_lbl.image = photo; img_lbl.pack(pady=(10,6))
        else:
            ttk.Label(frame, text=f"Saved report image at {img_path}").pack(pady=(10,6))
    except Exception as e:
        ttk.Label(frame, text=f"Could not make chart (matplotlib missing?): {e}").pack(pady=(10,6))

    suggestion_text = generate_suggestions(rows)
    ttk.Label(frame, text="Suggestions:", font=FONTS["H2"], style="H2.TLabel", background=COLORS["BG_CARD"]).pack(pady=(15, 4), anchor="w")
    ttk.Label(frame, text=suggestion_text, wraplength=700, justify="left", style="TLabel").pack(pady=(0, 15), anchor="w")
    
    ttk.Button(frame, text="Finish & Close App", style="Accent.TButton", 
               command=lambda: on_finish(root)).pack(pady=(15, 6), ipady=4, ipadx=10)

def generate_suggestions(rows):
    # (Function unchanged)
    if not rows: return "No sessions found to analyze."
    durations = [r[2] for r in rows]; distractions = [r[3] for r in rows]; completed = [r[4] for r in rows]
    avg_dis = sum(distractions)/len(distractions); completed_frac = sum(completed)/len(completed); avg_duration_min = sum(durations)/len(durations)/60.0
    if completed_frac >= 0.8 and avg_dis <= 1:
        next_len = avg_duration_min * 1.10
        next_advice = f"You tend to complete sessions with few distractions — try increasing your next session to about {int(next_len)} minutes."
    elif avg_dis > 2 or completed_frac < 0.6:
        next_len = max(5, avg_duration_min * 0.8)
        next_advice = f"You experienced several distractions — try shorter sessions (~{int(next_len)} minutes) and frequent breaks to build consistency."
    else:
        next_len = avg_duration_min
        next_advice = f"Keep your current session length (~{int(next_len)} minutes) and focus on improving consistency."
    topic_stats = {}
    for r in rows:
        name = r[1]; topic_stats.setdefault(name, []).append(r[3])
    avg_topic_dis = {t: (sum(v)/len(v)) for t,v in topic_stats.items()}
    best_topic = min(avg_topic_dis, key=avg_topic_dis.get) if avg_topic_dis else "your priority topic"
    plan = (f"{next_advice} For your day: schedule your most important session on '{best_topic}', alternate focus blocks with 5–10 min breaks, and re-evaluate after a week.")
    return plan

def on_finish(root):
    messagebox.showinfo("Saved", "Your session data is saved locally. Good job today!"); root.destroy()

# ---------- app entry ----------
def start_app():
    root = tk.Tk(); root.title("MindAnchor")
    root.attributes("-fullscreen", True)
    root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))
    
    # Set the main background color for the root window
    root.configure(bg=COLORS["BG_MAIN"])
    
    app_state.root = root
    
    # This container holds all the different "screens"
    container = ttk.Frame(root, style="TFrame")
    container.pack(expand=True, fill="both")
    app_state.container = container
    
    # Apply all our new styles
    style = apply_styles(root)
    app_state.style = style
    
    # --- NEW: Initialize the ChatbotManager ---
    print("Initializing ChatbotManager... (This may take a sec)")
    app_state.chat_manager = ChatbotManager(main_db_path=database.DB_PATH)
    print("ChatbotManager initialized.")
    # --- END NEW ---
    
    # Start with the new welcome screen
    show_welcome_frame(root, container, style)
    root.mainloop()

if __name__ == "__main__":
    database.init_db(); start_app()