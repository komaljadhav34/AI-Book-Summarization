from app import app, db, Book
from utils.learning import generate_mindmap, generate_quiz
import json

with app.app_context():
    book = Book.query.first()
    if not book:
        print("No books in db.")
    else:
        print(f"Testing generation for book '{book.title}' (ID: {book.id})")
        print(f"Raw text length: {len(book.raw_text)}")
        
        print("\n--- Testing Quiz Generation ---")
        try:
            quiz_json = generate_quiz(book.raw_text)
            quiz_data = json.loads(quiz_json)
            print(f"Generated {len(quiz_data)} questions.")
            if quiz_data:
                print(f"Sample Question: {quiz_data[0]['question']}")
        except Exception as e:
            print(f"Quiz Generation Error: {e}")

        print("\n--- Testing Mindmap Generation ---")
        try:
            if not book.summary:
                print("Book has no summary, generating a mock one...")
                book.summary = "This is a brief summary of the book text just for testing."
            
            mindmap = generate_mindmap(book.title, book.summary)
            print(f"Mindmap string length: {len(mindmap)}")
            print("Mindmap preview:")
            print("\n".join(mindmap.split("\n")[:5]))
            
        except Exception as e:
            print(f"Mindmap Generation Error: {e}")

        print("\n--- Checking current DB state ---")
        print(f"DB Quiz Data length: {len(str(book.quizzes))}")
        print(f"DB Mindmap Data length: {len(str(book.mindmap))}")
        
        # Now force save
        try:
            book.quizzes = quiz_json
            book.mindmap = mindmap
            db.session.commit()
            print("Successfully saved directly to DB.")
        except Exception as e:
            print(f"Error saving to DB: {e}")
