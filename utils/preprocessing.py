import re

def clean_text(text):
    """
    Cleans raw text by removing excessive whitespace and invisible characters.
    """
    if not text:
        return ""
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove some control characters but keep punctuation
    # (Basic implementation, can be expanded)
    text = text.strip()
    
    return text

def count_words(text):
    """
    Returns a rough word count.
    """
    if not text:
        return 0
    return len(text.split())
