const alertSound = new Audio("{{ url_for('static', filename='alert.mp3') }}");
let soundCooldown = false;
let lightCheckInterval;
let recordsInterval;
let statusInterval;

function initAudio() {
    document.body.addEventListener('click', () => {
        alertSound.play().catch(e => console.log("Audio init failed:", e));
    }, { once: true });
}

async function checkLightLevel() {
    try {
        const response = await fetch('/get_light_level');
        if (!response.ok) throw new Error("Network error");
        
        const data = await response.json();
        const alertDiv = document.getElementById('light-alert');
        
        if (data.brightness < 50) {
            alertDiv.classList.remove('hidden');
            
            if (!soundCooldown) {
                await alertSound.play().catch(e => console.log("Playback failed:", e));
                soundCooldown = true;
                setTimeout(() => soundCooldown = false, 10000);
            }
            
            if (Notification.permission === "granted") {
                new Notification("Low Light Detected", {
                    body: "Please move to a brighter area",
                    icon: "/static/warning-icon.png"
                });
            }
        } else {
            alertDiv.classList.add('hidden');
        }
    } catch (error) {
        console.error("Light check error:", error);
    }
}

async function fetchRecords() {
    try {
        const response = await fetch('/get_records', { cache: "no-store" });
        const data = await response.json();
        const tableBody = document.querySelector("#attendance-table tbody");
        tableBody.innerHTML = "";
        
        if (data.length === 0) {
            tableBody.innerHTML = "<tr><td colspan='3'>No records found</td></tr>";
            return;
        }
        
        data.forEach(row => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${row["Student Name"]}</td>
                <td>${row["Attendance"]}</td>
                <td>${row["Time"]}</td>
            `;
            tableBody.appendChild(tr);
        });
    } catch (error) {
        console.error("Records fetch error:", error);
    }
}

async function updateStatus() {
    try {
        const response = await fetch('/get_status');
        const data = await response.json();
        document.getElementById("attendance-status").textContent = data.message;
    } catch (error) {
        console.error("Status update error:", error);
    }
}

function markAttendance(name, subject) {
    fetch('/mark_attendance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, subject })
    })
    .then(response => response.json())
    .then(data => console.log(data.message))
    .catch(error => console.error("Mark error:", error));
}

function initSystem() {
    if (Notification.permission !== "granted") {
        Notification.requestPermission().catch(e => console.log("Notification error:", e));
    }
    
    initAudio();
    fetchRecords();
    updateStatus();
    
    recordsInterval = setInterval(fetchRecords, 5000);
    statusInterval = setInterval(updateStatus, 1000);
    lightCheckInterval = setInterval(checkLightLevel, 3000);
    
    Swal.fire({
        title: "System Ready",
        text: "All monitoring systems active",
        icon: "success",
        confirmButtonText: "OK",
        allowOutsideClick: false,
        allowEscapeKey: false,
        customClass: {
            popup: 'custom-swal-popup',
            title: 'custom-swal-title',
            confirmButton: 'custom-swal-button'
        }
    });
}

document.addEventListener('DOMContentLoaded', initSystem);

function cleanup() {
    clearInterval(recordsInterval);
    clearInterval(statusInterval);
    clearInterval(lightCheckInterval);
}

window.addEventListener('beforeunload', cleanup);