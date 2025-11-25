import tkinter as tk
from tkinter import ttk, messagebox
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdf_canvas

# IMPORTAR LA BASE DE DATOS DESDE EL OTRO ARCHIVO
from database import DatabaseManager

class LoginWindow:
    def __init__(self, root, db, on_success_callback):
        self.root = root
        self.db = db
        self.on_success = on_success_callback
        self.root.title("Acceso al Sistema")
        self.root.geometry("300x280")
        self.root.resizable(False, False)

        tk.Label(root, text="Bienvenido", font=("Arial", 18, "bold")).pack(pady=20)
        
        tk.Label(root, text="Usuario:").pack()
        self.entry_user = tk.Entry(root)
        self.entry_user.pack()

        tk.Label(root, text="Contraseña:").pack()
        self.entry_pass = tk.Entry(root, show="*")
        self.entry_pass.pack()

        tk.Button(root, text="Iniciar Sesión", command=self.login, bg="#4CAF50", fg="white", width=15).pack(pady=20)
        
        tk.Label(root, text="Usuario por defecto:", fg="gray", font=("Arial", 8)).pack()
        tk.Label(root, text="admin / password123", fg="gray", font=("Arial", 8, "bold")).pack()

    def login(self):
        if self.db.validate_login(self.entry_user.get(), self.entry_pass.get()):
            self.root.destroy()
            self.on_success()
        else:
            messagebox.showerror("Error", "Credenciales incorrectas")

class MainWindow:
    def __init__(self, db):
        self.db = db
        self.root = tk.Tk()
        self.root.title("Sistema de Gestión de Gastos Personales")
        self.root.geometry("1050x600")
        
        self.editing_id = None

        left_frame = tk.Frame(self.root, padx=15, pady=15)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.lbl_form_title = tk.Label(left_frame, text="Registrar Gasto", font=("Arial", 14, "bold"))
        self.lbl_form_title.pack(anchor="w", pady=(0, 10))
        
        
        tk.Label(left_frame, text="Categoría:").pack(anchor="w")
        self.combo_category = ttk.Combobox(left_frame, values=["Alimentación", "Transporte", "Ocio", "Servicios", "Salud", "Otros"])
        self.combo_category.pack(fill=tk.X, pady=2)
        self.combo_category.current(0)

        tk.Label(left_frame, text="Monto ($):").pack(anchor="w")
        self.entry_amount = tk.Entry(left_frame)
        self.entry_amount.pack(fill=tk.X, pady=2)

        tk.Label(left_frame, text="Descripción:").pack(anchor="w")
        self.entry_desc = tk.Entry(left_frame)
        self.entry_desc.pack(fill=tk.X, pady=2)

        # Botones Formulario
        btn_form_frame = tk.Frame(left_frame)
        btn_form_frame.pack(fill=tk.X, pady=15)

        self.btn_action = tk.Button(btn_form_frame, text="Agregar Gasto", command=self.save_item, bg="#2196F3", fg="white", width=15)
        self.btn_action.pack(side=tk.LEFT, padx=2)

        self.btn_cancel = tk.Button(btn_form_frame, text="Cancelar", command=self.cancel_edit, bg="#9E9E9E", fg="white")

        ttk.Separator(left_frame, orient='horizontal').pack(fill='x', pady=10)

        btn_table_frame = tk.Frame(left_frame)
        btn_table_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_table_frame, text="✏️ Editar Seleccionado", command=self.load_edit_item, bg="#FFC107").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_table_frame, text="🗑️ Eliminar", command=self.delete_item, bg="#F44336", fg="white").pack(side=tk.LEFT, padx=2)

        # Tabla de Datos
        columns = ("ID", "Cat", "Monto", "Desc")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=12)
        self.tree.heading("ID", text="ID")
        self.tree.heading("Cat", text="Categoría")
        self.tree.heading("Monto", text="Monto")
        self.tree.heading("Desc", text="Descripción")
        
        self.tree.column("ID", width=30)
        self.tree.column("Cat", width=100)
        self.tree.column("Monto", width=80)
        self.tree.column("Desc", width=150)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        right_frame = tk.Frame(self.root, bg="white", padx=10, pady=10, relief=tk.RAISED, borderwidth=1)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(right_frame, text="Estadísticas en Tiempo Real", font=("Arial", 12, "bold"), bg="white").pack(pady=10)
        
        self.chart_frame = tk.Frame(right_frame, bg="white")
        self.chart_frame.pack(fill=tk.BOTH, expand=True)

        tk.Button(right_frame, text="📄 Exportar Reporte PDF", command=self.export_pdf, bg="#FF9800", fg="white", font=("Arial", 10, "bold")).pack(pady=20)

        self.refresh_data()
        self.root.mainloop()

    def refresh_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        rows = self.db.get_expenses()
        for row in rows:
            display_row = list(row)
            display_row[2] = f"${row[2]:.2f}" 
            self.tree.insert("", "end", values=display_row)
        
        self.update_chart()

    def save_item(self):
        try:
            cat = self.combo_category.get()
            amount_str = self.entry_amount.get()
            desc = self.entry_desc.get()

            if not amount_str:
                messagebox.showwarning("Faltan datos", "Por favor ingrese un monto.")
                return

            amount = float(amount_str)

            if self.editing_id is None:
                self.db.add_expense(cat, amount, desc)
            else:
                self.db.update_expense(self.editing_id, cat, amount, desc)
                messagebox.showinfo("Éxito", "Registro actualizado.")
                self.cancel_edit()

            self.clear_form()
            self.refresh_data()
        except ValueError:
            messagebox.showerror("Error", "El monto debe ser numérico (ej. 150.50)")

    def load_edit_item(self):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected)
            values = item['values'] 
            
            raw_amount = str(values[2]).replace("$", "")

            self.editing_id = values[0]
            self.combo_category.set(values[1])
            self.entry_amount.delete(0, tk.END)
            self.entry_amount.insert(0, raw_amount)
            self.entry_desc.delete(0, tk.END)
            self.entry_desc.insert(0, values[3])

            self.btn_action.config(text="Guardar Cambios", bg="#4CAF50")
            self.lbl_form_title.config(text=f"Editando ID: {self.editing_id}", fg="#d32f2f")
            self.btn_cancel.pack(side=tk.LEFT, padx=5)
        else:
            messagebox.showwarning("Aviso", "Seleccione una fila para editar")

    def cancel_edit(self):
        self.editing_id = None
        self.clear_form()
        self.btn_action.config(text="Agregar Gasto", bg="#2196F3")
        self.lbl_form_title.config(text="Registrar Gasto", fg="black")
        self.btn_cancel.pack_forget()

    def clear_form(self):
        self.entry_amount.delete(0, tk.END)
        self.entry_desc.delete(0, tk.END)
        self.combo_category.current(0)

    def delete_item(self):
        selected = self.tree.selection()
        if selected:
            if messagebox.askyesno("Confirmar", "¿Seguro que desea eliminar este registro?"):
                item = self.tree.item(selected)

                self.db.delete_expense(item['values'][0])
                if self.editing_id == item['values'][0]:
                    self.cancel_edit()
                self.refresh_data()
        else:
            messagebox.showwarning("Aviso", "Seleccione una fila para eliminar")

    def update_chart(self):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        data = self.db.get_expenses_by_category()
        
        if not data:
            tk.Label(self.chart_frame, text="No hay datos suficientes", bg="white", fg="gray").place(relx=0.5, rely=0.5, anchor="center")
            return

        categories = [x[0] for x in data]
        amounts = [x[1] for x in data]

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        wedges, texts, autotexts = ax.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=90, pctdistance=0.85)
        
        centre_circle = matplotlib_Circle((0,0),0.70,fc='white')
        fig.gca().add_artist(centre_circle)
        
        ax.set_title("Distribución de Gastos", fontsize=12)

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.current_figure = fig

    def export_pdf(self):
        try:
            if not hasattr(self, 'current_figure'):
                return

            self.current_figure.savefig("chart_temp.png")
            
            pdf_name = "Reporte_Gastos.pdf"
            c = pdf_canvas.Canvas(pdf_name, pagesize=letter)
            w, h = letter

            c.setFillColorRGB(0.1, 0.3, 0.5) # Azul oscuro
            c.rect(0, h-80, w, 80, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1) # Blanco
            c.setFont("Helvetica-Bold", 24)
            c.drawString(50, h-50, "Reporte Financiero Personal")
            
            c.setFillColorRGB(0, 0, 0)
            c.drawImage("chart_temp.png", 50, h-400, width=400, height=300)

            c.setFont("Helvetica-Bold", 14)
            c.drawString(300, h-120, "Resumen por Categoría")
            
            data = self.db.get_expenses_by_category()
            total = 0
            y = h - 150
            
            c.setFont("Helvetica", 12)
            for cat, amount in data:
                c.drawString(320, y, f"{cat}:")
                c.drawRightString(500, y, f"${amount:.2f}")
                total += amount
                y -= 20
            
            c.setStrokeColorRGB(0.5, 0.5, 0.5)
            c.line(300, y, 500, y)
            y -= 25
            c.setFont("Helvetica-Bold", 14)
            c.drawString(320, y, "TOTAL:")
            c.drawRightString(500, y, f"${total:.2f}")

            c.save()
            
            if os.path.exists("chart_temp.png"): os.remove("chart_temp.png")
            
            messagebox.showinfo("PDF Generado", f"El reporte se guardó como: {pdf_name}")
            try:
                if os.name == 'nt': os.startfile(pdf_name)
                else: os.system(f"xdg-open {pdf_name}")
            except: pass

        except Exception as e:
            messagebox.showerror("Error PDF", str(e))

from matplotlib.patches import Circle as matplotlib_Circle

if __name__ == "__main__":
    
    db_manager = DatabaseManager()
    
    def start_app():
        MainWindow(db_manager)

    root = tk.Tk()
    LoginWindow(root, db_manager, start_app)
    root.mainloop()