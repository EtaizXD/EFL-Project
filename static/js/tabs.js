/**
 * tabs.js - จัดการการทำงานของแท็บระดับการศึกษา
 */

document.addEventListener('DOMContentLoaded', function() {
    // เลือกปุ่มแท็บทั้งหมด
    const tabButtons = document.querySelectorAll('.tab-btn');
    
    // เพิ่มการจัดการเหตุการณ์คลิกให้กับแต่ละปุ่ม
    tabButtons.forEach(button => {
        // ปิดการใช้งานปุ่มทั้งหมดยกเว้นระดับมหาวิทยาลัย
        if (button.getAttribute('data-level') !== 'university') {
            button.disabled = true;
        }
        
        button.addEventListener('click', function() {
            // ถ้าปุ่มถูก disabled ไม่ต้องทำอะไร
            if (this.disabled) return;
            
            // ลบคลาส active จากปุ่มทั้งหมด
            tabButtons.forEach(btn => {
                btn.classList.remove('active');
            });
            
            // เพิ่มคลาส active ให้กับปุ่มที่คลิก
            this.classList.add('active');
            
            // ดึงระดับการศึกษาจากปุ่มที่คลิก
            const level = this.getAttribute('data-level');
            
            // ในอนาคตอาจจะมีการเปลี่ยน API endpoint หรือการทำงานตามระดับที่เลือก
            // เช่น เปลี่ยน URL ของ API หรือการแสดงผลข้อมูลต่างๆ
            
            // รีเซ็ตฟอร์มและผลลัพธ์
            resetForm();
        });
    });
    
    /**
     * รีเซ็ตฟอร์มและผลลัพธ์
     */
    function resetForm() {
        // ล้างรายการไฟล์
        const fileList = document.getElementById('fileList');
        if (fileList) fileList.innerHTML = '';
        
        // ปิดการใช้งานปุ่ม submit
        const submitButton = document.getElementById('submitButton');
        if (submitButton) submitButton.disabled = true;
        
        // ซ่อนผลลัพธ์
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) resultsSection.style.display = 'none';
        
        // รีเซ็ตค่าการอัพโหลดไฟล์
        const fileInput = document.getElementById('audioFileInput');
        if (fileInput) fileInput.value = '';
        
        // ล้างข้อความแจ้งเตือน
        const errorMessage = document.getElementById('errorMessage');
        if (errorMessage) {
            errorMessage.textContent = '';
            errorMessage.style.display = 'none';
        }
        
        // รีเซ็ตตัวแปรที่เก็บไฟล์ใน main.js (ต้องเข้าถึงจาก window)
        if (window.selectedFiles) {
            window.selectedFiles = [];
        }
    }
});