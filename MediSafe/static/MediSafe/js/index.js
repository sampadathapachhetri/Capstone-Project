window.MedicalApp = window.MedicalApp || {};
window.MedicalApp.Pages = window.MedicalApp.Pages || {};
window.MedicalApp.currentPage = null;

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

document.addEventListener("DOMContentLoaded", async (e) => {
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
  go_dc_button.addEventListener("click", async () => {
    activeNav = drugcheck_nav;
    const pageName = navToPageMap[activeNav.id].pageName.toLowerCase();
    const url = new URL(window.location.href);
    url.searchParams.set("page", pageName);
    window.history.pushState({}, "", url);
    await fillActivePage();
  });
}

async function fillActivePage() {
  try {
    const activeNavId = activeNav.id;

    const pageConfig = navToPageMap[activeNavId];

    if (!pageConfig) {
      throw new Error(`No page mapped for nav: ${activeNavId}`);
    }

    const response = await fetch("sub/" + pageConfig.pageName.toLowerCase());

    // ONLY added from backend
    if (response.url && response.url.includes("/login/")) {
      window.location.href = "/login/";
      return;
    }
    // END ONLY

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const htmlContent = await response.text();

    contents.innerHTML = htmlContent;

    await loadPageScript(pageConfig.pageName);

    clearAllActive();

    activeNav.classList.add("active");

    MedicalApp.currentPage = pageConfig.pageName;
    path_nav.innerHTML = `<li>Home</li>
<<<<<<< HEAD
          <li>></li>
=======
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
>>>>>>> dev
          <li>${pageConfig.pageName}</li>`;
  } catch (error) {
    console.error("Error loading page:", error);
    contents.innerHTML = `<div class="error">Failed to load page: ${error.message}</div>`;
  }
}

function clearAllActive() {
  for (let item of allNavs) {
    item.classList.remove("active");
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
    script.src = `static/medisafe/js/${pageName.toLowerCase()}.js`;
    script.dataset.page = pageName;

    script.onload = () => {
      console.log(`Loaded Scipt:${pageName},js`);

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
