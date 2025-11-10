# chatbot_manager.py

import ollama
import sqlite3
import datetime
import logging
import spacy
nlp = spacy.load("en_core_web_sm")

from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer

# This is essential to stop ChatterBot from spamming your console
logging.basicConfig(level=logging.ERROR)

class ChatbotManager:
    """
    Manages all chatbot logic, automatically switching between 
    a "True AI" (Ollama) and a "Simple AI" (ChatterBot) fallback.
    It also injects user data from the main app's database.
    """
    
    def __init__(self, main_db_path="mindanchor_data.sqlite3"):
        """
        Initializes the manager.
        - main_db_path: Path to the main app's SQLite database 
                          (where session/distraction logs are stored).
        """
        self.db_path = main_db_path
        self.ollama_available = False
        self.chatterbot = self._setup_chatterbot()

        # --- Test for Ollama Server ---
        try:
            ollama.list() 
            self.ollama_available = True
            print("INFO: Ollama server detected. Chatbot running in 'Advanced' mode. 🚀")
        except Exception:
            self.ollama_available = False
            print("WARNING: Ollama server not found. Falling back to 'Simple' chatbot mode.")
            print("         (Install & run Ollama for 'Advanced' AI features.)")

    def _setup_chatterbot(self):
        """
        Initializes the "Simple AI" fallback bot (ChatterBot).
        It uses its *own* separate database to store its brain.
        """
        # This DB is just for the bot's *own* conversation knowledge
        bot_brain_db = 'sqlite:///chatterbot_brain.sqlite3'
        
        bot = ChatBot(
            'MindAnchor_Fallback',
            storage_adapter='chatterbot.storage.SQLStorageAdapter',
            database_uri=bot_brain_db
        )
        
        trainer = ListTrainer(bot)

        # Check if the bot is already trained (so we don't retrain every time)
        if bot.storage.count() == 0:
            print("INFO: Training fallback chatbot for the first time...")
            trainer.train([
                "Hello", "Hi! Ready to get some work done?",
                "Hi", "Hello! Let's start a focus session.",
                "How are you?", "I'm a program, but I'm ready to help you focus!",
                "What is this app?", "MindAnchor is a desktop app to help you focus and beat distractions.",
                "What is MindAnchor?", "MindAnchor is a focus timer that uses a Pomodoro-style system.",
                "Give me a focus tip", "Try the '2-minute rule': If a task takes less than two minutes, do it right now.",
                "Thanks", "You're welcome! Keep up the good work."
            ])
        return bot

    def _get_user_stats_context(self):
        """
        Queries the *main app's database* (database.py) to get stats.
        This string is what we "inject" into the AI's prompt.
        """
        context = "User has no session data yet for today."
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            today = str(datetime.date.today())
            
            # --- Query 1: Get total focus minutes today ---
            # USES: duration_sec, start_time (from database.py schema)
            cursor.execute(
                "SELECT SUM(duration_sec) FROM sessions WHERE date(start_time) = ?", 
                (today,)
            )
            focus_result = cursor.fetchone()
            total_focus_secs = (focus_result[0] or 0)
            total_focus_mins = total_focus_secs / 60

            # --- Query 2: Get top distraction (topic) today ---
            # USES: session_name, distractions (from database.py schema)
            cursor.execute(
                """
                SELECT session_name, SUM(distractions) as total_d 
                FROM sessions 
                WHERE date(start_time) = ? AND distractions > 0
                GROUP BY session_name
                ORDER BY total_d DESC 
                LIMIT 1
                """, 
                (today,)
            )
            distraction_result = cursor.fetchone()
            top_distraction_topic = distraction_result[0] if distraction_result else "None"
            
            conn.close()

            # --- Build the context string for the AI ---
            context = f"""
            Here is a summary of the user's activity today:
            - Total Focus Time: {total_focus_mins:.0f} minutes.
            - Topic with most distractions: {top_distraction_topic}.
            """
        
        except sqlite3.Error as e:
            print(f"DB READ ERROR: Could not get user stats: {e}")
            return "Database is not ready. No user stats available."
        
        return context


    def get_response(self, user_prompt):
        """
        This is the main function your app will call.
        It intelligently chooses the best engine to use.
        """
        
        if self.ollama_available:
            # --- PATH 1: "TRUE AI" (OLLAMA) ---
            try:
                # 1. Get the latest user data
                stats_context = self._get_user_stats_context()
                
                # --- NEW, SIMPLIFIED PROMPT ---
                system_prompt = f"""
                You are 'Anchor', a friendly and motivating focus coach.
                Keep all your answers very short (1-2 sentences).
                
                Here is the user's live data:
                {stats_context}
                
                Use this data to inform your answers naturally.
                """
                # --- END NEW PROMPT ---

                # 3. Call the Ollama server
                response = ollama.chat(
                    model='tinyllama',  # Use the small, fast model
                    messages=[          
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_prompt}
                    ]
                )
                return response['message']['content']
            
            except Exception as e:
                print(f"ERROR: Ollama call failed: {e}")
                self.ollama_available = False 
                
        # --- PATH 2: "SIMPLE AI" (CHATTERBOT FALLBACK) ---
        prompt_lower = user_prompt.lower()
        if "stats" in prompt_lower or "how am i doing" in prompt_lower:
            return self._get_user_stats_context()
        
        return str(self.chatterbot.get_response(user_prompt))

