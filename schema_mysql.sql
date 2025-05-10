-- schema_mysql.sql - สคริปต์สร้างฐานข้อมูลสำหรับระบบประเมินการออกเสียงภาษาอังกฤษ

-- สร้างฐานข้อมูล (หากยังไม่มี)
CREATE DATABASE IF NOT EXISTS EFL DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- ใช้ฐานข้อมูล EFL
USE EFL;

-- ตาราง users - เก็บข้อมูลผู้ใช้
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ตาราง user_sessions - เก็บข้อมูลเซสชันผู้ใช้
CREATE TABLE IF NOT EXISTS user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ตาราง audio_files - เก็บข้อมูลไฟล์เสียงที่อัปโหลด
CREATE TABLE IF NOT EXISTS audio_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    file_size INT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ตาราง assessment_results - เก็บผลการประเมินการออกเสียง
CREATE TABLE IF NOT EXISTS assessment_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    audio_file_id INT NOT NULL,
    pronunciation_level ENUM('High', 'Mid', 'Low') NOT NULL,
    probability FLOAT NOT NULL, -- ค่าความน่าจะเป็นของระดับที่ทำนาย (0.0 - 1.0)
    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (audio_file_id) REFERENCES audio_files(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ตาราง user_progress - เก็บประวัติความก้าวหน้าของผู้ใช้
CREATE TABLE IF NOT EXISTS user_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    date DATE NOT NULL,
    high_count INT DEFAULT 0,
    mid_count INT DEFAULT 0,
    low_count INT DEFAULT 0,
    total_count INT DEFAULT 0,
    UNIQUE KEY unique_user_date (user_id, date),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- สร้างบัญชีผู้ดูแลระบบเริ่มต้น (รหัสผ่าน: admin123)
-- รหัสผ่านใช้ werkzeug.security.generate_password_hash ซึ่งตรงกับฟังก์ชันในแอปพลิเคชัน
INSERT INTO users (username, password_hash, email, full_name) 
VALUES ('admin', 'pbkdf2:sha256:600000$lGBnxPTHWL9KrOB1$dc0ac62e65e4165fe5e92aed8ef5eec87ef2640bd3d0c7f5db2fad948e12983e', 'admin@example.com', 'ผู้ดูแลระบบ')
ON DUPLICATE KEY UPDATE id = id;

-- สร้าง trigger สำหรับอัปเดตตาราง user_progress เมื่อมีการเพิ่มผลประเมินใหม่
DELIMITER //
CREATE TRIGGER IF NOT EXISTS update_user_progress AFTER INSERT ON assessment_results
FOR EACH ROW
BEGIN
    DECLARE v_user_id INT;
    DECLARE v_today DATE;
    DECLARE v_level VARCHAR(10);
    
    -- ดึง user_id จากไฟล์เสียง
    SELECT user_id INTO v_user_id FROM audio_files WHERE id = NEW.audio_file_id;
    
    -- ตั้งค่าวันที่ปัจจุบัน
    SET v_today = CURDATE();
    
    -- ดึงระดับที่ประเมินได้
    SET v_level = NEW.pronunciation_level;
    
    -- อัปเดตความก้าวหน้าของผู้ใช้
    INSERT INTO user_progress (user_id, date, high_count, mid_count, low_count, total_count)
    VALUES (v_user_id, v_today, 
            IF(v_level = 'High', 1, 0),
            IF(v_level = 'Mid', 1, 0),
            IF(v_level = 'Low', 1, 0),
            1)
    ON DUPLICATE KEY UPDATE
        high_count = high_count + IF(v_level = 'High', 1, 0),
        mid_count = mid_count + IF(v_level = 'Mid', 1, 0),
        low_count = low_count + IF(v_level = 'Low', 1, 0),
        total_count = total_count + 1;
END//
DELIMITER ;

-- สร้าง views สำหรับแสดงผลสรุปของผู้ใช้แต่ละคน
CREATE OR REPLACE VIEW user_assessment_summary AS
SELECT 
    u.id AS user_id,
    u.username,
    u.full_name,
    COUNT(ar.id) AS total_assessments,
    SUM(CASE WHEN ar.pronunciation_level = 'High' THEN 1 ELSE 0 END) AS high_count,
    SUM(CASE WHEN ar.pronunciation_level = 'Mid' THEN 1 ELSE 0 END) AS mid_count,
    SUM(CASE WHEN ar.pronunciation_level = 'Low' THEN 1 ELSE 0 END) AS low_count,
    MAX(af.upload_date) AS last_assessment_date
FROM 
    users u
LEFT JOIN 
    audio_files af ON u.id = af.user_id
LEFT JOIN 
    assessment_results ar ON af.id = ar.audio_file_id
GROUP BY 
    u.id, u.username, u.full_name;