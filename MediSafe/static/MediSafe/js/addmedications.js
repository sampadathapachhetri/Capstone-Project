(function (global) {
  global.MedicalApp = global.MedicalApp || {};
  global.MedicalApp.Pages = global.MedicalApp.Pages || {};
  // addedd this as namespace
  global.MedicalApp.Pages.AddMedications = {
    // called upon load
    init: function () {
      console.log("AddMedications Initialized");
      this.setupEventListeners();
    },
    sendPostRequest: async function (
      medName,
      dosageUnit,
      dosageValue,
      dosageFreq,
      medMore,
    ) {
      try {
        const csrfToken = document.querySelector(
          '[name="csrfmiddlewaretoken"]',
        )?.value;
        const response = await fetch(`sub/addmedications`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({
            medication_name: medName,
            dosage_unit: dosageUnit,
            dosage_value: dosageValue,
            dosage_frequency: dosageFreq,
            medication_more: medMore,
          }),
        });

        const data = await response.json();
        console.log(data);
        return data.error;
      } catch (error) {
        console.error("Error:", error);
        return error;
      }
    },
    setupEventListeners: function () {
      submit_btn = document.getElementById("submit_btn");

      submit_btn.addEventListener("click", async (e) => {
        temperror = document.getElementById("temperror");
        if (temperror != null) {
          temperror.remove();
        }
        medName = document.getElementsByName("medication_name")[0].value;
        dosageUnit = document.getElementsByName("dosage_unit")[0].value;
        dosageValue = document.getElementsByName("dosage_value")[0].value;
        dosageFreq = document.getElementsByName("dosage_frequency")[0].value;
        medMore = document.getElementsByName("medication_more")[0].value;
        bottom_buttons = document.getElementById("bottom_buttons");
        addmeds_form = document.getElementById("addmeds_form");
        error = await this.sendPostRequest(
          medName,
          dosageUnit,
          dosageValue,
          dosageFreq,
          medMore,
        );
        if (error != null) {
          bottom_buttons.insertAdjacentHTML(
            "afterbegin",
            `
            <span style="color:red;width:70% " id="temperror">${error}</span>
            `,
          );
          addmeds_form.classList.add("shake");
          setTimeout(() => {
            addmeds_form.classList.remove("shake");
          }, 500);
        } else {
          location.reload();
        }
      });
    },
  };
})(window);
