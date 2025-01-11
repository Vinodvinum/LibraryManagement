import streamlit as st
import sqlite3
from PIL import Image


# Database connection
def connect_db():
    conn = sqlite3.connect('library.db')
    return conn


# Create tables
def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    # Create Books table with additional columns for ISBN, shelf location, and image
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT,
            shelf_location TEXT,
            quantity INTEGER DEFAULT 1,
            image BLOB
        )
    """)

    # Create Users table for student and staff management
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_type TEXT NOT NULL CHECK(user_type IN ('student', 'staff'))
        )
    """)

    # Create Transactions table for tracking borrow/return
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            user_id INTEGER,
            borrow_date TEXT,
            return_date TEXT,
            FOREIGN KEY(book_id) REFERENCES books(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# Initialize database
create_tables()


# Streamlit app
st.title("Library Management System")
menu = st.sidebar.selectbox("Menu", ["Home", "Add Book", "View Books", "Borrow Book", "Return Book", "Add User", "View Users"])


# Home Page
if menu == "Home":
    st.header("Welcome to the Library Management System")
    st.write("""
        This system allows you to manage books, track borrowing and returning, 
        and maintain a proper library workflow. Explore the various functionalities using the sidebar.
    """)


# Add Book
if menu == "Add Book":
    st.header("Add a New Book")
    title = st.text_input("Book Title")
    author = st.text_input("Author")
    isbn = st.text_input("ISBN")
    shelf_location = st.text_input("Shelf Location")
    quantity = st.number_input("Quantity", min_value=1, step=1)
    book_image = st.file_uploader("Upload Book Cover Image", type=["jpg", "jpeg", "png"])

    if st.button("Add Book"):
        if book_image is not None:
            image = Image.open(book_image)
            image = image.convert("RGB")
            image = image.save(f"{title}_cover.jpg")
            with open(f"{title}_cover.jpg", "rb") as img_file:
                img_data = img_file.read()
        else:
            img_data = None

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO books (title, author, isbn, shelf_location, quantity, image)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, author, isbn, shelf_location, quantity, img_data))
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
            st.write(f"ID: {book[0]}, Title: {book[1]}, Author: {book[2]}, ISBN: {book[3]}, Shelf: {book[4]}, Quantity: {book[5]}")
            if book[6]:
                image = Image.open(book[6])
                st.image(image, caption=book[1], use_column_width=True)
    else:
        st.write("No books available in the library.")


# Borrow Book
if menu == "Borrow Book":
    st.header("Borrow a Book")
    user_name = st.text_input("User Name")
    user_type = st.selectbox("User Type", ["student", "staff"])
    book_id = st.number_input("Book ID", min_value=1, step=1)

    if st.button("Borrow"):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT quantity FROM books WHERE id = ?", (book_id,))
        book = cursor.fetchone()

        cursor.execute("SELECT id FROM users WHERE name = ? AND user_type = ?", (user_name, user_type))
        user = cursor.fetchone()

        if book and book[0] > 0 and user:
            cursor.execute("INSERT INTO transactions (book_id, user_id, borrow_date) VALUES (?, ?, DATE('now'))", (book_id, user[0]))
            cursor.execute("UPDATE books SET quantity = quantity - 1 WHERE id = ?", (book_id,))
            conn.commit()
            st.success("Book borrowed successfully!")
        else:
            st.error("Book not available or user not found.")
        conn.close()


# Return Book
if menu == "Return Book":
    st.header("Return a Book")
    user_name = st.text_input("User Name")
    book_id = st.number_input("Book ID", min_value=1, step=1)

    if st.button("Return"):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE name = ?", (user_name,))
        user = cursor.fetchone()

        cursor.execute("""
            SELECT id FROM transactions
            WHERE book_id = ? AND user_id = ? AND return_date IS NULL
        """, (book_id, user[0]))
        transaction = cursor.fetchone()

        if transaction:
            cursor.execute("UPDATE transactions SET return_date = DATE('now') WHERE id = ?", (transaction[0],))
            cursor.execute("UPDATE books SET quantity = quantity + 1 WHERE id = ?", (book_id,))
            conn.commit()
            st.success("Book returned successfully!")
        else:
            st.error("No active borrow record found for this user and book.")
        conn.close()


# Add User (for Students and Staff)
if menu == "Add User":
    st.header("Add a New User")
    user_name = st.text_input("User Name")
    user_type = st.selectbox("User Type", ["student", "staff"])

    if st.button("Add User"):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, user_type) VALUES (?, ?)", (user_name, user_type))
        conn.commit()
        conn.close()
        st.success(f"User '{user_name}' added successfully!")


# View Users
if menu == "View Users":
    st.header("View Users")
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()

    if users:
        for user in users:
            st.write(f"ID: {user[0]}, Name: {user[1]}, Type: {user[2]}")
    else:
        st.write("No users found.")