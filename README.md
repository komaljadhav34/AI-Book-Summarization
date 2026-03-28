# 📘 Intelligent Book Summarization System (BART-based)

A **Flask-based AI web application** that helps users quickly understand large books or documents by generating **concise summaries** using **NLP and transformer-based abstractive summarization (BART)**.

---

## ✨ Features

- **Book Upload & Text Input**
  - Upload `.txt` or `.pdf` files
  - Paste raw text directly into the application

- **AI-Powered Summarization**
  - Uses Hugging Face’s `sshleifer/distilbart-cnn-12-6` model
  - Automatically chunks large text and generates meaningful summaries

- **Clean Web Interface**
  - Simple and user-friendly UI built with HTML, CSS, and JavaScript

- **Fast Processing**
  - Efficient handling of large documents using text chunking

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask  
- **AI / NLP:** Hugging Face Transformers, PyTorch  
- **Frontend:** HTML, CSS, JavaScript  
- **File Processing:** PDF/Text parsing  

---

# How to Run the Project (Step-by-Step)

---
## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
git clone <repository-url>
cd bart_summarizer

### 2️⃣ Create a Virtual Environment
python -m venv venv

Activate it:

Windows
venv\Scripts\activate

Linux / macOS
source venv/bin/activate

### 3️⃣ Install Dependencies
pip install -r requirements.txt

⚠️ Note:
This project uses Hugging Face Transformers and PyTorch.
Downloading the DistilBART model may require ~300MB storage.

### 4️⃣ Run the Application
python app.py

### 5️⃣ Open in Browser
Visit:
http://127.0.0.1:5000/
