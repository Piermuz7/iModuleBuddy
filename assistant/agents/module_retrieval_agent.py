from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.workflow import Context
from assistant.llm import llm
from utils.job_ranker import JobRanker
from utils.neo4j_methods import Neo4jMethods


async def suggest_modules_by_past_occupation(ctx: Context) -> str:
    """Extract the occupations from a database and suggest modules which develop skills required by those occupations."""
    current_state = await ctx.get("state")
    taken_modules = current_state["taken_modules"]
    weights = {"work_period": 0.5, "recency": 0.3, "job_type": 0.2}
    max_experience_years = 10

    try:
        neo4j_methods = Neo4jMethods()
        ranker = JobRanker(weights, max_experience_years)
        ranked_jobs = ranker.get_ranked_jobs()
        modules_data = neo4j_methods.get_modules_by_occupation(
            [job[0] for job in ranked_jobs], taken_modules
        )
        lookup_dict = {item[0]: item[1] for item in ranked_jobs}
        modules_data_with_scores = [rec.data() for rec in modules_data]
        for item in modules_data_with_scores:
            if item["occupation"]["occupation"] in lookup_dict:
                item["occupation_score"] = lookup_dict[item["occupation"]["occupation"]]
        current_state["modules_retrieved"] = sorted(
            modules_data_with_scores,
            key=lambda x: x["occupation_score"],
            reverse=True,
        )
        await ctx.set("state", current_state)
        modules_summary = "\n".join(
            [
                f"- Module: {m['module']}\n Occupation: {m['occupation']}\n Occupation Score: {m['occupation_score']:.2f}\n  Supporting Learning Outcomes: {m['supporting_learning_outcomes']}\n  Supported Skills: {m['supported_skills']}"
                for m in sorted(
                modules_data_with_scores,
                key=lambda x: x["occupation_score"],
                reverse=True,
            )
            ]
        )
        return modules_summary

    except Exception as e:
        return f"An error occurred: {e}"


async def suggest_modules_by_future_occupation(ctx: Context) -> str:
    """Suggest modules based only on the user's desired future occupation."""
    current_state = await ctx.get("state")
    taken_modules = current_state["taken_modules"]
    desired_occupation = current_state["desired_occupations"]
    try:
        neo4j_methods = Neo4jMethods()
        modules_data = neo4j_methods.get_modules_by_occupation(
            desired_occupation, taken_modules)
        modules_data = [rec.data() for rec in modules_data]
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


async def suggest_modules_by_preferences(ctx: Context) -> str:
    """Suggest modules based on user preferences (schedule, teachers, etc.) and desired occupation."""

    pass


async def suggest_modules_balanced(ctx: Context) -> str:
    """Suggest modules based on a balanced mix of past experience, future goals, and user preferences."""
    pass


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
        You are an AI assistant tasked with suggesting the best modules for a user based on a specific strategy. The user has already submitted all required data (past jobs, preferences, desired occupation, etc.), and you have access to that information.

        There are four possible strategies for selecting modules:
        - Past work experience
        - Future career goals
        - User preferences
        - A balanced mix of all the above

        The strategy to use is already available in your context under the key 'retrieval_strategy'. Use the `dispatch_module_suggestion` tool to automatically select and execute the correct strategy based on that value.

        The tool will return a set of modules that are already ranked according to the chosen strategy. Once you receive the list of ranked modules, your task is to:
        1. Prioritize explaining the relevance of each module to the user's occupation or career goals.
        2. Avoid listing duplicate modules.
        3. Provide a clear and concise explanation of how each module’s learning outcomes contribute to the skills or preferences based on the chosen strategy.
        4. If available, mention the occupation score or other relevant metrics but focus on explaining the module’s relevance.

        Your tone should be informative and professional. Focus on usefulness and practicality. Do not thank the user, reference your internal logic, or mention technical processes.

        Once you have created the summary, pass the modules to the StudyPlannerAgent to generate a study plan based on the suggested modules.
        """
    ),
    llm=llm,
    tools=[dispatch_module_suggestion],
    can_handoff_to=["StudyPlannerAgent"],
)
