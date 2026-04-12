(function (global) {
  global.MedicalApp = global.MedicalApp || {};
  global.MedicalApp.Pages = global.MedicalApp.Pages || {};
  // addedd this as namespace
  global.MedicalApp.Pages.AddMedications = {
    // called upon load
    init: function () {
      console.log("AddMedications Initialized");
    },
  };
})(window);
