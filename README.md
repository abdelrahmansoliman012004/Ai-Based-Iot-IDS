# 🚀 AI-Based IoT Intrusion Detection System (IDS)

An AI-based Intrusion Detection System designed for **IoT and Cyber-Physical Systems (CPS)** environments.
The system uses **machine learning** to detect malicious network behavior such as **DoS**, **MITM**, and **Data Injection attacks** through simulated traffic and real-time analysis.

---

## 📌 Project Overview

IoT networks suffer from limited resources, heterogeneous devices, and large attack surfaces, making traditional rule-based security mechanisms insufficient.
This project proposes an **AI-based IDS** that leverages a **Random Forest classifier** trained on network traffic features to distinguish between **normal and malicious packets**.

The IDS integrates:

* Attack simulation
* Machine learning-based detection
* A Flask web dashboard for monitoring and interaction

---

## 🎯 Objectives

* Study common security threats in IoT-based CPS environments
* Design an AI-based IDS capable of detecting evolving attacks
* Simulate realistic IoT attacks (DoS, MITM, Data Injection)
* Evaluate detection performance and system limitations

---

## 🧠 Detection Capabilities

| Attack Type        | Description                                    |
| ------------------ | ---------------------------------------------- |
| **DoS**            | Flooding and abnormal traffic behavior         |
| **MITM**           | Interception and manipulation of communication |
| **Data Injection** | Tampering with transmitted data                |

📊 **Detection Rate:**
The system detects approximately **45–50% of malicious packets** in real-time simulations
(e.g., detecting ~50 malicious packets out of 100 packets per second).

---

## ⚙️ System Architecture

The IDS follows a layered IoT–CPS architecture:

* **IoT Devices & Sensors**
* **Edge Devices & Gateways**
* **Secure Communication (TLS/SSL, MQTT, HTTP)**
* **Attack Simulation Layer**
* **AI-Based Detection Engine**
* **Flask Web Dashboard**

> The full system architecture diagram is included in the project report and presentation.

---

## 🧰 Technology Stack

| Component            | Technology                   |
| -------------------- | ---------------------------- |
| Programming Language | Python                       |
| Machine Learning     | Scikit-Learn (Random Forest) |
| Dataset              | NSL-KDD (processed)          |
| Web Framework        | Flask                        |
| Frontend             | HTML, CSS, JavaScript        |
| Visualization        | Console logs + dashboard UI  |

---

## 📁 Project Structure

```
Ai-Based-Iot-IDS/
│
├── Source/
│   ├── preprocessing.py
│   ├── model.py
│   ├── attack_simulation.py
│
├── static/
│   └── style.css
│
├── templates/
│   └── index.html
│
├── flask_app.py
├── classification_report.txt
├── README.md
└── .gitignore
```

---

## ▶️ How to Run the Project

1. **Create virtual environment**

```bash
python -m venv env
env\Scripts\activate
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Run the Flask application**

```bash
python flask_app.py
```

4. Open browser:

```
http://127.0.0.1:5000
```

---

## 📊 Evaluation & Results

* Model trained on processed NSL-KDD features
* Detection rate: **~45–50%**
* Works in real-time simulation
* Demonstrates feasibility of AI-based IDS in IoT environments

---

## ⚠️ Limitations

* Detection rate is moderate due to:

  * Synthetic traffic generation
  * Dataset imbalance
  * Simplified attack simulation
* No deployment on real IoT hardware
* Latency and scalability not fully evaluated

---

## 🔮 Future Work

* Improve detection rate using data augmentation
* Explore deep learning or hybrid IDS models
* Deploy on edge devices (Raspberry Pi, ESP32)
* Add real-time network packet capture
* Enhance dashboard with advanced analytics

---

## 📄 Academic Context

This project was developed as part of a **Cyber-Physical Systems / IoT Security course**, following IEEE research structure and evaluation methodology.
