import random
import time
import pandas as pd
import numpy as np
from joblib import load
from Source.preprocessing import column_names, numerical_cols, categorical_cols
import threading
from datetime import datetime

# Global thread-safe log list (shared with Flask)
detection_logs = []

# Load the pre-trained model and preprocessor
try:
    model = load('model.pkl')
    preprocessor = load('preprocessor.pkl')
    print("Model and preprocessor loaded successfully.")
except Exception as e:
    print(f"Warning: Failed to load model/preprocessor: {e}. Using mock predictions for simulation.")
    model = None
    preprocessor = None

CLASS_MAP = {0: 'normal', 1: 'DoS', 2: 'MITM', 3: 'Data Injection'}

def log_message(message):
    """Thread-safe log append with timestamp."""
    timestamp = datetime.now().strftime("%I:%M:%S %p")
    full_msg = f"{timestamp}: {message}"
    detection_logs.append(full_msg)
    print(full_msg)

def create_raw_packet(is_malicious, attack_type='dos'):
    """
    Generate raw feature dict mimicking NSL-KDD data (41 features only).
    FIXED: Extreme features for malicious to match NSL-KDD patterns (high counts/errors for DoS, diversity for MITM, corruption for Injection).
    """
    raw = {}
    
    # Common settings
    raw['duration'] = 0 if is_malicious else random.randint(0, 100)
    raw['protocol_type'] = random.choice(['tcp', 'udp', 'icmp']) if not is_malicious else ('tcp' if attack_type == 'dos' else 'tcp')
    raw['service'] = random.choice(['http', 'private', 'telnet', 'ftp_data', 'domain_u', 'eco_i', 'other']) if not is_malicious else ('http' if attack_type == 'dos' else 'other')
    raw['flag'] = random.choice(['SF', 'REJ', 'SH', 'RSTR', 'S3']) if not is_malicious else ('REJ' if attack_type == 'dos' else ('RSTR' if attack_type == 'data_injection' else 'REJ'))
    
    # Bytes (low for floods/probes; FIXED: 0 for malicious floods)
    raw['src_bytes'] = random.randint(1, 2000) if not is_malicious else 0
    raw['dst_bytes'] = random.randint(0, 2000) if not is_malicious else 0
    
    # Binary features (elevated for MITM/Injection; FIXED: 3+ for hijack/tamper)
    binary_features = ['land', 'wrong_fragment', 'urgent', 'num_failed_logins', 'logged_in', 
                       'num_compromised', 'root_shell', 'su_attempted', 'num_root', 
                       'num_file_creations', 'num_shells', 'num_access_files', 
                       'num_outbound_cmds', 'is_host_login', 'is_guest_login']
    for col in binary_features:
        if col == 'num_failed_logins' and is_malicious:
            raw[col] = random.randint(3, 5) if attack_type in ['mitm', 'data_injection'] else 0  # FIXED: High for hijack/tamper
        else:
            raw[col] = random.choice([0, 1]) if not is_malicious else 0
    
    # Hot (low for both)
    raw['hot'] = random.randint(0, 5) if not is_malicious else 0
    
    # Counts (FIXED: High for DoS flood 500+, medium 200+ for MITM/Injection)
    if attack_type == 'dos':
        raw['count'] = random.randint(500, 511) if is_malicious else random.randint(1, 100)
        raw['srv_count'] = random.randint(1, 10) if is_malicious else random.randint(1, 50)
    else:
        raw['count'] = random.randint(200, 300) if is_malicious else random.randint(1, 100)
        raw['srv_count'] = random.randint(1, 5) if is_malicious else random.randint(1, 50)
    
    # Error rates (FIXED: 1.0 for DoS SYN, 0.8-1.0 for MITM/Injection corruption)
    if attack_type == 'dos':
        raw['serror_rate'] = 1.0 if is_malicious else round(random.uniform(0, 0.5), 2)
        raw['srv_serror_rate'] = 1.0 if is_malicious else round(random.uniform(0, 1), 2)
        raw['rerror_rate'] = 1.0 if is_malicious else round(random.uniform(0, 0.5), 2)
        raw['srv_rerror_rate'] = 1.0 if is_malicious else round(random.uniform(0, 1), 2)
    else:
        raw['serror_rate'] = round(random.uniform(0.8, 1.0), 2) if is_malicious else round(random.uniform(0, 0.5), 2)
        raw['srv_serror_rate'] = round(random.uniform(0.8, 1.0), 2) if is_malicious else round(random.uniform(0, 1), 2)
        raw['rerror_rate'] = round(random.uniform(0.7, 1.0), 2) if is_malicious else round(random.uniform(0, 0.5), 2)
        raw['srv_rerror_rate'] = round(random.uniform(0.8, 1.0), 2) if is_malicious else round(random.uniform(0, 1), 2)
    
    # Rates (FIXED: Low same_srv 0.01 for DoS, high diff_srv 0.9 for MITM/Injection scanning)
    if attack_type == 'dos':
        raw['same_srv_rate'] = round(random.uniform(0.01, 0.05), 2) if is_malicious else round(random.uniform(0.5, 1), 2)
        raw['diff_srv_rate'] = 0.0 if is_malicious else round(random.uniform(0, 0.5), 2)
        raw['srv_diff_host_rate'] = 0.0 if is_malicious else round(random.uniform(0, 0.2), 2)
    else:
        raw['same_srv_rate'] = round(random.uniform(0.1, 0.3), 2) if is_malicious else round(random.uniform(0.5, 1), 2)
        raw['diff_srv_rate'] = round(random.uniform(0.9, 1.0), 2) if is_malicious else round(random.uniform(0, 0.5), 2)
        raw['srv_diff_host_rate'] = round(random.uniform(0.4, 0.6), 2) if is_malicious else round(random.uniform(0, 0.2), 2)
    
    # Host counts (FIXED: 255 for DoS flood, high 200+ for MITM/Injection)
    raw['dst_host_count'] = 255 if attack_type == 'dos' and is_malicious else random.randint(100, 255)
    raw['dst_host_srv_count'] = random.randint(1, 255) if not is_malicious else (1 if attack_type == 'dos' else random.randint(200, 255))
    raw['dst_host_same_srv_rate'] = 1.0 if attack_type == 'dos' and is_malicious else round(random.uniform(0, 1), 2)
    
    # Data Injection specific alterations (FIXED: High corruption)
    if attack_type == 'data_injection' and is_malicious:
        raw['src_bytes'] = int(raw['src_bytes'] * random.uniform(2.0, 4.0))  # Inflated
        raw['dst_bytes'] = int(raw['dst_bytes'] * random.uniform(0.1, 0.5))  # Corrupted
        raw['flag'] = 'RSTR'
        raw['num_failed_logins'] = random.randint(4, 6)
        raw['serror_rate'] = 1.0
        raw['diff_srv_rate'] = 1.0
    
    # Fill remaining with defaults
    for col in column_names[:-1]:
        if col not in raw:
            if col in categorical_cols:
                raw[col] = 'tcp' if col == 'protocol_type' else 'http' if col == 'service' else 'SF'
            else:
                raw[col] = 0.0 if 'rate' in col or 'error' in col else 0
    
    return raw

def classify_attack(packet, attack_type='dos'):
    """
    Classify the packet and identify attack type using multi-class model.
    """
    
    try:
        is_malicious = packet == 'malicious'
        raw_features = create_raw_packet(is_malicious, attack_type)
        
        # Create DataFrame and align to 41 features (exclude label)
        new_df = pd.DataFrame([raw_features])
        new_df = new_df.reindex(columns=column_names[:-1], fill_value=0)
        
        # FIXED: Dtypes to prevent NaN in transform
        new_df[numerical_cols] = new_df[numerical_cols].fillna(0).astype(float)
        new_df[categorical_cols] = new_df[categorical_cols].fillna('unknown').astype(str)
        
        # Apply preprocessor
        processed_features = preprocessor.transform(new_df)
        
        # Predict multi-class
        prediction = model.predict(processed_features)[0]
        attack_type_detected = CLASS_MAP[prediction]
        confidence = model.predict_proba(processed_features)[0].max()
        log_message(f"Attack detected: {attack_type_detected} ({attack_type.upper()} confidence: {confidence:.2f})")
        return attack_type_detected
    except Exception as e:
        log_message(f"Classification error for {attack_type}: {str(e)} - Treating as normal.")
        return 'normal'

def simulate_attack_thread(display_name, code_type):
    """Generic thread runner for simulations."""
    log_message(f"Starting {display_name} attack simulation...")
    malicious_detected = 0
    for i in range(100):
        packet = random.choice(["valid", "malicious"])
        log_message(f"Sending {packet} packet {i+1}...")
        
        attack_result = classify_attack(packet, code_type)
        if attack_result != 'normal':
            malicious_detected += 1
            log_message(f"{attack_result.upper()} packet detected! (Total detected: {malicious_detected})")
        
        time.sleep(0.5)
        
        if malicious_detected >= 50:
            log_message("Multiple malicious packets detected, stopping simulation...")
            break
    log_message(f"{display_name} attack simulation ended. {malicious_detected}/100 packets processed ({malicious_detected} malicious detections).")

def simulate_dos_attack():
    """DoS simulation - starts thread."""
    threading.Thread(target=simulate_attack_thread, args=('DoS', 'dos'), daemon=True).start()

def simulate_mitm_attack():
    """MITM simulation - starts thread."""
    threading.Thread(target=simulate_attack_thread, args=('MITM', 'mitm'), daemon=True).start()

def simulate_data_injection_attack():
    """Data Injection simulation - starts thread."""
    threading.Thread(target=simulate_attack_thread, args=('Data Injection', 'data_injection'), daemon=True).start()

if __name__ == "__main__":
    simulate_dos_attack()
    simulate_mitm_attack()
    simulate_data_injection_attack()
    time.sleep(60)  # Wait for demo