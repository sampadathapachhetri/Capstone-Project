(function (global) {
  global.MedicalApp = global.MedicalApp || {};
  global.MedicalApp.Pages = global.MedicalApp.Pages || {};

  global.MedicalApp.Pages.Dashboard = {
    init: function () {
      console.log("Dashboard Initialized");
      this.setupEventListeners();
      this.startAutoRefresh();
    },

    setupEventListeners: function () {},

    destroy: function () {
      console.log("Dashboard destroyed - cleaning up");
    },
  };
})(window);
