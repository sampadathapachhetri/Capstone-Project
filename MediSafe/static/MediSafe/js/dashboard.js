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

    startAutoRefresh: function () {
      this._refreshInterval = setInterval(() => {
        console.log("Auto refreshing dashboard...");
        this.loadData();
      }, 30000);
    },

    destroy: function () {
      console.log("Dashboard destroyed - cleaning up");

    },
  };
})(window);
