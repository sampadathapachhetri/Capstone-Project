(function (global) {
  global.MedicalApp = global.MedicalApp || {};
  global.MedicalApp.Pages = global.MedicalApp.Pages || {};

  global.MedicalApp.Pages.Dashboard = {
    init: function () {
      console.log("Dashboard Initialized");
      this.setupEventHandling();
    },

    setupEventHandling: function () {
      let dash_history_button = document.getElementById("dash_history_button");
      let dash_new_button = document.getElementById("dash_new_button");
      let view_all_button = document.getElementById("view_all_button");

      view_all_button.addEventListener("click", async (e) => {
        e.stopPropagation();
        e.preventDefault();
        activeNav = history_nav;
        await fillActivePage();
      });

      if (dash_history_button) {
        dash_history_button.addEventListener("click", async (e) => {
          e.stopPropagation();
          e.preventDefault();
          activeNav = history_nav;
          await fillActivePage();
        });
      }
      if (dash_new_button) {
        dash_new_button.addEventListener("click", async (e) => {
          e.stopPropagation();
          e.preventDefault();
          activeNav = drugcheck_nav;
          await fillActivePage();
        });
      }
    },
  };
})(window);
