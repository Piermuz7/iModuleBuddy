from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.workflow import Context
from assistant.llm import llm
from utils.neo4j_methods import Neo4jMethods


async def suggest_modules_by_occupation(ctx: Context) -> str:
    """Extract the occupations from a database and suggest modules which develop skills required by those occupations."""
    current_state = await ctx.get("state")
    occupations = current_state["desired_occupations"]
    taken_modules = current_state["taken_modules"]
    try:
        neo4j_methods = Neo4jMethods()
        modules_data = neo4j_methods.get_modules_by_occupation(
            occupations, taken_modules
        )
        current_state["modules_by_occupations"] = modules_data
        # await ctx.set("state", current_state)
        modules_summary = "\n".join(
            [
                f"- Module: {m['module']}\n Occupation: {m['occupation']}\n  Supporting Learning Outcomes: {m['supporting_learning_outcomes']}\n  Supported Skills: {m['supported_skills']}"
                for m in modules_data
            ]
        )
        return modules_summary
    except Exception as e:
        return f"An error occurred: {e}"


occupation_agent = FunctionAgent(
    name="OccupationAgent",
    description="This agent suggest the best modules to take based on the occupations stored in the database, which can be past from the past experience or future career path.",
    system_prompt=(
        """
        You are an AI assistant tasked with suggesting the best modules for a set of occupations and explaining how these modules contribute to the skills required for that occupation. Your goal is to provide a comprehensive and relevant list of modules that will help someone prepare for or excel in the specified occupation.

        You don't need to ask the user for any occupation, the used already submitted his preferences and you have already access to it.
        First, use the suggest_modules_by_occupation tool to retrieve the required occupations and then retrieve a set of modules that match the required skills for the occupations.

        After receiving the list of suggested modules, carefully analyze each module and its learning outcomes. Your task is to summarize how each module contributes to the skills required for the occupation. Focus on highlighting the relevance of the learning outcomes to the occupation's specific needs.

        When summarizing the modules:
        1. Prioritize explaining the modules' relevance over listing skills.
        2. Remove any duplicate modules from your summary.
        3. Provide a clear and concise explanation of how each module's content directly applies to the occupation.

        Remember to maintain a professional and informative tone throughout your response. Your suggestions should be practical and directly applicable to someone looking to develop skills for the specified occupation.
        Avoid to thank for the given input, mention your knowledge source or provide any unnecessary information.
        Once you have created the summary, use the StudyPlannerAgent to generate a study plan based on the suggested modules.
        """
    ),
    llm=llm,
    tools=[suggest_modules_by_occupation],
    can_handoff_to=["StudyPlannerAgent"],
)
