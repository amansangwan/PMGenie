from ai_reasoning_engine.ai_engine import ai_reasoning_engine
while(True):
    user_query = input(">> ")
    print(ai_reasoning_engine(user_query))