import re
 
def slugify(text: str) -> str:
    # A simple slugify function, can be enhanced
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
    return text 