from transformers import pipeline
from .chunker import chunk_text
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to cache the model pipeline
summarizer_pipeline = None

def load_model():
    """
    Loads the summarization pipeline. 
    Using 'sshleifer/distilbart-cnn-12-6' for a good balance of speed and quality.
    """
    global summarizer_pipeline
    if summarizer_pipeline is None:
        logger.info("Loading summarization model...")
        try:
            # Transformers 5.x unified task name to text-generation
            summarizer_pipeline = pipeline("text-generation", model="sshleifer/distilbart-cnn-12-6")
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise e
    return summarizer_pipeline

def generate_summary(text, max_length=150, min_length=40):
    """
    Orchestrates the summarization process with hierarchical support for large texts.
    """
    if not text:
        logger.warning("Empty text provided for summarization.")
        return ""

    logger.info(f"Starting summarization. Input length: {len(text)} characters.")
    summarizer = load_model()
    # Get tokenizer from pipeline
    tokenizer = summarizer.tokenizer
    
    # 1. First Pass: Chunk and Summarize
    # 800 tokens is a safe limit for BART (max 1024)
    chunks = chunk_text(text, max_tokens=800, overlap=100, tokenizer=tokenizer)
    logger.info(f"Text split into {len(chunks)} chunks.")
    
    chunk_summaries = []
    
    for i, chunk in enumerate(chunks):
        try:
            chunk_word_count = len(chunk.split())
            logger.info(f"Processing chunk {i+1}/{len(chunks)} ({chunk_word_count} words)...")
            
            # Ensure min_length/max_length are sensible for the chunk size
            # For hierarchical, we want concise summaries per chunk
            eff_max = min(max_length, max(60, int(chunk_word_count * 0.4)))
            eff_min = min(min_length, max(30, int(eff_max * 0.5)))
            
            res = summarizer(chunk, max_length=eff_max, min_length=eff_min, do_sample=False)
            if res:
                if 'summary_text' in res[0]:
                    chunk_summaries.append(res[0]['summary_text'])
                elif 'generated_text' in res[0]:
                    chunk_summaries.append(res[0]['generated_text'])
            
            logger.info(f"Successfully processed chunk {i+1}/{len(chunks)}")
        except Exception as e:
            logger.error(f"Error summarising chunk {i+1}: {str(e)}")
            
    if not chunk_summaries:
        raise Exception("Summarization failed to produce any output.")

    # 2. Second Pass: Hierarchical if needed
    # If we have many chunks, the concatenated summary might still be too long or disjointed.
    # BART model usually has a max position embedding of 1024 tokens (~700-800 words).
    combined_summary = " ".join(chunk_summaries)
    combined_words = len(combined_summary.split())
    
    if len(chunk_summaries) > 3 or combined_words > max_length * 1.5:
        logger.info(f"Performing second pass summarization as combined summary is {combined_words} words.")
        
        # If the combined summary is still very large, we might need a third pass, 
        # but for most use cases one hierarchical step is enough.
        # We'll treat the combined summaries as a new text and summarize it.
        # We use a larger max_length for the final pass if desired.
        try:
            # We don't want to over-summarize if the user wanted a long summary
            # Adjust final pass limits based on user preference
            final_res = summarizer(combined_summary[:4000], # BART limit safe window
                                 max_length=max_length, 
                                 min_length=min_length, 
                                 do_sample=False)
            if final_res:
                if 'summary_text' in final_res[0]:
                    final_summary = final_res[0]['summary_text']
                    logger.info("Hierarchical pass successful.")
                    return final_summary
                elif 'generated_text' in final_res[0]:
                    final_summary = final_res[0]['generated_text']
                    logger.info("Hierarchical pass successful.")
                    return final_summary
        except Exception as e:
            logger.error(f"Error in hierarchical pass: {e}. Falling back to combined chunks.")
    
    return combined_summary

def extract_topic(text, max_tokens=8):
    """
    Uses the summarization model to extract a very short, punchy topic/title from a text block.
    """
    if not text or len(text.strip()) < 10:
        return "Key Concept"
        
    try:
        summarizer = load_model()
        # We use very aggressive compression for branch titles
        res = summarizer(text[:500], max_length=max_tokens, min_length=3, do_sample=False)
        if res:
            topic = None
            if 'summary_text' in res[0]:
                topic = res[0]['summary_text'].strip()
            elif 'generated_text' in res[0]:
                topic = res[0]['generated_text'].strip()
                
            if topic:
                # Clean up trailing punctuation
                topic = re.sub(r'[.!?,;:]+$', '', topic)
                # Apply Title Case for professional look
                return topic.title()
    except Exception as e:
        logger.error(f"Error extracting topic: {e}")
    
    return "Thematic Concept"
