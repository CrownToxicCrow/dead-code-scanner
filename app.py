import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path

from dead_code_scanner import (
    scan_project,
    save_report,
    calculate_confidence,
    clean_dead_code,
    restore_from_backup
)

def choose_folder():
    folder = filedialog.askdirectory()
    if folder:
        path_entry.delete(0, tk.END)
        path_entry.insert(0, folder)

def run_restore():
    project_path = Path(path_entry.get())
    if not project_path.exists():
        messagebox.showerror("Ошибка", "Папка не найдена")
        return
    
    count = restore_from_backup(project_path)
    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, f"Восстановлено файлов из бэкапов: {count}\n")
    messagebox.showinfo("Готово", f"Восстановлено {count} файлов.")

def run_scan():
    project_path = Path(path_entry.get())

    if not project_path.exists():
        messagebox.showerror("Ошибка", "Папка не найдена")
        return

    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, "Сканирование началось...\n\n")

    results = scan_project(project_path)

    if results:
        for file_path, comments in results.items():
            clean_dead_code(file_path, comments)
        save_report(results)
        
        output_box.insert(tk.END, "Удаление мертвого кода завершено!\n")
        output_box.insert(tk.END, "Бэкапы созданы для всех измененных файлов.\n")
    
    save_report(results)

    if not results:
        output_box.insert(tk.END, "Подозрительно закомментированный код не найден.\n")
        output_box.insert(tk.END, "\nОтчет сохранен в report.txt")
        return

    for file_path, comments in results.items():
        output_box.insert(tk.END, f"\nФайл: {file_path}\n")

        for item in comments:
            output_box.insert(tk.END, "=" * 50 + "\n")
            output_box.insert(tk.END, "[ОБНАРУЖЕН МЕРТВЫЙ КОД]\n")
            output_box.insert(tk.END, f"Строки: {item['start']}-{item['end']}\n")
            output_box.insert(tk.END, f"Тип: {item['type']}\n")
            confidence = max(
                calculate_confidence(text)
                for _, text in item["lines"]
            )

            output_box.insert(
                tk.END,
                f"Уверенность: {confidence}%\n"
            )
            output_box.insert(tk.END, "Код:\n")

            if "snippet" in item:
                output_box.insert(tk.END, item["snippet"] + "\n")
            else:
                for line_num, text in item["lines"]:
                    output_box.insert(tk.END, f"  {line_num}: {text}\n")

            output_box.insert(tk.END, "=" * 50 + "\n\n")

    output_box.insert(tk.END, "\nОтчет сохранен в report.txt")


root = tk.Tk()
root.title("Java Dead Code Scanner")
root.geometry("900x600")

title_label = tk.Label(root, text="Java Dead Code Scanner", font=("Arial", 18, "bold"))
title_label.pack(pady=10)

frame = tk.Frame(root)
frame.pack(fill="x", padx=10)

path_entry = tk.Entry(frame, font=("Arial", 11))
path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

browse_button = tk.Button(frame, text="Обзор", command=choose_folder)
browse_button.pack(side="left")

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

scan_button = tk.Button(btn_frame, text="Сканировать и удалить", command=run_scan, font=("Arial", 12))
scan_button.pack(side="left", padx=5)

restore_button = tk.Button(btn_frame, text="Откат (Восстановить)", command=run_restore, font=("Arial", 12), fg="red")
restore_button.pack(side="left", padx=5)

output_box = scrolledtext.ScrolledText(root, font=("Consolas", 10))
output_box.pack(fill="both", expand=True, padx=10, pady=10)

root.mainloop()