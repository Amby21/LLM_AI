import ollama

print("Hi! I am your robot friend. Type bye to stop")

while True:
    you = input("You:")

    if you.lower == "bye":
        print("Bye bye!")
        break
    
    reply = ollama.chat(model="llama3", messages=[{"role": "user", "content": you}])
    print(reply["message"]["content"])
