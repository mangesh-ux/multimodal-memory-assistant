# styles.py
LIGHT_CARD_BG = "#f7f8fa"
DARK_CARD_BG = "#1e1e1e"
LIGHT_TEXT_COLOR = "#333"
DARK_TEXT_COLOR = "#eee"

# CSS variables
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
