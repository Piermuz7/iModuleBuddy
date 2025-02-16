from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.workflow import Context

from assistant.llm import llm


async def format_weekly_schedule(ctx: Context) -> str:
    """Format and structure a weekly study schedule based on the study plan data stored in context."""

    # Retrieve stored study plan data
    current_state = await ctx.get("state")
    study_plan = current_state.get("teaching_sessions_modules", [])

    print("STUDY PLAN: ", study_plan)

    if not study_plan:
        return "⚠️ No study plan found. Please generate a study plan first."

    try:
        weekly_schedule = {}

        for module in study_plan:
            module_name = module["module"]
            for ts in module["teaching_session"]:
                week = f"Week {ts.get('week', 'N/A')}"
                if week not in weekly_schedule:
                    weekly_schedule[week] = []

                weekly_schedule[week].append(
                    f"📌 **{module_name}**: {ts.get('day', 'N/A')} at {ts.get('time', 'N/A')} in {ts.get('location', 'N/A')}"
                )

        # Format output
        schedule_output = "## 📆 Weekly Study Schedule\n\n"
        for week, sessions in sorted(weekly_schedule.items()):
            schedule_output += f"### {week}\n"
            for session in sessions:
                schedule_output += f"- {session}\n"
            schedule_output += "\n"

        return schedule_output

    except Exception as e:
        return f"⚠️ Error while generating the weekly schedule: {e}"


weekly_study_scheduler_agent = FunctionAgent(
    name="WeeklyStudySchedulerAgent",
    description="Formats and structures a weekly study schedule using the study plan data provided by StudyPlannerAgent.",
    system_prompt=(
        """
        You are responsible for **structuring a weekly study schedule** from the pre-extracted study plan data.

        **Your Task:**
        - Retrieve the semester-wise study plan and teaching sessions previously extracted.
        - Organize modules into weekly study slots.
        - Respect teaching session schedules.
        - Ensure a balanced workload per week.
    
        **Study Weekly Scheduling Guidelines:**
        - The weekly study schedule must align with the semester-wise study plan.
        - Assign study sessions based on available teaching sessions.
        - Display the schedule in a structured week-by-week format.

        **Output Format**:
        ```
        ## 📆 Weekly Study Schedule

        ### Week Semester 1
        - 📌 [Module Name]: [Day] at [Time] in [Location]
        - 📌 [Module Name]: [Day] at [Time] in [Location]

        ### Week Semester 2
        - 📌 [Module Name]: [Day] at [Time] in [Location]
        
        ...
        
        ### Week Semester X
        - 📌 [Module Name]: [Day] at [Time] in [Location]
        ```
        
        ```

        Always return a structured weekly study schedule without asking for confirmation.
        """
    ),
    llm=llm,
    tools=[format_weekly_schedule],  # Only formats existing data, no new extraction
)
