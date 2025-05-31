from datetime import datetime

def format_context_with_metadata(chunks: list[dict]) -> str:
    context = ""
    for c in chunks:
        date_str = c.get("date_uploaded", "")[:10]
        try:
            pretty_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%b %d, %Y")
        except:
            pretty_date = date_str or "Unknown Date"
        tag_str = ", ".join(c.get("tags", [])) or "None"

        category_icons = {
            "health": "🩺",
            "career": "💼",
            "finance": "💰",
            "meeting": "📅",
            "thought": "💭",
            "idea": "💡",
            "personal": "👤"
        }

        category = c.get("category", "Uncategorized").lower()
        icon = category_icons.get(category, "📁")

        context += (
            f"📅 Date added to memory: {pretty_date}\n"
            f"📝 Title: {c.get('title', 'Untitled')}\n"
            f"🏷️ Tags: {tag_str}\n"
            f"📁 Source: {c.get('source_file', '')}\n"
            f"{icon} Category: {category.capitalize()}\n"
            f"🗒 Notes: {c.get('notes', 'No notes provided.')}\n\n"
            f"{c['text'].strip()}\n"
            f"{'-'*60}\n\n"
        )
    return context
