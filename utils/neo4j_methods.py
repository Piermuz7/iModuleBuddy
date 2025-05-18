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

    def get_module_overview(self):
        with GraphDatabase.driver(self.uri, auth=self.auth_config) as driver:
            query = """
                MATCH (n:Module)
                RETURN n.module_title AS title, n.module_type AS module_type
            """
            result = driver.execute_query(query)
            records = result.records

            return [
                {
                    "module": {
                        "module_title": record["title"],
                        "module_type": record["module_type"]
                    },
                    "score": 0
                }
                for record in records
            ]

    def get_module_individual_names(self):
        query = "MATCH (n:Module) RETURN n.individual_name"
        with GraphDatabase.driver(self.uri, auth=self.auth_config) as driver:
            result = driver.execute_query(query)
            return [record["n.individual_name"] for record in result.records]


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
                RETURN m{{.module_title, .module_type, .module_description}} AS module,
                       collect(DISTINCT ts{{.ay, .day, .group_name, .location, .periodicity, .semester, .time}}) AS teaching_session
                UNION
                MATCH (m:Module {{module_type: "mandatory"}})-[:has_schedule]->(ts:TeachingSession)
                WHERE NOT m.module_title IN {taken_modules}
                RETURN m{{.module_title, .module_type, .module_description}} AS module,
                       collect(DISTINCT ts{{.ay, .day, .group_name, .location, .periodicity, .semester, .time}}) AS teaching_session
                """
            records = driver.execute_query(get_occupation_query)

            result = []
            for record in records.records:
                tmp = record["module"]
                result.append({
                    "module_title": tmp.get("module_title"),
                    "module_type": tmp.get("module_type"),
                    "module_description": tmp.get("module_description", ""),
                    # Include description, default empty string
                    "teaching_session": record.get("teaching_session", [])
                })
            return result

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
                    "module_title": record["module_title"],
                    "module_type": record["module_type"],
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

    def matches_lecturer(self, ind, desired_lecturer):
        if not desired_lecturer:
            return False
        query = f"""
        MATCH (module:Module)-[:has_schedule]->(session:TeachingSession)-[:taught_by]->(professor:Professor)
        WHERE module.module_title = '{ind}' AND '{desired_lecturer}' CONTAINS professor.professor_surname
        RETURN COUNT(professor) > 0
        """
        with GraphDatabase.driver(self.uri, auth=self.auth_config) as driver:
            result = driver.execute_query(query)
            return result.records[0][0]

    def matches_day(self, ind, available_days):
        if not available_days:
            return False

        available_days_list = "[" + ", ".join(f'"{day}"' for day in available_days) + "]"

        query = f"""
        MATCH (module:Module {{individual_name: "{ind}"}})-[:has_schedule]->(session:TeachingSession)
        WHERE session.day IN {available_days_list}
        RETURN COUNT(session) > 0
        """
        with GraphDatabase.driver(self.uri, auth=self.auth_config) as driver:
            result = driver.execute_query(query)
            return result.records[0][0]

    def matches_assessment_type(self, ind, assessment_type):
        if not assessment_type:
            return False

        if assessment_type.lower() == "individual_and_group":
            accepted_types = ["individual", "group", "individual_and_group"]
            accepted_types_list = "[" + ", ".join(f'"{t}"' for t in accepted_types) + "]"
            query = f"""
            MATCH (module:Module {{individual_name: "{ind}"}})
            WHERE toLower(module.assessment_type) IN {accepted_types_list}
            RETURN COUNT(module) > 0
            """
        else:
            query = f"""
            MATCH (module:Module {{individual_name: "{ind}"}})
            WHERE toLower(module.assessment_type) = "{assessment_type.lower()}"
            RETURN COUNT(module) > 0
            """

        with GraphDatabase.driver(self.uri, auth=self.auth_config) as driver:
            result = driver.execute_query(query)
            return result.records[0][0]

    def has_project_work(self, ind):
        query = f"""
        MATCH (module:Module {{individual_name: "{ind}"}})
        RETURN module.project_work = true
        """
        with GraphDatabase.driver(self.uri, auth=self.auth_config) as driver:
            result = driver.execute_query(query)
            return result.records[0][0]

    def has_oral_assessment(self, ind):
        query = f"""
        MATCH (module:Module {{individual_name: "{ind}"}})
        RETURN module.oral_assessment = true
        """
        with GraphDatabase.driver(self.uri, auth=self.auth_config) as driver:
            result = driver.execute_query(query)
            return result.records[0][0]

    def get_modules_by_preferences(
            self,
            taken_modules,
            desired_lecturers,
            available_days,
            assessment_type,
            project_work,
            oral_assessment
    ):

        assessment_type = f'"{assessment_type.lower()}"'
        project_work = str(project_work).lower()
        oral_assessment = str(oral_assessment).lower()

        query = f"""
        MATCH (module:Module)
        OPTIONAL MATCH (module)-[:has_schedule]->(session:TeachingSession)
        OPTIONAL MATCH (session)-[:taught_by]->(professor:Professor)
        WITH module, collect(DISTINCT session.day) AS days,
             collect(DISTINCT professor.professor_surname) AS surnames

        WHERE NOT module.individual_name IN {taken_modules}

        WITH module,
             apoc.coll.intersection(days, {available_days}) AS day_match,
             ANY(surname IN surnames WHERE ANY(desired IN {desired_lecturers} WHERE desired CONTAINS surname)) AS lecturer_match,
             CASE
                 WHEN {assessment_type} = 'individual_and_group' THEN
                     module.assessment_type IN ['individual', 'group', 'individual_and_group']
                 ELSE
                     module.assessment_type = {assessment_type}
             END AS assessment_match,
             module.project_work = {project_work} AS project_work_match,
             module.oral_assessment = {oral_assessment} AS oral_assessment_match

        WITH module.module_title AS name,
         module.module_type AS module_type,
             (CASE WHEN size(day_match) > 0 THEN 1 ELSE 0 END) +
             (CASE WHEN lecturer_match THEN 1 ELSE 0 END) +
             (CASE WHEN assessment_match THEN 1 ELSE 0 END) +
             (CASE WHEN project_work_match THEN 1 ELSE 0 END) +
             (CASE WHEN oral_assessment_match THEN 1 ELSE 0 END) AS preference_score

        RETURN name, module_type, preference_score
        ORDER BY preference_score DESC
        """

        with GraphDatabase.driver(self.uri, auth=self.auth_config) as driver:
            result = driver.execute_query(query)
            return [
                {
                    "module": {
                        "module_title": record["name"],
                        "module_type": record["module_type"]
                    },
                    "preference_score": record["preference_score"]
                }
                for record in result.records
            ]
