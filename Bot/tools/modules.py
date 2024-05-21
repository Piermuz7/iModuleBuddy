from langchain.chains import GraphCypherQAChain
# tag::import-prompt-template[]
from langchain.prompts.prompt import PromptTemplate
# end::import-prompt-template[]

from llm import llm
from graph import graph

# tag::prompt[]
CYPHER_GENERATION_TEMPLATE = """
You are an expert Neo4j Developer translating user questions into Cypher to answer questions about course modules, lecturers and provide recommendations.
Convert the user's question based on the schema.

Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.

Example Cypher Statements:

1. How to find which modules are taught by a lecturer:
```
MATCH (l:Lecturer)-[:teaches]->(m:Module)
WHERE l.hasFirstName = 'Maja'
RETURN m.hasName
```

2. Subjects treated in a module:
```
MATCH (j)-[:isTreatedIn]->(m:Module)
WHERE m.hasName = 'Data Science'
RETURN j
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
cypher_prompt = PromptTemplate.from_template(CYPHER_GENERATION_TEMPLATE)
# end::template[]


# tag::cypher-qa[]
cypher_qa = GraphCypherQAChain.from_llm(
    llm,
    graph=graph,
    verbose=True,
    cypher_prompt=cypher_prompt
)
# tag::cypher-qa[]