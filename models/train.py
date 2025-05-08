import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import librosa
import joblib
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import LeaveOneOut, GridSearchCV
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# กำหนด path ต่างๆ ไว้ล่วงหน้า
DATA_PATH = "data/"  # แก้ไขเป็น path ที่เก็บไฟล์เสียงของคุณ
OUTPUT_PATH = "results/"  # path ที่จะเก็บผลลัพธ์และโมเดล

def extract_features(audio_file):
    """สกัดคุณลักษณะจากไฟล์เสียง"""
    # โหลดไฟล์เสียง
    y, sr = librosa.load(audio_file, sr=16000)
    
    # 1. MFCC คุณลักษณะ
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
    mfcc_stats = np.hstack([
        np.mean(mfccs, axis=1),
        np.std(mfccs, axis=1)
    ])
    
    # 2. คุณลักษณะทาง spectral
    spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    
    spectral_stats = np.hstack([
        [np.mean(spectral_centroids), np.std(spectral_centroids)],
        [np.mean(spectral_rolloff), np.std(spectral_rolloff)]
    ])
    
    # 3. คุณลักษณะเกี่ยวกับความดัง
    rms = librosa.feature.rms(y=y)[0]
    zero_crossing_rate = librosa.feature.zero_crossing_rate(y=y)[0]
    
    volume_stats = np.hstack([
        [np.mean(rms), np.std(rms)],
        [np.mean(zero_crossing_rate), np.std(zero_crossing_rate)]
    ])
    
    # 4. คุณลักษณะเกี่ยวกับ pitch และ rhythm
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    tempo = librosa.beat.tempo(y=y, sr=sr)[0]
    
    pitch_rhythm_stats = np.hstack([
        [tempo],
        np.mean(chroma, axis=1)
    ])
    
    # 5. คุณลักษณะเกี่ยวกับความเงียบ
    non_silent = librosa.effects.split(y, top_db=30)
    if len(non_silent) > 0:
        non_silent_duration = np.sum([end - start for start, end in non_silent]) / sr
        total_duration = len(y) / sr
        silence_ratio = 1 - (non_silent_duration / total_duration)
        avg_phrase_length = non_silent_duration / len(non_silent)
    else:
        silence_ratio = 1.0
        avg_phrase_length = 0.0
    
    silence_stats = np.array([silence_ratio, avg_phrase_length, len(non_silent) / total_duration])
    
    # รวมคุณลักษณะทั้งหมด
    features = np.hstack([
        mfcc_stats,
        spectral_stats,
        volume_stats,
        pitch_rhythm_stats,
        silence_stats
    ])
    
    return features

def train_and_evaluate(data_path=DATA_PATH, output_path=OUTPUT_PATH):
    """
    ฝึกโมเดลและวัดผลในขั้นตอนเดียว
    
    Args:
        data_path: path ของโฟลเดอร์ที่เก็บไฟล์เสียง
        output_path: path สำหรับบันทึกโมเดลและผลลัพธ์
    """
    # สร้างโฟลเดอร์สำหรับบันทึกผลลัพธ์
    os.makedirs(output_path, exist_ok=True)
    
    print("= ขั้นตอนที่ 1: การโหลดและสกัดคุณลักษณะ =")
    
    # โหลดไฟล์เสียงและสกัดคุณลักษณะ
    features_list = []
    labels = []
    file_names = []
    
    # โหลดไฟล์เสียงและสกัดคุณลักษณะ
    for file in os.listdir(data_path):
        if file.endswith((".wav", ".mp3")):
            try:
                # ระบุ label จากชื่อไฟล์ (ตัวอักษรตัวแรก)
                first_char = file[0].upper()
                if first_char == 'H':
                    label = 'High'
                elif first_char == 'M':
                    label = 'Mid'
                elif first_char == 'L':
                    label = 'Low'
                else:
                    print(f"ข้ามไฟล์ {file} เนื่องจากไม่สามารถระบุระดับได้")
                    continue
                
                # สกัดคุณลักษณะ
                file_path = os.path.join(data_path, file)
                features = extract_features(file_path)
                
                # เก็บข้อมูล
                features_list.append(features)
                labels.append(label)
                file_names.append(file)
                
                print(f"สกัดคุณลักษณะสำเร็จ: {file} (label: {label})")
            except Exception as e:
                print(f"เกิดข้อผิดพลาดกับไฟล์ {file}: {str(e)}")
    
    # แปลงเป็น numpy array
    X = np.array(features_list)
    le = LabelEncoder()
    y = le.fit_transform(labels)
    
    # บันทึกข้อมูลเมตาดาต้า
    metadata = pd.DataFrame({
        'file': file_names,
        'label': labels,
        'label_encoded': y
    })
    metadata.to_csv(os.path.join(output_path, 'metadata.csv'), index=False)
    
    # ตรวจสอบสมดุลของข้อมูล
    class_counts = pd.Series(labels).value_counts()
    print("\nการกระจายของข้อมูล:")
    for cls, count in class_counts.items():
        print(f"- {cls}: {count} ไฟล์")
    
    # แสดงกราฟการกระจายของข้อมูล
    plt.figure(figsize=(8, 5))
    sns.countplot(x=labels)
    plt.title('การกระจายของระดับความสามารถ')
    plt.xlabel('ระดับความสามารถ')
    plt.ylabel('จำนวนไฟล์')
    plt.savefig(os.path.join(output_path, 'data_distribution.png'))
    plt.close()
    
    print("\n= ขั้นตอนที่ 2: การปรับพารามิเตอร์ =")
    
    # พารามิเตอร์ที่ต้องการทดสอบ
    param_grid = {
        'C': [0.1, 1, 10, 100],
        'gamma': ['scale', 'auto', 0.01, 0.1],
        'kernel': ['rbf', 'linear']
    }
    
    # มาตรฐานข้อมูล
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # ใช้ GridSearchCV หาพารามิเตอร์ที่ดีที่สุด
    grid = GridSearchCV(
        SVC(probability=True, class_weight='balanced'),
        param_grid,
        cv=5,  # 5-fold cross-validation
        scoring='accuracy',
        verbose=1
    )
    
    # เทรนโมเดล
    grid.fit(X_scaled, y)
    
    # พารามิเตอร์ที่ดีที่สุด
    best_params = grid.best_params_
    print(f"\nพารามิเตอร์ที่ดีที่สุด: {best_params}")
    
    # บันทึกผลการปรับพารามิเตอร์
    cv_results = pd.DataFrame(grid.cv_results_)
    cv_results.to_csv(os.path.join(output_path, 'grid_search_results.csv'), index=False)
    
    print("\n= ขั้นตอนที่ 3: การวัดประสิทธิภาพด้วย Leave-One-Out Cross-Validation =")
    
    # กำหนด Leave-One-Out Cross-Validation
    loo = LeaveOneOut()
    
    # เตรียมตัวแปรเก็บผลลัพธ์
    y_true = []
    y_pred = []
    file_results = []
    
    # ทดสอบด้วย LOOCV
    for train_idx, test_idx in loo.split(X):
        # แบ่งข้อมูล
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # มาตรฐานข้อมูล
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # สร้างและเทรนโมเดล SVM ด้วยพารามิเตอร์ที่ดีที่สุด
        svm = SVC(
            kernel=best_params['kernel'],
            C=best_params['C'],
            gamma=best_params['gamma'],
            probability=True,
            class_weight='balanced'
        )
        svm.fit(X_train_scaled, y_train)
        
        # ทำนายผลลัพธ์
        y_test_pred = svm.predict(X_test_scaled)
        probabilities = svm.predict_proba(X_test_scaled)[0]
        
        # เก็บผลลัพธ์
        y_true.append(y_test[0])
        y_pred.append(y_test_pred[0])
        
        # เก็บข้อมูลไฟล์ที่ทดสอบ
        test_file = file_names[test_idx[0]]
        true_label = le.inverse_transform([y_test[0]])[0]
        pred_label = le.inverse_transform([y_test_pred[0]])[0]
        correct = (y_test[0] == y_test_pred[0])
        
        file_result = {
            'file': test_file,
            'true_label': true_label,
            'predicted_label': pred_label,
            'correct': correct,
            'prob_low': probabilities[0] if len(probabilities) > 0 else 0,
            'prob_mid': probabilities[1] if len(probabilities) > 1 else 0,
            'prob_high': probabilities[2] if len(probabilities) > 2 else 0
        }
        file_results.append(file_result)
    
    # สร้าง DataFrame เก็บผลลัพธ์รายไฟล์
    df_results = pd.DataFrame(file_results)
    df_results.to_csv(os.path.join(output_path, 'leave_one_out_results.csv'), index=False)
    
    # ประเมินผลโมเดล
    accuracy = accuracy_score(y_true, y_pred)
    print(f"ความแม่นยำโดยรวม: {accuracy:.4f}")
    
    # สร้าง confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    print("\nConfusion Matrix:")
    print(cm)
    
    # รายงานการจำแนกประเภท
    report = classification_report(y_true, y_pred, target_names=le.classes_, output_dict=True)
    print("\nClassification Report:")
    for cls in le.classes_:
        precision = report[cls]['precision']
        recall = report[cls]['recall']
        f1 = report[cls]['f1-score']
        support = report[cls]['support']
        print(f"- {cls}: Precision={precision:.2f}, Recall={recall:.2f}, F1={f1:.2f}, Support={support}")
    
    # แสดง confusion matrix ในรูปแบบกราฟ
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=le.classes_, 
                yticklabels=le.classes_)
    plt.xlabel('ค่าทำนาย')
    plt.ylabel('ค่าจริง')
    plt.title('Confusion Matrix')
    plt.savefig(os.path.join(output_path, 'confusion_matrix.png'))
    plt.close()
    
    print("\n= ขั้นตอนที่ 4: การสร้างและบันทึกโมเดลสุดท้าย =")
    
    # สร้างโมเดลสุดท้ายด้วยชุดข้อมูลทั้งหมด
    final_model = SVC(
        kernel=best_params['kernel'],
        C=best_params['C'],
        gamma=best_params['gamma'],
        probability=True,
        class_weight='balanced'
    )
    
    # เทรนโมเดลด้วยข้อมูลทั้งหมด
    final_model.fit(X_scaled, y)
    
    # บันทึกโมเดลและองค์ประกอบที่จำเป็น
    os.makedirs(os.path.join(output_path, 'model'), exist_ok=True)
    joblib.dump(final_model, os.path.join(output_path, 'model', 'svm_model.pkl'))
    joblib.dump(scaler, os.path.join(output_path, 'model', 'scaler.pkl'))
    joblib.dump(le, os.path.join(output_path, 'model', 'label_encoder.pkl'))
    
    print(f"\nสร้างและบันทึกโมเดลเรียบร้อยแล้ว ที่ {os.path.join(output_path, 'model')}")
    print(f"ความแม่นยำของโมเดล: {accuracy:.4f}")
    
    return {
        'model_path': os.path.join(output_path, 'model'),
        'accuracy': accuracy,
        'best_params': best_params
    }

# เรียกใช้ฟังก์ชันโดยตรง (ไม่ต้องรับ input)
if __name__ == "__main__":
    print(f"กำลังเทรนโมเดลจากข้อมูลใน: {DATA_PATH}")
    print(f"จะบันทึกผลลัพธ์ไปยัง: {OUTPUT_PATH}")
    
    try:
        result = train_and_evaluate()
        print("\nการฝึกโมเดลเสร็จสิ้น")
        print(f"โมเดลถูกบันทึกที่: {result['model_path']}")
        print(f"ความแม่นยำ: {result['accuracy']:.4f}")
        print(f"พารามิเตอร์ที่ดีที่สุด: {result['best_params']}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {str(e)}")