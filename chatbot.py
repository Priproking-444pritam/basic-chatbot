# chatbot.py

def chatbot_response(user_input):
    user_input = user_input.lower()

    if "hello" in user_input or "hi" in user_input:
        return "Hello there!"
    elif "how are you" in user_input:
        return "I'm just a program, but I'm doing great!"
    elif "bye" in user_input:
        return "Goodbye! Have a nice day!"
    else:
        return "I'm sorry, I don't understand that."

def main():
    print("Welcome to Basic Chatbot! (type 'bye' to exit)")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "bye":
            print("Bot:", chatbot_response(user_input))
            break
        response = chatbot_response(user_input)
        print("Bot:", response)

if __name__ == "__main__":
    main()