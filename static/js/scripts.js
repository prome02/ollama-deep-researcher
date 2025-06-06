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

function closeMp3Dialog() {
    document.getElementById('mp3Dialog').style.display = 'none';
    document.getElementById('dialogOverlay').style.display = 'none';
}

function openMp3Dialog() {
    document.getElementById('mp3Dialog').style.display = 'block';
    document.getElementById('dialogOverlay').style.display = 'block';
}

document.getElementById('readMp3StatusButton').addEventListener('click', async () => {
    const fileInput = document.getElementById('jsonFile');
    if (!fileInput.files.length) {
        alert('Please select a JSON file first.');
        return;
    }

    const file = fileInput.files[0];
    const reader = new FileReader();

    reader.onload = async (event) => {
        try {
            const jsonData = JSON.parse(event.target.result);
            const contentArray = jsonData['content'];
            const nameList = contentArray.map(item => `${item['No.']} ${item['caption']}`);

            const nameListContainer = document.getElementById('nameListContainer');
            nameListContainer.innerHTML = '';

            nameList.forEach((name, index) => {
                // 創建容器元素 (推薦使用 div 或 li)
                const container = document.createElement('div');
                container.className = 'checkbox-container'; // 用於後續CSS排版
                
                // 創建 checkbox
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = `item-${index}`; // 必須有唯一ID供label關聯
                checkbox.className = 'item-checkbox';
                checkbox.dataset.index = index;
            
                // 創建 label 並關聯 checkbox
                const label = document.createElement('label');
                label.htmlFor = `item-${index}`; // 與checkbox的id匹配
                label.textContent = name; // 顯示文字內容
                
                // 組合元素
                container.appendChild(checkbox);
                container.appendChild(label);
                nameListContainer.appendChild(container);
            });
            

            const chkAll = document.getElementById('chk_all');
            chkAll.checked = false;
            chkAll.addEventListener('change', () => {
                document.querySelectorAll('.item-checkbox').forEach(checkbox => {
                    checkbox.checked = chkAll.checked;
                });
            });

            openMp3Dialog();
        } catch (error) {
            alert('Invalid JSON file.');
        }
    };

    reader.readAsText(file);
});

document.getElementById('runButton').addEventListener('click', async () => {
    const fileInput = document.getElementById('jsonFile');
    if (!fileInput.files.length) {
        alert('Please select a JSON file first.');
        return;
    }

    const formData = new FormData();
    formData.append('jsonFile', fileInput.files[0]);

    const mp3Modes = Array.from(document.querySelectorAll('.item-checkbox')).map(checkbox => checkbox.checked);
    console.log('mp3Modes:', mp3Modes); // Print mp3Modes to console
    formData.append('mp3_modes', JSON.stringify(mp3Modes));

    const response = await fetch('/upload-json', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();
    if (response.ok) {
        alert('Processing completed successfully.');
    } else {
        alert(`Error: ${result.error}`);
    }

    closeMp3Dialog();
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

function checkProgress(folderPath) {
    fetch(`/progress/${folderPath}`)
        .then(response => response.json())
        .then(data => {
            console.log(`Progress: ${data.progress}%`);
            if (data.complete) {
                console.log("Processing complete!");
                clearInterval(progressInterval); // 停止輪詢
            }
        })
        .catch(error => console.error('Error:', error));
}


function startProcessing(folderPath) {
    const generateFinalVideo = document.getElementById('generateFinalVideo').checked;
    const audioConsistency = document.getElementById('audioConsistency').checked;

    fetch('/process-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folderPath: folderPath, generateFinalVideo: generateFinalVideo, audioConsistency: audioConsistency })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log('Processing started successfully');
            startProgressPolling(folderPath); // 開始輪詢進度
        } else {
            console.error('Error starting processing:', data.message);
        }
    })
    .catch(error => console.error('Error:', error));
}

function startProgressPolling(folderPath) {
    const normalizedPath = folderPath.replace(/\\/g, '/'); // 將反斜杠替換為正斜杠
    const progressInterval = setInterval(() => {
        fetch(`/progress/${encodeURIComponent(normalizedPath)}`)
            .then(response => response.json())
            .then(data => {
                console.log(`Progress: ${data.progress}%`);
                if (data.progress === 100) {
                    console.log('Processing complete!');
                    clearInterval(progressInterval); // 停止輪詢
                }
            })
            .catch(error => {
                console.error('Error fetching progress:', error);
                clearInterval(progressInterval); // 停止輪詢
            });
    }, 1000); // 每秒輪詢一次
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