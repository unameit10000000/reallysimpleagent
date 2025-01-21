import anthropic
import os, re, time
import requests
import schedule
import threading
from colorama import init, Fore
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

API_KEY = os.getenv('API_KEY')

class AIAgent:
    def __init__(self, system_prompt, anthropic_api_key):
        self.system_prompt = system_prompt
        self.messages = [{"role": "system", "content": system_prompt}]
        self.actions = {
            "search": self.search_wikipedia,
            "calculate": self.calculate,
            "get_weather": self.get_weather,
            "get_crypto": self.get_crypto_data,
            "start_cron": self.start_crypto_scheduler
        }
        self.anthropic_client = anthropic.Client(api_key=anthropic_api_key)
        self.models = {
            "haiku": "claude-3-haiku-20240307",
            "sonnet": "claude-3-sonnet-20240229",
        }
        self.scheduler_running = False

    # TODO: Implement this
    def search_wikipedia(self, query):
        return f"Search result for {query}"

    # TODO: Implement this
    def calculate(self, expression):
        return eval(expression)

    # TODO: Implement this
    def get_weather(self, city):
        return f"Weather data for {city} is 72°F and sunny."

    # Fetch cryptocurrency prices
    def get_crypto_data(self):
        url = "https://api.coingecko.com/api/v3/simple/price?ids=solana,ripple&vs_currencies=usd"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            solana_price = data['solana']['usd']
            xrp_price = data['ripple']['usd']
            return f"Solana: ${solana_price}, XRP: ${xrp_price}"
        else:
            return "Error fetching crypto data."

    def save_crypto_data(self):
        crypto_data = self.get_crypto_data()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n{Fore.GREEN}[CRON] Fetching crypto prices at {timestamp}")
        with open("crypto_prices.txt", "a") as file:
            file.write(f"{timestamp} - {crypto_data}\n")

    def run_scheduler(self):
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(1)

    def start_crypto_scheduler(self):
        if not self.scheduler_running:
            self.scheduler_running = True
            
            # Run every 1 minutes
            schedule.every(1).minutes.do(self.save_crypto_data)
            
            # Fetch immediately
            self.save_crypto_data()
            
            # Start a separate thread
            scheduler_thread = threading.Thread(target=self.run_scheduler)
            scheduler_thread.daemon = True
            scheduler_thread.start()
            
            return "Crypto price tracking has been started. Prices will be updated every 1 minutes."
        return "Scheduler is already running."

    def execute(self, user_input, model_choice="sonnet"):
        self.messages.append({"role": "user", "content": user_input})
        conversation_history = [msg for msg in self.messages if msg['role'] != 'system']

        try:
            selected_model = self.models.get(model_choice, self.models["sonnet"])

            response = self.anthropic_client.messages.create(
                model=selected_model,
                messages=conversation_history,
                system=self.system_prompt,
                max_tokens=1000,
                temperature=0.2,
                top_p=1.0,
            )

            if hasattr(response, 'content') and isinstance(response.content, list):
                assistant_message = response.content[0].text
            else:
                raise ValueError(f"Unexpected response structure: {response}")

            self.messages.append({"role": "assistant", "content": assistant_message})

            if 'cron' in user_input.lower() or 'schedule' in user_input.lower():
                result = self.start_crypto_scheduler()
                return result
            elif 'crypto' in user_input.lower():
                crypto_result = self.get_crypto_data()
                return crypto_result
            else:
                action_match = re.search(r'Action: (\w+): (.*)', assistant_message)
                if action_match:
                    action, action_input = action_match.groups()
                    if action in self.actions:
                        result = self.actions[action](action_input)
                        self.messages.append({"role": "system", "content": f"Observation: {result}"})
                    else:
                        self.messages.append({"role": "system", "content": f"Error: Unknown action {action}"})
                return assistant_message

        except Exception as e:
            return f"Error: {str(e)}"

# Initialize colorama
init(autoreset=True)

# Helper function to print assistant's response
def pretty_print_response(assistant_message):
    print(Fore.GREEN + "Assistant's Response:")
    print(Fore.YELLOW + f"{assistant_message}\n")

# Main loop
def run():
    anthropic_api_key = API_KEY
    agent = AIAgent("You are a helpful assistant that can search Wikipedia, perform calculations, check the weather, fetch cryptocurrency prices, and manage scheduling tasks. Your responses are concise.", anthropic_api_key)

    while True:
        user_input = input(Fore.MAGENTA + "Enter your question (or type 'exit' to quit): ")

        if user_input.lower() == 'exit':
            print(Fore.RED + "Exiting... Goodbye!")
            break

        response = agent.execute(user_input, model_choice="haiku")
        pretty_print_response(response)

if __name__ == "__main__":
    run()