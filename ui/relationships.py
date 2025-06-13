import streamlit as st
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import networkx as nx
import plotly.graph_objects as go
from core.user_paths import get_memory_index_path
from core.memory_handler import (
    update_memory_access,
    add_memory_relationship,
    MemoryImportance
)

def create_relationship_graph(memories: List[Dict[str, Any]]) -> nx.Graph:
    """Create a NetworkX graph from memory relationships."""
    G = nx.Graph()
    
    # Add nodes
    for memory in memories:
        G.add_node(
            memory["id"],
            title=memory.get("title", "Untitled"),
            category=memory.get("category", "uncategorized"),
            importance=memory.get("importance", 3)
        )
    
    # Add edges
    for memory in memories:
        for rel in memory.get("relationships", []):
            G.add_edge(
                memory["id"],
                rel["target_id"],
                type=rel["type"],
                description=rel.get("description", "")
            )
    
    return G

def render_relationships_view(user_id: str):
    """Render the relationships view of memories."""
    st.title("🔄 Memory Relationships")
    
    # Load memories
    memory_path = get_memory_index_path(user_id)
    if not memory_path.exists():
        st.info("No memories found. Start by creating some memories!")
        return
    
    with open(memory_path, "r") as f:
        memories = json.load(f)
    
    # Create relationship graph
    G = create_relationship_graph(memories)
    
    if not G.nodes():
        st.info("No memories found to create relationships.")
        return
    
    # Relationship management
    st.markdown("### Create New Relationship")
    col1, col2 = st.columns(2)
    
    with col1:
        # Source memory selection
        source_memory = st.selectbox(
            "Source Memory",
            options=[(m["id"], m.get("title", "Untitled")) for m in memories],
            format_func=lambda x: x[1]
        )
    
    with col2:
        # Target memory selection
        target_memory = st.selectbox(
            "Target Memory",
            options=[(m["id"], m.get("title", "Untitled")) for m in memories if m["id"] != source_memory[0]],
            format_func=lambda x: x[1]
        )
    
    # Relationship details
    relationship_type = st.selectbox(
        "Relationship Type",
        options=["references", "depends_on", "related_to", "summarizes", "expands_on", "contradicts"]
    )
    
    relationship_description = st.text_area("Relationship Description")
    
    if st.button("Create Relationship"):
        if source_memory and target_memory:
            add_memory_relationship(
                source_memory[0],
                target_memory[0],
                relationship_type,
                relationship_description,
                user_id
            )
            st.success("Relationship created successfully!")
            st.rerun()
    
    # Visualize relationships
    st.markdown("### Relationship Graph")
    
    if G.edges():
        # Create a Plotly figure
        pos = nx.spring_layout(G)
        
        # Create edge trace
        edge_x = []
        edge_y = []
        edge_text = []
        for edge in G.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_text.append(edge[2].get("type", ""))
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='text',
            mode='lines'
        )
        
        # Create node trace
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        for node in G.nodes(data=True):
            x, y = pos[node[0]]
            node_x.append(x)
            node_y.append(y)
            node_text.append(f"{node[1]['title']} ({node[1]['category']})")
            # Color nodes by importance
            importance = node[1].get("importance", 3)
            node_color.append({
                5: "#dc3545",  # Critical
                4: "#fd7e14",  # High
                3: "#ffc107",  # Medium
                2: "#20c997",  # Low
                1: "#6c757d"   # Minimal
            }.get(importance, "#6c757d"))
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="top center",
            marker=dict(
                showscale=True,
                colorscale='YlOrRd',
                size=20,
                color=node_color,
                line_width=2
            )
        )
        
        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title='Memory Relationships',
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                       )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show relationship details
        st.markdown("### Relationship Details")
        for memory in memories:
            if memory.get("relationships"):
                with st.expander(f"Relationships for: {memory.get('title', 'Untitled')}"):
                    for rel in memory["relationships"]:
                        # Find target memory
                        target = next((m for m in memories if m["id"] == rel["target_id"]), None)
                        if target:
                            st.markdown(f"""
                                <div style="
                                    background-color: rgba(49, 51, 63, 0.1);
                                    padding: 1rem;
                                    border-radius: 0.5rem;
                                    margin: 0.5rem 0;
                                ">
                                    <p><strong>Type:</strong> {rel['type']}</p>
                                    <p><strong>Target:</strong> {target.get('title', 'Untitled')}</p>
                                    <p><strong>Description:</strong> {rel.get('description', 'No description')}</p>
                                    <p><strong>Created:</strong> {datetime.fromisoformat(rel['created_at']).strftime('%Y-%m-%d %H:%M')}</p>
                                </div>
                            """, unsafe_allow_html=True)
    else:
        st.info("No relationships found. Create some relationships between memories to see them here!") 