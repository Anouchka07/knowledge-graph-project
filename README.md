# Knowledge Graph RAG System

A sophisticated Retrieval-Augmented Generation (RAG) system that creates knowledge graphs from text and enables natural language querying using Google's Gemini AI.

🔗 **[Live Demo on Streamlit Cloud](https://your-app-name.streamlit.app)** (Coming soon)

## Features

- **Knowledge Graph Generation**: Automatically extract entities and relationships from text
- **Interactive Visualization**: View your knowledge graph with an interactive web interface
- **Natural Language Querying**: Ask questions about your data in plain English
- **Entity Exploration**: Search and explore entities and their connections
- **Physics Toggle**: Control graph node behavior for better readability
- **Multiple Export Formats**: Save your knowledge graph in various formats

## Prerequisites

- Python 3.8 or higher
- Google Gemini API key
- Git (for cloning the repository)

## Quick Start (Streamlit Cloud)

1. Fork this repository
2. Deploy to Streamlit Cloud
3. Add your `GEMINI_API_KEY` to Streamlit secrets
4. Start exploring your knowledge graphs!

## Local Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/knowledge-graph-project.git
cd knowledge-graph-project
```

2. Create a virtual environment:
```bash
python -m venv env
```

3. Activate the virtual environment:
- On Windows: `env\Scripts\activate`
- On macOS/Linux: `source env/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Set up your environment variables:
- Create a `.env` file in the project root
- Add your Gemini API key: `GEMINI_API_KEY=your_api_key_here`

## Usage

### Web Interface (Streamlit)

1. Run the Streamlit app:
```bash
streamlit run streamlit_app.py
```

2. Open your browser and navigate to the provided URL
3. Upload a text file or use the existing `input.txt`
4. Generate your knowledge graph and explore!

### Command Line Interface

1. Place your text file as `input.txt` in the project root
2. Run the main script:
```bash
python main.py
```

## Deployment to Streamlit Cloud

1. Push your code to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect your GitHub repository
4. Add your `GEMINI_API_KEY` to the secrets
5. Deploy!

## API Key Setup

Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### For Local Development:
Add to `.env` file:
```
GEMINI_API_KEY=your_api_key_here
```

### For Streamlit Cloud:
Add to Streamlit Cloud secrets:
```toml
GEMINI_API_KEY = "your_api_key_here"
```

## Project Structure

- `streamlit_app.py`: Web interface with interactive features
- `main.py`: Core knowledge graph generation logic
- `graph_rag.py`: RAG system implementation
- `input.txt`: Sample input text
- `requirements.txt`: Python dependencies
- `secrets.toml.template`: Template for Streamlit secrets

## Features

### Interactive Graph Visualization
- Physics toggle for node positioning
- Compact settings panel
- Full-width graph display
- Entity type filtering

### Natural Language Querying
- Press Enter to query
- Clean, readable answers
- No redundant information

### Entity Management
- Search entities
- View connections
- Export data

## License

This project is licensed under the MIT License.
