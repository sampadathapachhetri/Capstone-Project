(function (global) {
  global.MedicalApp = global.MedicalApp || {};
  global.MedicalApp.Pages = global.MedicalApp.Pages || {};

  global.MedicalApp.Pages.Settings = {
    init: function () {
      console.log("Settings Initialized");
      this.setupEventHandling();
    },

    setupEventHandling: function () {
      let cancel_button = document.getElementById("cancel_button");

      if (cancel_button) {
        cancel_button.addEventListener("click", async (e) => {
          e.stopPropagation();
          e.preventDefault();
          activeNav = dashboard_nav;
          await fillActivePage();
        });
      }
    },
  };
})(window);
