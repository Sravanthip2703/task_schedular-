import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import datetime
import threading
import json
import time

class TaskScheduler:
    def __init__(self):
        self.tasks = []
        self.warning_period = 30  # Set the warning period in minutes
        self.alerted_tasks = set()

    def add_task(self, priority, deadline, description):
        task = (priority, deadline, datetime.datetime.now(), description)
        self.tasks.append(task)

    def get_next_task(self):
        if not self.tasks:
            return None
        next_task = min(self.tasks, key=lambda x: (x[0], x[1]))
        self.tasks.remove(next_task)
        return next_task

    def check_deadlines(self):
        now = datetime.datetime.now()
        approaching_deadlines = [task for task in self.tasks if task[1] - now < datetime.timedelta(minutes=self.warning_period)]
        return approaching_deadlines

    def save_schedule(self, filename):
        def serialize_datetime(obj):
            if isinstance(obj, datetime.datetime):
                return {'_type': 'datetime', 'value': obj.isoformat()}
            raise TypeError("Type not serializable")

        with open(filename, 'w') as file:
            data = {
                "tasks": self.tasks,
                "warning_period": self.warning_period
            }
            json.dump(data, file, default=serialize_datetime)

    def load_schedule(self, filename):
        def deserialize_datetime(obj):
            if '_type' in obj and obj['_type'] == 'datetime':
                return datetime.datetime.fromisoformat(obj['value'])
            return obj

        try:
            with open(filename, 'r') as file:
                data = json.load(file, object_hook=deserialize_datetime)
                self.tasks = data["tasks"]
                self.warning_period = data["warning_period"]
        except FileNotFoundError:
            messagebox.showwarning("File Not Found", "The specified file does not exist.")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Error decoding JSON data in the file.")

class TaskSchedulerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Task Scheduler")

        self.task_scheduler = TaskScheduler()

        # Treeview for displaying tasks
        self.tree = ttk.Treeview(self.master, columns=("Description", "Priority", "Deadline"))
        self.tree.heading("Description", text="Description")
        self.tree.heading("Priority", text="Priority")
        self.tree.heading("Deadline", text="Deadline")
        self.tree.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

        self.create_widgets()

        # Start a thread for checking deadlines
        self.check_deadlines_thread = threading.Thread(target=self.check_deadlines_periodically)
        self.check_deadlines_thread.daemon = True
        self.check_deadlines_thread.start()

    def remove_task(self):
        selected_item = self.tree.selection()
        if selected_item:
            index = int(selected_item[0].split("_")[1])
            removed_task = self.task_scheduler.remove_task(index)
            if removed_task:
                messagebox.showinfo("Task Removed", f"Task removed: {removed_task[3]}")
                self.update_task_list()
            else:
                messagebox.showwarning("Invalid Selection", "Please select a valid task.")
        else:
            messagebox.showwarning("No Selection", "Please select a task to remove.")
    def edit_task(self):
        selected_item = self.tree.focus()
        if selected_item:
            index = int(selected_item.split("_")[1])
        try:
            # Retrieve values from the selected item in the treeview
            values = self.tree.item(selected_item, "values")

            if len(values) >= 5:  # Ensure there are enough values to retrieve
                priority = int(values[1])
                deadline_str = values[2]
                deadline = datetime.datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
                description = values[0]
                recurring = values[3]
                frequency = int(values[4]) if recurring else None

                # Update entry fields with the retrieved values
                self.priority_entry.delete(0, tk.END)
                self.priority_entry.insert(0, priority)

                self.deadline_entry.delete(0, tk.END)
                self.deadline_entry.insert(0, deadline.strftime("%Y-%m-%d %H:%M"))

                self.description_entry.delete(0, tk.END)
                self.description_entry.insert(0, description)

                self.recurring_var.set(recurring)

                self.frequency_entry.delete(0, tk.END)
                self.frequency_entry.insert(0, frequency) if frequency is not None else None

            else:
                messagebox.showwarning("Invalid Selection", "Selected task does not have enough information.")
        except ValueError:
            messagebox.showerror("Error", "Invalid input. Please check your entries.")
        else:
            messagebox.showwarning("No Selection", "Please select a task to edit.")
        def check_deadlines_periodically(self):
            while True:
                approaching_deadlines = self.task_scheduler.check_deadlines()
            for task in approaching_deadlines:
                if task[3] not in self.task_scheduler.alerted_tasks:
                    self.task_scheduler.alerted_tasks.add(task[3])
                    self.alert_user(task)

            time.sleep(60)  # Check deadlines every 60 seconds
    def alert_user(self, task):
        messagebox.showwarning("Approaching Deadline",
                               f"The task '{task[3]}' is approaching its deadline!\n"
                               f"Priority: {task[0]}, Deadline: {task[1].strftime('%Y-%m-%d %H:%M')}, Recurring: {task[4]}, Frequency: {task[5]}")
    def update_task_list(self):
        # Clear existing items in the treeview
        for item in self.tree.get_children():
                self.tree.delete(item)

        # Add tasks to the treeview
        for index, task in enumerate(self.task_scheduler.tasks):
            self.tree.insert("", index, values=(task[3], task[0], task[1].strftime('%Y-%m-%d %H:%M'), task[4]))
    def create_widgets(self):
        # Priority Entry
        priority_label = tk.Label(self.master, text="Priority:")
        priority_label.grid(row=0, column=0, padx=5, pady=5)

        self.priority_entry = tk.Entry(self.master)
        self.priority_entry.grid(row=0, column=1, padx=5, pady=5)

        # Deadline Entry
        deadline_label = tk.Label(self.master, text="Deadline (YYYY-MM-DD HH:MM):")
        deadline_label.grid(row=1, column=0, padx=5, pady=5)

        self.deadline_entry = tk.Entry(self.master)
        self.deadline_entry.grid(row=1, column=1, padx=5, pady=5)

        # Description Entry
        description_label = tk.Label(self.master, text="Task Description:")
        description_label.grid(row=2, column=0, padx=5, pady=5)

        self.description_entry = tk.Entry(self.master)
        self.description_entry.grid(row=2, column=1, padx=5, pady=5)
        # Recurring Checkbox
        self.recurring_var = tk.BooleanVar()
        recurring_checkbox = tk.Checkbutton(self.master, text="Recurring", variable=self.recurring_var)
        recurring_checkbox.grid(row=3, column=0, padx=5, pady=5)

        # Frequency Entry
        frequency_label = tk.Label(self.master, text="Frequency (in minutes):")
        frequency_label.grid(row=3, column=1, padx=5, pady=5)

        self.frequency_entry = tk.Entry(self.master)
        self.frequency_entry.grid(row=3, column=2, padx=5, pady=5)

        # Add Task Button
        add_task_button = tk.Button(self.master, text="Add Task", command=self.add_task)
        add_task_button.grid(row=3, column=0, columnspan=2, pady=10)

        # Save Schedule Button
        save_schedule_button = tk.Button(self.master, text="Save Schedule", command=self.save_schedule)
        save_schedule_button.grid(row=6, column=0, pady=10)
        # Load Schedule Button
        load_schedule_button = tk.Button(self.master, text="Load Schedule", command=self.load_schedule)
        load_schedule_button.grid(row=6, column=1, pady=10)

        # Next Task Button
        next_task_button = tk.Button(self.master, text="Get Next Task", command=self.get_next_task)
        next_task_button.grid(row=5, column=0, columnspan=2, pady=10)

    def add_task(self):
        try:
            priority = int(self.priority_entry.get())
            deadline_str = self.deadline_entry.get()
            deadline = datetime.datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
            description = self.description_entry.get()
            self.task_scheduler.add_task(priority, deadline, description)
            self.update_task_list()
        except ValueError:
            messagebox.showerror("Error", "Invalid input. Please check your entries.")

    def get_next_task(self):
        next_task = self.task_scheduler.get_next_task()
        if next_task:
            # Display a dialog box with options
            result = messagebox.askquestion("Next Task", f"Next Task: {next_task[3]} (Priority: {next_task[0]}, Deadline: {next_task[1].strftime('%Y-%m-%d %H:%M')})\nDo you want to stop the alert for this task?")
            
            if result == 'yes':
                self.stop_alert(next_task[3])

        else:
            messagebox.showinfo("No Tasks", "No tasks in the scheduler.")

        approaching_deadlines = self.task_scheduler.check_deadlines()
        if approaching_deadlines:
            message = "Approaching deadlines:\n"
            for task in approaching_deadlines:
                message += f"{task[3]} - Deadline: {task[1].strftime('%Y-%m-%d %H:%M')}\n"
            messagebox.showwarning("Approaching Deadlines", message)

    def stop_alert(self, task_description):
        # Add your logic here for stopping the alert for the given task
        self.task_scheduler.alerted_tasks.add(task_description)
        print(f"Alert for task '{task_description}' stopped.")

    def update_task_list(self):
        self.tree.delete(*self.tree.get_children())
        for task in sorted(self.task_scheduler.tasks, key=lambda x: (x[0], x[1])):
            self.tree.insert("", "end", values=(task[3], task[0], task[1].strftime('%Y-%m-%d %H:%M')))

    def check_deadlines_periodically(self):
        while True:
            approaching_deadlines = self.task_scheduler.check_deadlines()
            for task in approaching_deadlines:
                if datetime.datetime.now() >= task[1] and task[3] not in self.task_scheduler.alerted_tasks:
                    self.show_alert(task[3])
            # Sleep for a short interval before checking again
            time.sleep(10)

    def show_alert(self, task_description):
        result = messagebox.askquestion("Deadline Alert", f"The deadline for task '{task_description}' has been reached!\nDo you want to stop the alert for this task?")
        
        if result == 'yes':
            self.stop_alert(task_description)
        else:
            print(f"Alert for task '{task_description}' will be displayed again later.")

    def save_schedule(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filename:
            self.task_scheduler.save_schedule(filename)
            messagebox.showinfo("Save Successful", "Schedule saved successfully.")

    def load_schedule(self):
        filename = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filename:
            self.task_scheduler.load_schedule(filename)
            self.update_task_list()
            messagebox.showinfo("Load Successful", "Schedule loaded successfully.")

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskSchedulerApp(root)
    root.mainloop()
