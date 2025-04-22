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
    const generateFinalVideo = document.getElementById('generateFinalVideo').checked;
    const audioConsistency = document.getElementById('audioConsistency').checked; // Get the value of the new checkbox

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
        body: JSON.stringify({
            folderPath: folderPath,
            generateFinalVideo: generateFinalVideo,
            audioConsistency: audioConsistency // Include the new checkbox value in the request
        })
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

document.getElementById('cropButton').addEventListener('click', () => {
    const imageFileInput = document.getElementById('imageFile');
    const cropWidthInput = document.getElementById('cropWidth');
    const cropHeightInput = document.getElementById('cropHeight');

    if (!imageFileInput.files.length) {
        alert('Please select an image file.');
        return;
    }

    const file = imageFileInput.files[0];
    const width = parseInt(cropWidthInput.value, 10);
    const height = parseInt(cropHeightInput.value, 10);

    if (isNaN(width) || isNaN(height) || width <= 0 || height <= 0) {
        alert('Please enter valid width and height values.');
        return;
    }

    const reader = new FileReader();
    reader.onload = function (event) {
        const imageSrc = event.target.result;
        const cropUI = document.createElement('div');
        cropUI.style.position = 'fixed';
        cropUI.style.top = '0';
        cropUI.style.left = '0';
        cropUI.style.width = '100%';
        cropUI.style.height = '100%';
        cropUI.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
        cropUI.style.zIndex = '1000';
        cropUI.style.display = 'flex';
        cropUI.style.justifyContent = 'center';
        cropUI.style.alignItems = 'center';

        const image = document.createElement('img');
        image.src = imageSrc;
        image.style.position = 'relative';
        image.style.maxWidth = '100%';
        image.style.maxHeight = '100%';
        cropUI.appendChild(image);

        const redBox = document.createElement('div');
        redBox.style.position = 'absolute';
        redBox.style.border = '2px solid red';
        cropUI.appendChild(redBox);

        document.body.appendChild(cropUI);

        image.onload = () => {
            const naturalWidth = image.naturalWidth;
            const naturalHeight = image.naturalHeight;
            const displayWidth = image.clientWidth;
            const displayHeight = image.clientHeight;

            const rect = image.getBoundingClientRect(); // Get the actual position of the image
            const widthRatio = displayWidth / naturalWidth;
            const heightRatio = displayHeight / naturalHeight;

            redBox.style.width = `${width * widthRatio}px`;
            redBox.style.height = `${height * heightRatio}px`;

            cropUI.addEventListener('mousemove', (e) => {
                const x = Math.min(Math.max(e.clientX - rect.left - (width * widthRatio) / 2, 0), rect.width - width * widthRatio);
                const y = Math.min(Math.max(e.clientY - rect.top - (height * heightRatio) / 2, 0), rect.height - height * heightRatio);
                redBox.style.left = `${rect.left + x}px`;
                redBox.style.top = `${rect.top + y}px`;
            });

            cropUI.addEventListener('click', (e) => {
                const x = Math.min(Math.max(e.clientX - rect.left - (width * widthRatio) / 2, 0), rect.width - width * widthRatio);
                const y = Math.min(Math.max(e.clientY - rect.top - (height * heightRatio) / 2, 0), rect.height - height * heightRatio);

                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(image, x / widthRatio, y / heightRatio, width, height, 0, 0, width, height);

                canvas.toBlob((blob) => {
                    const link = document.createElement('a');
                    const timestamp = new Date().getTime();
                    link.download = `cropped_image_${timestamp}.png`;
                    link.href = URL.createObjectURL(blob);
                    link.click();
                });

                document.body.removeChild(cropUI);
            });

            cropUI.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                document.body.removeChild(cropUI);
            });
        };
    };

    reader.readAsDataURL(file);
});