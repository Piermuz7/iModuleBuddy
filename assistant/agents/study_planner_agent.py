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

        # get extra modules and append it
        extra_modules = neo4j_methods.get_extra_modules()
        modules_data.extend(extra_modules)

        # Update the state with the retrieved data
        current_state["teaching_sessions_modules"] = modules_data
        await ctx.set("state", current_state)

        # Generate the prompt content
        prompt = ""
        for module in modules_data:
            prompt += f"Module: {module['module']}\n"
            prompt += f"Title: {module['module_title']}\n"
            prompt += f"Type: {module['module_type']}\n"
            prompt += f"Description: {module['module_description']}\n"
            prompt += f"Teaching Sessions:\n"
            for ts in module["teaching_session"]:
                # Handle teaching session fields with 'N/A'
                prompt += f"- Year:{ts.get('ay', 'N/A')} Semester:{ts.get('semester', 'N/A')} {ts.get('group_name', 'N/A')} Day:{ts.get('day', 'N/A')} Time:{ts.get('time', 'N/A')} Location:{ts.get('location', 'N/A')}\n"
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
    remaining_credits = 60 - taken_credits
    return {"taken_credits": taken_credits, "remaining_credits": remaining_credits}


study_planner_agent = FunctionAgent(
    name="StudyPlannerAgent",
    description="This agent creates a study plan for the student based on the extracted modules, number of semesters, and credits taken.",
system_prompt = (
    """
    You are an AI assistant tasked with creating a precise and balanced study plan for a student.
    Use the tools provided to retrieve:
    1. The modules available for planning.
    2. The number of semesters required for the study plan.
    3. The credits already completed and the credits remaining.

    Follow these rules:

    1. **Graduation Credit Requirement**:
        - The student must complete exactly **90 credits**, divided as:
          - **60 credits** from the Main Study Plan.
          - **30 credits** from thesis-related modules:
            - Research Methods in Information Systems (6 credits),
            - Master Thesis Proposal (6 credits),
            - Master Thesis (18 credits).

    2. **Module Distribution**:
        - Schedule all **Main Study Plan modules before any thesis-related modules**.
        - The order of thesis-related modules must always be:
          1. **Research Methods in Information Systems**,
          2. **Master Thesis Proposal**,
          3. **Master Thesis**.
        - Ensure that **no Main Study Plan module is scheduled after thesis-related modules**.
        - Assign **one module per semester**, unless all available semesters are already filled.
        - Distribute modules evenly to minimize empty semesters.
        - Place empty semesters only at the **end of the plan** and allow them as buffer time for the thesis.

    3. **Module Priorities**:
        - Include the following mandatory modules (if not already completed):
          - Alignment of Business and IT,
          - Business Intelligence,
          - Business Process Management,
          - Strategic Business Innovation.
        - Use elective modules to complete the remaining credits in the Main Study Plan.
        - Each module is worth **6 credits** and must respect its seasonal availability (Spring or Autumn).

    4. **Thesis-Related Modules**:
        - Schedule **Research Methods**, **Master Thesis Proposal**, and **Master Thesis** in the last two or three semesters.
        - Always maintain the sequence: **Research Methods → Master Thesis Proposal → Master Thesis**.
        - The Master Thesis must be treated as a single **18-credit module**.

    5. **Validation**:
        - After scheduling, **validate that Main Study Plan modules are completed before thesis-related modules**.
        - Ensure that the thesis-related modules follow the correct order.
        - If any module violates these rules, rearrange the schedule to comply.

    6. **Response Format**:
        Provide the study plan first, followed by additional notes and omit Important Notes.

        ### Semester-Wise Study Plan for [Number of Semesters]:
        - **Spring [Year]** (Total Credits: XX):
            - [Module Name] (Mandatory/Elective, Spring): Brief description.
            - (If no modules: "No modules assigned this semester.")
        - **Autumn [Year]** (Total Credits: XX):
            - [Module Name] (Mandatory/Elective, Autumn): Brief description.
            - (If no modules: "No modules assigned this semester.")

        ### Additional Notes:
        - Total graduation requirement: **90 credits**.
        - Credits already completed: **[Taken Credits]**.
        - Credits remaining: **[Remaining Credits]**.
        - Breakdown:
            - **[Adjusted Credits]** from the Main Study Plan,
            - **6 credits** from Research Methods,
            - **6 credits** from Master Thesis Proposal,
            - **18 credits** from Master Thesis.

    ### Important Notes:
    - Ensure Main Study Plan modules are completed before thesis-related modules.
    - Ensure thesis-related modules always follow the order:
      1. **Research Methods in Information Systems**,
      2. **Master Thesis Proposal**,
      3. **Master Thesis**.
    - Ensure credits total exactly **90** (credits taken + remaining = 90).
    - Minimize empty semesters and use them as buffer time for thesis preparation.
    """
)
    ,
    llm=llm,
    tools=[
        extract_modules_for_planning,
        extract_number_of_semesters,
        extract_credits_taken_and_remaining,
    ],
    can_handoff_to=["OccupationAgent"],
)
