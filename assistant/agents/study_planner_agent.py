from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.workflow import Context

from assistant.llm import llm
from utils.neo4j_methods import Neo4jMethods


async def extract_teaching_sessions(ctx: Context) -> str:
    """Extract the modules needed in the study plan."""

    current_state = await ctx.get("state")
    taken_modules = current_state["taken_modules"]
    modules_retrieved = current_state["modules_retrieved"]
    modules = []
    for record in modules_retrieved:
        if record["module"]["module_type"] != "mandatory":
            modules.append(record["module"]["module_title"])
    try:
        neo4j_methods = Neo4jMethods()
        modules_data = neo4j_methods.get_teaching_sessions_by_modules(
            modules=modules, taken_modules=taken_modules
        )
        # Update the state with the retrieved data
        current_state["teaching_sessions_modules"] = modules_data
        await ctx.set("state", current_state)
        # Generate the prompt content
        prompt = ""
        for module in modules_data:
            prompt += f"Module: {module['module_title']} ({module['module_type']})\n"
            prompt += f"Description: {module['module_description']}\n"
            prompt += f"Teaching Sessions:\n"
            for ts in module["teaching_session"]:
                # Handle teaching session fields with 'N/A'
                prompt += f"- Year:{ts.get('ay', 'N/A')} Semester:{ts.get('semester', 'N/A')} Group Name: {ts.get('group_name', 'N/A')} Day:{ts.get('day', 'N/A')} Time:{ts.get('time', 'N/A')} Location:{ts.get('location', 'N/A')}\n"
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

- The list of modules available for planning is already in your context under the key 'modules_retrieved'.    
- Use the tools provided to retrieve the following additional information:  
  1. The tool 'extract_number_of_semesters' to extract total number of semesters required for the study plan.  
  2. The tool 'extract_credits_taken_and_remaining' to extract credits already completed and the credits remaining.
  3. The tool 'extract_teaching_sessions' to extract module teaching sessions and description about modules.
- Note: The **Master Thesis** and **Master Thesis Proposal** modules do **not** have scheduled teaching sessions and can be started in **any semester**, as long as the prescribed sequence and graduation rules are respected.

The modules have already been ranked by importance based on the selected retrieval strategy (e.g., past experience, future goals, or user preferences).  
**Always prioritize modules in the exact order they are received — earlier modules are more important.** Do not reorder them or deprioritize any unless needed for constraint satisfaction.


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
    *Thesis-related modules, along with the following modules, are mandatory (if not already completed):
        *   Alignment of Business and IT,
        *   Business Intelligence,
        *   Business Process Management,
        *   Strategic Business Innovation.
    *   All other modules are elective and can be used to complete the remaining credits in the Main Study Plan.
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

**Output Rules:**
- Your response **must start directly** with the semester-wise study plan.
- **DO NOT** include any introductory, explanatory, or transitional text such as “Now I'll create...” or “Based on your inputs...”.
- Output must **only** contain the formatted study plan and weekly schedule as specified. Any text outside that format is strictly forbidden.
- This is critical: **No other text should be generated** under any circumstances.

```markdown
## 📆 Weekly Lecture Schedule

### Week Semester 1
- 📌 [Module Name]: [Day] at [Time] in [Location] ([Group Name])
- 📌 [Module Name]: [Day] at [Time] in [Location] ([Group Name])
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
        extract_teaching_sessions,
        extract_number_of_semesters,
        extract_credits_taken_and_remaining,
    ],
)
