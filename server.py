#!/usr/bin/env python3
"""
Sphere Robot Dashboard Server
Run: sudo python3 server.py
Open: http://<PI_IP>:5000

Hardware:
  Motors  — L298N via lgpio
  Camera  — Pi Camera (picamera2)
  IMU     — MPU6050 via I2C (simulated if absent)
  Gas     — MQ4/MQ7 via ADS1115 (simulated if absent)
"""

import time, threading, io, math, logging, struct
import lgpio
from flask import Flask, Response, render_template
from flask_socketio import SocketIO, emit

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
log = logging.getLogger("SphereBot")

# ═══════════════════════════════════════════════
#  PIN CONFIG  (BCM)
# ═══════════════════════════════════════════════
ENA=12; IN1=20; IN2=21
ENB=13; IN3=5;  IN4=6

# ═══════════════════════════════════════════════
#  MOTOR SETUP
# ═══════════════════════════════════════════════
h = lgpio.gpiochip_open(4)
for pin in [ENA, IN1, IN2, ENB, IN3, IN4]:   # claim ALL including PWM pins first
    lgpio.gpio_claim_output(h, pin, 0)

SPEED = 70   # default %

lgpio.tx_pwm(h, ENA, 1000, SPEED)
lgpio.tx_pwm(h, ENB, 1000, SPEED)

def motor_a(d):
    lgpio.gpio_write(h, IN1, 1 if d=='fwd' else 0)
    lgpio.gpio_write(h, IN2, 1 if d=='bwd' else 0)

def motor_b(d):
    lgpio.gpio_write(h, IN3, 1 if d=='fwd' else 0)
    lgpio.gpio_write(h, IN4, 1 if d=='bwd' else 0)

def stop():
    motor_a('stop'); motor_b('stop')

def drive(cmd, speed=None):
    global SPEED
    spd = speed if speed else SPEED
    lgpio.tx_pwm(h, ENA, 1000, spd)
    lgpio.tx_pwm(h, ENB, 1000, spd)
    if   cmd == 'forward':  motor_a('fwd'); motor_b('fwd')
    elif cmd == 'backward': motor_a('bwd'); motor_b('bwd')
    elif cmd == 'left':     motor_a('bwd'); motor_b('fwd')
    elif cmd == 'right':    motor_a('fwd'); motor_b('bwd')
    else:                   stop()
    log.info(f"Drive: {cmd} @ {spd}%")

log.info("Motors ready")

# ═══════════════════════════════════════════════
#  CAMERA SETUP
# ═══════════════════════════════════════════════
try:
    from picamera2 import Picamera2
    from picamera2.encoders import MJPEGEncoder
    from picamera2.outputs import FileOutput

    class CamOutput(io.BufferedIOBase):
        def __init__(self):
            self.frame = None
            self.cond  = threading.Condition()
        def write(self, buf):
            with self.cond:
                self.frame = buf
                self.cond.notify_all()

    picam2     = Picamera2()
    cam_output = CamOutput()
    picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
    picam2.start_recording(MJPEGEncoder(), FileOutput(cam_output))
    CAMERA_OK = True
    log.info("Camera ready")

except Exception as e:
    CAMERA_OK  = False
    cam_output = None
    log.warning(f"Camera unavailable: {e}")

def gen_frames():
    while True:
        if not CAMERA_OK or cam_output is None:
            time.sleep(0.1); continue
        with cam_output.cond:
            cam_output.cond.wait()
            frame = cam_output.frame
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# ═══════════════════════════════════════════════
#  IMU — MPU6050 (I2C 0x68)
# ═══════════════════════════════════════════════
try:
    import smbus2
    bus      = smbus2.SMBus(1)
    IMU_ADDR = 0x68
    bus.write_byte_data(IMU_ADDR, 0x6B, 0)   # wake up
    IMU_OK = True
    log.info("MPU6050 ready")
except Exception as e:
    IMU_OK = False
    log.warning(f"IMU unavailable (simulating): {e}")

def read_word(reg):
    hi = bus.read_byte_data(IMU_ADDR, reg)
    lo = bus.read_byte_data(IMU_ADDR, reg+1)
    val = (hi << 8) | lo
    return val - 65536 if val > 32767 else val

def read_imu():
    if IMU_OK:
        try:
            ax = read_word(0x3B) / 16384.0
            ay = read_word(0x3D) / 16384.0
            az = read_word(0x3F) / 16384.0
            gx = read_word(0x43) / 131.0
            gy = read_word(0x45) / 131.0
            gz = read_word(0x47) / 131.0
            roll  = math.degrees(math.atan2(ay, az))
            pitch = math.degrees(math.atan2(-ax, math.sqrt(ay**2 + az**2)))
            return {"roll": round(roll,1), "pitch": round(pitch,1),
                    "yaw": round(gz,1),
                    "ax": round(ax,2), "ay": round(ay,2), "az": round(az,2),
                    "ok": True}
        except:
            pass
    # Simulate gentle rocking when no IMU
    t = time.time()
    return {"roll":  round(math.sin(t*0.7)*8, 1),
            "pitch": round(math.sin(t*0.5)*5, 1),
            "yaw":   round(math.sin(t*0.3)*3, 1),
            "ax": 0.0, "ay": 0.0, "az": 1.0,
            "ok": False}

# ═══════════════════════════════════════════════
#  GAS SENSORS — ADS1115
# ═══════════════════════════════════════════════
try:
    import board, busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    i2c     = busio.I2C(board.SCL, board.SDA)
    ads     = ADS.ADS1115(i2c)
    mq4_ch  = AnalogIn(ads, ADS.P0)
    mq7_ch  = AnalogIn(ads, ADS.P1)
    GAS_OK  = True
    log.info("ADS1115 gas sensors ready")
except Exception as e:
    GAS_OK  = False
    log.warning(f"Gas sensors unavailable (simulating): {e}")

def read_gas():
    if GAS_OK:
        return {"mq4": round((mq4_ch.value/32767)*100, 1),
                "mq7": round((mq7_ch.value/32767)*100, 1), "ok": True}
    import random
    return {"mq4": round(random.uniform(4,12),1),
            "mq7": round(random.uniform(2,8),1), "ok": False}

# ═══════════════════════════════════════════════
#  FLASK + SOCKETIO
# ═══════════════════════════════════════════════
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sphere_v1'
sio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

@app.route('/')
def index(): return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame')

# ── Sensor broadcast thread ──────────────────
def broadcast_loop():
    while True:
        try:
            imu = read_imu()
            gas = read_gas()
            sio.emit('telemetry', {"imu": imu, "gas": gas})
        except Exception as e:
            log.error(f"Broadcast error: {e}")
        time.sleep(0.1)   # 10 Hz

threading.Thread(target=broadcast_loop, daemon=True).start()

# ── SocketIO events ──────────────────────────
@sio.on('connect')
def on_connect():
    log.info("Client connected")
    emit('init', {'speed': SPEED, 'camera': CAMERA_OK,
                  'imu': IMU_OK, 'gas': GAS_OK})

@sio.on('disconnect')
def on_disconnect():
    stop(); log.info("Client disconnected — motors stopped")

@sio.on('drive')
def on_drive(data):
    drive(data.get('cmd', 'stop'))

@sio.on('set_speed')
def on_speed(data):
    global SPEED
    SPEED = max(20, min(100, int(data.get('speed', 70))))
    log.info(f"Speed → {SPEED}%")
    emit('speed_ack', {'speed': SPEED})

# ═══════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════
if __name__ == '__main__':
    log.info("Sphere Dashboard starting on :5000")
    try:
        sio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        log.info("Shutting down")
    finally:
        stop()
        lgpio.gpiochip_close(h)
        if CAMERA_OK: picam2.stop_recording()
