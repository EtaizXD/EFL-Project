/**
 * main.js - จัดการการทำงานของ UI หลัก
 * รองรับการทำงานแบบสองภาษา (TH/EN) และทำงานร่วมกับ API จำแนกเสียง
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const audioFileInput = document.getElementById('audioFileInput');
    const fileList = document.getElementById('fileList');
    const submitButton = document.getElementById('submitButton');
    const loader = document.getElementById('loader');
    const resultsSection = document.getElementById('resultsSection');
    const resultsTableBody = document.getElementById('resultsTableBody');
    const errorMessage = document.getElementById('errorMessage');
    const summaryStats = document.getElementById('summaryStats');
    
    // State
    let selectedFiles = [];
    
    // Maximum number of files
    const MAX_FILES = 10;
    
    // Add event listener to file input
    audioFileInput.addEventListener('change', handleFileSelection);
    submitButton.addEventListener('click', handleSubmission);
    
    /**
     * จัดการกับเหตุการณ์ที่ผู้ใช้เลือกไฟล์
     */
    function handleFileSelection(event) {
        const newFiles = Array.from(event.target.files);
        
        // Clear error message
        errorMessage.textContent = '';
        errorMessage.style.display = 'none';
        
        // ตรวจสอบประเภทไฟล์
        const invalidFiles = newFiles.filter(file => !file.name.toLowerCase().endsWith('.wav'));
        if (invalidFiles.length > 0) {
            showError(document.body.classList.contains('en') ? 
                'Please select only WAV files.' : 
                'กรุณาเลือกเฉพาะไฟล์ WAV เท่านั้น');
            return;
        }
        
        // เพิ่มไฟล์ใหม่เข้าไปในคอลเลกชัน
        selectedFiles = [...selectedFiles, ...newFiles];
        
        // จำกัดจำนวนไฟล์ไม่เกิน 10 ไฟล์
        if (selectedFiles.length > MAX_FILES) {
            selectedFiles = selectedFiles.slice(0, MAX_FILES);
            showError(document.body.classList.contains('en') ? 
                'Maximum 10 files allowed. Only the first 10 files will be processed.' : 
                'จำกัดจำนวนไฟล์สูงสุด 10 ไฟล์ เลือกเฉพาะ 10 ไฟล์แรกเท่านั้น');
        }
        
        // อัพเดท UI แสดงรายการไฟล์
        updateFileList();
        
        // เปิด/ปิดปุ่ม submit ตามจำนวนไฟล์ที่เลือก
        submitButton.disabled = selectedFiles.length === 0;
    }
    
    /**
     * อัพเดท UI แสดงรายการไฟล์ที่เลือก
     */
    function updateFileList() {
        fileList.innerHTML = '';
        
        selectedFiles.forEach((file, index) => {
            const fileItem = document.createElement('li');
            fileItem.className = 'file-item';
            
            const fileName = document.createElement('span');
            fileName.className = 'file-name';
            fileName.textContent = file.name;
            
            const removeButton = document.createElement('button');
            removeButton.className = 'remove-file';
            removeButton.innerHTML = '<i class="fas fa-times"></i>';
            removeButton.addEventListener('click', function() {
                // Remove file from array
                const index = selectedFiles.indexOf(file);
                if (index !== -1) {
                    selectedFiles.splice(index, 1);
                }
                
                // Remove list item
                fileList.removeChild(fileItem);
                
                // Update submit button
                submitButton.disabled = selectedFiles.length === 0;
            });
            
            // Add elements to list item
            fileItem.appendChild(fileName);
            fileItem.appendChild(removeButton);
            
            // Add list item to file list
            fileList.appendChild(fileItem);
        });
    }
    
    /**
     * แสดงข้อความแจ้งเตือนความผิดพลาด
     */
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        setTimeout(() => {
            errorMessage.style.display = 'none';
        }, 5000);
    }
    
    /**
     * จัดการกับการส่งฟอร์ม
     */
    function handleSubmission() {
        if (selectedFiles.length === 0) {
            showError(document.body.classList.contains('en') ? 
                'Please select at least 1 file.' : 
                'กรุณาเลือกอย่างน้อย 1 ไฟล์');
            return;
        }
        
        // แสดงตัวโหลด
        loader.style.display = 'flex';
        resultsSection.style.display = 'none';
        
        // Create form data
        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('audio_files', file);
        });
        
        // ส่งคำขอไปยัง API endpoint
        fetch('/api/classify', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(document.body.classList.contains('en') ? 
                    'Connection to server failed' : 
                    'การเชื่อมต่อกับเซิร์ฟเวอร์มีปัญหา');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // ซ่อนตัวโหลดและแสดงผลลัพธ์
            loader.style.display = 'none';
            displayResults(data.results);
            
            // เลื่อนไปยังส่วนผลลัพธ์
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        })
        .catch(error => {
            loader.style.display = 'none';
            
            // หากกำลังทดสอบท้องถิ่นและยังไม่มี API ให้ใช้ข้อมูลจำลอง
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                console.warn(document.body.classList.contains('en') ? 
                    'Using simulation data because API connection failed' : 
                    'กำลังใช้ข้อมูลจำลองเนื่องจากไม่สามารถเชื่อมต่อกับ API ได้');
                
                displayResults(simulateClassification(selectedFiles));
                resultsSection.scrollIntoView({ behavior: 'smooth' });
            } else {
                showError(document.body.classList.contains('en') ? 
                    'Error in analysis: ' + error.message : 
                    'เกิดข้อผิดพลาดในการวิเคราะห์: ' + error.message);
            }
        });
    }
    
    /**
     * จำลองผลการจำแนกด้วยข้อมูลสุ่ม (สำหรับการทดสอบเท่านั้น)
     */
    function simulateClassification(files) {
        return files.map(file => {
            // สร้างความน่าจะเป็นแบบสุ่มสำหรับแต่ละคลาส
            const highProb = Math.random() * 0.6;
            const midProb = Math.random() * (0.8 - highProb);
            const lowProb = 1 - highProb - midProb;
            
            // กำหนดคลาสที่ทำนายตามความน่าจะเป็นสูงสุด
            let predictedClass;
            if (highProb >= midProb && highProb >= lowProb) {
                predictedClass = 'High';
            } else if (midProb >= highProb && midProb >= lowProb) {
                predictedClass = 'Mid';
            } else {
                predictedClass = 'Low';
            }
            
            return {
                file_name: file.name,
                predicted_class: predictedClass,
                probabilities: {
                    High: highProb,
                    Medium: midProb,
                    Low: lowProb
                }
            };
        });
    }
    
    /**
     * แสดงผลลัพธ์การจำแนก
     */
    function displayResults(rawResults) {
        console.log("Raw results from API:", rawResults);
        
        // Process the results to standardize format - ไม่จำเป็นต้องแปลง Medium เป็น Mid แล้ว
        // แปลง results และแก้ไขคำว่า 'Medium' เป็น 'Mid'
        const results = rawResults.map(result => {
            // แปลง predictedClass
            let predictedClass = result.predicted_class;
            if (predictedClass === 'Medium') {
                predictedClass = 'Mid';
            }
            
            // แปลง probabilities
            const probabilities = {};
            Object.keys(result.probabilities).forEach(key => {
                if (key === 'Medium') {
                    probabilities['Mid'] = result.probabilities[key];
                } else {
                    probabilities[key] = result.probabilities[key];
                }
            });
            
            return {
                fileName: result.file_name,
                predictedClass: predictedClass,
                probabilities: probabilities
            };
        });
        
        // Clear previous results
        resultsTableBody.innerHTML = '';
        summaryStats.innerHTML = '';
        resultsSection.style.display = 'block';
        
        // นับจำนวนไฟล์ในแต่ละระดับ
        const counts = {
            'High': 0,
            'Mid': 0,
            'Low': 0
        };
        
        results.forEach(result => {
            // ไม่ต้องแปลงคลาสจาก Medium -> Mid แล้ว
            const displayClass = result.predictedClass;
            counts[displayClass]++;  // อัปเดตค่าในตัวแปร counts
            
            const row = document.createElement('tr');
            
            // คอลัมน์ชื่อไฟล์
            const fileNameCell = document.createElement('td');
            fileNameCell.textContent = result.fileName;
            
            // คอลัมน์การจำแนก
            const classCell = document.createElement('td');
            const classSpan = document.createElement('span');
            
            // กำหนดชื่อคลาสสำหรับการจัดรูปแบบ CSS
            const cssClass = displayClass.toLowerCase();
            classSpan.textContent = displayClass;
            classSpan.className = `classification-${cssClass}`;
            classCell.appendChild(classSpan);
            
            // คอลัมน์ความน่าจะเป็น
            const probCell = document.createElement('td');
            
            // สร้างแถบความน่าจะเป็น
            const probBar = document.createElement('div');
            probBar.className = 'probabilities-bar';
            
            // เพิ่มส่วนย่อยสำหรับแต่ละคลาส - ใช้คลาสที่มีอยู่ใน probabilities โดยตรง
            Object.keys(result.probabilities).forEach(cls => {
                const segment = document.createElement('div');
                segment.className = `probability-segment probability-${cls.toLowerCase()}`;
                
                // ใช้ค่าความน่าจะเป็นที่ได้จากโมเดลโดยตรง
                const width = (result.probabilities[cls] || 0) * 100;
                segment.style.width = `${width}%`;
                probBar.appendChild(segment);
            });
            
            // สร้างป้ายกำกับความน่าจะเป็น
            const probLabels = document.createElement('div');
            probLabels.className = 'probability-label';
            
            // แสดงความน่าจะเป็นของแต่ละคลาสโดยตรง
            Object.keys(result.probabilities).forEach(cls => {
                const label = document.createElement('span');
                const probability = result.probabilities[cls] * 100;

                // แปลงชื่อที่แสดงจาก 'Medium' เป็น 'Mid'
                let displayClass = cls;
                if (cls === 'Medium') {
                    displayClass = 'Mid';
                }
                label.textContent = `${cls}: ${probability.toFixed(1)}%`;
                probLabels.appendChild(label);
            });
            
            probCell.appendChild(probBar);
            probCell.appendChild(probLabels);
            
            // เพิ่มเซลล์ให้กับแถว
            row.appendChild(fileNameCell);
            row.appendChild(classCell);
            row.appendChild(probCell);
            
            // เพิ่มแถวในตาราง
            resultsTableBody.appendChild(row);
        });
        
        // แสดงสรุปผล
        displaySummary(counts, results.length);
    }
    
    /**
     * แสดงสรุปผลการประเมิน
     */
    function displaySummary(counts, totalFiles) {
        // สร้าง HTML สำหรับสรุปผล (รองรับ 2 ภาษา)
        const isEnglish = document.body.classList.contains('en');
        
        const totalLabel = isEnglish ? 'Total Files' : 'จำนวนไฟล์ทั้งหมด';
        const highLabel = isEnglish ? 'High Level' : 'ระดับสูง';
        const midLabel = isEnglish ? 'Mid Level' : 'ระดับกลาง';
        const lowLabel = isEnglish ? 'Low Level' : 'ระดับต่ำ';
        
        // สร้างอิลิเมนต์สำหรับแต่ละหมวดหมู่
        const totalStat = createStatItem(totalFiles, totalLabel, '#4361ee');
        const highStat = createStatItem(counts.High, highLabel, '#7209b7');
        const midStat = createStatItem(counts.Mid, midLabel, '#f72585');
        const lowStat = createStatItem(counts.Low, lowLabel, '#4cc9f0');
        
        // เพิ่มสถิติในส่วนสรุป
        summaryStats.appendChild(totalStat);
        summaryStats.appendChild(highStat);
        summaryStats.appendChild(midStat);
        summaryStats.appendChild(lowStat);
    }
    
    /**
     * สร้างรายการสถิติสำหรับการแสดงผลสรุป
     */
    function createStatItem(value, label, color) {
        const statItem = document.createElement('div');
        statItem.className = 'summary-item';
        
        // เพิ่มคลาสตามประเภทของรายการ
        if (label === 'Total Files' || label === 'จำนวนไฟล์ทั้งหมด') {
            statItem.classList.add('total-item');
        } else if (label === 'High Level' || label === 'ระดับสูง') {
            statItem.classList.add('high-level');
        } else if (label === 'Mid Level' || label === 'ระดับกลาง') {
            statItem.classList.add('mid-level');
        } else if (label === 'Low Level' || label === 'ระดับต่ำ') {
            statItem.classList.add('low-level');
        }
        
        const statTitle = document.createElement('h4');
        statTitle.textContent = label;
        
        const statValue = document.createElement('div');
        statValue.className = 'summary-count';
        statValue.textContent = value;
        // ไม่ต้องกำหนดสี เพราะจะใช้สีขาวจาก CSS
        
        const statPercent = document.createElement('span');
        statPercent.className = 'summary-percent';
        
        // คำนวณเปอร์เซ็นต์เฉพาะเมื่อไม่ใช่ยอดรวม
        if (label !== 'Total Files' && label !== 'จำนวนไฟล์ทั้งหมด') {
            const totalCount = parseInt(document.querySelectorAll('.summary-item')[0]?.querySelector('.summary-count')?.textContent) || selectedFiles.length;
            if (totalCount > 0) {
                statPercent.textContent = `(${(value / totalCount * 100).toFixed(1)}%)`;
            }
        }
        
        statItem.appendChild(statTitle);
        statItem.appendChild(statValue);
        statItem.appendChild(statPercent);
        
        return statItem;
    }
    
    /**
     * ฟังก์ชั่นเพื่อรับป้ายชื่อภาษาไทย
     */
    function getThaiLabel(label) {
        switch(label) {
            case 'Total Files':
            case 'จำนวนไฟล์ทั้งหมด':
                return 'จำนวนไฟล์ทั้งหมด';
            case 'High Level':
            case 'ระดับสูง':
                return 'ระดับสูง';
            case 'Mid Level':
            case 'ระดับกลาง':
                return 'ระดับกลาง';
            case 'Low Level':
            case 'ระดับต่ำ':
                return 'ระดับต่ำ';
            default:
                return label;
        }
    }

    /**
     * ฟังก์ชั่นเพื่อรับป้ายชื่อภาษาอังกฤษ
     */
    function getEnglishLabel(label) {
        switch(label) {
            case 'Total Files':
            case 'จำนวนไฟล์ทั้งหมด':
                return 'Total Files';
            case 'High Level':
            case 'ระดับสูง':
                return 'High Level';
            case 'Mid Level':
            case 'ระดับกลาง':
                return 'Mid Level';
            case 'Low Level':
            case 'ระดับต่ำ':
                return 'Low Level';
            default:
                return label;
        }
    }

    // เริ่มต้นสำหรับรีเซ็ตหน้า UI เมื่อโหลดครั้งแรก
    function initializeUI() {
        // ซ่อนส่วนผลลัพธ์และข้อความแจ้งเตือนเมื่อเริ่มต้น
        resultsSection.style.display = 'none';
        errorMessage.style.display = 'none';
        loader.style.display = 'none';
        
        // ปิดปุ่ม submit เมื่อยังไม่มีการเลือกไฟล์
        submitButton.disabled = true;
    }
    
    // เรียกฟังก์ชันเริ่มต้น
    initializeUI();
});