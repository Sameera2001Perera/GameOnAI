from src.data_models.schemas import BuildState
from src.agents.game_dev_agent.graph_builder import GraphBuilder

def graph_stream(init_state, thread_id):

    graph_builder = GraphBuilder()
    app = graph_builder.build_app()


    config = {"configurable": {"thread_id": thread_id}}
    for chunk in app.stream(input=init_state, config=config):
        print("---- CHUNK ----")
        # print(chunk)
        print("---------------")
    

