import json
import os
import re
from typing import Dict, List, Tuple
import google.generativeai as genai
from dataclasses import dataclass
import networkx as nx
from pyvis.network import Network
from dotenv import load_dotenv

# Load environment variables from .env file
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

class KnowledgeGraphGenerator:
    def __init__(self, api_key: str):
        """Initialize the knowledge graph generator with Gemini API key."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def extract_entities_and_relationships(self, text: str) -> Tuple[List[Entity], List[Relationship]]:
        """Extract entities and relationships from text using Gemini."""
        
        # Limit text length to avoid response truncation
        if len(text) > 3000:
            text = text[:3000] + "..."
        
        prompt = f"""
        Analyze the following text and extract entities and relationships to create a knowledge graph.
        
        Text: {text}
        
        Please return ONLY a valid JSON object in the following format (no markdown code blocks):
        {{
            "entities": [
                {{
                    "name": "entity_name",
                    "type": "entity_type",
                    "description": "brief description"
                }}
            ],
            "relationships": [
                {{
                    "source": "source_entity",
                    "target": "target_entity",
                    "relation": "relationship_type",
                    "description": "brief description of the relationship"
                }}
            ]
        }}
        
        Guidelines:
        - Extract maximum 15 entities and 20 relationships to avoid response truncation
        - Use simple entity names (avoid quotes and special characters)
        - Entity types: Person, Organization, Location, Concept, Technology, Event, etc.
        - Relationship types: develops, creates, enables, includes, requires, etc.
        - Keep descriptions under 50 characters
        - Ensure entity names in relationships match exactly with entity names in the entities list
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Extract JSON from response
            json_text = response.text
            print(f"Raw response: {json_text[:500]}...")  # Debug print
            
            # Clean up the response to extract only the JSON part
            json_text = json_text.replace('```json', '').replace('```', '').strip()
            
            json_start = json_text.find('{')
            json_end = json_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                print("No valid JSON found in response")
                return [], []
            
            json_text = json_text[json_start:json_end]
            print(f"Extracted JSON: {json_text[:200]}...")  # Debug print
            
            # Try to fix common JSON issues
            json_text = json_text.replace('\n', ' ').replace('\r', ' ')
            json_text = ' '.join(json_text.split())  # Remove extra whitespace
            
            # Try to parse JSON
            try:
                data = json.loads(json_text)
            except json.JSONDecodeError:
                # If parsing fails, try to fix truncated JSON
                print("JSON appears truncated, attempting to fix...")
                # Check if the JSON ends properly
                if not json_text.endswith('}'):
                    # Count open braces and brackets
                    open_braces = json_text.count('{') - json_text.count('}')
                    open_brackets = json_text.count('[') - json_text.count(']')
                    
                    # Add missing closing characters
                    json_text += ']' * open_brackets + '}' * open_braces
                    
                data = json.loads(json_text)
            
            entities = [Entity(**entity) for entity in data['entities']]
            relationships = [Relationship(**rel) for rel in data['relationships']]
            
            return entities, relationships
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Problematic JSON: {json_text[:1000]}")
            return [], []
        except Exception as e:
            print(f"Error extracting entities and relationships: {e}")
            return [], []
    
    def create_interactive_graph(self, entities: List[Entity], relationships: List[Relationship], output_file: str = "knowledge_graph.html"):
        """Create an interactive HTML knowledge graph using pyvis."""
        
        # Create a network graph
        net = Network(height="800px", width="100%", bgcolor="#ffffff", font_color="black")
        
        # Configure physics and interaction options
        net.set_options("""
        var options = {
            "physics": {
                "enabled": true,
                "stabilization": {"enabled": true, "iterations": 100},
                "barnesHut": {
                    "gravitationalConstant": -2000,
                    "centralGravity": 0.3,
                    "springLength": 95,
                    "springConstant": 0.04,
                    "damping": 0.09
                }
            },
            "interaction": {
                "dragNodes": true,
                "dragView": true,
                "zoomView": true,
                "hover": true,
                "tooltipDelay": 300
            },
            "manipulation": {
                "enabled": false
            }
        }
        """)
        
        # Add nodes (entities)
        entity_colors = {
            "person": "#FF6B6B",
            "organization": "#4ECDC4",
            "location": "#45B7D1",
            "place": "#45B7D1",
            "concept": "#96CEB4",
            "event": "#FFEAA7",
            "object": "#DDA0DD",
            "award": "#FFD700",
            "equation": "#FF6347",
            "default": "#B0B0B0"
        }
        
        for entity in entities:
            color = entity_colors.get(entity.type.lower(), entity_colors["default"])
            net.add_node(
                entity.name,
                label=entity.name,
                title=f"Type: {entity.type}\nDescription: {entity.description}",
                color=color,
                size=20
            )
        
        # Add edges (relationships)
        for rel in relationships:
            net.add_edge(
                rel.source,
                rel.target,
                label=rel.relation,
                title=rel.description,
                color="#666666",
                width=2
            )
        
        # Add custom JavaScript for better drag behavior
        custom_js = """
        // Custom drag behavior to keep nodes in place
        network.on("stabilizationIterationsDone", function() {
            // Disable physics after initial stabilization
            network.setOptions({physics: {enabled: false}});
        });
        
        network.on("dragStart", function(params) {
            // Disable physics when dragging starts
            network.setOptions({physics: {enabled: false}});
        });
        
        network.on("dragEnd", function(params) {
            // Keep physics disabled after dragging
            if (params.nodes.length > 0) {
                var nodeId = params.nodes[0];
                var position = network.getPositions([nodeId]);
                // Node will stay in its new position
            }
        });
        
        // Add a toggle button for physics
        var physicsEnabled = false;
        var toggleButton = document.createElement('button');
        toggleButton.innerHTML = 'Toggle Physics';
        toggleButton.style.position = 'absolute';
        toggleButton.style.top = '10px';
        toggleButton.style.left = '10px';
        toggleButton.style.zIndex = '1000';
        toggleButton.style.padding = '5px 10px';
        toggleButton.style.backgroundColor = '#4CAF50';
        toggleButton.style.color = 'white';
        toggleButton.style.border = 'none';
        toggleButton.style.borderRadius = '3px';
        toggleButton.style.cursor = 'pointer';
        
        toggleButton.onclick = function() {
            physicsEnabled = !physicsEnabled;
            network.setOptions({physics: {enabled: physicsEnabled}});
            toggleButton.innerHTML = physicsEnabled ? 'Disable Physics' : 'Enable Physics';
            toggleButton.style.backgroundColor = physicsEnabled ? '#f44336' : '#4CAF50';
        };
        
        document.body.appendChild(toggleButton);
        """
        
        # Generate HTML with notebook=False to avoid template issues
        try:
            net.show(output_file, notebook=False)
            
            # Add custom JavaScript to the generated HTML
            with open(output_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Insert custom JavaScript before the closing body tag
            html_content = html_content.replace('</body>', f'<script>{custom_js}</script></body>')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"Interactive knowledge graph saved as {output_file}")
        except Exception as e:
            print(f"Error generating HTML: {e}")
            # Fallback: use write_html directly
            net.write_html(output_file, open_browser=False, notebook=False)
            print(f"Interactive knowledge graph saved as {output_file} (fallback method)")
    
    def generate_knowledge_graph(self, input_file: str, output_file: str = "knowledge_graph.html"):
        """Main method to generate knowledge graph from input file."""
        
        # Read input text
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Error: Input file '{input_file}' not found.")
            return
        except Exception as e:
            print(f"Error reading input file: {e}")
            return
        
        if not text.strip():
            print("Error: Input file is empty.")
            return
        
        print("Extracting entities and relationships...")
        entities, relationships = self.extract_entities_and_relationships(text)
        
        if not entities:
            print("No entities found in the text.")
            return
        
        print(f"Found {len(entities)} entities and {len(relationships)} relationships")
        
        # Print extracted information
        print("\nEntities:")
        for entity in entities:
            print(f"  - {entity.name} ({entity.type}): {entity.description}")
        
        print("\nRelationships:")
        for rel in relationships:
            print(f"  - {rel.source} --[{rel.relation}]--> {rel.target}")
        
        # Create interactive graph
        print("\nCreating interactive knowledge graph...")
        self.create_interactive_graph(entities, relationships, output_file)

def main():
    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: Please set your GEMINI_API_KEY environment variable.")
        print("You can get an API key from: https://makersuite.google.com/app/apikey")
        return
    
    # Initialize the generator
    generator = KnowledgeGraphGenerator(api_key)
    
    # Generate knowledge graph
    input_file = "input.txt"
    output_file = "knowledge_graph.html"
    
    generator.generate_knowledge_graph(input_file, output_file)

if __name__ == "__main__":
    main()
