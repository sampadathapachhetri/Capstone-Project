(function (global) {
  global.MedicalApp = global.MedicalApp || {};
  global.MedicalApp.Pages = global.MedicalApp.Pages || {};

  global.MedicalApp.Pages.Medications = {
    init: function () {
      console.log("Medications Initialized");
      this.setupEventHandling();
      this.setupSearch();
      this.setupCustomDropdown();
      this.setupFilterButton();
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

    setupSearch: function () {
      const searchInput = document.getElementById("medSearchInput");
      if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener("input", function () {
          const query = this.value.trim();

          // Only search if 2+ characters OR empty (to clear results)
          if (query.length >= 2 || query.length === 0) {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
              loadMedications(1);
            }, 400);
          }
        });

        // Search on Enter key
        searchInput.addEventListener("keydown", function (e) {
          if (e.key === "Enter") {
            clearTimeout(debounceTimer);
            loadMedications(1);
          }
        });
      }
    },

    setupCustomDropdown: function () {
      const toggle = document.getElementById("medStatusToggle");
      const menu = document.getElementById("medStatusMenu");
      const selectedSpan = document.getElementById("medSelectedStatus");

      if (!toggle || !menu) return;

      toggle.addEventListener("click", function (e) {
        e.stopPropagation();
        const isOpen = menu.classList.toggle("open");
        toggle.classList.toggle("open", isOpen);
      });

      menu.querySelectorAll("li").forEach((item) => {
        item.addEventListener("click", function () {
          const value = this.dataset.value;
          const label = this.textContent;

          selectedSpan.textContent = label;

          menu
            .querySelectorAll("li")
            .forEach((li) => li.classList.remove("active"));
          this.classList.add("active");

          menu.classList.remove("open");
          toggle.classList.remove("open");

          toggle.dataset.value = value;

          loadMedications(1);
        });
      });

      document.addEventListener("click", function (e) {
        if (!e.target.closest(".custom-dropdown")) {
          menu.classList.remove("open");
          toggle.classList.remove("open");
        }
      });

      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") {
          menu.classList.remove("open");
          toggle.classList.remove("open");
        }
      });
    },

    setupFilterButton: function () {
      const filterBtn = document.getElementById("med_filter_btn");
      if (filterBtn) {
        filterBtn.addEventListener("click", function () {
          loadMedications(1);
        });
      }
    },

    redirectHandler: async function (pageConfig) {
      if (pageConfig && pageConfig.file) {
        const response = await fetch(
          "sub/" + pageConfig.pageName.toLowerCase(),
        );
        if (!response.ok) {
          throw new Error(`FETCHING error: ${response.status}`);
        }
        const htmlText = await response.text();
        let contents_div = document.getElementById("contents_div");

        contents_div.innerHTML = htmlText;
        MedicalApp.currentPage = pageConfig.pageName;
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

        await this.loadPageScript(pageConfig);
      } else {
        console.error("Invalid page configuration");
      }
    },

    loadPageScript: async function (pageConfig) {
      return new Promise((resolve, reject) => {
        const pageName = pageConfig.pageName;

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
          console.log(`Loaded: ${pageName}`);
          if (MedicalApp.Pages[pageName] && MedicalApp.Pages[pageName].init) {
            MedicalApp.Pages[pageName].init();
          }
          resolve();
        };

        script.onerror = () => {
          console.error(`Failed to load script: ${pageName}`);
          reject(new Error(`Failed to load script: ${pageName}`));
        };

        document.head.appendChild(script);
      });
    },
    
  };

  // ============== LOAD MEDICATIONS FUNCTION ==============

  function loadMedications(pageNumber) {
    const searchInput = document.getElementById("medSearchInput");
    const statusToggle = document.getElementById("medStatusToggle");

    const searchQuery = searchInput ? searchInput.value.trim() : "";
    const statusFilter = statusToggle
      ? statusToggle.dataset.value || "all"
      : "all";

    // Show loading state
    const tableBody = document.getElementById("medications_table_body");
    if (tableBody) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; padding: 40px;">
            <div style="display: inline-block;">
              <div class="loading-spinner" style="margin: 0 auto;"></div>
              <p style="color: #64748b; margin-top: 12px;">Loading...</p>
            </div>
          </td>
        </tr>
      `;
    }

    let url = `/api/medications/?page=${pageNumber}`;
    if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`;
    if (statusFilter && statusFilter !== "all")
      url += `&active=${statusFilter}`;

    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          renderMedicationsTable(data);
        } else {
          showMedicationError(data.error || "Failed to load medications");
        }
      })
      .catch((error) => {
        console.error("Error loading medications:", error);
        showMedicationError("Unable to load medications. Please try again.");
      });
  }

  function renderMedicationsTable(data) {
    const tableBody = document.getElementById("medications_table_body");
    if (!tableBody) return;

    if (data.data.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; padding: 40px; color: #64748b;">
            No medications found matching your criteria
          </td>
        </tr>
      `;
      return;
    }

    let rows = "";
    data.data.forEach((med) => {
      const statusClass = med.active ? "med_active_tb" : "med_inactive_tb";
      const statusText = med.active ? "Active" : "Inactive";

      rows += `
        <tr class="med_rows" data-med-id="${med.id}">
          <td class="med_name_tb">
            <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#005fb8">
              <path d="M345-120q-94 0-159.5-65.5T120-345q0-45 17-86t49-73l270-270q32-32 73-49t86-17q94 0 159.5 65.5T840-615q0 45-17 86t-49 73L504-186q-32 32-73 49t-86 17Zm266-286 107-106q20-20 31-47t11-56q0-60-42.5-102.5T615-760q-29 0-56 11t-47 31L406-611l205 205ZM345-200q29 0 56-11t47-31l106-107-205-205-107 106q-20 20-31 47t-11 56q0 60 42.5 102.5T345-200Z"/>
            </svg>
            <span class="med_name_text">${med.name}</span>
          </td>
          <td class="med_dosage_tb">${med.dosage_amount} mg ${med.dosage_frequency}</td>
          <td class="med_category_tb">${med.category}</td>
          <td class="med_refill_tb">${med.last_refill}</td>
          <td class="med_status_tb ${statusClass}"><span>${statusText}</span></td>
          <td class="med_actions_tb">
            <div class="tooltip">
              <button onclick="window.location.href='/switch_status/${med.id}/'">
                <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#585858">
                  ${
                    med.active
                      ? '<path d="M324-111.5Q251-143 197-197t-85.5-127Q80-397 80-480t31.5-156Q143-709 197-763t127-85.5Q397-880 480-880t156 31.5Q709-817 763-763t85.5 127Q880-563 880-480t-31.5 156Q817-251 763-197t-127 85.5Q563-80 480-80t-156-31.5ZM480-160q54 0 104-17.5t92-50.5L228-676q-33 42-50.5 92T160-480q0 134 93 227t227 93Zm252-124q33-42 50.5-92T800-480q0-134-93-227t-227-93q-54 0-104 17.5T284-732l448 448ZM480-480Z"/>'
                      : '<path d="M268-240 42-466l57-56 170 170 56 56-57 56Zm226 0L268-466l56-57 170 170 368-368 56 57-424 424Zm0-226-57-56 198-198 57 56-198 198Z"/>'
                  }
                </svg>
              </button>
              <span class="tooltiptext">${med.active ? "Deactivate medication" : "Activate medication"}</span>
            </div>
            <div class="tooltip">
              <button onclick="window.location.href='/delete_medication/${med.id}/'">
                <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#585858">
                  <path d="M280-120q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Zm400-600H280v520h400v-520ZM360-280h80v-360h-80v360Zm160 0h80v-360h-80v360ZM280-720v520-520Z"/>
                </svg>
              </button>
              <span class="tooltiptext tooltiptext-bottom">Delete</span>
            </div>
          </td>
        </tr>
      `;
    });

    tableBody.innerHTML = rows;
  }

  function showMedicationError(message) {
    const tableBody = document.getElementById("medications_table_body");
    if (!tableBody) return;

    tableBody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align: center; padding: 40px; color: #dc2626;">
          <svg xmlns="http://www.w3.org/2000/svg" height="48px" viewBox="0 -960 960 960" width="48px" fill="#dc2626">
            <path d="M440-280h80v-240h-80v240Zm40-320q17 0 28.5-11.5T520-640q0-17-11.5-28.5T480-680q-17 0-28.5 11.5T440-640q0 17 11.5 28.5T480-600Zm0 520q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-80q134 0 227-93t93-227q0-134-93-227t-227-93q-134 0-227 93t-93 227q0 134 93 227t227 93Zm0-320Z"/>
          </svg>
          <p style="margin-top: 12px;">${message}</p>
        </td>
      </tr>
    `;
  }

  

  // Expose functions globally
  global.loadMedications = loadMedications;
}
  
)(window);
