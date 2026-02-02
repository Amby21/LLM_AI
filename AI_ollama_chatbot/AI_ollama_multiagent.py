#Multi Agent LLM Application

import ollama

#Summarizer Agent
class SummarizerAgent:
    def __init__(self):
        self.summaries = []
    
    def summarize(self,history):
        #Use Ollama to generate a summary
        response = ollama.chat(model="llama3", messages=[{"role":"system", "content":"You are a summarizer agent"},
                                                         {"role":"user", "content":f"Summarize this conversation:\n {history}"}
                                                         ])
        summary = response["message"]["content"]
        self.summaries.append(summary)
        return summary
    def get_summary(self):
        return "\n".join(self.summaries)
    
class WindowManager:
    def __init__(self,window_size=5):
        self.window_size = window_size
    
    def get_context(self,history,summary):
        messages = []
        if summary:
            messages.append({"role":"system","content":f"Conversational Summary:\n{summary}"})
        messages.extend(history[-self.window_size:])
        return messages
    
#state agent

class StateAgent:
    def __init__(self):
        self.state = {}
    
    def update_state(self,user_input):
        if "start" in user_input.lower():
            self.state["status"]="in-progress"
        elif "done" in user_input.lower():
            self.state["status"] = "completed"
        return self.state

#Multi-Agent Orchestrator

class MultiAgentSystem:
    def __init__(self):
        self.summarizer = SummarizerAgent()
        self.window_manager = WindowManager()
        self.state_agent = StateAgent()
        self.history = []

    def interact(self,user_input):
        #update history
        self.history.append({"role":"user","content":user_input})

        #update state
        state = self.state_agent.update_state(user_input)
        #Summarize if history is long
        if len(self.history) > 10:
            summary = self.summarizer.summarize(self.history[:-5])
        else:
            summary = self.summarizer.get_summary()
        #Get context
        messages = [{"role":"system","content":"You are a helpful assistant"}]
        # context = self.window_manager.get_context(self.history,summary)
        
        if summary: 
            messages.append({"role":"system","content":f"Conversation Summary:\n{summary}"})
        
        messages.extend(self.history[-5:])

        response = ollama.chat(model="llama3", messages=messages)
        answer = response["message"]["content"]
        self.history.append({"role":"assistant","content": answer})

        return answer,state        
    
if __name__ =="__main__":
    system = MultiAgentSystem()
    while True:
        user_input = input("You:")
        if user_input.lower() in ["quit","exit"]:
            break
        answer,state = system.interact(user_input)
        print("Assistant",answer)
        print("State",state)