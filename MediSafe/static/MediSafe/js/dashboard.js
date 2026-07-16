(function (global) {
  global.MedicalApp = global.MedicalApp || {};
  global.MedicalApp.Pages = global.MedicalApp.Pages || {};

  // Store current interaction data for export
  let currentInteractionData = null;

  global.MedicalApp.Pages.Dashboard = {
    init: function () {
      console.log("Dashboard Initialized");
      this.setupEventHandling();
      this.setupEyeIcons();
    },

    setupEventHandling: function () {
      let dash_history_button = document.getElementById("dash_history_button");
      let dash_new_button = document.getElementById("dash_new_button");
      let view_all_button = document.getElementById("view_all_button");

      if (view_all_button) {
        view_all_button.addEventListener("click", async (e) => {
          e.stopPropagation();
          e.preventDefault();
          if (
            typeof activeNav !== "undefined" &&
            typeof history_nav !== "undefined"
          ) {
            activeNav = history_nav;
            if (typeof fillActivePage === "function") {
              await fillActivePage();
            }
          }
        });
      }

      if (dash_history_button) {
        dash_history_button.addEventListener("click", async (e) => {
          e.stopPropagation();
          e.preventDefault();
          if (
            typeof activeNav !== "undefined" &&
            typeof history_nav !== "undefined"
          ) {
            activeNav = history_nav;
            if (typeof fillActivePage === "function") {
              await fillActivePage();
            }
          }
        });
      }

      if (dash_new_button) {
        dash_new_button.addEventListener("click", async (e) => {
          e.stopPropagation();
          e.preventDefault();
          if (
            typeof activeNav !== "undefined" &&
            typeof drugcheck_nav !== "undefined"
          ) {
            activeNav = drugcheck_nav;
            if (typeof fillActivePage === "function") {
              await fillActivePage();
            }
          }
        });
      }

      // Close modal when clicking outside
      document.addEventListener("click", function (e) {
        const modal = document.getElementById("analysisModal");
        if (e.target === modal) {
          closeAnalysisModal();
        }
      });

      // Close modal with Escape key
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") {
          closeAnalysisModal();
        }
      });
    },

    setupEyeIcons: function () {
      document.addEventListener("click", function (e) {
        const eyeIcon = e.target.closest(".dash_li_eye");
        if (eyeIcon) {
          e.preventDefault();
          e.stopPropagation();

          // Get the report ID
          const reportId = eyeIcon.getAttribute("data-report-id") || "1";

          // Find the list item to get basic data
          const listItem = eyeIcon.closest(".dash_recent_li");
          if (listItem) {
            // Extract drug names
            const drugNamesElement = listItem.querySelector(".dash_drug_names");
            let drugNames = "Unknown + Unknown";
            if (drugNamesElement) {
              drugNames = drugNamesElement.textContent.trim();
            }

            const drugs = drugNames.split("+").map((d) => d.trim());
            const drug1 = drugs[0] || "Unknown";
            const drug2 = drugs[1] || "Unknown";

            // Get severity from class
            const interactionDiv = listItem.querySelector(
              '[class*="dash_drug_interaction_"]',
            );
            let severity = "low";
            if (interactionDiv) {
              const classes = interactionDiv.className.split(" ");
              for (let cls of classes) {
                if (cls.startsWith("dash_drug_interaction_")) {
                  severity = cls.replace("dash_drug_interaction_", "");
                  break;
                }
              }
            }

            // Get description from data attribute
            const description =
              listItem.getAttribute("data-description") ||
              "No description available.";

            // Show the modal with loading state
            showAnalysisModal(reportId, drug1, drug2, severity, description);
          }
        }
      });
    },
  };

  // Show the analysis modal
  function showAnalysisModal(reportId, drug1, drug2, severity, description) {
    const modal = document.getElementById("analysisModal");
    const loadingState = document.getElementById("analysisLoadingState");
    const content = document.getElementById("analysisContent");

    // Show modal
    modal.style.display = "flex";
    document.body.style.overflow = "hidden";

    // Show loading, hide content
    loadingState.style.display = "flex";
    content.style.display = "none";

    // Fetch data from server
    fetchInteractionData(reportId, drug1, drug2, severity, description);
  }

  // Fetch interaction data from API
  function fetchInteractionData(reportId, drug1, drug2, severity, description) {
    // Make the actual API call
    fetch(`/api/gethistory/${reportId}`)
      .then((response) => response.json())
      .then((data) => {
        // Check if there's an error in the response
        if (data.error) {
          // Show error dialog
          showErrorDialog(data.error);
          return;
        }

        // Success - render the analysis
        renderAnalysisModal(data);
      })
      .catch((error) => {
        console.error("Error fetching interaction details:", error);
        // Show error dialog for network errors
        showErrorDialog(
          "Unable to load interaction details. Please check your connection and try again.",
        );
      });
  }

  // Show error dialog
  function showErrorDialog(errorMessage) {
    const loadingState = document.getElementById("analysisLoadingState");
    const content = document.getElementById("analysisContent");

    // Hide loading, show error
    loadingState.style.display = "none";
    content.style.display = "block";

    content.innerHTML = `
      <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 60px 40px;
        background: white;
        min-height: 300px;
      ">
        <svg xmlns="http://www.w3.org/2000/svg" height="64px" viewBox="0 -960 960 960" width="64px" fill="#dc2626">
          <path d="M440-280h80v-240h-80v240Zm40-320q17 0 28.5-11.5T520-640q0-17-11.5-28.5T480-680q-17 0-28.5 11.5T440-640q0 17 11.5 28.5T480-600Zm0 520q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-80q134 0 227-93t93-227q0-134-93-227t-227-93q-134 0-227 93t-93 227q0 134 93 227t227 93Zm0-320Z"/>
        </svg>
        <h3 style="color: #dc2626; margin: 20px 0 10px 0;">Unable to Load Data</h3>
        <p style="color: #64748b; text-align: center; max-width: 400px; margin: 0 0 24px 0; line-height: 1.6;">
          ${errorMessage}
        </p>
        <div style="display: flex; gap: 12px;">
          <button onclick="closeAnalysisModal()" style="
            background: #e2e8f0;
            color: #334155;
            border: none;
            padding: 10px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.2s;
          ">
            Close
          </button>
          <button onclick="location.reload()" style="
            background: #005fb8;
            color: white;
            border: none;
            padding: 10px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.2s;
          ">
            🔄 Refresh Page
          </button>
        </div>
      </div>
    `;
  }

  // Helper function to get mechanism based on severity (fallback)
  function getMechanism(severity) {
    const mechanisms = {
      high: "These drugs have a significant interaction that can lead to serious adverse effects. They may compete for the same metabolic pathways or have synergistic effects that amplify their actions. Close monitoring and dose adjustment are strongly recommended.",
      moderate:
        "These drugs may interact and cause moderate effects. They might affect each other's absorption, distribution, or metabolism. Patients should be monitored for potential side effects.",
      low: "These drugs have a mild interaction. While they may affect each other to some degree, the clinical significance is usually minimal. However, patients should still be aware of potential effects.",
    };
    return mechanisms[severity] || mechanisms["low"];
  }

  // Render the analysis content
  function renderAnalysisModal(data) {
    // Store the data for export
    currentInteractionData = data;

    const loadingState = document.getElementById("analysisLoadingState");
    const content = document.getElementById("analysisContent");

    // Build the HTML
    const severityClass =
      data.severity_level === 2
        ? "analysis_details_high"
        : data.severity_level === 1
          ? "analysis_details_medium"
          : "analysis_details_low";

    const summaryCardClass =
      data.severity_level === 2
        ? "analysis_summary_critical"
        : data.severity_level === 1
          ? "analysis_summary_moderate"
          : "analysis_summary_low";

    const severityDisplay = data.severity.toUpperCase();

    content.innerHTML = `
      <div id="analysis_root">
        <!-- Header -->
        <div id="analysis_header">
          <h3>Interaction Analysis</h3>
          <span>Detailed evaluation for multi-drug therapeutic regimen</span>
        </div>
        
        <!-- Drugs -->
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
        
        <!-- Summary -->
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
        
        <!-- Details -->
        <div id="analysis_details">
          <div id="analysis_details_top">
            <div id="analysis_details_topleft">
              <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#EA3323">
                <path d="m40-120 440-760 440 760H40Zm138-80h604L480-720 178-200Zm330.5-51.5Q520-263 520-280t-11.5-28.5Q497-320 480-320t-28.5 11.5Q440-297 440-280t11.5 28.5Q463-240 480-240t28.5-11.5ZM440-360h80v-200h-80v200Zm40-100Z"/>
              </svg>
              <h4>
                Interaction Detail
                <span>${data.drug1} + ${data.drug2}</span>
              </h4>
            </div>
            <div id="analysis_details_topright">
              <a href="#" onclick="exportAnalysisPDF()">EXPORT PDF</a>
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

    // Hide loading, show content
    loadingState.style.display = "none";
    content.style.display = "block";
  }

  // Close the modal
  function closeAnalysisModal() {
    const modal = document.getElementById("analysisModal");
    if (modal) {
      modal.style.display = "none";
      document.body.style.overflow = "";
    }
  }

  function copyAnalysisData() {
    const content = document.getElementById("analysisContent");
    if (content) {
      const text = content.innerText;
      navigator.clipboard
        .writeText(text)
        .then(() => {
          const btn = document.querySelector('[onclick="copyAnalysisData()"]');
          if (btn) {
            const originalText = btn.textContent;
            btn.textContent = "✓ COPIED!";
            setTimeout(() => {
              btn.textContent = originalText;
            }, 2000);
          }
        })
        .catch(() => {
          alert("Failed to copy. Please select and copy manually.");
        });
    }
  }

  function exportAnalysisPDF() {
    // Use the stored data
    const data = currentInteractionData;

    if (!data || !data.id) {
      alert(
        "No interaction data found to export. Please reload the modal and try again.",
      );
      return;
    }

    const historyId = data.id;
    const exportBtn = document.querySelector(
      '#analysis_details_topright a[onclick*="exportAnalysisPDF"]',
    );
    const originalText = exportBtn ? exportBtn.textContent : "EXPORT PDF";

    if (exportBtn) {
      exportBtn.textContent = "Generating...";
      exportBtn.style.opacity = "0.6";
      exportBtn.style.pointerEvents = "none";
    }

    fetch(`/export/interaction/pdf/${historyId}/`)
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
        console.error("Export error:", error);
        if (exportBtn) {
          exportBtn.textContent = "Export Failed";
          setTimeout(() => {
            exportBtn.textContent = originalText;
            exportBtn.style.opacity = "1";
            exportBtn.style.pointerEvents = "auto";
          }, 2000);
        }
        alert("Failed to generate PDF. Please try again.");
      });
  }

  // Expose functions globally
  global.showAnalysisModal = showAnalysisModal;
  global.closeAnalysisModal = closeAnalysisModal;
  global.copyAnalysisData = copyAnalysisData;
  global.exportAnalysisPDF = exportAnalysisPDF;
  global.fetchInteractionData = fetchInteractionData;
  global.renderAnalysisModal = renderAnalysisModal;
  global.showErrorDialog = showErrorDialog;
})(window);
