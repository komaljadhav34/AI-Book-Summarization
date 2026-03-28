import unittest
from unittest.mock import MagicMock
from utils.chunker import chunk_text

class TestTokenAwareChunking(unittest.TestCase):
    
    def test_chunk_text_with_tokenizer(self):
        # Mock tokenizer
        mock_tokenizer = MagicMock()
        # Mock encode to return a list of length equal to the number of words
        # This is a simplification but allows testing the logic
        mock_tokenizer.encode.side_effect = lambda text, **kwargs: [0] * len(text.split())
        
        text = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10"
        
        # Max 4 tokens, no overlap
        # Should result in: "word1 word2 word3 word4", "word5 word6 word7 word8", "word9 word10"
        chunks = chunk_text(text, max_tokens=4, overlap=0, tokenizer=mock_tokenizer)
        
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0], "word1 word2 word3 word4")
        self.assertEqual(chunks[1], "word5 word6 word7 word8")
        self.assertEqual(chunks[2], "word9 word10")
        
    def test_chunk_text_large_sentence(self):
        # Mock tokenizer
        mock_tokenizer = MagicMock()
        mock_tokenizer.encode.side_effect = lambda text, **kwargs: [0] * len(text.split())
        
        # One large sentence (no punctuation for simplicity in breaking)
        text = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10"
        
        # Max 3 tokens
        chunks = chunk_text(text, max_tokens=3, overlap=0, tokenizer=mock_tokenizer)
        
        self.assertEqual(len(chunks), 4)
        self.assertEqual(chunks[0], "word1 word2 word3")
        self.assertEqual(chunks[1], "word4 word5 word6")
        self.assertEqual(chunks[2], "word7 word8 word9")
        self.assertEqual(chunks[3], "word10")

if __name__ == '__main__':
    unittest.main()
