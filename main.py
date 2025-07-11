import json
import os
import re
from typing import Dict, List, Tuple
import google.generativeai as genai
from dataclasses import dataclass
import networkx as nx
from pyvis.network import Network
from dotenv import load_dotenv
try:
    import PyPDF2
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("PDF processing not available. Install PyPDF2 and pdfplumber for PDF support.")

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
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file using pdfplumber for better formatting."""
        if not PDF_AVAILABLE:
            raise ImportError("PDF processing libraries not available. Install PyPDF2 and pdfplumber.")
        
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Error with pdfplumber, trying PyPDF2: {e}")
            # Fallback to PyPDF2
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            except Exception as e2:
                print(f"Error with PyPDF2: {e2}")
                raise
        
        return text.strip()
    
    def preprocess_academic_text(self, text: str) -> str:
        """Preprocess academic text to improve entity extraction."""
        # Remove excessive whitespace and line breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common academic formatting artifacts
        text = re.sub(r'\b\d+\b(?=\s*$)', '', text, flags=re.MULTILINE)  # Remove page numbers
        text = re.sub(r'\[\d+\]', '', text)  # Remove citation numbers
        text = re.sub(r'\(\d{4}\)', '', text)  # Remove years in parentheses when standalone
        
        # Clean up hyphenated words at line breaks
        text = re.sub(r'([a-z])-\s+([a-z])', r'\1\2', text)
        
        return text
    
    def extract_entities_and_relationships(self, text: str) -> Tuple[List[Entity], List[Relationship]]:
        """Extract entities and relationships from text using Gemini."""
        
        # Preprocess text for better academic content handling
        text = self.preprocess_academic_text(text)
        
        # Increase text length limit for better academic content processing
        if len(text) > 6000:
            # For longer texts, take first 3000 and last 3000 characters to capture intro and conclusion
            text = text[:3000] + "\n\n[...middle content truncated...]\n\n" + text[-3000:]
        
        prompt = f"""
        You are an expert knowledge graph generator specializing in academic and literary content. Analyze the following text and extract entities and relationships to create a comprehensive knowledge graph.
        
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
        
        IMPORTANT GUIDELINES for Academic/Literary Content:
        
        ENTITY EXTRACTION:
        - Extract 20-30 entities for comprehensive coverage
        - Focus on key concepts, theories, methodologies, and frameworks
        - Include important authors, researchers, and historical figures mentioned
        - Identify specific terms, models, algorithms, or principles
        - Capture institutions, publications, and significant works referenced
        - Include temporal entities (time periods, dates, eras) when relevant
        - Extract geographical locations if contextually important
        
        ENTITY TYPES (choose most appropriate):
        - Concept: Abstract ideas, theories, principles, frameworks
        - Method: Techniques, algorithms, processes, methodologies
        - Person: Authors, researchers, historical figures, theorists
        - Organization: Institutions, companies, research groups
        - Publication: Books, papers, journals, studies
        - Technology: Tools, systems, software, instruments
        - Event: Historical events, discoveries, developments
        - Location: Geographic places, regions, countries
        - Temporal: Time periods, eras, dates
        - Field: Academic disciplines, domains of study
        - Metric: Measurements, indicators, variables
        
        RELATIONSHIP EXTRACTION:
        - Extract 25-35 relationships for rich connectivity
        - Focus on intellectual and conceptual connections
        - Include hierarchical relationships (broader/narrower concepts)
        - Capture causal relationships (causes, leads to, results in)
        - Identify comparative relationships (similar to, different from)
        - Include temporal relationships (preceded by, followed by, developed from)
        - Capture authorship and attribution relationships
        - Include methodological relationships (uses, applies, implements)
        
        RELATIONSHIP TYPES (choose most appropriate):
        - defines: One concept defines another
        - includes: One concept includes another as a component
        - uses: One entity uses another as a tool or method
        - develops: One entity develops or creates another
        - influences: One entity influences another
        - based_on: One concept is based on another
        - applies_to: One method applies to a domain or problem
        - authored_by: A work is authored by a person
        - published_in: A work is published in a venue
        - part_of: One entity is part of a larger entity
        - leads_to: One concept or event leads to another
        - measures: One metric measures another concept
        - belongs_to: One entity belongs to a category or field
        - preceded_by: One entity came before another temporally
        - similar_to: Two entities share similarities
        - opposite_of: Two entities are contrasting
        - requires: One entity requires another to function
        - evaluates: One method evaluates another entity
        
        QUALITY REQUIREMENTS:
        - Use clear, concise entity names (avoid overly long phrases)
        - Ensure entity names in relationships match exactly with entity names in the entities list
        - Provide meaningful descriptions (30-60 characters)
        - Maintain academic precision while keeping descriptions accessible
        - Prioritize the most important and well-established entities and relationships
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
        
        # Read input text based on file type
        try:
            if input_file.lower().endswith('.pdf'):
                if not PDF_AVAILABLE:
                    print("Error: PDF processing libraries not available. Install PyPDF2 and pdfplumber.")
                    return
                print("Extracting text from PDF...")
                text = self.extract_text_from_pdf(input_file)
            else:
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
