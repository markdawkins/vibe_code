import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import csv
import os
from tkinter import filedialog

class StudyTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Daily Study Tracker")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Define subjects
        self.subjects = [
            "Cisco DevNet Associate (200-901 DEVASC)",
            "AWS Certified Machine Learning Engineer (MLA-C01)", 
            "Cisco Encore Enterprise (350-401) ",
            "F5 Application Delivery Fundamentals (Exam 101)",
            "Infoblox Admin"
        ]
        
        # Status options
        self.status_options = ["Not Started", "In Progress", "Completed", "On Hold"]
        
        # Store entry widgets
        self.entries = {}
        
        self.setup_gui()
        
    def setup_gui(self):
        # Title
        title_label = tk.Label(self.root, text="Daily Study Progress Tracker", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Date display
        self.date_label = tk.Label(self.root, text=f"Date: {datetime.now().strftime('%Y-%m-%d')}",
                                   font=("Arial", 10))
        self.date_label.pack(pady=5)
        
        # Create main frame for subjects
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas and scrollbar for scrollable area
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create headers
        headers = ["Subject", "Task Name", "Status", "Comments"]
        for col, header in enumerate(headers):
            label = tk.Label(scrollable_frame, text=header, font=("Arial", 11, "bold"),
                           bg="lightgray", padx=10, pady=5, relief=tk.RAISED)
            label.grid(row=0, column=col, sticky="nsew", padx=2, pady=2)
        
        # Create input fields for each subject
        for idx, subject in enumerate(self.subjects, start=1):
            # Subject label (non-editable)
            subject_label = tk.Label(scrollable_frame, text=subject, font=("Arial", 10),
                                    bg="lightblue", padx=10, pady=5, relief=tk.RIDGE)
            subject_label.grid(row=idx, column=0, sticky="nsew", padx=2, pady=2)
            
            # Task name entry
            task_entry = tk.Entry(scrollable_frame, width=30, font=("Arial", 10))
            task_entry.grid(row=idx, column=1, sticky="nsew", padx=2, pady=2)
            
            # Status combobox
            status_combo = ttk.Combobox(scrollable_frame, values=self.status_options, 
                                        width=15, state="readonly")
            status_combo.set(self.status_options[0])  # Default: "Not Started"
            status_combo.grid(row=idx, column=2, sticky="nsew", padx=2, pady=2)
            
            # Comments text widget (with scrollbar)
            comments_frame = ttk.Frame(scrollable_frame)
            comments_frame.grid(row=idx, column=3, sticky="nsew", padx=2, pady=2)
            
            comments_text = tk.Text(comments_frame, height=3, width=30, font=("Arial", 9))
            comments_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            comments_scroll = ttk.Scrollbar(comments_frame, orient="vertical", 
                                           command=comments_text.yview)
            comments_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            comments_text.configure(yscrollcommand=comments_scroll.set)
            
            # Store entries for this subject
            self.entries[subject] = {
                'task_entry': task_entry,
                'status_combo': status_combo,
                'comments_text': comments_text
            }
        
        # Configure grid weights
        scrollable_frame.grid_columnconfigure(0, weight=1)
        scrollable_frame.grid_columnconfigure(1, weight=2)
        scrollable_frame.grid_columnconfigure(2, weight=1)
        scrollable_frame.grid_columnconfigure(3, weight=3)
        
        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button frame
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)
        
        # Save button
        save_btn = tk.Button(button_frame, text="Save to CSV", command=self.save_to_csv,
                            bg="green", fg="white", font=("Arial", 11, "bold"),
                            padx=20, pady=5)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        # Clear button
        clear_btn = tk.Button(button_frame, text="Clear All", command=self.clear_all,
                             bg="orange", fg="white", font=("Arial", 11, "bold"),
                             padx=20, pady=5)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Load button
        load_btn = tk.Button(button_frame, text="Load Today's Data", command=self.load_todays_data,
                            bg="blue", fg="white", font=("Arial", 11, "bold"),
                            padx=20, pady=5)
        load_btn.pack(side=tk.LEFT, padx=5)
        
        # Export button
        export_btn = tk.Button(button_frame, text="Export All Data", command=self.export_all_data,
                              bg="purple", fg="white", font=("Arial", 11, "bold"),
                              padx=20, pady=5)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_bar = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def get_current_data(self):
        """Get current data from all entries"""
        current_date = datetime.now().strftime('%Y-%m-%d')
        data = []
        
        for subject in self.subjects:
            entries = self.entries[subject]
            task_name = entries['task_entry'].get().strip()
            status = entries['status_combo'].get()
            comments = entries['comments_text'].get("1.0", tk.END).strip()
            
            # Only include if task name is provided
            if task_name:
                data.append({
                    'Date': current_date,
                    'Subject': subject,
                    'Task_Name': task_name,
                    'Status': status,
                    'Comments': comments
                })
        
        return data
    
    def save_to_csv(self):
        """Save current data to CSV file"""
        data = self.get_current_data()
        
        if not data:
            messagebox.showwarning("No Data", "Please enter at least one task before saving!")
            return
        
        filename = f"study_progress_{datetime.now().strftime('%Y%m%d')}.csv"
        
        try:
            # Check if file exists to determine if we need to write headers
            file_exists = os.path.isfile(filename)
            
            with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Date', 'Subject', 'Task_Name', 'Status', 'Comments']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerows(data)
            
            messagebox.showinfo("Success", f"Data saved successfully to {filename}")
            self.status_bar.config(text=f"Data saved to {filename}")
            self.clear_all()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {str(e)}")
            self.status_bar.config(text="Error saving data")
    
    def clear_all(self):
        """Clear all input fields"""
        for subject in self.subjects:
            entries = self.entries[subject]
            entries['task_entry'].delete(0, tk.END)
            entries['status_combo'].set(self.status_options[0])
            entries['comments_text'].delete("1.0", tk.END)
        
        self.status_bar.config(text="All fields cleared")
    
    def load_todays_data(self):
        """Load today's data from CSV file if it exists"""
        filename = f"study_progress_{datetime.now().strftime('%Y%m%d')}.csv"
        
        if not os.path.isfile(filename):
            messagebox.showinfo("No Data", f"No data found for today ({filename})")
            return
        
        try:
            # Clear current data first
            self.clear_all()
            
            with open(filename, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    subject = row['Subject']
                    if subject in self.entries:
                        self.entries[subject]['task_entry'].insert(0, row['Task_Name'])
                        self.entries[subject]['status_combo'].set(row['Status'])
                        self.entries[subject]['comments_text'].insert("1.0", row['Comments'])
            
            messagebox.showinfo("Success", f"Loaded today's data from {filename}")
            self.status_bar.config(text=f"Loaded data from {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
            self.status_bar.config(text="Error loading data")
    
    def export_all_data(self):
        """Export all data from all CSV files to a single file"""
        csv_files = [f for f in os.listdir('.') if f.startswith('study_progress_') and f.endswith('.csv')]
        
        if not csv_files:
            messagebox.showwarning("No Data", "No study progress CSV files found!")
            return
        
        # Ask for export filename
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export All Data As"
        )
        
        if not filename:
            return
        
        try:
            all_data = []
            for csv_file in sorted(csv_files):
                with open(csv_file, 'r', encoding='utf-8') as infile:
                    reader = csv.DictReader(infile)
                    for row in reader:
                        all_data.append(row)
            
            # Write all data to export file
            if all_data:
                with open(filename, 'w', newline='', encoding='utf-8') as outfile:
                    fieldnames = ['Date', 'Subject', 'Task_Name', 'Status', 'Comments']
                    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(all_data)
                
                messagebox.showinfo("Success", f"Exported {len(all_data)} records to {filename}")
                self.status_bar.config(text=f"Exported {len(all_data)} records")
            else:
                messagebox.showwarning("No Data", "No data found in CSV files!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")
            self.status_bar.config(text="Error exporting data")

def main():
    root = tk.Tk()
    app = StudyTracker(root)
    root.mainloop()

if __name__ == "__main__":
    main()
