import streamlit as st
from neo4j import GraphDatabase
from langchain_community.vectorstores import Neo4jVector
from assistant.llm import embeddings

def search_occupation(occupation):
    auth = (st.secrets['NEO4J_USERNAME'], st.secrets['NEO4J_PASSWORD'])
    with GraphDatabase.driver(st.secrets['NEO4J_URI'], auth=auth) as driver:
        search_occupation_query = f"""
            CALL db.index.fulltext.queryNodes("occupations", '{occupation}') YIELD node, score
            RETURN node.occupation
            """
        result = driver.execute_query(search_occupation_query)
        occupations = [record[0] for record in result.records]
        return occupations

def get_modules():
    auth = (st.secrets['NEO4J_USERNAME'], st.secrets['NEO4J_PASSWORD'])
    with GraphDatabase.driver(st.secrets['NEO4J_URI'], auth=auth) as driver:
        get_modules_query = f"""
            MATCH (n:Module) RETURN n.module_title
            """
        result = driver.execute_query(get_modules_query)
        modules = [record[0] for record in result.records]
        return modules

def get_occupations():
    auth = (st.secrets['NEO4J_USERNAME'], st.secrets['NEO4J_PASSWORD'])
    with GraphDatabase.driver(st.secrets['NEO4J_URI'], auth=auth) as driver:
        get_occupation_query = f"""
            MATCH (n:Occupation) RETURN n.occupation
            """
        result = driver.execute_query(get_occupation_query)
        occupations = [record[0] for record in result.records]
        return occupations


def update_vector_indexes():
    try:
        Neo4jVector.from_existing_graph(
            embeddings,
            url=st.secrets["NEO4J_URI"],
            username=st.secrets["NEO4J_USERNAME"],
            password=st.secrets["NEO4J_PASSWORD"],
            index_name='skillDescription',
            node_label="Skill",
            text_node_properties=['description'],
            embedding_node_property='embeddingDescription',
        )
    except Exception as e:
        print('Error updating Skill index: ', e)

    try:
        Neo4jVector.from_existing_graph(
            embeddings,
            url=st.secrets["NEO4J_URI"],
            username=st.secrets["NEO4J_USERNAME"],
            password=st.secrets["NEO4J_PASSWORD"],
            index_name='learningOutcomeIndex',
            node_label="LearningOutcome",
            text_node_properties=['learning_outcome'],
            embedding_node_property='embeddingLearningOutcome',
        )
    except Exception as e:
        print('Error updating Learning Outcome index: ', e)

    print('Indexes updated')