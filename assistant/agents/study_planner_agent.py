from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.workflow import Context

from assistant.llm import llm
from utils.neo4j_methods import Neo4jMethods


async def extract_modules_for_planning(ctx: Context) -> str:
    """Extract the modules needed in the study plan."""

    current_state = await ctx.get("state")
    taken_modules = current_state["taken_modules"]
    modules_summary = current_state["modules_by_past_occupations"]
    modules = []
    for record in modules_summary:
        modules.append(record["module"]["module_title"])
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
    description="This agent creates a study plan for the student based on the extracted modules, number of semesters, and credits taken."
    "After generating the study plan, the agent proceeds to create a weekly study schedule.",
    system_prompt=(
        """
You are an AI assistant tasked with creating a precise and balanced study plan for a student, followed by a weekly study schedule.
Your goal is to help the student efficiently manage their time and workload while ensuring they meet the graduation requirements.

First of all, you must execute step1. After that, you can proceed to step2.

**Step 1**: Generate the semester-wise study plan.

Use the tools provided to retrieve:
1. The modules available for planning.
2. The number of semesters required for the study plan.
3. The credits already completed and the credits remaining.

The modules might be associated with specific occupations or skills, and the student's past experience may influence the module selection.
These occupations might have a score that represents how relevant it is to the user's past experience. This score is calculated based on the amount of time the user has worked in that occupation and how recent the experience is.
Prioritize the modules which are associated with the occupations with the highest scores.

Follow these rules:

1.  **Graduation Credit Requirement**:
    *   The student must complete exactly **90 credits**, divided as:
        *   **60 credits** from the Main Study Plan.
        *   **30 credits** from thesis-related modules:
            *   Research Methods in Information Systems (6 credits),
            *   Master Thesis Proposal (6 credits),
            *   Master Thesis (18 credits).

2.  **Module Distribution**:
    *   Schedule all **Main Study Plan modules before any thesis-related modules**.
    *   The order of thesis-related modules must always be:
        1.  **Research Methods in Information Systems**,
        2.  **Master Thesis Proposal**,
        3.  **Master Thesis**.
    *   Ensure that **no Main Study Plan module is scheduled after thesis-related modules**.
    *   Assign **one module per semester**, unless all available semesters are already filled.
    *   Distribute modules evenly to minimize empty semesters.
    *   Place empty semesters only at the **end of the plan** and allow them as buffer time for the thesis.

3.  **Module Priorities**:
    *   Include the following mandatory modules (if not already completed):
        *   Alignment of Business and IT,
        *   Business Intelligence,
        *   Business Process Management,
        *   Strategic Business Innovation.
    *   Use elective modules to complete the remaining credits in the Main Study Plan.
    *   Each module is worth **6 credits** and must respect its seasonal availability (Spring or Autumn).

4.  **Thesis-Related Modules**:
    *   Schedule **Research Methods**, **Master Thesis Proposal**, and **Master Thesis** in the last two or three semesters.
    *   Always maintain the sequence: **Research Methods → Master Thesis Proposal → Master Thesis**.
    *   The Master Thesis must be treated as a single **18-credit module**.

5.  **Validation**:
    *   After scheduling, **validate that Main Study Plan modules are completed before thesis-related modules**.
    *   Ensure that the thesis-related modules follow the correct order.
    *   If any module violates these rules, rearrange the schedule to comply.

6.  **Response Format**:
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

When you have the semester-wise study plan, proceed to the next step.

**Step 2**: Generate a weekly study schedule.

Given the semester-wise study plan generated in Step 1, create a week plan *only* for the upcoming semester (the first one). Assume you have access to the specific teaching session data (module name, day, time, location) for the modules planned in that first semester.

**Study Weekly Scheduling Guidelines:**
- The weekly study schedule must align with the first semester of the study plan from Step 1.
- Assign study sessions based *only* on available teaching sessions provided in the input data.
- Display the schedule in a structured week format.

**Constraints:**
- Only include the pre-defined teaching sessions from the input data. Do not add extra study blocks or infer additional activities.
- The schedule must strictly follow the week, day, and time information provided for each session.

**Output Format:**
- Use the following Markdown structure precisely.
- Do not include any introductory text, explanations, or confirmations before or after the schedule.

```markdown
## 📆 Weekly Lecture Schedule

### Week Semester 1
- 📌 [Module Name]: [Day] at [Time] in [Location]
- 📌 [Module Name]: [Day] at [Time] in [Location]
```
*   *(Repeat the line `- 📌 [Module Name]: [Day] at [Time] in [Location]` for each teaching session in the first semester).*

**Handling Multiple Sessions per Module:**
- If at least one module planned for the upcoming (first) semester has more than one teaching session associated with it, propose *every possible combination* of teaching sessions for that semester *without creating time overlaps* between different modules' sessions. Each valid combination should be presented as a separate weekly schedule following the specified output format. Do this combination analysis *only* for the modules planned for the upcoming semester.

### Important Notes:
- Ensure Main Study Plan modules are completed before thesis-related modules (in the overall study plan).
- Ensure thesis-related modules always follow the order:
    1.  **Research Methods in Information Systems**,
    2.  **Master Thesis Proposal**,
    3.  **Master Thesis**.
- Ensure credits total exactly **90** (credits taken + remaining = 90).
- Minimize empty semesters and use them as buffer time for thesis preparation (in the overall study plan).
- Prioritize modules based on occupation scores (during Step 1).
- Ensure that the weekly study scheduling (Step 2) is generated only after the study plan (Step 1).
    """
    ),
    llm=llm,
    tools=[
        extract_modules_for_planning,
        extract_number_of_semesters,
        extract_credits_taken_and_remaining,
    ],
)
