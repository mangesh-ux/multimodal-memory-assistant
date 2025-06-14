import streamlit as st
from typing import Optional
import json
from pathlib import Path
from datetime import datetime, timedelta
from core.user_paths import get_memory_index_path
from streamlit_option_menu import option_menu

def render_sidebar(user_id: str):
    """Render the enhanced sidebar with OS-like navigation and features."""
    
    # Custom CSS for enhanced styling
    st.markdown("""
        <style>
            /* Main sidebar styling */
            .css-1d391kg {
                background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
                padding: 1rem;
            }
            
            /* Logo and title styling */
            .logo-container {
                padding: 1rem 0;
                margin-bottom: 2rem;
                text-align: center;
            }
            
            /* Navigation menu styling */
            .nav-link {
                transition: all 0.3s ease;
                border-radius: 8px !important;
                margin: 0.3rem 0 !important;
            }
            
            .nav-link:hover {
                background-color: rgba(255, 255, 255, 0.1) !important;
                transform: translateX(5px);
            }
            
            /* Metric cards styling */
            .metric-card {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                padding: 1.2rem;
                margin: 0.8rem 0;
                border: 1px solid rgba(255, 255, 255, 0.1);
                transition: all 0.3s ease;
            }
            
            .metric-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            }
            
            .metric-value {
                font-size: 2rem;
                font-weight: 700;
                background: linear-gradient(45deg, #4CAF50, #2196F3);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.5rem;
            }
            
            .metric-label {
                font-size: 0.9rem;
                color: #a0a0a0;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            /* Section headers */
            .section-header {
                color: #ffffff;
                font-size: 1.1rem;
                font-weight: 600;
                margin: 1.5rem 0 1rem 0;
                padding-bottom: 0.5rem;
                border-bottom: 2px solid rgba(255, 255, 255, 0.1);
            }
            
            /* Button styling */
            .stButton button {
                background: linear-gradient(45deg, #4CAF50, #2196F3);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0.8rem;
                transition: all 0.3s ease;
            }
            
            .stButton button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            }
            
            /* Expander styling */
            .streamlit-expanderHeader {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                margin: 0.5rem 0;
            }
            
            /* Footer styling */
            .footer {
                margin-top: 2rem;
                padding-top: 1rem;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                text-align: center;
                color: #a0a0a0;
            }
        </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        # Professional logo and tagline
        st.sidebar.image("./screenshots/logo_image.png", width=240)
        st.markdown('<div style="color:#a0a0a0; font-size:1rem; text-align:center; margin-bottom:0.5rem;">Your Personal Memory Operating System</div>', unsafe_allow_html=True)
        st.markdown('<hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.1); margin: 1rem 0 1.5rem 0;" />', unsafe_allow_html=True)
        
        # Main navigation with enhanced styling
        st.markdown('<div style="color:#a0a0a0; font-size:0.95rem; margin-bottom:0.5rem;">Navigate your MemoBrain OS</div>', unsafe_allow_html=True)
        selected = option_menu(
            menu_title=None,
            options=["📊 Dashboard", "📂 My Files", "📦 Memory Manager", "🔍 Search", "📅 Timeline", "🔄 Relationships", "💬 Ask MemoBrain"],
            icons=["speedometer2", "folder", "box", "search", "calendar", "diagram-3", "chat"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {
                    "padding": "0!important",
                    "background-color": "transparent",
                    "border-radius": "0.5rem",
                },
                "icon": {"color": "#4CAF50", "font-size": "1.2rem"},
                "nav-link": {
                    "font-size": "1rem",
                    "text-align": "left",
                    "margin": "0.2rem 0",
                    "border-radius": "0.5rem",
                    "color": "#ffffff",
                    "padding": "0.8rem 1rem",
                },
                "nav-link-selected": {
                    "background": "linear-gradient(45deg, #4CAF50, #2196F3)",
                    "color": "white",
                },
            },
        )
        st.session_state["current_page"] = selected
        
        # Quick actions with enhanced styling
        st.markdown('<div class="section-header">⚡ Quick Actions</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#a0a0a0; font-size:0.95rem; margin-bottom:0.5rem;">Create new memories or search instantly.</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ New Memory", use_container_width=True):
                st.session_state["current_page"] = "📦 Memory Manager"
        with col2:
            if st.button("🔍 Quick Search", use_container_width=True):
                st.session_state["current_page"] = "🔍 Search"
        
        # Memory insights with enhanced styling
        st.markdown('<div class="section-header">📊 Memory Insights</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#a0a0a0; font-size:0.95rem; margin-bottom:0.5rem;">Track your memory usage and recent activity (last 7 days).</div>', unsafe_allow_html=True)
        memory_path = get_memory_index_path(user_id)
        if memory_path.exists():
            with open(memory_path, "r") as f:
                memories = json.load(f)
            
            total_memories = len(memories)
            recent_memories = sum(1 for m in memories 
                                if datetime.fromisoformat(m.get("temporal_metadata", {}).get("last_accessed", "2000-01-01")) 
                                > datetime.now() - timedelta(days=7))
            
            # Display metrics with enhanced styling
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{total_memories}</div>
                    <div class="metric-label">Total Memories</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{recent_memories}</div>
                    <div class="metric-label">Recent Activity (7d)</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Memory categories with enhanced styling
            categories = {}
            for memory in memories:
                cat = memory.get("category", "uncategorized")
                categories[cat] = categories.get(cat, 0) + 1
            
            st.markdown('<div class="section-header">Categories</div>', unsafe_allow_html=True)
            st.markdown('<div style="color:#a0a0a0; font-size:0.95rem; margin-bottom:0.5rem;">Distribution of your memories by category.</div>', unsafe_allow_html=True)
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                st.markdown(f"<div style='padding: 0.5rem; background: rgba(255,255,255,0.05); border-radius: 6px; margin: 0.3rem 0;'>{cat}: {count}</div>", unsafe_allow_html=True)
        else:
            st.info("No memories found. Start by creating some!")
        
        # System status with enhanced styling
        st.markdown('<div class="section-header">💻 System Status</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#a0a0a0; font-size:0.95rem; margin-bottom:0.5rem;">Account and sync status.</div>', unsafe_allow_html=True)
        st.markdown(f"<div style='padding: 0.5rem; background: rgba(255,255,255,0.05); border-radius: 6px; margin: 0.3rem 0;'>User ID: {user_id}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='padding: 0.5rem; background: rgba(255,255,255,0.05); border-radius: 6px; margin: 0.3rem 0;'>Last Sync: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>", unsafe_allow_html=True)
        
        # Quick filters with enhanced styling
        st.markdown('<div class="section-header">🔍 Quick Filters</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#a0a0a0; font-size:0.95rem; margin-bottom:0.5rem;">Filter your memories by tags or importance.</div>', unsafe_allow_html=True)
        if memory_path.exists():
            with open(memory_path, "r") as f:
                memories = json.load(f)
            
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
            
            importance_levels = ["Critical", "High", "Medium", "Low", "Minimal"]
            selected_importance = st.multiselect(
                "Filter by importance",
                importance_levels,
                key="sidebar_importance"
            )
            if selected_importance:
                st.session_state["selected_importance"] = selected_importance
        
        # User preferences with enhanced styling
        st.markdown('<div class="section-header">⚙️ Preferences</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#a0a0a0; font-size:0.95rem; margin-bottom:0.5rem;">Customize your experience.</div>', unsafe_allow_html=True)
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
        
        # Help and support with enhanced styling
        st.markdown('<div class="section-header">❓ Help & Support</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#a0a0a0; font-size:0.95rem; margin-bottom:0.5rem;">Find documentation or report issues.</div>', unsafe_allow_html=True)
        if st.button("📚 Documentation", use_container_width=True):
            st.markdown("[Open Documentation](https://github.com/mangesh-ux/multimodal-memory-assistant)")
        
        if st.button("🐛 Report Issue", use_container_width=True):
            st.markdown("[Create Issue](https://github.com/mangesh-ux/multimodal-memory-assistant/issues)")
        
        # Footer with enhanced styling
        st.markdown("""
            <div class="footer">
                MemoBrain OS v1.0<br>
                © 2025 Mangesh Gupta
            </div>
        """, unsafe_allow_html=True)

