import speech_recognition as sr
import pyttsx3
import datetime
import random
import json
import os
from typing import Dict, List, Optional
import ollama
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

class FastVoiceAssistant:
    def __init__(self, name: str = "Assistant", model: str = "tinyllama"):
        self.name = name
        self.model = model
        self.memory: Dict[str, List[str]] = {
            "conversations": [],
            "tasks": [],
            "preferences": []
        }
        
        # Initialize speech engine
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 175)
        self.engine.setProperty('volume', 0.9)
        
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = False
        
        # Simplified fillers
        self.fillers = ["ok", "hmm", "ah"]
        
        # Response cache
        self.response_cache = {}
        
        # Load memory if exists
        self.load_memory()

    async def setup_model(self) -> None:
        """Ensure Ollama model is ready."""
        try:
            print(f"Checking {self.model} model...")
            await self._run_in_thread(lambda: ollama.pull(self.model))
            print("Model setup complete!")
        except Exception as e:
            print(f"Error setting up model: {e}")
            raise

    async def _run_in_thread(self, func):
        """Run synchronous functions in a thread pool."""
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, func)

    @lru_cache(maxsize=100)
    def _get_cached_response(self, prompt: str) -> Optional[str]:
        """Get cached response if available."""
        return self.response_cache.get(prompt)

    async def get_ollama_response(self, prompt: str) -> str:
        """Get response from Ollama model."""
        try:
            # Check cache first
            cached_response = self._get_cached_response(prompt)
            if cached_response:
                return cached_response

            # Generate response
            response = await self._run_in_thread(
                lambda: ollama.chat(
                    model=self.model,
                    messages=[{
                        'role': 'user',
                        'content': self._build_prompt(prompt)
                    }]
                )
            )

            # Extract response text
            if isinstance(response, dict) and 'message' in response:
                response_text = response['message']['content']
            else:
                response_text = str(response)

            # Cache the response
            self.response_cache[prompt] = response_text
            return response_text

        except Exception as e:
            print(f"Error getting Ollama response: {e}")
            return "I'm having trouble processing that right now."

    def _build_prompt(self, user_input: str) -> str:
        """Build minimal prompt for faster processing."""
        return f"Respond concisely to: {user_input}"

    def speak(self, text: str, interrupt: bool = False) -> None:
        """Convert text to speech with optional interruption."""
        if interrupt:
            self.engine.stop()
        
        if random.random() < 0.2:
            text = f"{random.choice(self.fillers)}, {text}"
        
        print(f"{self.name}: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self) -> Optional[str]:
        """Listen to user input with optimized settings."""
        with sr.Microphone() as source:
            print("\nListening...")
            try:
                audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=5)
                text = self.recognizer.recognize_google(audio)
                print(f"You: {text}")
                self.memory["conversations"].append(text)
                return text.lower()
            except (sr.WaitTimeoutError, sr.UnknownValueError):
                self.speak("Could you repeat that?")
            except Exception as e:
                print(f"Error: {e}")
            return None

    async def process_command(self, command: str) -> bool:
        """Process commands with optimized response handling."""
        if not command:
            return False

        # Quick responses for common commands
        quick_responses = {
            "time": lambda: f"It's {datetime.datetime.now().strftime('%I:%M %p')}",
            "date": lambda: f"Today is {datetime.datetime.now().strftime('%B %d, %Y')}",
            "hello": lambda: f"Hi! How can I help?",
            "bye": lambda: "Goodbye!",
            "goodbye": lambda: "Goodbye!"
        }

        # Check for quick responses first
        for key, response_func in quick_responses.items():
            if key in command:
                self.speak(response_func())
                return key in ["bye", "goodbye"]

        # Use Ollama for other responses
        response = await self.get_ollama_response(command)
        if not response.endswith(('.', '!', '?')):
            response += '.'
        self.speak(response)
        return False

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

    async def run(self) -> None:
        """Main loop with optimized processing."""
        try:
            await self.setup_model()
            self.speak("Ready to help!")
            
            while True:
                command = self.listen()
                if command:
                    should_exit = await self.process_command(command)
                    if should_exit:
                        break

        except Exception as e:
            print(f"An error occurred: {e}")
            self.save_memory()


async def main():
    assistant = FastVoiceAssistant("Helper", model="tinyllama")
    
    try:
        await assistant.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        assistant.save_memory()
    except Exception as e:
        print(f"An error occurred: {e}")
        assistant.save_memory()


if __name__ == "__main__":
    try:
        print("Checking if Ollama is running...")
        ollama.list()
        print("Ollama is running!")
        asyncio.run(main())
    except Exception as e:
        print("Error: Could not connect to Ollama.")
        print("Please make sure Ollama is running and try again.")
        print(f"Error details: {str(e)}")
