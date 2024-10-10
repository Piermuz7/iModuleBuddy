from neo4j import GraphDatabase
import pandas as pd
from esco import gather_occupations

URI_NEO4J = 'URI'
AUTH = ('USER', 'PASSWORD')
URI_ESCO_GROUP = 'http://data.europa.eu/esco/isco/C25'


def add_occupation(driver, occupation):
    driver.execute_query(
        '''
        MERGE (n:Occupation {description: $description, title: $title, uri: $uri})
        RETURN n
        ''',
        description=occupation.description, title=occupation.title, uri=occupation.uri, database_="neo4j"
    )


def add_skill(driver, skill):
    driver.execute_query(
        '''
        MERGE (n:Skill {skillType: $skill_type, title: $title, uri: $uri, description: $description})
        RETURN n
        ''',
        skill_type=skill.skill_type, title=skill.title, uri=skill.uri, description=skill.description, database_="neo4j"
    )


def link_occupation_skill(driver, occupation_uri, skill_uri, relation_type):
    driver.execute_query(
        '''
        MATCH (node1:Occupation {uri: $occupationUri})
        MATCH (node2:Skill {uri: $skillUri})
        MERGE (node1)-[r:requiresSkill {relationType: $relationType}]->(node2)
        RETURN r
        ''',
        occupationUri=occupation_uri, skillUri=skill_uri, relationType=relation_type, database_="neo4j"
    )


def process_occupation(driver, occupation):
    # Add the occupation node
    add_occupation(driver, occupation)

    # Add essential skills and create relationships
    for skill in occupation.skills:
        add_skill(driver, skill)
        link_occupation_skill(driver, occupation.uri, skill.uri, 'essential')

    # Add optional skills and create relationships
    for skill in occupation.optional_skills:
        add_skill(driver, skill)
        link_occupation_skill(driver, occupation.uri, skill.uri, 'optional')


def add_module(driver, individual_name, course_link, course_title, course_description, course_type, course_comment,
               course_competency_to_be_achieved, course_content):
    driver.execute_query(
        '''
        MERGE (n:Module {individual_name: $individual_name, course_link: $course_link, course_title: $course_title, course_description: $course_description, course_type: $course_type, course_comment: $course_comment, course_competency_to_be_achieved: $course_competency_to_be_achieved, course_content: $course_content})
        RETURN n
        ''',
        individual_name=individual_name, course_link=course_link, course_title=course_title,
        course_description=course_description, course_type=course_type, course_comment=course_comment,
        course_competency_to_be_achieved=course_competency_to_be_achieved, course_content=course_content,
        database_="neo4j"
    )

def add_learning_outcome(driver, learning_outcome):
    driver.execute_query(
        '''
        MERGE (n:LearningOutcome {learning_outcome: $learning_outcome})
        RETURN n
        ''',
        learning_outcome=learning_outcome, database_="neo4j"
    )

with GraphDatabase.driver(URI_NEO4J, auth=AUTH) as d:
    # read modules.csv and ignore Nan values
    modules_df = pd.read_csv('./csv/modules.csv').fillna('')
    for _, module_row in modules_df.iterrows():
        add_module(d, module_row['Individual Name'], module_row['Course_Link'], module_row['Course_Title'],
                   module_row['Course_Description'], module_row['Course_Type'], module_row['Course_Comment'],
                   module_row['Course_Competency_to_be_achieved'], module_row['Course_Content'])
    # read learning_outcomes.csv and ignore Nan values
    learning_outcomes_df = pd.read_csv('./csv/learning_outcomes.csv').fillna('')
    for _, learning_outcome_row in learning_outcomes_df.iterrows():
        add_learning_outcome(d, learning_outcome_row['Learning Outcome'])