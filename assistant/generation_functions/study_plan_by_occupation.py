import datetime
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import streamlit as st
from neo4j import GraphDatabase

from assistant.llm import llm
from utils.supabase_methods import get_student

prompt_template = """
You are given a set of modules that match the required skills for an occupation.
The student has already completed {credits_taken} credits from modules. 
They need to complete {remaining_credits} more credits to reach the required 66 credits from modules.

Please:
1. Create a **semester-wise study plan** across the number of semesters chosen by the user ({num_semesters}), ensuring that:
   - **Every semester includes at least one module whenever possible**. Empty semesters should only occur if there aren’t enough modules to fill all semesters.
   - The modules are distributed **evenly across all semesters**, with no semester exceeding 6 credits unless unavoidable.
   - The total credits from the modules is exactly {remaining_credits} (with each module contributing 6 credits).
   - Modules are assigned to semesters according to their availability (spring or autumn).
   - Mandatory modules are prioritized and included in the plan.
   - Duplicate modules are avoided.

2. For each module in the study plan:
   - Provide its name.
   - Specify if it is mandatory or elective.
   - Indicate its availability (spring or autumn).
   - Briefly describe how it contributes to the required skills.

3. Provide a summary of the total credits and progress:
   - Confirm that the total number of credits from the modules matches {remaining_credits}.
   - State that the overall graduation requirement is 90 credits.
   - Include the student’s progress, showing how many credits they have already completed ({credits_taken}) and the total remaining credits ({remaining_credits}).
   - Provide a breakdown of the remaining credits as follows:
       - **{remaining_credits} credits** from the modules in the semester-wise study plan,
       - **6 credits** from the Master Thesis Proposal, and
       - **18 credits** from the Master Thesis.

### Response Format
Please follow this exact structure in your response:


1. **Semester-Wise Study Plan for {num_semesters} semesters**:
    - **Spring [Year]** (Total Credits: XX):
        - [Module Name 1] (Mandatory/Elective, Spring): Brief relevance
    - **Autumn [Year]** (Total Credits: XX):
        - [Module Name 2] (Mandatory/Elective, Autumn): Brief relevance

2. **Additional Notes**:
    - The total number of credits from the semester-wise study plan is **{remaining_credits} credits**.
    - To graduate, a total of **90 credits** must be achieved.
    - You have already completed **{credits_taken} credits**, and you need to achieve **{remaining_credits} more credits**, divided as follows:
        - **{remaining_credits} credits** from the modules in the semester-wise study plan,
        - **6 credits** from the Master Thesis Proposal, and
        - **18 credits** from the Master Thesis.

### Input Data
Occupations, Skills, Relevant Modules, Module Availability (Spring/Autumn):
{modules_summary}

Number of Semesters Chosen: {num_semesters}

### Important Notes:
- **Ensure that every semester includes at least one module whenever possible.**
- **Strictly enforce an even distribution of credits**, with a maximum of 6 credits (one module) per semester unless unavoidable.
- Avoid duplicate modules across semesters.
- Ensure the total number of credits matches {remaining_credits}.
- Modules should respect their seasonal availability (spring or autumn).
"""
prompt = PromptTemplate(template=prompt_template, input_variables=["modules_summary", "num_semesters", "credits_taken", "remaining_credits"])


def create_study_plan_by_occupations():
    auth = (st.secrets['NEO4J_USERNAME'], st.secrets['NEO4J_PASSWORD'])
    student = get_student()
    occupations = student.desired_jobs
    taken_modules = student.taken_courses if student.taken_courses else []

    if not occupations:
        return 'No relevant modules found for the given occupation.'

    # Calculate the credits already achieved by the student
    credits_taken = len(taken_modules) * 6
    remaining_credits = 66 - credits_taken

    if remaining_credits <= 0:
        return f"The student has already completed the required credits ({credits_taken} credits from modules). No further planning is needed."

    with GraphDatabase.driver(st.secrets['NEO4J_URI'], auth=auth) as driver:
        occupation_query = f"""
        MATCH (o:Occupation)-[:requires_skill]->(s:Skill)
        WHERE o.occupation IN {occupations}
        CALL db.index.vector.queryNodes('learningOutcomeIndex', 3, s.embeddingDescription)
        YIELD node AS lo, score
        WHERE score>0.92
        MATCH (lo)<-[:has_learning_outcome]-(m:Module)-[:has_schedule]->(ts:TeachingSession)
        WHERE NOT m.module_title IN {taken_modules}
        RETURN m{{.module_title, .module_type}} as module, collect (DISTINCT lo.learning_outcome) as supporting_learning_outcomes, collect(distinct s{{.title, .description}}) as supported_skills, o{{.occupation, .description}} as occupation, collect (distinct ts{{.ay, .day, .group_name, .location, .periodicity, .semester, .time}}) as teaching_session
        ORDER BY size(supported_skills) DESC
        UNION
        MATCH (m:Module{{module_type: "mandatory"}})-[:has_schedule]->(ts:TeachingSession)
        WHERE NOT m.module_title IN {taken_modules}
        RETURN m{{.module_title, .module_type}} as module, 'Not Given' as supporting_learning_outcomes,'Not Given' as supported_skills,'Not Given' as occupation, collect (distinct ts{{.ay, .day, .group_name, .location, .periodicity, .semester, .time}}) as teaching_session
        """

        skill_results = driver.execute_query(occupation_query)

        # Step 4: Format the modules summary for the LLM
        modules_summary = "\n".join([
            f"- Module: {m[0]}\n Teaching Session: {m[4]}\n Occupation: {m[3]}\n  Support Learning Outcomes: {m[1]}\n  Supported Skills: {m[2]}"
            for m in skill_results.records
        ])

        # Step 5: Use the LLM to interpret the results
        chain = LLMChain(prompt=prompt, llm=llm)
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        num_semesters = student.expected_semesters

        # Update the prompt input with credits information
        response = chain.invoke({
            "modules_summary": modules_summary,
            "num_semesters": num_semesters,
            "current_date": current_date,
            "credits_taken": credits_taken,
            "remaining_credits": remaining_credits
        })

        return response['text']
