(function (global) {
  global.MedicalApp = global.MedicalApp || {};
  global.MedicalApp.Pages = global.MedicalApp.Pages || {};
  // addedd this as namespace
  global.MedicalApp.Pages.History = {
    // called upon load
    init: function () {
      console.log("History Initialized");
    },
  };
})(window);
