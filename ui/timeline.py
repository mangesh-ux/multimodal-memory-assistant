import streamlit as st
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from core.user_paths import get_memory_index_path
from core.memory_handler import update_memory_access, MemoryImportance

def render_timeline_view(user_id: str):
    """Render the timeline view of memories."""
    st.title("📅 Memory Timeline")
    
    # Load memories
    memory_path = get_memory_index_path(user_id)
    if not memory_path.exists():
        st.info("No memories found. Start by creating some memories!")
        return
    
    with open(memory_path, "r") as f:
        memories = json.load(f)
    
    # Sort memories by creation date
    memories.sort(
        key=lambda x: x.get("temporal_metadata", {}).get("created_at", "2000-01-01"),
        reverse=True
    )
    
    # Timeline filters
    col1, col2, col3 = st.columns(3)
    with col1:
        date_range = st.date_input(
            "Date Range",
            value=(datetime.now().date(), datetime.now().date()),
            key="timeline_date_range"
        )
    
    with col2:
        selected_categories = st.multiselect(
            "Categories",
            options=sorted(set(m.get("category", "uncategorized") for m in memories)),
            key="timeline_categories"
        )
    
    with col3:
        selected_importance = st.multiselect(
            "Importance",
            options=[level.name for level in MemoryImportance],
            key="timeline_importance"
        )
    
    # Filter memories
    filtered_memories = memories
    if date_range:
        start_date, end_date = date_range
        filtered_memories = [
            m for m in filtered_memories
            if start_date <= datetime.fromisoformat(
                m.get("temporal_metadata", {}).get("created_at", "2000-01-01")
            ).date() <= end_date
        ]
    
    if selected_categories:
        filtered_memories = [
            m for m in filtered_memories
            if m.get("category", "uncategorized") in selected_categories
        ]
    
    if selected_importance:
        filtered_memories = [
            m for m in filtered_memories
            if MemoryImportance(m.get("importance", 3)).name in selected_importance
        ]
    
    # Render timeline
    if not filtered_memories:
        st.info("No memories found matching the selected filters.")
        return
    
    # Group memories by date
    memories_by_date = {}
    for memory in filtered_memories:
        date = datetime.fromisoformat(
            memory.get("temporal_metadata", {}).get("created_at", "2000-01-01")
        ).date()
        if date not in memories_by_date:
            memories_by_date[date] = []
        memories_by_date[date].append(memory)
    
    # Render timeline entries
    for date in sorted(memories_by_date.keys(), reverse=True):
        st.markdown(f"### {date.strftime('%B %d, %Y')}")
        
        for memory in memories_by_date[date]:
            # Create a unique key for each memory
            memory_key = f"memory_{memory.get('id', '')}"
            
            # Determine importance color
            importance = memory.get("importance", 3)
            importance_color = {
                5: "#dc3545",  # Critical
                4: "#fd7e14",  # High
                3: "#ffc107",  # Medium
                2: "#20c997",  # Low
                1: "#6c757d"   # Minimal
            }.get(importance, "#6c757d")
            
            # Create timeline entry
            with st.expander(
                f"{memory.get('title', 'Untitled')} ({memory.get('category', 'uncategorized')})",
                expanded=False
            ):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Memory content
                    st.markdown(memory.get("text_preview", "")[:500] + "...")
                    
                    # Tags
                    if memory.get("tags"):
                        st.markdown(
                            " ".join(f"`{tag}`" for tag in memory.get("tags", [])),
                            unsafe_allow_html=True
                        )
                    
                    # Notes
                    if memory.get("notes"):
                        st.markdown("**Notes:**")
                        st.markdown(memory.get("notes"))
                
                with col2:
                    # Metadata
                    st.markdown(f"""
                        <div style="
                            border-left: 3px solid {importance_color};
                            padding-left: 10px;
                            margin: 10px 0;
                        ">
                            <p><strong>Importance:</strong> {MemoryImportance(importance).name}</p>
                            <p><strong>Created:</strong> {datetime.fromisoformat(memory.get('temporal_metadata', {}).get('created_at', '2000-01-01')).strftime('%H:%M')}</p>
                            <p><strong>Last accessed:</strong> {datetime.fromisoformat(memory.get('temporal_metadata', {}).get('last_accessed', '2000-01-01')).strftime('%Y-%m-%d %H:%M')}</p>
                            <p><strong>Access count:</strong> {memory.get('access_count', 0)}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Actions
                    if st.button("View Details", key=f"view_{memory_key}"):
                        update_memory_access(memory["id"], user_id)
                        st.session_state["selected_memory"] = memory
                        st.session_state["current_page"] = "📦 Memory Manager"
                    
                    if st.button("View Relationships", key=f"rel_{memory_key}"):
                        st.session_state["selected_memory"] = memory
                        st.session_state["current_page"] = "🔄 Relationships"
            
            # Add a subtle separator between memories
            st.markdown("---") 