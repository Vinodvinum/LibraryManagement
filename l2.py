import streamlit as st
import sqlite3
from PIL import Image
import base64
from datetime import datetime, timedelta

# Set the page configuration
st.set_page_config(page_title="Shree Cauvery Educational Library Management System", layout="wide")

# Function to set background image
def set_background(image_path):
    with open(image_path, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode()
    background_css = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{encoded_string}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(background_css, unsafe_allow_html=True)


# Database connection
def connect_db():
    conn = sqlite3.connect('library.db')
    return conn


# Modify database schema to add overdue_days and fine_amount to transactions table
def modify_schema():
    conn = connect_db()
    cursor = conn.cursor()

    # Check if the column already exists and only add if necessary
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN overdue_days INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE transactions ADD COLUMN fine_amount REAL DEFAULT 0.0")
        conn.commit()
    except sqlite3.OperationalError as e:
        # If columns already exist, this will be caught, so we can skip the error
        print("Columns already exist or other error:", e)

    conn.close()


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
            overdue_days INTEGER DEFAULT 0,
            fine_amount REAL DEFAULT 0.0,
            FOREIGN KEY(book_id) REFERENCES books(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# Initialize database
create_tables()
modify_schema()

# Streamlit app
st.title("Shree Cauvery Educational Library Management System")

# Set the background image
set_background(r"bg1.jpg")
menu = st.sidebar.selectbox("Menu",
                            ["Home", "Add Book", "View Books", "Search Book", "Borrow Book", "Return Book", "Add User",
                             "View Users", "Reports"])

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
            st.write(
                f"ID: {book[0]}, Title: {book[1]}, Author: {book[2]}, ISBN: {book[3]}, Shelf: {book[4]}, Quantity: {book[5]}")
            if book[6]:
                image = Image.open(book[6])
                st.image(image, caption=book[1], use_column_width=True)
    else:
        st.write("No books available in the library.")

# Search Book
if menu == "Search Book":
    st.header("Search for a Book")
    search_title = st.text_input("Search by Title")
    search_author = st.text_input("Search by Author")

    conn = connect_db()
    cursor = conn.cursor()
    query = "SELECT * FROM books WHERE title LIKE ? AND author LIKE ?"
    cursor.execute(query, ('%' + search_title + '%', '%' + search_author + '%'))
    books = cursor.fetchall()
    conn.close()

    if books:
        for book in books:
            st.write(
                f"ID: {book[0]}, Title: {book[1]}, Author: {book[2]}, ISBN: {book[3]}, Shelf: {book[4]}, Quantity: {book[5]}")
    else:
        st.write("No books found matching the search criteria.")

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
            cursor.execute("INSERT INTO transactions (book_id, user_id, borrow_date) VALUES (?, ?, DATE('now'))",
                           (book_id, user[0]))
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
            SELECT id, borrow_date FROM transactions
            WHERE book_id = ? AND user_id = ? AND return_date IS NULL
        """, (book_id, user[0]))
        transaction = cursor.fetchone()

        if transaction:
            # Calculate overdue days and fines
            borrow_date = datetime.strptime(transaction[1], "%Y-%m-%d")
            due_date = borrow_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
                days=14)  # assuming 14 days to return
            overdue_days = (datetime.now() - due_date).days
            fine_amount = max(0, overdue_days * 1)  # Assuming $1 fine per day

            # Update transaction and book data
            cursor.execute(
                "UPDATE transactions SET return_date = DATE('now'), overdue_days = ?, fine_amount = ? WHERE id = ?",
                (overdue_days, fine_amount, transaction[0]))
            cursor.execute("UPDATE books SET quantity = quantity + 1 WHERE id = ?", (book_id,))
            conn.commit()

            st.success(f"Book returned successfully! Fine: ${fine_amount}")
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

# Reports
if menu == "Reports":
    st.header("Library Reports")

    # Overdue Books Report
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.title, u.name, t.borrow_date, t.return_date, t.overdue_days, t.fine_amount 
        FROM transactions t 
        JOIN books b ON t.book_id = b.id 
        JOIN users u ON t.user_id = u.id 
        WHERE t.overdue_days > 0
    """)
    overdue_books = cursor.fetchall()
    conn.close()

    if overdue_books:
        st.subheader("Overdue Books")
        for record in overdue_books:
            st.write(
                f"Book: {record[0]}, User: {record[1]}, Borrow Date: {record[2]}, Return Date: {record[3]}, Overdue Days: {record[4]}, Fine: ${record[5]}")
    else:
        st.write("No overdue books at the moment.")


st.markdown("---")
st.markdown(
    '<div style="text-align: center; font-size: small;">💡 Created by Kiran N with ❤ using Streamlit </div>',
    unsafe_allow_html=True,
)