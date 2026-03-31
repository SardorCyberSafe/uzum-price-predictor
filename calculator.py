"""
G'AROYIB KALKULYATOR — Python Tkinter GUI
Basic + Scientific + Tarix + Klaviatura qo'llab-quvvatlash
"""

import tkinter as tk
from tkinter import font, messagebox
import math
import json
import os
from datetime import datetime


class Calculator:
    def __init__(self, root):
        self.root = root
        self.root.title("G'aroyib Kalkulyator")
        self.root.geometry("420x680")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")

        self.expression = ""
        self.result = ""
        self.history = []
        self.is_scientific = False
        self.memory = 0
        self.last_answer = 0

        self.load_history()
        self.setup_ui()
        self.bind_keys()

    def setup_ui(self):
        # ===== DISPLAY =====
        display_frame = tk.Frame(self.root, bg="#1a1a2e")
        display_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.expression_var = tk.StringVar(value="")
        self.result_var = tk.StringVar(value="0")

        expr_label = tk.Label(
            display_frame,
            textvariable=self.expression_var,
            font=("Consolas", 14),
            bg="#1a1a2e",
            fg="#888",
            anchor="e",
            wraplength=380,
        )
        expr_label.pack(fill="x", pady=(0, 2))

        result_label = tk.Label(
            display_frame,
            textvariable=self.result_var,
            font=("Consolas", 32, "bold"),
            bg="#1a1a2e",
            fg="#ffffff",
            anchor="e",
        )
        result_label.pack(fill="x", pady=(0, 5))

        # ===== MODE TOGGLE =====
        mode_frame = tk.Frame(self.root, bg="#1a1a2e")
        mode_frame.pack(fill="x", padx=10, pady=2)

        self.mode_btn = tk.Button(
            mode_frame,
            text="🔬 Scientific",
            command=self.toggle_mode,
            font=("Consolas", 10),
            bg="#16213e",
            fg="#e94560",
            activebackground="#0f3460",
            activeforeground="#fff",
            relief="flat",
            cursor="hand2",
            width=14,
        )
        self.mode_btn.pack(side="left")

        hist_btn = tk.Button(
            mode_frame,
            text="📜 Tarix",
            command=self.show_history,
            font=("Consolas", 10),
            bg="#16213e",
            fg="#e94560",
            activebackground="#0f3460",
            activeforeground="#fff",
            relief="flat",
            cursor="hand2",
            width=14,
        )
        hist_btn.pack(side="right")

        # ===== MEMORY BUTTONS =====
        mem_frame = tk.Frame(self.root, bg="#1a1a2e")
        mem_frame.pack(fill="x", padx=10, pady=2)

        mem_btns = [
            ("MC", self.mem_clear, "#0f3460"),
            ("MR", self.mem_recall, "#0f3460"),
            ("M+", self.mem_add, "#0f3460"),
            ("M-", self.mem_sub, "#0f3460"),
        ]
        for text, cmd, bg in mem_btns:
            btn = tk.Button(
                mem_frame,
                text=text,
                command=cmd,
                font=("Consolas", 10, "bold"),
                bg=bg,
                fg="#aaa",
                activebackground="#1a1a4e",
                activeforeground="#fff",
                relief="flat",
                cursor="hand2",
                width=6,
            )
            btn.pack(side="left", expand=True, fill="x", padx=1)

        # ===== SCIENTIFIC BUTTONS (hidden by default) =====
        self.sci_frame = tk.Frame(self.root, bg="#1a1a2e")

        sci_btns = [
            ("sin", lambda: self.insert_func("sin(")),
            ("cos", lambda: self.insert_func("cos(")),
            ("tan", lambda: self.insert_func("tan(")),
            ("log", lambda: self.insert_func("log(")),
            ("ln", lambda: self.insert_func("ln(")),
            ("√", lambda: self.insert_func("sqrt(")),
            ("x²", lambda: self.insert_op("**2")),
            ("xʸ", lambda: self.insert_op("**")),
            ("π", lambda: self.insert_const("pi")),
            ("e", lambda: self.insert_const("e")),
            ("(", lambda: self.insert_char("(")),
            (")", lambda: self.insert_char(")")),
            ("|x|", lambda: self.insert_func("abs(")),
            ("1/x", lambda: self.insert_op("1/(")),
            ("n!", self.factorial),
            ("%", lambda: self.insert_op("/100")),
        ]

        for i, (text, cmd) in enumerate(sci_btns):
            row, col = divmod(i, 4)
            btn = tk.Button(
                self.sci_frame,
                text=text,
                command=cmd,
                font=("Consolas", 12, "bold"),
                bg="#0f3460",
                fg="#4fc3f7",
                activebackground="#1a1a4e",
                activeforeground="#fff",
                relief="flat",
                cursor="hand2",
            )
            btn.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")

        for c in range(4):
            self.sci_frame.grid_columnconfigure(c, weight=1)

        # ===== MAIN BUTTONS =====
        btn_frame = tk.Frame(self.root, bg="#1a1a2e")
        btn_frame.pack(fill="both", expand=True, padx=10, pady=5)

        buttons = [
            ("C", self.clear, "#e94560", "#fff"),
            ("⌫", self.backspace, "#e94560", "#fff"),
            ("±", self.toggle_sign, "#0f3460", "#4fc3f7"),
            ("÷", lambda: self.insert_op("/"), "#0f3460", "#4fc3f7"),
            ("7", lambda: self.insert_char("7"), "#16213e", "#fff"),
            ("8", lambda: self.insert_char("8"), "#16213e", "#fff"),
            ("9", lambda: self.insert_char("9"), "#16213e", "#fff"),
            ("×", lambda: self.insert_op("*"), "#0f3460", "#4fc3f7"),
            ("4", lambda: self.insert_char("4"), "#16213e", "#fff"),
            ("5", lambda: self.insert_char("5"), "#16213e", "#fff"),
            ("6", lambda: self.insert_char("6"), "#16213e", "#fff"),
            ("−", lambda: self.insert_op("-"), "#0f3460", "#4fc3f7"),
            ("1", lambda: self.insert_char("1"), "#16213e", "#fff"),
            ("2", lambda: self.insert_char("2"), "#16213e", "#fff"),
            ("3", lambda: self.insert_char("3"), "#16213e", "#fff"),
            ("+", lambda: self.insert_op("+"), "#0f3460", "#4fc3f7"),
            ("0", lambda: self.insert_char("0"), "#16213e", "#fff"),
            (".", lambda: self.insert_char("."), "#16213e", "#fff"),
            ("=", self.calculate, "#e94560", "#fff"),
            ("=", self.calculate, "#e94560", "#fff"),
        ]

        for i, (text, cmd, bg, fg) in enumerate(buttons):
            row, col = divmod(i, 4)
            btn = tk.Button(
                btn_frame,
                text=text,
                command=cmd,
                font=("Consolas", 16, "bold"),
                bg=bg,
                fg=fg,
                activebackground="#2a2a5e",
                activeforeground="#fff",
                relief="flat",
                cursor="hand2",
                borderwidth=0,
                highlightthickness=0,
            )
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")

        for c in range(4):
            btn_frame.grid_columnconfigure(c, weight=1)
        for r in range(5):
            btn_frame.grid_rowconfigure(r, weight=1)

    def toggle_mode(self):
        self.is_scientific = not self.is_scientific
        if self.is_scientific:
            self.sci_frame.pack(
                fill="x", padx=10, pady=2, before=self.root.pack_slaves()[-2]
            )
            self.mode_btn.config(text="🔢 Oddiy")
            self.root.geometry("420x780")
        else:
            self.sci_frame.pack_forget()
            self.mode_btn.config(text="🔬 Scientific")
            self.root.geometry("420x680")

    def insert_char(self, char):
        self.expression += char
        self.expression_var.set(self.expression)

    def insert_op(self, op):
        if self.expression and self.expression[-1] in "+-*/":
            self.expression = self.expression[:-1]
        self.expression += op
        self.expression_var.set(self.expression)

    def insert_func(self, func):
        self.expression += func
        self.expression_var.set(self.expression)

    def insert_const(self, const):
        if const == "pi":
            self.expression += "pi"
        elif const == "e":
            self.expression += "e"
        self.expression_var.set(self.expression)

    def clear(self):
        self.expression = ""
        self.result = ""
        self.expression_var.set("")
        self.result_var.set("0")

    def backspace(self):
        self.expression = self.expression[:-1]
        self.expression_var.set(self.expression)

    def toggle_sign(self):
        if self.expression:
            if self.expression.startswith("-"):
                self.expression = self.expression[1:]
            else:
                self.expression = "-" + self.expression
            self.expression_var.set(self.expression)

    def factorial(self):
        try:
            n = int(eval(self.expression))
            result = math.factorial(n)
            self.add_to_history(f"{n}!", str(result))
            self.expression = str(result)
            self.expression_var.set(self.expression)
            self.result_var.set(self.format_result(result))
        except:
            self.result_var.set("Xatolik!")

    def calculate(self):
        if not self.expression:
            return

        try:
            expr = self.expression
            # Replace math functions
            expr = expr.replace("sin(", "math.sin(")
            expr = expr.replace("cos(", "math.cos(")
            expr = expr.replace("tan(", "math.tan(")
            expr = expr.replace("log(", "math.log10(")
            expr = expr.replace("ln(", "math.log(")
            expr = expr.replace("sqrt(", "math.sqrt(")
            expr = expr.replace("abs(", "abs(")
            expr = expr.replace("pi", str(math.pi))
            expr = expr.replace("e", str(math.e))

            result = eval(expr)

            if isinstance(result, complex):
                self.result_var.set("Kompleks son!")
                return

            self.last_answer = result
            self.add_to_history(self.expression, self.format_result(result))

            self.result_var.set(self.format_result(result))
            self.expression = str(result)
            self.expression_var.set(self.expression)

        except ZeroDivisionError:
            self.result_var.set("Nolga bo'lib bo'lmaydi!")
        except Exception:
            self.result_var.set("Xatolik!")

    def format_result(self, num):
        if isinstance(num, float):
            if num == int(num):
                return f"{int(num):,}"
            return f"{num:,.10g}"
        return f"{num:,}"

    # ===== MEMORY =====
    def mem_clear(self):
        self.memory = 0

    def mem_recall(self):
        self.expression += str(self.memory)
        self.expression_var.set(self.expression)

    def mem_add(self):
        try:
            val = eval(self.expression) if self.expression else 0
            self.memory += val
        except:
            pass

    def mem_sub(self):
        try:
            val = eval(self.expression) if self.expression else 0
            self.memory -= val
        except:
            pass

    # ===== HISTORY =====
    def add_to_history(self, expr, result):
        entry = {
            "expression": expr,
            "result": result,
            "time": datetime.now().strftime("%H:%M:%S"),
        }
        self.history.insert(0, entry)
        if len(self.history) > 50:
            self.history.pop()
        self.save_history()

    def show_history(self):
        if not self.history:
            messagebox.showinfo("Tarix", "Tarix bo'sh!")
            return

        top = tk.Toplevel(self.root)
        top.title("Hisoblash Tarixi")
        top.geometry("400x500")
        top.configure(bg="#1a1a2e")

        tk.Label(
            top,
            text="📜 Tarix",
            font=("Consolas", 16, "bold"),
            bg="#1a1a2e",
            fg="#e94560",
        ).pack(pady=10)

        frame = tk.Frame(top, bg="#1a1a2e")
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        for i, entry in enumerate(self.history[:30]):
            bg = "#16213e" if i % 2 == 0 else "#0f3460"
            row_frame = tk.Frame(frame, bg=bg)
            row_frame.pack(fill="x", pady=1)

            tk.Label(
                row_frame,
                text=entry["time"],
                font=("Consolas", 9),
                bg=bg,
                fg="#888",
                width=8,
                anchor="w",
            ).pack(side="left", padx=5)

            tk.Label(
                row_frame,
                text=entry["expression"],
                font=("Consolas", 10),
                bg=bg,
                fg="#4fc3f7",
                anchor="w",
            ).pack(side="left", fill="x", expand=True, padx=2)

            tk.Label(
                row_frame,
                text=f"= {entry['result']}",
                font=("Consolas", 11, "bold"),
                bg=bg,
                fg="#e94560",
                anchor="e",
            ).pack(side="right", padx=5)

            def make_cmd(e=entry):
                return lambda: self.load_from_history(e)

            row_frame.bind("<Button-1>", make_cmd())
            row_frame.bind("<Enter>", lambda e: e.widget.config(bg="#2a2a5e"))
            row_frame.bind("<Leave>", lambda e: e.widget.config(bg=bg))

        clear_btn = tk.Button(
            top,
            text="🗑️ Tarixni tozalash",
            command=self.clear_history,
            font=("Consolas", 10),
            bg="#e94560",
            fg="#fff",
            relief="flat",
            cursor="hand2",
        )
        clear_btn.pack(pady=10)

    def load_from_history(self, entry):
        self.expression = entry["result"].replace(",", "")
        self.expression_var.set(self.expression)
        self.result_var.set(entry["result"])

    def clear_history(self):
        self.history = []
        self.save_history()

    def save_history(self):
        try:
            with open("calc_history.json", "w") as f:
                json.dump(self.history, f)
        except:
            pass

    def load_history(self):
        try:
            with open("calc_history.json", "r") as f:
                self.history = json.load(f)
        except:
            self.history = []

    # ===== KEYBOARD =====
    def bind_keys(self):
        self.root.bind("<Key>", self.on_key)

    def on_key(self, event):
        key = event.char

        if key in "0123456789.":
            self.insert_char(key)
        elif key in "+-*/":
            self.insert_op(key)
        elif key == "(":
            self.insert_char("(")
        elif key == ")":
            self.insert_char(")")
        elif key == "\r" or key == "=":
            self.calculate()
        elif key == "\b" or key == "\x7f":
            self.backspace()
        elif key == "Escape":
            self.clear()
        elif key == "^":
            self.insert_op("**")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    calc = Calculator(root)
    calc.run()
