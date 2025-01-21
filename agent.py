import anthropic
import os, re, time
import requests
import schedule
import threading
from colorama import init, Fore
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
API_KEY = os.getenv('API_KEY')

class AIAgent:
    def __init__(self, anthropic_api_key):
        self.system_prompt = """You are an AI assistant that can perform both automated and one-time actions.
        
        Available Actions:
        1. search_wikipedia: Search Wikipedia for information
        2. calculate: Perform mathematical calculations
        3. get_weather: Fetch weather data
        4. get_crypto: Get current cryptocurrency prices
        
        Automation-Capable Actions:
        1. crypto_tracking: Monitor cryptocurrency prices periodically
        
        Response Format:
        - For automation requests: 'AUTOMATE: action_name'
        - For one-time actions: 'ACTION: action_name: parameter'
        - For general queries: Respond naturally
        
        Examples:
        User: "Can you monitor crypto prices regularly?"
        Assistant: "AUTOMATE: crypto_tracking"
        
        User: "What's the weather in London?"
        Assistant: "ACTION: get_weather: London"
        
        User: "Tell me about elephants"
        Assistant: "ACTION: search_wikipedia: elephants"
        
        User: "How are you today?"
        Assistant: "I'm doing well, thank you for asking! How can I help you today?"
        
        Always analyze the user's intent to determine if they want:
        1. To start an automated task
        2. To perform a one-time action
        3. To have a general conversation"""

        self.messages = [{"role": "system", "content": self.system_prompt}]
        self.actions = {
            "search_wikipedia": self.search_wikipedia,
            "calculate": self.calculate,
            "get_weather": self.get_weather,
            "get_crypto": self.get_crypto_data,
        }
        self.automated_actions = {
            "crypto_tracking": self.start_crypto_scheduler
        }
        self.anthropic_client = anthropic.Client(api_key=anthropic_api_key)
        self.models = {
            "haiku": "claude-3-haiku-20240307",
            "sonnet": "claude-3-sonnet-20240229",
        }
        self.scheduler_running = False

    def search_wikipedia(self, query):
        # TODO: Implement actual Wikipedia search
        return f"Search result for: {query}"

    def calculate(self, expression):
        try:
            return f"Result: {eval(expression)}"
        except Exception as e:
            return f"Error in calculation: {str(e)}"

    def get_weather(self, city):
        # TODO: Implement actual weather API
        return f"Weather data for {city} is 72°F and sunny."

    def get_crypto_data(self, specific_crypto=None):
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,ripple&vs_currencies=usd"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                prices = [f"{coin}: ${data[coin]['usd']}" for coin in data]
                return ", ".join(prices)
            return "Error fetching crypto data."
        except Exception as e:
            return f"Error: {str(e)}"

    def save_crypto_data(self):
        crypto_data = self.get_crypto_data()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n{Fore.GREEN}[AUTOMATED TASK] Fetching crypto prices at {timestamp}")
        with open("crypto_prices.txt", "a") as file:
            file.write(f"{timestamp} - {crypto_data}\n")

    def run_scheduler(self):
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(1)

    def start_crypto_scheduler(self):
        if not self.scheduler_running:
            self.scheduler_running = True
            
            # Schedule task for every 10 seconds
            schedule.every(10).seconds.do(self.save_crypto_data)
            
            # Initial run
            self.save_crypto_data()
            
            # Start scheduler in separate thread
            scheduler_thread = threading.Thread(target=self.run_scheduler)
            scheduler_thread.daemon = True
            scheduler_thread.start()
            
            return "Automated crypto price tracking started. Updates every 5 minutes."
        return "Automation already running."

    def execute(self, user_input, model_choice="haiku"):
        self.messages.append({"role": "user", "content": user_input})
        conversation_history = [msg for msg in self.messages if msg['role'] != 'system']

        try:
            selected_model = self.models.get(model_choice, self.models["haiku"])

            response = self.anthropic_client.messages.create(
                model=selected_model,
                messages=conversation_history,
                system=self.system_prompt,
                max_tokens=1000,
                temperature=0.2,
                top_p=1.0,
            )

            assistant_message = response.content[0].text
            self.messages.append({"role": "assistant", "content": assistant_message})

            # Check for automation command
            automate_match = re.search(r'AUTOMATE: (\w+)', assistant_message)
            if automate_match:
                action_name = automate_match.group(1)
                if action_name in self.automated_actions:
                    result = self.automated_actions[action_name]()
                    return f"Automated task started: {result}"
                return f"Error: Unknown automated action {action_name}"

            # Check for one-time action command
            action_match = re.search(r'ACTION: (\w+): (.*)', assistant_message)
            if action_match:
                action, param = action_match.groups()
                if action in self.actions:
                    result = self.actions[action](param)
                    return result
                return f"Error: Unknown action {action}"

            # Return normal conversation response
            return assistant_message

        except Exception as e:
            return f"Error: {str(e)}"

# Initialize colorama
init(autoreset=True)

def pretty_print_response(assistant_message):
    print(Fore.GREEN + "Assistant's Response:")
    print(Fore.YELLOW + f"{assistant_message}\n")

def run():
    print(Fore.CYAN + "🤖 AI Agent Initialized!")
    print(Fore.CYAN + "Available commands:")
    print(Fore.YELLOW + "- Ask for information")
    print(Fore.YELLOW + "- Request automated tasks")
    print(Fore.YELLOW + "- Have a general conversation")
    print(Fore.YELLOW + "- Type 'exit' to quit\n")

    agent = AIAgent(API_KEY)

    while True:
        user_input = input(Fore.MAGENTA + "Enter your question (or type 'exit' to quit): ")

        if user_input.lower() == 'exit':
            print(Fore.RED + "Exiting... Goodbye!")
            break

        response = agent.execute(user_input)
        pretty_print_response(response)

if __name__ == "__main__":
    run()