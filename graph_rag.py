import json
import os
from typing import List, Dict, Any, Tuple
import google.generativeai as genai
import networkx as nx
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Entity:
    name: str
    type: str
    description: str = ""

@dataclass
class Relationship:
    source: str
    target: str
    relation: str
    description: str = ""

class GraphRAG:
    def __init__(self, entities: List[Entity], relationships: List[Relationship]):
        """Initialize GraphRAG with entities and relationships."""
        self.entities = entities
        self.relationships = relationships
        self.graph = self._build_networkx_graph()
        
        # Initialize Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def _build_networkx_graph(self) -> nx.Graph:
        """Build a NetworkX graph from entities and relationships."""
        G = nx.Graph()
        
        # Add nodes (entities)
        for entity in self.entities:
            G.add_node(entity.name, 
                      type=entity.type, 
                      description=entity.description)
        
        # Add edges (relationships)
        for rel in self.relationships:
            if rel.source in G.nodes and rel.target in G.nodes:
                G.add_edge(rel.source, rel.target, 
                          relation=rel.relation, 
                          description=rel.description)
        
        return G
    
    def get_entity_info(self, entity_name: str) -> Dict[str, Any]:
        """Get information about a specific entity."""
        entity = next((e for e in self.entities if e.name == entity_name), None)
        if not entity:
            return None
        
        # Get connected entities
        connected = []
        if entity_name in self.graph.nodes:
            for neighbor in self.graph.neighbors(entity_name):
                edge_data = self.graph[entity_name][neighbor]
                connected.append({
                    'entity': neighbor,
                    'relation': edge_data.get('relation', ''),
                    'description': edge_data.get('description', '')
                })
        
        return {
            'entity': asdict(entity),
            'connections': connected
        }
    
    def find_path(self, start_entity: str, end_entity: str) -> List[str]:
        """Find the shortest path between two entities."""
        try:
            if start_entity in self.graph.nodes and end_entity in self.graph.nodes:
                path = nx.shortest_path(self.graph, start_entity, end_entity)
                return path
            return []
        except nx.NetworkXNoPath:
            return []
    
    def get_subgraph(self, center_entity: str, depth: int = 2) -> Tuple[List[Entity], List[Relationship]]:
        """Get a subgraph centered around an entity within a certain depth."""
        if center_entity not in self.graph.nodes:
            return [], []
        
        # Get nodes within the specified depth
        subgraph_nodes = set([center_entity])
        current_level = {center_entity}
        
        for _ in range(depth):
            next_level = set()
            for node in current_level:
                next_level.update(self.graph.neighbors(node))
            subgraph_nodes.update(next_level)
            current_level = next_level
        
        # Filter entities and relationships
        subgraph_entities = [e for e in self.entities if e.name in subgraph_nodes]
        subgraph_relationships = [r for r in self.relationships 
                                if r.source in subgraph_nodes and r.target in subgraph_nodes]
        
        return subgraph_entities, subgraph_relationships
    
    def search_entities(self, query: str) -> List[Entity]:
        """Search for entities based on name or description."""
        query_lower = query.lower()
        matching_entities = []
        
        for entity in self.entities:
            if (query_lower in entity.name.lower() or 
                query_lower in entity.description.lower() or
                query_lower in entity.type.lower()):
                matching_entities.append(entity)
        
        return matching_entities
    
    def get_graph_context(self, query: str, max_entities: int = 10) -> str:
        """Get relevant graph context for a query."""
        # Search for relevant entities
        relevant_entities = self.search_entities(query)[:max_entities]
        
        if not relevant_entities:
            # If no direct matches, use all entities (limited)
            relevant_entities = self.entities[:max_entities]
        
        # Build context string
        context_parts = []
        context_parts.append("Knowledge Graph Information:")
        context_parts.append("\nEntities:")
        
        for entity in relevant_entities:
            context_parts.append(f"- {entity.name} ({entity.type}): {entity.description}")
        
        context_parts.append("\nRelationships:")
        entity_names = {e.name for e in relevant_entities}
        
        relevant_relationships = [
            r for r in self.relationships 
            if r.source in entity_names or r.target in entity_names
        ]
        
        for rel in relevant_relationships[:20]:  # Limit relationships
            context_parts.append(f"- {rel.source} --[{rel.relation}]--> {rel.target}")
        
        return "\n".join(context_parts)
    
    def query_graph(self, user_query: str) -> str:
        """Query the knowledge graph using Gemini."""
        # Get relevant context from the graph
        graph_context = self.get_graph_context(user_query)
        
        # Create prompt for Gemini
        prompt = f"""
        You are a knowledge graph assistant. Use the following knowledge graph information to answer the user's question accurately and comprehensively.

        {graph_context}

        User Question: {user_query}

        Instructions:
        1. Use only the information provided in the knowledge graph
        2. If the information is not available in the graph, clearly state that
        3. Provide specific entity names and relationships when relevant
        4. If there are connections between entities, explain the path
        5. Be concise but informative

        Answer:
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error querying the knowledge graph: {str(e)}"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get basic statistics about the knowledge graph."""
        entity_types = {}
        for entity in self.entities:
            entity_types[entity.type] = entity_types.get(entity.type, 0) + 1
        
        relation_types = {}
        for rel in self.relationships:
            relation_types[rel.relation] = relation_types.get(rel.relation, 0) + 1
        
        return {
            'total_entities': len(self.entities),
            'total_relationships': len(self.relationships),
            'entity_types': entity_types,
            'relation_types': relation_types,
            'graph_density': nx.density(self.graph) if self.graph.number_of_nodes() > 0 else 0
        }
    
    def get_most_connected_entities(self, top_n: int = 5) -> List[Tuple[str, int]]:
        """Get the most connected entities in the graph."""
        if not self.graph.nodes:
            return []
        
        degree_centrality = nx.degree_centrality(self.graph)
        sorted_entities = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)
        
        return [(entity, int(centrality * (len(self.graph.nodes) - 1))) 
                for entity, centrality in sorted_entities[:top_n]]
