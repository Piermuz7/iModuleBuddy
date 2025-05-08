import streamlit as st
from neo4j import GraphDatabase
from langchain_community.vectorstores import Neo4jVector
from assistant.llm import embeddings


class Neo4jMethods:
    def __init__(self):
        self.auth_config = (
            st.secrets["NEO4J_USERNAME"],
            st.secrets["NEO4J_PASSWORD"],
        )
        self.uri = st.secrets["NEO4J_URI"]

    def search_occupation(self, occupation):
        with GraphDatabase.driver(self.uri, auth=self.auth_config) as driver:
            search_occupation_query = f"""
                CALL db.index.fulltext.queryNodes("occupations", '{occupation}') YIELD node, score
                RETURN node.occupation
                """
            result = driver.execute_query(search_occupation_query)
            occupations = [record[0] for record in result.records]
            return occupations

    def get_modules(self):
        with GraphDatabase.driver(self.uri, auth=self.auth_config) as driver:
            get_modules_query = """
                MATCH (n:Module) RETURN n.module_title
                """
            result = driver.execute_query(get_modules_query)
            modules = [record[0] for record in result.records]
            return modules

    def get_filtered_modules(self):
        """Fetch all modules excluding specific thesis-related modules."""
        exclude_modules = {
            "Research Methods in Information Systems",
            "Master Thesis Proposal",
            "Master Thesis"
        }

        all_modules = self.get_modules()
        filtered_modules = [module for module in all_modules if module not in exclude_modules]

        return filtered_modules

    def get_occupations(self):
        with GraphDatabase.driver(self.uri, auth=self.auth_config) as driver:
            get_occupation_query = """
                MATCH (n:Occupation) RETURN n.occupation
                """
            result = driver.execute_query(get_occupation_query)
            occupations = [record[0] for record in result.records]
            return occupations

    def get_teaching_sessions_by_modules(self, modules, taken_modules):
        with GraphDatabase.driver(self.uri, auth=self.auth_config) as driver:
            get_occupation_query = f"""
                MATCH (m:Module)-[:has_schedule]->(ts:TeachingSession)
                WHERE m.module_title IN {modules}
                RETURN m{{.module_title, .module_type}} as module, collect (distinct ts{{.ay, .day, .group_name, .location, .periodicity, .semester, .time}}) as teaching_session
                UNION
                MATCH (m:Module{{module_type: "mandatory"}})-[:has_schedule]->(ts:TeachingSession)
                WHERE NOT m.module_title IN {taken_modules}
                RETURN m{{.module_title, .module_type}} as module, collect (distinct ts{{.ay, .day, .group_name, .location, .periodicity, .semester, .time}}) as teaching_session
                """
            result = driver.execute_query(get_occupation_query)
            return result.records

    def get_modules_by_occupation(self, occupations, taken_modules):
        with GraphDatabase.driver(self.uri, auth=self.auth_config) as driver:
            get_modules_by_occupation_query = f"""
            MATCH (o:Occupation)-[:requires_skill]->(s:Skill)
            WHERE o.occupation IN {occupations}
            CALL db.index.vector.queryNodes('learningOutcomeIndex', 3, s.embeddingDescription)
            YIELD node AS lo, score
            WHERE score>0.92
            MATCH (lo)<-[:has_learning_outcome]-(m:Module)
            WHERE NOT m.module_title IN {taken_modules}
            RETURN m{{.module_title, .module_type}} as module, collect (DISTINCT lo.learning_outcome) as supporting_learning_outcomes, collect(distinct s{{.title, .description}}) as supported_skills, o{{.occupation, .description}} as occupation
            ORDER BY size(supported_skills) DESC
            """
            result = driver.execute_query(get_modules_by_occupation_query)
            return result.records

    def get_extra_modules(self):
        """Fetch the thesis-related modules, including teaching sessions for Research Methods."""
        query = """
            MATCH (m:Module)
            WHERE m.individual_name IN [
                'Course_Research_Methods_in_Information_Systems',
                'Course_Master_Thesis',
                'Course_Master_Thesis_Proposal'
            ]
            OPTIONAL MATCH (m)-[:has_schedule]->(ts:TeachingSession)
            RETURN m.individual_name AS module, 
                   m.module_title AS module_title, 
                   m.module_type AS module_type, 
                   m.module_description AS module_description,
                   collect(DISTINCT ts{.ay, .day, .group_name, .location, .periodicity, .semester, .time}) AS teaching_session
        """
        with GraphDatabase.driver(self.uri, auth=self.auth_config) as driver:
            result = driver.execute_query(query)
            return [
                {
                    "module": record["module"],
                    "module_title": record["module_title"],
                    "module_type": record["module_type"],
                    "module_description": record["module_description"],
                    "teaching_session": record["teaching_session"] or []  # fallback to empty list
                }
                for record in result.records
            ]

    def update_vector_indexes():
        try:
            Neo4jVector.from_existing_graph(
                embeddings,
                url=st.secrets["NEO4J_URI"],
                username=st.secrets["NEO4J_USERNAME"],
                password=st.secrets["NEO4J_PASSWORD"],
                index_name="skillDescription",
                node_label="Skill",
                text_node_properties=["description"],
                embedding_node_property="embeddingDescription",
            )
        except Exception as e:
            print("Error updating Skill index: ", e)

        try:
            Neo4jVector.from_existing_graph(
                embeddings,
                url=st.secrets["NEO4J_URI"],
                username=st.secrets["NEO4J_USERNAME"],
                password=st.secrets["NEO4J_PASSWORD"],
                index_name="learningOutcomeIndex",
                node_label="LearningOutcome",
                text_node_properties=["learning_outcome"],
                embedding_node_property="embeddingLearningOutcome",
            )
        except Exception as e:
            print("Error updating Learning Outcome index: ", e)

        print("Indexes updated")

    def get_professors(self):
        with GraphDatabase.driver(self.uri, auth=self.auth_config) as driver:
            get_modules_query = """
                MATCH (n:Professor) RETURN n.professor_name + ' ' + n.professor_surname AS professor_full_name
                """
            result = driver.execute_query(get_modules_query)
            modules = [record[0] for record in result.records]
            return modules