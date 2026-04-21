let sessionId = localStorage.getItem("tutor_session");

// App State
let currentQuiz = null;
let currentQuestionIndex = 0;
let quizScore = 0;
let quizTopic = "";

document.addEventListener("DOMContentLoaded", () => {
    initSession();
    setupNavigation();
    setupUpload();
    setupChat();
    setupQuiz();
});

async function initSession() {
    if (!sessionId) {
        try {
            const res = await fetch("/api/session", { method: "POST" });
            const data = await res.json();
            sessionId = data.session_id;
            localStorage.setItem("tutor_session", sessionId);
        } catch (e) {
            console.error("Failed to init session");
        }
    }
    document.getElementById("session-display").innerText = `Session: Active (${sessionId.slice(0, 6)})`;
}

// Navigation
function setupNavigation() {
    document.querySelectorAll(".nav-item[data-target]").forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            // Update active link
            document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
            e.currentTarget.classList.add("active");
            
            // Switch view
            const targetId = e.currentTarget.getAttribute("data-target");
            document.querySelectorAll(".view-section").forEach(v => v.classList.remove("active"));
            document.getElementById(targetId).classList.add("active");

            if (targetId === "progress-view") loadProgress();
        });
    });
}

// UI Helpers
function showToast(msg) {
    const toast = document.getElementById("toast");
    toast.innerText = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 3000);
}

// Upload Notes
function setupUpload() {
    const uploadBtn = document.getElementById("upload-btn");
    const fileInput = document.getElementById("file-input");

    uploadBtn.addEventListener("click", (e) => {
        e.preventDefault();
        fileInput.click();
    });

    fileInput.addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        showToast("Uploading and processing notes...");
        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("/api/upload", {
                method: "POST",
                body: formData
            });
            const data = await res.json();
            if (res.ok) {
                showToast("Notes processed successfully! Ready to learn.");
                document.getElementById("chat-history").innerHTML += `
                    <div class="message tutor">I've read your document <b>${file.name}</b>. What would you like to learn about it?</div>
                `;
            } else {
                throw new Error(data.detail || "Upload failed");
            }
        } catch (error) {
            showToast("Error processing notes.");
            console.error(error);
        }
        fileInput.value = "";
    });
}

// Chat
function setupChat() {
    const btn = document.getElementById("send-btn");
    const input = document.getElementById("chat-input");

    async function sendMsg() {
        const text = input.value.trim();
        if (!text) return;

        // Add user message
        const history = document.getElementById("chat-history");
        history.innerHTML += `<div class="message user">${text}</div>`;
        input.value = "";
        history.scrollTop = history.scrollHeight;

        // Add loading state
        const loadingId = "load-" + Date.now();
        history.innerHTML += `<div class="message tutor" id="${loadingId}">...</div>`;
        history.scrollTop = history.scrollHeight;

        try {
            const res = await fetch("/api/chat/tutor", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: text, top_k: 5 })
            });
            const data = await res.json();
            
            // Render markdown answer
            document.getElementById(loadingId).innerHTML = marked.parse(data.answer || "I'm sorry, I couldn't understand that.");
        } catch (e) {
            document.getElementById(loadingId).innerText = "Error reaching tutor.";
        }
        history.scrollTop = history.scrollHeight;
    }

    btn.addEventListener("click", sendMsg);
    input.addEventListener("keypress", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMsg();
        }
    });
}

// Quiz
function setupQuiz() {
    const genBtn = document.getElementById("generate-quiz-btn");
    
    genBtn.addEventListener("click", async () => {
        const topic = document.getElementById("quiz-topic").value.trim();
        if (!topic) {
            showToast("Please enter a topic first.");
            return;
        }

        document.getElementById("quiz-generator-container").style.display = "none";
        document.getElementById("quiz-loading").style.display = "block";
        quizTopic = topic;

        try {
            const res = await fetch("/api/quiz", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ topic: topic, top_k: 5 })
            });
            const data = await res.json();

            if (data.status === "success" && data.quiz && data.quiz.length > 0) {
                currentQuiz = data.quiz;
                currentQuestionIndex = 0;
                quizScore = 0;
                document.getElementById("quiz-loading").style.display = "none";
                document.getElementById("quiz-player").style.display = "block";
                renderQuestion();
            } else {
                throw new Error("Could not generate quiz.");
            }
        } catch (e) {
            showToast("Failed to generate quiz. Make sure notes are uploaded.");
            document.getElementById("quiz-loading").style.display = "none";
            document.getElementById("quiz-generator-container").style.display = "flex";
        }
    });

    document.getElementById("next-q-btn").addEventListener("click", () => {
        currentQuestionIndex++;
        if (currentQuestionIndex >= currentQuiz.length) {
            finishQuiz();
        } else {
            renderQuestion();
        }
    });

    document.getElementById("back-to-gen-btn").addEventListener("click", () => {
        document.getElementById("quiz-result").style.display = "none";
        document.getElementById("quiz-generator-container").style.display = "flex";
        document.getElementById("quiz-topic").value = "";
    });
}

function renderQuestion() {
    const q = currentQuiz[currentQuestionIndex];
    document.getElementById("quiz-progress").innerText = `Question ${currentQuestionIndex + 1} of ${currentQuiz.length}`;
    document.getElementById("quiz-question").innerText = q.question;
    
    const optionsContainer = document.getElementById("quiz-options");
    optionsContainer.innerHTML = "";
    
    q.options.forEach(opt => {
        const btn = document.createElement("button");
        btn.className = "option-btn";
        btn.innerText = opt;
        btn.onclick = () => selectOption(btn, opt, q.correct_answer, q.explanation);
        optionsContainer.appendChild(btn);
    });

    document.getElementById("quiz-explanation").style.display = "none";
    document.getElementById("next-q-btn").style.display = "none";
}

function selectOption(btn, selected, correct, explanation) {
    // Disable all options
    document.querySelectorAll(".option-btn").forEach(b => b.disabled = true);
    
    if (selected === correct) {
        btn.classList.add("correct");
        quizScore++;
    } else {
        btn.classList.add("incorrect");
        // Highlight correct
        document.querySelectorAll(".option-btn").forEach(b => {
            if (b.innerText === correct) b.classList.add("correct");
        });
    }

    const expDiv = document.getElementById("quiz-explanation");
    expDiv.innerHTML = `<strong>Explanation:</strong> ${explanation}`;
    expDiv.style.display = "block";
    
    document.getElementById("next-q-btn").style.display = "inline-block";
}

async function finishQuiz() {
    document.getElementById("quiz-player").style.display = "none";
    document.getElementById("quiz-result").style.display = "block";
    document.getElementById("final-score").innerText = `${quizScore}/${currentQuiz.length}`;
    
    let summary = "Good effort!";
    if (quizScore === currentQuiz.length) summary = "Perfect score! Outstanding work.";
    else if (quizScore === 0) summary = "Keep studying and try again!";
    document.getElementById("quiz-summary").innerText = summary;

    // Submit results
    try {
        await fetch("/api/quiz/submit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: sessionId,
                topic: quizTopic,
                score: quizScore,
                total: currentQuiz.length
            })
        });
    } catch (e) {
        console.error("Score submit failed");
    }
}

// Dashboard
let chartInstance = null;

async function loadProgress() {
    if (!sessionId) return;
    try {
        const res = await fetch(`/api/progress?session_id=${sessionId}`);
        const data = await res.json();
        
        const totalQuizzes = data.scores.length;
        document.getElementById("stat-quizzes").innerText = totalQuizzes;
        
        let avgScore = 0;
        if (totalQuizzes > 0) {
            const sum = data.scores.reduce((acc, s) => acc + (s.score / s.total), 0);
            avgScore = Math.round((sum / totalQuizzes) * 100);
        }
        document.getElementById("stat-avg").innerText = `${avgScore}%`;

        // Render Weaknesses
        const wList = document.getElementById("weakness-list");
        if (data.weaknesses.length > 0) {
            // Sort by severity descending
            const sortedW = data.weaknesses.sort((a,b) => b.severity - a.severity).slice(0,5);
            wList.innerHTML = sortedW.map(w => {
                if (w.severity < 0.2) return ""; // Only show if severity is high enough (e.g., >20% wrong)
                return `<li><span>${w.topic}</span> <span style="color:var(--danger)">Needs Work</span></li>`;
            }).join("");
            
            if (wList.innerHTML.trim() === "") {
                wList.innerHTML = `<li>You're doing great! No major weaknesses identified.</li>`;
            }
        } else {
            wList.innerHTML = `<li>No data yet. Take some quizzes!</li>`;
        }

        // Render Chart
        renderChart(data.scores);

    } catch(e) {
        console.error("Progress load failed", e);
    }
}

function renderChart(scores) {
    const ctx = document.getElementById('scoreChart').getContext('2d');
    
    if (chartInstance) chartInstance.destroy();

    if (scores.length === 0) return;

    const labels = scores.map((s, i) => `Quiz ${i+1}`);
    const dataPoints = scores.map(s => Math.round((s.score/s.total)*100));

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Score Percentage',
                data: dataPoints,
                borderColor: '#FFB800',
                backgroundColor: 'rgba(255, 184, 0, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, max: 100 }
            }
        }
    });
}
