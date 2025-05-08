"""
test_model.py - สคริปต์สำหรับทดสอบโมเดล XGBoost ในการจำแนกเสียง
"""

import os
import sys
import numpy as np
import json
import pickle
import librosa
import argparse
from pathlib import Path

def load_model(model_dir='models'):
    """
    โหลดโมเดลและไฟล์ที่เกี่ยวข้อง
    """
    print(f"กำลังโหลดโมเดลจาก {model_dir}...")
    
    # ตรวจสอบว่าไดเรกทอรีมีอยู่หรือไม่
    if not os.path.exists(model_dir):
        print(f"ไม่พบไดเรกทอรี: {model_dir}")
        return None, None, None
    
    model = None
    scaler = None
    label_encoder = None
    
    # ลองโหลดโมเดลด้วย pickle
    try:
        # ทดสอบโหลดโมเดล
        with open(os.path.join(model_dir, 'xgb_model.pkl'), 'rb') as f:
            model = pickle.load(f)
        
        # ทดสอบโหลด scaler
        with open(os.path.join(model_dir, 'scaler.pkl'), 'rb') as f:
            scaler = pickle.load(f)
        
        # ทดสอบโหลด label_encoder
        with open(os.path.join(model_dir, 'label_encoder.pkl'), 'rb') as f:
            label_encoder = pickle.load(f)
        
        print("โหลดโมเดลสำเร็จด้วย pickle")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการโหลดโมเดลด้วย pickle: {e}")
        
        # ลองโหลดด้วย joblib ถ้า pickle ไม่สำเร็จ
        try:
            import joblib
            
            model = joblib.load(os.path.join(model_dir, 'xgb_model.pkl'))
            scaler = joblib.load(os.path.join(model_dir, 'scaler.pkl'))
            label_encoder = joblib.load(os.path.join(model_dir, 'label_encoder.pkl'))
            
            print("โหลดโมเดลสำเร็จด้วย joblib")
        except Exception as e2:
            print(f"เกิดข้อผิดพลาดในการโหลดโมเดลด้วย joblib: {e2}")
    
    return model, scaler, label_encoder

def inspect_model_info(model_dir='Models'):
    """
    ตรวจสอบข้อมูลของโมเดลจาก model_info.json หรือ model_info.pkl
    """
    # ตรวจสอบไฟล์ model_info.json
    json_path = os.path.join(model_dir, 'model_info.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                model_info = json.load(f)
                print("\n=== ข้อมูลจาก model_info.json ===")
                print(f"ประเภทโมเดล: {model_info.get('model_type', 'ไม่ระบุ')}")
                print(f"คลาสทั้งหมด: {model_info.get('classes', [])}")
                print(f"จำนวนคุณลักษณะ: {len(model_info.get('feature_names', []))}")
                print(f"ความแม่นยำ: {model_info.get('accuracy', 'ไม่ระบุ')}")
                print(f"พารามิเตอร์ที่ดีที่สุด: {model_info.get('best_params', {})}")
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการอ่าน model_info.json: {e}")
    else:
        print(f"ไม่พบไฟล์ model_info.json ใน {model_dir}")
        
        # ลองตรวจสอบ model_info.pkl แทน
        pkl_path = os.path.join(model_dir, 'model_info.pkl')
        if os.path.exists(pkl_path):
            try:
                with open(pkl_path, 'rb') as f:
                    model_info = pickle.load(f)
                    print("\n=== ข้อมูลจาก model_info.pkl ===")
                    print(f"ประเภทโมเดล: {model_info.get('model_type', 'ไม่ระบุ')}")
                    print(f"คลาสทั้งหมด: {model_info.get('classes', [])}")
                    print(f"จำนวนคุณลักษณะ: {len(model_info.get('feature_names', []))}")
                    print(f"ความแม่นยำ: {model_info.get('accuracy', 'ไม่ระบุ')}")
                    print(f"พารามิเตอร์ที่ดีที่สุด: {model_info.get('best_params', {})}")
            except Exception as e:
                print(f"เกิดข้อผิดพลาดในการอ่าน model_info.pkl: {e}")
        else:
            print(f"ไม่พบไฟล์ model_info.pkl ใน {model_dir}")

def extract_features(file_path, sr=16000):
    """
    สกัดคุณลักษณะจากไฟล์เสียง (เหมือนกับใน trainxg.py)
    """
    try:
        # โหลดไฟล์เสียง
        y, sr = librosa.load(file_path, sr=sr)
        
        # ตรวจสอบว่าไฟล์เสียงไม่ว่าง
        if len(y) == 0:
            print(f"Warning: {file_path} is empty.")
            return None
        
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
        
        # แก้ไข: ใช้ librosa.feature.rhythm.tempo หรือ librosa.beat.tempo
        try:
            # ลองใช้ librosa.feature.rhythm.tempo (เวอร์ชันใหม่)
            from librosa.feature import rhythm
            tempo = rhythm.tempo(y=y, sr=sr)[0]
        except (ImportError, AttributeError):
            try:
                # ลองใช้ librosa.beat.tempo (เวอร์ชันเก่า)
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    tempo = librosa.beat.tempo(y=y, sr=sr)[0]
            except Exception as e:
                print(f"ไม่สามารถคำนวณ tempo ได้: {e}")
                tempo = 120.0  # ค่าเริ่มต้น
        
        pitch_rhythm_stats = np.hstack([
            [tempo],
            np.mean(chroma, axis=1)
        ])
        
        # 5. คุณลักษณะเกี่ยวกับความเงียบ
        non_silent = librosa.effects.split(y, top_db=30)
        total_duration = len(y) / sr
        
        if len(non_silent) > 0:
            non_silent_duration = np.sum([end - start for start, end in non_silent]) / sr
            silence_ratio = 1 - (non_silent_duration / total_duration)
            avg_phrase_length = non_silent_duration / len(non_silent)
        else:
            silence_ratio = 1.0
            avg_phrase_length = 0.0
        
        silence_stats = np.array([
            silence_ratio, 
            avg_phrase_length, 
            len(non_silent) / total_duration if total_duration > 0 else 0.0
        ])
        
        # รวมคุณลักษณะทั้งหมด
        features = np.hstack([
            mfcc_stats,
            spectral_stats,
            volume_stats,
            pitch_rhythm_stats,
            silence_stats
        ])
        
        return features
    
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการสกัดคุณลักษณะ: {e}")
        return None

def test_with_dummy_data(model, scaler, label_encoder, feature_size=64):
    """
    ทดสอบโมเดลด้วยข้อมูลสุ่ม
    """
    if model is None or scaler is None or label_encoder is None:
        print("โมเดลยังไม่ถูกโหลด ไม่สามารถทดสอบได้")
        return
    
    print("\n=== ทดสอบด้วยข้อมูลสุ่ม ===")
    
    # สร้างข้อมูลสุ่ม
    np.random.seed(42)  # กำหนดค่าเริ่มต้นเพื่อให้ผลลัพธ์คงที่
    dummy_features = np.random.randn(5, feature_size)  # สร้าง 5 ตัวอย่าง
    
    # ทดสอบการทำนาย
    for i in range(len(dummy_features)):
        features = dummy_features[i:i+1]
        
        try:
            # ปรับขนาดข้อมูล
            features_scaled = scaler.transform(features)
            
            # ทำนายคลาส
            predicted_class_numeric = model.predict(features_scaled)[0]
            predicted_class = label_encoder.inverse_transform([predicted_class_numeric])[0]
            
            # ดึงความน่าจะเป็น
            probabilities = model.predict_proba(features_scaled)[0]
            
            # แสดงผลลัพธ์
            print(f"\nตัวอย่างที่ {i+1}:")
            print(f"  ทำนายเป็น: {predicted_class}")
            
            # แสดงค่าความน่าจะเป็นของแต่ละคลาส
            for j, cls in enumerate(label_encoder.classes_):
                print(f"  {cls}: {probabilities[j]:.6f}")
            
            # ตรวจสอบความสอดคล้อง
            if predicted_class_numeric != np.argmax(probabilities):
                print(f"  คำเตือน: คลาสที่ทำนาย ({predicted_class}) ไม่ตรงกับคลาสที่มีความน่าจะเป็นสูงสุด!")
                
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการทำนาย: {e}")

def test_with_audio_file(model, scaler, label_encoder, file_path):
    """
    ทดสอบโมเดลกับไฟล์เสียงจริง
    """
    if model is None or scaler is None or label_encoder is None:
        print("โมเดลยังไม่ถูกโหลด ไม่สามารถทดสอบได้")
        return
    
    print(f"\n=== ทดสอบด้วยไฟล์เสียง: {os.path.basename(file_path)} ===")
    
    # สกัดคุณลักษณะจากไฟล์เสียง
    features = extract_features(file_path)
    
    if features is None:
        print("ไม่สามารถสกัดคุณลักษณะจากไฟล์เสียงได้")
        return
    
    print(f"จำนวนคุณลักษณะที่สกัดได้: {len(features)}")
    
    try:
        # ปรับขนาดข้อมูล
        features_scaled = scaler.transform([features])
        
        # ทำนายคลาส
        predicted_class_numeric = model.predict(features_scaled)[0]
        predicted_class = label_encoder.inverse_transform([predicted_class_numeric])[0]
        
        # ดึงความน่าจะเป็น
        probabilities = model.predict_proba(features_scaled)[0]
        
        # แสดงผลลัพธ์
        print(f"ทำนายเป็น: {predicted_class}")
        print("ความน่าจะเป็นของแต่ละคลาส:")
        
        # สร้างลำดับความน่าจะเป็นจากมากไปน้อย
        class_probs = [(label_encoder.classes_[i], probabilities[i]) for i in range(len(label_encoder.classes_))]
        class_probs.sort(key=lambda x: x[1], reverse=True)
        
        for cls, prob in class_probs:
            print(f"  {cls}: {prob:.6f}")
        
        # ตรวจสอบความสอดคล้อง
        top_class = class_probs[0][0]
        if predicted_class != top_class:
            print(f"คำเตือน: คลาสที่ทำนาย ({predicted_class}) ไม่ตรงกับคลาสที่มีความน่าจะเป็นสูงสุด ({top_class})!")
        
        # ถ้ามีความน่าจะเป็นที่ผิดปกติ (เช่น ทำนายเป็น Medium แต่ความน่าจะเป็นเป็น 0)
        for cls, prob in class_probs:
            if cls == predicted_class and prob < 0.1:
                print(f"คำเตือน: คลาสที่ทำนาย ({cls}) มีความน่าจะเป็นต่ำมาก ({prob:.6f})!")
        
        # ตรวจสอบผลรวมความน่าจะเป็น
        prob_sum = np.sum(probabilities)
        if abs(prob_sum - 1.0) > 1e-5:
            print(f"คำเตือน: ผลรวมความน่าจะเป็นไม่เท่ากับ 1.0: {prob_sum:.6f}")
        
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการทำนาย: {e}")

def main():
    parser = argparse.ArgumentParser(description='ทดสอบโมเดล XGBoost สำหรับการจำแนกเสียง')
    parser.add_argument('--model-dir', type=str, default='Models', help='ที่อยู่ของไดเร็กทอรีที่เก็บโมเดล')
    parser.add_argument('--audio-file', type=str, help='ไฟล์เสียงที่ต้องการทดสอบ (.wav)')
    parser.add_argument('--feature-size', type=int, default=64, help='ขนาดของคุณลักษณะ (feature size)')
    
    args = parser.parse_args()
    
    # โหลดโมเดลและไฟล์ที่เกี่ยวข้อง
    model, scaler, label_encoder = load_model(args.model_dir)
    
    # ตรวจสอบข้อมูลของโมเดล
    inspect_model_info(args.model_dir)
    
    # ถ้าโมเดลยังโหลดไม่ได้ ให้จบการทำงาน
    if model is None or scaler is None or label_encoder is None:
        print("ไม่สามารถโหลดโมเดลได้ ไม่สามารถทดสอบได้")
        return
    
    # ทดสอบด้วยข้อมูลสุ่ม
    test_with_dummy_data(model, scaler, label_encoder, args.feature_size)
    
    # ทดสอบด้วยไฟล์เสียง (ถ้ามีการระบุ)
    if args.audio_file and os.path.exists(args.audio_file):
        test_with_audio_file(model, scaler, label_encoder, args.audio_file)
    elif args.audio_file:
        print(f"ไม่พบไฟล์: {args.audio_file}")

if __name__ == "__main__":
    main()