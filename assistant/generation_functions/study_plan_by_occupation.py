import datetime
from typing import List

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import streamlit as st
from neo4j import GraphDatabase

from assistant.llm import llm
from utils.supabase_methods import get_student

prompt_template = """
You are given a set of modules that match the required skills for an occupation.
The student has already completed {credits_taken} credits from modules. They need to complete {remaining_credits} more credits to reach the required 66 credits from modules.

Please:
1. Summarize how each module contributes to the skills required for the occupation. 
   - Focus on highlighting how the learning outcomes of each module are relevant to the occupation's required skills.
   - Remove duplicate modules from the summary.

2. Create a comprehensive semester-wise study plan based on the number of semesters chosen by the user:
   - Ensure that each semester contains **distinct modules**, meaning no module is repeated.
   - Assign modules to semesters according to their availability (spring or autumn).
   - Include all mandatory modules in the plan. These are required for graduation and must be included in the total of {remaining_credits} credits from modules.
   - Distribute the workload evenly across the specified number of semesters to avoid overloading any semester with too many exams.
   - Ensure the total number of credits from modules (excluding thesis-related modules) is exactly {remaining_credits} credits, with each module contributing 6 credits.

3. Provide a clear breakdown of modules for each semester, including:
   - Module name
   - Whether the module is mandatory or elective
   - Availability (spring or autumn)
   - Brief statement on how it contributes to the required skills
   - Total credits for the semester

4. Add a summary of the remaining credit requirements:
   - State that a total of **90 credits** must be achieved to graduate.  
   - Include the student’s progress, showing how many credits they have already completed ({credits_taken}) and the total remaining credits ({remaining_credits}).
   - Provide a simple breakdown of the remaining credits as follows:
       - **{remaining_credits} credits** from the modules in the semester-wise study plan,  
       - **6 credits** from the Master Thesis Proposal, and  
       - **18 credits** from the Master Thesis.

### Response Format
Please follow this exact structure in your response:

1. **Summarized Relevance of Modules**:
    - [Module Name 1]:
        - Contribution 1
        - Contribution 2
    - [Module Name 2]:
        - Contribution 1
        - Contribution 2

2. **Semester-Wise Study Plan**:
    - **Spring [Year]** (Total Credits: XX):
        - [Module Name 1] (Mandatory/Elective, Spring): Brief relevance
        - [Module Name 2] (Mandatory/Elective, Spring): Brief relevance
    - **Autumn [Year]** (Total Credits: XX):
        - [Module Name 3] (Mandatory/Elective, Autumn): Brief relevance
        - [Module Name 4] (Mandatory/Elective, Autumn): Brief relevance

3. **Additional Notes**:  
    - To graduate, a total of **90 credits** must be achieved.  
    - You have already completed **{credits_taken} credits**, and you need to achieve **{remaining_credits} more credits**, which are divided as follows:  
        - **{remaining_credits} credits** from the modules in the semester-wise study plan,  
        - **6 credits** from the Master Thesis Proposal, and  
        - **18 credits** from the Master Thesis.  

Input Data:
Occupations, Skills, Relevant Modules, Module Availability (Spring/Autumn):
{modules_summary}

Number of Semesters Chosen: {num_semesters}

### Important Notes:
- Use the exact section headers and structure as shown in the **Example Output**.
- Distribute mandatory and elective modules across semesters to avoid overloading one semester with too many exams or credits.
- Include all mandatory modules while ensuring the total credits from modules (excluding thesis-related modules) is exactly {remaining_credits}.
- Each semester should ideally contain 18–24 credits (3–4 modules).
- Ensure no module is repeated across semesters.
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
