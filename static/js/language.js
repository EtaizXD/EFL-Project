document.addEventListener('DOMContentLoaded', function() {
    // Get language buttons
    const langThBtn = document.getElementById('langTH');
    const langEnBtn = document.getElementById('langEN');
    
    // Check for stored language preference
    const storedLang = localStorage.getItem('preferredLanguage');
    if (storedLang === 'en') {
        document.body.classList.add('en');
        langThBtn.classList.remove('active');
        langEnBtn.classList.add('active');
    } else {
        // Default is Thai
        document.body.classList.remove('en');
        langThBtn.classList.add('active');
        langEnBtn.classList.remove('active');
    }
    
    // Add event listeners to language buttons
    langThBtn.addEventListener('click', function() {
        document.body.classList.remove('en');
        langThBtn.classList.add('active');
        langEnBtn.classList.remove('active');
        localStorage.setItem('preferredLanguage', 'th');
    });
    
    langEnBtn.addEventListener('click', function() {
        document.body.classList.add('en');
        langThBtn.classList.remove('active');
        langEnBtn.classList.add('active');
        localStorage.setItem('preferredLanguage', 'en');
    });
});