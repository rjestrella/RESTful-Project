import socket
import subprocess
import RPi.GPIO as GPIO
from flask import Flask, render_template
app = Flask(__name__)

proc = None
GPIO.setwarnings(False)
dutycycle = 90
dutycycle1 = 90
GPIO.setmode(GPIO.BCM)
GPIO.setup(18,GPIO.OUT)

pwm = GPIO.PWM(18,100)
pwm.start(90)

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

@app.route("/")
def hello():
    return render_template("index.html")

@app.route("/startmotion", methods=['POST'])
def start_motion():
    global proc
    print(" > Motion Alerts Enabled")
    proc = subprocess.Popen(["python", "core.py", "-c", "conf.json"])
    print(" > Process id {}".format(proc.pid))
    return "Enabled"

@app.route("/stopmotion", methods=['POST'])
def stop_motion():
    global proc
    print(" > Motion Alerts Disabled")
    proc.kill()
    print(" > Process {} killed!".format(proc.pid))
    return "Disabled"

@app.route("/startlive", methods=['GET', 'POST'])
def start_live():
    global proc
    proc = subprocess.Popen(["bash", "stream_video.sh"])
    print(" > Live Stream enabled")
    return "LIVE ENABLED"

@app.route("/stoplive", methods=['GET', 'POST'])
def stop_live():
    global proc
    proc = subprocess.Popen(["killall", "mjpg_streamer"])
    print(" > Live Stream stopped")
    return "LIVE DISABLED"   

@app.route("/left", methods=['POST'])
def update_left():
    global dutycycle
    dutycycle = dutycycle + 5
    duty = float(dutycycle)/10.0 + 2.5
    pwm.ChangeDutyCycle(duty)
    print(" > Rotating Camera Left")
    return "LEFT"

@app.route("/center", methods=['POST'])
def center():
    global dutycycle
    pwm.ChangeDutyCycle(90)
    print(" > Centering Camera")
    return "CENTER"

@app.route("/right", methods=['POST'])
def update_right():
    global dutycycle1
    dutycycle1 = dutycycle1 - 5
    duty1 = float(dutycycle1)/10.0 + 2.5
    pwm.ChangeDutyCycle(duty1)
    print(" > Rotation Camera Right")
    return "RIGHT"

@app.route("/status", methods=['GET', 'POST'])
def status_update():
    global proc
    if proc is None:
        print(" > Server is IDLE")
        return "IDLE"
    elif proc.poll() is None:
        print(" > Server is running (Process {})!".format(proc.pid))
        return "PROCESSING"
    else:
        print(" > Server is IDLE")
        return "IDLE"

if __name__ == "__main__":
    print "Connect to http://{}:5555 to view web interface".format(get_ip_address())
    app.run(host="0.0.0.0", port=5555, debug=False)

