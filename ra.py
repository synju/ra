import cv2
import tkinter as tk
from tkinter import Label, Menu, Canvas
from PIL import Image, ImageTk
import json
import os

# Get the directory of the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the settings file in the same directory as the script
SETTINGS_FILE = os.path.join(SCRIPT_DIR, "settings.json")


class WebcamApp:
	def __init__(self, window, window_title):
		self.window = window
		self.window.title(window_title)

		self.video_source = 0
		self.vid = cv2.VideoCapture(self.video_source)

		# Set the video aspect ratio (width:height)
		self.aspect_ratio = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH) / self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

		# Initialize the always on top state and flip state
		self.always_on_top = False
		self.flip_horizontally = False

		# Load previous window size, position, always on top, and flip state
		self.load_window_settings()

		# Initialize width and height after window is displayed
		self.window.update_idletasks()
		self.width = self.window.winfo_width()
		self.height = self.window.winfo_height()

		# Apply the always on top setting after loading
		self.window.attributes("-topmost", self.always_on_top)

		# Create a canvas to display the video with a black background
		self.canvas = Canvas(self.window, bg="black")
		self.canvas.pack(expand=True, fill=tk.BOTH)

		# Bind the window resize and move event to update settings
		self.window.bind('<Configure>', self.resize_event)

		# Bind right-click event to show context menu
		self.canvas.bind("<Button-3>", self.show_context_menu)

		# Bind the Escape key to close the application
		self.window.bind("<Escape>", lambda event: self.on_closing())

		# Allow resizing of the window manually
		self.window.resizable(True, True)

		# Start the video loop
		self.update()

		# Create a context menu for right-click
		self.context_menu = Menu(self.window, tearoff=0)
		self.context_menu.add_command(label=self.get_always_on_top_label(), command=self.toggle_always_on_top)
		self.context_menu.add_command(label=self.get_flip_label(), command=self.toggle_flip)
		self.context_menu.add_separator()
		self.context_menu.add_command(label="Exit", command=self.on_closing)

		self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
		self.window.mainloop()

	def load_window_settings(self):
		"""Load window size, position, always on top, and flip state from settings.json."""
		if os.path.exists(SETTINGS_FILE):
			with open(SETTINGS_FILE, "r") as f:
				settings = json.load(f)
				width = settings.get("width", 800)
				height = settings.get("height", 600)
				x = settings.get("x", 100)
				y = settings.get("y", 100)
				self.always_on_top = settings.get("always_on_top", False)  # Load always on top state
				self.flip_horizontally = settings.get("flip_horizontally", False)  # Load flip state
				self.window.geometry(f"{width}x{height}+{x}+{y}")
		else:
			# Default size, position, and always on top setting
			self.window.geometry("800x600+100+100")
			self.always_on_top = False
			self.flip_horizontally = False

	def save_window_settings(self):
		"""Save current window size, position, always on top, and flip state to settings.json."""
		settings = {
			"width": self.window.winfo_width(),
			"height": self.window.winfo_height(),
			"x": self.window.winfo_x(),
			"y": self.window.winfo_y(),
			"always_on_top": self.always_on_top,  # Save always on top state
			"flip_horizontally": self.flip_horizontally  # Save flip state
		}
		with open(SETTINGS_FILE, "w") as f:
			json.dump(settings, f, indent=4)

	def resize_event(self, event):
		"""Handles the window resize and maintains video aspect ratio."""
		self.width = self.window.winfo_width()
		self.height = self.window.winfo_height()

		# Save the window position, size, always on top, and flip state every time it's resized or moved
		self.save_window_settings()

	def show_context_menu(self, event):
		# Update the labels for "Always on Top" and "Flip Horizontally" before showing the menu
		self.context_menu.entryconfig(0, label=self.get_always_on_top_label())
		self.context_menu.entryconfig(1, label=self.get_flip_label())

		# Display the context menu at the location of the mouse click
		self.context_menu.post(event.x_root, event.y_root)

	def toggle_always_on_top(self):
		# Toggle the "always on top" feature
		self.always_on_top = not self.always_on_top
		self.window.attributes("-topmost", self.always_on_top)

		# Save the new always on top state immediately
		self.save_window_settings()

	def toggle_flip(self):
		# Toggle the flip horizontally feature
		self.flip_horizontally = not self.flip_horizontally

		# Save the new flip state immediately
		self.save_window_settings()

	def get_always_on_top_label(self):
		# Return the label for "Always on Top" with its current state
		state = "Enabled" if self.always_on_top else "Disabled"
		return f"Always on Top ({state})"

	def get_flip_label(self):
		# Return the label for "Flip Horizontally" with its current state
		state = "Enabled" if self.flip_horizontally else "Disabled"
		return f"Flip Horizontally ({state})"

	def update(self):
		ret, frame = self.vid.read()
		if ret:
			# Flip the frame horizontally if the setting is enabled
			if self.flip_horizontally:
				frame = cv2.flip(frame, 1)

			# Get the size of the window
			window_width = self.canvas.winfo_width()
			window_height = self.canvas.winfo_height()

			# Calculate the video frame size that fits within the window while maintaining aspect ratio
			video_width = window_width
			video_height = int(video_width / self.aspect_ratio)

			if video_height > window_height:
				video_height = window_height
				video_width = int(video_height * self.aspect_ratio)

			# Ensure the video dimensions are never less than 1 (to avoid OpenCV errors)
			video_width = max(1, video_width)
			video_height = max(1, video_height)

			# Resize the frame to fit the calculated size
			frame = cv2.resize(frame, (video_width, video_height))

			# Convert the image to RGB (OpenCV uses BGR)
			frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

			# Convert the image to a format Tkinter can handle
			img = Image.fromarray(frame)
			imgtk = ImageTk.PhotoImage(image=img)

			# Clear the canvas and draw the resized video centered
			self.canvas.delete("all")
			x_center = (window_width - video_width) // 2
			y_center = (window_height - video_height) // 2
			self.canvas.create_image(x_center, y_center, anchor=tk.NW, image=imgtk)
			self.canvas.imgtk = imgtk

		# Continue the loop if the window is still open
		if self.vid.isOpened():
			self.window.after(10, self.update)

	def on_closing(self):
		# Stop the video capture and close the window
		if self.vid.isOpened():
			self.vid.release()

		# Save the current window settings
		self.save_window_settings()

		# Close the window
		self.window.destroy()


# Create the main window
window = tk.Tk()
app = WebcamApp(window, "Eye of Ra")
