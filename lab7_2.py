import socket
import RPi.GPIO as GPIO

# --- GPIO Setup ---

GPIO.setwarnings(False)
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
led_pins = {'led1': 17, 'led2': 27, 'led3': 22}

# Set up PWM for each LED
led_pwms = {}
led_brightness = {}

for name, pin in led_pins.items():
    try:
        GPIO.setup(pin, GPIO.OUT)
        pwm = GPIO.PWM(pin, 1000)  # 1 kHz frequency
        pwm.start(0)
        led_pwms[name] = pwm
        led_brightness[name] = 0
    except Exception as e:
        print(f"Error initializing {name} on pin {pin}: {e}")

# --- Helper function to parse POST data ---
def parsePOSTdata(request):
    post_data = {}
    try:
        # Split by two CRLFs to isolate body from headers
        body = request.split("\r\n\r\n", 1)[1]
        pairs = body.split("&")
        for pair in pairs:
            if "=" in pair:
                key, val = pair.split("=")
                post_data[key] = val
    except Exception:
        pass
    return post_data

# --- Web Page HTML + JavaScript ---
def web_page():
    return """<!DOCTYPE html>
<html>
<head>
  <title>LED Brightness Control</title>
  <style>
    body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background-color: #f5f5f5; }
    h2 { color: #333; }
    .slider-container { margin: 20px auto; width: 60%; background: #fff; padding: 15px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
    input[type=range] { width: 80%; }
    .label { font-weight: bold; }
  </style>
  <script>
    function updateBrightness(led, value) {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", "/", true);
      xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
      xhr.send("led=" + led + "&brightness=" + value);
      document.getElementById("val_" + led).textContent = value;
    }
  </script>
</head>
<body>
  <h2>LED Brightness Control</h2>

  <div class="slider-container">
    <div class="label">LED 1: <span id="val_led1">0</span>%</div>
    <input type="range" min="0" max="100" value="0"
           oninput="updateBrightness('led1', this.value)">
  </div>

  <div class="slider-container">
    <div class="label">LED 2: <span id="val_led2">0</span>%</div>
    <input type="range" min="0" max="100" value="0"
           oninput="updateBrightness('led2', this.value)">
  </div>

  <div class="slider-container">
    <div class="label">LED 3: <span id="val_led3">0</span>%</div>
    <input type="range" min="0" max="100" value="0"
           oninput="updateBrightness('led3', this.value)">
  </div>
</body>
</html>"""

# --- Main Server Function ---
def serve_web_page():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 8080))  # Use 8080 instead of 80 (avoids permission issues)
    s.listen(5)
    print("Server started. Access at: http://<raspberrypi_ip>:8080")

    try:
        while True:
            conn, addr = s.accept()
            print(f"Connection from {addr[0]}")
            request = conn.recv(1024).decode('utf-8')

            if not request:
                conn.close()
                continue

            # Handle POST request
            if request.startswith('POST'):
                data_dict = parsePOSTdata(request)
                led_choice = data_dict.get('led', '')
                brightness = int(data_dict.get('brightness', 0))
                if led_choice in led_pwms:
                    led_pwms[led_choice].ChangeDutyCycle(brightness)
                    led_brightness[led_choice] = brightness
                    print(f"{led_choice} → {brightness}%")

                response = "HTTP/1.1 204 No Content\r\n\r\n"  # No page reload
            else:
                html = web_page()
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html

            conn.send(response.encode())
            conn.close()

    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        for pwm in led_pwms.values():
            pwm.stop()
        GPIO.cleanup()
        s.close()

# --- Run the server ---
if __name__ == "__main__":
    serve_web_page()
