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
        self.root.geometry("1050x750")
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
        
        # Target Reached options
        self.target_options = ["Yes", "No"]
        
        # Study Hours options
        self.hours_options = ["1 hour", "2 hours", "3 hours"]
        
        # Course Completion % options
        self.completion_options = ["25%", "50%", "75%", "100%"]
        
        # Exam Scheduled options
        self.exam_options = ["Yes", "No"]
        
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
        headers = ["Subject", "Study Task Details", "Status", "Target Reached", 
                  "Study Hours", "Course Completion %", "Exam Scheduled", "Comments"]
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
            
            # Study Task Details entry
            task_entry = tk.Entry(scrollable_frame, width=22, font=("Arial", 10))
            task_entry.grid(row=idx, column=1, sticky="nsew", padx=2, pady=2)
            
            # Status combobox
            status_combo = ttk.Combobox(scrollable_frame, values=self.status_options, 
                                        width=13, state="readonly")
            status_combo.set(self.status_options[0])  # Default: "Not Started"
            status_combo.grid(row=idx, column=2, sticky="nsew", padx=2, pady=2)
            
            # Target Reached combobox
            target_combo = ttk.Combobox(scrollable_frame, values=self.target_options, 
                                       width=12, state="readonly")
            target_combo.set(self.target_options[1])  # Default: "No"
            target_combo.grid(row=idx, column=3, sticky="nsew", padx=2, pady=2)
            
            # Study Hours combobox
            hours_combo = ttk.Combobox(scrollable_frame, values=self.hours_options, 
                                      width=10, state="readonly")
            hours_combo.set(self.hours_options[0])  # Default: "1 hour"
            hours_combo.grid(row=idx, column=4, sticky="nsew", padx=2, pady=2)
            
            # Course Completion % combobox (new field)
            completion_combo = ttk.Combobox(scrollable_frame, values=self.completion_options, 
                                           width=15, state="readonly")
            completion_combo.set(self.completion_options[0])  # Default: "25%"
            completion_combo.grid(row=idx, column=5, sticky="nsew", padx=2, pady=2)
            
            # Exam Scheduled combobox (new field)
            exam_combo = ttk.Combobox(scrollable_frame, values=self.exam_options, 
                                     width=12, state="readonly")
            exam_combo.set(self.exam_options[1])  # Default: "No"
            exam_combo.grid(row=idx, column=6, sticky="nsew", padx=2, pady=2)
            
            # Comments text widget (with scrollbar)
            comments_frame = ttk.Frame(scrollable_frame)
            comments_frame.grid(row=idx, column=7, sticky="nsew", padx=2, pady=2)
            
            comments_text = tk.Text(comments_frame, height=3, width=22, font=("Arial", 9))
            comments_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            comments_scroll = ttk.Scrollbar(comments_frame, orient="vertical", 
                                           command=comments_text.yview)
            comments_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            comments_text.configure(yscrollcommand=comments_scroll.set)
            
            # Store entries for this subject
            self.entries[subject] = {
                'task_entry': task_entry,
                'status_combo': status_combo,
                'target_combo': target_combo,
                'hours_combo': hours_combo,
                'completion_combo': completion_combo,
                'exam_combo': exam_combo,
                'comments_text': comments_text
            }
        
        # Configure grid weights
        scrollable_frame.grid_columnconfigure(0, weight=1)
        scrollable_frame.grid_columnconfigure(1, weight=2)
        scrollable_frame.grid_columnconfigure(2, weight=1)
        scrollable_frame.grid_columnconfigure(3, weight=1)
        scrollable_frame.grid_columnconfigure(4, weight=1)
        scrollable_frame.grid_columnconfigure(5, weight=1)
        scrollable_frame.grid_columnconfigure(6, weight=1)
        scrollable_frame.grid_columnconfigure(7, weight=2)
        
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
        
        # Summary button
        summary_btn = tk.Button(button_frame, text="Show Summary", command=self.show_summary,
                               bg="brown", fg="white", font=("Arial", 11, "bold"),
                               padx=20, pady=5)
        summary_btn.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_bar = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def get_current_data(self):
        """Get current data from all entries"""
        current_date = datetime.now().strftime('%Y-%m-%d')
        data = []
        
        for subject in self.subjects:
            entries = self.entries[subject]
            task_details = entries['task_entry'].get().strip()
            status = entries['status_combo'].get()
            target_reached = entries['target_combo'].get()
            study_hours = entries['hours_combo'].get()
            course_completion = entries['completion_combo'].get()
            exam_scheduled = entries['exam_combo'].get()
            comments = entries['comments_text'].get("1.0", tk.END).strip()
            
            # Only include if study task details are provided
            if task_details:
                data.append({
                    'Date': current_date,
                    'Subject': subject,
                    'Study_Task_Details': task_details,
                    'Status': status,
                    'Target_Reached': target_reached,
                    'Study_Hours': study_hours,
                    'Course_Completion_Percent': course_completion,
                    'Exam_Scheduled': exam_scheduled,
                    'Comments': comments
                })
        
        return data
    
    def save_to_csv(self):
        """Save current data to CSV file"""
        data = self.get_current_data()
        
        if not data:
            messagebox.showwarning("No Data", "Please enter at least one study task before saving!")
            return
        
        filename = f"study_progress_{datetime.now().strftime('%Y%m%d')}.csv"
        
        try:
            # Check if file exists to determine if we need to write headers
            file_exists = os.path.isfile(filename)
            
            with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Date', 'Subject', 'Study_Task_Details', 'Status', 
                             'Target_Reached', 'Study_Hours', 'Course_Completion_Percent',
                             'Exam_Scheduled', 'Comments']
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
            entries['status_combo'].set(self.status_options[0])      # "Not Started"
            entries['target_combo'].set(self.target_options[1])      # "No"
            entries['hours_combo'].set(self.hours_options[0])        # "1 hour"
            entries['completion_combo'].set(self.completion_options[0])  # "25%"
            entries['exam_combo'].set(self.exam_options[1])          # "No"
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
                        self.entries[subject]['task_entry'].insert(0, row['Study_Task_Details'])
                        self.entries[subject]['status_combo'].set(row['Status'])
                        self.entries[subject]['target_combo'].set(row['Target_Reached'])
                        self.entries[subject]['hours_combo'].set(row['Study_Hours'])
                        self.entries[subject]['completion_combo'].set(row['Course_Completion_Percent'])
                        self.entries[subject]['exam_combo'].set(row['Exam_Scheduled'])
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
                    fieldnames = ['Date', 'Subject', 'Study_Task_Details', 'Status', 
                                 'Target_Reached', 'Study_Hours', 'Course_Completion_Percent',
                                 'Exam_Scheduled', 'Comments']
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
    
    def show_summary(self):
        """Show summary statistics for today's data"""
        data = self.get_current_data()
        
        if not data:
            messagebox.showinfo("No Data", "No data entered for today yet!")
            return
        
        # Calculate statistics
        total_tasks = len(data)
        completed_tasks = sum(1 for item in data if item['Status'] == 'Completed')
        targets_reached = sum(1 for item in data if item['Target_Reached'] == 'Yes')
        exams_scheduled = sum(1 for item in data if item['Exam_Scheduled'] == 'Yes')
        
        # Calculate total study hours
        total_hours = 0
        for item in data:
            hours_str = item['Study_Hours'].split()[0]  # Extract number from "X hours"
            total_hours += int(hours_str)
        
        # Calculate average course completion
        completion_values = []
        for item in data:
            percent_str = item['Course_Completion_Percent'].replace('%', '')
            completion_values.append(int(percent_str))
        
        avg_completion = sum(completion_values) / len(completion_values) if completion_values else 0
        
        # Create summary window
        summary_window = tk.Toplevel(self.root)
        summary_window.title("Study Summary")
        summary_window.geometry("500x450")
        summary_window.resizable(False, False)
        
        # Add summary information
        tk.Label(summary_window, text="Today's Study Summary", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        tk.Label(summary_window, text=f"Date: {datetime.now().strftime('%Y-%m-%d')}", 
                font=("Arial", 11)).pack(pady=5)
        
        tk.Label(summary_window, text="=" * 40, font=("Arial", 10)).pack()
        
        tk.Label(summary_window, text=f"Total Study Tasks: {total_tasks}", 
                font=("Arial", 11)).pack(pady=5)
        
        tk.Label(summary_window, text=f"Completed Tasks: {completed_tasks}", 
                font=("Arial", 11)).pack(pady=5)
        
        tk.Label(summary_window, text=f"Targets Reached: {targets_reached}", 
                font=("Arial", 11)).pack(pady=5)
        
        tk.Label(summary_window, text=f"Total Study Hours: {total_hours}", 
                font=("Arial", 11)).pack(pady=5)
        
        tk.Label(summary_window, text=f"Exams Scheduled: {exams_scheduled}", 
                font=("Arial", 11)).pack(pady=5)
        
        tk.Label(summary_window, text=f"Average Course Completion: {avg_completion:.1f}%", 
                font=("Arial", 11)).pack(pady=5)
        
        # Calculate completion rate
        if total_tasks > 0:
            completion_rate = (completed_tasks / total_tasks) * 100
            tk.Label(summary_window, text=f"Task Completion Rate: {completion_rate:.1f}%", 
                    font=("Arial", 11)).pack(pady=5)
        
        tk.Label(summary_window, text="=" * 40, font=("Arial", 10)).pack()
        
        # Subject-wise breakdown
        tk.Label(summary_window, text="Subject-wise Breakdown:", 
                font=("Arial", 11, "bold")).pack(pady=5)
        
        subject_frame = ttk.Frame(summary_window)
        subject_frame.pack(pady=5, fill=tk.BOTH, expand=True)
        
        # Add scrollbar for subject breakdown
        canvas = tk.Canvas(subject_frame)
        scrollbar = ttk.Scrollbar(subject_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        for subject in self.subjects:
            subject_data = [item for item in data if item['Subject'] == subject]
            if subject_data:
                task_detail = subject_data[0]['Study_Task_Details']
                status = subject_data[0]['Status']
                target = subject_data[0]['Target_Reached']
                hours = subject_data[0]['Study_Hours']
                completion = subject_data[0]['Course_Completion_Percent']
                exam = subject_data[0]['Exam_Scheduled']
                
                info = f"{subject}: {task_detail[:25]}... - {status} - Target: {target} - {hours} - Completion: {completion} - Exam: {exam}"
                tk.Label(scrollable_frame, text=info, font=("Arial", 9), 
                        wraplength=450, justify=tk.LEFT).pack(pady=2, anchor=tk.W)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Close button
        tk.Button(summary_window, text="Close", command=summary_window.destroy,
                 bg="gray", fg="white", padx=20, pady=5).pack(pady=10)

def main():
    root = tk.Tk()
    app = StudyTracker(root)
    root.mainloop()

if __name__ == "__main__":
    main()
