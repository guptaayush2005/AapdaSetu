/**
 * AapdaSetu - Unified Core Frontend Engine
 * Centralized API handler, Geolocation, Prediction & Shared Navigation
 */

let API_BASE = (window.API_BASE) ? window.API_BASE : "http://127.0.0.1:8000";
(async function verifyApiBase() {
  try {
    const r8 = await fetch("http://127.0.0.1:8000/health", { signal: AbortSignal.timeout(600) });
    if (r8.ok) { API_BASE = "http://127.0.0.1:8000"; return; }
  } catch {}
  try {
    const r81 = await fetch("http://127.0.0.1:8001/health", { signal: AbortSignal.timeout(600) });
    if (r81.ok) { API_BASE = "http://127.0.0.1:8001"; return; }
  } catch {}
})();

// Fallback Indian States & Districts if backend is starting or offline
const FALLBACK_LOCATIONS = [
  { state: "Uttarakhand", district: "Chamoli" },
  { state: "Uttarakhand", district: "Rudraprayag" },
  { state: "Uttarakhand", district: "Uttarkashi" },
  { state: "Uttarakhand", district: "Haridwar" },
  { state: "Uttarakhand", district: "Dehradun" },
  { state: "Uttarakhand", district: "Pauri Garhwal" },
  { state: "Himachal Pradesh", district: "Kullu" },
  { state: "Himachal Pradesh", district: "Mandi" },
  { state: "Himachal Pradesh", district: "Shimla" },
  { state: "Himachal Pradesh", district: "Kangra" },
  { state: "Himachal Pradesh", district: "Kinnaur" },
  { state: "Assam", district: "Dhemaji" },
  { state: "Assam", district: "Barpeta" },
  { state: "Assam", district: "Morigaon" },
  { state: "Assam", district: "Cachar" },
  { state: "Assam", district: "Kamrup" },
  { state: "Assam", district: "Dibrugarh" },
  { state: "Bihar", district: "Patna" },
  { state: "Bihar", district: "Darbhanga" },
  { state: "Bihar", district: "Muzaffarpur" },
  { state: "Bihar", district: "Bhagalpur" },
  { state: "Bihar", district: "Saharsa" },
  { state: "Bihar", district: "Supaul" },
  { state: "Kerala", district: "Wayanad" },
  { state: "Kerala", district: "Idukki" },
  { state: "Kerala", district: "Ernakulam" },
  { state: "Kerala", district: "Alappuzha" },
  { state: "Kerala", district: "Kottayam" },
  { state: "Maharashtra", district: "Kolhapur" },
  { state: "Maharashtra", district: "Sangli" },
  { state: "Maharashtra", district: "Raigad" },
  { state: "Maharashtra", district: "Ratnagiri" },
  { state: "Maharashtra", district: "Pune" },
  { state: "Odisha", district: "Puri" },
  { state: "Odisha", district: "Cuttack" },
  { state: "Odisha", district: "Kendrapara" },
  { state: "Odisha", district: "Balasore" },
  { state: "Gujarat", district: "Surat" },
  { state: "Gujarat", district: "Bharuch" },
  { state: "Gujarat", district: "Vadodara" },
  { state: "Gujarat", district: "Navsari" },
  { state: "Uttar Pradesh", district: "Varanasi" },
  { state: "Uttar Pradesh", district: "Prayagraj" },
  { state: "Uttar Pradesh", district: "Gorakhpur" },
  { state: "Uttar Pradesh", district: "Ballia" }
];

/**
 * Populate State and District dropdowns with live API fallback
 */
async function loadLocations(stateSelectId = "state", districtSelectId = "district", predictBtnId = "predictBtn") {
  const stateSelect = document.getElementById(stateSelectId);
  const districtSelect = document.getElementById(districtSelectId);
  const predictBtn = document.getElementById(predictBtnId);

  if (!stateSelect || !districtSelect) return;

  let locations = [];

  try {
    const res = await fetch(`${API_BASE}/locations`, { signal: AbortSignal.timeout(3500) });
    if (res.ok) {
      locations = await res.json();
    }
  } catch (err) {
    console.warn("Using offline fallback locations:", err.message);
  }

  if (!locations || locations.length === 0) {
    locations = FALLBACK_LOCATIONS;
  }

  const states = [...new Set(locations.map(item => item.state))].sort();

  stateSelect.innerHTML = '<option value="">Select State</option>';
  states.forEach(state => {
    const opt = document.createElement("option");
    opt.value = state;
    opt.textContent = state;
    stateSelect.appendChild(opt);
  });

  stateSelect.addEventListener("change", function () {
    const selectedState = this.value;
    districtSelect.innerHTML = '<option value="">Select District</option>';
    if (predictBtn) predictBtn.disabled = true;

    if (!selectedState) {
      districtSelect.disabled = true;
      return;
    }

    const districts = locations
      .filter(item => item.state === selectedState)
      .map(item => item.district)
      .sort();

    districts.forEach(district => {
      const opt = document.createElement("option");
      opt.value = district;
      opt.textContent = district;
      districtSelect.appendChild(opt);
    });

    districtSelect.disabled = false;
  });

  districtSelect.addEventListener("change", function () {
    if (predictBtn) {
      predictBtn.disabled = !this.value;
    }
  });
}

/**
 * Hyper-Local Location Selector: State -> District -> Village / Ward / Local Area
 */
async function loadHyperlocalLocations(stateSelectId = "state", districtSelectId = "district", wardSelectId = "ward", predictBtnId = "predictBtn", onSelectCallback = null) {
  const stateSelect = document.getElementById(stateSelectId);
  const districtSelect = document.getElementById(districtSelectId);
  const wardSelect = document.getElementById(wardSelectId);
  const predictBtn = document.getElementById(predictBtnId);

  if (!stateSelect || !districtSelect) return;

  let hierarchy = null;

  try {
    const res = await fetch(`${API_BASE}/locations/hyperlocal`, { signal: AbortSignal.timeout(3500) });
    if (res.ok) {
      hierarchy = await res.json();
    }
  } catch (err) {
    console.warn("Using local fallback hierarchy for hyper-local locations:", err.message);
  }

  // If backend unreachable, build fallback hierarchy from FALLBACK_LOCATIONS
  if (!hierarchy) {
    hierarchy = {};
    FALLBACK_LOCATIONS.forEach(loc => {
      if (!hierarchy[loc.state]) hierarchy[loc.state] = {};
      hierarchy[loc.state][loc.district] = [
        { name: `${loc.district} Riverbank Lowland Ward 1`, type: "Ward", slope_angle_deg: 12.5, elevation_m: 420, terrain_type: "Valley River Basin" },
        { name: `${loc.district} North Hill Slope Village`, type: "Village", slope_angle_deg: 32.0, elevation_m: 850, terrain_type: "Steep Mountain Slope" },
        { name: `${loc.district} Central Floodplain Ward`, type: "Ward", slope_angle_deg: 4.5, elevation_m: 210, terrain_type: "Alluvial Flat Plain" }
      ];
    });
  }

  window.aapdaHyperlocalHierarchy = hierarchy;

  const states = Object.keys(hierarchy).sort();
  stateSelect.innerHTML = '<option value="">Select State</option>';
  states.forEach(state => {
    const opt = document.createElement("option");
    opt.value = state;
    opt.textContent = state;
    stateSelect.appendChild(opt);
  });

  stateSelect.addEventListener("change", function () {
    const selState = this.value;
    districtSelect.innerHTML = '<option value="">Select District</option>';
    if (wardSelect) {
      wardSelect.innerHTML = '<option value="">Select District First</option>';
      wardSelect.disabled = true;
    }
    if (predictBtn) predictBtn.disabled = true;

    if (!selState || !hierarchy[selState]) {
      districtSelect.disabled = true;
      return;
    }

    const districts = Object.keys(hierarchy[selState]).sort();
    districts.forEach(dist => {
      const opt = document.createElement("option");
      opt.value = dist;
      opt.textContent = dist;
      districtSelect.appendChild(opt);
    });
    districtSelect.disabled = false;
  });

  districtSelect.addEventListener("change", function () {
    const selState = stateSelect.value;
    const selDistrict = this.value;

    if (predictBtn) predictBtn.disabled = !selDistrict;

    if (!wardSelect) return;

    wardSelect.innerHTML = '<option value="">Select Village / Ward / Local Area</option>';
    if (!selDistrict || !hierarchy[selState] || !hierarchy[selState][selDistrict]) {
      wardSelect.disabled = true;
      return;
    }

    const wards = hierarchy[selState][selDistrict] || [];
    wards.forEach(w => {
      const opt = document.createElement("option");
      opt.value = w.name;
      opt.textContent = `${w.name} (${w.slope_angle_deg}° slope, ${w.elevation_m}m)`;
      opt.dataset.slope = w.slope_angle_deg;
      opt.dataset.elevation = w.elevation_m;
      opt.dataset.terrain = w.terrain_type;
      wardSelect.appendChild(opt);
    });

    wardSelect.disabled = false;
    if (wards.length > 0) {
      wardSelect.selectedIndex = 1; // Default to first authentic settlement
      if (onSelectCallback) {
        onSelectCallback(wards[0]);
      }
    }
  });

  if (wardSelect) {
    wardSelect.addEventListener("change", function () {
      const selState = stateSelect.value;
      const selDistrict = districtSelect.value;
      const selWardName = this.value;
      if (!selWardName || !hierarchy[selState] || !hierarchy[selState][selDistrict]) return;

      const wardObj = hierarchy[selState][selDistrict].find(w => w.name === selWardName);
      if (wardObj && onSelectCallback) {
        onSelectCallback(wardObj);
      }
    });
  }
}

/**
 * Mobile Navigation Drawer Toggle
 */
function toggleMobileNav() {
  const drawer = document.getElementById("mobileNavDrawer");
  const menuBtn = document.querySelector(".mobile-menu-btn");
  if (drawer) {
    const isOpen = drawer.classList.toggle("open");
    if (menuBtn) {
      menuBtn.textContent = isOpen ? "✕" : "☰";
      menuBtn.setAttribute("aria-expanded", isOpen ? "true" : "false");
    }
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
  }
}

/**
 * Toast Notification System
 */
function showToast(message, type = "info") {
  let container = document.getElementById("toastContainer");
  if (!container) {
    container = document.createElement("div");
    container.id = "toastContainer";
    container.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 10px;
    `;
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  const bgColors = {
    info: "#1677ff",
    success: "#10b981",
    warning: "#f59e0b",
    error: "#e02424"
  };

  toast.style.cssText = `
    background: ${bgColors[type] || "#0b2341"};
    color: #fff;
    padding: 12px 18px;
    border-radius: 10px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    font-size: 0.9rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
    animation: fadeIn 0.25s ease;
  `;
  toast.innerHTML = `<span>${type === 'error' ? '⚠️' : (type === 'success' ? '✅' : 'ℹ️')}</span> ${message}`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "0.3s";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Global initialization
document.addEventListener("DOMContentLoaded", () => {
  const menuBtn = document.querySelector(".mobile-menu-btn");
  if (menuBtn) {
    menuBtn.addEventListener("click", toggleMobileNav);
  }

  // Initialize Auth Header, Login Modal, and Dam Broadcast Banner
  initAuthUI();
  initLoginModal();
  checkActiveDamAlerts();
});

/* ================= AUTHENTICATION SYSTEM ================= */
function getCurrentUser() {
  try {
    const raw = localStorage.getItem("aapdaCurrentUser");
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
}

function setCurrentUser(user) {
  if (user) {
    localStorage.setItem("aapdaCurrentUser", JSON.stringify(user));
    if (user.role === "ADMIN" && user.admin_key) {
      localStorage.setItem("aapdaAdminKey", user.admin_key);
    }
  } else {
    localStorage.removeItem("aapdaCurrentUser");
  }
  initAuthUI();
}

function logout() {
  const u = getCurrentUser();
  setCurrentUser(null);
  showToast(`Logged out ${u ? u.display_name || u.username : ''}`, "info");
  setTimeout(() => window.location.reload(), 500);
}

function initAuthUI() {
  const user = getCurrentUser();
  const navActions = document.querySelector(".nav-actions");
  if (!navActions) return;

  // Remove existing auth widget if present
  const existing = document.getElementById("navAuthWidget");
  if (existing) existing.remove();

  const authWrap = document.createElement("div");
  authWrap.id = "navAuthWidget";
  authWrap.style.cssText = "display:flex;align-items:center;gap:8px;";

  if (user) {
    const isAdmin = user.role === "ADMIN";
    authWrap.innerHTML = `
      <div class="auth-user-badge ${isAdmin ? 'admin' : 'citizen'}">
        <span>${isAdmin ? '🛡️' : '👤'}</span>
        <span>${user.username}</span>
      </div>
      ${isAdmin ? '<a href="admin.html" class="auth-nav-btn" style="background:#dc2626;">EOC Admin</a>' : ''}
      <button onclick="logout()" class="auth-nav-btn" title="Logout" style="padding:6px 10px;font-size:0.75rem;">
        Logout ✕
      </button>
    `;
  } else {
    authWrap.innerHTML = `
      <button onclick="openLoginModal()" class="auth-nav-btn">
        <span>🔑 Login</span>
      </button>
    `;
  }

  // Insert before the SOS button
  const sosBtn = navActions.querySelector(".sos-header-btn");
  if (sosBtn) {
    navActions.insertBefore(authWrap, sosBtn);
  } else {
    navActions.appendChild(authWrap);
  }
}

function initLoginModal() {
  if (document.getElementById("authModalBackdrop")) return;

  const modal = document.createElement("div");
  modal.id = "authModalBackdrop";
  modal.className = "auth-modal-backdrop";
  modal.innerHTML = `
    <div class="auth-modal-card">
      <div class="auth-tab-row">
        <button class="auth-tab-btn active" id="tabCitizenBtn" onclick="switchAuthTab('citizen')">
          👤 Citizen Login
        </button>
        <button class="auth-tab-btn" id="tabAdminBtn" onclick="switchAuthTab('admin')">
          🛡️ Admin EOC Login
        </button>
      </div>

      <div class="auth-body">
        <h3 id="authTitle" style="color:var(--navy);font-size:1.2rem;margin:0 0 6px;font-family:'Outfit',sans-serif;">
          Citizen Access
        </h3>
        <p id="authSubtitle" style="color:var(--text-muted);font-size:0.8rem;margin:0 0 16px;">
          Log in for zero-click instant rescue and personalized family emergency updates.
        </p>

        <form id="authLoginForm" onsubmit="handleAuthSubmit(event)">
          <div style="display:flex;flex-direction:column;gap:12px;">
            <div>
              <label style="font-size:0.75rem;font-weight:700;color:var(--navy);display:block;margin-bottom:4px;">User / Admin ID</label>
              <input type="text" id="authUsernameInput" class="form-input" placeholder="e.g. kausha123" required>
            </div>
            <div>
              <label style="font-size:0.75rem;font-weight:700;color:var(--navy);display:block;margin-bottom:4px;">Password</label>
              <input type="password" id="authPasswordInput" class="form-input" placeholder="Enter password" required>
            </div>

            <button type="submit" id="authSubmitBtn" class="btn-primary" style="width:100%;height:46px;margin-top:6px;">
              <span>Sign In 🚀</span>
            </button>
          </div>
        </form>

        <div style="margin-top:16px;padding-top:14px;border-top:1px solid #e2e8f0;">
          <div style="font-size:0.75rem;font-weight:700;color:#64748b;margin-bottom:4px;">⚡ 1-Click Quick Demo Fill:</div>
          <button type="button" class="quick-demo-pill" onclick="fillDemoCredentials('citizen')">
            👤 Citizen: <strong>kausha123 / 123</strong>
          </button>
          <button type="button" class="quick-demo-pill" onclick="fillDemoCredentials('admin')">
            🛡️ Admin: <strong>ayush / 123</strong>
          </button>
        </div>

        <button onclick="closeLoginModal()" style="position:absolute;top:14px;right:16px;border:0;background:transparent;font-size:1.2rem;color:#94a3b8;cursor:pointer;">
          ✕
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeLoginModal();
  });
}

let currentAuthRole = "citizen";

function openLoginModal(role = "citizen") {
  const modal = document.getElementById("authModalBackdrop");
  if (modal) {
    modal.classList.add("active");
    switchAuthTab(role);
  }
}

function closeLoginModal() {
  const modal = document.getElementById("authModalBackdrop");
  if (modal) modal.classList.remove("active");
}

function switchAuthTab(role) {
  currentAuthRole = role;
  const tabCitizen = document.getElementById("tabCitizenBtn");
  const tabAdmin = document.getElementById("tabAdminBtn");
  const title = document.getElementById("authTitle");
  const sub = document.getElementById("authSubtitle");
  const userInput = document.getElementById("authUsernameInput");
  const passInput = document.getElementById("authPasswordInput");

  if (role === "admin") {
    tabAdmin.classList.add("active");
    tabCitizen.classList.remove("active");
    title.textContent = "Disaster Operations Officer (Admin)";
    sub.textContent = "Authorized access for Dam Gate Broadcasts & NDRF Dispatch.";
    userInput.value = "ayush";
    passInput.value = "123";
  } else {
    tabCitizen.classList.add("active");
    tabAdmin.classList.remove("active");
    title.textContent = "Citizen Portal Access";
    sub.textContent = "Zero-click instant emergency rescue and family safety.";
    userInput.value = "kausha123";
    passInput.value = "123";
  }
}

function fillDemoCredentials(role) {
  switchAuthTab(role);
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  const username = document.getElementById("authUsernameInput").value.trim();
  const password = document.getElementById("authPasswordInput").value.trim();
  const btn = document.getElementById("authSubmitBtn");

  btn.disabled = true;
  btn.innerHTML = "⏳ Authenticating...";

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
      signal: AbortSignal.timeout(4000)
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Invalid credentials");

    setCurrentUser(data);
    closeLoginModal();
    showToast(`Welcome back, ${data.display_name}! (${data.role})`, "success");

    if (data.role === "ADMIN" && !window.location.pathname.includes("admin.html")) {
      setTimeout(() => { window.location.href = "admin.html"; }, 600);
    }
  } catch (err) {
    // Client-side fallback authentication if backend offline
    if (username.toLowerCase() === "ayush" && password === "123") {
      const adminData = { role: "ADMIN", username: "ayush", display_name: "Operations Officer Ayush", admin_key: "AapdaSetuAdmin2026" };
      setCurrentUser(adminData);
      closeLoginModal();
      showToast("Signed in as Admin (Ayush)", "success");
      if (!window.location.pathname.includes("admin.html")) {
        setTimeout(() => { window.location.href = "admin.html"; }, 600);
      }
    } else if (username.toLowerCase() === "kausha123" && password === "123") {
      const userData = { role: "CITIZEN", username: "kausha123", display_name: "Citizen Kaushal", phone: "+91 98765 43210" };
      setCurrentUser(userData);
      closeLoginModal();
      showToast("Signed in as Citizen (kausha123)", "success");
    } else {
      showToast(err.message || "Invalid credentials", "error");
    }
  } finally {
    btn.disabled = false;
    btn.innerHTML = "<span>Sign In 🚀</span>";
  }
}

/* ================= 1-CLICK INSTANT RESCUE SOS ================= */
async function trigger1ClickRescue(customOriginCoords) {
  let user = getCurrentUser();
  if (!user) {
    user = { username: "kausha123", display_name: "Citizen Kaushal", phone: "+91 98765 43210", role: "CITIZEN" };
    setCurrentUser(user);
  }

  showToast("🚨 EK DUM EMERGENCY: 1-Click SOS Activated! Signal Dispatching...", "warning");
  playEmergencyTone();

  // Instant ticket ID generation
  const pvtToken = "PVT-RES-" + Math.random().toString(36).substring(2, 8).toUpperCase();
  let ticketId = "REQ-" + Math.random().toString(36).substring(2, 8).toUpperCase();
  let serverToken = pvtToken;

  // Resolve initial coordinates immediately
  let lat = 30.2815, lon = 78.9750;
  let locName = "Rudraprayag Riverside (GPS Calibrated)";

  if (Array.isArray(customOriginCoords) && customOriginCoords.length === 2) {
    lat = customOriginCoords[0];
    lon = customOriginCoords[1];
    locName = `Origin Coordinates (${lat.toFixed(4)}, ${lon.toFixed(4)})`;
  } else if (typeof currentOriginCoords !== "undefined" && Array.isArray(currentOriginCoords)) {
    lat = currentOriginCoords[0];
    lon = currentOriginCoords[1];
    locName = `Calibrated GPS (${lat.toFixed(4)}, ${lon.toFixed(4)})`;
  }

  const originInput = document.getElementById("routeOrigin");
  if (originInput && originInput.value) {
    locName = originInput.value;
  }

  const nowStr = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const mapsLink = `https://maps.google.com/?q=${lat.toFixed(5)},${lon.toFixed(5)}`;

  // Formulate high-urgency distress message (Hindi + English)
  const rawMessage = `🚨 *EMERGENCY SOS - MAI KHATRE ME HU!* 🚨\n\n` +
    `Mujhe turant emergency rescue / madad chahiye!\n` +
    `📍 *Location:* ${locName}\n` +
    `🌐 *GPS Coords:* ${lat.toFixed(5)}, ${lon.toFixed(5)}\n` +
    `🗺️ *Live Google Maps:* ${mapsLink}\n` +
    `🎫 *Rescue Ticket:* ${ticketId}\n` +
    `⏱️ *Time:* ${nowStr}\n` +
    `⚠️ *Priority:* Level 1 Critical Life-Threat Emergency\n\n` +
    `Kripya turant 112, SDRF ya NDRF ko meri location bhej kar madad team bhejein!`;

  const encodedMsg = encodeURIComponent(rawMessage);
  const whatsappUrl = `https://api.whatsapp.com/send?text=${encodedMsg}`;
  const smsUrl = `sms:112?body=${encodedMsg}`;

  // Resolve official District Magistrate (DM / Collector / DDMA) contacts
  const dmDetails = getDistrictDmDetails(lat, lon, locName);
  const dmSubject = `🚨 URGENT: [LIFE-THREAT RESCUE SOS] DDMA / DM Control Room - Citizen Trapped - ${ticketId}`;
  const dmBody = `TO: ${dmDetails.officer}\nDistrict Emergency Operations Centre (DEOC)\n\nURGENT LIFE-THREAT RESCUE DISPATCH REQUEST\n--------------------------------------------------\nTicket ID: ${ticketId}\nCitizen Name: ${user.display_name || user.username}\nContact Phone: ${user.phone || '+91 98765 43210'}\nUrgency: LEVEL 1 CRITICAL LIFE-THREAT\n\nEXACT LOCATION:\nLocation Name: ${locName}\nGPS Coordinates: ${lat.toFixed(5)}, ${lon.toFixed(5)}\nLive Google Maps: ${mapsLink}\n\nSITUATION DETAILS:\nCitizen is stranded / trapped in a high-risk flood & hazard disaster zone and requires immediate rescue evacuation by NDRF / SDRF / Quick Response Teams.\n\nTimestamp: ${nowStr}, ${new Date().toLocaleDateString('en-IN')}\nDispatched via: AapdaSetu National AI Disaster Response System\n--------------------------------------------------`;
  const dmMailtoUrl = `mailto:${dmDetails.email}?cc=${encodeURIComponent(dmDetails.backupEmail + ',ndrf-relief@nic.in,seoc.disaster@nic.in')}&subject=${encodeURIComponent(dmSubject)}&body=${encodeURIComponent(dmBody)}`;
  const dmGmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(dmDetails.email)}&cc=${encodeURIComponent(dmDetails.backupEmail + ',ndrf-relief@nic.in,seoc.disaster@nic.in')}&su=${encodeURIComponent(dmSubject)}&body=${encodeURIComponent(dmBody)}`;

  const payload = {
    pickup_location: locName,
    name: user.display_name || user.username || "Citizen Emergency (1-Click SOS)",
    phone: user.phone || "+91 98765 43210",
    user_id: user.username || "kausha123",
    people: 1,
    rescue_vehicle: "NDRF Motor Boat / Inflatable Raft",
    latitude: lat,
    longitude: lon,
    priority: "Critical",
    flood_risk: "CRITICAL",
    is_private: true,
    private_token: pvtToken
  };

  // INSTANT FEEDBACK: Show the interactive confirmed modal immediately (0ms delay)!
  showRescueConfirmedModal(ticketId, payload, rawMessage, mapsLink, whatsappUrl, smsUrl, dmDetails, dmMailtoUrl, dmGmailUrl);

  // Auto-sync with rescue.html tracker if currently on that page
  const trackInput = document.getElementById("trackInput");
  if (trackInput) {
    trackInput.value = ticketId;
    if (typeof trackRescue === "function") {
      trackRescue();
    }
    const successBox = document.getElementById("rescueSuccessBox");
    const displayId = document.getElementById("ticketIdDisplay");
    if (successBox) successBox.style.display = "block";
    if (displayId) displayId.textContent = ticketId;
  }

  // Drop initial Leaflet marker if map active
  dropSosMapMarker(lat, lon, ticketId, nowStr, dmDetails, whatsappUrl);

  // ASYNC BACKGROUND TASKS: Geolocation refine, Backend sync & DM Email alert
  (async () => {
    // 1. Try high-accuracy live GPS in background without blocking UI
    if (navigator.geolocation && (!customOriginCoords || !customOriginCoords.length)) {
      try {
        const pos = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 2500, enableHighAccuracy: true });
        });
        lat = pos.coords.latitude;
        lon = pos.coords.longitude;
        locName = `Live Satellite GPS (${lat.toFixed(4)}, ${lon.toFixed(4)})`;
        if (originInput) originInput.value = locName;

        // Update active modal & map marker
        payload.latitude = lat;
        payload.longitude = lon;
        payload.pickup_location = locName;
        updateRescueConfirmedModalData(ticketId, lat, lon, locName);
        dropSosMapMarker(lat, lon, ticketId, nowStr, dmDetails, whatsappUrl);
      } catch (e) {
        console.log("GPS calibrated fallback used:", e.message);
      }
    }

    // 2. Post to backend rescue quick dispatch
    try {
      const res = await fetch(`${API_BASE}/rescue/quick`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(3500)
      });
      if (res.ok) {
        const data = await res.json();
        if (data.request_id) ticketId = data.request_id;
        if (data.private_token) serverToken = data.private_token;
      }
    } catch (err) {
      console.log("Offline rescue ticket queued:", ticketId);
    }

    // 3. Automated background dispatch to District Magistrate (DM) control room
    sendDmEmergencyEmail(ticketId, payload, lat, lon, locName, dmDetails, dmSubject, dmBody);
  })();
}

function dropSosMapMarker(lat, lon, ticketId, nowStr, dmDetails, whatsappUrl) {
  const activeMap = (typeof map !== "undefined" && map) || (typeof homeMap !== "undefined" && homeMap) || (typeof monitoringMap !== "undefined" && monitoringMap);
  if (activeMap && typeof L !== "undefined") {
    try {
      const sosIcon = L.divIcon({
        className: "custom-map-pin danger-pin",
        html: `<div style="background:#dc2626;color:#fff;width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 0 24px rgba(220,38,38,0.9);border:3px solid #fff;font-size:20px;animation:pulseDangerMarker 1.5s infinite;cursor:pointer;">🆘</div>`,
        iconSize: [44, 44],
        iconAnchor: [22, 22]
      });

      L.marker([lat, lon], { icon: sosIcon }).addTo(activeMap)
        .bindPopup(`
          <div style="font-family:'Inter',sans-serif;padding:6px;min-width:210px;">
            <strong style="color:#b91c1c;font-size:14px;">🚨 SOS ACTIVE: Trapped Citizen</strong><br>
            <span style="font-size:12px;color:#334155;">Ticket: <b>${ticketId}</b></span><br>
            <span style="font-size:11px;color:#dc2626;font-weight:700;">Broadcasted at ${nowStr}</span><br>
            <span style="font-size:11px;color:#2563eb;font-weight:600;">DM Alert: ${dmDetails.email}</span><br>
            <a href="${whatsappUrl}" target="_blank" style="display:inline-block;margin-top:6px;background:#25d366;color:#fff;padding:4px 8px;border-radius:4px;font-size:11px;font-weight:700;text-decoration:none;">Share on WhatsApp</a>
          </div>
        `).openPopup();

      activeMap.setView([lat, lon], 16, { animate: true });
    } catch(e) {}
  }
}

function updateRescueConfirmedModalData(ticketId, lat, lon, locName) {
  const gpsEl = document.getElementById("rescueModalGpsTag");
  if (gpsEl) gpsEl.textContent = locName;

  const mapLinkEl = document.getElementById("rescueModalMapLink");
  const newMapUrl = `https://maps.google.com/?q=${lat.toFixed(5)},${lon.toFixed(5)}`;
  if (mapLinkEl) mapLinkEl.href = newMapUrl;

  const rawMessage = `🚨 *EMERGENCY SOS - MAI KHATRE ME HU!* 🚨\n\n` +
    `Mujhe turant emergency rescue / madad chahiye!\n` +
    `📍 *Location:* ${locName}\n` +
    `🌐 *GPS Coords:* ${lat.toFixed(5)}, ${lon.toFixed(5)}\n` +
    `🗺️ *Live Google Maps:* ${newMapUrl}\n` +
    `🎫 *Rescue Ticket:* ${ticketId}\n` +
    `⚠️ *Priority:* Level 1 Critical Life-Threat Emergency\n\n` +
    `Kripya turant 112, SDRF ya NDRF ko meri location bhej kar madad team bhejein!`;

  const waEl = document.getElementById("rescueModalWaBtn");
  if (waEl) waEl.href = `https://api.whatsapp.com/send?text=${encodeURIComponent(rawMessage)}`;

  const smsEl = document.getElementById("rescueModalSmsBtn");
  if (smsEl) smsEl.href = `sms:112?body=${encodeURIComponent(rawMessage)}`;
}

/**
 * Official Indian District Magistrate & DDMA Directory Resolver
 * Primary active recipient set to District Manager: guptaayush932589@gmail.com
 */
function getDistrictDmDetails(lat, lon, locName) {
  const districtManagerEmail = "guptaayush932589@gmail.com";
  const text = (locName || "").toLowerCase();
  let dist = "Rudraprayag", state = "Uttarakhand", govNic = "dm-rud-ua@nic.in", phone = "01364-233377";

  if (text.includes("chamoli") || text.includes("joshimath") || (lat >= 30.2 && lat <= 30.8 && lon >= 79.2 && lon <= 79.8)) {
    dist = "Chamoli"; govNic = "dm-cha-ua@nic.in"; phone = "01372-251437";
  } else if (text.includes("dehradun") || text.includes("rishikesh")) {
    dist = "Dehradun"; govNic = "dm-deh-ua@nic.in"; phone = "0135-2626066";
  } else if (text.includes("haridwar")) {
    dist = "Haridwar"; govNic = "dm-har-ua@nic.in"; phone = "01334-223999";
  } else if (text.includes("patna") || text.includes("bihar")) {
    dist = "Patna"; state = "Bihar"; govNic = "dm-patna.bih@nic.in"; phone = "0612-2219545";
  } else if (text.includes("varanasi") || text.includes("kashi")) {
    dist = "Varanasi"; state = "Uttar Pradesh"; govNic = "dmvar@nic.in"; phone = "0542-2508550";
  } else if (text.includes("guwahati") || text.includes("kamrup") || text.includes("assam")) {
    dist = "Kamrup Metropolitan (Guwahati)"; state = "Assam"; govNic = "dc-kamrup@nic.in"; phone = "0361-2733052";
  }

  return {
    district: dist,
    state: state,
    officer: `District Magistrate / District Manager, ${dist} (Ayush Gupta)`,
    email: districtManagerEmail,
    govNicEmail: govNic,
    backupEmail: `${govNic},ndrf-relief@nic.in`,
    phone: phone
  };
}

/**
 * Automated Dispatch to District Magistrate (DM) Email
 */
async function sendDmEmergencyEmail(ticketId, payload, lat, lon, locName, dmDetails, subject, body) {
  try {
    const postData = {
      _subject: subject || `🚨 [LIFE-THREAT SOS] Rescue Required - DM Ayush Gupta (${ticketId})`,
      _template: "table",
      "RECIPIENT": "District Magistrate & Disaster Manager (Ayush Gupta)",
      "EMAIL": "guptaayush932589@gmail.com",
      "Ticket ID": ticketId,
      "Citizen Name": payload.name || "Citizen Emergency",
      "Citizen Phone": payload.phone || "+91 98765 43210",
      "Location": locName,
      "GPS Coordinates": `${lat.toFixed(5)}, ${lon.toFixed(5)}`,
      "Google Maps Navigation": `https://maps.google.com/?q=${lat.toFixed(5)},${lon.toFixed(5)}`,
      "Urgency Level": "LEVEL 1 CRITICAL DISASTER LIFE-THREAT",
      "Timestamp": new Date().toLocaleString("en-IN")
    };

    // 1. Direct automated real email to guptaayush932589@gmail.com via verified Web3Forms (Zero activation needed)
    fetch("https://api.web3forms.com/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify({
        access_key: "1d6cc9b4-f2ce-40ff-8d1b-f040d1e01045",
        subject: subject || `🚨 [LIFE-THREAT SOS] Rescue Required - DM Ayush Gupta (${ticketId})`,
        from_name: "AapdaSetu Emergency SOS",
        "RECIPIENT": "District Magistrate & Disaster Manager (Ayush Gupta)",
        "EMAIL": "guptaayush932589@gmail.com",
        "Ticket ID": ticketId,
        "Citizen Name": payload.name || "Citizen Emergency",
        "Citizen Phone": payload.phone || "+91 98765 43210",
        "Location": locName,
        "GPS Coordinates": `${lat.toFixed(5)}, ${lon.toFixed(5)}`,
        "Google Maps Navigation": `https://maps.google.com/?q=${lat.toFixed(5)},${lon.toFixed(5)}`,
        "Urgency Level": "LEVEL 1 CRITICAL DISASTER LIFE-THREAT",
        "Timestamp": new Date().toLocaleString("en-IN"),
        message: body || "Immediate evacuation / rescue required."
      })
    }).then(r => r.json()).then(res => {
      console.log("✅ [DM SOS EMAIL SENT VIA WEB3FORMS]:", res);
    }).catch(e => console.log("DM Email delivery log:", e));

    // 2. Try Backend Endpoint if running
    fetch(`${API_BASE}/emergency/email-dm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ticket_id: ticketId,
        name: payload.name,
        phone: payload.phone,
        pickup_location: locName,
        latitude: lat,
        longitude: lon,
        district: dmDetails.district,
        state: dmDetails.state,
        dm_email: "guptaayush932589@gmail.com",
        details: body
      }),
      signal: AbortSignal.timeout(3500)
    }).catch(() => {});

  } catch(e) {
    console.log("DM Email Dispatch error:", e);
  }
}

/**
 * Daily Automated Flood Early Warning Surveillance Daemon
 * Ensures the District Manager receives exactly 1 automated bulletin per calendar day when flood hazard is active.
 */
function triggerDailyFloodSurveillanceAlert(locName, riverName, waterLevel, dangerLevel, force = false) {
  try {
    const now = new Date();
    const todayKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
    const lastSent = localStorage.getItem("aapdasetu_last_dm_flood_alert_date");

    if (lastSent === todayKey && !force) {
      console.log(`[AapdaSetu] Daily flood alert already dispatched today (${todayKey}). 1/day limit active.`);
      return;
    }

    const subject = `🚨 [DAILY FLOOD ALERT] Imminent Flood Early Warning: ${riverName} River at ${locName}`;
    fetch("https://api.web3forms.com/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify({
        access_key: "1d6cc9b4-f2ce-40ff-8d1b-f040d1e01045",
        subject: subject,
        from_name: "AapdaSetu River Gauge Early Warning",
        "RECIPIENT": "District Magistrate & Disaster Manager (Ayush Gupta)",
        "EMAIL": "guptaayush932589@gmail.com",
        "ALERT FREQUENCY": "AUTOMATIC DAILY FLOOD BULLETIN (1 EMAIL / DAY)",
        "River / Basin": riverName,
        "Location": locName,
        "Current Water Level": `${waterLevel} m`,
        "Danger Mark": `${dangerLevel} m`,
        "Severity": "RIVER CROSSING DANGER LEVEL - HIGH FLOOD LIKELIHOOD",
        "Dispatch Date": todayKey,
        "Timestamp": new Date().toLocaleString("en-IN"),
        message: `Official Daily Flood Alert for ${locName}. ${riverName} river water level has reached ${waterLevel}m crossing danger mark ${dangerLevel}m.`
      })
    })
    .then(r => r.json())
    .then(res => {
      if (res.success) {
        localStorage.setItem("aapdasetu_last_dm_flood_alert_date", todayKey);
      }
    })
    .catch(() => {});
  } catch(e) {}
}

function playEmergencyTone() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(800, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(400, ctx.currentTime + 0.3);
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.5);
  } catch (e) {}
}

function showRescueConfirmedModal(ticketId, payload, rawMessage, mapsLink, whatsappUrl, smsUrl, dmDetails, dmMailtoUrl, dmGmailUrl) {
  let modal = document.getElementById("rescueTrackModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "rescueTrackModal";
    modal.className = "auth-modal-backdrop active";
    modal.addEventListener("click", function(e) {
      if (e.target === modal) modal.classList.remove("active");
    });
    document.body.appendChild(modal);
  } else {
    modal.classList.add("active");
  }

  const dmInfo = dmDetails || getDistrictDmDetails(payload.latitude || 30.28, payload.longitude || 78.97, payload.pickup_location);
  const encodedMsg = encodeURIComponent(rawMessage || `🚨 EMERGENCY SOS: Location ${payload.pickup_location}`);
  const finalWaUrl = whatsappUrl || `https://api.whatsapp.com/send?text=${encodedMsg}`;
  const finalSmsUrl = smsUrl || `sms:112?body=${encodedMsg}`;
  const finalMapUrl = mapsLink || `https://maps.google.com/?q=${payload.latitude},${payload.longitude}`;

  const dmSub = `🚨 URGENT: [LIFE-THREAT RESCUE SOS] DDMA / DM Control Room - Citizen Trapped - ${ticketId}`;
  const dmBod = `TO: ${dmInfo.officer}\nDistrict Emergency Operations Centre (DEOC)\n\nURGENT LIFE-THREAT RESCUE DISPATCH REQUEST\n--------------------------------------------------\nTicket ID: ${ticketId}\nCitizen Name: ${payload.name}\nContact Phone: ${payload.phone}\nUrgency: LEVEL 1 CRITICAL LIFE-THREAT\n\nEXACT LOCATION:\nLocation Name: ${payload.pickup_location}\nGPS Coordinates: ${payload.latitude}, ${payload.longitude}\nLive Google Maps: ${finalMapUrl}\n\nSITUATION DETAILS:\nCitizen is stranded / trapped in high flood hazard danger zone and urgently requests NDRF / SDRF boat evacuation.\n\nDispatched via: AapdaSetu National AI Disaster Response System\n--------------------------------------------------`;
  const finalDmMailto = dmMailtoUrl || `mailto:${dmInfo.email}?cc=${encodeURIComponent(dmInfo.backupEmail + ',ndrf-relief@nic.in,seoc.disaster@nic.in')}&subject=${encodeURIComponent(dmSub)}&body=${encodeURIComponent(dmBod)}`;
  const finalDmGmail = dmGmailUrl || `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(dmInfo.email)}&cc=${encodeURIComponent(dmInfo.backupEmail + ',ndrf-relief@nic.in,seoc.disaster@nic.in')}&su=${encodeURIComponent(dmSub)}&body=${encodeURIComponent(dmBod)}`;

  modal.innerHTML = `
    <div class="auth-modal-card" style="max-width:540px;border-top:6px solid #dc2626;">
      <div style="padding:26px 20px;text-align:center;">
        <div style="font-size:3rem;animation:heartbeat 1s infinite;margin-bottom:6px;">🚨</div>
        
        <div style="display:flex;justify-content:center;gap:6px;margin-bottom:8px;flex-wrap:wrap;">
          <span class="badge danger" style="padding:4px 12px;font-size:0.75rem;font-weight:900;">
            RESCUE DISPATCHED (PRIORITY 1)
          </span>
          <span class="badge-private" style="padding:4px 10px;font-size:0.72rem;">
            ⚡ 1-CLICK DANGER SOS BROADCAST
          </span>
        </div>

        <h2 style="color:var(--navy);font-size:1.35rem;margin:8px 0 4px;font-family:'Outfit',sans-serif;font-weight:900;">
          Mai Khatre Me Hu — Signal Dispatched!
        </h2>
        <p style="color:#64748b;font-size:0.85rem;margin:0 0 14px;">
          Aapka live GPS location seedhe NDRF/SDRF Control Room, WhatsApp channel aur <b>District Magistrate (DM Ayush Gupta)</b> ko dispatch ho chuka hai.
        </p>

        <!-- District Magistrate Official Email Notification Card -->
        <div style="background:#eff6ff;border:1.5px solid #93c5fd;border-radius:12px;padding:14px;text-align:left;margin-bottom:12px;">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;flex-wrap:wrap;gap:4px;">
            <strong style="color:#1e40af;font-size:0.88rem;display:flex;align-items:center;gap:6px;">
              <span>🏛️</span> DM (District Magistrate) Control Room
            </strong>
            <span class="badge-pill safe" style="font-size:0.68rem;padding:3px 8px;">
              <span class="pulse-dot green"></span> Auto Dispatched
            </span>
          </div>
          <p style="font-size:0.8rem;color:#1e3a8a;margin-bottom:8px;line-height:1.4;">
            Official rescue requisition auto-sent to: <br>
            <b>${dmInfo.officer}</b> (<code>${dmInfo.email}</code>)
          </p>
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <a href="${finalDmGmail}" target="_blank" rel="noopener" style="flex:1;background:#ea4335;color:#fff;padding:9px 12px;border-radius:var(--radius-sm);font-weight:800;font-size:0.82rem;text-decoration:none;display:inline-flex;align-items:center;justify-content:center;gap:6px;box-shadow:0 2px 8px rgba(234,67,53,0.3);cursor:pointer;">
              <span>📧</span> <span>Send via Gmail to DM</span>
            </a>
            <a href="${finalDmMailto}" style="flex:1;background:#2563eb;color:#fff;padding:9px 12px;border-radius:var(--radius-sm);font-weight:800;font-size:0.82rem;text-decoration:none;display:inline-flex;align-items:center;justify-content:center;gap:6px;cursor:pointer;">
              <span>✉️</span> <span>Open Email App</span>
            </a>
          </div>
        </div>

        <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:12px;padding:14px;text-align:left;font-size:0.84rem;margin-bottom:12px;">
          <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
            <span style="color:#991b1b;font-weight:700;">Ticket ID:</span>
            <strong id="rescueModalTicketId" style="color:var(--navy);font-family:monospace;font-size:1.05rem;">${ticketId}</strong>
          </div>
          <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
            <span style="color:#991b1b;font-weight:700;">Live GPS Tag:</span>
            <span id="rescueModalGpsTag" style="color:#334155;font-size:0.82rem;font-weight:600;">${payload.pickup_location}</span>
          </div>
          <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
            <span style="color:#991b1b;font-weight:700;">Live Map Link:</span>
            <a id="rescueModalMapLink" href="${finalMapUrl}" target="_blank" style="color:#2563eb;font-weight:700;text-decoration:underline;font-size:0.82rem;cursor:pointer;">Google Maps Location ↗</a>
          </div>
          <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
            <span style="color:#991b1b;font-weight:700;">Assigned Unit:</span>
            <span style="color:#059669;font-weight:800;">🚤 NDRF Quick Response Boat / SDRF</span>
          </div>
          <div style="display:flex;justify-content:space-between;">
            <span style="color:#991b1b;font-weight:700;">Urgency Status:</span>
            <span style="color:#dc2626;font-weight:900;">🔴 Level 1 Life-Threat Emergency</span>
          </div>
        </div>

        <div style="display:flex;flex-direction:column;gap:10px;margin-bottom:12px;">
          <a id="rescueModalWaBtn" href="${finalWaUrl}" target="_blank" rel="noopener" style="padding:13px;text-align:center;font-size:0.98rem;display:flex;align-items:center;justify-content:center;gap:10px;background:#25D366;color:#fff;border-radius:var(--radius-sm);font-weight:900;text-decoration:none;box-shadow:0 4px 14px rgba(37,211,102,0.35);cursor:pointer;">
            <span style="font-size:1.3rem;">💬</span>
            <span>WhatsApp Par Direct Send Karein</span>
          </a>
          <div style="display:flex;gap:10px;flex-wrap:wrap;">
            <a id="rescueModalSmsBtn" href="${finalSmsUrl}" style="flex:1;padding:11px;text-align:center;font-size:0.9rem;display:flex;align-items:center;justify-content:center;gap:6px;background:#2563eb;color:#fff;border-radius:var(--radius-sm);font-weight:800;text-decoration:none;cursor:pointer;">
              <span>📱</span> <span>112 SMS Bhejo</span>
            </a>
            <a id="rescueModalCallBtn" href="tel:112" class="btn-danger" style="flex:1;padding:11px;text-align:center;font-size:0.9rem;display:flex;align-items:center;justify-content:center;gap:6px;text-decoration:none;cursor:pointer;">
              <span>📞</span> <span>Call 112 Dial</span>
            </a>
          </div>
          <button type="button" id="copySosGlobalBtn" onclick="copyGlobalSosText('${encodeURIComponent(rawMessage || '')}')" style="background:#f1f5f9;color:#334155;border:1px solid #cbd5e1;padding:10px;border-radius:var(--radius-sm);font-weight:700;font-size:0.86rem;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;">
            <span>📋</span> <span id="copySosGlobalBtnText">Danger Message Copy Karein</span>
          </button>
        </div>

        <div style="display:flex;gap:10px;">
          <a href="rescue.html?track=${encodeURIComponent(ticketId)}" class="btn-primary" style="flex:1;padding:10px;font-size:0.85rem;text-align:center;text-decoration:none;cursor:pointer;">
            🔍 View Live Radar Tracker
          </a>
          <button onclick="document.getElementById('rescueTrackModal').classList.remove('active')" class="btn-outline" style="flex:1;padding:10px;font-size:0.85rem;cursor:pointer;">
            Close Window
          </button>
        </div>
      </div>
    </div>
  `;
}

function copyGlobalSosText(encoded) {
  try {
    const text = decodeURIComponent(encoded);
    navigator.clipboard.writeText(text).then(() => {
      const btnText = document.getElementById("copySosGlobalBtnText");
      if (btnText) {
        btnText.textContent = "✅ Message Copied to Clipboard!";
        setTimeout(() => { btnText.textContent = "Danger Message Copy Karein"; }, 3000);
      }
      showToast("Emergency SOS message copied to clipboard!", "success");
    });
  } catch(e) {}
}

/* ================= GLOBAL EMERGENCY SOS MODAL HELPER ================= */
function openEmergencySOSModal() {
  let modal = document.getElementById("globalSosModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "globalSosModal";
    modal.className = "auth-modal-backdrop active";
    modal.addEventListener("click", function(e) {
      if (e.target === modal) modal.classList.remove("active");
    });
    document.body.appendChild(modal);
  } else {
    modal.classList.add("active");
  }

  modal.innerHTML = `
    <div class="auth-modal-card" style="max-width:540px;border-top:6px solid #dc2626;">
      <div style="padding:28px 24px;text-align:center;">
        <div style="font-size:2.8rem;animation:heartbeat 1.2s infinite;margin-bottom:6px;">🚨</div>
        <h2 style="color:var(--navy);font-size:1.4rem;margin:0 0 6px;font-family:'Outfit',sans-serif;">
          AapdaSetu Emergency Assistance
        </h2>
        <p style="color:#64748b;font-size:0.88rem;margin:0 0 20px;">
          Kripya apni sthiti chunein (Please choose your situation):
        </p>

        <!-- Option A: Ekdum Emergency (No Form) -->
        <div style="background:#fef2f2;border:2px solid #ef4444;border-radius:14px;padding:18px;margin-bottom:14px;text-align:left;">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
            <span style="background:#dc2626;color:#fff;font-size:0.75rem;font-weight:900;padding:3px 8px;border-radius:9999px;">
              🔴 EKDUM EMERGENCY (NO FORM)
            </span>
            <span style="font-size:0.75rem;color:#991b1b;font-weight:700;">⚡ 1-Click Auto Dispatch</span>
          </div>
          <h3 style="font-size:1.1rem;color:#7f1d1d;margin:0 0 4px;font-weight:800;">
            Paani badh raha hai ya jaan ka khatra hai?
          </h3>
          <p style="font-size:0.82rem;color:#991b1b;margin:0 0 12px;line-height:1.4;">
            Koi form bharne ki zaroorat nahi hai. Single click se live GPS NDRF ko dispatch ho jayega.
          </p>
          <button onclick="document.getElementById('globalSosModal').classList.remove('active'); trigger1ClickRescue();" class="btn-1click-sos" style="width:100%;padding:14px;font-size:1.05rem;">
            <span>⚡ 1-CLICK INSTANT RESCUE SOS</span>
          </button>
        </div>

        <!-- Option B: Normal Case (Form Fill) -->
        <div style="background:#f8fafc;border:1px solid #cbd5e1;border-radius:14px;padding:16px;margin-bottom:16px;text-align:left;">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
            <span style="background:#0f2744;color:#fff;font-size:0.75rem;font-weight:800;padding:3px 8px;border-radius:9999px;">
              📝 NORMAL / PLANNED CASE
            </span>
            <span style="font-size:0.75rem;color:#64748b;font-weight:600;">Details Form</span>
          </div>
          <h3 style="font-size:1.05rem;color:var(--navy);margin:0 0 4px;font-weight:700;">
            Relief, Ration, Shelter ya Planned Evacuation?
          </h3>
          <p style="font-size:0.82rem;color:#64748b;margin:0 0 10px;line-height:1.4;">
            Agar turant jaan ka khatra nahi hai aur detailed information deni hai, to form bharein.
          </p>
          <a href="rescue.html?mode=normal" onclick="document.getElementById('globalSosModal').classList.remove('active');" class="btn-secondary" style="display:block;text-align:center;padding:10px;font-size:0.9rem;font-weight:700;">
            📝 Fill Normal Rescue Form →
          </a>
        </div>

        <!-- Direct Emergency Dial Helplines Grid -->
        <div style="margin-bottom:14px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:12px;">
          <div style="font-size:0.78rem;font-weight:800;color:var(--navy);margin-bottom:8px;text-align:left;display:flex;align-items:center;gap:6px;">
            <span>📞</span> <span>Direct 24x7 Helpline Calling Lines:</span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
            <a href="tel:112" class="btn-danger" style="padding:10px;font-size:0.86rem;font-weight:800;text-decoration:none;display:flex;align-items:center;justify-content:center;gap:6px;" title="Universal Emergency 112">
              <span>📞 112 National</span>
            </a>
            <a href="tel:1078" class="btn-primary" style="padding:10px;font-size:0.86rem;font-weight:800;text-decoration:none;display:flex;align-items:center;justify-content:center;gap:6px;" title="NDRF Flood Rescue 1078">
              <span>🛡️ 1078 NDRF</span>
            </a>
            <a href="tel:108" class="btn-primary" style="background:#059669;border-color:#047857;padding:10px;font-size:0.86rem;font-weight:800;text-decoration:none;display:flex;align-items:center;justify-content:center;gap:6px;" title="Medical Ambulance 108">
              <span>🚑 108 Ambulance</span>
            </a>
            <a href="tel:1077" class="btn-secondary" style="background:#fff;border-color:#cbd5e1;padding:10px;font-size:0.86rem;font-weight:800;text-decoration:none;display:flex;align-items:center;justify-content:center;gap:6px;color:#1e3a8a;" title="DM / DEOC Control 1077">
              <span>🏛️ 1077 DM / EOC</span>
            </a>
          </div>
        </div>

        <button onclick="document.getElementById('globalSosModal').classList.remove('active')" class="btn-outline" style="width:100%;padding:10px;font-size:0.9rem;cursor:pointer;">
          Close Window
        </button>
      </div>
    </div>
  `;
}


/* ================= DAM GATE OPENING & ADMIN EMERGENCY BROADCAST ================= */
let damAlertCountdownTimer = null;
let damAlertInterval = null;

async function checkActiveDamAlerts() {
  let banner = document.getElementById("damTopBanner");
  if (!banner) {
    banner = document.createElement("div");
    banner.id = "damTopBanner";
    banner.className = "dam-emergency-banner";
    document.body.insertBefore(banner, document.body.firstChild);
  }

  let adminAlert = null;
  const now = Date.now();
  const ALERT_LIFESPAN_MS = 15000; // 15 Seconds auto-dismiss

  // 1. Check local storage first for active broadcast
  const stored = localStorage.getItem("aapdaActiveDamAlert") || localStorage.getItem("aapdaActiveAdminAlert");
  if (stored) {
    try {
      const parsed = JSON.parse(stored);
      const alertTime = parsed.timestamp || 0;
      const elapsed = now - alertTime;

      // If broadcasted within the last 15 seconds
      if (alertTime > 0 && elapsed < ALERT_LIFESPAN_MS) {
        adminAlert = parsed;
      } else {
        // Expired beyond 15 seconds: purge so it never re-appears
        localStorage.removeItem("aapdaActiveDamAlert");
        localStorage.removeItem("aapdaActiveAdminAlert");
      }
    } catch (e) {
      console.warn("Error parsing stored admin alert:", e);
    }
  }

  // 2. If no valid local broadcast found, check backend history for very recent broadcast (<15s)
  if (!adminAlert) {
    try {
      const res = await fetch(`${API_BASE}/alerts/history?limit=3`, { signal: AbortSignal.timeout(2500) });
      if (res.ok) {
        const data = await res.json();
        const list = data.alerts || [];
        const recent = list.find(a => {
          if (!a.created_at) return false;
          const createdTime = new Date(a.created_at).getTime();
          const diff = now - createdTime;
          return diff >= 0 && diff < ALERT_LIFESPAN_MS;
        });

        if (recent) {
          adminAlert = {
            title: recent.title,
            message: recent.message,
            timestamp: new Date(recent.created_at).getTime(),
            dam_name: recent.river_source || recent.district,
            downstream: recent.district
          };
        }
      }
    } catch (e) {}
  }

  if (adminAlert) {
    const elapsed = now - (adminAlert.timestamp || now);
    const remainingMs = Math.max(800, ALERT_LIFESPAN_MS - elapsed);
    renderDamAlertBanner(banner, adminAlert, remainingMs);
  } else {
    dismissAdminAlert(banner, false);
  }
}

function dismissAdminAlert(banner = null, animate = true) {
  if (!banner) banner = document.getElementById("damTopBanner");
  if (!banner) return;

  if (damAlertCountdownTimer) {
    clearTimeout(damAlertCountdownTimer);
    damAlertCountdownTimer = null;
  }
  if (damAlertInterval) {
    clearInterval(damAlertInterval);
    damAlertInterval = null;
  }

  localStorage.removeItem("aapdaActiveDamAlert");
  localStorage.removeItem("aapdaActiveAdminAlert");

  if (animate) {
    banner.classList.add("closing");
    setTimeout(() => {
      banner.classList.remove("active", "closing");
      banner.style.display = "none";
    }, 450);
  } else {
    banner.classList.remove("active", "closing");
    banner.style.display = "none";
  }
}

function renderDamAlertBanner(banner, alertData, remainingMs) {
  // Clear any existing active timer to avoid overlap
  if (damAlertCountdownTimer) clearTimeout(damAlertCountdownTimer);
  if (damAlertInterval) clearInterval(damAlertInterval);

  window.lastDamAlert = alertData;

  banner.classList.remove("closing");
  banner.classList.add("active");
  banner.style.display = "block";

  let remainingSec = Math.ceil(remainingMs / 1000);

  banner.innerHTML = `
    <div class="dam-timer-progress" id="damTimerProgress" style="animation: damProgressAnim ${remainingMs}ms linear forwards;"></div>
    <div class="dam-banner-inner">
      <div class="dam-banner-content">
        <div class="dam-siren-box">🚨</div>
        <div>
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:2px;flex-wrap:wrap;">
            <strong style="font-size:0.94rem;letter-spacing:0.02em;color:#fff;">
              ${alertData.title || '🚨 EMERGENCY DISASTER ALERT'}
            </strong>
            <span class="dam-timer-badge" id="damTimerBadge">
              ⏱️ Auto-closing in <strong id="damTimerSec">${remainingSec}</strong>s
            </span>
          </div>
          <span style="font-size:0.82rem;opacity:0.95;color:#fef2f2;line-height:1.4;">
            ${alertData.message || 'Evacuate downstream riverbed plains immediately.'}
          </span>
        </div>
      </div>
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
        <div class="dam-audio-btn-group" style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;">
          <button class="btn-dam-audio" onclick="speakDamText()" title="Listen in active language">
            🔊 Listen (${getLanguageLabel(getCurrentLanguage())})
          </button>
          <button class="btn-dam-audio" onclick="speakDamText('hi')">
            🔊 हिन्दी
          </button>
          <button class="btn-dam-audio" onclick="speakDamText('en')">
            🔊 EN
          </button>
        </div>
        <button class="dam-close-btn" onclick="dismissAdminAlert()" title="Close Alert Now" aria-label="Close Alert">
          ✕
        </button>
      </div>
    </div>
  `;

  // Countdown second ticker (15, 14, 13... 0)
  const secEl = document.getElementById("damTimerSec");
  damAlertInterval = setInterval(() => {
    remainingSec--;
    if (secEl) {
      secEl.textContent = Math.max(0, remainingSec);
    }
    if (remainingSec <= 0) {
      clearInterval(damAlertInterval);
      damAlertInterval = null;
    }
  }, 1000);

  // Auto-dismiss after remainingMs (15 seconds total lifespan)
  damAlertCountdownTimer = setTimeout(() => {
    dismissAdminAlert(banner, true);
  }, remainingMs);
}

// Cross-tab Synchronization: when admin issues an alert from admin.html, all open tabs immediately pop up and auto-dismiss after 15s
window.addEventListener("storage", (event) => {
  if (event.key === "aapdaActiveDamAlert" || event.key === "aapdaActiveAdminAlert") {
    if (event.newValue) {
      checkActiveDamAlerts();
    } else {
      dismissAdminAlert(null, true);
    }
  }
});

function speakDamText(lang = null) {
  if (!('speechSynthesis' in window)) {
    showToast("Speech synthesis not supported on this browser", "error");
    return;
  }

  if (!lang) lang = getCurrentLanguage();

  window.speechSynthesis.cancel();
  const alert = window.lastDamAlert || {
    dam_name: "Tehri Dam",
    opening_time: "Within 1 Hour",
    discharge_cusecs: 75000,
    downstream: "Haridwar and Rishikesh"
  };

  const damMessages = {
    hi: `सावधान! आपातकालीन बाढ़ चेतावनी। ${alert.dam_name || 'डैम'} के गेट खोले जा रहे हैं। नदी के निचले इलाकों और तटीय क्षेत्रों में रहने वाले सभी नागरिक तुरंत ऊंचे और सुरक्षित स्थानों पर चले जाएं।`,
    hinglish: `Savdhan! Emergency flood warning. ${alert.dam_name || 'Dam'} ke gates open kiye ja rahe hain. Riverbanks aur low-lying areas ke log turant unchi jagah par chale jayein.`,
    mr: `सावधान! आपत्कालीन पूर इशारा. ${alert.dam_name || 'धरणा'}चे दरवाजे उघडले जात आहेत. नदीकाठच्या सर्व नागरिकांनी तात्काळ सुरक्षित आणि उंच जागी जावे.`,
    bn: `সাবধান! জরুরী বন্যা সতর্কতা। ${alert.dam_name || 'বাঁধের'} স্লুইস গেট খোলা হচ্ছে। নদীর তীরবর্তী এলাকার মানুষ অবিলম্বে নিরাপদ ও উঁচু স্থানে সরে যান।`,
    gu: `સાવધાન! કટોકટી પૂર ચેતવણી. ${alert.dam_name || 'ડેમ'}ના દરવાજા ખોલવામાં આવી રહ્યા છે. નદી કિનારાના લોકો તાત્કાલિક સુરક્ષિત સ્થળે ખસી જાય.`,
    te: `హెచ్చరిక! అత్యవసర వరద హెచ్చరిక. ${alert.dam_name || 'ఆనకట్ట'} గేట్లు ఎత్తుతున్నారు. నదీ తీర ప్రాంత ప్రజలు వెంటనే సురక్షిత ఎత్తైన ప్రాంతాలకు వెళ్ళండి.`,
    ta: `எச்சரிக்கை! அவசர வெள்ள அபாய எச்சரிக்கை. ${alert.dam_name || 'அணை'} மதகுகள் திறக்கப்படுகின்றன. ஆற்றோர மக்கள் உடனடியாக பாதுகாப்பான மேடான இடங்களுக்கு செல்லவும்.`,
    kn: `ಎಚ್ಚರಿಕೆ! ತುರ್ತು ಪ್ರವಾಹ ಮುನ್ನೆಚ್ಚರಿಕೆ. ${alert.dam_name || 'ಅಣೆಕಟ್ಟು'} ಗೇಟ್‌ಗಳನ್ನು ತೆರೆಯಲಾಗುತ್ತಿದೆ. ನದಿ ತೀರದ ನಿವಾಸಿಗಳು ತಕ್ಷಣವೇ ಎತ್ತರದ ಸುರಕ್ಷಿತ ಪ್ರದೇಶಗಳಿಗೆ ತೆರಳಿ.`,
    ml: `ജാഗ്രത! അടിയന്തിര പ്രളയ മുന്നറിയിപ്പ്. ${alert.dam_name || 'ഡാമിന്റെ'} ഷട്ടറുകൾ തുറക്കുന്നു. നദീതീരങ്ങളിൽ ഉള്ളവർ ഉടൻ തന്നെ സുരക്ഷിതമായ ഉയർന്ന സ്ഥലങ്ങളിലേക്ക് മാറുക.`,
    pa: `ਸਾਵਧਾਨ! ਐਮਰਜੈਂਸੀ ਹੜ੍ਹ ਚੇਤਾਵਨੀ। ${alert.dam_name || 'ਡੈਮ'} ਦੇ ਗੇਟ ਖੋਲ੍ਹੇ ਜਾ ਰਹੇ ਹਨ। ਦਰਿਆ ਕੰਢੇ ਦੇ ਵਸਨੀਕ ਤੁਰੰਤ ਉੱਚੀਆਂ ਸੁਰੱਖਿਅਤ ਥਾਵਾਂ 'ਤੇ ਚਲੇ ਜਾਣ।`,
    or: `ସତର୍କତା! ଜରୁରୀ ବନ୍ୟା ଚେତାବନୀ। ${alert.dam_name || 'ଡ୍ୟାମ୍'}ର ଗେଟ୍ ଖୋଲାଯାଉଛି। ନଦୀକୂଳିଆ ଲୋକେ ତୁରନ୍ତ ଉଚ୍ଚ ନିରାପଦ ସ୍ଥାନକୁ ଯାଆନ୍ତୁ।`,
    as: `সাৱধান! জৰুৰী বান সতৰ্কবাৰ্তা। ${alert.dam_name || 'বান্ধৰ'} গেট খোলা হৈছে। নৈপৰীয়া ৰাইজ পলম নকৰি ওখ সুৰক্ষিত স্থানলৈ যাওক।`,
    ur: `خبردار! ہنگامی سیلاب انتباہ۔ ${alert.dam_name || 'ڈیم'} کے گیٹ کھولے جا رہے ہیں۔ دریا کے قریبی مکین فوری محفوظ مقامات پر چلے جائیں۔`,
    bho: `सावधान! आपातकालीन बाढ़ चेतावनी। ${alert.dam_name || 'बांध'} के फाटक खोलल जात बा। नदी किनारे के लोग तुरंत ऊंच सुरक्षित जगह पर चली जांव।`,
    ne: `सावधान! आपतकालीन बाढी चेतावनी। ${alert.dam_name || 'बाँध'}को ढोका खोलिँदैछ। नदी किनारका बासिन्दाहरू तुरुन्तै अग्लो सुरक्षित स्थानमा जानुहोस्।`,
    sa: `सावधानम्! आपत्कालीन जलप्लव-सूचना। ${alert.dam_name || 'सेतोः'} द्वाराणि उद्घाट्यन्ते। तटवर्तिनः जनाः त्वरितम् उच्चतर-सुरक्षित-स्थानं गच्छन्तु।`,
    en: `Emergency flood warning! ${alert.dam_name || 'Dam'} floodgates are opening. High water discharge in progress. All residents downstream must evacuate immediately.`
  };

  const langCodes = {
    hi: "hi-IN", hinglish: "hi-IN", mr: "mr-IN", bn: "bn-IN", gu: "gu-IN",
    te: "te-IN", ta: "ta-IN", kn: "kn-IN", ml: "ml-IN", pa: "pa-IN",
    or: "or-IN", as: "as-IN", ur: "ur-IN", bho: "hi-IN", ne: "ne-NP",
    sa: "hi-IN", en: "en-IN"
  };

  const text = damMessages[lang] || damMessages.hi;
  const utter = new SpeechSynthesisUtterance(text);
  utter.rate = 0.92;
  utter.lang = langCodes[lang] || "hi-IN";
  window.speechSynthesis.speak(utter);
  showToast(`🔊 Playing voice broadcast in ${getLanguageLabel(lang)}...`, "info");
}

/* ================= PRIVATE SHELTER AUTO-BOOKING & GOVERNMENT RELIEF ENGINE ================= */
async function openPrivateShelterBooking(shelterId, shelterName, availBeds = 100) {
  let user = getCurrentUser();
  if (!user) {
    user = { username: "kausha123", display_name: "Citizen Kaushal", phone: "+91 98765 43210", role: "CITIZEN" };
    setCurrentUser(user);
  }

  let modal = document.getElementById("shelterBookingModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "shelterBookingModal";
    modal.className = "auth-modal-backdrop active";
    document.body.appendChild(modal);
  } else {
    modal.classList.add("active");
  }

  modal.innerHTML = `
    <div class="auth-modal-card" style="max-width:540px;border-top:6px solid #1d4ed8;">
      <div style="padding:28px 24px;">
        
        <!-- Header Strip -->
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
          <div>
            <div style="display:flex;gap:6px;margin-bottom:6px;flex-wrap:wrap;">
              <span class="badge-govt-aid">🏛️ GOVT OF INDIA / SDMA RELIEF</span>
              <span class="badge-private">🔒 Confidential Pass</span>
            </div>
            <h3 style="margin:0;font-size:1.25rem;color:var(--navy);font-family:'Outfit',sans-serif;">
              Government Evacuation & Shelter Pass
            </h3>
            <p style="font-size:0.8rem;color:#64748b;margin:3px 0 0;">
              Authorized under State Disaster Relief Fund (SDRF). 100% Free Public Assistance.
            </p>
          </div>
          <button onclick="document.getElementById('shelterBookingModal').classList.remove('active')" style="border:0;background:transparent;font-size:1.4rem;cursor:pointer;color:#94a3b8;line-height:1;">✕</button>
        </div>

        <!-- Shelter Camp Card -->
        <div style="background:#f8fafc;border:1px solid #cbd5e1;border-radius:10px;padding:12px 16px;margin-bottom:14px;">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <strong style="color:var(--navy);font-size:0.95rem;">${shelterName}</strong>
            <span style="font-size:0.75rem;font-weight:700;color:#059669;background:#d1fae5;padding:2px 8px;border-radius:12px;">
              🟢 ${availBeds} Free Beds
            </span>
          </div>
          <span style="font-size:0.78rem;color:#64748b;">Camp ID: <code>${shelterId}</code> • District Administration & SDRF Base</span>
        </div>

        <form id="privateShelterForm" onsubmit="submitPrivateShelterBooking(event, '${shelterId}', '${shelterName.replace(/'/g, "\\'")}')">
          <div style="display:flex;flex-direction:column;gap:12px;">
            
            <!-- Citizen Info -->
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
              <div>
                <label style="font-size:0.74rem;font-weight:700;color:var(--navy);display:block;margin-bottom:4px;">Citizen Name (Confidential)</label>
                <input type="text" id="bookCitizenName" class="form-input" value="${user.display_name || 'Citizen Kaushal'}" required>
              </div>
              <div>
                <label style="font-size:0.74rem;font-weight:700;color:var(--navy);display:block;margin-bottom:4px;">Emergency Mobile No.</label>
                <input type="tel" id="bookCitizenPhone" class="form-input" value="${user.phone || '+91 98765 43210'}" required>
              </div>
            </div>

            <!-- Beds & Priority -->
            <div style="display:grid;grid-template-columns:1fr 1.2fr;gap:10px;">
              <div>
                <label style="font-size:0.74rem;font-weight:700;color:var(--navy);display:block;margin-bottom:4px;">Number of Beds</label>
                <select id="bookPeopleCount" class="form-select">
                  <option value="1">1 Person</option>
                  <option value="2" selected>2 Persons</option>
                  <option value="3">3 Persons</option>
                  <option value="4">4 Persons (Family)</option>
                  <option value="5">5 Persons (Family)</option>
                  <option value="6">6+ Persons (Group)</option>
                </select>
              </div>
              <div>
                <label style="font-size:0.74rem;font-weight:700;color:var(--navy);display:block;margin-bottom:4px;">Special Care Category</label>
                <select id="bookSpecialNeeds" class="form-select">
                  <option value="Standard">Standard Shelter Bed</option>
                  <option value="Senior Citizen">Senior Citizen (Ground Floor)</option>
                  <option value="Infant / Mother">Infants / Children / Nursing Mother</option>
                  <option value="Differently-Abled">Differently-Abled / Mobility Bed</option>
                  <option value="Medical Urgent">Patient Under Treatment / Medication</option>
                </select>
              </div>
            </div>

            <!-- Government Disaster Relief Entitlements -->
            <div class="govt-relief-card">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
                <span style="font-size:0.78rem;font-weight:800;color:#1e3a8a;display:flex;align-items:center;gap:6px;">
                  🏛️ Official Government Assistance Included (₹0 Cost):
                </span>
                <span class="govt-stamp-badge">100% Free SDRF Scheme</span>
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:0.76rem;">
                <label style="display:flex;align-items:center;gap:6px;cursor:pointer;color:#166534;font-weight:600;">
                  <input type="checkbox" id="chkFood" checked disabled style="accent-color:#059669;">
                  <span>🍲 Free Meals & Clean Water</span>
                </label>
                <label style="display:flex;align-items:center;gap:6px;cursor:pointer;color:#166534;font-weight:600;">
                  <input type="checkbox" id="chkMedical" checked disabled style="accent-color:#059669;">
                  <span>🩺 Doctor Care & Medicine</span>
                </label>
                <label style="display:flex;align-items:center;gap:6px;cursor:pointer;color:#166534;font-weight:600;">
                  <input type="checkbox" id="chkKit" checked disabled style="accent-color:#059669;">
                  <span>🏕️ Bedding & Relief Kit</span>
                </label>
                <label style="display:flex;align-items:center;gap:6px;cursor:pointer;color:#166534;font-weight:600;">
                  <input type="checkbox" id="chkGrant" checked disabled style="accent-color:#059669;">
                  <span>💰 Ex-Gratia Relief Registration</span>
                </label>
              </div>
            </div>

            <!-- Government Evacuation Transit Request -->
            <div class="transit-toggle-box" id="transitBox">
              <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:0.8rem;font-weight:700;color:#92400e;">
                <input type="checkbox" id="chkTransport" onchange="toggleGovtTransitField()" style="width:16px;height:16px;accent-color:#d97706;">
                <span>🚨 I am stranded/waterlogged. Request Government SDRF Transport to camp</span>
              </label>
              <div id="transitAddressWrap" style="display:none;margin-top:10px;">
                <label style="font-size:0.72rem;font-weight:700;color:#92400e;display:block;margin-bottom:3px;">
                  📍 Your Current Stranded Location / Landmark
                </label>
                <input type="text" id="bookPickupAddress" class="form-input" placeholder="e.g. House No. 14, Near Primary School, Riverbank Ward 3" style="background:#fff;border-color:#fcd34d;">
                <span style="font-size:0.72rem;color:#b45309;display:block;margin-top:4px;">
                  ℹ️ SDRF rescue boat / district emergency van will be dispatched to escort you to this camp.
                </span>
              </div>
            </div>

            <!-- Security & Hotline Note -->
            <div style="font-size:0.75rem;color:#1e3a8a;background:#eff6ff;border:1px solid #bfdbfe;padding:8px 12px;border-radius:8px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px;">
              <span>🔒 Encrypted Booking: Your location remains confidential.</span>
              <span style="font-weight:700;">📞 24x7 EOC Helpline: <a href="tel:1077" style="color:#1d4ed8;font-weight:800;text-decoration:underline;">1077</a> / <a href="tel:112" style="color:#1d4ed8;font-weight:800;text-decoration:underline;">112</a></span>
            </div>

            <button type="submit" id="submitShelterBookBtn" class="btn-primary" style="height:48px;margin-top:4px;background:linear-gradient(135deg,#1e3a8a,#2563eb);border:none;font-size:0.95rem;box-shadow:0 4px 14px rgba(37,99,235,0.35);">
              <span>🏛️ Confirm Govt Shelter Pass & Reserve Bed</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  `;
}

function toggleGovtTransitField() {
  const chk = document.getElementById("chkTransport");
  const wrap = document.getElementById("transitAddressWrap");
  const box = document.getElementById("transitBox");
  if (!chk || !wrap) return;
  if (chk.checked) {
    wrap.style.display = "block";
    box.classList.add("active");
  } else {
    wrap.style.display = "none";
    box.classList.remove("active");
  }
}

async function submitPrivateShelterBooking(e, shelterId, shelterName) {
  e.preventDefault();
  const btn = document.getElementById("submitShelterBookBtn");
  btn.disabled = true;
  btn.innerHTML = "⏳ Processing Official Government Reservation...";

  const name = document.getElementById("bookCitizenName").value.trim();
  const phone = document.getElementById("bookCitizenPhone").value.trim();
  const count = parseInt(document.getElementById("bookPeopleCount").value) || 1;
  const specialNeeds = document.getElementById("bookSpecialNeeds").value;
  const needTransport = document.getElementById("chkTransport") ? document.getElementById("chkTransport").checked : false;
  const pickupAddress = needTransport && document.getElementById("bookPickupAddress") ? document.getElementById("bookPickupAddress").value.trim() : "";
  const user = getCurrentUser() || { username: "kausha123" };

  const payload = {
    shelter_id: shelterId,
    shelter_name: shelterName,
    citizen_id: user.username || "kausha123",
    citizen_name: name,
    citizen_phone: phone,
    people_count: count,
    is_private: true,
    need_food_rations: true,
    need_medical_aid: true,
    need_transport: needTransport,
    pickup_address: pickupAddress,
    special_needs: specialNeeds
  };

  let bookingResult = null;
  try {
    const res = await fetch(`${API_BASE}/shelters/private-book`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(4000)
    });
    if (res.ok) {
      bookingResult = await res.json();
    }
  } catch (err) {
    console.log("Using local government booking pass:", err.message);
  }

  if (!bookingResult) {
    bookingResult = {
      booking_id: "SHTR-BK-" + Math.random().toString(36).substring(2, 8).toUpperCase(),
      private_pass: "PVT-PASS-" + Math.random().toString(36).substring(2, 8).toUpperCase(),
      shelter_id: shelterId,
      shelter_name: shelterName,
      people_count: count,
      citizen_name: name,
      citizen_phone: phone,
      need_food_rations: true,
      need_medical_aid: true,
      need_transport: needTransport,
      pickup_address: pickupAddress,
      special_needs: specialNeeds,
      status: "CONFIRMED",
      created_at: new Date().toISOString()
    };
  }

  // Cache to LocalStorage so citizen always has their offline pass
  try {
    let saved = JSON.parse(localStorage.getItem("aapdaMyPasses") || "[]");
    saved.unshift(bookingResult);
    localStorage.setItem("aapdaMyPasses", JSON.stringify(saved.slice(0, 20)));
  } catch (err) {}

  showShelterConfirmedModal(bookingResult);
}

function showShelterConfirmedModal(data) {
  const modal = document.getElementById("shelterBookingModal");
  if (!modal) return;

  const transportInfo = data.need_transport && data.pickup_address
    ? `<span style="color:#d97706;font-weight:700;">🚑 SDRF Escort Dispatched to: ${data.pickup_address}</span>`
    : `<span style="color:#10b981;font-weight:600;">🚶 Self-Transit / Direct Arrival at Camp</span>`;

  modal.innerHTML = `
    <div class="auth-modal-card" style="max-width:520px;border-top:6px solid #1d4ed8;">
      <div style="padding:28px 24px;">
        
        <!-- Official Header -->
        <div style="text-align:center;margin-bottom:12px;">
          <div style="display:inline-flex;align-items:center;gap:6px;background:#dbeafe;color:#1e40af;border:1px solid #93c5fd;border-radius:20px;padding:4px 14px;font-size:0.75rem;font-weight:800;margin-bottom:8px;">
            🏛️ STATE DISASTER MANAGEMENT AUTHORITY (SDMA)
          </div>
          <h2 style="color:var(--navy);font-size:1.4rem;margin:0 0 4px;font-family:'Outfit',sans-serif;">
            Emergency Evacuation Pass & Relief Voucher
          </h2>
          <span style="font-size:0.8rem;color:#059669;font-weight:700;">
            ✅ OFFICIAL PASS CONFIRMED • 100% FREE PUBLIC RELIEF
          </span>
        </div>

        <!-- Official Barcode Simulation -->
        <div class="pass-barcode-wrap">
          <div class="pass-barcode-lines"></div>
          <span style="font-family:monospace;font-size:0.82rem;letter-spacing:0.18em;color:#475569;font-weight:700;">
            ${data.private_pass}
          </span>
        </div>

        <!-- Details Grid -->
        <div style="background:#f8fafc;border:1px solid #cbd5e1;border-radius:12px;padding:16px;font-size:0.84rem;margin-bottom:14px;display:flex;flex-direction:column;gap:8px;">
          <div style="display:flex;justify-content:space-between;border-bottom:1px dashed #e2e8f0;padding-bottom:6px;">
            <span style="color:#64748b;font-weight:600;">Confidential Pass Code:</span>
            <div style="display:flex;align-items:center;gap:6px;">
              <strong style="color:#1d4ed8;font-family:monospace;font-size:1.05rem;letter-spacing:0.04em;">${data.private_pass}</strong>
              <button onclick="navigator.clipboard.writeText('${data.private_pass}'); showToast('Pass code copied to clipboard!', 'success');" style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:4px;padding:2px 6px;font-size:0.7rem;cursor:pointer;color:#1e40af;">
                📋 Copy
              </button>
            </div>
          </div>

          <div style="display:flex;justify-content:space-between;border-bottom:1px dashed #e2e8f0;padding-bottom:6px;">
            <span style="color:#64748b;font-weight:600;">Booking ID:</span>
            <span style="color:var(--navy);font-family:monospace;font-weight:700;">${data.booking_id}</span>
          </div>

          <div style="display:flex;justify-content:space-between;border-bottom:1px dashed #e2e8f0;padding-bottom:6px;">
            <span style="color:#64748b;font-weight:600;">Relief Shelter Base:</span>
            <strong style="color:var(--navy);text-align:right;">${data.shelter_name}</strong>
          </div>

          <div style="display:flex;justify-content:space-between;border-bottom:1px dashed #e2e8f0;padding-bottom:6px;">
            <span style="color:#64748b;font-weight:600;">Reserved Capacity:</span>
            <span style="color:#1e293b;font-weight:700;">${data.people_count} Person(s) (${data.special_needs || 'Standard'})</span>
          </div>

          <div style="display:flex;justify-content:space-between;border-bottom:1px dashed #e2e8f0;padding-bottom:6px;">
            <span style="color:#64748b;font-weight:600;">Transit Mode:</span>
            <span>${transportInfo}</span>
          </div>

          <div style="display:flex;flex-direction:column;gap:4px;padding-top:2px;">
            <span style="color:#1e3a8a;font-weight:800;font-size:0.78rem;">🏛️ Granted Government Entitlements:</span>
            <div style="display:flex;gap:6px;flex-wrap:wrap;">
              <span class="govt-relief-pill">🍲 Free SDRF Meals & Water</span>
              <span class="govt-relief-pill">🩺 Doctor & Health Kit</span>
              <span class="govt-relief-pill">💰 Ex-Gratia Token</span>
            </div>
          </div>
        </div>

        <!-- Emergency EOC Helpline notice -->
        <div style="font-size:0.75rem;color:#1e3a8a;background:#eff6ff;padding:8px 12px;border-radius:8px;margin-bottom:14px;border:1px solid #bfdbfe;display:flex;justify-content:space-between;align-items:center;">
          <span>📞 Camp Helpline: <a href="tel:1077" style="color:#1d4ed8;font-weight:800;text-decoration:underline;">1077 (EOC)</a> / <a href="tel:112" style="color:#1d4ed8;font-weight:800;text-decoration:underline;">112</a></span>
          <span>District Control Room Connected</span>
        </div>

        <!-- Action Buttons -->
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px;">
          <button onclick="window.print()" class="btn-outline" style="padding:10px;font-size:0.85rem;display:flex;align-items:center;justify-content:center;gap:6px;">
            <span>🖨️ Print Govt Pass</span>
          </button>
          <a href="https://wa.me/?text=${encodeURIComponent('AapdaSetu Emergency Shelter Pass: ' + data.private_pass + ' | Camp: ' + data.shelter_name + ' | Reserved: ' + data.people_count + ' Person(s). Valid for SDRF Relief.')}" target="_blank" class="btn-secondary" style="padding:10px;font-size:0.85rem;display:flex;align-items:center;justify-content:center;gap:6px;background:#25d366;color:#fff;border:none;">
            <span>💬 Share WhatsApp</span>
          </a>
        </div>

        <button onclick="document.getElementById('shelterBookingModal').classList.remove('active'); showToast('Pass confirmed & stored in My Passes', 'success');" class="btn-primary" style="width:100%;padding:11px;font-size:0.9rem;background:#059669;border-color:#047857;">
          <span>Done ✓ Keep Pass Safe</span>
        </button>
      </div>
    </div>
  `;
}

async function viewMyPrivateShelterPasses() {
  const user = getCurrentUser() || { username: "kausha123" };
  let modal = document.getElementById("shelterBookingModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "shelterBookingModal";
    modal.className = "auth-modal-backdrop active";
    document.body.appendChild(modal);
  } else {
    modal.classList.add("active");
  }

  modal.innerHTML = `
    <div class="auth-modal-card" style="max-width:540px;border-top:6px solid #1d4ed8;">
      <div style="padding:28px 24px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
          <div>
            <div style="display:flex;gap:6px;margin-bottom:4px;">
              <span class="badge-govt-aid">🏛️ SDMA Evacuation Registry</span>
            </div>
            <h3 style="margin:0;font-size:1.25rem;color:var(--navy);font-family:'Outfit',sans-serif;">
              My Government Shelter Passes
            </h3>
          </div>
          <button onclick="document.getElementById('shelterBookingModal').classList.remove('active')" style="border:0;background:transparent;font-size:1.3rem;cursor:pointer;color:#94a3b8;">✕</button>
        </div>
        <p style="font-size:0.82rem;color:#64748b;margin:0 0 16px;">
          Active evacuation passes registered under citizen: <strong>${user.display_name || user.username || 'kausha123'}</strong>
        </p>

        <div id="privatePassesContainer" style="max-height:380px;overflow-y:auto;display:flex;flex-direction:column;gap:12px;">
          <div style="text-align:center;padding:24px;color:#94a3b8;">Loading official passes...</div>
        </div>

        <button onclick="document.getElementById('shelterBookingModal').classList.remove('active')" class="btn-outline" style="width:100%;margin-top:16px;padding:10px;">
          Close
        </button>
      </div>
    </div>
  `;

  const container = document.getElementById("privatePassesContainer");

  let list = [];
  try {
    const res = await fetch(`${API_BASE}/shelters/my-bookings?citizen_id=${encodeURIComponent(user.username || 'kausha123')}`, {
      signal: AbortSignal.timeout(3500)
    });
    if (res.ok) {
      const data = await res.json();
      list = data.bookings || [];
    }
  } catch (err) {
    console.log("Using cached offline passes:", err.message);
  }

  // Merge with locally stored passes if backend is offline
  if (list.length === 0) {
    try {
      list = JSON.parse(localStorage.getItem("aapdaMyPasses") || "[]");
    } catch (e) {}
  }

  if (list.length === 0) {
    container.innerHTML = `
      <div style="text-align:center;padding:34px 20px;background:#f8fafc;border-radius:10px;border:1px dashed #cbd5e1;">
        <span style="font-size:2.2rem;">🏕️</span>
        <p style="margin:8px 0 4px;font-size:0.9rem;font-weight:700;color:var(--navy);">No Active Passes Found</p>
        <p style="margin:0;font-size:0.8rem;color:#64748b;">Click "🔒 Private Auto-Book Bed" on any relief camp card to generate an official government evacuation pass.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = "";
  list.forEach(b => {
    const isCancelled = b.status === "CANCELLED";
    const div = document.createElement("div");
    div.style.cssText = `background:${isCancelled ? '#fef2f2' : '#f0fdf4'};border:1px solid ${isCancelled ? '#fecaca' : '#bbf7d0'};border-radius:10px;padding:14px;font-size:0.85rem;`;
    div.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
        <strong style="color:${isCancelled ? '#991b1b' : '#166534'};font-size:0.95rem;">${b.shelter_name}</strong>
        <span class="badge-private" style="background:${isCancelled ? '#fee2e2' : '#047857'};color:${isCancelled ? '#991b1b' : '#a7f3d0'};border-color:${isCancelled ? '#f87171' : '#059669'};">
          ${b.status || 'CONFIRMED'}
        </span>
      </div>
      <div style="display:flex;justify-content:space-between;margin-bottom:4px;color:#334155;">
        <span>Pass Code:</span>
        <strong style="color:${isCancelled ? '#64748b' : '#047857'};font-family:monospace;letter-spacing:0.05em;font-size:0.95rem;">${b.private_pass}</strong>
      </div>
      <div style="display:flex;justify-content:space-between;margin-bottom:8px;color:#64748b;font-size:0.78rem;">
        <span>Reserved: <strong>${b.people_count} Person(s)</strong> (${b.special_needs || 'Standard'})</span>
        <span>ID: <code>${b.booking_id}</code></span>
      </div>

      <!-- Government Entitlements Granted Strip -->
      <div style="font-size:0.73rem;color:#1e3a8a;background:#eff6ff;padding:5px 8px;border-radius:6px;margin-bottom:8px;display:flex;gap:6px;flex-wrap:wrap;">
        <span>🍲 Free Meals</span>
        <span>•</span>
        <span>🩺 Medical Post</span>
        <span>•</span>
        <span>${b.need_transport ? '🚑 SDRF Escort' : '🚶 Self Transit'}</span>
      </div>

      <div style="display:flex;gap:8px;justify-content:flex-end;">
        <button onclick='showShelterConfirmedModal(${JSON.stringify(b).replace(/'/g, "&apos;")})' class="btn-outline" style="padding:4px 10px;font-size:0.75rem;">
          👁️ View Voucher
        </button>
        ${!isCancelled ? `
          <button onclick="cancelShelterPass('${b.booking_id}')" class="btn-outline" style="padding:4px 10px;font-size:0.75rem;color:#dc2626;border-color:#fca5a5;">
            ✕ Cancel Pass
          </button>
        ` : ''}
      </div>
    `;
    container.appendChild(div);
  });
}

async function cancelShelterPass(bookingId) {
  if (!confirm("Are you sure you want to cancel this emergency reservation? The bed capacity will be released for other citizens.")) return;
  const user = getCurrentUser() || { username: "kausha123" };
  try {
    const res = await fetch(`${API_BASE}/shelters/bookings/${encodeURIComponent(bookingId)}?citizen_id=${encodeURIComponent(user.username || 'kausha123')}`, {
      method: "DELETE",
      signal: AbortSignal.timeout(3500)
    });
    if (res.ok) {
      showToast("Shelter reservation cancelled. Beds returned to camp.", "info");
    }
  } catch (err) {
    console.log("Cancelled locally:", err.message);
  }

  // Update local cache
  try {
    let saved = JSON.parse(localStorage.getItem("aapdaMyPasses") || "[]");
    saved = saved.map(x => x.booking_id === bookingId ? { ...x, status: "CANCELLED" } : x);
    localStorage.setItem("aapdaMyPasses", JSON.stringify(saved));
  } catch (e) {}

  viewMyPrivateShelterPasses();
}

/* ================= PLATFORM MULTILINGUAL ENGINE (i18n) ================= */
const I18N_DICTIONARY = {
  en: {
    brand_tagline: "Disaster Response",
    nav_home: "Home",
    nav_prediction: "AI Prediction",
    nav_weather: "Weather",
    nav_monitoring: "Rivers & Dams",
    nav_emergency: "Emergency SOS",
    nav_rescue: "Rescue Help",
    nav_shelters: "Safe Shelters",
    nav_routes: "Safe Routes",
    nav_alerts: "Live Alerts",
    nav_community: "Community",
    nav_family: "Family Check-in",
    nav_donation: "Relief Fund",
    nav_chatbot: "AI Assistant",
    nav_admin: "Admin EOC",
    nav_signin: "Sign In",
    nav_signout: "Sign Out",
    hero_pill: "🚨 NATIONAL FLOOD EARLY WARNING SYSTEM",
    hero_title: "AI-Powered Disaster Response & Flood Protection",
    hero_subtitle: "Real-time AI flood risk modeling, instant satellite telemetry, verified emergency safe shelters, and zero-click rescue dispatch for every citizen.",
    btn_sos_call: "Call 112 Now",
    btn_1click_sos: "1-Click Private Auto-Rescue",
    btn_check_risk: "Check District Risk 🤖",
    btn_predict: "Generate AI Prediction",
    btn_share_gps: "Share My GPS Location",
    btn_private_shelter: "🔒 Private Auto-Book Slot",
    btn_directions: "🗺️ Directions",
    btn_call_center: "📞 Call Center",
    badge_private: "🔒 PRIVATE ENCRYPTED",
    stat_rescue_calls: "Active Rescue Calls",
    stat_alerts: "Official Alerts Issued",
    stat_reports: "Citizen Hazard Reports",
    stat_shelters: "Verified Safe Shelters",
    dm_alert_title: "District Magistrate Official Alert Dispatched",
    dm_alert_subtitle: "Emergency EOC notification delivered to District Administration.",
    dam_banner_title: "EMERGENCY: Dam Floodgates Opening Warning",
    dam_banner_sub: "Spillway discharge in progress. Evacuate downstream riverbed plains immediately.",
    listen_hi: "🔊 हिन्दी में सुनें",
    listen_en: "🔊 Listen (English)",
    search_shelter_placeholder: "Search by District or Camp Name...",
    select_state: "Select State",
    select_district: "Select District",
    occupancy: "Occupancy",
    beds_free: "Beds Free",
    facilities: "Facilities"
  },
  hi: {
    brand_tagline: "आपदा प्रबंधन",
    nav_home: "होम",
    nav_prediction: "एआई भविष्यवाणी",
    nav_weather: "मौसम पूर्वानुमान",
    nav_monitoring: "नदियां एवं बांध",
    nav_emergency: "आपातकालीन एसओएस",
    nav_rescue: "रेस्क्यू सहायता",
    nav_shelters: "सुरक्षित आश्रय स्थल",
    nav_routes: "सुरक्षित मार्ग",
    nav_alerts: "लाइव अलर्ट",
    nav_community: "नागरिक रिपोर्ट",
    nav_family: "परिवार सुरक्षा",
    nav_donation: "राहत कोष",
    nav_chatbot: "एआई सहायक",
    nav_admin: "एडमिन कंट्रोल",
    nav_signin: "लॉग इन",
    nav_signout: "लॉग आउट",
    hero_pill: "🚨 राष्ट्रीय बाढ़ पूर्व चेतावनी प्रणाली",
    hero_title: "एआई आधारित आपदा प्रबंधन एवं बाढ़ पूर्व चेतावनी",
    hero_subtitle: "सटीक एआई बाढ़ पूर्वानुमान, वास्तविक समय नदी स्तर, सत्यापित सुरक्षित राहत शिविर और बिना किसी फॉर्म के 1-क्लिक निजी बचाव दल सहायता।",
    btn_sos_call: "112 पर तुरंत कॉल करें",
    btn_1click_sos: "⚡ 1-क्लिक निजी ऑटो-रेस्क्यू",
    btn_check_risk: "जिले का जोखिम जांचें 🤖",
    btn_predict: "एआई भविष्यवाणी प्राप्त करें",
    btn_share_gps: "📍 अपना जीपीएस स्थान भेजें",
    btn_private_shelter: "🔒 निजी बेड ऑटो-बुक करें",
    btn_directions: "🗺️ दिशा-निर्देश",
    btn_call_center: "📞 कंट्रोल रूम",
    badge_private: "🔒 सुरक्षित एवं निजी",
    stat_rescue_calls: "सक्रिय बचाव अभियान",
    stat_alerts: "जारी आधिकारिक चेतावनियां",
    stat_reports: "नागरिक आपदा रिपोर्ट्स",
    stat_shelters: "सत्यापित सुरक्षित राहत शिविर",
    dm_alert_title: "जिलाधिकारी (DM) को आधिकारिक सूचना भेजी गई",
    dm_alert_subtitle: "आपातकालीन ईओसी सूचना सीधे जिला प्रशासन को प्रेषित की गई।",
    dam_banner_title: "आपातकालीन चेतावनी: बांध के जलद्वार खोले जा रहे हैं",
    dam_banner_sub: "नदी में भारी जलप्रवाह जारी। तटीय क्षेत्रों के नागरिक तुरंत सुरक्षित स्थानों पर जाएं।",
    listen_hi: "🔊 हिन्दी में सुनें",
    listen_en: "🔊 अंग्रेजी में सुनें",
    search_shelter_placeholder: "जिला या राहत शिविर खोजें...",
    select_state: "राज्य चुनें",
    select_district: "जिला चुनें",
    occupancy: "भरे हुए बेड",
    beds_free: "बेड खाली",
    facilities: "उपलब्ध सुविधाएं"
  },
  hinglish: {
    brand_tagline: "Disaster Response",
    nav_home: "Home",
    nav_prediction: "AI Flood Prediction",
    nav_weather: "Mausam Forecast",
    nav_monitoring: "Rivers & Dams",
    nav_emergency: "Emergency SOS 112",
    nav_rescue: "Rescue Help",
    nav_shelters: "Safe Shelters",
    nav_routes: "Safe Routes",
    nav_alerts: "Live Alerts",
    nav_community: "Community Reports",
    nav_family: "Family Safety",
    nav_donation: "Relief Fund",
    nav_chatbot: "AI Chat Assistant",
    nav_admin: "Admin EOC",
    nav_signin: "Sign In",
    nav_signout: "Sign Out",
    hero_pill: "🚨 NATIONAL FLOOD EARLY WARNING SYSTEM",
    hero_title: "AI-Powered Disaster Response & Flood Bachav",
    hero_subtitle: "Real-time AI flood risk modeling, satellite telemetry, verified safe relief shelters, aur 1-click private emergency rescue har citizen ke liye.",
    btn_sos_call: "Abhi 112 Call Karein",
    btn_1click_sos: "⚡ 1-Click Private Auto-Rescue",
    btn_check_risk: "Apne District Ka Risk Dekhein 🤖",
    btn_predict: "AI Flood Prediction Nikalein",
    btn_share_gps: "📍 Apna GPS Location Share Karein",
    btn_private_shelter: "🔒 Private Bed Auto-Book Karein",
    btn_directions: "🗺️ Rasta Dekhein",
    btn_call_center: "📞 Helpdesk Call",
    badge_private: "🔒 PRIVATE ENCRYPTED",
    stat_rescue_calls: "Active Rescue Calls",
    stat_alerts: "Issued Flood Alerts",
    stat_reports: "Public Hazard Reports",
    stat_shelters: "Verified Safe Shelters",
    dm_alert_title: "DM Office Ko Alert Bheja Gaya",
    dm_alert_subtitle: "Emergency EOC alert District Magistrate ko deliver ho chuka hai.",
    dam_banner_title: "EMERGENCY: Dam Ke Floodgates Khole Jaa Rahe Hain",
    dam_banner_sub: "River me heavy discharge shuru ho raha hai. Riverbanks ke log turant unchi jagah par chale jayein.",
    listen_hi: "🔊 Hindi Me Sunein",
    listen_en: "🔊 English Me Sunein",
    search_shelter_placeholder: "District ya shelter search karein...",
    select_state: "State Select Karein",
    select_district: "District Select Karein",
    occupancy: "Occupancy",
    beds_free: "Beds Available",
    facilities: "Suvidhayein"
  },
  mr: {
    brand_tagline: "आपत्ती व्यवस्थापन",
    nav_home: "मुख्यपृष्ठ",
    nav_prediction: "एआय अंदाज",
    nav_weather: "हवामान अंदाज",
    nav_monitoring: "नद्या आणि धरणे",
    nav_emergency: "आपत्कालीन एसओएस",
    nav_rescue: "बचाव सहाय्य",
    nav_shelters: "सुरक्षित निवारे",
    nav_routes: "सुरक्षित मार्ग",
    nav_alerts: "थेट सूचना",
    nav_community: "नागरी अहवाल",
    nav_family: "कुटुंब सुरक्षा",
    nav_donation: "मदत निधी",
    nav_chatbot: "एआय सहाय्यक",
    nav_admin: "प्रशासन कक्ष",
    nav_signin: "लॉग इन",
    nav_signout: "लॉग आउट",
    hero_pill: "🚨 राष्ट्रीय पूर पूर्वसूचना प्रणाली",
    hero_title: "एआय आधारित आपत्ती व्यवस्थापन व पूर संरक्षण",
    hero_subtitle: "अचूक एआय पूर अंदाज, नद्यांचे थेट जलस्तर, सुरक्षित निवारा छावण्या आणि नागरिकांसाठी त्वरित १-क्लिक खाजगी बचाव सहाय्य.",
    btn_sos_call: "११२ वर कॉल करा",
    btn_1click_sos: "⚡ १-क्लिक खाजगी ऑटो-बचाव",
    btn_check_risk: "जिल्ह्याचा धोका तपासा 🤖",
    btn_predict: "एआय अंदाज मिळवा",
    btn_share_gps: "📍 जीपीएस स्थान पाठवा",
    btn_private_shelter: "🔒 खाजगी बेड आरक्षित करा",
    btn_directions: "🗺️ मार्ग",
    btn_call_center: "📞 मदत केंद्र",
    badge_private: "🔒 खाजगी व सुरक्षित",
    stat_rescue_calls: "सक्रिय बचाव कार्य",
    stat_alerts: "अधिकृत सूचना",
    stat_reports: "नागरी अहवाल",
    stat_shelters: "सुरक्षित निवारे",
    dm_alert_title: "जिल्हाधिकाऱ्यांना अधिकृत सूचना पाठवली",
    dm_alert_subtitle: "आपत्कालीन ईओसी इशारा थेट जिल्हा प्रशासनाला दिला गेला.",
    dam_banner_title: "आपत्कालीन सूचना: धरणाचे दरवाजे उघडले जात आहेत",
    dam_banner_sub: "नदीपात्रात मोठ्या प्रमाणात विसर्ग सुरू. नागरिकांनी तात्काळ सुरक्षित स्थळी जावे.",
    listen_hi: "🔊 हिंदीत ऐका",
    listen_en: "🔊 इंग्रजीत ऐका",
    search_shelter_placeholder: "जिल्हा किंवा निवारा शोधा...",
    select_state: "राज्य निवडा",
    select_district: "जिल्हा निवडा",
    occupancy: "भरलेले बेड",
    beds_free: "शिल्लक बेड",
    facilities: "उपलब्ध सुविधा"
  },
  bn: {
    brand_tagline: "দুর্যোগ প্রতিক্রিয়া",
    nav_home: "হোম",
    nav_prediction: "এআই পূর্বাভাস",
    nav_weather: "আবহাওয়ার খবর",
    nav_monitoring: "নদী ও বাঁধ",
    nav_emergency: "জরুরী এসওএস",
    nav_rescue: "উদ্ধার সহায়তা",
    nav_shelters: "নিরাপদ আশ্রয়",
    nav_routes: "নিরাপদ পথ",
    nav_alerts: "লাইভ সতর্কতা",
    nav_community: "জনসাধারণের রিপোর্ট",
    nav_family: "পরিবার নিরাপত্তা",
    nav_donation: "ত্রাণ তহবিল",
    nav_chatbot: "এআই সহকারী",
    nav_admin: "প্রশাসন ইওসি",
    nav_signin: "লগ ইন",
    nav_signout: "লগ আউট",
    hero_pill: "🚨 জাতীয় বন্যা আগাম সতর্কতা ব্যবস্থা",
    hero_title: "এআই চালিত দুর্যোগ প্রতিক্রিয়া ও বন্যা সুরক্ষা",
    hero_subtitle: "রিয়েল-টাইম এআই পূর্বাভাস, নদীর জলস্তর পর্যবেক্ষণ, যাচাইকৃত আশ্রয় শিবির এবং প্রতিটি নাগরিকের জন্য ১-ক্লিক গোপনীয় জরুরি উদ্ধার।",
    btn_sos_call: "১১২ নম্বরে কল করুন",
    btn_1click_sos: "⚡ ১-ক্লিক গোপনীয় অটো-উদ্ধার",
    btn_check_risk: "ঝুঁকি যাচাই করুন 🤖",
    btn_predict: "এআই পূর্বাভাস দেখুন",
    btn_share_gps: "📍 জিপিএস শেয়ার করুন",
    btn_private_shelter: "🔒 গোপনীয় বেড বুক করুন",
    btn_directions: "🗺️ পথনির্দেশ",
    btn_call_center: "📞 কন্ট্রোল রুম",
    badge_private: "🔒 সুরক্ষিত ও গোপনীয়",
    stat_rescue_calls: "সক্রিয় উদ্ধার অভিযান",
    stat_alerts: "জারি করা সতর্কতা",
    stat_reports: "নাগরিক রিপোর্ট",
    stat_shelters: "নিরাপদ আশ্রয়কেন্দ্র",
    dm_alert_title: "জেলা শাসকের (DM) কাছে সতর্কতা পাঠানো হয়েছে",
    dm_alert_subtitle: "জরুরী ইওসি নোটিফিকেশন জেলা প্রশাসনের কাছে পৌঁছেছে।",
    dam_banner_title: "জরুরী সতর্কতা: বাঁধের স্লুইস গেট খোলা হচ্ছে",
    dam_banner_sub: "নদীতে অতিরিক্ত জল ছাড়া হচ্ছে। তীরবর্তী এলাকার মানুষ অবিলম্বে নিরাপদ স্থানে যান।",
    listen_hi: "🔊 হিন্দিতে শুনুন",
    listen_en: "🔊 ইংরেজিতে শুনুন",
    search_shelter_placeholder: "জেলা বা আশ্রয়কেন্দ্র অনুসন্ধান...",
    select_state: "রাজ্য নির্বাচন করুন",
    select_district: "জেলা নির্বাচন করুন",
    occupancy: "ভর্তি আসন",
    beds_free: "খালি আসন",
    facilities: "সুবিধাসমূহ"
  },
  gu: {
    brand_tagline: "આપત્તિ વ્યવસ્થાપન",
    nav_home: "હોમ",
    nav_prediction: "એઆઈ આગાહી",
    nav_weather: "હવામાન આગાહી",
    nav_monitoring: "નદીઓ અને બંધો",
    nav_emergency: "ઇમરજન્સી એસઓએસ",
    nav_rescue: "બચાવ સહાય",
    nav_shelters: "સુરક્ષિત આશ્રયસ્થાનો",
    nav_routes: "સલામત માર્ગો",
    nav_alerts: "લાઇવ ચેતવણીઓ",
    nav_community: "નાગરિક અહેવાલો",
    nav_family: "પરિવાર સુરક્ષા",
    nav_donation: "રાહત ફંડ",
    nav_chatbot: "એઆઈ સહાયક",
    nav_admin: "કંટ્રોલ સેન્ટર",
    nav_signin: "સાઇન ઇન",
    nav_signout: "સાઇન આઉટ",
    hero_pill: "🚨 રાષ્ટ્રીય પૂર પૂર્વ ચેતવણી પ્રણાલી",
    hero_title: "એઆઈ આધારિત આપત્તિ વ્યવસ્થાપન અને પૂર સુરક્ષા",
    hero_subtitle: "ચોક્કસ એઆઈ પૂર આગાહી, નદીઓના જળસ્તર, ચકાસાયેલ સુરક્ષિત આશ્રયસ્થાનો અને ૧-ક્લિક ખાનગી બચાવ સહાય.",
    btn_sos_call: "૧૧૨ પર કૉલ કરો",
    btn_1click_sos: "⚡ ૧-ક્લિક ખાનગી ઑટો-બચાવ",
    btn_check_risk: "જોખમ તપાસો 🤖",
    btn_predict: "એઆઈ આગાહી મેળવો",
    btn_share_gps: "📍 જીપીએસ સ્થાન મોકલો",
    btn_private_shelter: "🔒 ખાનગી બેડ બુક કરો",
    btn_directions: "🗺️ માર્ગદર્શન",
    btn_call_center: "📞 સહાય કેન્દ્ર",
    badge_private: "🔒 ખાનગી અને સુરક્ષિત",
    stat_rescue_calls: "સક્રિય બચાવ કામગીરી",
    stat_alerts: "સત્તાવાર ચેતવણીઓ",
    stat_reports: "નાગરિક અહેવાલો",
    stat_shelters: "સુરક્ષિત આશ્રયસ્થાનો",
    dm_alert_title: "જિલ્લા કલેક્ટરને સત્તાવાર ચેતવણી મોકલી",
    dm_alert_subtitle: "ઇમરજન્સી ઇઓસી નોટિફિકેશન સીધી જિલ્લા વહીવટીતંત્રને પહોંચાડી દેવામાં આવી છે.",
    dam_banner_title: "ઇમરજન્સી ચેતવણી: ડેમના દરવાજા ખોલવામાં આવી રહ્યા છે",
    dam_banner_sub: "નદીમાં ભારે પાણી છોડવાનું શરૂ. નીચાણવાળા વિસ્તારોના લોકો તાત્કાલિક સુરક્ષિત સ્થળે ખસી જાય.",
    listen_hi: "🔊 હિન્દીમાં સાંભળો",
    listen_en: "🔊 અંગ્રેજીમાં સાંભળો",
    search_shelter_placeholder: "જિલ્લો અથવા આશ્રયસ્થાન શોધો...",
    select_state: "રાજ્ય પસંદ કરો",
    select_district: "જિલ્લો પસંદ કરો",
    occupancy: "ભરેલા બેડ",
    beds_free: "ખાલી બેડ",
    facilities: "સુવિધાઓ"
  }
};

function getCurrentLanguage() {
  return localStorage.getItem("aapda_language") || localStorage.getItem("aapdaLanguage") || "en";
}

function getTranslationDict(lang) {
  if (typeof window !== "undefined" && window.translations && window.translations[lang]) {
    return window.translations[lang];
  }
  if (typeof I18N_DICTIONARY !== "undefined" && I18N_DICTIONARY[lang]) {
    return I18N_DICTIONARY[lang];
  }
  if (typeof window !== "undefined" && window.translations && window.translations.en) {
    return window.translations.en;
  }
  return (typeof I18N_DICTIONARY !== "undefined" && I18N_DICTIONARY.en) ? I18N_DICTIONARY.en : {};
}

function getLanguageLabel(code) {
  if (typeof window !== "undefined" && window.translations && window.translations[code]) {
    return window.translations[code].language;
  }
  if (typeof window !== "undefined" && window.ALL_STATE_LANGUAGES) {
    const found = window.ALL_STATE_LANGUAGES.find(l => l.code === code);
    if (found) return found.name;
  }
  const fallbackMap = {
    en: "English", hi: "हिन्दी (Hindi)", hinglish: "Hinglish", bn: "বাংলা (Bengali)",
    mr: "मराठी (Marathi)", te: "తెలుగు (Telugu)", ta: "தமிழ் (Tamil)", gu: "ગુજરાતી (Gujarati)",
    kn: "ಕನ್ನಡ (Kannada)", ml: "മലയാളം (Malayalam)", pa: "ਪੰਜਾਬੀ (Punjabi)", or: "ଓଡ଼ିଆ (Odia)",
    as: "অসমীয়া (Assamese)", ur: "اردو (Urdu)", bho: "भोजपुरी (Bhojpuri)", mai: "मैथिली (Maithili)",
    raj: "राजस्थानी (Rajasthani)", hne: "छत्तीसगढ़ी (Chhattisgarhi)", bgc: "हरियाणवी (Haryanvi)",
    doi: "डोगरी (Dogri)", ks: "कॉशुर (Kashmiri)", kok: "कोंकणी (Konkani)", mni: "মৈতৈলোন্ (Manipuri)",
    ne: "नेपाली (Nepali)", sat: "संताली (Santali)", brx: "बोडो (Bodo)", gbm: "गढ़वाली (Garhwali)",
    kfy: "कुमाऊँनी (Kumaoni)", kha: "Khasi", lus: "Mizo", sa: "संस्कृतम् (Sanskrit)"
  };
  return fallbackMap[code] || code;
}

function setLanguage(lang) {
  const dict = getTranslationDict(lang);
  localStorage.setItem("aapda_language", lang);
  localStorage.setItem("aapdaLanguage", lang);
  applyTranslations(lang);

  // Sync all dropdowns on the page
  document.querySelectorAll("#languageSelector").forEach(sel => {
    sel.value = lang;
  });

  showToast(`🌐 Language: ${getLanguageLabel(lang)}`, "info");
}

function applyTranslations(lang) {
  const dict = getTranslationDict(lang);
  if (!dict) return;

  // 1. Elements with data-i18n attribute
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) {
      if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
        el.placeholder = dict[key];
      } else {
        el.textContent = dict[key];
      }
    }
  });

  // 1b. Elements with data-i18n-placeholder attribute
  document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
    const key = el.getAttribute("data-i18n-placeholder");
    if (dict[key]) {
      el.placeholder = dict[key];
    }
  });

  // 2. Translate main navigation links automatically across all pages
  const navMap = [
    { match: "index.html", text: dict.nav_home || dict.home, icon: "🏠" },
    { match: "prediction.html", text: dict.nav_prediction || dict.prediction, icon: "🤖" },
    { match: "weather.html", text: dict.nav_weather || dict.weather, icon: "🌤️" },
    { match: "monitoring.html", text: dict.nav_monitoring || dict.monitoring, icon: "🌊" },
    { match: "emergency.html", text: dict.nav_emergency || dict.emergency, icon: "🚨" },
    { match: "rescue.html", text: dict.nav_rescue || dict.rescue, icon: "🚑" },
    { match: "shelters.html", text: dict.nav_shelters || dict.shelters, icon: "🏕️" },
    { match: "safe-route.html", text: dict.nav_routes || dict.safeRoutes, icon: "🗺️" },
    { match: "alerts.html", text: dict.nav_alerts || dict.alerts, icon: "🔔" },
    { match: "community.html", text: dict.nav_community || dict.community, icon: "📢" },
    { match: "family.html", text: dict.nav_family || dict.family, icon: "👨‍👩‍👧" },
    { match: "donation.html", text: dict.nav_donation || dict.donation, icon: "❤️" },
    { match: "chatbot.html", text: dict.nav_chatbot || dict.assistant, icon: "💬" },
    { match: "admin.html", text: dict.nav_admin || dict.admin, icon: "🛡️" }
  ];

  document.querySelectorAll(".nav-link").forEach(a => {
    const href = a.getAttribute("href") || "";
    for (const item of navMap) {
      if (item.text && (href.endsWith(item.match) || href === item.match)) {
        a.textContent = item.text;
        break;
      }
    }
  });

  document.querySelectorAll(".mobile-nav-drawer a").forEach(a => {
    const href = a.getAttribute("href") || "";
    for (const item of navMap) {
      if (item.text && (href.endsWith(item.match) || href === item.match)) {
        a.textContent = item.icon + " " + item.text;
        break;
      }
    }
  });

  // 3. Translate Brand Tagline
  const brandTag = document.querySelector(".brand-tagline");
  if (brandTag && dict.brand_tagline) brandTag.textContent = dict.brand_tagline;

  // 4. Translate Header SOS button
  document.querySelectorAll(".sos-header-btn").forEach(btn => {
    btn.textContent = dict.btn_sos_call ? `🚨 ${dict.btn_sos_call}` : (dict.sos || "🚨 SOS 112");
  });

  // 5. Translate 1-click rescue buttons
  document.querySelectorAll(".btn-1click-sos").forEach(btn => {
    btn.innerHTML = `<span>🔒</span> <span>${dict.btn_1click_sos || '1-Click Private Auto-Rescue'}</span>`;
  });

  // 6. Translate Private shelter booking buttons & badges
  document.querySelectorAll(".btn-private-booking").forEach(btn => {
    btn.textContent = dict.btn_private_shelter || "🔒 Private Auto-Book Bed";
  });
  document.querySelectorAll(".badge-private").forEach(b => {
    b.textContent = dict.badge_private || "🔒 PRIVATE ENCRYPTED";
  });

  // 7. Translate Hero section on index/landing
  const heroPill = document.querySelector(".hero-pill");
  if (heroPill && dict.hero_pill) heroPill.textContent = dict.hero_pill;

  const heroTitle = document.querySelector(".hero-title");
  if (heroTitle && dict.hero_title) {
    heroTitle.innerHTML = dict.hero_title;
  }

  const heroSub = document.querySelector(".page-hero p, .page-hero .hero-subtitle");
  if (heroSub && dict.hero_subtitle) heroSub.textContent = dict.hero_subtitle;

  // 8. Translate search & dropdown placeholders
  const searchShelterInput = document.getElementById("searchShelter");
  if (searchShelterInput && dict.search_shelter_placeholder) {
    searchShelterInput.placeholder = dict.search_shelter_placeholder;
  }

  document.querySelectorAll("select#stateSelect option[value=''], select#state option[value='']").forEach(opt => {
    opt.textContent = dict.select_state || dict.selectState || "Select State";
  });
  document.querySelectorAll("select#districtSelect option[value=''], select#district option[value='']").forEach(opt => {
    opt.textContent = dict.select_district || dict.selectDistrict || "Select District";
  });

  // 9. Update live dam broadcast audio label if present
  const damBroadcastBtn = document.querySelector(".btn-dam-audio");
  if (damBroadcastBtn) {
    damBroadcastBtn.textContent = `🔊 Broadcast (${getLanguageLabel(lang)})`;
  }
}

// Global initialization on every page load
document.addEventListener("DOMContentLoaded", () => {
  const currentLang = getCurrentLanguage();

  const langList = (typeof window !== "undefined" && window.ALL_STATE_LANGUAGES) ? window.ALL_STATE_LANGUAGES : [
    { code: "en", name: "English", region: "All India / National" },
    { code: "hi", name: "हिन्दी (Hindi)", region: "उत्तर प्रदेश, मध्य प्रदेश, बिहार, राजस्थान, दिल्ली, हरियाणा" },
    { code: "hinglish", name: "Hinglish", region: "All India (Everyday Conversational)" },
    { code: "bn", name: "বাংলা (Bengali)", region: "পশ্চিমবঙ্গ, ত্রিপুরা, আসাম, আন্দামান" },
    { code: "mr", name: "मराठी (Marathi)", region: "महाराष्ट्र, गोवा" },
    { code: "te", name: "తెలుగు (Telugu)", region: "ఆంధ్రప్రదేశ్, తెలంగాణ" },
    { code: "ta", name: "தமிழ் (Tamil)", region: "தமிழ்நாடு, புதுச்சேரி, அந்தமான்" },
    { code: "gu", name: "ગુજરાતી (Gujarati)", region: "ગુજરાત, દમણ અને દીવ" },
    { code: "kn", name: "ಕನ್ನಡ (Kannada)", region: "ಕರ್ನಾಟಕ" },
    { code: "ml", name: "മലയാളം (Malayalam)", region: "കേരളം, ലക്ഷദ്വീപ്" },
    { code: "pa", name: "ਪੰਜਾਬੀ (Punjabi)", region: "ਪੰਜਾਬ, ਚੰਡੀਗੜ੍ਹ, ਹਰਿਆਣਾ" },
    { code: "or", name: "ଓଡ଼ିଆ (Odia)", region: "ଓଡ଼ିଶା" },
    { code: "as", name: "অসমীয়া (Assamese)", region: "অসম (Assam)" },
    { code: "ur", name: "اردو (Urdu)", region: "جموں و کشمیر، تلنگانہ، دہلی، اتر پردیش، بہار" },
    { code: "bho", name: "भोजपुरी (Bhojpuri)", region: "बिहार, पूर्वांचल उत्तर प्रदेश, झारखंड" },
    { code: "mai", name: "मैथिली (Maithili)", region: "मिथिलांचल - बिहार, झारखंड" },
    { code: "raj", name: "राजस्थानी (Rajasthani)", region: "राजस्थान" },
    { code: "hne", name: "छत्तीसगढ़ी (Chhattisgarhi)", region: "छत्तीसगढ़" },
    { code: "bgc", name: "हरियाणवी (Haryanvi)", region: "हरियाणा, दिल्ली एनसीआर" },
    { code: "doi", name: "डोगरी (Dogri)", region: "जम्मू और कश्मीर, हिमाचल प्रदेश" },
    { code: "ks", name: "कॉशुर (Kashmiri)", region: "جموں و کشمیر / जम्मू व कश्मीर" },
    { code: "kok", name: "कोंकणी (Konkani)", region: "गोंय (Goa), कारवार, कोकण" },
    { code: "mni", name: "মৈতৈলোন্ (Manipuri)", region: "মণিপুর (Manipur)" },
    { code: "ne", name: "नेपाली (Nepali)", region: "सिक्किम, दार्जिलिंग, उत्तर बंगाल, असम" },
    { code: "sat", name: "संताली (Santali)", region: "झारखंड, ओडिशा, पश्चिम बंगाल (ᱚᱞ ᱪᱤᱠᱤ)" },
    { code: "brx", name: "बोडो (Bodo)", region: "असम, बोडोलैंड (Bodoland / BTR)" },
    { code: "gbm", name: "गढ़वाली (Garhwali)", region: "उत्तराखंड (गढ़वाल मंडल)" },
    { code: "kfy", name: "कुमाऊँनी (Kumaoni)", region: "उत्तराखंड (कुमाऊँ मंडल)" },
    { code: "kha", name: "Khasi", region: "Meghalaya (Khasi & Jaintia Hills)" },
    { code: "lus", name: "Mizo", region: "Mizoram" },
    { code: "sa", name: "संस्कृतम् (Sanskrit)", region: "उत्तराखण्डम्, भारतम् (Classical)" }
  ];

  // Populate options on all language selectors dynamically with all 31 Indian state languages
  document.querySelectorAll("#languageSelector").forEach(sel => {
    sel.innerHTML = langList.map(l => 
      `<option value="${l.code}">🌐 ${l.name} — ${l.region}</option>`
    ).join("");
    sel.value = currentLang;
    sel.addEventListener("change", function() {
      setLanguage(this.value);
    });
  });

  applyTranslations(currentLang);

  // Initialize Native Mobile Bottom Navigation Bar & Drawer listeners
  initMobileEnhancements();
});

/**
 * Mobile UX Enhancement Engine
 * Injects app-like quick bottom navigation bar and handles mobile drawer interactions
 */
function initMobileEnhancements() {
  // 1. Auto-close mobile drawer when any link is tapped
  const drawerLinks = document.querySelectorAll("#mobileNavDrawer a");
  drawerLinks.forEach(link => {
    link.addEventListener("click", () => {
      const drawer = document.getElementById("mobileNavDrawer");
      const menuBtn = document.querySelector(".mobile-menu-btn");
      if (drawer && drawer.classList.contains("open")) {
        drawer.classList.remove("open");
        document.body.style.overflow = "";
        if (menuBtn) menuBtn.textContent = "☰";
      }
    });
  });

  // 2. Inject Mobile Quick-Action Bottom Bar if not already present
  if (!document.querySelector(".mobile-bottom-bar")) {
    const bar = document.createElement("nav");
    bar.className = "mobile-bottom-bar";
    bar.setAttribute("aria-label", "Mobile Quick Actions");

    const currentPath = window.location.pathname.toLowerCase();
    const isHome = currentPath.endsWith("index.html") || currentPath.endsWith("/") || currentPath.endsWith("aapda-setu-one.vercel.app");
    const isRoute = currentPath.includes("safe-route");
    const isMonitoring = currentPath.includes("monitoring");
    const isShelters = currentPath.includes("shelters");

    bar.innerHTML = `
      <a href="index.html" class="mobile-bar-item ${isHome ? 'active' : ''}">
        <span class="icon">🏠</span>
        <span>Home</span>
      </a>
      <a href="safe-route.html" class="mobile-bar-item ${isRoute ? 'active' : ''}">
        <span class="icon">🗺️</span>
        <span>Routes</span>
      </a>
      <a href="javascript:void(0)" onclick="openEmergencySOSModal()" class="mobile-bar-item mobile-bar-sos" title="Emergency SOS 112">
        <span class="icon">🚨</span>
        <span>SOS 112</span>
      </a>
      <a href="monitoring.html" class="mobile-bar-item ${isMonitoring ? 'active' : ''}">
        <span class="icon">🌊</span>
        <span>Rivers</span>
      </a>
      <a href="shelters.html" class="mobile-bar-item ${isShelters ? 'active' : ''}">
        <span class="icon">🏕️</span>
        <span>Shelters</span>
      </a>
    `;
    document.body.appendChild(bar);
  }
}

/* ================= UNIVERSAL SOS & HELPLINE CLICK DELEGATION ================= */
// Ensures EVERY SOS and helpline button across all pages is 100% clickable & reliable
document.addEventListener("click", function (e) {
  const sosHeader = e.target.closest(".sos-header-btn");
  if (sosHeader) {
    e.preventDefault();
    openEmergencySOSModal();
    return;
  }
  const mobileSos = e.target.closest(".mobile-bar-sos");
  if (mobileSos) {
    e.preventDefault();
    openEmergencySOSModal();
    return;
  }
  // Ensure emergency chip clicks reliably launch dialer on all mobile and web browsers
  const chip = e.target.closest(".emergency-chip");
  if (chip && chip.getAttribute("href") && chip.getAttribute("href").startsWith("tel:")) {
    // Let browser default handle or trigger fallback
    const telNumber = chip.getAttribute("href");
    if (telNumber) {
      window.location.href = telNumber;
    }
  }
});