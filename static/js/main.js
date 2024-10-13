let detectedObjects = [];

document.addEventListener('DOMContentLoaded', () => {
    const startDetectBtn = document.getElementById("start-detect-btn");
    const assignTaskBtn = document.getElementById("assign-task-btn");
    const statusMessage = document.getElementById("status-message");
    const objectsList = document.getElementById("objects-list");

    startDetectBtn.addEventListener("click", function () {
        statusMessage.innerText = "Detecting objects...";
        
        fetch("/detect", {
            method: "POST"
        })
        .then(response => response.json())
        .then(data => {
            objectsList.innerHTML = "";  // Clear previous results
            
            if (data.objects && data.objects.length > 0) {
                detectedObjects = data.objects;
                data.objects.forEach(obj => {
                    let listItem = document.createElement("li");
                    listItem.textContent = obj;
                    objectsList.appendChild(listItem);
                });
                statusMessage.innerText = "";
                assignTaskBtn.style.display = "block";  // Show assign button
            } else {
                statusMessage.innerText = data.message;
            }
        });
    });

    assignTaskBtn.addEventListener("click", function () {
        if (detectedObjects.length > 0) {
            let task = detectedObjects[0];  // Assign the first detected task for simplicity
            statusMessage.innerText = `Assigning task: ${task}...`;

            fetch("/assign-task", {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ task: task })
            })
            .then(response => response.json())
            .then(data => {
                statusMessage.innerText = data.message;
                assignTaskBtn.style.display = "none";  // Hide button after assigning
            });
        }
    });
});