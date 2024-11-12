from assistant.llm import llm
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import streamlit as st
from neo4j import GraphDatabase
from utils.supabase_methods import get_student

prompt_template = """
You are given a set of modules that match the required skills for an occupation. Please summarize how each module contributes to the skills required for the occupation. Focus on highlighting how the learning outcomes of each module are relevant to the occupation's required skills.
The main focus should be on the modules and not on the skills, remove duplicate modules from the summary
Occupations,Skills and Relevant Modules:
{modules_summary}
"""
prompt = PromptTemplate(template=prompt_template, input_variables=["modules_summary"])


# Define the function to execute the search and retrieve relevant data
def find_relevant_modules_for_occupations(boh):
    auth = (st.secrets['NEO4J_USERNAME'], st.secrets['NEO4J_PASSWORD'])
    occupations = get_student().desired_jobs
    if not occupations:
        return 'No relevant modules found for the given occupation.'
    with GraphDatabase.driver(st.secrets['NEO4J_URI'], auth=auth) as driver:
        occupation_query = f"""
        MATCH (o:Occupation)-[:requires_skill]->(s:Skill)
        WHERE o.occupation IN {occupations}
        CALL db.index.vector.queryNodes('learningOutcomeIndex', 3, s.embeddingDescription)
        YIELD node AS lo, score
        WHERE score>0.92
        MATCH (lo)<-[:has_learning_outcome]-(m:Module)
        RETURN m.module_title as module, collect (DISTINCT lo.learning_outcome) as supporting_learning_outcomes, collect(distinct s{{.title, .description}}) as supported_skills, o{{.occupation, .description}} as occupation
        ORDER BY size(supported_skills) DESC
        """
        skill_results = driver.execute_query(occupation_query)
        # Step 4: Format the modules summary for the LLM
        modules_summary = "\n".join([
            f"- Module: {m[0]}\n Occupation: {m[3]}\n  Support Learning Outcomes: {m[1]}\n  Supported Skills: {m[2]}\n Number of Supported Skills: {len(m[2])}"
            for m in skill_results.records
        ])
        # Step 5: Use the LLM to interpret the results
        chain = LLMChain(prompt=prompt, llm=llm)
        response = chain.invoke({"modules_summary": modules_summary})

        return response['text']

