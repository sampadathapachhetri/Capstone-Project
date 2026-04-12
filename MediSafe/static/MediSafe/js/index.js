// Declaring namespaces
window.MedicalApp = window.MedicalApp || {};
window.MedicalApp.Pages = window.MedicalApp.Pages || {};
window.MedicalApp.currentPage = null;

// Left side navigation buttons
let dashboard_nav = document.getElementById("dashboard_nav_button");
let drugcheck_nav = document.getElementById("drug_checker_nav_button");
let history_nav = document.getElementById("history_nav_button");
let medications_nav = document.getElementById("medications_nav_button");
let settings_nav = document.getElementById("settings_nav_button");
let go_dc_button = document.getElementById("go_dc_button");

let allNavs = [
  dashboard_nav,
  drugcheck_nav,
  history_nav,
  medications_nav,
  settings_nav,
];

// mapping all buttons to respective page via filename
let navToPageMap = {
  dashboard_nav_button: { file: "dashboard.html", pageName: "Dashboard" },
  drug_checker_nav_button: { file: "drugCheck.html", pageName: "DrugCheck" },
  history_nav_button: { file: "history.html", pageName: "History" },
  medications_nav_button: { file: "medications.html", pageName: "Medications" },
  settings_nav_button: { file: "settings.html", pageName: "Settings" },
};

// active nav button
let activeNav = null;
// the container in index.html where all these small pages are pushed
let contents = document.getElementById("contents_div");

document.addEventListener("DOMContentLoaded", async (e) => {
  //triggers upon load
  activeNav = dashboard_nav;
  setupNavigation(); //setup navigation buttons i.e add event listeners and set the clicked button as activeNav
  await fillActivePage(); // function to fill the sub container with a page (dashboard.html as first)
});
function setupNavigation() {
  allNavs.forEach((nav) => {
    if (nav) {
      nav.addEventListener("click", async () => {
        activeNav = nav;
        await fillActivePage();
      });
    }
  });
  go_dc_button.addEventListener("click", async () => {
    activeNav = drugcheck_nav;
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

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const htmlContent = await response.text();

    contents.innerHTML = htmlContent;

    await loadPageScript(pageConfig.pageName);

    clearAllActive();

    activeNav.classList.add("active");

    MedicalApp.currentPage = pageConfig.pageName;
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
