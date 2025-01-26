from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.workflow import Context
from assistant.llm import llm
from utils.neo4j_methods import Neo4jMethods


async def extract_modules_for_planning(ctx: Context) -> str:
    """Extract the modules needed in the study plan."""

    current_state = await ctx.get("state")
    taken_modules = current_state["taken_modules"]
    modules_summary = current_state("modules_by_occupations")
    modules = []
    for record in modules_summary:
        modules.append(record["module"])
    try:
        neo4j_methods = Neo4jMethods()
        modules_data = neo4j_methods.get_teaching_sessions_by_modules(
            modules=modules, taken_modules=taken_modules
        )
        current_state = await ctx.get("state")
        current_state["teaching_sessions_modules"] = modules_data
        await ctx.set("state", current_state)
        prompt = ""
        for module in modules_data:
            prompt += f"Module: {module['module']}\n"
            prompt += f"Teaching Sessions:\n"
            for ts in module["teaching_session"]:
                prompt += f"- Year:{ts['ay']} Semester:{ts['semester']} {ts['group_name']} Day:{ts['day']} Time:{ts['time']} Location:{ts['location']}\n"
            prompt += "\n"

        return prompt
    except Exception as e:
        return f"An error occurred: {e}"


async def extract_number_of_semesters(ctx: Context) -> str:
    """Extract the number of semesters needed in the study plan."""

    current_state = await ctx.get("state")
    expected_semesters = current_state["expected_semesters"]
    return expected_semesters


async def extract_credits_taken_and_remaining(ctx: Context) -> dict:
    """Extract the number of credits taken by the student."""

    current_state = await ctx.get("state")
    taken_modules = current_state["taken_modules"]
    taken_credits = len(taken_modules) * 6
    remaining_credits = 66 - taken_credits
    return {"taken_credits": taken_credits, "remaining_credits": remaining_credits}


study_planner_agent = FunctionAgent(
    name="StudyPlannerAgent",
    description="This agent creates a study plan for the student based on the extracted modules, number of semesters, and credits taken.",
    system_prompt=(
        """
        You are an AI assistant tasked with creating a study plan for a student
        You don't need any input from the user, you can extract any data you need using the tools provided.
        First, use the extract_modules_for_planning tool to retrieve the modules needed in the study plan.
        Then, use the extract_number_of_semesters tool to retrieve the number of semesters needed in the study plan.
        Finally, use the extract_credits_taken_and_remaining tool to retrieve the number of credits taken by the student.
        The student has already completed a certain number of credits from modules. They need to complete a certain number of more credits to reach the required 66 credits from modules.
        Please:
        1. Create a **semester-wise study plan** across the number of semesters chosen by the user, ensuring that:
        - **Every semester includes at least one module whenever possible**. Empty semesters should only occur if there aren’t enough modules to fill all semesters.
        - The modules are distributed **evenly across all semesters**, with no semester exceeding 6 credits unless unavoidable.
        - The total credits from the modules matches exactly the number of remaining credits that the student must complete (with each module contributing 6 credits).
        - Modules are assigned to semesters according to their availability (spring or autumn).
        - Mandatory modules are prioritized and included in the plan.
        - Duplicate modules are avoided.

        2. For each module in the study plan:
        - Provide its name.
        - Specify if it is mandatory or elective.
        - Indicate its availability (spring or autumn).
        - Briefly describe how it contributes to the required skills.

        3. Provide a summary of the total credits and progress:
        - Confirm that the total number of credits from the modules matches the number of remaining credits that the student must complete.
        - State that the overall graduation requirement is 90 credits.
        - Include the student’s progress, showing how many credits they have already completed and the total remaining credits.
        - Provide a breakdown of the remaining credits as follows:
            - *The number of remaining credits** from the modules in the semester-wise study plan,
            - **6 credits** from the Master Thesis Proposal, and
            - **18 credits** from the Master Thesis.

        ### Response Format
        Please follow this exact structure in your response:


        1. **Semester-Wise Study Plan for the number of semesters**:
            - **Spring [Year]** (Total Credits: XX):
                - [Module Name 1] (Mandatory/Elective, Spring): Brief relevance
            - **Autumn [Year]** (Total Credits: XX):
                - [Module Name 2] (Mandatory/Elective, Autumn): Brief relevance

        2. **Additional Notes**:
            - The total number of credits from the semester-wise study plan is **remaining credits**.
            - To graduate, a total of **90 credits** must be achieved.
            - You have already completed **taken credits**, and you need to achieve **remaining more credits**, divided as follows:
                - **remaining credits** from the modules in the semester-wise study plan,
                - **6 credits** from the Master Thesis Proposal, and
                - **18 credits** from the Master Thesis.

        ### Important Notes:
        - **Ensure that every semester includes at least one module whenever possible.**
        - **Strictly enforce an even distribution of credits**, with a maximum of 6 credits (one module) per semester unless unavoidable.
        - Avoid duplicate modules across semesters.
        - Ensure the total number of credits matches the remaining credits.
        - Modules should respect their seasonal availability (spring or autumn).
        """
    ),
    llm=llm,
    tools=[
        extract_modules_for_planning,
        extract_number_of_semesters,
        extract_credits_taken_and_remaining,
    ],
    can_handoff_to=["OccupationAgent"],
)
