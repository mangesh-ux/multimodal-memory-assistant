# styles.py

# Light and dark mode color values
LIGHT_CARD_BG = "#f7f8fa"
DARK_CARD_BG = "#1e1e1e"
LIGHT_TEXT_COLOR = "#333"
DARK_TEXT_COLOR = "#eee"

# Injects CSS variables for dark mode detection
CSS_VARIABLES = f"""
<style>
:root {{
    --card-bg: {LIGHT_CARD_BG};
    --text-color: {LIGHT_TEXT_COLOR};
}}
@media (prefers-color-scheme: dark) {{
    :root {{
        --card-bg: {DARK_CARD_BG};
        --text-color: {DARK_TEXT_COLOR};
    }}
}}
</style>
"""

# Legacy constants — now referencing CSS variables
CARD_BG = "var(--card-bg)"
TEXT_COLOR = "var(--text-color)"
TAG_COLOR = "#ffb703"
PADDING = "1rem"
RADIUS = "8px"
BORDER = "1px solid #ccc"

CHAT_CSS = """
<style>
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.chat-bubble {
    max-width: 85%;
    padding: 0.8rem 1rem;
    border-radius: 1rem;
    line-height: 1.4;
    word-wrap: break-word;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.chat-user {
    align-self: flex-end;
    background-color: #1e88e5;
    color: white;
    border-bottom-right-radius: 0;
}

.chat-assistant {
    align-self: flex-start;
    background-color: var(--card-bg);
    color: var(--text-color);
    border-bottom-left-radius: 0;
    border: 1px solid #ddd;
}
</style>
"""

__all__ = ["CARD_BG", "TEXT_COLOR", "LIGHT_CARD_BG", "DARK_CARD_BG", "LIGHT_TEXT_COLOR", 
           "DARK_TEXT_COLOR", "CSS_VARIABLES", "CARD_BG", "TEXT_COLOR", "TAG_COLOR", "CHAT_CSS",
           "PADDING", "RADIUS", "BORDER"]
