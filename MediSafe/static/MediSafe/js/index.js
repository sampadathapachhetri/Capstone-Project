window.MedicalApp = window.MedicalApp || {};
window.MedicalApp.Pages = window.MedicalApp.Pages || {};
window.MedicalApp.currentPage = null;

// ========== CUSTOM TOOLTIP ==========

// Create tooltip element
const tooltip = document.createElement("div");
tooltip.id = "custom-tooltip";
tooltip.style.cssText = `
  position: fixed;
  background: #1e293b;
  color: white;
  padding: 8px 14px;
  border-radius: 6px;
  font-family: 'Inter', sans-serif;
  font-size: 12px;
  font-weight: 500;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.2s ease;
  z-index: 99999;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  white-space: nowrap;
  max-width: 300px;
`;

// Add arrow to tooltip
const tooltipArrow = document.createElement("div");
tooltipArrow.style.cssText = `
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-top: 6px solid #1e293b;
`;
tooltip.appendChild(tooltipArrow);
document.body.appendChild(tooltip);

let tooltipTimeout = null;

function showCustomTooltip(element, text) {
  // Clear any pending hide timeout
  if (tooltipTimeout) {
    clearTimeout(tooltipTimeout);
    tooltipTimeout = null;
  }

  // Get element position
  const rect = element.getBoundingClientRect();

  // Position tooltip BELOW the element (not above)
  const tooltipWidth = Math.min(text.length * 8 + 30, 300);
  const left = rect.left + rect.width / 2 - tooltipWidth / 2;
  const top = rect.bottom + 10; // 10px below the icon

  tooltip.style.left = `${Math.max(10, left)}px`;
  tooltip.style.top = `${Math.max(10, top)}px`;
  tooltip.style.width = `${Math.min(tooltipWidth, 280)}px`;
  tooltip.textContent = text;
  tooltip.style.opacity = "1";

  // Change arrow direction (point up instead of down)
  tooltipArrow.style.borderTop = "none";
  tooltipArrow.style.borderBottom = `6px solid #1e293b`;
  tooltipArrow.style.top = "-6px";
  tooltipArrow.style.bottom = "auto";
}

function hideCustomTooltip() {
  // Add a small delay before hiding to prevent flickering
  if (tooltipTimeout) {
    clearTimeout(tooltipTimeout);
  }
  tooltipTimeout = setTimeout(() => {
    tooltip.style.opacity = "0";
    tooltipTimeout = null;
  }, 100);
}

// Update tooltip position on scroll or resize
document.addEventListener("scroll", () => {
  if (tooltip.style.opacity === "1") {
    // Find which element is being hovered
    const hoveredElement = document.querySelector("#notification_button:hover");
    if (hoveredElement) {
      const rect = hoveredElement.getBoundingClientRect();
      const text =
        hoveredElement.getAttribute("data-tooltip") ||
        hoveredElement.title ||
        "";
      const tooltipWidth = Math.min(text.length * 8 + 30, 300);
      const left = rect.left + rect.width / 2 - tooltipWidth / 2;
      tooltip.style.left = `${Math.max(10, left)}px`;
      tooltip.style.top = `${Math.max(10, rect.bottom + 10)}px`;
    }
  }
});

// ========== NOTIFICATION FUNCTIONS ==========

function isNotificationEnabled() {
  if (!("Notification" in window)) {
    return false;
  }
  return Notification.permission === "granted";
}

function updateNotificationUI() {
  const notIcon = document.getElementById("notification_button");
  if (!notIcon) return;

  const isGranted = isNotificationEnabled();

  // Update tooltip text (stored in data attribute for custom tooltip)
  if (isGranted) {
    notIcon.setAttribute(
      "data-tooltip",
      "Click to revoke notification permission",
    );
    notIcon.setAttribute("title", "Click to revoke notification permission");
    notIcon.style.cursor = "pointer";
    // Show filled bell icon
    notIcon.innerHTML = `<path d="M160-200v-80h80v-280q0-83 50-147.5T420-792v-28q0-25 17.5-42.5T480-880q25 0 42.5 17.5T540-820v28q80 20 130 84.5T720-560v280h80v80H160Zm320-300Zm0 420q-33 0-56.5-23.5T400-160h160q0 33-23.5 56.5T480-80ZM320-280h320v-280q0-66-47-113t-113-47q-66 0-113 47t-47 113v280Z" />`;
  } else {
    notIcon.setAttribute(
      "data-tooltip",
      "Click to request notification permission",
    );
    notIcon.setAttribute("title", "Click to request notification permission");
    notIcon.style.cursor = "pointer";
    // Show muted/bell-off icon
    notIcon.innerHTML = `<path d="M160-200v-80h80v-280q0-33 8.5-65t25.5-61l60 60q-7 16-10.5 32.5T320-560v280h248L56-792l56-56 736 736-56 56-146-144H160Zm560-154-80-80v-126q0-66-47-113t-113-47q-26 0-50 8t-44 24l-58-58q20-16 43-28t49-18v-28q0-25 17.5-42.5T480-880q25 0 42.5 17.5T540-820v28q80 20 130 84.5T720-560v206Zm-276-50Zm36 324q-33 0-56.5-23.5T400-160h160q0 33-23.5 56.5T480-80Zm33-481Z"/>`;
  }

  // Setup hover events for custom tooltip
  notIcon.removeEventListener("mouseenter", handleTooltipMouseEnter);
  notIcon.removeEventListener("mouseleave", handleTooltipMouseLeave);
  notIcon.addEventListener("mouseenter", handleTooltipMouseEnter);
  notIcon.addEventListener("mouseleave", handleTooltipMouseLeave);
}

function handleTooltipMouseEnter(e) {
  const element = e.currentTarget;
  const tooltipText =
    element.getAttribute("data-tooltip") || element.title || "";
  if (tooltipText) {
    showCustomTooltip(element, tooltipText);
  }
}

function handleTooltipMouseLeave() {
  hideCustomTooltip();
}

function showToast(message, type = "info") {
  // Remove existing toast if any
  const existingToast = document.getElementById("notification-toast");
  if (existingToast) {
    existingToast.remove();
  }

  const toast = document.createElement("div");
  toast.id = "notification-toast";

  // Different colors based on type
  const colors = {
    success: "#10B981",
    error: "#EF4444",
    info: "#3B82F6",
    warning: "#F59E0B",
  };

  toast.style.cssText = `
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: ${colors[type] || colors.info};
    color: white;
    padding: 12px 24px;
    border-radius: 8px;
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    font-weight: 500;
    z-index: 10000;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    animation: slideUp 0.3s ease;
    max-width: 90%;
    text-align: center;
    pointer-events: none;
  `;
  toast.textContent = message;
  document.body.appendChild(toast);

  // Auto-remove after 3 seconds
  setTimeout(() => {
    toast.style.animation = "slideDown 0.3s ease";
    setTimeout(() => {
      if (toast.parentNode) {
        toast.remove();
      }
    }, 300);
  }, 3000);
}

// Add CSS animations for the toast (only if not already added)
if (!document.getElementById("toast-styles")) {
  const styleSheet = document.createElement("style");
  styleSheet.id = "toast-styles";
  styleSheet.textContent = `
    @keyframes slideUp {
      from { opacity: 0; transform: translateX(-50%) translateY(20px); }
      to { opacity: 1; transform: translateX(-50%) translateY(0); }
    }
    @keyframes slideDown {
      from { opacity: 1; transform: translateX(-50%) translateY(0); }
      to { opacity: 0; transform: translateX(-50%) translateY(20px); }
    }
  `;
  document.head.appendChild(styleSheet);
}

async function toggleNotificationPermission() {
  if (!("Notification" in window)) {
    showToast("Your browser doesn't support notifications", "error");
    return;
  }

  const isGranted = Notification.permission === "granted";

  if (isGranted) {
    // Try to revoke permission
    try {
      if (navigator.permissions && navigator.permissions.revoke) {
        const result = await navigator.permissions.revoke({
          name: "notifications",
        });
        if (result.state === "prompt") {
          console.log("Notification permission revoked");
          updateNotificationUI();
          showToast("Notification permission has been revoked", "success");
        } else {
          showToast("Permission state: " + result.state, "info");
        }
      } else {
        // Fallback: Guide user to manual revocation
        showToast("Please revoke permissions in browser settings", "warning");
        setTimeout(() => {
          if (
            confirm(
              "Would you like to open browser settings to manage permissions?",
            )
          ) {
            if (window.chrome && window.chrome.tabs) {
              window.open("chrome://settings/content/notifications", "_blank");
            } else {
              alert(
                'Please go to Site Settings > Notifications and set to "Block" or "Ask"\n(for vivaldi: Go to browser settings > Permission > Site > Notification)',
              );
            }
          }
        }, 500);
      }
    } catch (error) {
      console.error("Failed to revoke permission:", error);
      showToast(
        "Could not revoke permission. Please use browser settings.",
        "error",
      );
    }
  } else {
    // Request permission
    try {
      const permission = await Notification.requestPermission();
      if (permission === "granted") {
        console.log("Notification permission granted");
        updateNotificationUI();
        showToast("Notification permission granted!", "success");

        // Send permission status to server
        try {
          await fetch("/api/update-notification-status/", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": getCSRFToken(),
            },
            body: JSON.stringify({ enabled: true }),
          });
        } catch (e) {
          console.log("Could not update server with permission status");
        }

        // Show a test notification
        setTimeout(() => {
          try {
            new Notification("MediSafe Notifications Enabled", {
              body: "You will now receive medication reminders and safety alerts. (If enabled in the User settings)",
              icon: "/static/MediSafe/images/logo.png",
            });
          } catch (e) {
            // Silent fail
          }
        }, 500);
      } else if (permission === "denied") {
        showToast(
          "Notification permission denied. Please enable in browser settings.",
          "error",
        );
      } else {
        showToast("Notification permission request dismissed", "info");
      }
    } catch (error) {
      console.error("Error requesting permission:", error);
      showToast("Error requesting notification permission", "error");
    }
  }
}

// Helper to get CSRF token from cookie
function getCSRFToken() {
  const name = "csrftoken";
  const cookies = document.cookie.split(";");
  for (let cookie of cookies) {
    const [key, value] = cookie.trim().split("=");
    if (key === name) {
      return value;
    }
  }
  return "";
}

function showNotification(
  title,
  body,
  icon = "/static/MediSafe/images/logo.png",
) {
  // Check if browser supports notifications
  if (!("Notification" in window)) {
    console.log("Browser doesn't support notifications");
    return;
  }

  // Check permission
  if (Notification.permission === "granted") {
    try {
      new Notification(title, {
        body: body,
        icon: icon,
      });
    } catch (e) {
      console.log("Failed to show notification:", e);
    }
  } else if (Notification.permission === "default") {
    Notification.requestPermission().then((permission) => {
      if (permission === "granted") {
        try {
          new Notification(title, {
            body: body,
            icon: icon,
          });
        } catch (e) {
          console.log("Failed to show notification:", e);
        }
      }
    });
  }
}

function showNotIcon() {
  updateNotificationUI();
}

// ========== NAVIGATION FUNCTIONS ==========

let dashboard_nav = document.getElementById("dashboard_nav_button");
let drugcheck_nav = document.getElementById("drug_checker_nav_button");
let history_nav = document.getElementById("history_nav_button");
let medications_nav = document.getElementById("medications_nav_button");
let settings_nav = document.getElementById("settings_nav_button");
let go_dc_button = document.getElementById("go_dc_button");
let path_nav = document.getElementById("path_nav");

let allNavs = [
  dashboard_nav,
  drugcheck_nav,
  history_nav,
  medications_nav,
  settings_nav,
];

let navToPageMap = {
  dashboard_nav_button: { file: "dashboard.html", pageName: "Dashboard" },
  drug_checker_nav_button: { file: "drugCheck.html", pageName: "DrugCheck" },
  history_nav_button: { file: "history.html", pageName: "History" },
  medications_nav_button: { file: "medications.html", pageName: "Medications" },
  settings_nav_button: { file: "settings.html", pageName: "Settings" },
};

let activeNav = null;
let contents = document.getElementById("contents_div");

// ========== INITIALIZATION ==========

document.addEventListener("DOMContentLoaded", async (e) => {
  // Initialize notification UI
  showNotIcon();

  // Add click event listener to notification icon
  const notificationButton = document.getElementById("notification_button");
  if (notificationButton) {
    notificationButton.addEventListener("click", toggleNotificationPermission);
  }

  // Check for reminder notifications from server
  try {
    const response = await fetch("/api/canReminderNot/");
    const data = await response.json();
    if (data.allowed == true) {
      showNotification(
        "Monthly Report Alert",
        "Remember to Regularly Export your reports monthly.",
      );
    }
  } catch (error) {
    console.log("Could not fetch reminder notification status:", error);
  }

  // Handle page parameter from URL
  const urlParams = new URLSearchParams(window.location.search);
  const page = urlParams.get("page");

  if (page === "dashboard") {
    activeNav = dashboard_nav;
  } else if (page === "drugcheck") {
    activeNav = drugcheck_nav;
  } else if (page === "history") {
    activeNav = history_nav;
  } else if (page === "medications") {
    activeNav = medications_nav;
  } else if (page === "settings") {
    activeNav = settings_nav;
  } else {
    activeNav = dashboard_nav;
    const pageName = navToPageMap[activeNav.id].pageName.toLowerCase();
    const url = new URL(window.location.href);
    url.searchParams.set("page", pageName);
    window.history.pushState({}, "", url);
  }

  setupNavigation();
  await fillActivePage();
});

window.addEventListener("popstate", () => {
  window.location.reload();
});

// Listen for permission changes from other tabs/windows
if (navigator.permissions && navigator.permissions.query) {
  try {
    navigator.permissions
      .query({ name: "notifications" })
      .then((permissionStatus) => {
        permissionStatus.onchange = () => {
          console.log(
            "Notification permission changed to:",
            permissionStatus.state,
          );
          updateNotificationUI();

          // Notify server about permission change
          const isGranted = Notification.permission === "granted";
          try {
            fetch("/api/update-notification-status/", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken(),
              },
              body: JSON.stringify({ enabled: isGranted }),
            }).catch(() => {});
          } catch (e) {
            // Silent fail
          }
        };
      })
      .catch(() => {
        // Permissions API not fully supported
      });
  } catch (e) {
    // Silent fail
  }
}

// ========== NAVIGATION SETUP ==========

function setupNavigation() {
  allNavs.forEach((nav) => {
    if (nav) {
      nav.addEventListener("click", async () => {
        activeNav = nav;
        const pageName = navToPageMap[activeNav.id].pageName.toLowerCase();
        const url = new URL(window.location.href);
        url.searchParams.set("page", pageName);
        window.history.pushState({}, "", url);
        await fillActivePage();
      });
    }
  });

  if (go_dc_button) {
    go_dc_button.addEventListener("click", async () => {
      activeNav = drugcheck_nav;
      const pageName = navToPageMap[activeNav.id].pageName.toLowerCase();
      const url = new URL(window.location.href);
      url.searchParams.set("page", pageName);
      window.history.pushState({}, "", url);
      await fillActivePage();
    });
  }
}

async function fillActivePage() {
  try {
    const activeNavId = activeNav.id;
    const pageConfig = navToPageMap[activeNavId];

    if (!pageConfig) {
      throw new Error(`No page mapped for nav: ${activeNavId}`);
    }

    const response = await fetch("sub/" + pageConfig.pageName.toLowerCase());

    // Redirect to login if backend redirects
    if (response.url && response.url.includes("/login/")) {
      window.location.href = "/login/";
      return;
    }

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const htmlContent = await response.text();
    contents.innerHTML = htmlContent;

    await loadPageScript(pageConfig.pageName);

    clearAllActive();
    activeNav.classList.add("active");

    MedicalApp.currentPage = pageConfig.pageName;

    // Update breadcrumb
    if (path_nav) {
      path_nav.innerHTML = `<li>Home</li>
           <li>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              height="24px"
              viewBox="0 -960 960 960"
              width="24px"
              fill="#1D1D1D">
              <path d="M400-280v-400l200 200-200 200Z" />
            </svg>
          </li>
          <li>${pageConfig.pageName}</li>`;
    }
  } catch (error) {
    console.error("Error loading page:", error);
    if (contents) {
      contents.innerHTML = `<div class="error">Failed to load page: ${error.message}</div>`;
    }
  }
}

function clearAllActive() {
  for (let item of allNavs) {
    if (item) {
      item.classList.remove("active");
    }
  }
}

async function loadPageScript(pageName) {
  return new Promise((resolve, reject) => {
    const existingScript = document.querySelector(
      `script[data-page="${pageName}"]`,
    );
    if (existingScript) {
      if (MedicalApp.Pages[pageName] && MedicalApp.Pages[pageName].init) {
        MedicalApp.Pages[pageName].init();
      }
      resolve();
      return;
    }

    const script = document.createElement("script");
    script.src = `/static/medisafe/js/${pageName.toLowerCase()}.js`;
    script.dataset.page = pageName;

    script.onload = () => {
      console.log(`Loaded Script: ${pageName}.js`);

      if (MedicalApp.Pages[pageName] && MedicalApp.Pages[pageName].init) {
        MedicalApp.Pages[pageName].init();
      }
      resolve();
    };

    script.onerror = () => {
      console.error(`Failed to load script: ${pageName}.js`);
      reject(new Error(`Failed to load script for ${pageName}`));
    };
    document.head.appendChild(script);
  });
}
