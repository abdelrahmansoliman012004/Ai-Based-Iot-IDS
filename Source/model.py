import random 
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_curve
import joblib
import numpy as np
import json
from Source.preprocessing import preprocess_data, column_names, numerical_cols, categorical_cols
import pandas as pd

def train_model():
    # Preprocess
    X_train, X_test, y_train, y_test, preprocessor = preprocess_data()

    # FIXED: Add 10k synthetic malicious samples (extreme/varied for >90% detection)
    synthetic_X = []
    synthetic_y = []
    for _ in range(10000 // 3):  # ~3333 per class
        # Synthetic DoS (extreme flood: count=510, serror=1.0, flag='S0' known)
        raw_dos = {
            'duration': 0, 'protocol_type': 'tcp', 'service': 'http', 'flag': 'S0', 
            'src_bytes': 0, 'dst_bytes': 0, 'land': 0, 'wrong_fragment': 0, 'urgent': 0, 
            'hot': 0, 'num_failed_logins': 0, 'logged_in': 0, 'num_compromised': 0, 
            'root_shell': 0, 'su_attempted': 0, 'num_root': 0, 'num_file_creations': 0,
            'num_shells': 0, 'num_access_files': 0, 'num_outbound_cmds': 0, 'is_host_login': 0, 
            'is_guest_login': 0, 'count': random.randint(500, 511), 'srv_count': random.randint(1, 10), 
            'serror_rate': 1.0, 'srv_serror_rate': 1.0, 'rerror_rate': 1.0, 'srv_rerror_rate': 1.0
        }
        new_df_dos = pd.DataFrame([raw_dos])
        new_df_dos = new_df_dos.reindex(columns=column_names[:-1], fill_value=0)
        new_df_dos[numerical_cols] = new_df_dos[numerical_cols].astype(float)
        new_df_dos[categorical_cols] = new_df_dos[categorical_cols].astype(str)
        synthetic_X.append(preprocessor.transform(new_df_dos)[0])
        synthetic_y.append(1)  # DoS

        # Synthetic MITM (scanning: diff_srv=1.0, failed_logins=5, flag='S0')
        raw_mitm = raw_dos.copy()
        raw_mitm['count'] = random.randint(200, 300)
        raw_mitm['diff_srv_rate'] = 1.0
        raw_mitm['num_failed_logins'] = random.randint(4, 6)
        new_df_mitm = pd.DataFrame([raw_mitm])
        new_df_mitm = new_df_mitm.reindex(columns=column_names[:-1], fill_value=0)
        new_df_mitm[numerical_cols] = new_df_mitm[numerical_cols].astype(float)
        new_df_mitm[categorical_cols] = new_df_mitm[categorical_cols].astype(str)
        synthetic_X.append(preprocessor.transform(new_df_mitm)[0])
        synthetic_y.append(2)  # MITM

        # Synthetic Injection (corruption: serror=1.0, RSTR flag, failed_logins=5+)
        raw_inj = raw_dos.copy()
        raw_inj['serror_rate'] = 1.0
        raw_inj['flag'] = 'RSTR'
        raw_inj['num_failed_logins'] = random.randint(5, 7)
        raw_inj['src_bytes'] = random.randint(1000, 2000)  # Inflated
        new_df_inj = pd.DataFrame([raw_inj])
        new_df_inj = new_df_inj.reindex(columns=column_names[:-1], fill_value=0)
        new_df_inj[numerical_cols] = new_df_inj[numerical_cols].astype(float)
        new_df_inj[categorical_cols] = new_df_inj[categorical_cols].astype(str)
        synthetic_X.append(preprocessor.transform(new_df_inj)[0])
        synthetic_y.append(3)  # Injection
    
    X_train = np.vstack([X_train, synthetic_X])
    y_train = np.hstack([y_train, synthetic_y])
    print(f"Augmented train shape: {X_train.shape}, y distribution: {np.bincount(y_train)}")

    # FIXED: Tune RF for >90% (more trees, split limit)
    model = RandomForestClassifier(n_estimators=500, min_samples_split=2, random_state=42, class_weight='balanced', oob_score=True)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=['normal', 'DoS', 'MITM', 'Data Injection'])

    print("Test Accuracy:", accuracy)
    print("Classification Report:\n", report)

    # Save
    joblib.dump(model, 'model.pkl')
    joblib.dump(preprocessor, 'preprocessor.pkl')

    # Metrics/JSON (unchanged)
    cm = confusion_matrix(y_test, y_pred).tolist()
    class_names = ['normal', 'DoS', 'MITM', 'Data Injection']
    detection_rates = [round(cm[i][i] / sum(cm[i]), 3) for i in range(len(class_names))]

    cm_data = {"z": cm, "x": class_names, "y": class_names, "colorscale": "RdYlGn", "title": "Confusion Matrix", "labels": {"x": "Predicted", "y": "Actual", "color": "Count"}}
    with open('static/cm_data.json', 'w') as f:
        json.dump(cm_data, f)

    dr_data = {"x": class_names, "y": detection_rates, "title": "Detection Rates per Attack Type", "labels": {"x": "Attack Type", "y": "Detection Rate"}}
    with open('static/dr_data.json', 'w') as f:
        json.dump(dr_data, f)

    oob_scores = []
    estimators_range = [10, 25, 50, 75, 100, 200, 500]
    for n in estimators_range:
        temp_model = RandomForestClassifier(n_estimators=n, min_samples_split=2, random_state=42, class_weight='balanced', oob_score=True)
        temp_model.fit(X_train, y_train)
        oob_scores.append(round(temp_model.oob_score_, 3))
    acc_data = {"x": estimators_range, "y": oob_scores, "title": "Accuracy Over Training (OOB Scores)", "labels": {"x": "Number of Estimators", "y": "OOB Accuracy"}}
    with open('static/acc_data.json', 'w') as f:
        json.dump(acc_data, f)

    y_test_binary = (y_test > 0).astype(int)
    y_pred_proba = model.predict_proba(X_test)[:, 1:].sum(axis=1)
    precision, recall, _ = precision_recall_curve(y_test_binary, y_pred_proba)
    pr_data = {"x": recall.tolist(), "y": precision.tolist(), "title": "Precision-Recall Curve (Malicious vs Normal)", "labels": {"x": "Recall", "y": "Precision"}}
    with open('static/pr_data.json', 'w') as f:
        json.dump(pr_data, f)

    report_data = {"accuracy": round(accuracy, 3), "report": report, "cm": cm, "detection_rates": detection_rates}
    with open('static/report_data.json', 'w') as f:
        json.dump(report_data, f)

    print("Graph JSONs saved in /static/ for UI loading.")

if __name__ == '__main__':
    train_model()