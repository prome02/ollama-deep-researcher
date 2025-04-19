// Ensure the left and right sections are properly initialized
const leftSection = document.querySelector('.col-md-6:first-child');
const rightSection = document.querySelector('.col-md-6:last-child');

if (!leftSection || !rightSection) {
    console.error('Left or right section not found. Ensure the HTML structure matches the CSS.');
}

document.getElementById('uploadJsonButton').addEventListener('click', async (e) => {
    e.preventDefault();
    const formData = new FormData();
    const fileInput = document.getElementById('jsonFile');
    formData.append('jsonFile', fileInput.files[0]);

    const response = await fetch('/upload-json', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();
    const resultDiv = document.getElementById('result');
    if (response.ok) {
        resultDiv.innerHTML = `<div class="alert alert-success"><p>Processing completed successfully:</p><pre>${JSON.stringify(result, null, 2)}</pre></div>`;
    } else {
        resultDiv.innerHTML = `<div class="alert alert-danger"><p>Error: ${result.error}</p></div>`;
    }
});

function submitFolderPath() {
    const folderPath = document.getElementById('folderPath').value;
    const progressBarContainer = document.getElementById('progressBarContainer');
    const progressBar = document.getElementById('progressBar');

    progressBarContainer.style.display = 'block';
    progressBar.style.width = '0%';
    progressBar.setAttribute('aria-valuenow', 0);

    fetch('/process-folder', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ folderPath: folderPath })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(`Error: ${data.error}`);
        } else {
            const interval = setInterval(() => {
                fetch(`/progress/${encodeURIComponent(folderPath)}`)
                    .then(response => response.json())
                    .then(progressData => {
                        const progress = progressData.progress;
                        progressBar.style.width = `${progress}%`;
                        progressBar.setAttribute('aria-valuenow', progress);

                        if (progress >= 100) {
                            clearInterval(interval);
                            alert('Processing completed successfully!');
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching progress:', error);
                        clearInterval(interval);
                    });
            }, 1000);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while processing the folder.');
    });
}