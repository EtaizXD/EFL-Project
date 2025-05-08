/**
 * classifier.js - จัดการการสื่อสารกับ API และการประมวลผลผลลัพธ์การจำแนกเสียง
 */

/**
 * ส่งไฟล์เสียงไปวิเคราะห์ที่เซิร์ฟเวอร์
 * @param {File[]} files - อาร์เรย์ของไฟล์เสียงที่จะวิเคราะห์
 * @returns {Promise<Array>} - Promise ที่ให้ผลลัพธ์การจำแนก
 */
function classifyAudioFiles(files) {
    return new Promise((resolve, reject) => {
        const formData = new FormData();
        
        // เพิ่มไฟล์ทั้งหมดเข้าไปใน FormData
        files.forEach((file, index) => {
            formData.append('audio_files', file);
        });
        
        // ส่งคำขอไปยัง API endpoint
        fetch('/api/classify', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('การเชื่อมต่อกับเซิร์ฟเวอร์มีปัญหา');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            resolve(data.results);
        })
        .catch(error => {
            // หากกำลังทดสอบท้องถิ่นและยังไม่มี API ให้ใช้ข้อมูลจำลอง
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                console.warn('กำลังใช้ข้อมูลจำลองเนื่องจากไม่สามารถเชื่อมต่อกับ API ได้');
                resolve(simulateClassification(files));
            } else {
                reject(error);
            }
        });
    });
}

/**
 * จำลองผลการจำแนกด้วยข้อมูลสุ่ม (สำหรับการทดสอบเท่านั้น)
 * @param {File[]} files - อาร์เรย์ของไฟล์เสียง
 * @returns {Array} - อาร์เรย์ของผลลัพธ์การจำแนกจำลอง
 */
function simulateClassification(files) {
    return files.map(file => {
        // สร้างความน่าจะเป็นแบบสุ่มสำหรับแต่ละคลาส
        const highProb = Math.random() * 0.6;
        const mediumProb = Math.random() * (0.8 - highProb);
        const lowProb = 1 - highProb - mediumProb;
        
        // กำหนดคลาสที่ทำนายตามความน่าจะเป็นสูงสุด
        let predictedClass;
        if (highProb >= mediumProb && highProb >= lowProb) {
            predictedClass = 'High';
        } else if (mediumProb >= highProb && mediumProb >= lowProb) {
            predictedClass = 'Medium';
        } else {
            predictedClass = 'Low';
        }
        
        return {
            fileName: file.name,
            predictedClass: predictedClass,
            probabilities: {
                High: highProb,
                Medium: mediumProb,
                Low: lowProb
            }
        };
    });
}

/**
 * แปลงผลลัพธ์ดิบที่ได้จาก API ให้อยู่ในรูปแบบที่พร้อมแสดงผล
 * @param {Object} rawResults - ผลลัพธ์ดิบจาก API
 * @returns {Array} - อาร์เรย์ของผลลัพธ์ที่พร้อมแสดงผล
 */
function processResults(rawResults) {
    return rawResults.map(result => {
        return {
            fileName: result.file_name,
            predictedClass: result.predicted_class,
            probabilities: {
                High: result.probabilities.High || 0,
                Medium: result.probabilities.Medium || 0,
                Low: result.probabilities.Low || 0
            }
        };
    });
}