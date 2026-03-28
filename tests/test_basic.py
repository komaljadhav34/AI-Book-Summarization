import unittest
import os
from app import app, db, User, Book

class SummarizerTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False 
        
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def register(self, username, email, password):
        return self.app.post('/signup', data=dict(
            username=username,
            email=email,
            password=password
        ), follow_redirects=True)

    def login(self, email, password):
        return self.app.post('/login', data=dict(
            email=email,
            password=password
        ), follow_redirects=True)

    def test_auth(self):
        # Test Registration
        rv = self.register('testuser', 'test@example.com', 'password123')
        self.assertIn(b'Welcome, testuser!', rv.data)
        
        # Test Logout
        rv = self.app.get('/logout', follow_redirects=True)
        self.assertIn(b'Login', rv.data)
        
        # Test Login
        rv = self.login('test@example.com', 'password123')
        self.assertIn(b'Welcome, testuser!', rv.data)

    def test_book_upload_and_search(self):
        self.register('testuser', 'test@example.com', 'password123')
        
        # Test Upload (Paste Text)
        rv = self.app.post('/upload-text', data=dict(
            title='Test Book',
            author='Test Author',
            text='This is a sample text content for testing purposes.'
        ), follow_redirects=True)
        
        # Check database
        with app.app_context():
            book = Book.query.first()
            self.assertIsNotNone(book)
            self.assertEqual(book.title, 'Test Book')
            self.assertEqual(book.author, 'Test Author')

        # Test List Books
        rv = self.app.get('/books')
        self.assertIn(b'Test Book', rv.data)
        
        # Test Search
        rv = self.app.get('/books?q=Test')
        self.assertIn(b'Test Book', rv.data)
        
        rv = self.app.get('/books?q=NonExistent')
        self.assertNotIn(b'Test Book', rv.data)

    def test_delete_book(self):
        self.register('testuser', 'test@example.com', 'password123')
        
        # Upload
        self.app.post('/upload-text', data=dict(
            title='Delete Me',
            author='Author',
            text='To be deleted.'
        ), follow_redirects=True)
        
        with app.app_context():
            book = Book.query.filter_by(title='Delete Me').first()
            book_id = book.id
            
        # Delete
        rv = self.app.post(f'/book/delete/{book_id}', follow_redirects=True)
        self.assertIn(b'Book deleted successfully.', rv.data)
        
        with app.app_context():
            book = Book.query.get(book_id)
            self.assertIsNone(book)

if __name__ == '__main__':
    unittest.main()
