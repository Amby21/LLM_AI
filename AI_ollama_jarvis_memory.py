import ollama
memory = []

ROBOT_NAME = "Jarvis"

print(f"Hi! I am {ROBOT_NAME}. I Remember what we talk about")
print("Type 'bye' to stop.\n")

while True:
    you = input("You :")

    if you.lower() == 'bye':
        print("Bye Bye")
        break
    memory.append({"role":"user", "content": you})

    reply = ollama.chat(model="llama3",
                        messages=[
                            {"role":"system", "content": f"You are a friendly robot named {ROBOT_NAME}"},
                            *memory
                        ])
    answer = reply["message"]["content"]
    memory.append ({"role":"assistant","content": answer})
    print(f"{ROBOT_NAME}", answer)

