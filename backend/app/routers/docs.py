"""
Documentation endpoints - serve markdown docs from skills folder
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import os

router = APIRouter(prefix="/docs", tags=["docs"])

SKILLS_DIR = Path(__file__).parent.parent.parent / "skills"


@router.get("")
async def get_docs():
    """Return all available documentation with content"""
    
    docs = {
        "sections": [
            {
                "id": "skills",
                "title": "Skills & Patterns",
                "icon": "lightbulb",
                "items": []
            },
            {
                "id": "getting-started",
                "title": "Getting Started",
                "icon": "zap",
                "items": [
                    {
                        "id": "introduction",
                        "title": "Introduction",
                        "content": """# Welcome to dbSherpa Studio

dbSherpa Studio is a powerful visual workflow automation platform for building intelligent AI-driven surveillance and data workflows.

## What is dbSherpa Studio?

dbSherpa Studio combines AI with deterministic data processing to create sophisticated automation workflows for trade surveillance, compliance monitoring, and data analysis.

## Key Features

- **Visual Workflow Builder**: Drag-and-drop interface for complex workflows
- **AI-Powered Nodes**: LLM integration for intelligent decision-making
- **Data Processing**: Built-in nodes for data collection and analysis
- **Real-time Execution**: Run workflows on-demand or automatically
- **Template Library**: Pre-built workflows for common use cases

## Getting Started

1. Create a new workflow from Templates
2. Add nodes from the Node Palette
3. Connect nodes to define workflow logic
4. Configure each node
5. Run and view results

Ready to build? Check out our Skills documentation."""
                    }
                ]
            }
        ]
    }
    
    # Load skills markdown files
    if SKILLS_DIR.exists():
        for md_file in sorted(SKILLS_DIR.glob("skills-*.md")):
            try:
                content = md_file.read_text(encoding='utf-8')
                title = md_file.stem.replace('skills-', '').replace('-', ' ').title()
                doc_id = md_file.stem.replace('skills-', '')
                
                docs["sections"][0]["items"].append({
                    "id": doc_id,
                    "title": title,
                    "content": content
                })
            except Exception as e:
                print(f"Error loading {md_file}: {e}")
    
    return docs
