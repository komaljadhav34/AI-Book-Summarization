import unittest
from unittest.mock import patch, MagicMock
from utils.preprocessing import clean_text
from utils.chunker import chunk_text
from utils.summarizer import generate_summary

class AITestCase(unittest.TestCase):
    
    def test_clean_text(self):
        raw = "  This   is  a   text.  \n\n"
        cleaned = clean_text(raw)
        self.assertEqual(cleaned, "This is a text.")
        
    def test_chunk_text(self):
        # Create a text with 20 words
        text = "word " * 20
        # Chunk with max 10 words, overlap 5
        chunks = chunk_text(text, max_tokens=10, overlap=5)
        
        self.assertTrue(len(chunks) > 1)
        # Check if chunks are strings
        self.assertIsInstance(chunks[0], str)
        
    @patch('utils.summarizer.load_model')
    def test_generate_summary_orchestration(self, mock_load_model):
        # Mock the pipeline behavior
        mock_pipeline = MagicMock()
        mock_pipeline.return_value = [{'summary_text': 'Summary of chunk.'}]
        mock_load_model.return_value = mock_pipeline
        
        text = "This is a long text that needs summarization. " * 10
        summary = generate_summary(text, max_length=50, min_length=10)
        
        self.assertIn('Summary of chunk.', summary)
        # Verify model was called
        mock_pipeline.assert_called()

if __name__ == '__main__':
    unittest.main()
