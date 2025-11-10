# 🧠 MindAnchor ⚓

![Python Version](https://img.shields.io/badge/Python-3.13.5-blue?logo=python&logoColor=yellow)
![Dependencies](https://img.shields.io/badge/Dependencies-Installed%20✓-brightgreen)
![License](https://img.shields.io/badge/License-MIT--NC-orange)
![Status](https://img.shields.io/badge/Status-Active%20Development-blueviolet)
![Hackathon](https://img.shields.io/badge/Built%20At-Hack--O--Octo%203.0-red)
![Team](https://img.shields.io/badge/Team-Quantum%20Overdrive-blue)
![Built%20With](https://img.shields.io/badge/Built%20With-Python%20%7C%20OpenCV%20%7C%20Tkinter-success)


**MindAnchor** — a smart focus companion app built in just 24 hours during **Hack-O-Octo 3.0**, organized by **GDG Chandigarh University**. Created by **Team Quantum Overdrive**, MindAnchor helps Gen Z students fight distractions, track focus, and improve productivity using AI-powered guidance, webcam presence detection, and a friendly chatbot named **Anchor**.

---

## 🧩 Table of Contents

1. [About](#about)
2. [Features](#features)
3. [Tech Stack](#tech-stack)
4. [Installation & Run](#installation--run)
5. [Project Structure](#project-structure)
6. [How It Works](#how-it-works)
7. [Future Work](#future-work)
8. [Long-Term Vision](#long-term-vision)
9. [Team & Credits](#team--credits)
10. [License](#license)

---

## 💡 About

MindAnchor is a local desktop prototype designed to reduce digital distractions and help students focus during study sessions. It uses webcam-based face detection to track user presence, logs distractions, and generates focus reports. An integrated chatbot named **Anchor** provides interactive motivation, learns from session logs, and evolves with user data.

> *Currently uses Ollama for chatbot functionality — future versions will include a custom ML model and downloadable desktop, Android, and web versions.*

---

## ⚙️ Features

* 🎯 **Focus Session Timer** — start, pause, and stop tracking your study time.
* 👁️ **Face-Presence Detection** (OpenCV) — detects when you’re distracted or away.
* 📊 **Session Reports** — shows distraction analytics after two sessions.
* 💬 **AI Chatbot (Anchor)** — an interactive study companion powered by ChatterBot + Ollama.
* 🧠 **Self-Learning Behavior** — chatbot evolves based on previous logs.
* 💾 **Local Database (SQLite)** — securely stores logs and focus data.
* 🪄 **Lightweight GUI (Tkinter)** — intuitive, minimal, and distraction-free interface.

---

## 🧠 Tech Stack

* **Language:** Python 3.13+
* **GUI:** Tkinter
* **Computer Vision:** OpenCV (`opencv-python`)
* **Database:** SQLite (`sqlite3`)
* **Data Handling & Visualization:** `numpy`, `pandas`, `matplotlib`, `pillow`
* **Chatbot & AI:** `chatterbot`, `chatterbot-corpus`, `ollama`
* **Planned ML Model:** Custom local model (future integration)

> 🧾 All dependencies are listed in `requirements.txt`.

---

## 💻 Installation & Run

### Prerequisites

* Python 3.8 or higher
* Ollama installed and a model pulled (e.g., `ollama pull llama3`)

### Steps

```bash
# Clone this repository
git clone https://github.com/<your-username>/MindAnchor.git
cd MindAnchor

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # For Windows
# source venv/bin/activate  # For macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Download the spaCy English model (required)
python -m spacy download en_core_web_sm


# Run the app
python main.py
```

---

## 🧱 Project Structure

```
MindAnchor/
├─ main.py                 # Entry point
├─ gui.py                  # Tkinter GUI logic
├─ database.py             # SQLite database management
├─ chatbot_manager.py      # Chatbot + AI integration
├─ requirements.txt        # Dependencies
├─ README.md               # Documentation
├─ LICENSE                 # MIT License
├─ .gitignore              # Ignored files and folders
├─ data/                   # User session data
│   └─ .gitkeep
├─ reports/                # Generated focus reports
│   └─ .gitkeep
```

---

## 🔍 How It Works

1. User starts a session through the GUI.
2. The webcam monitors face presence using OpenCV.
3. Events (focus/distraction) are logged in SQLite.
4. Chatbot Anchor interacts and gives real-time feedback.
5. Reports are generated after multiple sessions.
6. AI chatbot learns from user logs and evolves suggestions.

---

## 🚀 Future Work

* Improve real-time detection speed & accuracy.
* Introduce emotion detection for focus intensity.
* Expand database to include multi-user support.
* Optimize chatbot intelligence with better context retention.
* Integrate personalized focus challenges and reminders.

---

## 🌐 Long-Term Vision

MindAnchor began as a 24-hour hackathon prototype — but we’re building it into a full productivity ecosystem.

### Planned Roadmap

* 🤖 **Custom ML Model** — replace Ollama/ChatterBot with a locally trained model.
* 💻 **Standalone PC App** — packaged with PyInstaller for easy install.
* 📱 **Android App** — mobile-first interface for focus tracking on the go.
* 🌍 **Web Version** — sync progress and access reports anywhere.
* ☁️ **Cloud Analytics (optional)** — future integration for secure online sync.

> *Our vision: to build the ultimate AI-powered productivity companion for students and professionals alike.*

---

## 👨‍💻 Team & Credits

**Team Quantum Overdrive** — Hack-O-Octo 3.0, GDG Chandigarh University (8–9 Nov 2025)

| Member             | Role                                                                                                        |
| ------------------ | ----------------------------------------------------------------------------------------------------------- |
| **Anubhab Pathak** | Team Leader & Visionary Creator — Original Idea, Full System Architecture, Integration, and Final Debugging |
| **Ratul Moond**    | Face Detection & Computer Vision                                                                            |
| **Faraaz Abeer**   | Chatbot Prototype & AI Logic                                                                                |
| **Insha Khan**     | GUI Design & Visual Layout                                                                                  |

**Judges’ Feedback:** Great idea, well executed — encouraged further development!

---

## 📜 License

Licensed under the **MIT License (Non-Commercial Use)** © 2025 Team Quantum Overdrive.  
See the [LICENSE](LICENSE) file for full terms and usage permissions.


> © 2025 Team Quantum Overdrive — Original concept and implementation by first-year students of Chandigarh University.
