#!/usr/bin/env python3

import csv
import os
import tkinter as tk
from tkinter import ttk, messagebox


def calculate_monthly_payment(principal, annual_rate, months):
    """
    Calculate monthly payment using standard loan amortization formula.
    """

    if months <= 0:
        return 0.0

    monthly_rate = annual_rate / 100 / 12

    # Handle 0% interest loans
    if monthly_rate == 0:
        return principal / months

    payment = (
        principal
        * monthly_rate
        * (1 + monthly_rate) ** months
        / ((1 + monthly_rate) ** months - 1)
    )

    return payment


def process_csv():
    csv_file = "bills.csv"

    if not os.path.exists(csv_file):
        messagebox.showerror(
            "Error",
            f"{csv_file} not found in current directory."
        )
        return

    rows = []

    try:
        with open(csv_file, "r", newline="") as infile:
            reader = csv.DictReader(infile)

            for row in reader:
                debt_name = row["debt_name"]

                principal = float(row["debt_amount"])
                annual_rate = float(row["debt_interest"])
                months = int(row["number_of_months"])

                payment = calculate_monthly_payment(
                    principal,
                    annual_rate,
                    months
                )

                row["monthly_payment"] = f"{payment:.2f}"
                rows.append(row)

        # Write updated CSV
        with open(csv_file, "w", newline="") as outfile:
            fieldnames = [
                "debt_name",
                "debt_amount",
                "debt_interest",
                "number_of_months",
                "monthly_payment",
            ]

            writer = csv.DictWriter(
                outfile,
                fieldnames=fieldnames
            )

            writer.writeheader()
            writer.writerows(rows)

        # Display results
        output_text.delete("1.0", tk.END)

        output_text.insert(
            tk.END,
            "Debt Monthly Payment Summary\n"
        )
        output_text.insert(
            tk.END,
            "============================\n\n"
        )

        for row in rows:
            output_text.insert(
                tk.END,
                f"{row['debt_name']:<25} "
                f"${float(row['monthly_payment']):,.2f}\n"
            )

        messagebox.showinfo(
            "Success",
            "Monthly payments calculated and bills.csv updated."
        )

    except Exception as e:
        messagebox.showerror(
            "Error",
            f"Failed to process file:\n\n{str(e)}"
        )


# GUI
root = tk.Tk()
root.title("Debt Payment Calculator")
root.geometry("700x500")

title_label = ttk.Label(
    root,
    text="Debt Payment Calculator",
    font=("Arial", 16, "bold")
)
title_label.pack(pady=10)

process_button = ttk.Button(
    root,
    text="Calculate Monthly Payments",
    command=process_csv
)
process_button.pack(pady=10)

output_text = tk.Text(
    root,
    height=20,
    width=80
)
output_text.pack(padx=10, pady=10)

root.mainloop()
