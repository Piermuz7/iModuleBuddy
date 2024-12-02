from langchain.chains import GraphCypherQAChain
# tag::import-prompt-template[]
from langchain.prompts.prompt import PromptTemplate

from assistant.graph_config import graph
from assistant.llm import llm

# end::import-prompt-template[]


# tag::prompt[]
CYPHER_GENERATION_TEMPLATE_OLD = """
You are an expert Neo4j Developer translating user questions into Cypher to answer questions about course modules, lecturers and provide recommendations.
Convert the user's question based on the schema.

Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.

Example Cypher Statements:

1. How to find which modules are taught by a lecturer:
```
MATCH (l:Lecturer)-[:teaches]->(m:Module)
WHERE l.hasFirstName = ['Maja']
RETURN m.hasName
```

2. Subjects treated in a module:
```
MATCH (j)-[:isTreatedIn]->(m:Module)
WHERE m.hasName = ['Data Science']
RETURN j
```

3. How to distinguish between same entities with different characteristics, in this case, modules offered in Spring and modules offered in Autumn:
```
MATCH (m:Module)
WHERE ANY (item IN m.isOfferedIn WHERE item = 'Autumn')
RETURN m.isOfferedIn, m.hasName

UNION

MATCH (m:Module)
WHERE ANY (item IN m.isOfferedIn WHERE item = 'Spring')
RETURN m.isOfferedIn, m.hasName
```

4. Modules which don't require collaboration for any Assessment:
```
MATCH (m:Module)
WHERE NOT EXISTS {{ MATCH (m)-[:isAssessedThrough]->(j) WHERE j.hasCollaboration = [true] }}
RETURN m.hasName
```

5. Given a student called 'Mario' which has a already taken some modules, find the modules that he has not taken yet:
```
MATCH (s:Student {{hasFirstName: ['Mario']}})-[:hasTaken]->(m:Module)
WITH collect(m) AS takenModules
MATCH (m:Module)
WHERE NOT m IN takenModules
RETURN m.hasName
```

6. Get general information about a module called 'Data Science':
```
MATCH (a:Module {{hasName: ['Challenging International Managers And Leaders']}})-[r]-(b)
RETURN a, r, b
```

Your answers should be concise and to the point. Do not include any additional information that is not requested.
Answer with only the generated Cypher statement.


Schema:
{schema}

Question:
{question}

Cypher Query:
"""

CYPHER_GENERATION_TEMPLATE = """
You are an expert Neo4j Developer translating user questions into Cypher to answer questions about course modules and provide recommendations.
Convert the user's question based on the schema.

Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.

Example Cypher Statements:

1. Get general information about a module called 'Data Science':
```
MATCH (a:Module {{course_title: ['Data Science']}})-[r]-(b)
RETURN a, r, b
```

2. List all modules with their details:
```
MATCH (m:Module)
RETURN m.module_title AS Title, 
       m.module_description AS Description, 
       m.module_type AS Type, 
       m.module_link AS Link
```

3. Find all modules along with their associated learning outcomes:
```
MATCH (m:Module)-[:has_learning_outcome]->(lo:LearningOutcome)
RETURN m.module_title AS Module, 
       collect(lo.learning_outcome) AS LearningOutcomes
```

4. Find modules associated with a specific skill:
```
MATCH (m:Module)-[:has_learning_outcome]->(lo:LearningOutcome)-[:has_skill]->(s:Skill)
WHERE s.title = "Problem-Solving"
RETURN m.module_title AS ModuleTitle, 
       s.title AS Skill
```

5. Count the number of learning outcomes associated with each module:
```
MATCH (m:Module)-[:has_learning_outcome]->(lo:LearningOutcome)
RETURN m.module_title AS ModuleTitle, 
        COUNT(lo) AS LearningOutcomeCount
```

6. Find all modules of a specific type (e.g., mandatory or elective)
MATCH (m:Module)
WHERE m.module_type = "mandatory"
RETURN m.module_title AS Title, 
       m.module_description AS Description, 
       m.module_link AS Link

7. Find all modules along with their linked skills:
```
MATCH (m:Module)-[:has_learning_outcome]->(lo:LearningOutcome)-[:has_skill]->(s:Skill)
RETURN m.module_title AS ModuleTitle, 
       COLLECT(DISTINCT s.title) AS Skills
```

8. Retrieve modules related to a specific keyword in the description
```
MATCH (m:Module)
WHERE m.module_description CONTAINS "data analysis"
RETURN m.module_title AS Title, 
       m.module_description AS Description
```

9. Find modules linked to both a specific skill and occupation
```
MATCH (o:Occupation {{occupation: "data scientist"}})-[:requires_skill]->(s:Skill {{title: "Python (computer programming)"}})<-[:has_skill]-(lo:LearningOutcome)<-[:has_learning_outcome]-(m:Module)
RETURN o.occupation AS Occupation, 
       s.title AS Skill, 
       m.module_title AS ModuleTitle
```

10. Retrieve all modules along with their content and competencies to be achieved
```
MATCH (m:Module)
RETURN m.module_title AS ModuleTitle, 
       m.module_content AS Content, 
       m.module_competency_to_be_achieved AS CompetencyToBeAchieved
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
    top_k=100,
    cypher_prompt=cypher_prompt
)
# tag::cypher-qa[]

