import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import jwt

class LibraryAdminApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Management System - Admin")
        self.token = None
        
        # Login Frame
        self.login_frame = ttk.LabelFrame(root, text="Admin Login")
        self.login_frame.pack(padx=10, pady=10, fill="x")
        
        ttk.Label(self.login_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5)
        self.username_entry = ttk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.login_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = ttk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        self.login_btn = ttk.Button(self.login_frame, text="Login", command=self.login)
        self.login_btn.grid(row=2, column=0, columnspan=2, pady=5)
        
        # Main Frame (hidden initially)
        self.main_frame = ttk.Frame(root)
        
        # Borrow Stats
        self.stats_frame = ttk.LabelFrame(self.main_frame, text="Borrowing Statistics")
        self.stats_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.stats_tree = ttk.Treeview(self.stats_frame, columns=('title', 'borrowers'), show='headings')
        self.stats_tree.heading('title', text='Book Title')
        self.stats_tree.heading('borrowers', text='Borrowers Count')
        self.stats_tree.pack(fill="both", expand=True)
        
        self.refresh_btn = ttk.Button(self.main_frame, text="Refresh", command=self.load_stats)
        self.refresh_btn.pack(pady=5)
        
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        try:
            response = requests.post(
                "http://auth_service:5000/login",
                auth=(username, password)
            )
        except requests.exceptions.RequestException as e:
                messagebox.showerror("Error", f"Request failed: {str(e)}")
                return
    
        if response.status_code == 200:
                self.token = response.json().get('token')
                user_info = jwt.decode(self.token, options={"verify_signature": False})
                
                if user_info.get('role') == 'admin':
                    self.login_frame.pack_forget()
                    self.main_frame.pack(fill="both", expand=True)
                    self.load_stats()
                else:
                    messagebox.showerror("Error", "Admin access required!")
        else:
                messagebox.showerror("Error", "Invalid credentials!")
    
    def load_stats(self):
        if not self.token:
            return
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get("http://book_service:5001/borrow_status", headers=headers)
            
            if response.status_code == 200:
                # Clear existing data
                for item in self.stats_tree.get_children():
                    self.stats_tree.delete(item)
                
                # Add new data
                stats = response.json()
                for stat in stats:
                    self.stats_tree.insert('', 'end', values=(stat['title'], stat['borrowers_count']))
            else:
                messagebox.showerror("Error", f"Failed to load stats: {response.text}")
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("600x400")
    app = LibraryAdminApp(root)
    root.mainloop()