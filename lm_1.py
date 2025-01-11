import streamlit as st
import sqlite3

# Admin credentials (hardcoded for simplicity)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# User credentials (hardcoded for simplicity)
USER_USERNAME = "user"
USER_PASSWORD = "user123"

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

# Initialize the database
create_tables()

# Streamlit app
st.title("Library Management System")

# Starting page - Allow the user to choose Admin or User
def choose_role():
    role = st.selectbox("Please choose your role", ["Select Role", "Admin", "User"])
    return role

# Admin Login
def admin_login():
    admin_username = st.text_input("Admin Username", key="admin_username")
    admin_password = st.text_input("Admin Password", type="password", key="admin_password")
    if st.button("Login as Admin"):
        if admin_username == ADMIN_USERNAME and admin_password == ADMIN_PASSWORD:
            st.session_state['role'] = 'admin'
            return True
        else:
            st.error("Invalid Admin credentials!")
            return False
    return False

# User Login
def user_login():
    user_username = st.text_input("User Username", key="user_username")
    user_password = st.text_input("User Password", type="password", key="user_password")
    if st.button("Login as User"):
        if user_username == USER_USERNAME and user_password == USER_PASSWORD:
            st.session_state['role'] = 'user'
            return True
        else:
            st.error("Invalid User credentials!")
            return False
    return False

# Logout function
def logout():
    st.session_state.clear()  # Clear session to log out
    st.experimental_rerun()  # Reload the app

# Check the role from session_state or prompt for login
def check_role():
    if 'role' in st.session_state:
        return st.session_state['role']
    else:
        return None

# Admin Panel
def admin_panel():
    st.sidebar.button("Logout", on_click=logout)
    menu = st.sidebar.selectbox("Admin Menu", ["Home", "Add Book", "View Books", "View Transactions", "Remove Book"])
    st.subheader("Admin Panel")

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

    # View Transactions
    if menu == "View Transactions":
        st.header("All Transactions")
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions")
        transactions = cursor.fetchall()
        conn.close()

        if transactions:
            for transaction in transactions:
                st.write(f"Transaction ID: {transaction[0]}, Book ID: {transaction[1]}, User: {transaction[2]}, Borrow Date: {transaction[3]}, Return Date: {transaction[4]}")
        else:
            st.write("No transactions yet.")

    # Remove Book
    if menu == "Remove Book":
        st.header("Remove a Book")
        book_id = st.number_input("Book ID to Remove", min_value=1)

        if st.button("Remove Book"):
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
            conn.commit()
            conn.close()
            st.success(f"Book with ID {book_id} has been removed.")

# User Panel
def user_panel():
    st.sidebar.button("Logout", on_click=logout)
    menu = st.sidebar.selectbox("User Menu", ["Home", "View Books", "Borrow Book", "Return Book"])
    st.subheader("User Panel")

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
        user_return = st.text_input("User Name")
        book_id_return = st.number_input("Book ID", min_value=1, step=1)

        if st.button("Return"):
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM transactions
                WHERE book_id = ? AND user = ? AND return_date IS NULL
            """, (book_id_return, user_return))
            transaction = cursor.fetchone()

            if transaction:
                cursor.execute("UPDATE transactions SET return_date = DATE('now') WHERE id = ?", (transaction[0],))
                cursor.execute("UPDATE books SET quantity = quantity + 1 WHERE id = ?", (book_id_return,))
                conn.commit()
                st.success("Book returned successfully!")
            else:
                st.error("No active borrow record found for this user and book.")
            conn.close()

# Main logic
role = check_role()

if role is None:
    # Ask the user to select a role if not logged in
    role = choose_role()

if role == "Admin":
    if admin_login():
        admin_panel()
elif role == "User":
    if user_login():
        user_panel()
else:
    st.warning("Please select your role from the starting page.")