import streamlit as st
from typing import Optional
import json
from pathlib import Path
from datetime import datetime, timedelta
from core.user_paths import get_memory_index_path
from streamlit_option_menu import option_menu

def render_sidebar(user_id: str):
    """Render the enhanced sidebar with OS-like navigation and features."""
    
    with st.sidebar:
        # Logo and title
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image("./screenshots/logo_image.png", width=50)
        with col2:
            st.markdown("### MemoBrain OS")
        
        # Main navigation using option menu
        selected = option_menu(
            menu_title=None,
            options=["📊 Dashboard", "📂 My Files", "📦 Memory Manager", "🔍 Search", "📅 Timeline", "🔄 Relationships", "💬 Ask MemoBrain"],
            icons=["speedometer2", "folder", "box", "search", "calendar", "diagram-3", "chat"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {
                    "padding": "0!important",
                    "background-color": "var(--background-color)",
                    "border-radius": "0.5rem",
                },
                "icon": {"color": "var(--text-color)", "font-size": "1.2rem"},
                "nav-link": {
                    "font-size": "1rem",
                    "text-align": "left",
                    "margin": "0.2rem 0",
                    "border-radius": "0.5rem",
                    "color": "var(--text-color)",
                    "padding": "0.8rem 1rem",
                },
                "nav-link-selected": {
                    "background-color": "var(--primary-color)",
                    "color": "white",
                },
            },
        )
        st.session_state["current_page"] = selected
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ New Memory", use_container_width=True):
                st.session_state["current_page"] = "📦 Memory Manager"
        with col2:
            if st.button("🔍 Quick Search", use_container_width=True):
                st.session_state["current_page"] = "🔍 Search"
        
        # Memory insights
        st.markdown("### 📊 Memory Insights")
        memory_path = get_memory_index_path(user_id)
        if memory_path.exists():
            with open(memory_path, "r") as f:
                memories = json.load(f)
            
            # Calculate insights
            total_memories = len(memories)
            recent_memories = sum(1 for m in memories 
                                if datetime.fromisoformat(m.get("temporal_metadata", {}).get("last_accessed", "2000-01-01")) 
                                > datetime.now() - timedelta(days=7))
            
            # Create metrics with custom styling
            st.markdown("""
                <style>
                    .metric-card {
                        background-color: var(--background-color);
                        border: 1px solid var(--border-color);
                        border-radius: 0.5rem;
                        padding: 1rem;
                        margin: 0.5rem 0;
                    }
                    .metric-value {
                        font-size: 1.5rem;
                        font-weight: bold;
                        color: var(--primary-color);
                    }
                    .metric-label {
                        font-size: 0.9rem;
                        color: var(--text-color);
                    }
                </style>
            """, unsafe_allow_html=True)
            
            # Display metrics
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{total_memories}</div>
                    <div class="metric-label">Total Memories</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{recent_memories}</div>
                    <div class="metric-label">Recent Activity</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Memory categories
            categories = {}
            for memory in memories:
                cat = memory.get("category", "uncategorized")
                categories[cat] = categories.get(cat, 0) + 1
            
            st.markdown("#### Categories")
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                st.markdown(f"- {cat}: {count}")
        else:
            st.info("No memories found. Start by creating some!")
        
        # System status
        st.markdown("### 💻 System Status")
        st.markdown(f"**User ID:** {user_id}")
        st.markdown(f"**Last Sync:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Quick filters
        st.markdown("### 🔍 Quick Filters")
        if memory_path.exists():
            with open(memory_path, "r") as f:
                memories = json.load(f)
            
            # Get unique tags
            all_tags = set()
            for memory in memories:
                all_tags.update(memory.get("tags", []))
            
            if all_tags:
                selected_tags = st.multiselect(
                    "Filter by tags",
                    sorted(all_tags),
                    key="sidebar_tags"
                )
                if selected_tags:
                    st.session_state["selected_tags"] = selected_tags
            
            # Importance filter
            importance_levels = ["Critical", "High", "Medium", "Low", "Minimal"]
            selected_importance = st.multiselect(
                "Filter by importance",
                importance_levels,
                key="sidebar_importance"
            )
            if selected_importance:
                st.session_state["selected_importance"] = selected_importance
        
        # User preferences
        st.markdown("### ⚙️ Preferences")
        with st.expander("Display Settings"):
            st.checkbox("Show previews", value=True, key="show_previews")
            st.checkbox("Auto-generate summaries", value=True, key="auto_summarize")
            st.checkbox("Show relationships", value=True, key="show_relationships")
        
        with st.expander("Memory Settings"):
            st.number_input("Default importance", 1, 5, 3, key="default_importance")
            st.multiselect(
                "Default categories",
                ["personal", "work", "finance", "health", "education"],
                default=["personal"],
                key="default_categories"
            )
        
        # Help and support
        st.markdown("### ❓ Help & Support")
        if st.button("📚 Documentation", use_container_width=True):
            st.markdown("[Open Documentation](https://github.com/mangesh-ux/multimodal-memory-assistant)")
        
        if st.button("🐛 Report Issue", use_container_width=True):
            st.markdown("[Create Issue](https://github.com/mangesh-ux/multimodal-memory-assistant/issues)")
        
        # Footer
        st.markdown("---")
        st.markdown("MemoBrain OS v1.0")
        st.markdown("© 2025 Mangesh Gupta")

