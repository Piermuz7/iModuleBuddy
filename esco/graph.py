from neo4j import GraphDatabase
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


with GraphDatabase.driver(URI_NEO4J, auth=AUTH) as d:
    try:
        occupations = gather_occupations(URI_ESCO_GROUP)
        for o in occupations:
            process_occupation(d, o)
        print('data added successfully')
    except Exception as e:
        print(f"An error occurred: {e}")
