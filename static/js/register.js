/**
 * register.js - จัดการการตรวจสอบความถูกต้องของแบบฟอร์มการลงทะเบียน
 */

document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('registerForm');
    
    // ฟังก์ชันตรวจสอบความถูกต้องของฟอร์ม
    window.validateForm = function() {
        const username = document.getElementById('username').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm_password').value;
        
        // ตรวจสอบชื่อผู้ใช้
        if (username.length < 4) {
            showError(document.body.classList.contains('en') ? 
                'Username must be at least 4 characters long.' : 
                'ชื่อผู้ใช้ต้องมีความยาวอย่างน้อย 4 ตัวอักษร');
            return false;
        }
        
        // ตรวจสอบรูปแบบอีเมล
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            showError(document.body.classList.contains('en') ? 
                'Please enter a valid email address.' : 
                'กรุณาระบุอีเมลที่ถูกต้อง');
            return false;
        }
        
        // ตรวจสอบความยาวรหัสผ่าน
        if (password.length < 8) {
            showError(document.body.classList.contains('en') ? 
                'Password must be at least 8 characters long.' : 
                'รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร');
            return false;
        }
        
        // ตรวจสอบความซับซ้อนของรหัสผ่าน
        const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/;
        if (!passwordRegex.test(password)) {
            showError(document.body.classList.contains('en') ? 
                'Password must contain at least one uppercase letter, one lowercase letter, and one number.' : 
                'รหัสผ่านต้องประกอบด้วยตัวอักษรพิมพ์ใหญ่อย่างน้อย 1 ตัว ตัวอักษรพิมพ์เล็กอย่างน้อย 1 ตัว และตัวเลขอย่างน้อย 1 ตัว');
            return false;
        }
        
        // ตรวจสอบว่ารหัสผ่านและการยืนยันรหัสผ่านตรงกัน
        if (password !== confirmPassword) {
            showError(document.body.classList.contains('en') ? 
                'Passwords do not match.' : 
                'รหัสผ่านไม่ตรงกัน');
            return false;
        }
        
        return true;
    };
    
    // ฟังก์ชันแสดงข้อความแจ้งเตือนความผิดพลาด
    function showError(message) {
        // ตรวจสอบว่ามีข้อความแจ้งเตือนอยู่แล้วหรือไม่
        let errorElement = document.querySelector('.error-message');
        
        // หากยังไม่มี ให้สร้างใหม่
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'error-message';
            registerForm.prepend(errorElement);
        }
        
        // แสดงข้อความแจ้งเตือน
        errorElement.textContent = message;
        errorElement.style.display = 'block';
        
        // ซ่อนข้อความแจ้งเตือนหลังจาก 5 วินาที
        setTimeout(() => {
            errorElement.style.display = 'none';
        }, 5000);
    }
});