(function (global) {
  global.MedicalApp = global.MedicalApp || {};
  global.MedicalApp.Pages = global.MedicalApp.Pages || {};
  global.MedicalApp.Pages.DrugCheck = {
    drugs: new Map(),
    maxCards: 2,
    init: function () {
      console.log("DrugCheck Initialized");
      totalCards = document.querySelectorAll(".drug_choosen_card").length;
      if (totalCards == 0) {
        this.forNoInsertedCard();
      }
      this.setupEventHandling();
    },
    forNoInsertedCard: function () {
      let drug_cards_container = document.getElementById(
        "drug_cards_container",
      );
      this.drugs.clear();
      drug_cards_container.style.display = "flex";
      drug_cards_container.style.justifyContent = "center";
      drug_cards_container.style.alignItems = "center";

      drug_cards_container.innerHTML = `
        <span style="color:#616161;"> No Drug Added. Add using the box above</span>
      `;
      this.forDisableInteractionButton();
      this.forEnableValidationButton();
    },
    forYesIntertedCard: function () {
      let drug_cards_container = document.getElementById(
        "drug_cards_container",
      );
      drug_cards_container.innerHTML = null;
    },
    forEnableInteractionButton: function () {
      let drug_check_button = document.getElementById("drug_check_button");
      drug_check_button.removeAttribute("disabled");
    },
    forDisableInteractionButton: function () {
      let drug_check_button = document.getElementById("drug_check_button");
      drug_check_button.setAttribute("disabled", "");
    },
    forEnableValidationButton: function () {
      let confirm_drug_button = document.getElementById("confirm_drug_button");
      confirm_drug_button.removeAttribute("disabled");
    },
    forDisablingValidationButton: function () {
      let confirm_drug_button = document.getElementById("confirm_drug_button");
      confirm_drug_button.setAttribute("disabled", "");
    },

    getTotalCards: function () {
      totalCards = document.querySelectorAll(".drug_choosen_card").length;
      return totalCards;
    },
    showInvalidInputError: function (msg) {
      this.removeInvalidInputError();
      let drugnameInputBox = document.getElementById("drugnameInputBox");
      drugnameInputBox.value = "";
      drugnameInputBox.classList.add("shake");
      setTimeout(() => {
        drugnameInputBox.classList.remove("shake");
      }, 500);
      let drug_check_input_extra = document.getElementById(
        "drug_check_input_extra",
      );
      drug_check_input_extra.insertAdjacentHTML(
        "beforeend",
        `
        <span style="color:#ff0000"; id="temperrormsg">${msg}</span>
        `,
      );
    },
    removeInvalidInputError: function () {
      let cont = document.getElementById("temperrormsg");
      if (cont != null) {
        cont.remove();
      }
    },

    addDrug: function (commonname, drugbankId, drugsynonym) {
      if (this.drugs.size >= this.maxCards) {
        this.showInvalidInputError("Maximum 2 drugs allowed");
        return false;
      }
      if (this.drugs.has(commonname)) {
        this.showInvalidInputError(`${commonname} is already added`);
        return false;
      }
      for (let [key, value] of this.drugs) {
        if (value.drugbankId == drugbankId) {
          this.showInvalidInputError("This drug is already added");
          return false;
        }
      }
      this.drugs.set(commonname, drugbankId);

      drug_cards_container.insertAdjacentHTML(
        "afterbegin",
        `
            <div class="drug_choosen_card"
              data-drug-name="${commonname}"
              data-drug-id="${drugbankId}"
            >
            <div>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                height="24px"
                viewBox="0 -960 960 960"
                width="24px"
                fill="#005fb8">
                <path
                  d="M345-120q-94 0-159.5-65.5T120-345q0-45 17-86t49-73l270-270q32-32 73-49t86-17q94 0 159.5 65.5T840-615q0 45-17 86t-49 73L504-186q-32 32-73 49t-86 17Zm266-286 107-106q20-20 31-47t11-56q0-60-42.5-102.5T615-760q-29 0-56 11t-47 31L406-611l205 205ZM345-200q29 0 56-11t47-31l106-107-205-205-107 106q-20 20-31 47t-11 56q0 60 42.5 102.5T345-200Z" />
              </svg>
              <div>
                <span> ${drugsynonym} </span>
                <p>Common Name: ${commonname}</p>
              </div>
            </div>
            <button class="drug_choosen_close_btn" type="button">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                height="30px"
                viewBox="0 -960 960 960"
                width="30px"
                fill="#C1C1C1">
                <path
                  d="m336-280-56-56 144-144-144-143 56-56 144 144 143-144 56 56-144 143 144 144-56 56-143-144-144 144Z" />
              </svg>
            </button>
          </div>
            `,
      );
      return true;
    },
    removeDrug: function (commonname) {
      if (!this.drugs.has(commonname)) {
        console.warn("Drug not found: ", commonname);
        return false;
      }
      this.drugs.delete(commonname);
      return true;
    },
    validateDrugName: async function (name) {
      // takes common name and returns list[commonname,drugbankID] and errorString
      if (name == null) {
        return [["", ""], "Empty Input Box"];
      }
      if (name.trim() != "") {
        const params = new URLSearchParams({
          drugname: name.trim(),
        });
        const response = await fetch(`/api/checkdrug/?${params}`, {
          method: "GET",
        });
        if (response != null) {
          const data = await response.json();
          console.log(data);
          return [
            [data["commonname"], data["synonym"], data["drugbankId"]],
            data.error,
          ];
        }
        return [[name, name, name], "Fetching Error"];
      } else {
        return [[name, name, name], "Invalid data"];
      }
    },
    sendFileToServer: async function (file) {
      const formData = new FormData();
      formData.append("image", file);
      const csrfToken = document.querySelector(
        '[name="csrfmiddlewaretoken"]',
      )?.value;
      try {
        const response = await fetch("/api/extract-name", {
          method: "POST",
          headers: {
            "X-CSRFToken": csrfToken,
          },
          body: formData,
        });
        const data = await response.json();
        console.log(data);
        if (data.success) {
          return [data["commonname"], null];
        } else {
          return [null, error];
        }
      } catch (error) {
        return [null, error];
      }
    },
    setupEventHandling: function () {
      let drug_check_button = document.getElementById("drug_check_button");
      let camera_button = document.getElementById("camera_button");
      let imageInput = document.getElementById("imageInput");
      let navToPageMap = {
        drug_check_button: {
          file: "intAnalysis.html",
          pageName: "IntAnalysis",
        },
      };
      drug_cards_container = document.getElementById("drug_cards_container");
      // EVENT LISTENDER: IMAGE UPLOAD BUTTON
      camera_button.addEventListener("click", (e) => {
        e.stopPropagation();
        e.preventDefault();

        imageInput.click();
      });
      imageInput.addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        isValid = ["image/jpg", "image/png", "image/jpeg"].includes(
          file.type.trim(),
        );
        e.target.value = "";
        if (isValid) {
          const overlay = document.getElementById("loading-overlay");
          overlay.style.display = "flex";
          [commonname, errorString] = await this.sendFileToServer(file);
          if (errorString != null) {
            showInvalidInputError(errorString);
          }
          overlay.style.display = "none";
          let drugnameInputBox = document.getElementById("drugnameInputBox");
          drugnameInputBox.value = commonname;
        }
      });

      // EVENT LISTENER: CLOSE BUTTON EVENT LISTENER
      drug_cards_container.addEventListener("click", (e) => {
        const closeBtn = e.target.closest(".drug_choosen_close_btn");
        if (closeBtn) {
          const card = closeBtn.closest(".drug_choosen_card");
          if (card) {
            const commonname = card.dataset.drugName;
            this.removeDrug(commonname);
            card.remove();
          }
          if (this.getTotalCards() == 0) {
            this.forNoInsertedCard();
          }
          this.forDisableInteractionButton();
          this.forEnableValidationButton();
        }
      });
      if (drug_check_button) {
        totalCards = this.getTotalCards();
        if (totalCards == 2) {
          this.forEnableInteractionButton();
        }
        // EVENT LISTENER: DRUG INTERACTION CHECKER
        drug_check_button.addEventListener("click", async (e) => {
          totalCards = this.getTotalCards();
          e.stopPropagation();
          e.preventDefault();
          await this.redirectHandler(navToPageMap.drug_check_button);
        });
      }

      let confirm_drug_button = document.getElementById("confirm_drug_button");
      if (confirm_drug_button) {
        // EVENT LISTENER: DRUG VALIDATION BUTTON
        confirm_drug_button.addEventListener("click", async (e) => {
          e.stopPropagation();
          e.preventDefault();

          let commonname;
          let drugbankId;
          let drugsynonym;
          totalCards = this.getTotalCards();

          if (totalCards == 2) {
            this.forEnableInteractionButton();
            this.forDisablingValidationButton();
          } else if (totalCards < 2) {
            let drugnameInputBox = document.getElementById("drugnameInputBox");
            commonname = drugnameInputBox.value;
            [[commonname, drugsynonym, drugbankId], errormsg] =
              await this.validateDrugName(commonname);
            if (errormsg != null) {
              this.showInvalidInputError(errormsg);
              return;
            }
            if (totalCards == 0) {
              this.forYesIntertedCard();
              this.forEnableValidationButton();
            }
            this.addDrug(commonname, drugbankId, drugsynonym);
            drugnameInputBox.value = "";
            this.removeInvalidInputError();
            totalCards = this.getTotalCards();
            if (totalCards == 2) {
              this.forEnableInteractionButton();
              this.forDisablingValidationButton();
            } else {
              this.forDisableInteractionButton();
              this.forEnableValidationButton();
            }
          } else {
            this.forDisableInteractionButton();
            this.forEnableValidationButton();
          }
        });
      }
    },

    redirectHandler: async function (pageConfig) {
      if (pageConfig && pageConfig.file) {
        const values = Array.from(this.drugs.values());
        const params = new URLSearchParams({
          drug1: values[0],
          drug2: values[1],
        });
        this.forNoInsertedCard();

        const response = await fetch(
          `sub/${pageConfig.pageName.toLowerCase()}/?${params}`,
        );
        if (!response.ok) {
          throw new Error(`FETCHING error: ${response.status}`);
        }
        const htmlText = await response.text();
        let contents_div = document.getElementById("contents_div");

        contents_div.innerHTML = htmlText;
        MedicalApp.currentPage = pageConfig.pageName;

        // Load the script for the new page
        await this.loadPageScript(pageConfig);
        path_nav.innerHTML += `
         <li>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              height="24px"
              viewBox="0 -960 960 960"
              width="24px"
              fill="#1D1D1D">
              <path d="M400-280v-400l200 200-200 200Z" />
            </svg>
          </li>
         <li>${pageConfig.pageName}</li>`;
      } else {
        console.error("Invalid page configuration");
      }
    },

    loadPageScript: async function (pageConfig) {
      return new Promise((resolve, reject) => {
        const pageName = pageConfig.pageName;

        const existingScript = document.querySelector(
          `script[data-page="${pageName}"]`, // Fixed here
        );

        if (existingScript) {
          if (MedicalApp.Pages[pageName] && MedicalApp.Pages[pageName].init) {
            MedicalApp.Pages[pageName].init();
          }
          resolve();
          return;
        }

        const script = document.createElement("script");
        script.src = `static/medisafe/js/${pageName.toLowerCase()}.js`;
        script.dataset.page = pageName;

        script.onload = () => {
          console.log(`Loaded: ${pageName}`);
          if (MedicalApp.Pages[pageName] && MedicalApp.Pages[pageName].init) {
            MedicalApp.Pages[pageName].init(); // Fixed here
          }
          resolve();
        };

        script.onerror = () => {
          console.error(`Failed to load script: ${pageName}`); // Fixed here
          reject(new Error(`Failed to load script: ${pageName}`));
        };

        document.head.appendChild(script);
      });
    },
  };
})(window);
