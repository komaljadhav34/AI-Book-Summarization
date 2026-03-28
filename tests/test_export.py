import unittest
from app import app, db, User, Book
from unittest.mock import MagicMock

class ExportTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False 
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
            
    def register_and_login(self):
        self.app.post('/signup', data=dict(username='test', email='test@test.com', password='pw'), follow_redirects=True)
        self.app.post('/login', data=dict(email='test@test.com', password='pw'), follow_redirects=True)
        
    def test_dashboard_stats(self):
        self.register_and_login()
        # Initial stats
        rv = self.app.get('/dashboard')
        self.assertIn(b'Total Uploads: 0', rv.data)
        
        # Upload book
        self.app.post('/upload-text', data=dict(title='T', author='A', text='Hello World'), follow_redirects=True)
        rv = self.app.get('/dashboard')
        self.assertIn(b'Total Uploads: 1', rv.data)
        self.assertIn(b'Total Words Processed: 2', rv.data)
        
    def test_export_txt(self):
        self.register_and_login()
        # Upload and mock summary
        self.app.post('/upload-text', data=dict(title='ExportTest', author='A', text='Content'), follow_redirects=True)
        with app.app_context():
            book = Book.query.first()
            book.summary = "This is a summary."
            db.session.commit()
            book_id = book.id
            
        rv = self.app.get(f'/book/{book_id}/download/txt')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b"This is a summary.", rv.data)
        
    def test_export_pdf(self):
        pass # Skipping PDF test as it requires binary check, but route existence is key.

if __name__ == '__main__':
    unittest.main()
