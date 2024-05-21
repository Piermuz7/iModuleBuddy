# tag::importtool[]
from langchain.tools import Tool
# end::importtool[]
from langchain.agents import AgentExecutor, create_react_agent

from llm import llm

from tools.finetuned import cypher_qa

# tag::tools[]
tools = [
    Tool.from_function(
        name="Cypher QA",
        description="Provide information about movies questions using Cypher",
        func = cypher_qa,
        return_direct=True
    ),
]
# end::tools[]


# tag::importprompt[]
from langchain.prompts import PromptTemplate
# end::importprompt[]

# tag::prompt[]
agent_prompt = PromptTemplate.from_template("""

Assistant is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a language model, Assistant is able to generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide responses that are coherent and relevant to the topic at hand.

Assistant is constantly learning and improving, and its capabilities are constantly evolving. It is able to process and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a wide range of questions. Additionally, Assistant is able to generate its own text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on a wide range of topics.

Overall, Assistant is a powerful tool that can help with a wide range of tasks and provide valuable insights and information on a wide range of topics. Whether you need help with a specific question or just want to have a conversation about a particular topic, Assistant is here to assist.

TOOLS:

------

Assistant has access to the following tools:

{tools}

To use a tool, please use the following format:

```

Thought: Do I need to use a tool? Yes

Action: the action to take, should be one of [{tool_names}]

Action Input: the input to the action

Observation: the result of the action

```

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

```

Thought: Do I need to use a tool? No

Final Answer: [your response here]

```

Begin!

New input: {input}

{agent_scratchpad}
""")
# end::prompt[]

# tag::agent[]
agent = create_react_agent(llm, tools, agent_prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True
)
# end::agent[]

# tag::generate_response[]
def generate_response(prompt):
    """
    Create a handler that calls the Conversational agent
    and returns a response to be rendered in the UI
    """

    response = agent_executor.invoke({"input": prompt})

    return response['output']
# end::generate_response[]


"""

The `generate_response()` method can be called from the `handle_submit()` method in `bot.py`:

# tag::import[]
from agent import generate_response
# end::import[]

# tag::submit[]
# Submit handler
def handle_submit(message):
    # Handle the response
    with st.spinner('Thinking...'):

        response = generate_response(message)
        write_message('assistant', response)
# end::submit[]

"""
