"""
app.py - Flask ของเซิร์ฟเวอร์สำหรับระบบจำแนกเสียงแบบมีระบบล็อกอิน (ใช้ MySQL)
"""

import os
import uuid
import datetime
import mysql.connector
from mysql.connector import pooling
from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import json
import logging
import traceback

# import โมดูลสำหรับประมวลผลเสียง
import audio_processor

# ลองโหลด dotenv หากติดตั้งแล้ว
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ตั้งค่า logging ให้แสดงรายละเอียด
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/flask_debug.log')
    ]
)

# สร้างแอปพลิเคชัน Flask
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'development_secret_key')

# กำหนดค่าสำหรับการอัพโหลดไฟล์
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav'}
MAX_FILES = 10

# สร้างโฟลเดอร์อัพโหลดหากยังไม่มี
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# สร้าง instance ของ AudioProcessor พร้อม debug
try:
    logging.info("Creating AudioProcessor instance...")
    audio_processor_instance = audio_processor.AudioProcessor(models_dir='models')
    logging.info("AudioProcessor created successfully")
except Exception as e:
    logging.error(f"Failed to create AudioProcessor: {e}")
    logging.error(f"AudioProcessor creation traceback: {traceback.format_exc()}")
    # สร้าง fallback processor
    audio_processor_instance = None

# สร้าง connection pool สำหรับ MySQL
# สร้าง connection สำหรับ MySQL/MariaDB
db_config = {
    'host': 'localhost',
    'database': 'EFL',
    'user': 'root',
    'password': '',  # ปล่อยเป็นสตริงว่าง
    'charset': 'utf8mb4',
    'use_unicode': True,
    'get_warnings': True,
}

try:
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="pronunciation_pool",
        pool_size=5,  # จำนวน connections ที่เก็บไว้ในพูล
        **db_config
    )
    print("Database connection pool created successfully")
except Exception as e:
    print(f"Error creating connection pool: {e}")
    connection_pool = None

# ฟังก์ชันสำหรับรับ connection จากพูล
def get_db_connection():
    if connection_pool:
        return connection_pool.get_connection()
    else:
        # หากไม่สามารถสร้างพูลได้ ให้สร้าง connection ใหม่
        return mysql.connector.connect(**db_config)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    """ตรวจสอบว่าไฟล์มีนามสกุลที่อนุญาตหรือไม่"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# เพิ่มการจับ error ทั่วไป
@app.errorhandler(500)
def internal_error(error):
    logging.error(f"500 Error: {error}")
    logging.error(f"Traceback: {traceback.format_exc()}")
    return jsonify({'error': 'Internal server error occurred'}), 500

# Routes
@app.route('/')
def index():
    """เรนเดอร์หน้าเว็บหลัก"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            
            # Create a new session in the database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            session_token = str(uuid.uuid4())
            expires_at = datetime.datetime.now() + datetime.timedelta(days=7)
            
            cursor.execute(
                "INSERT INTO user_sessions (user_id, session_token, expires_at) VALUES (%s, %s, %s)",
                (user['id'], session_token, expires_at)
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            session['session_token'] = session_token
            
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        
        password_hash = generate_password_hash(password)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, email, full_name) VALUES (%s, %s, %s, %s)",
                (username, password_hash, email, full_name)
            )
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as e:
            flash(f'Registration failed: {e}', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    if 'user_id' in session and 'session_token' in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE user_sessions SET is_active = FALSE WHERE user_id = %s AND session_token = %s",
            (session['user_id'], session['session_token'])
        )
        
        conn.commit()
        cursor.close()
        conn.close()
    
    session.clear()
    return redirect(url_for('login'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/api/classify', methods=['POST'])
@login_required
def classify_audio():
    """
    API endpoint สำหรับการจำแนกไฟล์เสียง
    รับไฟล์ WAV และส่งกลับผลการจำแนก
    """
    temp_paths = []
    
    try:
        logging.info("=== API /api/classify called ===")
        logging.info(f"Request method: {request.method}")
        logging.info(f"Request content type: {request.content_type}")
        logging.info(f"Request files keys: {list(request.files.keys())}")
        logging.info(f"User ID: {session.get('user_id')}")
        logging.info(f"Audio processor instance: {audio_processor_instance}")
        
        # ตรวจสอบว่า AudioProcessor ถูกสร้างสำเร็จหรือไม่
        if audio_processor_instance is None:
            logging.error("AudioProcessor instance is None")
            return jsonify({'error': 'ระบบวิเคราะห์เสียงไม่พร้อมใช้งาน'}), 503
        
        # ตรวจสอบว่ามีไฟล์ในคำขอหรือไม่
        if 'audio_files' not in request.files:
            logging.error("No audio_files in request.files")
            return jsonify({'error': 'ไม่พบไฟล์เสียงในคำขอ'}), 400
        
        files = request.files.getlist('audio_files')
        logging.info(f"Received {len(files)} files")
        
        # ตรวจสอบจำนวนไฟล์
        if len(files) > MAX_FILES:
            logging.error(f"Too many files: {len(files)} > {MAX_FILES}")
            return jsonify({'error': f'จำนวนไฟล์เกินขีดจำกัด (สูงสุด {MAX_FILES} ไฟล์)'}), 400
        
        results = []
        
        # บันทึกไฟล์และประมวลผลแต่ละไฟล์
        for i, file in enumerate(files):
            logging.info(f"Processing file {i+1}/{len(files)}: {file.filename}")
            
            if file and allowed_file(file.filename):
                try:
                    # สร้างชื่อไฟล์ที่ปลอดภัยและไม่ซ้ำกัน
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    
                    logging.info(f"Saving file to: {file_path}")
                    
                    # ตรวจสอบว่าโฟลเดอร์ upload มีอยู่หรือไม่
                    upload_dir = app.config['UPLOAD_FOLDER']
                    if not os.path.exists(upload_dir):
                        logging.info(f"Creating upload directory: {upload_dir}")
                        os.makedirs(upload_dir, exist_ok=True)
                    
                    # บันทึกไฟล์
                    file.save(file_path)
                    temp_paths.append(file_path)
                    
                    file_size = os.path.getsize(file_path)
                    logging.info(f"File saved successfully, size: {file_size} bytes")
                    
                    # ตรวจสอบไฟล์ว่าเป็น WAV จริงๆ หรือไม่
                    try:
                        import librosa
                        y, sr = librosa.load(file_path, sr=None, duration=1.0)  # โหลดแค่ 1 วินาทีเพื่อทดสอบ
                        logging.info(f"Audio file validation successful - sample rate: {sr}, samples: {len(y)}")
                    except Exception as audio_error:
                        logging.error(f"Invalid audio file: {audio_error}")
                        # ลบไฟล์ที่ไม่ใช่เสียง
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            temp_paths.remove(file_path)
                        return jsonify({'error': f'ไฟล์ {filename} ไม่ใช่ไฟล์เสียงที่ถูกต้อง'}), 400
                    
                    # จำแนกไฟล์เสียง
                    logging.info(f"Starting audio classification...")
                    classification_result = audio_processor_instance.classify_audio(file_path)
                    logging.info(f"Classification completed: {classification_result}")
                    
                    # เพิ่มชื่อไฟล์เดิมเข้าไปในผลลัพธ์
                    classification_result['file_name'] = file.filename
                    
                    # บันทึกลงฐานข้อมูล (ถ้ามีการล็อกอิน)
                    if 'user_id' in session:
                        try:
                            logging.info(f"Saving to database...")
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            
                            # บันทึกข้อมูลไฟล์
                            cursor.execute(
                                """
                                INSERT INTO audio_files (user_id, file_name, file_path, file_size) 
                                VALUES (%s, %s, %s, %s)
                                """,
                                (session['user_id'], filename, file_path, file_size)
                            )
                            
                            conn.commit()
                            file_id = cursor.lastrowid
                            logging.info(f"File saved to DB with ID: {file_id}")
                            
                            # บันทึกผลการประเมิน
                            pronunciation_level = classification_result['predicted_class']
                            probability = classification_result['probabilities'].get(pronunciation_level, 0)
                            
                            cursor.execute(
                                """
                                INSERT INTO assessment_results (audio_file_id, pronunciation_level, probability) 
                                VALUES (%s, %s, %s)
                                """,
                                (file_id, pronunciation_level, probability)
                            )
                            
                            conn.commit()
                            logging.info(f"Assessment result saved to DB")
                            cursor.close()
                            conn.close()
                            
                        except Exception as db_error:
                            logging.warning(f"Database error (non-critical): {db_error}")
                            # Database errors are non-critical, continue processing
                    
                    results.append(classification_result)
                    logging.info(f"File {i+1} processed successfully")
                    
                except Exception as file_error:
                    logging.error(f"Error processing file {file.filename}: {file_error}")
                    logging.error(f"File processing traceback: {traceback.format_exc()}")
                    return jsonify({'error': f'เกิดข้อผิดพลาดในการประมวลผลไฟล์ {file.filename}: {str(file_error)}'}), 500
                    
            else:
                error_msg = f'ไฟล์ {file.filename} ไม่ใช่ไฟล์ WAV'
                logging.error(error_msg)
                return jsonify({'error': error_msg}), 400
        
        logging.info(f"All files processed successfully. Returning {len(results)} results")
        return jsonify({'results': results})
    
    except Exception as e:
        logging.error(f"CRITICAL ERROR in classify_audio: {str(e)}")
        logging.error(f"Full traceback: {traceback.format_exc()}")
        
        # ลบไฟล์ชั่วคราวที่อาจจะถูกสร้างไว้
        for temp_path in temp_paths:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    logging.info(f"Cleaned up temp file: {temp_path}")
            except Exception as cleanup_error:
                logging.error(f"Failed to cleanup {temp_path}: {cleanup_error}")
        
        return jsonify({'error': f'เกิดข้อผิดพลาดภายในเซิร์ฟเวอร์: {str(e)}'}), 500

@app.route('/results', methods=['GET'])
@login_required
def get_results():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        """
        SELECT af.id, af.file_name, ar.pronunciation_level, ar.probability 
        FROM audio_files af
        JOIN assessment_results ar ON af.id = ar.audio_file_id
        WHERE af.user_id = %s
        ORDER BY af.upload_date DESC
        """,
        (session['user_id'],)
    )
    
    results = cursor.fetchall()
    
    # Format probability as percentage
    for result in results:
        result['probability'] = f"{result['probability']:.2%}"
    
    # Get summary statistics - ใช้ค่า 'Mid' โดยตรง (ไม่ใช่ 'Medium')
    high_count = sum(1 for result in results if result['pronunciation_level'] == 'High')
    mid_count = sum(1 for result in results if result['pronunciation_level'] == 'Mid')
    low_count = sum(1 for result in results if result['pronunciation_level'] == 'Low')
    
    summary = {
        'total': len(results),
        'high': high_count,
        'mid': mid_count,
        'low': low_count
    }
    
    cursor.close()
    conn.close()
    
    return jsonify({'results': results, 'summary': summary}), 200

# เพิ่ม route สำหรับทรัพยากรคงที่ (static resources)
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# ตรวจสอบการเชื่อมต่อฐานข้อมูลและสร้างตารางหากจำเป็น
def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # ทดสอบการเชื่อมต่อฐานข้อมูล
        cursor.execute("SELECT 1")
        cursor.fetchone()
        
        print("Connected to database successfully.")
        
        # ตรวจสอบว่าตาราง users มีอยู่หรือไม่
        cursor.execute("SHOW TABLES LIKE 'users'")
        exists = cursor.fetchone()
        
        if not exists:
            print("Tables do not exist. Creating tables...")
            
            # อ่านและรันสคริปต์ SQL
            with open('schema_mysql.sql', 'r') as f:
                sql_script = f.read()
                
            # แยกคำสั่ง SQL เพื่อรันทีละคำสั่ง
            for statement in sql_script.split(';'):
                if statement.strip():
                    cursor.execute(statement)
            
            conn.commit()
            print("Tables created successfully.")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        raise

if __name__ == '__main__':
    # ตรวจสอบและสร้างตารางฐานข้อมูลหากจำเป็น
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
        print("You may need to run schema_mysql.sql manually.")
    
    app.run(debug=True)