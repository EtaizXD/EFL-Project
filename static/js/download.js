/**
 * download.js - จัดการฟังก์ชันการดาวน์โหลดผลการประเมินการออกเสียง
 */

document.addEventListener('DOMContentLoaded', function() {
    // ค้นหาปุ่มดาวน์โหลด
    const downloadBtn = document.getElementById('downloadResultsBtn');
    
    // ถ้าไม่มีปุ่มดาวน์โหลดในหน้านี้ ให้ออกจากฟังก์ชัน
    if (!downloadBtn) return;
    
    // เพิ่ม event listener เมื่อคลิกปุ่มดาวน์โหลด
    downloadBtn.addEventListener('click', function() {
        downloadResults();
    });
    
    /**
     * ฟังก์ชันสำหรับดาวน์โหลดผลการประเมินเป็นไฟล์ CSV
     */
    function downloadResults() {
        // ค้นหาตารางผลลัพธ์
        const resultsTable = document.querySelector('.results-table');
        
        // ค้นหาส่วน tbody ของตาราง
        const tableBody = resultsTable.querySelector('tbody');
        
        // ถ้าไม่มีตารางผลลัพธ์หรือไม่มีแถวข้อมูลใน tbody ให้แสดงข้อความแจ้งเตือน
        if (!tableBody || tableBody.rows.length === 0) {
            alert(document.body.classList.contains('en') ? 
                'No results to download.' : 
                'ไม่มีผลลัพธ์ที่จะดาวน์โหลด');
            return;
        }
        
        // สร้างข้อมูลสำหรับคำนวณเปอร์เซ็นต์แต่ละระดับ
        let highCount = 0;
        let midCount = 0;
        let lowCount = 0;
        let totalCount = 0;
        let results = [];
        
        // วนลูปผ่านแถวข้อมูลเพื่อเก็บข้อมูลและนับจำนวนแต่ละระดับ
        for (let i = 0; i < tableBody.rows.length; i++) {
            const row = tableBody.rows[i];
            
            // ตรวจสอบว่ามีเซลล์พอไหม
            if (row.cells.length < 3) continue;
            
            // ดึงข้อมูลจากคอลัมน์ (ชื่อไฟล์, ระดับการออกเสียง, ความน่าจะเป็น)
            const filename = row.cells[0].textContent.trim();
            
            // ดึงระดับ (High, Mid, Low) จาก span ภายในเซลล์
            let level = '';
            const levelSpan = row.cells[1].querySelector('span');
            if (levelSpan) {
                if (levelSpan.classList.contains('classification-high')) {
                    level = 'High';
                    highCount++;
                } else if (levelSpan.classList.contains('classification-mid') || 
                           levelSpan.classList.contains('classification-medium')) {
                    level = 'Mid';
                    midCount++;
                } else if (levelSpan.classList.contains('classification-low')) {
                    level = 'Low';
                    lowCount++;
                }
            }
            
            // ดึงข้อมูลความน่าจะเป็นจากคอลัมน์ที่ 3
            let probabilities = { high: '0%', mid: '0%', low: '0%' };
            
            // ค้นหาแถบความน่าจะเป็นหรือข้อความแสดงเปอร์เซ็นต์
            const probabilityCell = row.cells[2];
            
            // วิธีที่ 1: ตรวจหาแถบความน่าจะเป็น (probability bar)
            const probabilityBar = probabilityCell.querySelector('.probabilities-bar');
            if (probabilityBar) {
                const highSegment = probabilityBar.querySelector('.probability-high');
                const midSegment = probabilityBar.querySelector('.probability-medium, .probability-mid');
                const lowSegment = probabilityBar.querySelector('.probability-low');
                
                // ดึงความกว้างของแต่ละส่วนจาก style (เช่น width: 70%)
                if (highSegment) {
                    const widthStyle = highSegment.style.width;
                    probabilities.high = widthStyle || '0%';
                }
                if (midSegment) {
                    const widthStyle = midSegment.style.width;
                    probabilities.mid = widthStyle || '0%';
                }
                if (lowSegment) {
                    const widthStyle = lowSegment.style.width;
                    probabilities.low = widthStyle || '0%';
                }
            } 
            // วิธีที่ 2: หากไม่มีแถบ ให้ดึงจากข้อความในเซลล์
            else {
                // แยกข้อความและหาเปอร์เซ็นต์
                const text = probabilityCell.textContent.trim();
                
                // ค้นหาเปอร์เซ็นต์ด้วย regex
                const highMatch = text.match(/High:?\s*(\d+(?:\.\d+)?)%/i);
                const midMatch = text.match(/Mid:?\s*(\d+(?:\.\d+)?)%/i);
                const lowMatch = text.match(/Low:?\s*(\d+(?:\.\d+)?)%/i);
                
                if (highMatch) probabilities.high = highMatch[1] + '%';
                if (midMatch) probabilities.mid = midMatch[1] + '%';
                if (lowMatch) probabilities.low = lowMatch[1] + '%';
            }
            
            // ตรวจสอบว่ามีชื่อไฟล์และระดับหรือไม่
            if (filename && level) {
                // เก็บข้อมูลเพื่อสร้าง CSV ภายหลัง
                results.push({
                    filename: filename,
                    level: level,
                    probabilities: probabilities
                });
                totalCount++;
            }
        }
        
        // คำนวณเปอร์เซ็นต์ของแต่ละระดับ
        const highPercent = totalCount > 0 ? (highCount / totalCount * 100).toFixed(2) : '0.00';
        const midPercent = totalCount > 0 ? (midCount / totalCount * 100).toFixed(2) : '0.00';
        const lowPercent = totalCount > 0 ? (lowCount / totalCount * 100).toFixed(2) : '0.00';
        
        // สร้างข้อมูล CSV พร้อมส่วนหัว
        let csvContent = 'Filename,Level,High Probability,Mid Probability,Low Probability\n';
        
        // เพิ่มข้อมูลแต่ละไฟล์
        results.forEach(result => {
            // ห่อชื่อไฟล์ด้วยเครื่องหมายคำพูดเพื่อรองรับกรณีที่มีเครื่องหมายคอมม่าในชื่อไฟล์
            const escapedFilename = `"${result.filename.replace(/"/g, '""')}"`;
            
            // ลบเครื่องหมาย % ออกเพื่อให้ CSV มีรูปแบบที่สอดคล้องกัน
            const highProb = result.probabilities.high.replace('%', '');
            const midProb = result.probabilities.mid.replace('%', '');
            const lowProb = result.probabilities.low.replace('%', '');
            
            csvContent += `${escapedFilename},${result.level},${highProb},${midProb},${lowProb}\n`;
        });
        
        // เพิ่มบรรทัดว่างและสรุปผล
        csvContent += '\n';
        csvContent += 'Summary Statistics\n';
        csvContent += `High Level,${highCount},${highPercent}%\n`;
        csvContent += `Mid Level,${midCount},${midPercent}%\n`;
        csvContent += `Low Level,${lowCount},${lowPercent}%\n`;
        csvContent += `Total Files,${totalCount},100.00%\n`;
        
        // สร้าง Blob จากข้อมูล CSV
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        
        // สร้าง URL สำหรับ Blob
        const url = URL.createObjectURL(blob);
        
        // สร้างลิงก์สำหรับดาวน์โหลด
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', 'pronunciation_assessment_results.csv');
        link.style.display = 'none';
        
        // เพิ่มลิงก์ลงในหน้าและคลิกเพื่อเริ่มการดาวน์โหลด
        document.body.appendChild(link);
        link.click();
        
        // ลบลิงก์และล้าง URL
        setTimeout(function() {
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }, 100);
    }
});