(function (global) {
  global.MedicalApp = global.MedicalApp || {};
  global.MedicalApp.Pages = global.MedicalApp.Pages || {};

  // Store current interaction data for export
  let currentInteractionData = null;

  global.MedicalApp.Pages.IntAnalysis = {
    init: function () {
      console.log("Interaction Analysis Initialized");
      this.setupCopyButton();
      this.setupExportButton();
      // Store the data from the template
      this.storeDataFromTemplate();
    },

    storeDataFromTemplate: function () {
      // Extract data from the rendered template
      const drug1Element = document.querySelector(".active_drug_name");
      const drug2Element = document.querySelectorAll(".active_drug_name")[1];
      const severityElement = document.querySelector("#analysis_summary_card");
      const descriptionElement = document.querySelector(
        "#analysis_summary_left p",
      );
      const mechanismElement = document.querySelector("#analysis_mechanism");

      // Get severity level from class
      let severityLevel = 0;
      const summaryCard = document.getElementById("analysis_summary_card");
      if (summaryCard) {
        if (summaryCard.classList.contains("analysis_summary_critical")) {
          severityLevel = 2;
        } else if (
          summaryCard.classList.contains("analysis_summary_moderate")
        ) {
          severityLevel = 1;
        }
      }

      // Get severity text
      let severity = "low";
      if (severityElement) {
        const severityText = severityElement.textContent.trim();
        if (
          severityText.toLowerCase().includes("high") ||
          severityText.toLowerCase().includes("critical")
        ) {
          severity = "high";
        } else if (severityText.toLowerCase().includes("moderate")) {
          severity = "moderate";
        } else if (severityText.toLowerCase().includes("low")) {
          severity = "low";
        }
      }

      // Get report ID from URL or data attribute
      const urlParams = new URLSearchParams(window.location.search);
      const reportId = urlParams.get("id") || urlParams.get("report_id") || "1";

      currentInteractionData = {
        id: parseInt(reportId),
        drug1: drug1Element ? drug1Element.textContent.trim() : "Unknown",
        drug2: drug2Element ? drug2Element.textContent.trim() : "Unknown",
        severity: severity,
        severity_level: severityLevel,
        description: descriptionElement
          ? descriptionElement.textContent.trim()
          : "No description available.",
        mechanism: mechanismElement
          ? mechanismElement.textContent.trim()
          : "No mechanism available.",
      };

      console.log("Stored interaction data:", currentInteractionData);
    },

    setupCopyButton: function () {
      const copyBtn = document.getElementById("copy_button");
      if (copyBtn) {
        copyBtn.addEventListener("click", (e) => {
          e.preventDefault();
          this.copyFindingsToClipboard();
        });
      }
    },

    setupExportButton: function () {
      const exportBtn = document.getElementById("export_button");
      if (exportBtn) {
        exportBtn.addEventListener("click", (e) => {
          e.preventDefault();
          this.exportAnalysisPDF();
        });
      }
    },

    copyFindingsToClipboard: function () {
      const data = currentInteractionData;

      if (!data || !data.id) {
        alert("No interaction data found to copy.");
        return;
      }

      // Format as CSV: drug1, drug2, severity, description
      const csvLine = `"${data.drug1}","${data.drug2}","${data.severity.toUpperCase()}","${data.description || "No description"}"`;

      // Also create a human-readable formatted version
      const formattedText = `
        Drug Interaction Report
        ------------------------
        Drug 1: ${data.drug1}
        Drug 2: ${data.drug2}
        Severity: ${data.severity.toUpperCase()}
        Description: ${data.description || "No description available."}
        Mechanism: ${data.mechanism || "No mechanism available."}
      `.trim();

      // Copy both formats to clipboard
      const textToCopy = `${formattedText}\n\n--- CSV Format ---\n${csvLine}`;

      navigator.clipboard
        .writeText(textToCopy)
        .then(() => {
          // Show success feedback on the button
          const copyBtn = document.getElementById("copy_button");
          if (copyBtn) {
            const originalText = copyBtn.textContent;
            copyBtn.textContent = "✓ COPIED!";
            setTimeout(() => {
              copyBtn.textContent = originalText;
            }, 2000);
          }
        })
        .catch(() => {
          // Fallback
          alert(
            "Failed to copy. Please select and copy manually.\n\n" + textToCopy,
          );
        });
    },

    exportAnalysisPDF: function () {
      // ... get historyId ...

      const exportBtn = document.getElementById("export_button");
      const originalText = exportBtn ? exportBtn.textContent : "EXPORT PDF";

      if (exportBtn) {
        exportBtn.textContent = "Generating...";
        exportBtn.style.opacity = "0.6";
        exportBtn.style.pointerEvents = "none";
      }

      // Add a timeout to the fetch
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

      const url = `/export/interaction/pdf/${historyId}/`;
      console.log("Fetching URL:", url);

      fetch(url, { signal: controller.signal })
        .then((response) => {
          clearTimeout(timeoutId);
          console.log("Response status:", response.status);
          if (!response.ok) {
            throw new Error(`Export failed with status: ${response.status}`);
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
          clearTimeout(timeoutId);
          console.error("Export error:", error);
          if (error.name === "AbortError") {
            alert("Export took too long. Please try again.");
          } else {
            alert(`Failed to generate PDF: ${error.message}`);
          }
          if (exportBtn) {
            exportBtn.textContent = "Export Failed";
            setTimeout(() => {
              exportBtn.textContent = originalText;
              exportBtn.style.opacity = "1";
              exportBtn.style.pointerEvents = "auto";
            }, 2000);
          }
        })
        .finally(() => {
          this._isExporting = false;
        });
    },
  };
})(window);
