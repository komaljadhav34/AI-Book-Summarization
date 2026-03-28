from app import app, db, Book
from utils.summarizer import generate_summary, load_model
from utils.learning import generate_mindmap, generate_quiz
import traceback

with app.app_context():
    book = Book.query.order_by(Book.id.desc()).first()
    print(f"Testing full background pipeline for Book ID: {book.id}, Title: {book.title}")
    
    try:
        print("1. Loading model...")
        load_model()
        
        print(f"2. Generating summary (raw text length: {len(book.raw_text)})...")
        # Just use what's already there to speed up if possible, or re-run
        summary = book.summary
        if not summary:
            summary = generate_summary(book.raw_text, max_length=250, min_length=50)
            book.summary = summary
        print(f"Summary length: {len(summary)}")
        
        print("3. Generating learning features...")
        try:
            print("  -> Mindmap")
            mindmap = generate_mindmap(book.title, summary)
            print(f"     Mindmap length: {len(mindmap) if mindmap else 'None'}")
            book.mindmap = mindmap
            
            print("  -> Quizzes")
            quizzes = generate_quiz(book.raw_text)
            print(f"     Quizzes length: {len(quizzes) if quizzes else 'None'}")
            book.quizzes = quizzes
            
        except Exception as le:
            print(f"CRITICAL ERROR in learning features: {le}")
            print(traceback.format_exc())
            
        print("4. Committing to DB...")
        db.session.commit()
        print("Done!")
        
    except Exception as e:
        print(f"Pipeline error: {e}")
        print(traceback.format_exc())
