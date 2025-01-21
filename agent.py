import os, re
import anthropic
from colorama import init, Fore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('API_KEY')  # Ensure your .env file has the correct API key

class AIAgent:
    def __init__(self, system_prompt, anthropic_api_key):
        self.system_prompt = system_prompt
        self.messages = [{"role": "system", "content": system_prompt}]
        self.actions = {
            "search": self.search_wikipedia,
            "calculate": self.calculate,
            "get_weather": self.get_weather
        }
        # Initialize the anthropic client properly with the API key
        self.anthropic_client = anthropic.Client(api_key=anthropic_api_key)  # Correct client initialization

        # Define available models
        self.models = {
            "haiku": "claude-3-5-haiku-latest",  # fastest
            "sonnet": "claude-3-5-sonnet-latest",  # smartest
            "sonnet-20241022": "claude-3-5-sonnet-latest", 
        }

    def search_wikipedia(self, query):
        # Placeholder for Wikipedia search logic
        return f"Search result for {query}"

    def calculate(self, expression):
        # Evaluate the mathematical expression
        return eval(expression)

    def get_weather(self, city):
        # Placeholder for weather fetching logic
        return f"Weather data for {city} is 72°F and sunny."

    def execute(self, user_input, model_choice="sonnet"):
        self.messages.append({"role": "user", "content": user_input})

        # Construct the conversation history without the system message
        conversation_history = [msg for msg in self.messages if msg['role'] != 'system']  # Exclude system role

        try:
            # Choose the model based on user input or predefined option
            selected_model = self.models.get(model_choice, self.models["sonnet"])  # Default to "sonnet" if invalid choice

            # Call the API using the correct method and the required arguments
            response = self.anthropic_client.messages.create(
                model=selected_model,  # Use the selected model here
                messages=conversation_history,  # Pass only the user and assistant messages
                system=self.system_prompt,  # Pass the system prompt here separately
                max_tokens=1000,  # Ensure max_tokens is set
                temperature=0.2,
                top_p=1.0,
            )

            # Check if the response contains a 'content' field and extract the text
            if hasattr(response, 'content') and isinstance(response.content, list):
                # Extract text from the first TextBlock in the content list
                assistant_message = response.content[0].text
            else:
                raise ValueError(f"Unexpected response structure: {response}")

            # Append the assistant message to the conversation
            self.messages.append({"role": "assistant", "content": assistant_message})

            # Check if an action is specified in the assistant's message
            action_match = re.search(r'Action: (\w+): (.*)', assistant_message)
            if action_match:
                action, action_input = action_match.groups()
                if action in self.actions:
                    result = self.actions[action](action_input)
                    self.messages.append({"role": "system", "content": f"Observation: {result}"})
                else:
                    self.messages.append({"role": "system", "content": f"Error: Unknown action {action}"})
            else:
                return assistant_message

        except Exception as e:
            return f"Error: {str(e)}"


# Initialize colorama
init(autoreset=True)

def pretty_print_response(assistant_message):
    # Split the message into the numbered steps
    steps = assistant_message.split('\n\n')
    
    # Start with a header
    print(Fore.GREEN + "Assistant's Response:")

    # Loop through each step and print it with appropriate numbering
    for idx, step in enumerate(steps, 1):
        print(Fore.CYAN + f"Step {idx}:")
        print(Fore.YELLOW + f"{step.strip()}\n")


def run():
    # Initialize the AI agent with a system prompt and Anthropic API key
    anthropic_api_key = API_KEY
    agent = AIAgent("You are a helpful assistant that can search Wikipedia, perform calculations, and check the weather. Your responses are short and sweet.", anthropic_api_key)

    while True:
        # Get user input prompt
        user_input = input(Fore.MAGENTA + "Enter your question (or type 'exit' to quit): ")

        if user_input.lower() == 'exit':
            print(Fore.RED + "Exiting... Goodbye!")
            break

        # Execute the agent with the provided user input
        response = agent.execute(user_input, model_choice="haiku")

        # Pretty print the response with colors
        pretty_print_response(response)

# Start the main program
if __name__ == "__main__":
    run()
