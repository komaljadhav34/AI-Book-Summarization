"""
Emergency migration: adds ALL columns that any version of models.py may require.
Safe to run multiple times - it skips columns that already exist.
"""
import sqlite3

def migrate():
    conn = sqlite3.connect('instance/summarizer.db')
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(book)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Current columns: {columns}")
    
    # All columns that ANY version of the model may need
    all_needed = {
        # Current model columns
        'mindmap': 'TEXT',
        'quizzes': 'TEXT',
        'processing_status': "VARCHAR(20) DEFAULT 'none'",
        'processing_started_at': 'FLOAT',
        'total_words': 'INTEGER DEFAULT 0',
        'error_message': 'TEXT',
        # Old model columns (from previous app versions)
        'quiz_data': 'TEXT',
        'mindmap_data': 'TEXT',
        'concept_graph_data': 'TEXT',
        'summary_tree_data': 'TEXT',
        'qa_builder_data': 'TEXT',
        'learning_path_data': 'TEXT',
        'smart_notes_data': 'TEXT',
    }
    
    for col_name, col_def in all_needed.items():
        if col_name not in columns:
            print(f"  + Adding '{col_name}'...")
            cursor.execute(f"ALTER TABLE book ADD COLUMN {col_name} {col_def}")
        else:
            print(f"  [ok] '{col_name}' exists.")
    
    conn.commit()
    conn.close()
    print("\nMigration complete!")

if __name__ == "__main__":
    migrate()
