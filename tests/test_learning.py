import unittest
import json
from utils.learning import generate_mindmap, generate_quiz

class TestLearningFeatures(unittest.TestCase):
    
    def setUp(self):
        self.sample_text = """
        The Great Gatsby is a 1925 novel by American writer F. Scott Fitzgerald. 
        Set in the Jazz Age on Long Island, near New York City, the novel depicts 
        first-person narrator Nick Carraway's interactions with mysterious millionaire 
        Jay Gatsby and Gatsby's obsession to reunite with his former lover, Daisy Buchanan.
        """
        self.sample_summary = "A story about Jay Gatsby and his mysterious life in West Egg. It explores themes of wealth, class, and the American Dream."

    def test_generate_mindmap(self):
        mindmap = generate_mindmap("The Great Gatsby", self.sample_summary)
        self.assertIn("mindmap", mindmap)
        self.assertIn("Gatsby", mindmap)
        self.assertIn("root(", mindmap)

    def test_generate_quiz(self):
        quiz_json = generate_quiz(self.sample_text, num_questions=2)
        quiz = json.loads(quiz_json)
        
        self.assertIsInstance(quiz, list)
        if len(quiz) > 0:
            self.assertIn("question", quiz[0])
            self.assertIn("options", quiz[0])
            self.assertIn("correct", quiz[0])
            self.assertEqual(len(quiz[0]["options"]), 4)

if __name__ == '__main__':
    unittest.main()
