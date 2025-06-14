import streamlit as st
from typing import Optional
import json
from pathlib import Path
from datetime import datetime, timedelta
from core.user_paths import get_memory_index_path

def render_sidebar(user_id: str):
    """Render the enhanced sidebar with OS-like navigation and features."""
    
    with st.sidebar:
        st.image("./screenshots/logo_image.png", width=50)
        st.title("MemoBrain OS")
        
        # Main navigation
        st.markdown("### 📱 Navigation")
        page = st.radio(
            "Select a view",
            ["📊 Dashboard", "📂 My Files", "📦 Memory Manager", "💬 Ask MemoBrain", "📅 Timeline", "🔄 Relationships", "🔍 Search"],
            label_visibility="collapsed"
        )
        st.session_state["current_page"] = page
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        if st.button("➕ New Memory"):
            st.session_state["current_page"] = "📦 Memory Manager"
        
        if st.button("🔍 Quick Search"):
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
            
            st.metric("Total Memories", total_memories)
            st.metric("Recent Activity", recent_memories)
            
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
                    sorted(all_tags)
                )
                if selected_tags:
                    st.session_state["selected_tags"] = selected_tags
            
            # Importance filter
            importance_levels = ["Critical", "High", "Medium", "Low", "Minimal"]
            selected_importance = st.multiselect(
                "Filter by importance",
                importance_levels
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
        if st.button("📚 Documentation"):
            st.markdown("[Open Documentation](https://github.com/mangesh-ux/multimodal-memory-assistant)")
        
        if st.button("🐛 Report Issue"):
            st.markdown("[Create Issue](https://github.com/mangesh-ux/multimodal-memory-assistant/issues)")
        
        # Footer
        st.markdown("---")
        st.markdown("MemoBrain OS v1.0")
        st.markdown("© 2025 Mangesh Gupta")

