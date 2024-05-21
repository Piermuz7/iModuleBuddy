from langchain.chains import GraphCypherQAChain
# tag::import-prompt-template[]
from langchain.prompts.prompt import PromptTemplate
# end::import-prompt-template[]

from llm import llm
from graph import graph

# tag::prompt[]
JOB_ASSISTANT_TEMPLATE = """
You are an expert Neo4j Developer translating user questions into Cypher to answer questions about job roles and competencies required for a particular job role.
Convert the user's question based on the schema.

Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.

Example Cypher Statements:

1. How to find which competencies are demanded for a job role:
```
MATCH (j:JobRole)-[:demands]->(m)
WHERE j.hasName = 'Business Analyst'
RETURN m
```

Your answers should be concise and to the point. Do not include any additional information that is not requested.
Answer with only the generated Cypher statement.



Schema:
{schema}

Question:
{question}

Cypher Query:
"""
# end::prompt[]

# tag::template[]
cypher_prompt = PromptTemplate.from_template(JOB_ASSISTANT_TEMPLATE)
# end::template[]


# tag::cypher-qa[]
job_assistant = GraphCypherQAChain.from_llm(
    llm,
    graph=graph,
    verbose=True,
    cypher_prompt=cypher_prompt
)
# tag::cypher-qa[]