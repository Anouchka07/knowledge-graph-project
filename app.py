import streamlit as st
from graph_rag import GraphRAG, Entity, Relationship
import streamlit_agraph as agraph
import json

# Define Streamlit interface
st.set_page_config(page_title="Knowledge Graph Query",
                   layout="wide")

st.title("Knowledge Graph RAG System")

# Placeholder for instructions
with st.expander("Instructions"):
    st.write("Use this interface to visualize the knowledge graph and query it with natural language questions.")

# Load entities and relationships (you might want to load these from a database or file)
entities = [
    Entity(name="ArtificialIntelligence", type="Concept", description="Capability of computational systems to perform tasks like humans"),
    Entity(name="ComputerScience", type="Concept", description="Field of research"),
    Entity(name="MachineLearning", type="Technology", description="Enables machines to learn from data"),
    Entity(name="DeepLearning", type="Technology", description="Subfield of machine learning")
    # Add other entities...
]

relationships = [
    Relationship(source="ArtificialIntelligence", target="ComputerScience", relation="field of", description="Relation to CS"),
    Relationship(source="ArtificialIntelligence", target="MachineLearning", relation="includes", description="Relationship with ML"),
    Relationship(source="MachineLearning", target="DeepLearning", relation="includes", description="Relationship with DL")
    # Add other relationships...
]

# Initialize GraphRAG
graph_rag = GraphRAG(entities, relationships)

# Define graph visualization function
def draw_graph(entities, relationships):
    config = {
        "nodeHighlightBehavior": True,
        "highlightColor": "#F7A7A6",
        "collapsible": True,
        "node": {
            "labelProperty": "name",
            "renderLabel": True
        },
        "link": {
            "labelProperty": "relation"
        }
    }

    nodes = [
        agraph.Node(id=entity.name, label=entity.name, title=entity.description)
        for entity in entities
    ]
    edges = [
        agraph.Edge(source=rel.source, target=rel.target, label=rel.relation)
        for rel in relationships
    ]

    return agraph.aGraph(
        nodes=nodes,
        edges=edges,
        config=config
    )

# Display graph
st.subheader("Knowledge Graph Visualization")
st.graph = draw_graph(entities, relationships)

# Query Input
st.subheader("Query the Graph")
user_query = st.text_area("Enter your question about the knowledge graph:")

# Query result
if st.button("Query"):
    if user_query:
        response = graph_rag.query_graph(user_query)
        st.text_area("Response from model:", value=response, height=200)
    else:
        st.warning("Please enter a query to continue.")
