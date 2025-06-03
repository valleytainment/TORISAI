# TORIS AI - GUI Automation Module
# Inspired by Agent-S gui_agents module but simplified for compatibility with 12GB RAM systems

import os
import time
import subprocess
import platform
import json
import base64
from PIL import Image, ImageGrab
import io
import sys  # Added missing import

class GUIAutomation:
    """
    GUI Automation for TORIS AI.
    Provides basic screen capture and mouse/keyboard control functionality.
    """
    
    def __init__(self, screenshots_dir="./screenshots"):
        """Initialize GUI automation with specified directories"""
        self.screenshots_dir = screenshots_dir
        self.ensure_directories()
        self._setup_platform_specific()
    
    def ensure_directories(self):
        """Ensure necessary directories exist"""
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    def _setup_platform_specific(self):
        """Setup platform-specific dependencies"""
        self.platform = platform.system()
        
        # Install platform-specific dependencies if needed
        if self.platform == "Windows":
            try:
                import pyautogui
                self.automation_lib = "pyautogui"
            except ImportError:
                print("Installing PyAutoGUI...")
                subprocess.run([sys.executable, "-m", "pip", "install", "pyautogui"], check=True)
                import pyautogui
                self.automation_lib = "pyautogui"
        
        elif self.platform == "Darwin":  # macOS
            try:
                import pyautogui
                self.automation_lib = "pyautogui"
            except ImportError:
                print("Installing PyAutoGUI...")
                subprocess.run([sys.executable, "-m", "pip", "install", "pyautogui"], check=True)
                import pyautogui
                self.automation_lib = "pyautogui"
        
        else:  # Linux
            try:
                import pyautogui
                self.automation_lib = "pyautogui"
            except ImportError:
                print("Installing PyAutoGUI...")
                subprocess.run([sys.executable, "-m", "pip", "install", "pyautogui"], check=True)
                import pyautogui
                self.automation_lib = "pyautogui"
    
    def capture_screen(self, region=None):
        """
        Capture the screen or a region of it
        
        Args:
            region (tuple, optional): Region to capture (left, top, width, height)
            
        Returns:
            str: Path to the saved screenshot
        """
        try:
            # Generate filename with timestamp
            timestamp = int(time.time())
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Capture screenshot
            if self.automation_lib == "pyautogui":
                import pyautogui
                if region:
                    screenshot = pyautogui.screenshot(region=region)
                else:
                    screenshot = pyautogui.screenshot()
                screenshot.save(filepath)
            
            return filepath
        except Exception as e:
            print(f"Error capturing screen: {str(e)}")
            return None
    
    def click(self, x, y, button="left", clicks=1):
        """
        Click at the specified coordinates
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            button (str): Mouse button ('left', 'right', 'middle')
            clicks (int): Number of clicks
            
        Returns:
            bool: Success status
        """
        try:
            if self.automation_lib == "pyautogui":
                import pyautogui
                pyautogui.click(x=x, y=y, button=button, clicks=clicks)
            return True
        except Exception as e:
            print(f"Error clicking: {str(e)}")
            return False
    
    def move_to(self, x, y):
        """
        Move mouse to the specified coordinates
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            
        Returns:
            bool: Success status
        """
        try:
            if self.automation_lib == "pyautogui":
                import pyautogui
                pyautogui.moveTo(x, y)
            return True
        except Exception as e:
            print(f"Error moving mouse: {str(e)}")
            return False
    
    def type_text(self, text, interval=0.01):
        """
        Type text at the current cursor position
        
        Args:
            text (str): Text to type
            interval (float): Interval between keystrokes
            
        Returns:
            bool: Success status
        """
        try:
            if self.automation_lib == "pyautogui":
                import pyautogui
                pyautogui.write(text, interval=interval)
            return True
        except Exception as e:
            print(f"Error typing text: {str(e)}")
            return False
    
    def press_key(self, key):
        """
        Press a key
        
        Args:
            key (str): Key to press
            
        Returns:
            bool: Success status
        """
        try:
            if self.automation_lib == "pyautogui":
                import pyautogui
                pyautogui.press(key)
            return True
        except Exception as e:
            print(f"Error pressing key: {str(e)}")
            return False
    
    def hotkey(self, *keys):
        """
        Press a combination of keys
        
        Args:
            *keys: Keys to press
            
        Returns:
            bool: Success status
        """
        try:
            if self.automation_lib == "pyautogui":
                import pyautogui
                pyautogui.hotkey(*keys)
            return True
        except Exception as e:
            print(f"Error pressing hotkey: {str(e)}")
            return False
    
    def find_image_on_screen(self, image_path, confidence=0.9):
        """
        Find an image on the screen
        
        Args:
            image_path (str): Path to the image file
            confidence (float): Confidence threshold (0-1)
            
        Returns:
            tuple: (x, y) coordinates of the center of the found image, or None if not found
        """
        try:
            if self.automation_lib == "pyautogui":
                import pyautogui
                location = pyautogui.locateOnScreen(image_path, confidence=confidence)
                if location:
                    return pyautogui.center(location)
            return None
        except Exception as e:
            print(f"Error finding image: {str(e)}")
            return None
    
    def scroll(self, clicks, x=None, y=None):
        """
        Scroll the mouse wheel
        
        Args:
            clicks (int): Number of clicks (positive for up, negative for down)
            x (int, optional): X coordinate
            y (int, optional): Y coordinate
            
        Returns:
            bool: Success status
        """
        try:
            if self.automation_lib == "pyautogui":
                import pyautogui
                pyautogui.scroll(clicks, x, y)
            return True
        except Exception as e:
            print(f"Error scrolling: {str(e)}")
            return False
    
    def get_screen_size(self):
        """
        Get the screen size
        
        Returns:
            tuple: (width, height) of the screen
        """
        try:
            if self.automation_lib == "pyautogui":
                import pyautogui
                return pyautogui.size()
            return None
        except Exception as e:
            print(f"Error getting screen size: {str(e)}")
            return None

# Example usage
if __name__ == "__main__":
    gui = GUIAutomation()
    screenshot_path = gui.capture_screen()
    print(f"Screenshot saved to: {screenshot_path}")
    screen_size = gui.get_screen_size()
    print(f"Screen size: {screen_size}")
