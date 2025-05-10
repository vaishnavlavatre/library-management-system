import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
from datetime import datetime
import jwt

class LibraryStudentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Management System - Student")
        self.token = None
        self.user_id = None

        self.login_frame = ttk.LabelFrame(root, text="Student Login")
        self.login_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(self.login_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5)
        self.username_entry = ttk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.login_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = ttk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        self.login_btn = ttk.Button(self.login_frame, text="Login", command=self.login)
        self.login_btn.grid(row=2, column=0, columnspan=2, pady=5)

        ttk.Button(self.login_frame, text="Register", command=self.show_register).grid(row=3, column=0, columnspan=2, pady=5)

        self.register_frame = ttk.LabelFrame(root, text="Student Registration")

        ttk.Label(self.register_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5)
        self.reg_username = ttk.Entry(self.register_frame)
        self.reg_username.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.register_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5)
        self.reg_password = ttk.Entry(self.register_frame, show="*")
        self.reg_password.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(self.register_frame, text="Register", command=self.register).grid(row=2, column=0, columnspan=2, pady=5)
        ttk.Button(self.register_frame, text="Back to Login", command=self.show_login).grid(row=3, column=0, columnspan=2, pady=5)

        self.main_frame = ttk.Frame(root)

        self.books_frame = ttk.LabelFrame(self.main_frame, text="Available Books")
        self.books_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.books_tree = ttk.Treeview(self.books_frame, columns=('id','title', 'author', 'quantity'), show='headings')
        self.books_tree.heading('id', text='Book ID')
        self.books_tree.heading('title', text='Title')
        self.books_tree.heading('author', text='Author')
        self.books_tree.heading('quantity', text='Available')
        self.books_tree.pack(fill="both", expand=True)
        self.books_tree.bind('<<TreeviewSelect>>', self.on_book_select)

        self.action_frame = ttk.Frame(self.main_frame)
        self.action_frame.pack(padx=10, pady=5, fill="x")

        ttk.Label(self.action_frame, text="Book ID:").pack(side="left", padx=5)
        self.book_id_entry = ttk.Entry(self.action_frame, width=10)
        self.book_id_entry.pack(side="left", padx=5)

        self.borrow_btn = ttk.Button(self.action_frame, text="Borrow", command=self.borrow_book)
        self.borrow_btn.pack(side="left", padx=5)

        self.return_btn = ttk.Button(self.action_frame, text="Return", command=self.return_book)
        self.return_btn.pack(side="left", padx=5)

        self.notif_frame = ttk.LabelFrame(self.main_frame, text="Notifications")
        self.notif_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.notif_text = tk.Text(self.notif_frame, height=5, state="disabled")
        self.notif_text.pack(fill="both", expand=True)

        self.refresh_btn = ttk.Button(self.main_frame, text="Refresh", command=self.refresh_data)
        self.refresh_btn.pack(pady=5)

    def show_register(self):
        self.login_frame.pack_forget()
        self.register_frame.pack(padx=10, pady=10, fill="x")

    def show_login(self):
        self.register_frame.pack_forget()
        self.login_frame.pack(padx=10, pady=10, fill="x")

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        try:
            response = requests.post("http://auth_service:5000/login", auth=(username, password))

            if response.status_code == 200:
                self.token = response.json().get('token')
                user_info = jwt.decode(self.token, options={"verify_signature": False})
                self.user_id = user_info.get('id')

                self.login_frame.pack_forget()
                self.main_frame.pack(fill="both", expand=True)
                self.refresh_data()
            else:
                messagebox.showerror("Error", "Invalid credentials!")
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")

    def register(self):
        username = self.reg_username.get()
        password = self.reg_password.get()

        try:
            response = requests.post("http://auth_service:5000/register",
                                     json={'username': username, 'password': password, 'role': 'student'})

            if response.status_code == 201:
                messagebox.showinfo("Success", "Registration successful! Please login.")
                self.show_login()
            else:
                messagebox.showerror("Error", response.json().get('message', 'Registration failed!'))
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")

    def refresh_data(self):
        self.load_books()
        self.load_notifications()

    def load_books(self):
        if not self.token:
            return

        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get("http://book_service:5001/books", headers=headers)

            if response.status_code == 200:
                for item in self.books_tree.get_children():
                    self.books_tree.delete(item)

                books = response.json()
                for book in books:
                    self.books_tree.insert('', 'end', values=(book['id'], book['title'], book['author'], book['quantity']))
            else:
                messagebox.showerror("Error", f"Failed to load books: {response.text}")
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")

    def load_notifications(self):
        if not self.token or not self.user_id:
            return

        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get(f"http://notification_service:5002/notifications/{self.user_id}", headers=headers)

            if response.status_code == 200:
                self.notif_text.config(state="normal")
                self.notif_text.delete(1.0, tk.END)

                notifications = response.json()
                for notif in notifications:
                    created_at = notif.get('created_at', 'Unknown Time')
                    message = notif.get('message', 'No message available')
                    self.notif_text.insert(tk.END, f"[{created_at}] {message}\n")

                self.notif_text.config(state="disabled")
            else:
                messagebox.showerror("Error", f"Failed to load notifications: {response.text}")
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")

    def borrow_book(self):
        if not self.token or not self.user_id:
            messagebox.showerror("Error", "User not logged in properly.")
            return

        book_id = self.book_id_entry.get().strip()
        print(f"[DEBUG] Borrow clicked. Book ID: '{book_id}', User ID: '{self.user_id}'")

        if not book_id:
            messagebox.showerror("Error", "Please enter a book ID!")
            return

        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            payload = {'book_id': book_id, 'user_id': self.user_id}
            response = requests.post("http://book_service:5001/borrow", json=payload, headers=headers)

            if response.status_code == 200:
                messagebox.showinfo("Success", "Book borrowed successfully!")
                self.refresh_data()
            else:
                messagebox.showerror("Error", response.json().get('message', 'Borrow failed!'))
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")

    def return_book(self):
        if not self.token or not self.user_id:
            messagebox.showerror("Error", "User not logged in properly.")
            return

        book_id = self.book_id_entry.get().strip()
        print(f"[DEBUG] Return clicked. Book ID: '{book_id}', User ID: '{self.user_id}'")

        if not book_id:
            messagebox.showerror("Error", "Please enter a book ID!")
            return

        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            payload = {'book_id': book_id, 'user_id': self.user_id}
            response = requests.post("http://book_service:5001/return", json=payload, headers=headers)

            if response.status_code == 200:
                messagebox.showinfo("Success", "Book returned successfully!")
                self.refresh_data()
            else:
                messagebox.showerror("Error", response.json().get('message', 'Return failed!'))
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")

    def on_book_select(self, event):
        selected_item = self.books_tree.selection()
        if selected_item:
            book_id = self.books_tree.item(selected_item)['values'][0]
            self.book_id_entry.delete(0, tk.END)
            self.book_id_entry.insert(0, str(book_id))

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    app = LibraryStudentApp(root)
    root.mainloop()
