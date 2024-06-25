from rdflib_neo4j import Neo4jStoreConfig, Neo4jStore, HANDLE_VOCAB_URI_STRATEGY, HANDLE_MULTIVAL_STRATEGY
from rdflib import Graph

# set the configuration to connect to your Aura DB
AURA_DB_URI="bolt://localhost:7687"
AURA_DB_USERNAME="neo4j"
AURA_DB_PWD="ciaociao"

auth_data = {'uri': AURA_DB_URI,
             'database': "neo4j",
             'user': AURA_DB_USERNAME,
             'pwd': AURA_DB_PWD}

# Define your custom mappings & store config
config = Neo4jStoreConfig(auth_data=auth_data,
                          handle_vocab_uri_strategy=HANDLE_VOCAB_URI_STRATEGY.IGNORE,
                          handle_multival_strategy=HANDLE_MULTIVAL_STRATEGY.ARRAY,
                          batching=True)

file_path = 'FILEPATH'

# Create the RDF Graph, parse & ingest the data to Neo4j, and close the store(If the field batching is set to True in the Neo4jStoreConfig, remember to close the store to prevent the loss of any uncommitted records.)
neo4j_aura = Graph(store=Neo4jStore(config=config))
# Calling the parse method will implictly open the store
neo4j_aura.parse(file_path, format="ttl")
neo4j_aura.close(True)