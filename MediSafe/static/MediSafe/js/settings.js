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

    init: function () {
      console.log("Settings Initialized");
      this.cacheElements();
      this.setupEventHandling();
    },

    cacheElements: function () {
      this.overlay = document.getElementById("deleteOverlay");
      this.confirmBtn = document.getElementById("confirmDeleteBtn");
      this.cancelBtn = document.getElementById("cancelDeleteBtn");
      this.deleteBtn = document.getElementById("delete_user_btn");
      this.confirmInput = document.getElementById("confirmDeleteInput");
      this.errorDiv = document.getElementById("deleteError");
      this.cancelButton = document.getElementById("cancel_button");
    },

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
      // Assuming these are defined globally
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

    setupEventHandling: function () {
      // Cancel navigation
      if (this.cancelButton) {
        this.cancelButton.addEventListener(
          "click",
          this.handleCancelNavigation.bind(this),
        );
      }

      // Delete button triggers overlay
      this.deleteBtn.addEventListener("click", this.enableOverlay.bind(this));

      // Confirm button
      this.confirmBtn.addEventListener(
        "click",
        this.handleDeleteConfirm.bind(this),
      );

      // Cancel button
      this.cancelBtn.addEventListener("click", this.disableOverlay.bind(this));

      // Click outside to close
      this.overlay.addEventListener("click", (e) => {
        if (e.target === this.overlay) this.disableOverlay();
      });

      // Escape key
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && this.overlay.classList.contains("active")) {
          this.disableOverlay();
        }
      });

      // Input validation
      this.confirmInput.addEventListener(
        "input",
        this.handleInputChange.bind(this),
      );
    },
  };
})(window);
