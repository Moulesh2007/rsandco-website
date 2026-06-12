// static/js/admin.js

let databaseMode = "mock"; // Default is mock unless Supabase active
let supabaseClient = null;
let plantsList = [];
let projectsList = [];

document.addEventListener("DOMContentLoaded", () => {
    initMode();
    setupEventListeners();
});

// Initialize database mode and authentication checks
async function initMode() {
    const modeBadge = document.getElementById("database-mode");
    
    // Check if client-side custom Supabase keys are configured in local storage
    const customUrl = localStorage.getItem("RSCO_SUPABASE_URL");
    const customKey = localStorage.getItem("RSCO_SUPABASE_KEY");

    if (customUrl && customKey && window.supabase) {
        try {
            supabaseClient = window.supabase.createClient(customUrl, customKey);
            databaseMode = "supabase";
            modeBadge.innerText = "Supabase Connected";
            modeBadge.className = "mode-badge supabase";
            checkSession();
        } catch (e) {
            console.error("Custom Supabase init failed:", e);
            useMockMode();
        }
    } else {
        useMockMode();
    }
}

function useMockMode() {
    databaseMode = "mock";
    const modeBadge = document.getElementById("database-mode");
    modeBadge.innerText = "Local Mock Mode";
    modeBadge.className = "mode-badge";
    
    // Check if mock bypass is active
    const mockAuth = sessionStorage.getItem("RSCO_MOCK_AUTH");
    if (mockAuth === "true") {
        showDashboard();
    } else {
        showLogin();
    }
}

// Check Supabase session
async function checkSession() {
    if (!supabaseClient) return;
    const { data, error } = await supabaseClient.auth.getSession();
    if (data && data.session) {
        showDashboard();
    } else {
        showLogin();
    }
}

function showLogin() {
    document.getElementById("login-container").classList.remove("hidden");
    document.getElementById("dashboard-container").classList.add("hidden");
    document.getElementById("logout-btn").classList.add("hidden");
}

function showDashboard() {
    document.getElementById("login-container").classList.add("hidden");
    document.getElementById("dashboard-container").classList.remove("hidden");
    document.getElementById("logout-btn").classList.remove("hidden");
    
    loadDashboardData();
}

// Set up UI event listeners
function setupEventListeners() {
    // Bypass authentication to preview Mock Mode
    const bypassBtn = document.getElementById("bypass-btn");
    if (bypassBtn) {
        bypassBtn.addEventListener("click", () => {
            sessionStorage.setItem("RSCO_MOCK_AUTH", "true");
            databaseMode = "mock";
            showDashboard();
            showToast("Bypassed authentication. Updates are saved in memory.", "success");
        });
    }

    // Login Form Submit (Supabase auth or Mock auth)
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const email = document.getElementById("login-email").value;
            const password = document.getElementById("login-password").value;
            
            const submitBtn = document.getElementById("login-submit");
            const spinner = submitBtn.querySelector(".btn-spinner");
            const btnText = submitBtn.querySelector(".btn-text");
            const feedback = document.getElementById("login-feedback");

            spinner.classList.remove("hidden");
            btnText.classList.add("hidden");
            submitBtn.disabled = true;

            if (databaseMode === "supabase" && supabaseClient) {
                const { error } = await supabaseClient.auth.signInWithPassword({ email, password });
                if (error) {
                    feedback.innerText = error.message;
                    feedback.className = "form-feedback error";
                    feedback.classList.remove("hidden");
                    
                    spinner.classList.add("hidden");
                    btnText.classList.remove("hidden");
                    submitBtn.disabled = false;
                } else {
                    feedback.classList.add("hidden");
                    showDashboard();
                    showToast("Authentication successful.", "success");
                }
            } else {
                // In Mock Mode, allow any email with password 'admin' or 'password'
                setTimeout(() => {
                    if (password === "admin" || password === "password") {
                        sessionStorage.setItem("RSCO_MOCK_AUTH", "true");
                        feedback.classList.add("hidden");
                        showDashboard();
                        showToast("Authenticated via Local Mock Mode.", "success");
                    } else {
                        feedback.innerText = "Invalid credentials for Mock Mode. Try password: 'admin'";
                        feedback.className = "form-feedback error";
                        feedback.classList.remove("hidden");
                        spinner.classList.add("hidden");
                        btnText.classList.remove("hidden");
                        submitBtn.disabled = false;
                    }
                }, 800);
            }
        });
    }

    // Logout
    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", async () => {
            if (databaseMode === "supabase" && supabaseClient) {
                await supabaseClient.auth.signOut();
            }
            sessionStorage.removeItem("RSCO_MOCK_AUTH");
            showToast("Logged out successfully.", "success");
            showLogin();
        });
    }
}

// Load Dashboard Controls Data
async function loadDashboardData() {
    await Promise.all([loadPlantsControls(), loadProjectsControls()]);
}

async function loadPlantsControls() {
    const listContainer = document.getElementById("admin-plants-list");
    if (!listContainer) return;
    
    listContainer.innerHTML = '<div class="loading-spinner"></div>';
    
    try {
        const res = await fetch("/api/plants");
        plantsList = await res.json();
        
        listContainer.innerHTML = "";
        
        plantsList.forEach(plant => {
            const card = document.createElement("div");
            card.className = "control-item-card";
            card.innerHTML = `
                <div class="control-header">
                    <span class="control-title">${plant.name}</span>
                    <span class="control-type">${plant.type}</span>
                </div>
                <form class="control-form" data-id="${plant.id}" onsubmit="savePlantUpdate(event, '${plant.id}')">
                    <div class="select-wrapper">
                        <select class="control-select" name="status">
                            <option value="Active" ${plant.status === 'Active' ? 'selected' : ''}>Active</option>
                            <option value="Maintenance" ${plant.status === 'Maintenance' ? 'selected' : ''}>Maintenance</option>
                            <option value="Offline" ${plant.status === 'Offline' ? 'selected' : ''}>Offline</option>
                        </select>
                    </div>
                    <div>
                        <label class="control-json-label">Live Metrics (JSON format):</label>
                        <textarea class="control-json-textarea" name="metrics" rows="4">${JSON.stringify(plant.live_metrics, null, 2)}</textarea>
                    </div>
                    <button type="submit" class="btn-gold btn-block" style="padding: 10px 20px; font-size: 0.75rem;">Apply Parameters</button>
                </form>
            `;
            listContainer.appendChild(card);
        });
    } catch (err) {
        listContainer.innerHTML = `<p style="color: var(--gold-dark); text-align: center;">Error loading facilities.</p>`;
    }
}

async function loadProjectsControls() {
    const listContainer = document.getElementById("admin-projects-list");
    if (!listContainer) return;

    listContainer.innerHTML = '<div class="loading-spinner"></div>';

    try {
        const res = await fetch("/api/projects");
        projectsList = await res.json();

        listContainer.innerHTML = "";

        projectsList.forEach(project => {
            const card = document.createElement("div");
            card.className = "control-item-card";
            card.innerHTML = `
                <div class="control-header">
                    <span class="control-title">${project.name}</span>
                    <span class="control-type">${project.status}</span>
                </div>
                <div class="control-form">
                    <label class="control-json-label">Execution Progress:</label>
                    <div class="slider-group">
                        <input type="range" class="control-slider" min="0" max="100" value="${project.progress}" 
                            oninput="updateSliderVal(this, '${project.id}')" 
                            onchange="saveProjectProgress('${project.id}', this.value)">
                        <span class="slider-val" id="slider-val-${project.id}">${project.progress}%</span>
                    </div>
                </div>
            `;
            listContainer.appendChild(card);
        });
    } catch (err) {
        listContainer.innerHTML = `<p style="color: var(--gold-dark); text-align: center;">Error loading project portfolio.</p>`;
    }
}

// Live feedback during slider drag
window.updateSliderVal = function(slider, projectId) {
    const display = document.getElementById(`slider-val-${projectId}`);
    if (display) {
        display.innerText = `${slider.value}%`;
    }
};

// Save operations to server
window.savePlantUpdate = async function(event, plantId) {
    event.preventDefault();
    const form = event.target;
    const status = form.status.value;
    const metricsStr = form.metrics.value;
    
    let metrics = {};
    try {
        metrics = JSON.parse(metricsStr);
    } catch (err) {
        showToast("Invalid JSON formatting in metrics configuration.", "error");
        return;
    }

    try {
        const res = await fetch("/api/admin/update-plant", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id: plantId, status, live_metrics: metrics })
        });
        
        if (res.ok) {
            showToast("Plant configuration saved.", "success");
        } else {
            const data = await res.json();
            showToast(data.error || "Update failure.", "error");
        }
    } catch (err) {
        showToast("Failed to update facility parameters.", "error");
    }
};

window.saveProjectProgress = async function(projectId, progress) {
    try {
        const res = await fetch("/api/admin/update-project", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id: projectId, progress: parseInt(progress) })
        });
        
        if (res.ok) {
            showToast("Project progress updated.", "success");
        } else {
            const data = await res.json();
            showToast(data.error || "Update failure.", "error");
        }
    } catch (err) {
        showToast("Failed to update project progress.", "error");
    }
};

// Toast Notifications Manager
function showToast(message, type = "success") {
    const toast = document.getElementById("toast");
    if (!toast) return;

    toast.innerText = message;
    toast.className = `toast-notification show ${type}`;

    setTimeout(() => {
        toast.classList.remove("show");
    }, 4000);
}
