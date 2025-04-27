from neo4j import GraphDatabase
import pandas as pd
import os
import json

URI_NEO4J = 'URI'
AUTH = ('USER', 'PASSWORD')

# Constants for CSV paths
CSV_DIRECTORY = os.path.join(os.getcwd(), 'csv')
SKILLS_CSV = os.path.join(CSV_DIRECTORY, 'skills.csv')
KNOWLEDGE_CSV = os.path.join(CSV_DIRECTORY, 'knowledge.csv')
OCCUPATIONS_CSV = os.path.join(CSV_DIRECTORY, 'occupations.csv')
LEARNING_OUTCOMES_CSV = os.path.join(CSV_DIRECTORY, 'learning_outcomes_uris.csv')
MODULES_CSV = os.path.join(CSV_DIRECTORY, 'modules.csv')
SCHEDULING_CSV = os.path.join(CSV_DIRECTORY, 'modules_scheduling.csv')
ASSESSMENTS_JSON = os.path.join(CSV_DIRECTORY, 'modules_assessments.json')


def add_module(driver, individual_name, module_link, module_title, module_description, module_type, module_comment,
               module_competency_to_be_achieved, module_content):
    driver.execute_query(
        '''
        MERGE (n:Module {individual_name: $individual_name, module_link: $module_link, module_title: $module_title, module_description: $module_description, module_type: $module_type, module_comment: $module_comment, module_competency_to_be_achieved: $module_competency_to_be_achieved, module_content: $module_content})
        RETURN n
        ''',
        individual_name=individual_name, module_link=module_link, module_title=module_title,
        module_description=module_description, module_type=module_type, module_comment=module_comment,
        module_competency_to_be_achieved=module_competency_to_be_achieved, module_content=module_content,
        database_="neo4j"
    )


def add_learning_outcome(driver, learning_outcome, module_title):
    driver.execute_query(
        '''
        MERGE (lo:LearningOutcome {learning_outcome: $learning_outcome, module_title: $module_title})
        RETURN lo
        ''',
        learning_outcome=learning_outcome, module_title=module_title, database_='neo4j'
    )


def add_skill(driver, title, skill_type, index, description, uri):
    driver.execute_query(
        '''
        MERGE (n:Skill {title: $title, skill_type: $skill_type, index: $index, description: $description, uri: $uri})
        RETURN n
        ''',
        title=title, skill_type=skill_type, index=index, description=description, uri=uri, database_='neo4j'
    )


def add_occupation(driver, occupation, uri, description):
    driver.execute_query(
        '''
        MERGE (o:Occupation {occupation: $occupation, uri: $uri, description: $description})
        RETURN o
        ''',
        occupation=occupation, uri=uri, description=description, database_='neo4j'
    )


def add_professor(driver, professor_name, professor_surname):
    records, _, _ = driver.execute_query(
        '''
        MERGE (p:Professor {professor_name: $professor_name, professor_surname: $professor_surname})
        ON CREATE SET p.uuid = randomUUID()
        RETURN p.uuid AS node_uuid
        ''',
        professor_name=professor_name, professor_surname=professor_surname, database_='neo4j'
    )
    return records[0]['node_uuid']


def add_teaching_session(driver, module, group_name, day, time, periodicity, semester, location, ay):
    records, _, _ = driver.execute_query(
        '''
        MERGE (t:TeachingSession {module:$module, group_name: $group_name, day: $day, time:$time, periodicity: $periodicity, semester: $semester, location:$location, ay:$ay})
        ON CREATE SET t.uuid = randomUUID()
        RETURN t.uuid AS node_uuid
        ''',
        module=module, group_name=group_name, day=day, time=time, periodicity=periodicity, semester=semester,
        location=location, ay=ay,
        database_='neo4j'
    )
    return records[0]['node_uuid']


def link_module_teachingSession(driver, module_name, teaching_session_uuid):
    driver.execute_query(
        '''
        MATCH (module:Module {individual_name: $module_name})
        MATCH (t:TeachingSession {uuid: $teaching_session_uuid})
        MERGE (module)-[r:has_schedule]->(t)
        RETURN r
        ''',
        module_name=module_name, teaching_session_uuid=teaching_session_uuid, database_="neo4j"
    )


def link_teachingSession_professor(driver, teaching_session_uuid, professor_uuid):
    driver.execute_query(
        '''
        MATCH (t:TeachingSession {uuid: $teaching_session_uuid})
        MATCH (p:Professor {uuid: $professor_uuid})
        MERGE (t)-[r:taught_by]->(p)
        RETURN r
        ''',
        teaching_session_uuid=teaching_session_uuid, professor_uuid=professor_uuid, database_="neo4j"
    )


def link_occupation_skill(driver, occupation_uri, skill_uri, relation_type):
    driver.execute_query(
        '''
        MATCH (node1:Occupation {uri: $occupation_uri})
        MATCH (node2:Skill {uri: $skill_uri})
        MERGE (node1)-[r:requires_skill {relationType: $relation_type}]->(node2)
        RETURN r
        ''',
        occupation_uri=occupation_uri, skill_uri=skill_uri, relation_type=relation_type, database_="neo4j"
    )


def link_module_learning_outcome(driver, module_name, learning_outcome):
    driver.execute_query(
        '''
        MATCH (module:Module {individual_name: $module_name})
        MATCH (lo:LearningOutcome {learning_outcome: $learning_outcome})
        MERGE (module)-[r:has_learning_outcome]->(lo)
        RETURN r
        ''',
        module_name=module_name, learning_outcome=learning_outcome, database_="neo4j"
    )


def link_learning_objective_skill(driver, learning_outcome, skill_uri):
    driver.execute_query(
        '''
        MATCH (lo:LearningOutcome {learning_outcome: $learning_outcome})
        MATCH (skill:Skill {uri: $skill_uri})
        MERGE (lo)-[r:has_skill]->(skill)
        RETURN r
        ''',
        learning_outcome=learning_outcome, skill_uri=skill_uri, database_="neo4j"
    )


def process_occupation_skill_link(driver, df):
    for _, r in df.iterrows():
        if pd.notna(r['essential_skills']):
            essential_skills = r['essential_skills'].split(',')
            for skill_uri in essential_skills:
                link_occupation_skill(driver, r['uri'], skill_uri.strip(), 'essential')

        if pd.notna(r['essential_knowledge']):
            essential_knowledge = r['essential_knowledge'].split(',')
            for knowledge_uri in essential_knowledge:
                link_occupation_skill(driver, r['uri'], knowledge_uri.strip(), 'essential')

        if pd.notna(r['optional_skills']):
            optional_skills = r['optional_skills'].split(',')
            for skill_uri in optional_skills:
                link_occupation_skill(driver, r['uri'], skill_uri.strip(), 'optional')

        if pd.notna(r['optional_knowledge']):
            optional_knowledge = r['optional_knowledge'].split(',')
            for knowledge_uri in optional_knowledge:
                link_occupation_skill(driver, r['uri'], knowledge_uri.strip(), 'optional')


def process_module_learning_outcome_link(driver, df):
    for _, r in df.iterrows():
        module_title = r['Module Title']
        learning_outcome = r['Learning Outcome']
        link_module_learning_outcome(driver, module_title, learning_outcome)


def process_learning_outcome_skill_link(driver, df):
    for _, r in df.iterrows():
        if pd.notna(r['Promoted skill']):
            skills_uris = r['Promoted skill'].split(',')
            for uri in skills_uris:
                link_learning_objective_skill(driver, r['Learning Outcome'], uri.strip())
        if pd.notna(r['Promoted knowledge']):
            knowledge_uris = r['Promoted knowledge'].split(',')
            for uri in knowledge_uris:
                link_learning_objective_skill(driver, r['Learning Outcome'], uri.strip())


def update_modules_with_assessment_info():
    with open(ASSESSMENTS_JSON, 'r', encoding='utf-8') as f:
        assessment_data = json.load(f)

    with GraphDatabase.driver(URI_NEO4J, auth=AUTH) as driver:
        for entry in assessment_data:
            module_name = entry['module_name']
            project_work = entry['project_work']
            assessment_type = entry['assessment_type']
            oral_assessment = entry['oral_assessment']

            driver.execute_query(
                '''
                MATCH (m:Module {module_title: $module_name})
                SET m.project_work = $project_work,
                    m.assessment_type = $assessment_type,
                    m.oral_assessment = $oral_assessment
                RETURN m
                ''',
                module_name=module_name,
                project_work=project_work,
                assessment_type=assessment_type,
                oral_assessment=oral_assessment,
                database_="neo4j"
            )




def populate_graph():
    with GraphDatabase.driver(URI_NEO4J, auth=AUTH) as d:
        # create nodes
        skills_df = pd.read_csv(SKILLS_CSV)
        for _, row in skills_df.iterrows():
            add_skill(d, row['title'], 'skill', row['index'], row['description'], row['uri'])

        knowledge_df = pd.read_csv(KNOWLEDGE_CSV)
        for _, row in knowledge_df.iterrows():
            add_skill(d, row['title'], 'knowledge', row['index'], row['description'], row['uri'])

        occupations_df = pd.read_csv(OCCUPATIONS_CSV)
        for _, row in occupations_df.iterrows():
            add_occupation(d, row['occupation'], row['uri'], row['description'])

        learning_outcomes_df = pd.read_csv(LEARNING_OUTCOMES_CSV)
        for _, row in learning_outcomes_df.iterrows():
            add_learning_outcome(d, row['Learning Outcome'], row['Module Title'])

        modules_df = pd.read_csv(MODULES_CSV)
        for _, row in modules_df.iterrows():
            course_comment = row['Course_Comment']
            if pd.isna(course_comment):
                course_comment = ""
            add_module(d, row['Individual Name'], row['Course_Link'], row['Course_Title'], row['Course_Description'],
                    row['Course_Type'], course_comment, row['Course_Competency_to_be_achieved'],
                    row['Course_Content'])

        # create relationships
        process_module_learning_outcome_link(d, learning_outcomes_df)
        process_learning_outcome_skill_link(d, learning_outcomes_df)
        process_occupation_skill_link(d, occupations_df)

        # add scheduling and professors
        scheduling_df = pd.read_csv(SCHEDULING_CSV, skipinitialspace=True)
        for _, row in scheduling_df.iterrows():
            teaching_session_uuid = add_teaching_session(
                d,
                module=row['Individual Name'],
                group_name=row['Group_Name'],
                day=row['Day'],
                time=row['Time'],
                periodicity=row['Periodicity'],
                semester=row['Semester'],
                location=row['Location'],
                ay=row['AY'])

            link_module_teachingSession(d, module_name=row['Individual Name'],
                                        teaching_session_uuid=teaching_session_uuid)

            professor_uuid = add_professor(
                d, professor_name=row['Professor_Name'], professor_surname=row['Professor_Surname'])

            link_teachingSession_professor(d, teaching_session_uuid=teaching_session_uuid,
                                        professor_uuid=professor_uuid)


