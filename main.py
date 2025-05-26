from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
from typing_extensions import TypedDict
from typing import Annotated
from datetime import datetime, timezone

llm = ChatOllama(model="llama3")

class State(TypedDict):
    messages: Annotated[list, add_messages]

def get_current_time() -> dict:
    """Return the current UTC time in ISO‑8601 format.
    Example → {"utc": "2025-05-21T06:42:00Z"}
    """
    current_time = datetime.now(timezone.utc).isoformat()
    return {"utc": current_time}

# Нода: получение времени
def time_node(state: State) -> dict:
    utc_time = get_current_time()["utc"]
    return {"messages": [AIMessage(content=f"The current UTC time is {utc_time}")]}

# Нода: обычный чат
def chatbot(state: State) -> dict:
    return {"messages": [llm.invoke(state["messages"])]}

# Нода-роутер
def router_node(state: State) -> State:
    return state

# Функция маршрутизации
def route_selector(state: State) -> str:
    last_msg = state["messages"][-1].content.lower()
    if "time" in last_msg:
        return "time"
    return "chat"


# Сборка графа
graph_builder = StateGraph(State)

graph_builder.add_node("router_node", router_node)
graph_builder.add_node("time_node", time_node)
graph_builder.add_node("chatbot", chatbot)

graph_builder.set_entry_point("router_node")

graph_builder.add_conditional_edges("router_node", route_selector, {
    "time": "time_node",
    "chat": "chatbot"
})

graph_builder.add_edge("time_node", END)
graph_builder.add_edge("chatbot", END)



graph = graph_builder.compile()


# Потоковое выполнение
def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            last_msg = value["messages"][-1]
            if isinstance(last_msg, AIMessage):
                print("Assistant:", last_msg.content)

# Цикл общения
while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Goodbye!")
            break
        stream_graph_updates(user_input)
    except Exception as e:
        print("Error:", e)
        break
