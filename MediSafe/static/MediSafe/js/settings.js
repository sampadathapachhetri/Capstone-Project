(function (global) {
  const APP = (global.MedicalApp = global.MedicalApp || {});
  APP.Pages = APP.Pages || {};

  APP.Pages.Settings = {
    overlay: null,
    confirmBtn: null,
    cancelBtn: null,
    deleteBtn: null,
    confirmInput: null,
    errorDiv: null,

    // Password change elements
    passwordOverlay: null,
    otpInput: null,
    newPasswordInput: null,
    confirmPasswordInput: null,
    confirmPasswordBtn: null,
    cancelPasswordBtn: null,
    resendOtpLink: null,
    otpError: null,
    passwordError: null,
    confirmError: null,
    resendStatus: null,

    init: function () {
      console.log("Settings Initialized");
      this.cacheElements();
      this.setupEventHandling();
      this.setupPasswordChange();
      this.setupExportButton();
    },

    cacheElements: function () {
      this.overlay = document.getElementById("deleteOverlay");
      this.confirmBtn = document.getElementById("confirmDeleteBtn");
      this.cancelBtn = document.getElementById("cancelDeleteBtn");
      this.deleteBtn = document.getElementById("delete_user_btn");
      this.confirmInput = document.getElementById("confirmDeleteInput");
      this.errorDiv = document.getElementById("deleteError");
      this.cancelButton = document.getElementById("cancel_button");

      // Password change elements
      this.passwordOverlay = document.getElementById("passwordOverlay");
      this.otpInput = document.getElementById("otpInput");
      this.newPasswordInput = document.getElementById("newPasswordInput");
      this.confirmPasswordInput = document.getElementById(
        "confirmPasswordInput",
      );
      this.confirmPasswordBtn = document.getElementById("confirmPasswordBtn");
      this.cancelPasswordBtn = document.getElementById("cancelPasswordBtn");
      this.resendOtpLink = document.getElementById("resendOtpLink");
      this.otpError = document.getElementById("otpError");
      this.passwordError = document.getElementById("passwordError");
      this.confirmError = document.getElementById("confirmError");
      this.resendStatus = document.getElementById("resendStatus");
    },

    // Helper to get user email from the input field
    getUserEmail: function () {
      const emailInput = document.querySelector('input[name="email"]');
      if (emailInput) {
        return emailInput.value || emailInput.placeholder || "";
      }
      return "";
    },

    // ========== DELETE ACCOUNT FUNCTIONS ==========

    enableOverlay: function () {
      this.overlay.classList.add("active");
      this.confirmInput.value = "";
      this.confirmInput.focus();
      this.confirmBtn.disabled = true;
      this.errorDiv.textContent = "";
    },

    disableOverlay: function () {
      this.overlay.classList.remove("active");
      this.confirmInput.value = "";
      this.confirmBtn.disabled = true;
      this.errorDiv.textContent = "";
    },

    handleCancelNavigation: async function (e) {
      e.stopPropagation();
      e.preventDefault();
      const pageName = navToPageMap[activeNav.id].pageName.toLowerCase();
      const url = new URL(window.location.href);
      url.searchParams.set("page", pageName);
      window.history.pushState({}, "", url);
      await fillActivePage();
    },

    handleDeleteConfirm: function () {
      if (this.confirmInput.value.toLowerCase() !== "delete") {
        this.errorDiv.textContent = "Please type DELETE to confirm";
        return;
      }

      fetch("/delete_account/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")
            .value,
        },
        body: JSON.stringify({}),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            alert("Account deleted successfully!");
            this.disableOverlay();
            window.location.href = "/logout/";
          } else {
            this.errorDiv.textContent =
              data.message || "Failed to delete account";
          }
        })
        .catch((error) => {
          this.errorDiv.textContent = "An error occurred. Please try again.";
          console.error("Delete error:", error);
        });
    },

    handleInputChange: function () {
      const isMatch = this.confirmInput.value.toUpperCase() === "DELETE";
      this.confirmBtn.disabled = !isMatch;
      if (isMatch) this.errorDiv.textContent = "";
    },

    // ========== PASSWORD CHANGE FUNCTIONS ==========

    setupPasswordChange: function () {
      // Find the "Change Password" button
      const changePasswordBtn = document.querySelector(
        "#security_chpassword_div button",
      );
      if (changePasswordBtn) {
        changePasswordBtn.addEventListener("click", () => {
          this.showPasswordDialog();
        });
      }

      // Cancel button
      if (this.cancelPasswordBtn) {
        this.cancelPasswordBtn.addEventListener("click", () => {
          this.closePasswordDialog();
        });
      }

      // Confirm button
      if (this.confirmPasswordBtn) {
        this.confirmPasswordBtn.addEventListener("click", () => {
          this.handlePasswordChange();
        });
      }

      // Resend OTP link
      if (this.resendOtpLink) {
        this.resendOtpLink.addEventListener("click", (e) => {
          e.preventDefault();
          this.handleResendOTP();
        });
      }

      // Enter key support
      if (this.confirmPasswordInput) {
        this.confirmPasswordInput.addEventListener("keydown", (e) => {
          if (e.key === "Enter") {
            this.handlePasswordChange();
          }
        });
      }

      // Real-time validation on password fields
      if (this.newPasswordInput) {
        this.newPasswordInput.addEventListener("input", () => {
          this.validatePassword();
        });
      }

      if (this.confirmPasswordInput) {
        this.confirmPasswordInput.addEventListener("input", () => {
          this.validatePassword();
        });
      }

      // Close on Escape
      document.addEventListener("keydown", (e) => {
        if (
          e.key === "Escape" &&
          this.passwordOverlay?.classList.contains("active")
        ) {
          this.closePasswordDialog();
        }
      });

      // Close on outside click
      if (this.passwordOverlay) {
        this.passwordOverlay.addEventListener("click", (e) => {
          if (e.target === this.passwordOverlay) {
            this.closePasswordDialog();
          }
        });
      }
    },

    showPasswordDialog: function () {
      if (!this.passwordOverlay) return;
      this.passwordOverlay.classList.add("active");
      this.clearErrors();
      this.otpInput.value = "";
      this.newPasswordInput.value = "";
      this.confirmPasswordInput.value = "";
      this.confirmPasswordBtn.disabled = false;
      this.confirmPasswordBtn.textContent = "Update Password";
      this.resendStatus.textContent = "";
      this.otpInput.focus();
    },

    closePasswordDialog: function () {
      if (!this.passwordOverlay) return;
      this.passwordOverlay.classList.remove("active");
      this.clearErrors();
      this.resendStatus.textContent = "";
    },

    clearErrors: function () {
      if (this.otpError) this.otpError.textContent = "";
      if (this.passwordError) this.passwordError.textContent = "";
      if (this.confirmError) this.confirmError.textContent = "";
      [this.otpInput, this.newPasswordInput, this.confirmPasswordInput].forEach(
        (input) => {
          if (input) input.classList.remove("error");
        },
      );
    },

    validatePassword: function () {
      const password = this.newPasswordInput?.value || "";
      const confirm = this.confirmPasswordInput?.value || "";
      let isValid = true;

      // Password validation
      if (password.length > 0 && password.length < 8) {
        this.passwordError.textContent =
          "Password must be at least 8 characters";
        this.newPasswordInput.classList.add("error");
        isValid = false;
      } else {
        this.passwordError.textContent = "";
        this.newPasswordInput.classList.remove("error");
      }

      // Confirm password validation
      if (confirm.length > 0 && confirm !== password) {
        this.confirmError.textContent = "Passwords do not match";
        this.confirmPasswordInput.classList.add("error");
        isValid = false;
      } else {
        this.confirmError.textContent = "";
        this.confirmPasswordInput.classList.remove("error");
      }

      return isValid;
    },

    handlePasswordChange: async function () {
      // Validate passwords
      if (!this.validatePassword()) {
        return;
      }

      const email = this.getUserEmail();
      const otp = this.otpInput?.value || "";
      const password = this.newPasswordInput?.value || "";

      // Validate email
      if (!email || email === "") {
        this.otpError.textContent = "Email not found. Please refresh the page.";
        return;
      }

      // Validate OTP
      if (otp.length !== 5) {
        this.otpError.textContent = "Please enter a valid 6-digit OTP";
        this.otpInput.classList.add("error");
        return;
      }

      // Disable button and show loading
      this.confirmPasswordBtn.disabled = true;
      this.confirmPasswordBtn.textContent = "Updating...";
      this.clearErrors();

      try {
        const csrfToken = document.querySelector(
          '[name="csrfmiddlewaretoken"]',
        )?.value;

        const response = await fetch("/api/requestPassReset", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({
            email: email,
            otp: otp,
            password: password,
          }),
        });

        const data = await response.json();

        if (data.error) {
          // Show error
          if (
            data.error.toLowerCase().includes("otp") ||
            data.error.toLowerCase().includes("code")
          ) {
            this.otpError.textContent = data.error;
            this.otpInput.classList.add("error");
          } else if (data.error.toLowerCase().includes("password")) {
            this.passwordError.textContent = data.error;
            this.newPasswordInput.classList.add("error");
          } else {
            this.otpError.textContent = data.error;
          }
          this.confirmPasswordBtn.disabled = false;
          this.confirmPasswordBtn.textContent = "Update Password";
        } else {
          this.showSuccessAndRedirect();
        }
      } catch (error) {
        console.error("Error changing password:", error);
        this.otpError.textContent = "An error occurred. Please try again.";
        this.confirmPasswordBtn.disabled = false;
        this.confirmPasswordBtn.textContent = "Update Password";
      }
    },

    showSuccessAndRedirect: function () {
      // Show success message
      const formGroup = this.otpInput?.closest(".form-group");
      if (formGroup) {
        const successDiv = document.createElement("div");
        successDiv.className = "success-message";
        successDiv.innerHTML = `
          <svg xmlns="http://www.w3.org/2000/svg" height="20px" viewBox="0 -960 960 960" width="20px" fill="#16a34a">
            <path d="M424-296 282-438l56-56 86 86 198-198 56 56-254 254Zm56 216q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-80q134 0 227-93t93-227q0-134-93-227t-227-93q-134 0-227 93t-93 227q0 134 93 227t227 93Zm0-320Z"/>
          </svg>
          Password changed successfully! Redirecting to login...
        `;
        formGroup.parentNode.insertBefore(successDiv, formGroup.nextSibling);
      }

      this.confirmPasswordBtn.textContent = "Success!";

      // Redirect to logout after 2 seconds
      setTimeout(() => {
        window.location.href = "/logout/";
      }, 2000);
    },

    handleResendOTP: async function () {
      const email = this.getUserEmail();

      if (!email || email === "") {
        this.resendStatus.textContent =
          "Email not found. Please refresh the page.";
        this.resendStatus.className = "resend-status error";
        return;
      }

      this.resendStatus.textContent = "Sending...";
      this.resendStatus.className = "resend-status";

      try {
        const csrfToken = document.querySelector(
          '[name="csrfmiddlewaretoken"]',
        )?.value;

        const response = await fetch("/api/requestotp", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({
            email: email,
          }),
        });

        const data = await response.json();

        if (data.error) {
          this.resendStatus.textContent = data.error;
          this.resendStatus.className = "resend-status error";
        } else {
          this.resendStatus.textContent = "✓ OTP sent successfully!";
          this.resendStatus.className = "resend-status";
          this.otpError.textContent = "";
          this.otpInput.classList.remove("error");

          setTimeout(() => {
            this.resendStatus.textContent = "";
          }, 5000);
        }
      } catch (error) {
        console.error("Error resending OTP:", error);
        this.resendStatus.textContent = "Failed to send OTP. Please try again.";
        this.resendStatus.className = "resend-status error";
      }
    },

    // ========== EVENT HANDLING ==========

    setupEventHandling: function () {
      // Cancel navigation
      if (this.cancelButton) {
        this.cancelButton.addEventListener(
          "click",
          this.handleCancelNavigation.bind(this),
        );
      }

      // Delete button triggers overlay
      if (this.deleteBtn) {
        this.deleteBtn.addEventListener("click", this.enableOverlay.bind(this));
      }

      // Confirm button
      if (this.confirmBtn) {
        this.confirmBtn.addEventListener(
          "click",
          this.handleDeleteConfirm.bind(this),
        );
      }

      // Cancel button
      if (this.cancelBtn) {
        this.cancelBtn.addEventListener(
          "click",
          this.disableOverlay.bind(this),
        );
      }

      // Click outside to close
      if (this.overlay) {
        this.overlay.addEventListener("click", (e) => {
          if (e.target === this.overlay) this.disableOverlay();
        });
      }

      // Escape key
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && this.overlay?.classList.contains("active")) {
          this.disableOverlay();
        }
      });

      // Input validation
      if (this.confirmInput) {
        this.confirmInput.addEventListener(
          "input",
          this.handleInputChange.bind(this),
        );
      }
    },

    // Add this method to the Settings object
    setupExportButton: function () {
      const exportBtn = document.querySelector("#privacy_export_div button");
      if (exportBtn) {
        exportBtn.addEventListener("click", (e) => {
          e.preventDefault();
          this.exportCombinedPDF();
        });
      }
    },

    exportCombinedPDF: function () {
      const exportBtn = document.querySelector("#privacy_export_div button");
      const originalText = exportBtn.innerHTML;

      // Show loading state
      exportBtn.innerHTML =
        '<span style="display:flex;align-items:center;gap:8px;"><div class="loading-spinner-small"></div> Generating PDF...</span>';
      exportBtn.disabled = true;

      fetch("/export/combined/pdf/")
        .then((response) => {
          if (!response.ok) {
            throw new Error("Export failed");
          }
          return response.blob();
        })
        .then((blob) => {
          // Create download link
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          const date = new Date().toISOString().split("T")[0];
          a.download = `complete_export_${date}.pdf`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          a.remove();

          // Reset button
          exportBtn.innerHTML = originalText;
          exportBtn.disabled = false;
        })
        .catch((error) => {
          console.error("Export error:", error);
          exportBtn.innerHTML = originalText;
          exportBtn.disabled = false;
          alert("Failed to generate PDF. Please try again.");
        });
    },
  };
})(window);
