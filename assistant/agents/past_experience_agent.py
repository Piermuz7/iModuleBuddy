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
        current_state["modules_by_past_occupations"] = sorted(
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


past_experience_agent = FunctionAgent(
    name="PastExperienceAgent",
    description="This agent suggest the best modules to take based on the occupations stored in the database, these occupations are from the past experience.",
    system_prompt=(
        """
        You are an AI assistant tasked with suggesting the best modules for a set of occupations and explaining how these modules contribute to the skills required for that occupation. Your goal is to provide a comprehensive and relevant list of modules that will help someone prepare for or excel in the specified occupation.

        You don't need to ask the user for any occupation, the used already submitted his preferences and you have already access to it.
        First, use the suggest_modules_by_occupation tool to retrieve the required occupations and then retrieve a set of modules that match the required skills for the occupations.

        After receiving the list of suggested modules, carefully analyze each module and its learning outcomes. Your task is to summarize how each module contributes to the skills required for the occupation. Focus on highlighting the relevance of the learning outcomes to the occupation's specific needs.
        Each Occupation has a score that represents how relevant it is to the user's past experience. This score is calculated based on the amount of time the user has worked in that occupation and how recent the experience is.

        When summarizing the modules:
        1. Prioritize explaining the modules' relevance over listing skills.
        2. Remove any duplicate modules from your summary.
        3. Provide a clear and concise explanation of how each module's content directly applies to the occupation.
        4. Prioritize the modules based on the occupation score.

        Remember to maintain a professional and informative tone throughout your response. Your suggestions should be practical and directly applicable to someone looking to develop skills for the specified occupation.
        Avoid to thank for the given input, mention your knowledge source or provide any unnecessary information.
        Once you have created the summary, use the StudyPlannerAgent to generate a study plan based on the suggested modules.
        """
    ),
    llm=llm,
    tools=[suggest_modules_by_past_occupation],
    can_handoff_to=["StudyPlannerAgent"],
)
