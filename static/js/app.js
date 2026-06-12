// static/js/app.js

document.addEventListener("DOMContentLoaded", () => {
    // 1. Hide Loader
    const loader = document.getElementById("loader");
    if (loader) {
        setTimeout(() => {
            loader.classList.add("fade-out");
        }, 800);
    }


    // 2. Sticky Header on Scroll
    window.addEventListener("scroll", () => {
        const header = document.querySelector(".luxury-header");
        if (header) {
            if (window.scrollY > 50) {
                header.classList.add("scrolled");
            } else {
                header.classList.remove("scrolled");
            }
        }
    });



    // 3. Mobile Menu Toggle
    const mobileBtn = document.querySelector(".mobile-menu-btn");
    const navDrawer = document.querySelector(".mobile-nav-drawer");
    if (mobileBtn && navDrawer) {
        mobileBtn.addEventListener("click", () => {
            mobileBtn.classList.toggle("open");
            navDrawer.classList.toggle("open");
        });

        // Close drawer on link click
        navDrawer.querySelectorAll("a").forEach(link => {
            link.addEventListener("click", () => {
                mobileBtn.classList.remove("open");
                navDrawer.classList.remove("open");
            });
        });
    }

    // 4. Scroll Reveal Observer
    const revealElements = document.querySelectorAll(".scroll-reveal");
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("visible");
            }
        });
    }, { threshold: 0.1 });

    revealElements.forEach(el => revealObserver.observe(el));

    // 5. Fetch and Render Dynamic Data
    fetchFounder();
    fetchPlants();
    fetchProjects();

    // 6. Contact Form Submission
    const contactForm = document.getElementById("contact-form");
    const contactFeedback = document.getElementById("contact-message-feedback");
    
    if (contactForm) {
        contactForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const submitBtn = contactForm.querySelector('button[type="submit"]');
            const spinner = submitBtn.querySelector('.btn-spinner');
            const btnText = submitBtn.querySelector('.btn-text');

            // Show loading state
            spinner.classList.remove('hidden');
            btnText.classList.add('hidden');
            submitBtn.disabled = true;

            const name = document.getElementById("contact-name").value;
            const email = document.getElementById("contact-email").value;
            const message = document.getElementById("contact-message").value;

            try {
                const res = await fetch("/api/contact", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ name, email, message })
                });
                const result = await res.json();
                
                if (res.ok && result.success) {
                    showFormFeedback(contactFeedback, "success", "Message received. Our executive team will reach out shortly.");
                    contactForm.reset();
                } else {
                    showFormFeedback(contactFeedback, "error", result.error || "An error occurred. Please try again.");
                }
            } catch (err) {
                showFormFeedback(contactFeedback, "error", "Network failure. Please connect directly via corporate phone.");
            } finally {
                spinner.classList.add('hidden');
                btnText.classList.remove('hidden');
                submitBtn.disabled = false;
            }
        });
    }

    // 7. Newsletter Subscription Form
    const newsletterForm = document.getElementById("newsletter-form");
    const newsletterFeedback = document.getElementById("newsletter-feedback");

    if (newsletterForm) {
        newsletterForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const email = document.getElementById("newsletter-email").value;

            try {
                const res = await fetch("/api/subscribe", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email })
                });
                const result = await res.json();

                if (res.ok && result.success) {
                    showFormFeedback(newsletterFeedback, "success", "Subscribed successfully.");
                    newsletterForm.reset();
                } else {
                    showFormFeedback(newsletterFeedback, "error", result.error || "Subscription failed.");
                }
            } catch (err) {
                showFormFeedback(newsletterFeedback, "error", "Network error.");
            }
        });
    }
});

// Helper for UI feedback
function showFormFeedback(element, type, message) {
    if (!element) return;
    element.className = `form-feedback ${type}`;
    element.innerText = message;
    element.classList.remove("hidden");
    setTimeout(() => {
        element.classList.add("hidden");
    }, 6000);
}

// Fetch Founder details
async function fetchFounder() {
    const container = document.getElementById("founder-container");
    if (!container) return;

    try {
        const res = await fetch("/api/founder");
        const founder = await res.json();
        
        container.innerHTML = `
            <div class="founder-img-wrapper">
                <img class="founder-img" src="${founder.photo_url}" alt="${founder.name}">
            </div>
            <div class="founder-content">
                <h3>${founder.name}</h3>
                <span class="founder-title">${founder.role}</span>
                <p class="founder-bio">${founder.bio}</p>
                <div class="founder-vision-box">
                    <p>"${founder.vision}"</p>
                </div>
            </div>
        `;
    } catch (err) {
        console.error("Error fetching founder details", err);
    }
}

// Fetch Plant Details
async function fetchPlants() {
    const container = document.getElementById("plants-container");
    if (!container) return;

    try {
        const res = await fetch("/api/plants");
        const plants = await res.json();
        
        container.innerHTML = "";
        
        plants.forEach(plant => {
            let metricsHTML = "";
            const metrics = plant.live_metrics || {};
            const statusClass = plant.status.toLowerCase();
            
            // Build metrics list based on metrics keys
            for (const [key, value] of Object.entries(metrics)) {
                // Formatting keys for presentation
                const label = key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                
                if (typeof value === 'object') {
                    // For nested JSONs like Silo Levels
                    let subItems = "";
                    for (const [sKey, sVal] of Object.entries(value)) {
                        subItems += `${sKey.toUpperCase()}: ${sVal} | `;
                    }
                    metricsHTML += `
                        <div class="metric-item">
                            <span class="metric-label">${label}</span>
                            <span class="metric-value" style="font-size: 0.75rem;">${subItems.slice(0, -3)}</span>
                        </div>
                    `;
                } else {
                    metricsHTML += `
                        <div class="metric-item">
                            <span class="metric-label">${label}</span>
                            <span class="metric-value">${value}</span>
                        </div>
                    `;
                }
            }

            let addressHTML = "";
            if (plant.address && plant.map_url) {
                addressHTML = `
                    <div class="metrics-divider"></div>
                    <div style="margin-top: 15px; font-size: 0.8rem; line-height: 1.5; text-align: left;">
                        <span class="metrics-title" style="margin-bottom: 6px; display: block;">Facility Location</span>
                        <p style="color: var(--text-muted); margin-bottom: 12px;">${plant.address}</p>
                        <a href="${plant.map_url}" target="_blank" class="btn-outline" style="padding: 8px 16px; font-size: 0.7rem; border-radius: 4px; display: inline-flex; width: auto; letter-spacing: 1px;">Get Directions</a>
                    </div>
                `;
            }

            const card = document.createElement("div");
            card.className = "plant-card";
            card.id = `plant-card-${plant.id}`;
            card.innerHTML = `
                <div class="plant-header">
                    <span class="plant-badge">${plant.type} Unit</span>
                    <div class="status-indicator-wrap">
                        <span class="status-dot ${statusClass}"></span>
                        <span class="status-text ${statusClass}">${plant.status}</span>
                    </div>
                </div>
                <h3 class="plant-name">${plant.name}</h3>
                <p class="plant-capacity">Designed Capacity: ${plant.capacity}</p>
                <div class="metrics-divider"></div>
                <h4 class="metrics-title">Live Metrics</h4>
                <div class="metrics-list">
                    ${metricsHTML || '<div class="metric-item"><span class="metric-label">Operational Status</span><span class="metric-value">Standard Operations</span></div>'}
                </div>
                ${addressHTML}
                <div class="plant-footer">Updated: ${plant.last_updated}</div>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error("Error fetching plants", err);
    }
}

// Fetch Projects
async function fetchProjects() {
    const container = document.getElementById("projects-container");
    if (!container) return;

    try {
        const res = await fetch("/api/projects");
        const projects = await res.json();
        
        container.innerHTML = "";
        
        projects.forEach(project => {
            const card = document.createElement("div");
            card.className = "project-card";
            card.innerHTML = `
                <div class="project-img-wrap">
                    <img class="project-img" src="${project.image_url}" alt="${project.name}" loading="lazy">
                    <div class="project-overlay">
                        <span class="project-status">${project.status}</span>
                    </div>
                </div>
                <div class="project-info">
                    <h3 class="project-name">${project.name}</h3>
                    <p class="project-desc">${project.description}</p>
                    <div class="progress-wrap">
                        <div class="progress-header">
                            <span class="progress-label">Execution Progress</span>
                            <span class="progress-pct">${project.progress}%</span>
                        </div>
                        <div class="progress-bar-container">
                            <div class="progress-bar-fill" style="width: ${project.progress}%"></div>
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error("Error fetching projects", err);
    }
}
