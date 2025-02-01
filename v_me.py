import speech_recognition as sr
import pyttsx3
import datetime
import random
import json
import os
from typing import Dict, List, Optional

class VoiceAssistant:
    def __init__(self, name: str = "Assistant"):
        self.name = name
        self.memory: Dict[str, List[str]] = {
            "conversations": [],
            "tasks": [],
            "preferences": []
        }
        
        # Initialize speech engine
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)    # Speed of speech
        self.engine.setProperty('volume', 0.9)  # Volume level
        
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        
        # Natural responses with fillers
        self.fillers = ["hmm", "let me see", "okay", "right", "got it", "understood"]
        
        # Load memory if exists
        self.load_memory()

    def speak(self, text: str) -> None:
        """Convert text to speech with natural fillers."""
        if random.random() < 0.3:  # 30% chance to add a filler
            text = f"{random.choice(self.fillers)}, {text}"
        print(f"{self.name}: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self) -> Optional[str]:
        """Listen to user input through microphone."""
        with sr.Microphone() as source:
            print("\nListening...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5)
                text = self.recognizer.recognize_google(audio)
                print(f"You: {text}")
                self.memory["conversations"].append(text)
                return text.lower()
            except sr.WaitTimeoutError:
                self.speak("I didn't hear anything. Could you please speak again?")
            except sr.UnknownValueError:
                self.speak("I didn't catch that. Could you please repeat?")
            except sr.RequestError:
                self.speak("I'm having trouble accessing the speech recognition service.")
            except Exception as e:
                print(f"Error: {e}")
            return None

    def process_command(self, command: str) -> None:
        """Process user commands and generate appropriate responses."""
        if not command:
            return

        # Basic commands
        if "time" in command:
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            self.speak(f"It's {current_time}")
            
        elif "date" in command:
            current_date = datetime.datetime.now().strftime("%B %d, %Y")
            self.speak(f"Today is {current_date}")
            
        elif "remember" in command:
            self.speak("I'll make a note of that.")
            self.memory["tasks"].append(command.replace("remember", "").strip())
            
        elif "what did i tell you" in command or "what do you remember" in command:
            if self.memory["tasks"]:
                self.speak("Here's what I remember:")
                for task in self.memory["tasks"][-3:]:  # Last 3 items
                    self.speak(f"- {task}")
            else:
                self.speak("I don't have any tasks stored in memory yet.")
                
        elif "clear memory" in command:
            self.memory = {"conversations": [], "tasks": [], "preferences": []}
            self.speak("Memory cleared.")
            
        elif "goodbye" in command or "bye" in command:
            self.speak("Goodbye! Have a great day!")
            self.save_memory()
            return
            
        else:
            responses = [
                "I'm here to help. What can I do for you?",
                "I didn't quite understand. Could you rephrase that?",
                "That's not something I'm capable of, but I can help with tasks, reminders, time, and date.",
                "I'm still learning. Could you try a different command?"
            ]
            self.speak(random.choice(responses))

    def save_memory(self) -> None:
        """Save memory to a JSON file."""
        try:
            with open('assistant_memory.json', 'w') as f:
                json.dump(self.memory, f)
        except Exception as e:
            print(f"Error saving memory: {e}")

    def load_memory(self) -> None:
        """Load memory from JSON file if it exists."""
        try:
            if os.path.exists('assistant_memory.json'):
                with open('assistant_memory.json', 'r') as f:
                    self.memory = json.load(f)
        except Exception as e:
            print(f"Error loading memory: {e}")

    def run(self) -> None:
        """Main loop for running the assistant."""
        self.speak(f"Hello! I'm {self.name}, your voice assistant. How can I help you today?")
        
        while True:
            command = self.listen()
            if command:
                self.process_command(command)
            if "goodbye" in str(command) or "bye" in str(command):
                break


if __name__ == "__main__":
    # Create and run the assistant
    assistant = VoiceAssistant("Helper")
    
    try:
        assistant.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        assistant.save_memory()
    except Exception as e:
        print(f"An error occurred: {e}")
        assistant.save_memory()
