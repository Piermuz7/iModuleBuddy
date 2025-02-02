from llama_index.core.agent.workflow import (
    AgentWorkflow,
    AgentStream,
    AgentOutput,
    ToolCall,
    ToolCallResult,
)
from assistant.agents.past_experience_agent import past_experience_agent
from assistant.agents.study_planner_agent import study_planner_agent
from utils.supabase_methods import get_student


async def execute_agent_workflow(user_msg: str):
    student = get_student()
    taken_modules = student.taken_courses if student.taken_courses else []
    desired_occupations = student.desired_jobs
    expected_semesters = student.expected_semesters
    agent_workflow = AgentWorkflow(
        agents=[study_planner_agent, past_experience_agent],
        root_agent=past_experience_agent.name,
        initial_state={
            "taken_modules": taken_modules,
            "desired_occupations": desired_occupations,
            "expected_semesters": expected_semesters,
        },
    )
    handler = agent_workflow.run(
        user_msg=user_msg,
    )

    current_agent = None
    current_tool_calls = ""
    async for event in handler.stream_events():
        if (
            hasattr(event, "current_agent_name")
            and event.current_agent_name != current_agent
        ):
            current_agent = event.current_agent_name
            print(f"\n{'='*50}")
            print(f"🤖 Agent: {current_agent}")
            print(f"{'='*50}\n")

        if isinstance(event, AgentStream):
            if event.delta:
                print(event.delta, end="", flush=True)
        # elif isinstance(event, AgentInput):
        #     print("📥 Input:", event.input)
        elif isinstance(event, AgentOutput):
            if event.response.content:
                print("📤 Output:", event.response.content)
            if event.tool_calls:
                print(
                    "🛠️  Planning to use tools:",
                    [call.tool_name for call in event.tool_calls],
                )
        elif isinstance(event, ToolCallResult):
            print(f"🔧 Tool Result ({event.tool_name}):")
            # print(f"  Arguments: {event.tool_kwargs}")
            # print(f"  Output: {event.tool_output}")
        elif isinstance(event, ToolCall):
            print(f"🔨 Calling Tool: {event.tool_name}")
            # print(f"  With arguments: {event.tool_kwargs}")
    response = await handler

    return response.response.content
