(function (global) {
  global.MedicalApp = global.MedicalApp || {};
  global.MedicalApp.Pages = global.MedicalApp.Pages || {};

  // Store current interaction data for export
  let currentInteractionData = null;

  global.MedicalApp.Pages.History = {
    init: function () {
      console.log("History Initialized");
      this.setupReportLinks();
      this.setupModalClose();
      this.setupPagination();
      this.setupFilters();
      this.setupCustomDropdown();
      this.setupPrintButton();
      this.setupCSVExport();
    },

    setupReportLinks: function () {
      document.addEventListener("click", function (e) {
        const reportLink = e.target.closest(".view-report-link");
        if (reportLink) {
          e.preventDefault();
          e.stopPropagation();

          const reportId = reportLink.getAttribute("data-report-id") || "1";
          const row = reportLink.closest(".history_row");

          if (row) {
            const drugCells = row.querySelectorAll(".history_card_drugs span");
            const drug1 = drugCells[0]
              ? drugCells[0].textContent.trim()
              : "Unknown";
            const drug2 = drugCells[1]
              ? drugCells[1].textContent.trim()
              : "Unknown";

            const severityDiv = row.querySelector(
              '[class*="history_card_risk_"]',
            );
            let severity = "low";
            if (severityDiv) {
              const classes = severityDiv.className.split(" ");
              for (let cls of classes) {
                if (cls.startsWith("history_card_risk_")) {
                  severity = cls.replace("history_card_risk_", "");
                  break;
                }
              }
            }

            const description =
              row.getAttribute("data-description") ||
              "No description available.";
            showAnalysisModal(reportId, drug1, drug2, severity, description);
          }
        }
      });
    },

    setupModalClose: function () {
      document.addEventListener("click", function (e) {
        const modal = document.getElementById("analysisModal");
        if (e.target === modal) {
          closeAnalysisModal();
        }
      });

      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") {
          closeAnalysisModal();
        }
      });
    },

    setupPagination: function () {
      document.addEventListener("click", function (e) {
        const pageBtn = e.target.closest(".page-btn");
        if (pageBtn && !pageBtn.disabled) {
          e.preventDefault();
          e.stopPropagation();
          const pageNumber = pageBtn.getAttribute("data-page");
          if (pageNumber) {
            loadHistoryPage(pageNumber);
          }
        }
      });
    },

    setupFilters: function () {
      const searchInput = document.getElementById("searchInput");
      if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener("input", function () {
          const query = this.value.trim();

          if (query.length >= 2 || query.length === 0) {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
              loadHistoryPage(1);
            }, 400);
          }
        });

        searchInput.addEventListener("keydown", function (e) {
          if (e.key === "Enter") {
            clearTimeout(debounceTimer);
            loadHistoryPage(1);
          }
        });
      }

      const dateRangeBtn = document.getElementById("dateRangeBtn");
      if (dateRangeBtn) {
        dateRangeBtn.addEventListener("click", function (e) {
          e.stopPropagation();
          showDatePicker();
        });
      }
    },

    setupCustomDropdown: function () {
      const toggle = document.getElementById("severityToggle");
      const menu = document.getElementById("severityMenu");
      const selectedSpan = document.getElementById("selectedSeverity");

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

          loadHistoryPage(1);
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

    setupPrintButton: function () {
      const printBtn = document.getElementById("export_history_pdf_btn");
      if (printBtn) {
        printBtn.addEventListener("click", (e) => {
          e.preventDefault();
          this.exportHistoryPDF();
        });
      }
    },

    exportHistoryPDF: function () {
      const printBtn = document.getElementById("export_history_pdf_btn");
      const originalText = printBtn.innerHTML;

      printBtn.innerHTML =
        '<span style="display:flex;align-items:center;gap:8px;"><div class="loading-spinner-small"></div> Generating PDF...</span>';
      printBtn.disabled = true;

      fetch("/export/history/pdf/")
        .then((response) => {
          if (!response.ok) {
            throw new Error("Export failed");
          }
          return response.blob();
        })
        .then((blob) => {
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          const date = new Date().toISOString().split("T")[0];
          a.download = `interaction_history_${date}.pdf`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          a.remove();

          printBtn.innerHTML = originalText;
          printBtn.disabled = false;
        })
        .catch((error) => {
          console.error("Export error:", error);
          printBtn.innerHTML = originalText;
          printBtn.disabled = false;
          alert("Failed to generate PDF. Please try again.");
        });
    },

    setupCSVExport: function () {
      const csvBtn = document.getElementById("export_csv_btn");
      if (csvBtn) {
        csvBtn.addEventListener("click", (e) => {
          e.preventDefault();
          this.exportHistoryCSV();
        });
      }
    },

    exportHistoryCSV: function () {
      const csvBtn = document.getElementById("export_csv_btn");
      const originalText = csvBtn.innerHTML;

      csvBtn.innerHTML =
        '<span style="display:flex;align-items:center;gap:8px;"><div class="loading-spinner-small"></div> Generating CSV...</span>';
      csvBtn.disabled = true;

      fetch("/export/history/csv/")
        .then((response) => {
          if (!response.ok) {
            throw new Error("Export failed");
          }
          return response.blob();
        })
        .then((blob) => {
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          const date = new Date().toISOString().split("T")[0];
          a.download = `interaction_history_${date}.csv`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          a.remove();

          csvBtn.innerHTML = originalText;
          csvBtn.disabled = false;
        })
        .catch((error) => {
          console.error("Export error:", error);
          csvBtn.innerHTML = originalText;
          csvBtn.disabled = false;
          alert("Failed to export CSV. Please try again.");
        });
    },
  };

  // ============== PAGINATION FUNCTIONS ==============

  function loadHistoryPage(pageNumber) {
    const searchInput = document.getElementById("searchInput");
    const severityToggle = document.getElementById("severityToggle");
    const dateRangeBtn = document.getElementById("dateRangeBtn");

    const searchQuery = searchInput ? searchInput.value.trim() : "";
    const severity = severityToggle
      ? severityToggle.dataset.value || "all"
      : "all";
    const dateFrom = dateRangeBtn ? dateRangeBtn.dataset.dateFrom || "" : "";
    const dateTo = dateRangeBtn ? dateRangeBtn.dataset.dateTo || "" : "";

    const tableBody = document.getElementById("history_table_body");
    tableBody.innerHTML = `
      <tr>
        <td colspan="4" style="text-align: center; padding: 40px;">
          <div style="display: inline-block;">
            <div class="loading-spinner" style="margin: 0 auto;"></div>
            <p style="color: #64748b; margin-top: 12px;">Loading...</p>
          </div>
        </td>
      </tr>
    `;

    let url = `/api/history/?page=${pageNumber}`;
    if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`;
    if (severity && severity !== "all") url += `&severity=${severity}`;
    if (dateFrom) url += `&date_from=${dateFrom}`;
    if (dateTo) url += `&date_to=${dateTo}`;

    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          renderHistoryTable(data);
        } else {
          showErrorInTable(data.error || "Failed to load history");
        }
      })
      .catch((error) => {
        console.error("Error loading history:", error);
        showErrorInTable("Unable to load history. Please try again.");
      });
  }

  function renderHistoryTable(data) {
    const tableBody = document.getElementById("history_table_body");
    const paginationInfo = document.getElementById("pagination_info");
    const paginationControls = document.getElementById("pagination_controls");

    if (data.data.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="4" class="empty-state">No history found</td>
        </tr>
      `;
    } else {
      let rows = "";
      data.data.forEach((item) => {
        const severityClass = item.severity.toLowerCase();
        rows += `
          <tr class="history_row" data-description="${item.description || "No description available."}">
            <td>
              <div class="history_card_date">
                <h3>${item.date}</h3>
                <span>${item.time}</span>
              </div>
            </td>
            <td>
              <div class="history_card_drugs">
                <span>${item.drug1}</span>
                <span>${item.drug2}</span>
              </div>
            </td>
            <td>
              <div class="history_card_risk_${severityClass}">
                <div class="dot severity-${item.severity_level}"></div>
                <span>${item.severity}</span>
              </div>
            </td>
            <td>
              <a href="#" class="view-report-link" data-report-id="${item.id}">View Report</a>
            </td>
          </tr>
        `;
      });
      tableBody.innerHTML = rows;
    }

    const start = data.pagination.start_index || 0;
    const end = data.pagination.end_index || 0;
    const total = data.pagination.total_items || 0;
    paginationInfo.textContent = `Showing ${start} to ${end} of ${total} checks`;

    let controls = "";
    const currentPage = data.pagination.current_page || 1;
    const totalPages = data.pagination.total_pages || 1;

    if (data.pagination.has_previous) {
      controls += `<button class="page-btn" data-page="${data.pagination.previous_page}">&lt;</button>`;
    } else {
      controls += `<button class="page-btn" disabled>&lt;</button>`;
    }

    for (let i = 1; i <= totalPages; i++) {
      if (i === currentPage) {
        controls += `<button class="page-btn active" data-page="${i}">${i}</button>`;
      } else if (i > currentPage - 3 && i < currentPage + 3) {
        controls += `<button class="page-btn" data-page="${i}">${i}</button>`;
      }
    }

    if (data.pagination.has_next) {
      controls += `<button class="page-btn" data-page="${data.pagination.next_page}">&gt;</button>`;
    } else {
      controls += `<button class="page-btn" disabled>&gt;</button>`;
    }

    paginationControls.innerHTML = controls;
  }

  function showErrorInTable(message) {
    const tableBody = document.getElementById("history_table_body");
    tableBody.innerHTML = `
      <tr>
        <td colspan="4" style="text-align: center; padding: 40px; color: #dc2626;">
          <svg xmlns="http://www.w3.org/2000/svg" height="48px" viewBox="0 -960 960 960" width="48px" fill="#dc2626">
            <path d="M440-280h80v-240h-80v240Zm40-320q17 0 28.5-11.5T520-640q0-17-11.5-28.5T480-680q-17 0-28.5 11.5T440-640q0 17 11.5 28.5T480-600Zm0 520q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-80q134 0 227-93t93-227q0-134-93-227t-227-93q-134 0-227 93t-93 227q0 134 93 227t227 93Zm0-320Z"/>
          </svg>
          <p style="margin-top: 12px;">${message}</p>
          <button onclick="location.reload()" style="
            margin-top: 16px;
            background: #005fb8;
            color: white;
            border: none;
            padding: 8px 20px;
            border-radius: 6px;
            cursor: pointer;
          ">
            Retry
          </button>
        </td>
      </tr>
    `;
  }

  // ============== DATE PICKER FUNCTIONS ==============

  function showDatePicker() {
    const existingPicker = document.getElementById("datePickerModal");
    if (existingPicker) {
      existingPicker.remove();
      return;
    }

    const dateRangeBtn = document.getElementById("dateRangeBtn");
    const currentDateFrom = dateRangeBtn
      ? dateRangeBtn.dataset.dateFrom || ""
      : "";
    const currentDateTo = dateRangeBtn ? dateRangeBtn.dataset.dateTo || "" : "";

    const pickerHTML = `
      <div id="datePickerModal" style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        backdrop-filter: blur(2px);
      ">
        <div style="
          background: white;
          padding: 24px;
          border-radius: 12px;
          max-width: 420px;
          width: 90%;
          box-shadow: 0 20px 60px rgba(0,0,0,0.3);
          animation: slideUp 0.3s ease;
        ">
          <h3 style="margin: 0 0 16px 0; font-size: 1.1em; color: #1e293b;">Select Date Range</h3>
          <div style="display: flex; flex-direction: column; gap: 14px;">
            <div>
              <label style="display: block; font-size: 0.8em; font-weight: 600; margin-bottom: 4px; color: #64748b;">From</label>
              <input type="date" id="dateFrom" value="${currentDateFrom}" style="
                width: 100%; 
                padding: 8px 12px; 
                border: 1px solid #e2e8f0; 
                border-radius: 6px; 
                font-size: 0.95em;
                font-family: 'Inter', sans-serif;
                outline: none;
                transition: border-color 0.2s;
              ">
            </div>
            <div>
              <label style="display: block; font-size: 0.8em; font-weight: 600; margin-bottom: 4px; color: #64748b;">To</label>
              <input type="date" id="dateTo" value="${currentDateTo}" style="
                width: 100%; 
                padding: 8px 12px; 
                border: 1px solid #e2e8f0; 
                border-radius: 6px; 
                font-size: 0.95em;
                font-family: 'Inter', sans-serif;
                outline: none;
                transition: border-color 0.2s;
              ">
            </div>
          </div>
          <div style="display: flex; gap: 10px; margin-top: 20px; justify-content: flex-end;">
            <button onclick="closeDatePicker()" style="
              padding: 8px 18px;
              border: 1px solid #e2e8f0;
              border-radius: 6px;
              background: white;
              cursor: pointer;
              color: #64748b;
              font-size: 0.85em;
              font-weight: 500;
              font-family: 'Inter', sans-serif;
              transition: all 0.2s;
            ">Cancel</button>
            <button onclick="applyDateFilter()" style="
              padding: 8px 18px;
              border: none;
              border-radius: 6px;
              background: #005fb8;
              cursor: pointer;
              color: white;
              font-weight: 600;
              font-size: 0.85em;
              font-family: 'Inter', sans-serif;
              transition: all 0.2s;
            ">Apply</button>
            <button onclick="clearDateFilter()" style="
              padding: 8px 18px;
              border: none;
              border-radius: 6px;
              background: #e2e8f0;
              cursor: pointer;
              color: #334155;
              font-weight: 500;
              font-size: 0.85em;
              font-family: 'Inter', sans-serif;
              transition: all 0.2s;
            ">Clear</button>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML("beforeend", pickerHTML);

    const dateFromInput = document.getElementById("dateFrom");
    if (dateFromInput) {
      setTimeout(() => dateFromInput.focus(), 100);
    }
  }

  function closeDatePicker() {
    const picker = document.getElementById("datePickerModal");
    if (picker) {
      picker.remove();
    }
  }

  function applyDateFilter() {
    const dateFrom = document.getElementById("dateFrom");
    const dateTo = document.getElementById("dateTo");
    const dateRangeBtn = document.getElementById("dateRangeBtn");

    if (dateRangeBtn) {
      if (dateFrom && dateFrom.value) {
        dateRangeBtn.dataset.dateFrom = dateFrom.value;
      } else {
        delete dateRangeBtn.dataset.dateFrom;
      }

      if (dateTo && dateTo.value) {
        dateRangeBtn.dataset.dateTo = dateTo.value;
      } else {
        delete dateRangeBtn.dataset.dateTo;
      }

      if (dateRangeBtn.dataset.dateFrom || dateRangeBtn.dataset.dateTo) {
        dateRangeBtn.classList.add("active");
      } else {
        dateRangeBtn.classList.remove("active");
      }
    }

    closeDatePicker();
    loadHistoryPage(1);
  }

  function clearDateFilter() {
    const dateRangeBtn = document.getElementById("dateRangeBtn");
    if (dateRangeBtn) {
      delete dateRangeBtn.dataset.dateFrom;
      delete dateRangeBtn.dataset.dateTo;
      dateRangeBtn.classList.remove("active");
    }
    closeDatePicker();
    loadHistoryPage(1);
  }

  // ============== MODAL FUNCTIONS ==============

  function showAnalysisModal(reportId, drug1, drug2, severity, description) {
    const modal = document.getElementById("analysisModal");
    const loadingState = document.getElementById("analysisLoadingState");
    const content = document.getElementById("analysisContent");

    modal.style.display = "flex";
    document.body.style.overflow = "hidden";

    loadingState.style.display = "flex";
    content.style.display = "none";

    fetch(`/api/gethistory/${reportId}`)
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          showErrorDialog(data.error);
          return;
        }
        renderAnalysisModal(data);
      })
      .catch((error) => {
        console.error("Error fetching interaction details:", error);
        showErrorDialog(
          "Unable to load interaction details. Please check your connection and try again.",
        );
      });
  }

  function showErrorDialog(errorMessage) {
    const loadingState = document.getElementById("analysisLoadingState");
    const content = document.getElementById("analysisContent");

    loadingState.style.display = "none";
    content.style.display = "block";

    content.innerHTML = `
      <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 40px; background: white; min-height: 300px;">
        <svg xmlns="http://www.w3.org/2000/svg" height="64px" viewBox="0 -960 960 960" width="64px" fill="#dc2626">
          <path d="M440-280h80v-240h-80v240Zm40-320q17 0 28.5-11.5T520-640q0-17-11.5-28.5T480-680q-17 0-28.5 11.5T440-640q0 17 11.5 28.5T480-600Zm0 520q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-80q134 0 227-93t93-227q0-134-93-227t-227-93q-134 0-227 93t-93 227q0 134 93 227t227 93Zm0-320Z"/>
        </svg>
        <h3 style="color: #dc2626; margin: 20px 0 10px 0;">Unable to Load Data</h3>
        <p style="color: #64748b; text-align: center; max-width: 400px; margin: 0 0 24px 0; line-height: 1.6;">${errorMessage}</p>
        <div style="display: flex; gap: 12px;">
          <button onclick="closeAnalysisModal()" style="background: #e2e8f0; color: #334155; border: none; padding: 10px 24px; border-radius: 8px; cursor: pointer; font-weight: 600;">Close</button>
          <button onclick="location.reload()" style="background: #005fb8; color: white; border: none; padding: 10px 24px; border-radius: 8px; cursor: pointer; font-weight: 600;">🔄 Refresh Page</button>
        </div>
      </div>
    `;
  }

  function renderAnalysisModal(data) {
    // Store the data for export
    currentInteractionData = data;
    console.log("Stored interaction data:", currentInteractionData);

    const loadingState = document.getElementById("analysisLoadingState");
    const content = document.getElementById("analysisContent");

    const summaryCardClass =
      data.severity_level === 2
        ? "analysis_summary_critical"
        : data.severity_level === 1
          ? "analysis_summary_moderate"
          : "analysis_summary_low";
    const severityDisplay = data.severity.toUpperCase();

    content.innerHTML = `
      <div id="analysis_root" data-report-id="${data.id}">
        <!-- Hidden input to store the ID for export -->
        <input type="hidden" id="reportIdHidden" value="${data.id}">
        
        <div id="analysis_header">
          <h3>Interaction Analysis</h3>
          <span>Detailed evaluation for multi-drug therapeutic regimen</span>
        </div>
        <div id="analysis_drugs">
          <div id="active_drugs_header">
            <span id="active_drugs_label">SELECTED SUBSTANCES</span>
            <span id="active_drugs_quantity">2 Drugs Analyzed</span>
          </div>
          <div id="active_drugs_list">
            <li>
              <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#0051f8">
                <path d="M318-120q-82 0-140-58t-58-140q0-40 15-76t43-64l134-133 56 56-134 134q-17 17-25.5 38.5T200-318q0 49 34.5 83.5T318-200q23 0 45-8.5t39-25.5l133-134 57 57-134 133q-28 28-64 43t-76 15Zm79-220-57-57 223-223 57 57-223 223Zm251-28-56-57 134-133q17-17 25-38t8-44q0-50-34-85t-84-35q-23 0-44.5 8.5T558-726L425-592l-57-56 134-134q28-28 64-43t76-15q82 0 139.5 58T839-641q0 39-14.5 75T782-502L648-368Z"/>
              </svg>
              <span class="active_drug_name">${data.drug1}</span>
            </li>
            <li>
              <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#0051f8">
                <path d="M318-120q-82 0-140-58t-58-140q0-40 15-76t43-64l134-133 56 56-134 134q-17 17-25.5 38.5T200-318q0 49 34.5 83.5T318-200q23 0 45-8.5t39-25.5l133-134 57 57-134 133q-28 28-64 43t-76 15Zm79-220-57-57 223-223 57 57-223 223Zm251-28-56-57 134-133q17-17 25-38t8-44q0-50-34-85t-84-35q-23 0-44.5 8.5T558-726L425-592l-57-56 134-134q28-28 64-43t76-15q82 0 139.5 58T839-641q0 39-14.5 75T782-502L648-368Z"/>
              </svg>
              <span class="active_drug_name">${data.drug2}</span>
            </li>
          </div>
        </div>
        <div id="analysis_summary">
          <div id="analysis_summary_left">
            <div>
              <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#0051f8">
                <path d="M400-400h160v-80H400v80Zm0-120h320v-80H400v80Zm0-120h320v-80H400v80Zm-80 400q-33 0-56.5-23.5T240-320v-480q0-33 23.5-56.5T320-880h480q33 0 56.5 23.5T880-800v480q0 33-23.5 56.5T800-240H320Zm0-80h480v-480H320v480ZM160-80q-33 0-56.5-23.5T80-160v-560h80v560h560v80H160Zm160-720v480-480Z"/>
              </svg>
              <span>INTERACTION SUMMARY</span>
            </div>
            <p>${data.description}</p>
          </div>
          <div id="analysis_summary_right">
            <div id="analysis_summary_card" class="${summaryCardClass}">
              <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="currentColor">
                <path d="M440-280h80v-240h-80v240Zm68.5-331.5Q520-623 520-640t-11.5-28.5Q497-680 480-680t-28.5 11.5Q440-657 440-640t11.5 28.5Q463-600 480-600t28.5-11.5ZM480-80q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-80q134 0 227-93t93-227q0-134-93-227t-227-93q-134 0-227 93t-93 227q0 134 93 227t227 93Zm0-320Z"/>
              </svg>
              ${severityDisplay} RISK
            </div>
          </div>
        </div>
        <div id="analysis_details">
          <div id="analysis_details_top">
            <div id="analysis_details_topleft">
              <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#EA3323">
                <path d="m40-120 440-760 440 760H40Zm138-80h604L480-720 178-200Zm330.5-51.5Q520-263 520-280t-11.5-28.5Q497-320 480-320t-28.5 11.5Q440-297 440-280t11.5 28.5Q463-240 480-240t28.5-11.5ZM440-360h80v-200h-80v200Zm40-100Z"/>
              </svg>
              <h4>Interaction Detail <span>${data.drug1} + ${data.drug2}</span></h4>
            </div>
            <div id="analysis_details_topright">
            </div>
          </div>
          <div id="analysis_details_bottom">
            <div id="analysis_details_bottomleft">
              <span>MECHANISM</span>
              <p>${data.mechanism || data.description}</p>
            </div>
            <div id="analysis_details_bottomright">
              <span>RECOMMENDATION</span>
              <p>${data.recommendation || "This program is for educational purposes. Always consult a professional physician before consuming any medication."}</p>
            </div>
          </div>
        </div>
      </div>
    `;

    loadingState.style.display = "none";
    content.style.display = "block";
  }

  function closeAnalysisModal() {
    const modal = document.getElementById("analysisModal");
    if (modal) {
      modal.style.display = "none";
      document.body.style.overflow = "";
    }
  }

  function exportAnalysisPDF() {
    console.log("=== exportAnalysisPDF called ===");

    let historyId = null;

    // Method 1: Try hidden input (most reliable)
    const hiddenInput = document.getElementById("reportIdHidden");
    if (hiddenInput && hiddenInput.value) {
      historyId = hiddenInput.value;
      console.log("Got ID from hidden input:", historyId);
    }

    // Method 2: Try data attribute on analysis_root
    if (!historyId) {
      const rootElement = document.getElementById("analysis_root");
      if (rootElement) {
        historyId = rootElement.getAttribute("data-report-id");
        console.log("Got ID from data-report-id:", historyId);
      }
    }

    // Method 3: Try from stored data
    if (!historyId && currentInteractionData && currentInteractionData.id) {
      historyId = currentInteractionData.id;
      console.log("Got ID from currentInteractionData:", historyId);
    }

    // Method 4: Try from modal content
    if (!historyId) {
      const modalContent = document.getElementById("analysisContent");
      if (modalContent) {
        const match = modalContent.innerHTML.match(/Report\s*#(\d+)/i);
        if (match) {
          historyId = match[1];
          console.log("Got ID from modal content:", historyId);
        }
      }
    }

    // Method 5: Try URL params
    if (!historyId) {
      const urlParams = new URLSearchParams(window.location.search);
      historyId = urlParams.get("id") || urlParams.get("report_id");
      console.log("Got ID from URL params:", historyId);
    }

    // Method 6: Try URL path
    if (!historyId) {
      const pathParts = window.location.pathname.split("/");
      for (let i = pathParts.length - 1; i >= 0; i--) {
        if (pathParts[i] && /^\d+$/.test(pathParts[i])) {
          historyId = pathParts[i];
          break;
        }
      }
      console.log("Got ID from URL path:", historyId);
    }

    if (!historyId) {
      alert("Could not find report ID. Please try again.");
      return;
    }

    console.log("=== Exporting PDF for ID:", historyId);

    const exportBtn = document.querySelector(
      '#analysis_details_topright a[onclick*="exportAnalysisPDF"]',
    );
    const originalText = exportBtn ? exportBtn.textContent : "EXPORT PDF";

    if (exportBtn) {
      exportBtn.textContent = "Generating...";
      exportBtn.style.opacity = "0.6";
      exportBtn.style.pointerEvents = "none";
    }

    const url = `/export/interaction/pdf/${historyId}/`;
    console.log("=== Fetching URL:", url);

    fetch(url)
      .then((response) => {
        console.log("=== Response status:", response.status);
        if (!response.ok) {
          // Try to get error message from response
          return response
            .json()
            .then((errData) => {
              console.error("=== Error response:", errData);
              throw new Error(
                errData.error ||
                  `Export failed with status: ${response.status}`,
              );
            })
            .catch(() => {
              // If not JSON, throw generic error
              throw new Error(`Export failed with status: ${response.status}`);
            });
        }
        return response.blob();
      })
      .then((blob) => {
        console.log("=== Received blob, size:", blob.size);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        const date = new Date().toISOString().split("T")[0];
        a.download = `interaction_report_${historyId}_${date}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

        if (exportBtn) {
          exportBtn.textContent = "✓ Exported!";
          setTimeout(() => {
            exportBtn.textContent = originalText;
            exportBtn.style.opacity = "1";
            exportBtn.style.pointerEvents = "auto";
          }, 2000);
        }
      })
      .catch((error) => {
        console.error("=== Export error:", error);
        if (exportBtn) {
          exportBtn.textContent = "Export Failed";
          setTimeout(() => {
            exportBtn.textContent = originalText;
            exportBtn.style.opacity = "1";
            exportBtn.style.pointerEvents = "auto";
          }, 2000);
        }
        alert(`Failed to generate PDF: ${error.message}`);
      });
  }

  // Expose functions globally
  global.loadHistoryPage = loadHistoryPage;
  global.closeAnalysisModal = closeAnalysisModal;
  global.exportAnalysisPDF = exportAnalysisPDF;
  global.showAnalysisModal = showAnalysisModal;
  global.showDatePicker = showDatePicker;
  global.closeDatePicker = closeDatePicker;
  global.applyDateFilter = applyDateFilter;
  global.clearDateFilter = clearDateFilter;
})(window);
