# ระบบประเมินการออกเสียงภาษาอังกฤษสำหรับผู้เรียนชาวไทย
# Thai EFL Learners' English Pronunciation Assessment System

ระบบประเมินการออกเสียงภาษาอังกฤษ สำหรับผู้เรียนชาวไทยที่เรียนภาษาอังกฤษในฐานะภาษาต่างประเทศ (Thai EFL learners) โดยใช้โมเดล Machine Learning ที่ผ่านการฝึกอบรมมาอย่างดี

## ความต้องการของระบบ

- Python 3.12.9
- MySQL 5.7 หรือ MariaDB 10.3 หรือสูงกว่า
- เนื้อที่ว่างอย่างน้อย 2GB สำหรับติดตั้งไลบรารีและโมเดล
- หน่วยความจำ (RAM) อย่างน้อย 4GB

## คุณสมบัติหลัก

- อัพโหลดไฟล์เสียงภาษาอังกฤษสูงสุด 10 ไฟล์พร้อมกัน (รองรับเฉพาะไฟล์ WAV)
- วิเคราะห์และประเมินระดับการออกเสียงโดยใช้ Machine Learning (XGBoost)
- แสดงผลการประเมินแบบทันที พร้อมความน่าจะเป็นของแต่ละระดับ (สูง/กลาง/ต่ำ)
- จัดเก็บประวัติการประเมินในฐานข้อมูล
- รองรับการใช้งานทั้งภาษาไทยและภาษาอังกฤษ

## การติดตั้ง

### 1. ติดตั้ง Python และ MySQL

**สำหรับ Windows:**

1. ดาวน์โหลดและติดตั้ง Python 3.12.9 จาก [python.org](https://www.python.org/downloads/)
2. ดาวน์โหลดและติดตั้ง [XAMPP](https://www.apachefriends.org/download.html) หรือ [MySQL Community Server](https://dev.mysql.com/downloads/mysql/)

**สำหรับ macOS:**

1. ติดตั้ง Python และ MySQL ด้วย [Homebrew](https://brew.sh/):
   ```
   brew install python mysql
   ```

**สำหรับ Linux (Ubuntu/Debian):**

1. ติดตั้ง Python และ MySQL:
   ```
   sudo apt update
   sudo apt install python3 python3-pip python3-venv mysql-server libmysqlclient-dev
   ```

### 2. ตั้งค่าฐานข้อมูล MySQL

1. เริ่มบริการ MySQL:
   - Windows (XAMPP): เปิด XAMPP Control Panel และกดปุ่ม Start สำหรับ MySQL
   - macOS: `brew services start mysql`
   - Linux: `sudo systemctl start mysql`

2. นำเข้าไฟล์สคีมา SQL:
   ```
   mysql -u root -p < schema_mysql.sql
   ```

### 3. ติดตั้งแอปพลิเคชัน

1. โคลนหรือดาวน์โหลดโค้ดของแอปพลิเคชัน:
   ```
   git clone https://github.com/yourusername/pronunciation-assessment.git
   cd pronunciation-assessment
   ```

2. สร้างสภาพแวดล้อมเสมือน (Virtual Environment):
   ```
   python -m venv venv
   ```

3. เปิดใช้งานสภาพแวดล้อมเสมือน:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. ติดตั้งแพ็กเกจที่จำเป็น:
   ```
   pip install -r requirements.txt
   ```

5. สร้างไฟล์ `.env` สำหรับการกำหนดค่า:
   ```
   SECRET_KEY=your_secret_key_here
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_DB=EFL
   ```

6. สร้างโฟลเดอร์ที่จำเป็นและเริ่มแอปพลิเคชัน:
   ```
   mkdir uploads Models
   python app.py
   ```

7. เปิดเว็บเบราวเซอร์และไปที่ URL:
   ```
   http://localhost:5000
   ```

## การสร้าง requirements.txt จาก Conda Environment

หากคุณกำลังพัฒนาโดยใช้ Conda และต้องการสร้างไฟล์ requirements.txt สำหรับการดำเนินการในสภาพแวดล้อมอื่น:

### วิธีที่ 1: ใช้ pip freeze (แนะนำ)

```bash
# เปิดใช้งานสภาพแวดล้อม Conda ที่ต้องการ
conda activate ชื่อ_environment_ของคุณ

# สร้างไฟล์ requirements.txt
pip freeze > requirements.txt
```

### วิธีที่ 2: ใช้ Conda List และกรอง

```bash
conda activate ชื่อ_environment_ของคุณ
conda list --export > requirements.txt
```

หรือเพื่อให้เข้ากันได้กับ pip:

```bash
conda list -e | grep -v "^#" > requirements.txt
```

### วิธีที่ 3: ใช้ conda-pack (สำหรับจำลองสภาพแวดล้อมทั้งหมด)

```bash
# ติดตั้ง conda-pack
conda install -c conda-forge conda-pack

# แพ็คสภาพแวดล้อม
conda pack -n ชื่อ_environment_ของคุณ -o environment.tar.gz
```

### วิธีที่ 4: ใช้ export conda environment เป็น YAML

```bash
conda env export > environment.yml
```

หรือเฉพาะแพ็กเกจที่ติดตั้งเอง:

```bash
conda env export --from-history > environment.yml
```

## การใช้งาน

1. ลงชื่อเข้าใช้ด้วยบัญชีผู้ใช้ของคุณ หรือลงทะเบียนบัญชีใหม่
2. อัปโหลดไฟล์เสียง WAV ที่ต้องการวิเคราะห์ (สูงสุด 10 ไฟล์)
3. กดปุ่ม "วิเคราะห์การออกเสียง" เพื่อเริ่มการประเมิน
4. รับผลการวิเคราะห์ที่แสดงระดับการออกเสียง (สูง/กลาง/ต่ำ) พร้อมค่าความน่าจะเป็น
5. ดาวน์โหลดผลการประเมินเป็นไฟล์ CSV หากต้องการ

## โครงสร้างของโปรเจกต์

```
pronunciation-assessment/
├── app.py                  # แอปพลิเคชัน Flask หลัก
├── audio_processor.py      # โมดูลประมวลผลเสียงและจำแนกด้วย XGBoost
├── requirements.txt        # รายชื่อแพ็กเกจที่จำเป็น
├── schema_mysql.sql        # สคริปต์สร้างฐานข้อมูล
├── templates/              # เทมเพลต HTML
│   ├── about.html
│   ├── index.html
│   ├── login.html
│   └── register.html
├── static/                 # ไฟล์ CSS, JavaScript และสินทรัพย์อื่นๆ
│   ├── css/
│   ├── js/
│   └── images/
├── uploads/                # โฟลเดอร์สำหรับไฟล์อัปโหลด
└── Models/                 # โฟลเดอร์เก็บโมเดล ML
    ├── xgb_model.pkl
    ├── scaler.pkl
    └── label_encoder.pkl
```

## การสนับสนุนและการติดต่อ

หากมีคำถามหรือต้องการความช่วยเหลือ กรุณาติดต่อ:

- อีเมล: ksinwong@gmail.com

## ลิขสิทธิ์และการใช้งาน

© 2025 ระบบประเมินการออกเสียงภาษาอังกฤษสำหรับผู้เรียนชาวไทย

พัฒนาโดย: ศูนย์วิจัยด้านภาษา วัฒนธรรม และการพัฒนามนุษย์ ในอาเซียนตอนล่าง, คณะศิลปศาสตร์ มหาวิทยาลัยสงขลานครินทร์
