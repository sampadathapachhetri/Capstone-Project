(function (global) {
  global.MedicalApp = global.MedicalApp || {};
  global.MedicalApp.Pages = global.MedicalApp.Pages || {};

  global.MedicalApp.Pages.Medications = {
    init: function () {
      console.log("Medications Initialized");
      this.setupEventHandling();
    },

    setupEventHandling: function () {
      let new_med_button = document.getElementById("new_med_button");
      let navToPageMap = {
        new_med_button: {
          file: "addMedications.html",
          pageName: "AddMedications",
        },
      };

      if (new_med_button) {
        new_med_button.addEventListener("click", async (e) => {
          e.stopPropagation();
          e.preventDefault();
          await this.redirectHandler(navToPageMap.new_med_button);
        });
      }
    },

    redirectHandler: async function (pageConfig) {
      if (pageConfig && pageConfig.file) {
        const response = await fetch("" + pageConfig.file);
        if (!response.ok) {
          throw new Error(`FETCHING error: ${response.status}`);
        }
        const htmlText = await response.text();
        let contents_div = document.getElementById("contents_div");

        contents_div.innerHTML = htmlText;
        MedicalApp.currentPage = pageConfig.pageName;

        // Load the script for the new page
        await this.loadPageScript(pageConfig);

        path_nav.innerHTML += `
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
      } else {
        console.error("Invalid page configuration");
      }
    },

    loadPageScript: async function (pageConfig) {
      return new Promise((resolve, reject) => {
        const pageName = pageConfig.pageName;

        // FIXED: Added missing closing bracket
        const existingScript = document.querySelector(
          `script[data-page="${pageName}"]`, // Fixed here
        );

        if (existingScript) {
          if (MedicalApp.Pages[pageName] && MedicalApp.Pages[pageName].init) {
            MedicalApp.Pages[pageName].init();
          }
          resolve();
          return;
        }

        const script = document.createElement("script");
        script.src = `../js/${pageName.toLowerCase()}.js`;
        script.dataset.page = pageName;

        script.onload = () => {
          console.log(`Loaded: ${pageName}`);
          // FIXED: Changed Pagees to Pages
          if (MedicalApp.Pages[pageName] && MedicalApp.Pages[pageName].init) {
            MedicalApp.Pages[pageName].init(); // Fixed here
          }
          resolve();
        };

        script.onerror = () => {
          // FIXED: Changed eroor to error
          console.error(`Failed to load script: ${pageName}`); // Fixed here
          reject(new Error(`Failed to load script: ${pageName}`));
        };

        document.head.appendChild(script);
      });
    },
  };
})(window);
