# ปรับปรุงสคริปต์ XGBoost สำหรับการรันแบบ Local (เวอร์ชันที่เรียบง่าย)
import pandas as pd
import numpy as np
import librosa
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score
import os
import matplotlib.pyplot as plt
import joblib  # สำหรับบันทึกโมเดลและ scaler

# กำหนดพาธสำหรับโฟลเดอร์ข้อมูล
train_data_folder = 'Train'  # โฟลเดอร์ข้อมูลฝึกฝน
test_data_folder = 'Test'  # โฟลเดอร์ข้อมูลทดสอบ
output_folder = 'Models'  # โฟลเดอร์สำหรับเก็บไฟล์ผลลัพธ์

# สร้างโฟลเดอร์ output ถ้ายังไม่มี
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print(f"สร้างโฟลเดอร์ output: {output_folder}")

# ฟังก์ชันสกัดคุณลักษณะจากไฟล์ .wav
def extract_features(file_path):
    y, sr = librosa.load(file_path, sr=22050)  # Resample เป็น 22050 Hz เพื่อความสม่ำเสมอ
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)  # สกัด 13 MFCC features
    return np.mean(mfccs.T, axis=0)  # คืนค่าเฉลี่ยของ MFCCs เป็นเวกเตอร์คุณลักษณะ

# ตรวจสอบโฟลเดอร์ข้อมูลฝึกฝน
if not os.path.exists(train_data_folder):
    raise FileNotFoundError(f"ไม่พบโฟลเดอร์ {train_data_folder}")
print(f"ตรวจสอบเนื้อหาในโฟลเดอร์ {train_data_folder}...")
print(os.listdir(train_data_folder))

# อ่านไฟล์ .wav จากโฟลเดอร์ฝึกฝน
train_file_paths = [os.path.join(train_data_folder, f) for f in os.listdir(train_data_folder) if f.lower().endswith('.wav')]

# กำหนดป้ายชื่อตามตัวอักษรแรกของชื่อไฟล์
train_labels = []
for file_path in train_file_paths:
    file_name = os.path.basename(file_path)  # ดึงชื่อไฟล์
    first_letter = file_name[0].lower()  # ดึงตัวอักษรแรกและแปลงเป็นตัวพิมพ์เล็ก
    if first_letter == 'h':
        train_labels.append('High')
    elif first_letter == 'm':
        train_labels.append('Medium')
    elif first_letter == 'l':
        train_labels.append('Low')
    else:
        raise ValueError(f"รูปแบบชื่อไฟล์ไม่ถูกต้อง: {file_name} ตัวอักษรแรกต้องเป็น H, M, หรือ L")

# ตรวจสอบว่าจำนวนป้ายชื่อตรงกับจำนวนไฟล์
if len(train_labels) != len(train_file_paths):
    raise ValueError("จำนวนป้ายชื่อไม่ตรงกับจำนวนไฟล์")

# แสดงรายละเอียดชุดข้อมูล
print("ไฟล์ในโฟลเดอร์ฝึกฝน:", [os.path.basename(f) for f in train_file_paths])
print("ป้ายชื่อ:", train_labels)

# แปลงป้ายชื่อเป็นค่าตัวเลข
label_encoder = LabelEncoder()
train_labels_encoded = label_encoder.fit_transform(train_labels)

# สกัดคุณลักษณะและเตรียมชุดข้อมูลฝึกฝน
X_train = np.array([extract_features(file_path) for file_path in train_file_paths])
y_train = np.array(train_labels_encoded)

# ปรับค่าคุณลักษณะให้เป็นมาตรฐาน
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)

# ตรวจสอบโฟลเดอร์ข้อมูลทดสอบ
if not os.path.exists(test_data_folder):
    raise FileNotFoundError(f"ไม่พบโฟลเดอร์ {test_data_folder}")
print(f"ตรวจสอบเนื้อหาในโฟลเดอร์ {test_data_folder}...")
print(os.listdir(test_data_folder))

# อ่านไฟล์ .wav จากโฟลเดอร์ทดสอบ
test_file_paths = [os.path.join(test_data_folder, f) for f in os.listdir(test_data_folder) if f.lower().endswith('.wav')]

# กำหนดป้ายชื่อตามตัวอักษรแรกของชื่อไฟล์
test_labels = []
for file_path in test_file_paths:
    file_name = os.path.basename(file_path)  # ดึงชื่อไฟล์
    first_letter = file_name[0].lower()  # ดึงตัวอักษรแรกและแปลงเป็นตัวพิมพ์เล็ก
    if first_letter == 'h':
        test_labels.append('High')
    elif first_letter == 'm':
        test_labels.append('Medium')
    elif first_letter == 'l':
        test_labels.append('Low')
    else:
        raise ValueError(f"รูปแบบชื่อไฟล์ไม่ถูกต้อง: {file_name} ตัวอักษรแรกต้องเป็น H, M, หรือ L")

# ตรวจสอบว่าจำนวนป้ายชื่อตรงกับจำนวนไฟล์
if len(test_labels) != len(test_file_paths):
    raise ValueError("จำนวนป้ายชื่อไม่ตรงกับจำนวนไฟล์")

# แสดงรายละเอียดชุดข้อมูล
print("ไฟล์ในโฟลเดอร์ทดสอบ:", [os.path.basename(f) for f in test_file_paths])
print("ป้ายชื่อ:", test_labels)

# แปลงป้ายชื่อเป็นค่าตัวเลข
test_labels_encoded = label_encoder.transform(test_labels)

# สกัดคุณลักษณะและเตรียมชุดข้อมูลทดสอบ
X_test = np.array([extract_features(file_path) for file_path in test_file_paths])
y_test = np.array(test_labels_encoded)

# ปรับค่าคุณลักษณะให้เป็นมาตรฐาน (ใช้ scaler เดียวกับข้อมูลฝึกฝน)
X_test = scaler.transform(X_test)

# ใช้ค่าไฮเปอร์พารามิเตอร์ที่เหมาะสมสำหรับ XGBoost โดยตรง (ไม่ใช้ GridSearchCV)
print("สร้างและฝึกสอนโมเดล XGBoost...")

# สร้างโมเดล XGBoost โดยกำหนดพารามิเตอร์ตรงๆ
xgb = XGBClassifier(
    n_estimators=100,  # จำนวนต้นไม้
    max_depth=3,       # ความลึกสูงสุดของต้นไม้
    learning_rate=0.1, # อัตราการเรียนรู้
    subsample=0.8,     # สัดส่วนของข้อมูลที่นำมาใช้ในแต่ละต้นไม้
    random_state=42,   # กำหนดค่า seed สำหรับการสุ่ม
    eval_metric='mlogloss'  # เมทริกการประเมิน
)

# ฝึกสอนโมเดล
xgb.fit(X_train, y_train)

# ประเมินโมเดล
y_pred = xgb.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
print(f"ความแม่นยำบนชุดข้อมูลทดสอบ: {accuracy * 100:.2f}%")

# แปลงการทำนายเชิงตัวเลขกลับเป็นป้ายชื่อเดิม
y_pred_decoded = label_encoder.inverse_transform(y_pred)

# จำแนกไฟล์ .wav ใหม่จากโฟลเดอร์ทดสอบและบันทึกผลลัพธ์เป็น CSV
results = []

# จำแนกไฟล์ใหม่
for i, new_file in enumerate(test_file_paths):
    features = extract_features(new_file)  # สกัดคุณลักษณะ
    features = scaler.transform([features])  # ปรับค่าให้เป็นมาตรฐาน
    predicted_class_numeric = xgb.predict(features)[0]  # ทำนายคลาส (เชิงตัวเลข)
    predicted_class = label_encoder.inverse_transform([predicted_class_numeric])[0]  # แปลงกลับเป็นป้ายชื่อเดิม
    
    # ดึงความน่าจะเป็นของแต่ละคลาส
    class_probabilities = xgb.predict_proba(features)[0]
    class_names = label_encoder.classes_
    prob_dict = {class_name: prob for class_name, prob in zip(class_names, class_probabilities)}
    
    results.append({
        'File Name': os.path.basename(new_file),  # ชื่อไฟล์เดิม
        'Predicted Class': predicted_class,  # คลาสที่ทำนาย
        'Probabilities': prob_dict  # ความน่าจะเป็นของแต่ละคลาส
    })
    
    print(f"ไฟล์: {os.path.basename(new_file)}, ทำนาย: {predicted_class}, ความน่าจะเป็น: {prob_dict}")

# บันทึกผลลัพธ์เป็นไฟล์ CSV
results_df = pd.DataFrame([
    {'File Name': r['File Name'], 'Predicted Class': r['Predicted Class']} 
    for r in results
])
results_csv_path = os.path.join(output_folder, 'WAVxgboostresult.csv')
results_df.to_csv(results_csv_path, index=False)

print(f"บันทึกผลลัพธ์การจำแนกไปที่ {results_csv_path}")

# บันทึกโมเดลที่ฝึกสอนแล้วและ scaler
# บันทึกโมเดล XGBoost ที่ฝึกสอนแล้ว
joblib.dump(xgb, os.path.join(output_folder, 'xgboost_model.joblib'))

# บันทึก StandardScaler ที่ปรับแล้ว
joblib.dump(scaler, os.path.join(output_folder, 'scaler.joblib'))

# บันทึก LabelEncoder
joblib.dump(label_encoder, os.path.join(output_folder, 'label_encoder.joblib'))

print("บันทึกโมเดล, scaler, และ label encoder เรียบร้อยแล้ว")

# วาดกราฟแสดงความสำคัญของคุณลักษณะ
plt.figure(figsize=(10, 6))
feature_importance = xgb.feature_importances_
# สร้างชื่อคุณลักษณะ (MFCC_1, MFCC_2, ...)
feature_names = [f'MFCC_{i+1}' for i in range(len(feature_importance))]
plt.barh(feature_names, feature_importance)
plt.xlabel('Feature Importance')
plt.ylabel('Features')
plt.title('XGBoost Feature Importance')
plt.tight_layout()
plt.savefig(os.path.join(output_folder, 'feature_importance.png'))
print(f"บันทึกกราฟความสำคัญของคุณลักษณะไปที่ {os.path.join(output_folder, 'feature_importance.png')}")

# วาดกราฟแสดงความน่าจะเป็นของการทำนาย
plt.figure(figsize=(12, 8))
    
# เตรียมข้อมูลสำหรับกราฟ
files = [r['File Name'] for r in results]
classes = list(results[0]['Probabilities'].keys())
    
# สร้างตำแหน่งแท่งกราฟ
x = np.arange(len(files))
width = 0.25  # ความกว้างของแต่ละแท่ง
    
# สร้างแท่งกราฟสำหรับแต่ละคลาส
for i, cls in enumerate(classes):
    probs = [r['Probabilities'][cls] for r in results]
    plt.bar(x + (i - 1) * width, probs, width, label=cls)
    
# กำหนดรายละเอียดกราฟ
plt.xlabel('ไฟล์')
plt.ylabel('ความน่าจะเป็น')
plt.title('ความน่าจะเป็นในการทำนายคลาสของแต่ละไฟล์')
plt.xticks(x, files, rotation=45, ha='right')
plt.legend()
plt.tight_layout()
    
# บันทึกกราฟ
output_plot = os.path.join(output_folder, 'prediction_probabilities.png')
plt.savefig(output_plot)
print(f"บันทึกกราฟความน่าจะเป็นไปที่ {output_plot}")