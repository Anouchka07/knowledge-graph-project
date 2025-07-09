import streamlit as st
import json
import os
import sys
from typing import List, Dict, Any
import pandas as pd
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import KnowledgeGraphGenerator, Entity, Relationship
from graph_rag import GraphRAG
import streamlit_agraph as agraph

# Load environment variables
load_dotenv()

# Streamlit page configuration
st.set_page_config(
    page_title="Knowledge Graph RAG System",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .entity-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    /* Make graph container take full width */
    .element-container {
        width: 100% !important;
    }
    /* Compact expander styling */
    .streamlit-expanderHeader {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 0.5rem;
        margin-bottom: 1rem;
    }
    /* Physics toggle highlighting */
    .stCheckbox > label {
        font-weight: bold;
        color: #1f77b4;
    }
    /* Make answer boxes wider and more prominent */
    .element-container div[data-testid="stMarkdown"] {
        width: 100% !important;
    }
    /* Success/Info boxes take full width */
    .stSuccess, .stInfo {
        width: 100% !important;
        padding: 1rem !important;
        margin: 0.5rem 0 !important;
    }
    /* Query response styling */
    .stSuccess > div {
        font-size: 1.1rem !important;
        line-height: 1.6 !important;
        white-space: pre-wrap !important;
    }
</style>
""", unsafe_allow_html=True)

# Main title
st.markdown('<h1 class="main-header">Graph RAG</h1>', unsafe_allow_html=True)

# Initialize session state
if 'graph_rag' not in st.session_state:
    st.session_state.graph_rag = None
if 'entities' not in st.session_state:
    st.session_state.entities = []
if 'relationships' not in st.session_state:
    st.session_state.relationships = []

# Sidebar for controls
with st.sidebar:
    st.header("🔧 Controls")
    
    # File upload for input text
    uploaded_file = st.file_uploader("Upload text file", type=['txt'])
    
    # Or use the existing input.txt
    use_existing = st.checkbox("Use existing input.txt", value=True)
    
    if st.button("🔄 Generate Knowledge Graph"):
        if use_existing or uploaded_file:
            try:
                # Initialize the knowledge graph generator
                # Try to get API key from Streamlit secrets first, then environment variables
                try:
                    api_key = st.secrets["GEMINI_API_KEY"]
                except KeyError:
                    api_key = os.getenv('GEMINI_API_KEY')
                
                if not api_key:
                    st.error("GEMINI_API_KEY not found in Streamlit secrets or environment variables")
                    st.error("Please add your Gemini API key to the Streamlit Cloud secrets.")
                    st.stop()
                
                generator = KnowledgeGraphGenerator(api_key)
                
                # Read text input
                if uploaded_file:
                    text = uploaded_file.read().decode('utf-8')
                else:
                    with open('input.txt', 'r', encoding='utf-8') as f:
                        text = f.read()
                
                # Generate entities and relationships
                with st.spinner("Generating knowledge graph..."):
                    entities, relationships = generator.extract_entities_and_relationships(text)
                
                if entities:
                    st.session_state.entities = entities
                    st.session_state.relationships = relationships
                    st.session_state.graph_rag = GraphRAG(entities, relationships)
                    st.success(f"✅ Generated {len(entities)} entities and {len(relationships)} relationships")
                else:
                    st.error("❌ No entities found in the text")
                    
            except Exception as e:
                st.error(f"Error generating knowledge graph: {str(e)}")
        else:
            st.warning("Please upload a file or use existing input.txt")
    
    # Display graph statistics
    if st.session_state.graph_rag:
        st.header("📊 Graph Statistics")
        stats = st.session_state.graph_rag.get_statistics()
        
        st.metric("Total Entities", stats['total_entities'])
        st.metric("Total Relationships", stats['total_relationships'])
        st.metric("Graph Density", f"{stats['graph_density']:.3f}")
        
        # Entity types breakdown
        st.subheader("Entity Types")
        for entity_type, count in stats['entity_types'].items():
            st.write(f"• {entity_type}: {count}")

# Main content area
if st.session_state.graph_rag:
    
    # Create tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Query Graph", "📈 Visualization", "🔎 Entity Explorer", "📋 Graph Data"])
    
    with tab1:
        st.header("Query the Knowledge Graph")
        
        # Query input with Enter key functionality
        user_query = st.text_input(
            "Enter your question (press Enter to query):",
            placeholder="Ask a question about your knowledge graph...",
            key="query_input"
        )
        
        # Process query when user presses Enter or types
        if user_query:
            with st.spinner("Querying knowledge graph..."):
                response = st.session_state.graph_rag.query_graph(user_query)
            
            # Display answer directly with black text
            st.markdown("---")
            st.markdown("### Answer:")
            st.markdown(f'<div style="background-color: #f0f2f6; padding: 1rem; border-radius: 8px; color: black; font-size: 1.1rem; line-height: 1.6;">{response}</div>', unsafe_allow_html=True)
            st.markdown("---")
        
        # Sample queries
        # st.subheader("💡 Sample Queries")
        # sample_queries = [
        #     "What is artificial intelligence?",
        #     "How is machine learning related to deep learning?",
        #     "What technologies are included in AI?",
        #     "Tell me about the relationship between AI and computer science"
        # ]
        
        # for i, query in enumerate(sample_queries):
        #     if st.button(f"📌 {query}", key=f"sample_{i}"):
        #         response = st.session_state.graph_rag.query_graph(query)
        #         st.markdown(f"**Q:** {query}")
        #         st.markdown(f"**A:** {response}")
    
    with tab2:
        st.header("Knowledge Graph Visualization")
        
        # Compact graph configuration at the top
        with st.expander("⚙️ Graph Settings", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                node_size = st.slider("Node Size", 10, 50, 25, key="node_size")
            
            with col2:
                edge_distance = st.slider("Edge Distance", 50, 200, 100, key="edge_distance")
            
            with col3:
                # Physics toggle
                physics_enabled = st.checkbox("Enable Physics", value=True, key="physics_toggle")
                st.caption("💡 Disable physics to manually position nodes")
            
            with col4:
                # Entity type filter
                entity_types = list(set(e.type for e in st.session_state.entities))
                selected_types = st.multiselect(
                    "Filter by Type",
                    entity_types,
                    default=entity_types,
                    key="entity_filter"
                )
        
        # Physics status indicator
        if physics_enabled:
            st.success("🔴 Physics: ON - Nodes will auto-arrange and can be dragged")
        else:
            st.info("⚫ Physics: OFF - Nodes can be manually positioned")
        
        # Main graph area takes full width
        with st.container():
            # Filter entities and relationships based on selected types
            filtered_entities = [e for e in st.session_state.entities if e.type in selected_types]
            filtered_entity_names = {e.name for e in filtered_entities}
            filtered_relationships = [
                r for r in st.session_state.relationships 
                if r.source in filtered_entity_names and r.target in filtered_entity_names
            ]
            
            # Create graph visualization
            if filtered_entities and filtered_relationships:
                # Define colors for different entity types
                color_map = {
                    'Concept': '#FF6B6B',
                    'Technology': '#4ECDC4',
                    'Organization': '#45B7D1',
                    'Person': '#96CEB4',
                    'Event': '#FFEAA7',
                    'Location': '#DDA0DD'
                }
                
                nodes = []
                for entity in filtered_entities:
                    color = color_map.get(entity.type, '#B0B0B0')
                    nodes.append(
                        agraph.Node(
                            id=entity.name,
                            label=entity.name,
                            size=node_size,
                            color=color,
                            title=f"{entity.type}: {entity.description}"
                        )
                    )
                
                edges = []
                for rel in filtered_relationships:
                    edges.append(
                        agraph.Edge(
                            source=rel.source,
                            target=rel.target,
                            label=rel.relation,
                            color="#666666"
                        )
                    )
                
                config = agraph.Config(
                    width=1200,
                    height=700,
                    directed=True,
                    physics=physics_enabled,
                    hierarchical=False,
                    nodeHighlightBehavior=True,
                    highlightColor="#F7A7A6",
                    collapsible=True,
                    # Additional physics configuration
                    physics_enabled=physics_enabled,
                    physics_stabilization_iterations=100 if physics_enabled else 0
                )
                
                return_value = agraph.agraph(
                    nodes=nodes,
                    edges=edges,
                    config=config
                )
                
                if return_value:
                    st.write(f"Selected node: {return_value}")
            else:
                st.info("No entities match the selected filters")
    
    with tab3:
        st.header("Entity Explorer")
        
        # Search entities
        search_query = st.text_input("🔍 Search entities:", placeholder="Type to search...")
        
        if search_query:
            matching_entities = st.session_state.graph_rag.search_entities(search_query)
            
            if matching_entities:
                st.subheader(f"Found {len(matching_entities)} matching entities:")
                
                for entity in matching_entities:
                    with st.expander(f"{entity.name} ({entity.type})"):
                        st.write(f"**Description:** {entity.description}")
                        
                        # Get entity connections
                        entity_info = st.session_state.graph_rag.get_entity_info(entity.name)
                        if entity_info and entity_info['connections']:
                            st.write("**Connections:**")
                            for conn in entity_info['connections']:
                                st.write(f"• {conn['relation']} → {conn['entity']}")
                        else:
                            st.write("No connections found")
            else:
                st.info("No entities found matching your search")
        
        # Most connected entities
        st.subheader("🔗 Most Connected Entities")
        most_connected = st.session_state.graph_rag.get_most_connected_entities()
        
        if most_connected:
            df = pd.DataFrame(most_connected, columns=['Entity', 'Connections'])
            st.dataframe(df, use_container_width=True)
    
    with tab4:
        st.header("Graph Data")
        
        # Display entities
        st.subheader("📋 Entities")
        if st.session_state.entities:
            entities_df = pd.DataFrame([
                {
                    'Name': e.name,
                    'Type': e.type,
                    'Description': e.description
                }
                for e in st.session_state.entities
            ])
            st.dataframe(entities_df, use_container_width=True)
        
        # Display relationships
        st.subheader("🔗 Relationships")
        if st.session_state.relationships:
            relationships_df = pd.DataFrame([
                {
                    'Source': r.source,
                    'Relation': r.relation,
                    'Target': r.target,
                    'Description': r.description
                }
                for r in st.session_state.relationships
            ])
            st.dataframe(relationships_df, use_container_width=True)
        
        # Download options
        st.subheader("💾 Download Data")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Download as JSON"):
                data = {
                    'entities': [
                        {
                            'name': e.name,
                            'type': e.type,
                            'description': e.description
                        }
                        for e in st.session_state.entities
                    ],
                    'relationships': [
                        {
                            'source': r.source,
                            'target': r.target,
                            'relation': r.relation,
                            'description': r.description
                        }
                        for r in st.session_state.relationships
                    ]
                }
                
                st.download_button(
                    label="Download JSON",
                    data=json.dumps(data, indent=2),
                    file_name="knowledge_graph.json",
                    mime="application/json"
                )

else:
    # Welcome message when no graph is loaded
    st.markdown("""
    
    This system allows you to:
    - **Generate** knowledge graphs from text using AI
    - **Visualize** entities and their relationships
    - **Query** the graph with natural language questions
    - **Explore** entities and connections
    
    ### Getting Started:
    1. Use the sidebar to upload a text file or use the existing `input.txt`
    2. Click "Generate Knowledge Graph" to create your graph
    3. Explore the tabs to visualize and query your data
    
    ### Features:
    - Interactive graph visualization
    - Natural language querying with Gemini AI
    - Entity search and exploration
    - Graph statistics and analytics
    - Export capabilities
    """)
    
    # # Display some example information
    # st.info("Make sure your `input.txt` file contains meaningful text for the best results!")

# Footer
st.markdown("---")
st.markdown(" Powered by Gemini")
