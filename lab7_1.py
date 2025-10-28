import socket
import RPi.GPIO as GPIO


GPIO.setmode(GPIO.BCM)
led_pins = {'a':17, 'b':27, 'c':22}

led_pwms={}
for key, pin in led_pins.items():
    GPIO.setup(pin,GPIO.OUT)
    pwm = GPIO.PWM(pin,1000)
    pwm.start(0) #all leds initially off
    led_pwms[key] = pwm
led_brightness = {'a':0, 'b':0, 'c':0}

def parsePOSTdata(data): #copied from gitghub repo
    data_dict = {}
    idx = data.find('\r\n\r\n')+4
    data = data[idx:]
    data_pairs = data.split('&')
    for pair in data_pairs:
        key_val = pair.split('=')
        if len(key_val) == 2:
            data_dict[key_val[0]] = key_val[1]
    return data_dict

def ledwebpage():
    return f"""\
<html>
  <body>
      <h2>Lab7 part1</h2>
      <h3>Brightness level:</h3>
      <form method = "POST">
        <label for="slider1">Brightness level (0-100):</label><br>
        <input type = "range" id ="slider1" name ="slider1" min = "0" max = "100" value = "50"/><br><br>

        <h3>Select LED:</h3>
        <form action="/cgi-bin/radio.py" method ="POST">
        <input type ="radio" name="option" value="a" checked> LED 1 <br>
        <input type ="radio" name="option" value="b" > LED 2 <br>
        <input type ="radio" name="option" value="c" > LED 3 <br><br>
        
        <button type="submit">Change Brightness</button>
    </form>
    <h3>Current Brightness Level:</h3>
    <p>LED 1: {led_brightness['a']}%</p>
    <p>LED 2: {led_brightness['b']}%</p>
    <p>LED 3: {led_brightness['c']}%</p>
  </body>
</html>
"""



def serve_web_page():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP-IP socket
    s.bind(('', 80))
    s.listen(3)  # up to 3 queued connections
    try:
        while True:
            print('Waiting for connection...')
            conn, (client_ip, client_port) = s.accept()     # blocking call
            request = conn.recv(1024).decode('utf-8')
            print(f'Connection from {client_ip}')

            if reqeust.startswith('POST'):
            	data_dict = parsePOSTdata(request)
            	led_choice = data_dict.get('option','a')
            	brightness = int(data_dict.get('slider1',0))

            	if led_choice in led_pwms:
            		led_brightness[led_choice] = brightness
            		led_pwms[led_choice].ChangeDutyCycle(brightness)
            conn.send(b'HTTP/1.1 200 OK\n')         # status line
            conn.send(b'Content-type: text/html\n') # header (content type)
            conn.send(b'Connection: close\r\n\r\n') # header (tell client to close at end)
            # send body in try block in case connection is interrupted:
            try:
                conn.sendall(web_page()).encode('utf-8')                  # body
            finally:
                conn.close()                
    except KeyboardInterrupt:
    	print("Server stopped")
    finally:
    	for pwm in led_pwms.values():
    		pwm.stop()
    	GPIO.cleanuo()
    	s.close()

if __name__ == '__main__'
    serve_web_page()
