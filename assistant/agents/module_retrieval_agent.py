from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.workflow import Context
from assistant.llm import llm
from utils.job_ranker import JobRanker
from utils.neo4j_methods import Neo4jMethods


async def suggest_modules_by_past_occupation(ctx: Context) -> str:
    """Extract the occupations from a database and suggest modules which develop skills required by those occupations."""
    try:
        current_state = await ctx.get("state")
        modules_data_with_scores = get_modules_scored_by_past_occupation(current_state)
        current_state["modules_retrieved"] = modules_data_with_scores
        await ctx.set("state", current_state)

        modules_summary = "\n".join(
            [
                f"- Module: {m['module']}\n Occupation: {m['occupation']}\n Occupation Score: {m['occupation_score']:.2f}\n  Supporting Learning Outcomes: {m['supporting_learning_outcomes']}\n  Supported Skills: {m['supported_skills']}"
                for m in modules_data_with_scores
            ]
        )
        return modules_summary

    except Exception as e:
        return f"An error occurred: {e}"


def get_modules_scored_by_past_occupation(state):
    weights = {"work_period": 0.5, "recency": 0.3, "job_type": 0.2}
    max_experience_years = 10

    taken_modules = state["taken_modules"]

    ranker = JobRanker(weights, max_experience_years)
    ranked_jobs = ranker.get_ranked_jobs()

    occupation_list = [job[0] for job in ranked_jobs]
    score_lookup = {job[0]: job[1] for job in ranked_jobs}

    neo4j_methods = Neo4jMethods()
    modules_data = neo4j_methods.get_modules_by_occupation(occupation_list, taken_modules)
    modules_data_with_scores = [rec.data() for rec in modules_data]

    for item in modules_data_with_scores:
        occupation = item["occupation"]["occupation"]
        item["occupation_score"] = score_lookup.get(occupation, 0)

    return sorted(modules_data_with_scores, key=lambda x: x["occupation_score"], reverse=True)


async def suggest_modules_by_future_occupation(ctx: Context) -> str:
    """Suggest modules based only on the user's desired future occupation."""
    try:
        current_state = await ctx.get("state")
        modules_data = get_modules_scored_by_future_occupation(current_state)
        current_state["modules_retrieved"] = modules_data
        await ctx.set("state", current_state)

        modules_summary = "\n".join(
            [
                f"- Module: {m['module']}\n  Occupation: {m['occupation']}\n  Supporting Learning Outcomes: {m['supporting_learning_outcomes']}\n  Supported Skills: {m['supported_skills']}"
                for m in modules_data
            ]
        )
        return modules_summary
    except Exception as e:
        return f"An error occurred: {e}"


def get_modules_scored_by_future_occupation(state):
    taken_modules = state["taken_modules"]
    desired_occupations = state["desired_occupations"]

    neo4j_methods = Neo4jMethods()
    modules_data = neo4j_methods.get_modules_by_occupation(
        desired_occupations, taken_modules
    )
    return [rec.data() for rec in modules_data]


async def suggest_modules_by_preferences(ctx: Context) -> str:
    """Suggest modules based on user preferences using a single optimized query."""
    try:
        current_state = await ctx.get("state")
        modules = get_modules_scored_by_preferences(current_state)
        current_state["modules_retrieved"] = modules
        await ctx.set("state", current_state)

        modules_summary = "\n".join(
            f"- {m['module']['module_title']} (Score: {m['preference_score']})"
            for m in modules
        )
        return modules_summary

    except Exception as e:
        return f"An error occurred: {e}"


def get_modules_scored_by_preferences(state):
    taken_modules = state["taken_modules"]
    available_days = state["available_days"]
    desired_lecturers = state["desired_lecturers"]
    assessment_type = state["assessment_type"]
    project_work = state["project_work"]
    oral_assessment = state["oral_assessment"]

    neo4j_methods = Neo4jMethods()
    return neo4j_methods.get_modules_by_preferences(
        taken_modules,
        available_days,
        desired_lecturers,
        assessment_type,
        project_work,
        oral_assessment
    )


async def suggest_modules_balanced(ctx: Context) -> str:
    """Suggest modules based on a balanced mix of past experience, future goals, and user preferences."""
    current_state = await ctx.get("state")

    try:
        neo4j_methods = Neo4jMethods()
        modules = neo4j_methods.get_module_overview()

        # Add scores from past occupations
        past_occupations_scored_modules = get_modules_scored_by_past_occupation(current_state)
        for m in past_occupations_scored_modules:
            title = m["module"]["module_title"]
            score = m["occupation_score"]
            for module in modules:
                if module["module"]["module_title"] == title:
                    module["score"] += score
                    break

        # Add scores from future occupations
        future_occupations_scored_modules = get_modules_scored_by_future_occupation(current_state)
        for m in future_occupations_scored_modules:
            title = m["module"]["module_title"]
            for module in modules:
                if module["module"]["module_title"] == title:
                    module["score"] += 1 / 6
                    break

        # Add scores from preferences
        preferences_scored_modules = get_modules_scored_by_preferences(current_state)
        for m in preferences_scored_modules:
            title = m["module"]["module_title"]
            pref_score = m["preference_score"]
            for module in modules:
                if module["module"]["module_title"] == title:
                    module["score"] += pref_score / 6
                    break

        # Sort modules by score
        modules = sorted(modules, key=lambda x: x["score"], reverse=True)

        # Save result
        current_state["modules_retrieved"] = modules
        await ctx.set("state", current_state)

        # Format output
        modules_summary = "\n".join(
            f"- {m['module']['module_title']} (Score: {m['score']:.2f})"
            for m in modules
        )
        return modules_summary

    except Exception as e:
        return f"An error occurred: {e}"


async def dispatch_module_suggestion(ctx: Context) -> str:
    """
    Dispatch to the correct module suggestion function based on the retrieval strategy in context.
    """
    state = await ctx.get("state")
    strategy = state.get("retrieval_strategy")
    if strategy == "past_experience":
        return await suggest_modules_by_past_occupation(ctx)
    elif strategy == "future_goals":
        return await suggest_modules_by_future_occupation(ctx)
    elif strategy == "preferences":
        return await suggest_modules_by_preferences(ctx)
    elif strategy == "balanced":
        return await suggest_modules_balanced(ctx)
    else:
        return f"Unknown retrieval strategy: {strategy}"


module_retrieval_agent = FunctionAgent(
    name="ModuleRetrievalAgent",
    description="This agent suggests the best modules to take based on a selected strategy: past experience, future goals, preferences, or a balanced mix.",
    system_prompt=(
        """
        You are an AI assistant tasked with suggesting the best university modules for a user based on a specific strategy. 
        The user has already submitted all necessary information, including past occupations, future career goals, and personal preferences. 
        You have access to this data via context.

        There are four possible strategies for selecting modules. Only one will be used at a time, and it is available under the context key `retrieval_strategy`.

        Strategies:

        - **Past work experience**: Suggest modules based only on the user's previous occupations. Prioritize modules that develop skills the user has already applied or partially mastered in real jobs.

        - **Future career goals**: Suggest modules based only on the user's desired future occupations. Focus on modules that help the user acquire skills required for their career objectives.

        - **User preferences**: Suggest modules based only on the user's stated preferences. These preferences are available in the context state under keys like:
            - `available_days`
            - `desired_lecturers`
            - `assessment_type`
            - `project_work`
            - `oral_assessment`
          Focus on modules that align with these logistical or learning style preferences.

        - **Balanced mix**: Suggest modules based on a balanced combination of the above three strategies. This combines scores from past jobs, future goals, and preferences into a unified recommendation.

        Use the `dispatch_module_suggestion` tool to select and execute the correct strategy based on the value of `retrieval_strategy`.

        Once you receive the list of scored modules from the tool, your role is to:

        1. Prioritize explaining the relevance of each module to the user's past experience, future goals, or preferences—depending on the chosen strategy.
        2. Avoid listing duplicate modules.
        3. Provide a clear and concise explanation of how each module’s content or learning outcomes support the selected strategy.
        4. If available, you may mention the module’s score or rank, but your main focus is on relevance and usefulness.

        After presenting the recommended modules and their explanations, **immediately hand off the list of modules to the StudyPlannerAgent to generate a study plan** based on the suggested modules. Do not ask the user for confirmation or expect any further input before the handoff.

        Your tone should be informative and professional. Focus on usefulness and practicality. Do not thank the user, reference your internal logic, or mention technical processes.

        """
    ),
    llm=llm,
    tools=[dispatch_module_suggestion],
    can_handoff_to=["StudyPlannerAgent"],
)
