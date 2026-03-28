import os
import re
import pdfplumber
import threading
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Book, AccessLog

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "secret123"

# ---------------- CONFIG ----------------
UPLOAD_FOLDER = "uploads"
PASTE_FOLDER = "pasted_texts"
ALLOWED_EXTENSIONS = {"txt", "pdf"}
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///summarizer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PASTE_FOLDER, exist_ok=True)

# ---------------- INIT EXTENSIONS ----------------
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ---------------- HELPERS ----------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_pdf_text(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists')
            return redirect(url_for('signup'))

        # Simple logic for first admin
        role = 'user'
        if email in ['admin@admin.com', 'komaljadhav@gmail.com']:
            role = 'admin'

        new_user = User(username=username, email=email, password_hash=generate_password_hash(password), role=role)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('dashboard'))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('dashboard'))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/dashboard")
@login_required
def dashboard():
    user_books = Book.query.filter_by(user_id=current_user.id).all()
    book_count = len(user_books)
    total_words = sum(len(b.raw_text.split()) for b in user_books)
    return render_template("dashboard.html", name=current_user.username, 
                           book_count=book_count, total_words=total_words)


@app.route("/book/<int:book_id>")
@login_required
def book_details(book_id):
    book = db.get_or_404(Book, book_id)
    # RBAC: Allow if owner or admin
    if book.user_id != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to view this book.')
        return redirect(url_for('books'))
    print(f"DEBUG RENDER: Book {book.id}")
    print(f"DEBUG RENDER: Mindmap is {'None' if book.mindmap is None else f'Length {len(str(book.mindmap))}'}")
    print(f"DEBUG RENDER: Quizzes is {'None' if book.quizzes is None else f'Length {len(str(book.quizzes))}'}")
    return render_template("book_details.html", book=book)

@app.route("/books")
@login_required
def books():
    query = request.args.get("q", "").strip()
    if query:
        # Filter by title or author containing the query (case-insensitive)
        user_books = Book.query.filter(
            Book.user_id == current_user.id,
            (Book.title.ilike(f"%{query}%")) | (Book.author.ilike(f"%{query}%"))
        ).all()
    else:
        user_books = Book.query.filter_by(user_id=current_user.id).all()
    
    return render_template("books.html", books=user_books, query=query)

@app.route("/upload", methods=["GET"])
@login_required
def upload_page():
    return render_template("upload.html")

@app.route("/upload-text", methods=["POST"])
@login_required
def upload_text():
    file = request.files.get("file")
    text = request.form.get("text", "").strip()
    title = request.form.get("title", "Untitled")
    author = request.form.get("author", "Unknown")

    extracted_text = ""

    # ---- FILE UPLOAD ----
    if file and file.filename != "":
        if not allowed_file(file.filename):
            return jsonify({"error": "Only PDF or TXT allowed"}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        if filename.endswith(".txt"):
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                extracted_text = f.read()
        else:
            extracted_text = extract_pdf_text(filepath)

    # ---- PASTED TEXT ----
    elif text:
        extracted_text = text

    else:
        return jsonify({"error": "No input received"}), 400

    extracted_text = re.sub(r"\s+", " ", extracted_text).strip()

    new_book = Book(
        title=title,
        author=author,
        raw_text=extracted_text,
        user_id=current_user.id
    )
    db.session.add(new_book)
    db.session.commit()

    return jsonify({
        "status": "success",
        "length": len(extracted_text),
        "book_id": new_book.id,
        "preview": extracted_text[:300]
    })

@app.route("/book/<int:book_id>/summarize", methods=["POST"])
@login_required
def summarize_book(book_id):
    book = db.get_or_404(Book, book_id)
    if book.user_id != current_user.id and current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    if book.processing_status == 'processing':
        return jsonify({"error": "Already processing"}), 400

    max_len = int(request.form.get("max_length", 250))
    min_len = int(request.form.get("min_length", 50))

    book.processing_status = 'processing'
    book.error_message = None
    db.session.commit()

    # Start background thread
    def run_summarization(app_context, b_id, mx, mn):
        with app_context:
            try:
                from utils.summarizer import generate_summary, load_model
                from utils.learning import generate_mindmap, generate_quiz
                target_book = db.session.get(Book, b_id)
                load_model()
                summary = generate_summary(target_book.raw_text, max_length=mx, min_length=mn)
                target_book.summary = summary
                
                target_book.processing_status = 'completed'
                db.session.commit()
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                target_book = db.session.get(Book, b_id)
                target_book.processing_status = 'error'
                target_book.error_message = str(e)
                app.logger.error(f"Background summarization error: {error_details}")
                db.session.commit()

    thread = threading.Thread(target=run_summarization, args=(app.app_context(), book.id, max_len, min_len))
    thread.start()

    return jsonify({"status": "accepted", "message": "Summarization started in background"})

@app.route("/book/<int:book_id>/generate_mindmap", methods=["POST"])
@login_required
def api_generate_mindmap(book_id):
    print(f"DEBUG: api_generate_mindmap CALLED for book {book_id}")
    book = db.get_or_404(Book, book_id)
    if book.user_id != current_user.id and current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
        
    if not book.summary:
        return jsonify({"error": "Summary must be generated first"}), 400
        
    try:
        from utils.learning import generate_mindmap
        book.mindmap = generate_mindmap(book.title, book.summary)
        db.session.commit()
        return jsonify({"status": "success", "mindmap": book.mindmap})
    except Exception as e:
        app.logger.error(f"Error generating mindmap: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/book/<int:book_id>/generate_quiz", methods=["POST"])
@login_required
def api_generate_quiz(book_id):
    print(f"DEBUG: api_generate_quiz CALLED for book {book_id}")
    book = db.get_or_404(Book, book_id)
    if book.user_id != current_user.id and current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
        
    try:
        from utils.learning import generate_quiz
        book.quizzes = generate_quiz(book.raw_text)
        db.session.commit()
        return jsonify({"status": "success", "quizzes": book.quizzes})
    except Exception as e:
        app.logger.error(f"Error generating quiz: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/book/<int:book_id>/status")
@login_required
def book_status(book_id):
    book = db.get_or_404(Book, book_id)
    if book.user_id != current_user.id and current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    return jsonify({
        "status": book.processing_status,
        "summary": book.summary,
        "mindmap": book.mindmap,
        "quizzes": book.quizzes,
        "error": book.error_message
    })


@app.route("/book/delete/<int:book_id>", methods=["POST"])
@login_required
def delete_book(book_id):
    book = db.get_or_404(Book, book_id)
    # RBAC: Allow if owner or admin
    if book.user_id != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to delete this book.')
        return redirect(url_for('books'))
    
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted successfully.')
    return redirect(request.referrer or url_for('books'))

@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied.')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    books = Book.query.all()
    return render_template("admin_dashboard.html", users=users, books=books)

@app.route("/book/<int:book_id>/download/<format>")
@login_required
def download_summary(book_id, format):
    book = db.get_or_404(Book, book_id)
    if book.user_id != current_user.id and current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    if not book.summary:
        flash("No summary available to download.")
        return redirect(url_for('book_details', book_id=book_id))

    if format == 'txt':
        return jsonify({
            "filename": f"{secure_filename(book.title)}_summary.txt",
            "content": book.summary
        })
        # Note: Ideally send_file or Response with headers for download. 
        # But to keep it simple with existing imports or a quick fix:
        from flask import Response
        return Response(
            book.summary,
            mimetype="text/plain",
            headers={"Content-disposition": f"attachment; filename={secure_filename(book.title)}_summary.txt"}
        )

    elif format == 'pdf':
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import simpleSplit
            import io

            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            p.drawString(100, height - 50, f"Summary: {book.title}")
            p.drawString(100, height - 70, f"Author: {book.author}")
            p.line(100, height - 75, width - 100, height - 75)
            
            text_object = p.beginText(100, height - 100)
            text_object.setFont("Helvetica", 12)
            
            # Wrap text
            lines = simpleSplit(book.summary, "Helvetica", 12, width - 200)
            for line in lines:
                text_object.textLine(line)
                
            p.drawText(text_object)
            p.showPage()
            p.save()
            
            buffer.seek(0)
            from flask import send_file
            return send_file(
                buffer,
                as_attachment=True,
                download_name=f"{secure_filename(book.title)}_summary.pdf",
                mimetype='application/pdf'
            )
        except ImportError:
            flash("PDF generation library not installed.")
            return redirect(url_for('book_details', book_id=book_id))
        except Exception as e:
            flash(f"Error generating PDF: {str(e)}")
            return redirect(url_for('book_details', book_id=book_id))

    return redirect(url_for('book_details', book_id=book_id))

# ---------------- RUN ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # Pre-load the summarization model
        try:
            from utils.summarizer import load_model
            print("Pre-loading summarization model...")
            load_model()
            print("Model pre-loaded successfully.")
        except Exception as e:
            print(f"Warning: Failed to pre-load model on startup: {e}")
            
    app.run(debug=True, port=5001)
