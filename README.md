# 🌐 Sphere-Robot

A sphere-shaped autonomous robot built with Raspberry Pi 5, controlled via a real-time web dashboard. Features live motor control, MJPEG camera streaming, and gas sensor monitoring.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![ROS2](https://img.shields.io/badge/ROS2-Humble-orange?style=flat-square)
![Flask](https://img.shields.io/badge/Flask-SocketIO-green?style=flat-square)
![RPi](https://img.shields.io/badge/Raspberry%20Pi-5-red?style=flat-square&logo=raspberrypi)

---

## 📸 Demo

> Web dashboard with live camera feed, D-pad controls, speed slider, and motor status.

---

## 🤖 Hardware

| Component | Details |
|---|---|
| Compute | Raspberry Pi 5 |
| Motors | 2× 500 RPM DC Motors |
| Motor Driver | L298N Dual H-Bridge |
| Camera | Raspberry Pi Camera V2 (IMX219) |
| Gas Sensors | MQ-4 (Methane/LPG) + MQ-7 (CO) |
| ADC | PCF8591 / ADS1115 |
| Power | LiPo Battery + Buck Converter |

---

## 🔌 Wiring

### L298N Motor Driver
| L298N Pin | RPi 5 GPIO (BCM) |
|-----------|-----------------|
| ENA       | GPIO 12         |
| IN1       | GPIO 20         |
| IN2       | GPIO 21         |
| ENB       | GPIO 13         |
| IN3       | GPIO 5          |
| IN4       | GPIO 6          |

### Gas Sensors (via PCF8591 ADC)
| PCF8591 | RPi 5 |
|---------|-------|
| VCC     | 3.3V  |
| GND     | GND   |
| SDA     | GPIO 2|
| SCL     | GPIO 3|
| AIN0    | MQ-4 AOUT |
| AIN1    | MQ-7 AOUT |

---

## 📁 Project Structure

```
Sphere-Robot/
├── server.py          ← Flask-SocketIO server (run on Pi)
├── templates/
│   └── index.html     ← Web dashboard (auto-served)
└── README.md
```

---

## 🚀 Setup & Run

### 1. Install dependencies on Pi
```bash
pip3 install flask flask-socketio --break-system-packages
sudo apt install python3-picamera2 -y
```

### 2. Clone on Pi
```bash
git clone https://github.com/Aditya-ai-machinelearning/Sphere-Robot.git
cd Sphere-Robot
mkdir -p templates
mv index.html templates/
```

### 3. Run
```bash
sudo python3 server.py
```

### 4. Open dashboard
```
http://<PI_IP_ADDRESS>:5000
```

---

## 🎮 Controls

| Key / Button | Action    |
|--------------|-----------|
| W / ↑        | Forward   |
| S / ↓        | Backward  |
| A / ←        | Turn Left |
| D / →        | Turn Right|
| Space        | Stop      |
| Slider       | Speed %   |

---

## 🛠️ Tech Stack

- **Python 3** — main language
- **Flask + Flask-SocketIO** — web server + real-time communication
- **lgpio** — GPIO control on RPi 5
- **picamera2** — camera streaming
- **ROS2 Humble** — robotics middleware (laptop bridge)
- **HTML/CSS/JS** — dashboard frontend

---

## 📡 ROS2 Bridge

Run on your laptop to control via `/cmd_vel`:

```bash
source /opt/ros/humble/setup.bash
python3 ros2_bridge.py --pi-ip <PI_IP>
```

Topics:
- `/cmd_vel` → motor commands
- `/sphere/gas` → MQ4/MQ7 readings
- `/sphere/status` → robot status

---

## 🗺️ Roadmap

- [x] Motor control via web dashboard
- [x] Real-time WebSocket communication
- [x] Speed control
- [ ] Camera live feed (awaiting correct ribbon cable)
- [ ] MQ-4 / MQ-7 gas sensors via PCF8591
- [ ] MPU6050 IMU + 3D orientation display
- [ ] ROS2 bridge integration
- [ ] Autonomous obstacle avoidance
- [ ] GPS waypoint navigation

---

## 👨‍💻 Author

**Aditya** — EEE Student | Robotics & Physical AI Enthusiast  
Building towards an industrial Physical AI & Robotics company.

[![GitHub](https://img.shields.io/badge/GitHub-Aditya--ai--machinelearning-black?style=flat-square&logo=github)](https://github.com/Aditya-ai-machinelearning)
