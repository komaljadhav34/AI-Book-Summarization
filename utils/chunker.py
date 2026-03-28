import re
from .preprocessing import clean_text

def chunk_text(text, max_tokens=None, overlap=50, tokenizer=None):
    """
    Splits text into overlapping chunks, attempting to break at sentence boundaries.
    If a tokenizer is provided, use it for accurate token counting.
    """
    if max_tokens is None:
        max_tokens = 400 if tokenizer is None else 800

    text = clean_text(text)
    
    # Split text into sentences using simple regex
    sentence_endings = re.compile(r'(?<=[.!?])\s+')
    sentences = sentence_endings.split(text)
    
    chunks = []
    current_chunk = []
    current_count = 0
    
    def get_count(t):
        if tokenizer:
            return len(tokenizer.encode(t, add_special_tokens=False))
        return len(t.split())

    for sentence in sentences:
        sentence_count = get_count(sentence)
        
        # If a single sentence is longer than max_tokens, we have to break it
        if sentence_count > max_tokens:
            # If we had something in the current chunk, push it
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_count = 0
            
            # Break large sentence into smaller pieces
            words = sentence.split()
            temp_words = []
            temp_count = 0
            for word in words:
                word_with_space = word + " "
                word_count = get_count(word_with_space)
                
                if temp_count + word_count > max_tokens:
                    if temp_words:
                        chunks.append(" ".join(temp_words))
                    temp_words = [word]
                    temp_count = word_count
                else:
                    temp_words.append(word)
                    temp_count += word_count
            
            if temp_words:
                current_chunk = temp_words
                current_count = temp_count
            continue

        # If adding this sentence exceeds max_tokens, start a new chunk
        if current_count + sentence_count > max_tokens:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            
            # Start new chunk
            current_chunk = [sentence]
            current_count = sentence_count
        else:
            current_chunk.append(sentence)
            current_count += sentence_count
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks
