import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import imageio.v2 as imageio
import os
import configparser
import requests
import base64
import json
from image_generate import BaiduImageGenerator

class ResizeDialog:
    def __init__(self, parent, initial_width, initial_height):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Resize Settings")
        self.dialog.geometry("300x150")
        self.dialog.resizable(False, False)
        
        width_frame = ttk.Frame(self.dialog)
        width_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(width_frame, text="Width:").pack(side='left')
        self.width_entry = ttk.Entry(width_frame)
        self.width_entry.pack(side='left', padx=5)
        self.width_entry.insert(0, initial_width)
        
        height_frame = ttk.Frame(self.dialog)
        height_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(height_frame, text="Height:").pack(side='left')
        self.height_entry = ttk.Entry(height_frame)
        self.height_entry.pack(side='left', padx=5)
        self.height_entry.insert(0, initial_height)
        
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=10)
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side='right')
        
        self.result = None
    
    def ok(self):
        self.result = (self.width_entry.get(), self.height_entry.get())
        self.dialog.destroy()
    
    def cancel(self):
        self.dialog.destroy()

class CompressionDialog:
    def __init__(self, parent, initial_quality):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Compression Settings")
        self.dialog.geometry("300x150")
        self.dialog.resizable(False, False)
        
        ttk.Label(self.dialog, text="Compression Quality:").pack(padx=10, pady=5)
        self.quality = tk.IntVar(value=initial_quality)
        self.slider = ttk.Scale(
            self.dialog,
            from_=1,
            to=100,
            orient='horizontal',
            variable=self.quality
        )
        self.slider.pack(fill='x', padx=10, pady=5)
        
        self.value_label = ttk.Label(self.dialog, text=f"Quality: {initial_quality}%")
        self.value_label.pack(pady=5)
        self.slider.config(command=self.update_label)
        
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=10)
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side='right')
        
        self.result = None
    
    def update_label(self, value):
        self.value_label.config(text=f"Quality: {int(float(value))}%")
    
    def ok(self):
        self.result = self.quality.get()
        self.dialog.destroy()
    
    def cancel(self):
        self.dialog.destroy()

class PromptDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Generate Image")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        
        prompt_frame = ttk.Frame(self.dialog)
        prompt_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(prompt_frame, text="Prompt:").pack(side='left')
        self.prompt_entry = ttk.Entry(prompt_frame, width=40)
        self.prompt_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        style_frame = ttk.Frame(self.dialog)
        style_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(style_frame, text="Style:").pack(side='left')
        self.style_var = tk.StringVar(value="写实风格")
        styles = ["写实风格", "油画风格", "水彩画风格", "卡通风格", "二次元风格", "浮世绘风格", 
                 "未来主义风格", "像素风格", "概念艺术风格", "赛博朋克风格", "洛丽塔风格"]
        self.style_menu = ttk.OptionMenu(style_frame, self.style_var, *styles)
        self.style_menu.pack(side='left', padx=5)
        
        size_frame = ttk.Frame(self.dialog)
        size_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(size_frame, text="Size:").pack(side='left')
        self.size_var = tk.StringVar(value="1024x1024")
        sizes = ["1024x1024", "1024x1536", "1536x1024"]
        self.size_menu = ttk.OptionMenu(size_frame, self.size_var, *sizes)
        self.size_menu.pack(side='left', padx=5)

        number_frame = ttk.Frame(self.dialog)
        number_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(number_frame, text="Image Count:").pack(side='left')
        self.number_var = tk.StringVar(value="1")
        numbers = ["1", "2", "3", "4"]
        self.number_menu = ttk.OptionMenu(number_frame, self.number_var, *numbers)
        self.number_menu.pack(side='left', padx=5)
        
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=10)
        ttk.Button(button_frame, text="Generate", command=self.ok).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side='right')
        
        self.result = None

    def ok(self):
        self.result = (self.prompt_entry.get(), 
                      self.style_var.get(),
                      self.size_var.get(),
                      int(self.number_var.get()))
        self.dialog.destroy()
    
    def cancel(self):
        self.dialog.destroy()

class ImageToolsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Tools")
        self.root.geometry("800x600")
        
        self.config = configparser.ConfigParser()
        self.config_file = "config.ini"
        self.load_config()
        
        self.files = []
        self.thumbnails = []
        
        # Configure grid layout
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)
        
        # Menu
        self.menu = tk.Menu(root)
        self.root.config(menu=self.menu)
        
        # Settings menu
        self.settings_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Settings", menu=self.settings_menu)
        self.settings_menu.add_command(label="Resize Settings", command=self.show_resize_dialog)
        self.settings_menu.add_command(label="Compression Settings", command=self.show_compression_dialog)
        
        # Add AI menu
        self.ai_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="AI Tools", menu=self.ai_menu)
        self.ai_menu.add_command(label="Generate Image", command=self.show_generate_dialog)
       
        
        # File selection
        self.file_label = ttk.Label(root, text="Select Images:")
        self.file_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.file_button = ttk.Button(root, text="Browse", command=self.browse_files)
        self.file_button.grid(row=0, column=1, padx=10, pady=10, sticky="e")
        
        # Canvas to display selected files - hidden by default
        self.canvas = tk.Canvas(root, width=780, height=400, bg="white")
        self.scroll_y = tk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        
        self.frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Create an empty label for "No images" message
        self.empty_label = ttk.Label(root, text="No images selected", foreground="gray")
        self.empty_label.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
        
        # Format conversion options
        self.format_label = ttk.Label(root, text="Convert to Format:")
        self.format_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.format_var = tk.StringVar(value="png")
        self.format_options = ["png", "jpg", "webp"]
        self.format_menu = ttk.OptionMenu(root, self.format_var, *self.format_options)
        self.format_menu.grid(row=2, column=1, padx=10, pady=10, sticky="e")
        
        # Create frames for options
        self.options_frame = ttk.Frame(root)
        self.options_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        # Add checkboxes
        self.resize_var = tk.BooleanVar(value=False)
        self.resize_check = ttk.Checkbutton(
            self.options_frame, 
            text="Resize", 
            variable=self.resize_var
        )
        self.resize_check.pack(side="left", padx=5)
        
        self.compress_var = tk.BooleanVar(value=False)
        self.compress_check = ttk.Checkbutton(
            self.options_frame, 
            text="Compress", 
            variable=self.compress_var
        )
        self.compress_check.pack(side="left", padx=5)
        
        # Process button
        self.process_button = ttk.Button(root, text="Process Images", command=self.process_images)
        self.process_button.grid(row=3, column=0, columnspan=2, padx=10, pady=20)
        
        self.image_generator = BaiduImageGenerator()
    
    def load_config(self):
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            self.config['SETTINGS'] = {
                'width': '800', 
                'height': '600',
                'compression_quality': '95'
            }
           
            self.save_config()
    
    def save_config(self):
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
    
    def show_resize_dialog(self):
        dialog = ResizeDialog(
            self.root,
            self.config['SETTINGS'].get('width', '800'),
            self.config['SETTINGS'].get('height', '600')
        )
        self.root.wait_window(dialog.dialog)
        if dialog.result:
            width, height = dialog.result
            self.config['SETTINGS']['width'] = width
            self.config['SETTINGS']['height'] = height
            self.save_config()

    def show_compression_dialog(self):
        initial_quality = int(self.config['SETTINGS'].get('compression_quality', '95'))
        dialog = CompressionDialog(self.root, initial_quality)
        self.root.wait_window(dialog.dialog)
        if dialog.result is not None:
            self.config['SETTINGS']['compression_quality'] = str(dialog.result)
            self.save_config()
    
   

    def show_generate_dialog(self):
        dialog = PromptDialog(self.root)
        self.root.wait_window(dialog.dialog)
        if dialog.result:
            prompt, style, size, count = dialog.result
            width, height = map(int, size.split('x'))
            self.generate_image(prompt, width, height)

    def generate_image(self, prompt, width=640, height=480):
        try:
            # Generate image using BaiduImageGenerator
            result = self.image_generator.generate_image(prompt, width, height)
            if not result:
                raise Exception("Failed to start generation")

            print("Generation started...")
            
            if 'status' not in result or 'taskid' not in result:
                raise Exception("Invalid response format")
            
            task_id = result['taskid']
            token = result.get('token', '')
            timestamp = result.get('timestamp', '')
            
            # Wait for completion
            print("\nWaiting for generation to complete...")
            final_result = self.image_generator.wait_for_completion(task_id, prompt, token, timestamp)
            
            if not final_result:
                raise Exception("Generation failed or timed out")
            
            # Save images
            saved_files = self.image_generator.save_images(final_result, prompt)
            if saved_files:
                # Add generated images to the current selection
                self.files = list(self.files)
                self.files.extend(saved_files)
                self.files = tuple(self.files)
                self.show_thumbnails()
                messagebox.showinfo("Success", f"Successfully generated {len(saved_files)} images")
            else:
                raise Exception("No images were saved")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate image: {str(e)}")
    
    def browse_files(self):
        self.files = filedialog.askopenfilenames(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.webp;*.avif")])
        self.show_thumbnails()
    
    def show_thumbnails(self):
        self.thumbnails = []
        for widget in self.frame.winfo_children():
            widget.destroy()
            
        if not self.files:
            # Hide canvas and scrollbar, show empty message
            self.canvas.grid_remove()
            self.scroll_y.grid_remove()
            self.empty_label.grid()
            return
            
        # Show canvas and scrollbar, hide empty message
        self.empty_label.grid_remove()
        self.canvas.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.scroll_y.grid(row=1, column=2, sticky="ns")
        
        # Display thumbnails
        for file in self.files:
            if file.lower().endswith('avif'):
                img = imageio.imread(file, plugin='avif')
                img = Image.fromarray(img)
            else:
                img = Image.open(file)
            img.thumbnail((100, 100))
            thumbnail = ImageTk.PhotoImage(img)
            self.thumbnails.append(thumbnail)
            label = tk.Label(self.frame, image=thumbnail)
            label.pack(side="left", padx=5, pady=5)
    
    def process_images(self):
        if not self.files:
            messagebox.showerror("Error", "Please select images")
            return
        
        width = self.config['SETTINGS']['width']
        height = self.config['SETTINGS']['height']
        compression_quality = int(self.config['SETTINGS'].get('compression_quality', '95'))
        target_format = self.format_var.get()
        
        for filepath in self.files:
            try:
                if filepath.lower().endswith('avif'):
                    img = imageio.imread(filepath, plugin='avif')
                    img = Image.fromarray(img)
                else:
                    img = Image.open(filepath)
                
                # Resize image only if checkbox is checked
                if self.resize_var.get() and width and height:
                    img = img.resize((int(width), int(height)))
                
                # Save with compression settings if enabled
                quality = compression_quality if self.compress_var.get() else 95
                
                new_filename = os.path.splitext(os.path.basename(filepath))[0] + f".{target_format}"
                new_filepath = os.path.join(os.path.dirname(filepath), new_filename)
                
                if target_format.lower() == 'jpg':
                    img.save(new_filepath, 'JPEG', quality=quality)
                elif target_format.lower() == 'png':
                    optimize = self.compress_var.get()
                    img.save(new_filepath, 'PNG', optimize=optimize)
                else:  # webp
                    img.save(new_filepath, 'WEBP', quality=quality)
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to process {filepath}: {e}")
        
        messagebox.showinfo("Success", "Images processed successfully")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageToolsApp(root)
    root.mainloop()
