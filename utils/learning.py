import json
import re
import random
import logging

logger = logging.getLogger(__name__)

def _sentences(text, min_words=6):
    """Split text into sentences with at least min_words words."""
    if not text: return []
    raw = re.split(r'[.!?](?:\s+|$)', text.strip())
    return [s.strip() for s in raw if len(s.split()) >= min_words]

def _key_phrases(text, n=15):
    """Advanced phrase extraction looking for thematic concepts."""
    if not text: return []
    
    # 1. Capitalized word sequences (2-3 words)
    titles = re.findall(r'\b[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){1,2}\b', text)
    
    # 2. Bigrams of medium words
    bigrams = re.findall(r'\b([a-zA-Z]{5,})\s+([a-zA-Z]{5,})\b', text)
    bigram_list = [f"{a} {b}" for a, b in bigrams]
    
    # 3. Frequent solitary concepts
    words = re.findall(r'\b[a-zA-Z]{7,}\b', text)
    freq = {}
    stop = {'summary', 'chapter', 'section', 'author'}
    for w in words:
        lw = w.lower()
        if lw not in stop:
            freq[lw] = freq.get(lw, 0) + 1
    
    sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    frequent = [w.capitalize() for w, f in sorted_freq[:10]]

    pool = titles + bigram_list + frequent
    
    unique = []
    seen = set()
    for p in pool:
        norm = p.lower().strip()
        if norm in seen: continue
        
        # Avoid overlapping substrings
        if any(norm in u.lower() or u.lower() in norm for u in unique):
            continue
            
        unique.append(p)
        seen.add(norm)
            
    return unique[:n]

def generate_quiz(text, num_questions=5):
    """Generates a JSON string representing a quiz."""
    if not isinstance(text, str) or not text:
        return json.dumps([])
    
    sents = _sentences(text, min_words=10)
    phrases = [str(p) for p in _key_phrases(text, n=30) if isinstance(p, str)]
    questions = []

    # Simple shuffle to get variety
    random.shuffle(sents)

    for sent in sents:
        if len(questions) >= num_questions: break
        words = sent.split()
        
        # Try to find a good word to blank out
        potential_targets = [w.strip('.,!?;()"\':') for w in words if len(w) > 6]
        if not potential_targets: continue
        
        target = random.choice(potential_targets)
        
        # Escape special chars for regex
        pattern = re.escape(target)
        blanked = re.sub(pattern, "_______", sent, count=1)
        
        opts = [target]
        distractor_pool = [p for p in phrases if p.lower() != target.lower() and len(p.split()) == 1]
        
        # Add more words from text if needed
        if len(distractor_pool) < 10:
            text_words = list(set(re.findall(r'\b[a-zA-Z]{6,}\b', text)))
            distractor_pool.extend([w for w in text_words if w.lower() != target.lower()])
            
        # Hard thematic fallbacks
        fallbacks = ["process", "analysis", "content", "standard", "concept", "approach", "essential"]
        distractor_pool.extend([f for f in fallbacks if f.lower() != target.lower()])
        
        random.shuffle(distractor_pool)
        
        for d in distractor_pool:
            if len(opts) >= 4: break
            if d.lower() not in [op.lower() for op in opts]:
                opts.append(d)
        
        random.shuffle(opts)
        questions.append({
            "id": len(questions) + 1,
            "question": f"Fill in the blank: \"{blanked}\"",
            "options": opts,
            "correct": opts.index(target)
        })

    return json.dumps(questions)

def generate_mindmap(title, summary):
    """
    Generates a more meaningful Mermaid mindmap string by:
    1. Splitting summary into thematic blocks.
    2. Extracting a core topic for each block using BART.
    3. Identifying supporting points for each topic.
    """
    if not isinstance(summary, str) or not summary:
        return f'mindmap\n  root(("{re.sub(r"[^a-zA-Z0-9 ]", "", str(title))[:40]}"))'

    from .summarizer import extract_topic

    def sanitize(txt):
        # Mermaid is sensitive to special characters
        s = re.sub(r'["\[\]{}():]', '', str(txt)).strip()
        return s[:300] # Increased for full sentences

    clean_title = sanitize(title[:50])
    if len(clean_title) < 3: clean_title = "Executive Summary"
    
    # Split summary into roughly thematic chunks (by paragraph or sentence groups)
    sentences = _sentences(summary, min_words=5)
    if not sentences:
        return f'mindmap\n  root({clean_title})\n    (Summary too short for mindmap)'

    # Group into 2-4 thematic blocks
    if len(sentences) <= 2:
        blocks = sentences
    else:
        num_blocks = min(4, max(2, len(sentences) // 2))
        chunk_size = max(1, len(sentences) // num_blocks)
        blocks = [" ".join(sentences[i:i + chunk_size]) for i in range(0, len(sentences), chunk_size)]
    
    lines = ['mindmap', f'  root( {clean_title} )']
    used_subpoints = set()
    used_branch_titles = set()
    
    # Helper to count keyword overlap for semantic relevance
    def get_relevance_score(text, keywords):
        text_words = set(re.findall(r'\b\w{4,}\b', text.lower()))
        overlap = text_words.intersection(keywords)
        return len(overlap)

    for block in blocks[:5]: # Allow up to 5 main branches
        # Try to extract a topical concept
        ai_topic = extract_topic(block)
        phrases = _key_phrases(block, n=5)
        
        # Select the best title: AI topic or the most representative phrase
        # We want the one that appears or relates most to the sentences in this block
        sentences_in_block = _sentences(block, min_words=5)
        if not sentences_in_block: continue
        
        candidate_titles = [ai_topic] + phrases
        best_title = ai_topic
        max_overlap = -1
        
        # Keywords for the whole block to find the "center"
        block_keywords = set()
        for s in sentences_in_block:
            block_keywords.update(re.findall(r'\b\w{5,}\b', s.lower()))
            
        for cand in candidate_titles:
            cand_words = set(re.findall(r'\b\w{4,}\b', cand.lower()))
            overlap = len(cand_words.intersection(block_keywords))
            # Bonus for noun-phrase like structure (Title Case, no verbs)
            if not any(cand.lower().startswith(v) for v in {'is', 'are', 'was', 'were', 'use', 'take', 'consider'}):
                overlap += 1
            
            if overlap > max_overlap:
                max_overlap = overlap
                best_title = cand
        
        topic = best_title
        
        # Final trim for UI aesthetics - max 5 words for branch titles
        topic_words = topic.split()
        if len(topic_words) > 0:
            # Filter out common leading verbs/prepositions
            stop_starts = {'consider', 'using', 'by', 'adjusting', 'to', 'for', 'with', 'from', 'in', 'on', 'at', 'is', 'are', 'was', 'were', 'the', 'and', 'use', 'take', 'creating', 'how', 'about', 'some', 'is', 'a', 'the', 'type', 'of'}
            
            while len(topic_words) > 1 and topic_words[0].lower().strip('.,') in stop_starts:
                topic_words = topic_words[1:]
            
            if len(topic_words) > 4:
                topic_words = topic_words[:4]

            # Trim trailing definitional fragments like "... Is A" or "... Is The"
            while len(topic_words) > 2 and topic_words[-1].lower().strip('.,') in {'is', 'are', 'was', 'were', 'a', 'the', 'of', 'and', 'type', 'to', 'for'}:
                topic_words = topic_words[:-1]
            
            topic = " ".join(topic_words).title()
        
        topic_clean = sanitize(topic)
        
        # Deduplication check
        topic_norm = topic_clean.lower().strip()
        is_duplicate = any(topic_norm in existing or existing in topic_norm for existing in used_branch_titles)
        
        if len(topic_clean) < 3 or is_duplicate: continue
        
        # Keywords for relevance scoring (nouns from the topic)
        topic_keywords = {w.lower() for w in topic_words if len(w) > 3}
        
        lines.append(f'    {topic_clean}')
        used_branch_titles.add(topic_norm)
        
        # Get sub-points (leaf nodes)
        block_sentences = _sentences(block, min_words=5)
        
        # Score sentences by relevance to the branch topic
        scored_sentences = []
        for s in block_sentences:
            s_clean = sanitize(s)
            is_exactly_topic = s_clean.lower().strip() == topic.lower().strip()
            if is_exactly_topic or s_clean[:30] in used_subpoints: continue
            
            score = get_relevance_score(s_clean, topic_keywords)
            scored_sentences.append((score, s_clean))
            
        # Prioritize higher relevance scores
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        
        sub_points = []
        for score, s_clean in scored_sentences:
            # Truncate and clean up fragment starts
            words = s_clean.split()
            
            # Avoid sentence continuations if possible
            if s_clean.lower().startswith(topic.lower()):
                topic_len = len(topic.split())
                remaining = words[topic_len:]
                stop_starts = {'is', 'are', 'was', 'were', 'has', 'have', 'had', 'the', 'a', 'an', 'and', 'but', 'or', 'in', 'of'}
                while remaining and remaining[0].lower().strip('.,') in stop_starts:
                    remaining = remaining[1:]
                display_text = " ".join(remaining) if len(remaining) > 2 else s_clean
            else:
                display_text = s_clean
            
            display_text = display_text.strip().capitalize()
            
            if display_text and len(display_text) > 4:
                sub_points.append(f'      ("{display_text}")')
                used_subpoints.add(s_clean[:30])
                if len(sub_points) >= 2: break
            
        # Fallback if filtering left no sub-points
        if not sub_points and scored_sentences:
            for score, s_clean in scored_sentences[:2]:
                text = s_clean.strip().capitalize()
                sub_points.append(f'      ("{text}")')
        
        lines.extend(sub_points)

    # Final validation - if BART failed or blocks were weird
    if len(lines) < 3:
        lines.append('    Main Themes')
        for s in sentences[:3]:
            lines.append(f'      ("{sanitize(s)}")')

    return '\n'.join(lines)
