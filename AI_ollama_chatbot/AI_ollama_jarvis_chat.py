import ollama

ROBOT_NAME = "Jarvis"
print(f"Hi! My name is {ROBOT_NAME}, I am your robot friend")
print("Type Bye to stop")

while True:

    you = input("You: ")

    if you.lower() == "bye":
        print(f"{ROBOT_NAME}: Bye Bye See you soon!")
        break
    reply = ollama.chat(model = "llama3", 
                        messages= [ {"role": "system","content": f"You are friendly robot named {ROBOT_NAME}. Talk simply and kindly." 
                                    },
                                    {"role":"user", "content": you}
                                ]
                        )
    print(f"{ROBOT_NAME}:", reply["message"]["content"])