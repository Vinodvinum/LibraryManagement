import streamlit as st
import sqlite3


# Database connection
def connect_db():
    conn = sqlite3.connect('library.db')
    return conn


# Create tables
def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    # Create Books table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            quantity INTEGER DEFAULT 1
        )
    """)

    # Create Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            user TEXT NOT NULL,
            borrow_date TEXT,
            return_date TEXT,
            FOREIGN KEY(book_id) REFERENCES books(id)
        )
    """)

    conn.commit()
    conn.close()


# Initialize database
create_tables()


# Streamlit app
st.title("Library Management System")
menu = st.sidebar.selectbox("Menu", ["Home", "Add Book", "View Books", "Borrow Book", "Return Book"])


# Home Page
if menu == "Home":
    st.header("Welcome to the Library Management System")
    st.write("""
        This system allows you to manage books, track borrowing and returning, 
        and maintain a proper library workflow.
    """)


# Add Book
if menu == "Add Book":
    st.header("Add a New Book")
    title = st.text_input("Book Title")
    author = st.text_input("Author")
    quantity = st.number_input("Quantity", min_value=1, step=1)

    if st.button("Add Book"):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO books (title, author, quantity) VALUES (?, ?, ?)", (title, author, quantity))
        conn.commit()
        conn.close()
        st.success(f"Book '{title}' by {author} added successfully!")


# View Books
if menu == "View Books":
    st.header("Available Books")
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    conn.close()

    if books:
        for book in books:
            st.write(f"ID: {book[0]}, Title: {book[1]}, Author: {book[2]}, Quantity: {book[3]}")
    else:
        st.write("No books available in the library.")


# Borrow Book
if menu == "Borrow Book":
    st.header("Borrow a Book")
    user = st.text_input("User Name")
    book_id = st.number_input("Book ID", min_value=1, step=1)

    if st.button("Borrow"):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT quantity FROM books WHERE id = ?", (book_id,))
        book = cursor.fetchone()

        if book and book[0] > 0:
            cursor.execute("INSERT INTO transactions (book_id, user, borrow_date) VALUES (?, ?, DATE('now'))", (book_id, user))
            cursor.execute("UPDATE books SET quantity = quantity - 1 WHERE id = ?", (book_id,))
            conn.commit()
            st.success("Book borrowed successfully!")
        else:
            st.error("Book not available.")
        conn.close()


# Return Book
if menu == "Return Book":
    st.header("Return a Book")
    user = st.text_input("User Name")
    book_id = st.number_input("Book ID", min_value=1, step=1)

    if st.button("Return"):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM transactions
            WHERE book_id = ? AND user = ? AND return_date IS NULL
        """, (book_id, user))
        transaction = cursor.fetchone()

        if transaction:
            cursor.execute("UPDATE transactions SET return_date = DATE('now') WHERE id = ?", (transaction[0],))
            cursor.execute("UPDATE books SET quantity = quantity + 1 WHERE id = ?", (book_id,))
            conn.commit()
            st.success("Book returned successfully!")
        else:
            st.error("No active borrow record found for this user and book.")
        conn.close()