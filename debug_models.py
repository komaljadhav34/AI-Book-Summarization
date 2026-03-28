from app import app, db, Book
import inspect

with app.app_context():
    print("--- Book Model Inspection ---")
    print(f"Book Class: {Book}")
    print(f"File: {inspect.getfile(Book)}")
    
    print("\nColumns in Book.__table__:")
    for col in Book.__table__.columns:
        print(f"  - {col.name}")
        
    print("\nAttempting to query one Book:")
    try:
        book = Book.query.first()
        print(f"Successfully fetched book: {book}")
    except Exception as e:
        print(f"Query failed: {e}")
