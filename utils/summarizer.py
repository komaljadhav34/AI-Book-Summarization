import os
import requests
import time
import logging
import re
from .chunker import chunk_text

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# We use the free Hugging Face Inference API for BART CNN
HF_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

def get_api_key():
    return os.environ.get("HF_API_KEY", "")

def load_model():
    """
    Deprecated for API usage. We keep the signature so app.py doesn't break.
    """
    logger.info("Using Hugging Face Inference API. No local model loaded into RAM.")
    pass

def query_hf_api(payload, retries=5):
    api_key = get_api_key()
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        
    for attempt in range(retries):
        try:
            response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
            
            # API indicates the model is currently loading on their end
            if response.status_code == 503:
                data = response.json()
                wait_time = data.get("estimated_time", 15.0)
                logger.warning(f"Model is loading on HF Server. Waiting {wait_time}s...")
                time.sleep(max(wait_time, 5))
                continue
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API Request failed: {e}. Attempt {attempt + 1}/{retries}")
            if attempt == retries - 1:
                raise Exception(f"Hugging Face API Error: {str(e)}")
            time.sleep(3)
        
    raise Exception("Hugging Face API failed after multiple retries.")

def generate_summary(text, max_length=150, min_length=40):
    if not text:
        return ""

    if not get_api_key():
        logger.warning("HF_API_KEY is not set. Inference API may rate limit or fail. Please set it as an Environment Variable in Render.")

    logger.info(f"Starting API summarization. Input length: {len(text)} characters.")
    
    # We pass tokenizer=None so chunker uses simple word splitting. Max 600 words per chunk for BART.
    chunks = chunk_text(text, max_tokens=600, overlap=100)
    logger.info(f"Text split into {len(chunks)} chunks.")
    
    chunk_summaries = []
    
    for i, chunk in enumerate(chunks):
        chunk_word_count = len(chunk.split())
        logger.info(f"Processing chunk {i+1}/{len(chunks)} ({chunk_word_count} words)...")
        
        eff_max = min(max_length, max(60, int(chunk_word_count * 0.4)))
        eff_min = min(min_length, max(30, int(eff_max * 0.5)))
        
        payload = {
            "inputs": chunk,
            "parameters": {
                "max_length": eff_max,
                "min_length": eff_min,
                "do_sample": False
            }
        }
        res = query_hf_api(payload)
        
        if res and isinstance(res, list):
            if 'summary_text' in res[0]:
                chunk_summaries.append(res[0]['summary_text'])
            elif 'generated_text' in res[0]:
                chunk_summaries.append(res[0]['generated_text'])
                
        logger.info(f"Successfully processed chunk {i+1}/{len(chunks)}")
        
    if not chunk_summaries:
        raise Exception("Summarization failed to produce any output. (Did you set HF_API_KEY?)")

    combined_summary = " ".join(chunk_summaries)
    combined_words = len(combined_summary.split())
    
    if len(chunk_summaries) > 3 or combined_words > max_length * 1.5:
        logger.info(f"Performing second pass summarization on {combined_words} words.")
        payload = {
            "inputs": combined_summary[:4000],
            "parameters": {
                "max_length": max_length,
                "min_length": min_length,
                "do_sample": False
            }
        }
        final_res = query_hf_api(payload)
        if final_res and isinstance(final_res, list):
            if 'summary_text' in final_res[0]:
                return final_res[0]['summary_text']
            elif 'generated_text' in final_res[0]:
                return final_res[0]['generated_text']
    
    return combined_summary

def extract_topic(text, max_tokens=8):
    if not text or len(text.strip()) < 10:
        return "Key Concept"
        
    try:
        payload = {
            "inputs": text[:500],
            "parameters": {
                "max_length": max_tokens,
                "min_length": 3,
                "do_sample": False
            }
        }
        res = query_hf_api(payload)
        topic = None
        if res and isinstance(res, list):
            if 'summary_text' in res[0]:
                topic = res[0]['summary_text'].strip()
            elif 'generated_text' in res[0]:
                topic = res[0]['generated_text'].strip()
                
        if topic:
            topic = re.sub(r'[.!?,;:]+$', '', topic)
            return topic.title()
    except Exception as e:
        logger.error(f"Error extracting topic: {e}")
    
    return "Thematic Concept"
