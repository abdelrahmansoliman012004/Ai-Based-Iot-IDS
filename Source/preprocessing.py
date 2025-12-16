import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

# Define column names (41 features + label + difficulty_level = 43 columns for NSL-KDD)
column_names = [
    'duration', 'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes', 
    'land', 'wrong_fragment', 'urgent', 'hot', 'num_failed_logins', 'logged_in',
    'num_compromised', 'root_shell', 'su_attempted', 'num_root', 'num_file_creations',
    'num_shells', 'num_access_files', 'num_outbound_cmds', 'is_host_login', 
    'is_guest_login', 'count', 'srv_count', 'serror_rate', 'srv_serror_rate', 
    'rerror_rate', 'srv_rerror_rate', 'same_srv_rate', 'diff_srv_rate', 
    'srv_diff_host_rate', 'dst_host_count', 'dst_host_srv_count', 'dst_host_same_srv_rate', 
    'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate', 'dst_host_srv_diff_host_rate', 
    'dst_host_serror_rate', 'dst_host_srv_serror_rate', 'dst_host_rerror_rate', 
    'dst_host_srv_rerror_rate', 'label', 'difficulty_level'
]

# FIXED: Globals for imports in attack_simulation
categorical_cols = ['protocol_type', 'service', 'flag']
numerical_cols = [col for col in column_names if col not in categorical_cols + ['label', 'difficulty_level']]

def preprocess_data():
    # Load dataset (update path as needed)
    dataset_path = r"D:\UNI\Term 7\Cyber Physical System (CPS)\Project 2\Ai Based Iot IDS\nsl-kdd\KDDTrain+.txt"
    df = pd.read_csv(dataset_path, delimiter=',', header=None)
    df.columns = column_names
    
    print("Columns in the dataset:", df.columns.tolist())
    print("Dataset shape:", df.shape)  # Should print (rows, 43)
    print("First few rows of the dataset:")
    print(df.head())
    
    # Drop difficulty_level (not used for training)
    df = df.drop('difficulty_level', axis=1)
    
    # Multi-class mapping for IoT focus: 0=normal, 1=DoS, 2=MITM/probe, 3=Data Injection (U2R/R2L as proxies)
    dos_attacks = ['neptune', 'back', 'land', 'pod', 'smurf', 'teardrop', 'processtable', 'udpstorm', 'apache2', 'mailbomb']
    mitm_probes = ['satan', 'ipsweep', 'portsweep', 'mscan', 'saint']
    data_injection_attacks = ['guess_passwd', 'ftp_write', 'imap', 'phf', 'multihop', 'warezmaster', 'rootkit', 
                              'buffer_overflow', 'loadmodule', 'perl', 'sqlattack', 'xterm', 'ps']  # U2R/R2L for injection
    df['label'] = df['label'].apply(lambda x: 0 if x == 'normal' else 
                                    (1 if x in dos_attacks else 
                                     (2 if x in mitm_probes else 
                                      (3 if x in data_injection_attacks else 1))))  # Default to DoS
    
    print("Class distribution before split:", df['label'].value_counts().sort_index())
    
    # Split data before preprocessing to avoid leakage
    X = df.drop('label', axis=1)
    y = df['label']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Create preprocessor pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_cols),
            ('cat', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'), categorical_cols)
        ]
    )
    
    # Fit and transform
    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)
    
    print("Processed feature shape (no SMOTE):", X_train_processed.shape)
    return X_train_processed, X_test_processed, y_train, y_test, preprocessor

if __name__ == "__main__":
    preprocess_data()
    print("Preprocessing completed successfully!")