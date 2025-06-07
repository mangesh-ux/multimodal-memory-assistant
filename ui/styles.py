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
