import requests
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import re
import json


def get_model_data(model_version_id):
    """Fetches model data from the Civitai API."""
    try:
        url = f"https://civitai.com/api/v1/model-versions/{model_version_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")  # Log the error
        messagebox.showerror("Request Error", f"Failed to fetch data: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")  # Log other errors
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        return None

def parse_model_data(model_data, urn, custom_text=""):
    """Parses JSON, extracts data, and adds custom text and version."""
    if not model_data:
        return None

    try:
        model_name = model_data.get('model', {}).get('name', 'N/A')
        trained_words = "; ".join(model_data.get('trainedWords', []))  # Join with semicolon
        base_model = model_data.get('baseModel', 'N/A')

        match = re.search(r'civitai:(\d+)@(\d+)', urn)
        urn_part = f"{match.group(1)}@{match.group(2)}" if match else "N/A"

        description = f"{model_name}"
        if custom_text:
            description += f". {custom_text.strip()}"

        version_info = urn_part

        files_data = []
        for file_info in model_data.get('files', []):
            # Skip files with "Other" format
            if file_info.get('metadata', {}).get('format') == 'Other':
                continue

            file_name = file_info.get('name', 'N/A').replace('.safetensors', '').replace('.ckpt', '')
            range_val = "0 - 1"  # Always set range to "0 - 1"


            # Remove pipe characters from *all* relevant string fields before adding to files_data
            files_data.append({
                'rate': '',  # Add the 'rate' column, initially empty
                'name': file_name.replace("|", ""),
                'model': base_model.replace("|", ""),
                'range': range_val.replace("|", ""),
                'trigger': trained_words.replace("|", ""),
                'description': description.replace("|", ""),
                'version': version_info.replace("|", "")
            })
        return files_data

    except (KeyError, TypeError, AttributeError) as e:
        print(f"Parsing error: {e}") # Log the error
        messagebox.showerror("Parsing Error", f"Failed to parse model data: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}") # Log other errors
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        return None

def format_as_markdown_table(data):
    """Formats data as a Markdown table, including 'Rate', and 'Version' columns."""
    if not data:
        return "No data found."

    header = "| Rate | Name | Model | Range | Trigger | Description | Version |\n|---|---|---|---|---|---|---|\n"
    rows = "".join(
        f"| {row['rate']} | {row['name']} | {row['model']} | {row['range']} | {row['trigger']} | {row['description']} | {row['version']} |\n"
        for row in data
    )
    return header + rows

def fetch_and_display_data():
    """Fetches data, displays it, and handles invalid URNs and duplicates."""
    urns_text = urn_entry.get("1.0", tk.END).strip()
    lines = urns_text.splitlines()

    all_data = []
    invalid_urns = []
    processed_model_version_ids = set()  # Keep track of processed IDs
    total_lines = len(lines)  # Initial estimate, might be adjusted
    progress_bar["maximum"] = total_lines # Set initially, update later
    progress_bar["value"] = 0
    root.update_idletasks()
    processed_count = 0  # Counter for actual progress


    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        parts = line.split(" ", 1)
        urn = parts[0]
        custom_text = parts[1] if len(parts) > 1 else ""

        match = re.search(r'(\d+)(?:@(\d+))?$', urn)
        if not match:
            invalid_urns.append(line)
            # Don't increment processed_count for invalid URNs
            progress_bar["value"] = i + 1  # visual progress for user.
            root.update_idletasks()
            continue

        model_version_id = match.group(2) or match.group(1)

        # Check for duplicates *before* making the API call
        if model_version_id in processed_model_version_ids:
            print(f"Skipping duplicate model version ID: {model_version_id}")
            # Don't increment processed_count, just skip the duplicate
            progress_bar["value"] = i + 1
            root.update_idletasks()
            continue

        processed_model_version_ids.add(model_version_id)  # Add to set *before* API call
        model_data = get_model_data(model_version_id)

        if model_data:
            parsed_data = parse_model_data(model_data, urn, custom_text)
            if parsed_data:
                all_data.extend(parsed_data)
            else:
                invalid_urns.append(line)
        else:
            invalid_urns.append(line)

        processed_count += 1
        progress_bar["value"] = i+1  # Update after processing each URN
        root.update_idletasks()

    progress_bar["maximum"] = len(lines) # Set the max to the original number of entries
    progress_bar["value"] = len(lines)


    output_text.delete("1.0", tk.END)
    if all_data:
        markdown_table = format_as_markdown_table(all_data)
        output_text.insert("1.0", markdown_table)
    else:
        output_text.insert("1.0", "No valid data found.")

    if invalid_urns:
        invalid_urns_text = "\n".join(invalid_urns)
        output_text.insert(tk.END, f"\n\nInvalid URNs or Parsing Errors:\n{invalid_urns_text}")

    if len(processed_model_version_ids) < len(lines):
         output_text.insert(tk.END, f"\n\nSkipped {len(lines) - len(processed_model_version_ids)} duplicate URNs.")

    progress_bar["value"] = 0

def copy_results():
    """Copies the content of the output_text to the clipboard."""
    text_to_copy = output_text.get("1.0", tk.END).strip()
    if text_to_copy:
        root.clipboard_clear()
        root.clipboard_append(text_to_copy)
    else: # Handle empty output
        messagebox.showinfo("Info", "Nothing to copy.")

def create_context_menu(text_widget):
    """Creates a context menu (right-click menu) for the given text widget."""

    context_menu = tk.Menu(text_widget, tearoff=0)

    def copy_text():
        try:
            # Copy selected text, if any; otherwise, copy all text
            text_widget.clipboard_clear()
            text_widget.clipboard_append(text_widget.selection_get())
        except tk.TclError: # If there is no selection
            text_widget.clipboard_clear()
            text_widget.clipboard_append(text_widget.get("1.0", "end-1c"))
    def paste_text():
        try:
            text_widget.insert(tk.INSERT, text_widget.clipboard_get())
        except tk.TclError:
            pass # nothing on clipboard to paste
    context_menu.add_command(label="Copy", command=copy_text)
    context_menu.add_command(label="Paste", command=paste_text)

    def show_context_menu(event):
        """Displays the context menu at the mouse position."""
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    text_widget.bind("<Button-3>", show_context_menu) # Bind to right-click



# --- GUI Setup ---
root = tk.Tk()
root.title("Civitai Model Data Extractor")
root.minsize(600, 400)

style = ttk.Style()
style.theme_use("clam")

input_frame = ttk.Frame(root, padding="10")
input_frame.pack(fill=tk.X, padx=5, pady=5)

urn_label = ttk.Label(input_frame, text="Civitai URNs (one per line, add custom text after a space):")
urn_label.pack(side=tk.TOP, anchor=tk.W)

urn_entry = scrolledtext.ScrolledText(input_frame, width=50, height=5, wrap=tk.WORD)
urn_entry.pack(side=tk.TOP, fill=tk.X, expand=True)
create_context_menu(urn_entry) # Add context menu

button_frame = ttk.Frame(input_frame)
button_frame.pack(side=tk.TOP, pady=5)

fetch_button = ttk.Button(button_frame, text="Fetch Data", command=fetch_and_display_data)
fetch_button.pack(side=tk.LEFT, padx=5)

copy_button = ttk.Button(button_frame, text="Copy Result", command=copy_results)
copy_button.pack(side=tk.LEFT, padx=5)

progress_bar = ttk.Progressbar(input_frame, orient="horizontal", length=200, mode="determinate")
progress_bar.pack(side=tk.TOP, fill=tk.X, pady=5)

output_frame = ttk.Frame(root, padding="10")
output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

output_label = ttk.Label(output_frame, text="Markdown Table Output:")
output_label.pack(anchor=tk.W)

output_text = scrolledtext.ScrolledText(output_frame, width=80, height=15, wrap=tk.WORD)
output_text.pack(fill=tk.BOTH, expand=True)
create_context_menu(output_text)  # Add context menu

root.mainloop()