// Add selector functionality
document.getElementById('addSelector')?.addEventListener('click', function() {
    const container = document.getElementById('selectorsContainer');
    const newSelector = document.createElement('div');
    newSelector.className = 'input-group mb-2';
    newSelector.innerHTML = `
        <input type="text" class="form-control selector-key" placeholder="Key (e.g., title)" name="selector-key[]">
        <input type="text" class="form-control selector-value" placeholder="CSS Selector (e.g., h1)" name="selector-value[]">
        <button type="button" class="btn btn-danger remove-selector">
            <i class="bi bi-trash"></i>
        </button>
    `;
    container.appendChild(newSelector);
    attachRemoveListener(newSelector.querySelector('.remove-selector'));
});

// Add HTML selector functionality
document.getElementById('addHtmlSelector')?.addEventListener('click', function() {
    const container = document.getElementById('htmlSelectorsContainer');
    const newSelector = document.createElement('div');
    newSelector.className = 'input-group mb-2';
    newSelector.innerHTML = `
        <input type="text" class="form-control html-selector-key" placeholder="Key (e.g., title)" name="html-selector-key[]">
        <input type="text" class="form-control html-selector-value" placeholder="CSS Selector (e.g., h1)" name="html-selector-value[]">
        <button type="button" class="btn btn-danger remove-html-selector">
            <i class="bi bi-trash"></i>
        </button>
    `;
    container.appendChild(newSelector);
    attachRemoveHtmlListener(newSelector.querySelector('.remove-html-selector'));
});

// Attach remove listeners
function attachRemoveListener(button) {
    button.addEventListener('click', function() {
        this.closest('.input-group').remove();
    });
}

function attachRemoveHtmlListener(button) {
    button.addEventListener('click', function() {
        this.closest('.input-group').remove();
    });
}

// Attach listeners to existing remove buttons
document.querySelectorAll('.remove-selector').forEach(btn => {
    attachRemoveListener(btn);
});

document.querySelectorAll('.remove-html-selector').forEach(btn => {
    attachRemoveHtmlListener(btn);
});

// URL Scraping Form Handler
document.getElementById('urlScrapingForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const url = document.getElementById('urlInput').value;
    const selectors = {};
    
    // Collect selectors
    document.querySelectorAll('#selectorsContainer .input-group').forEach(group => {
        const key = group.querySelector('.selector-key').value.trim();
        const value = group.querySelector('.selector-value').value.trim();
        if (key && value) {
            selectors[key] = value;
        }
    });
    
    // Show loading
    document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('resultsCard').style.display = 'none';
    
    try {
        const response = await fetch('/api/v1/scraping/scrape-url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                selectors: Object.keys(selectors).length > 0 ? selectors : null
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to scrape website');
        }
        
        displayResults(data);
    } catch (error) {
        displayError(error.message);
    } finally {
        document.getElementById('loadingSpinner').style.display = 'none';
    }
});

// HTML Scraping Form Handler
document.getElementById('htmlScrapingForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const htmlContent = document.getElementById('htmlContent').value;
    const selectors = {};
    
    // Collect selectors
    document.querySelectorAll('#htmlSelectorsContainer .input-group').forEach(group => {
        const key = group.querySelector('.html-selector-key').value.trim();
        const value = group.querySelector('.html-selector-value').value.trim();
        if (key && value) {
            selectors[key] = value;
        }
    });
    
    // Show loading
    document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('resultsCard').style.display = 'none';
    
    try {
        const response = await fetch('/api/v1/scraping/scrape-html', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                html_content: htmlContent,
                selectors: Object.keys(selectors).length > 0 ? selectors : null
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to scrape HTML');
        }
        
        displayResults(data);
    } catch (error) {
        displayError(error.message);
    } finally {
        document.getElementById('loadingSpinner').style.display = 'none';
    }
});

// Display results
function displayResults(data) {
    const resultsContent = document.getElementById('resultsContent');
    let html = '<div class="accordion" id="resultsAccordion">';
    
    // Basic Info
    if (data.url) {
        html += `
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#basicInfo">
                        <strong>Basic Information</strong>
                    </button>
                </h2>
                <div id="basicInfo" class="accordion-collapse collapse show" data-bs-parent="#resultsAccordion">
                    <div class="accordion-body">
                        <p><strong>URL:</strong> ${data.url || 'N/A'}</p>
                        <p><strong>Status Code:</strong> ${data.status_code || 'N/A'}</p>
                        <p><strong>Title:</strong> ${data.title || 'N/A'}</p>
                        <p><strong>Meta Description:</strong> ${data.meta_description || 'N/A'}</p>
                    </div>
                </div>
            </div>
        `;
    } else {
        html += `
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#basicInfo">
                        <strong>Basic Information</strong>
                    </button>
                </h2>
                <div id="basicInfo" class="accordion-collapse collapse show" data-bs-parent="#resultsAccordion">
                    <div class="accordion-body">
                        <p><strong>Title:</strong> ${data.title || 'N/A'}</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Text Content
    if (data.text_content) {
        const truncatedText = data.text_content.length > 500 
            ? data.text_content.substring(0, 500) + '...' 
            : data.text_content;
        html += `
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#textContent">
                        <strong>Text Content</strong> <span class="badge bg-secondary ms-2">${data.text_content.length} chars</span>
                    </button>
                </h2>
                <div id="textContent" class="accordion-collapse collapse" data-bs-parent="#resultsAccordion">
                    <div class="accordion-body">
                        <pre class="bg-light p-3" style="max-height: 400px; overflow-y: auto;">${truncatedText}</pre>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Links
    if (data.links && data.links.length > 0) {
        html += `
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#links">
                        <strong>Links</strong> <span class="badge bg-secondary ms-2">${data.links.length}</span>
                    </button>
                </h2>
                <div id="links" class="accordion-collapse collapse" data-bs-parent="#resultsAccordion">
                    <div class="accordion-body">
                        <ul class="list-group">
                            ${data.links.slice(0, 50).map(link => `
                                <li class="list-group-item">
                                    <strong>${link.text || '(no text)'}</strong><br>
                                    <small class="text-muted">${link.href}</small>
                                </li>
                            `).join('')}
                            ${data.links.length > 50 ? `<li class="list-group-item text-muted">... and ${data.links.length - 50} more</li>` : ''}
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Images
    if (data.images && data.images.length > 0) {
        html += `
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#images">
                        <strong>Images</strong> <span class="badge bg-secondary ms-2">${data.images.length}</span>
                    </button>
                </h2>
                <div id="images" class="accordion-collapse collapse" data-bs-parent="#resultsAccordion">
                    <div class="accordion-body">
                        <ul class="list-group">
                            ${data.images.slice(0, 50).map(img => `
                                <li class="list-group-item">
                                    <strong>Alt:</strong> ${img.alt || '(no alt)'}<br>
                                    <small class="text-muted">${img.src}</small>
                                </li>
                            `).join('')}
                            ${data.images.length > 50 ? `<li class="list-group-item text-muted">... and ${data.images.length - 50} more</li>` : ''}
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Custom Data
    if (data.custom_data && Object.keys(data.custom_data).length > 0) {
        html += `
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#customData">
                        <strong>Custom Data</strong>
                    </button>
                </h2>
                <div id="customData" class="accordion-collapse collapse" data-bs-parent="#resultsAccordion">
                    <div class="accordion-body">
                        <pre class="bg-light p-3">${JSON.stringify(data.custom_data, null, 2)}</pre>
                    </div>
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    
    // Full JSON View
    html += `
        <div class="mt-4">
            <h5>Full JSON Response</h5>
            <pre class="bg-light p-3" style="max-height: 500px; overflow-y: auto;" id="jsonOutput">${JSON.stringify(data, null, 2)}</pre>
        </div>
    `;
    
    resultsContent.innerHTML = html;
    document.getElementById('resultsCard').style.display = 'block';
    window.scrapingResults = data; // Store for copy function
}

// Display error
function displayError(message) {
    const resultsContent = document.getElementById('resultsContent');
    resultsContent.innerHTML = `
        <div class="alert alert-danger" role="alert">
            <h5><i class="bi bi-exclamation-triangle"></i> Error</h5>
            <p>${message}</p>
        </div>
    `;
    document.getElementById('resultsCard').style.display = 'block';
}

// Copy results function
function copyResults() {
    if (window.scrapingResults) {
        const jsonString = JSON.stringify(window.scrapingResults, null, 2);
        navigator.clipboard.writeText(jsonString).then(() => {
            alert('Results copied to clipboard!');
        }).catch(err => {
            console.error('Failed to copy:', err);
            // Fallback: select text
            const jsonOutput = document.getElementById('jsonOutput');
            if (jsonOutput) {
                const range = document.createRange();
                range.selectNode(jsonOutput);
                window.getSelection().removeAllRanges();
                window.getSelection().addRange(range);
                alert('Please manually copy the selected text');
            }
        });
    }
}
