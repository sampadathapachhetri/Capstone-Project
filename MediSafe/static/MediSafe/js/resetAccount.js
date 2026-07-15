let go_back_div = document.getElementById("go_back_div");

go_back_div.addEventListener("click", (e) => {
  window.location.href = "/login/";
});

document.addEventListener("DOMContentLoaded", (e) => {
  setupEventListeners();
});

function enableOverlay() {
  document.getElementById("otpOverlay").classList.add("active");
  document.getElementById("otpInput").disabled = false;
  document.getElementById("submitBtn").disabled = false;
  document.getElementById("cancelBtn").disabled = false;
  document.getElementById("otpInput").focus();
  clearError();
}

function disableOverlay() {
  document.getElementById("otpOverlay").classList.remove("active");
  document.getElementById("otpInput").disabled = true;
  document.getElementById("submitBtn").disabled = true;
  document.getElementById("cancelBtn").disabled = true;
  document.getElementById("otpInput").value = "";
  document.getElementById("passInput").value = "";
}

async function requestOTP() {
  let email = document.getElementById("email_field").value;
  if (email == "") {
    return "Invalid Email";
  }
  try {
    const csrfToken = document.querySelector(
      '[name="csrfmiddlewaretoken"]',
    )?.value;
    const response = await fetch(`/api/requestotp`, {
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
    console.log(data);
    return data.error;
  } catch (error) {
    console.error("Error:", error);
    return error;
  }
}

async function requestPasswordChange() {
  try {
    password = document.getElementById("passInput").value;
    let email = document.getElementById("email_field").value;
    if (email == "") {
      return "Invalid Email";
    }
    let otp = document.getElementById("otpInput").value;
    const csrfToken = document.querySelector(
      '[name="csrfmiddlewaretoken"]',
    )?.value;
    const response = await fetch(`/api/requestPassReset`, {
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
    console.log(data);
    return data.error;
  } catch (error) {
    console.error("Error:", error);
    return error;
  }
}

function showError(err) {
  let temperror = document.getElementById("temperror");
  let email_field = document.getElementById("email_field");
  email_field.classList.add("shake");
  temperror.innerHTML = `<span style="color:red;font-size:.9em;width:100%;">${err}</span>`;
  setTimeout(() => {
    email_field.classList.remove("shake");
  }, 1000);
}
function clearError() {
  let temperror = document.getElementById("temperror");
  temperror.innerHTML = ``;
}
function showOTPError(err) {
  otperror = document.getElementById("otperror");
  otp = document.getElementById("otpInput");

  otp.classList.add("shake");

  otperror.innerHTML = `<span style="color:red;font-size:.9em;width:100%;">${err}</span>`;
  setTimeout(() => {
    otp.classList.remove("shake");
  }, 1000);
}
function clearOTPError() {
  let temperror = document.getElementById("otperror");
  temperror.innerHTML = ``;
}

async function toRequestOTP() {
  document.body.classList.add("loading");
  error = await requestOTP();
  disableOverlay();
  if (error != null) {
    showError(error);
    document.body.classList.remove("loading");
    return;
  } else {
    enableOverlay();
    document.body.classList.remove("loading");
  }
}

function setupEventListeners() {
  let resendOtpLink = document.getElementById("resendOtpLink");
  let submit_btn = document.getElementById("submitBtn");
  let cancel_btn = document.getElementById("cancelBtn");
  let confirm_button = document.getElementById("confirm_button");
  let email = document.getElementById("email_field").value;
  let otp = document.getElementById("otpInput").value;
  let temperror = document.getElementById("temperror");

  confirm_button.addEventListener("click", async (e) => {
    e.stopPropagation();
    e.preventDefault();
    await toRequestOTP();
  });

  submit_btn.addEventListener("click", async (e) => {
    e.stopPropagation();
    e.preventDefault();
    err = await requestPasswordChange();
    if (err == null) {
      disableOverlay();
      clearOTPError();
      alert("Password Changed Successfully!!");
      window.location.href = "/";
    }
    showOTPError(err);
  });

  cancel_btn.addEventListener("click", (e) => {
    e.stopPropagation();
    e.preventDefault();
    disableOverlay();
    clearOTPError();
  });

  // Close overlay when clicking outside
  document.getElementById("otpOverlay").addEventListener("click", (e) => {
    if (e.target === document.getElementById("otpOverlay")) {
      disableOverlay();
    }
  });

  // Close on Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      disableOverlay();
    }
  });
  resendOtpLink.addEventListener("click", async (e) => {
    disableOverlay();
    toRequestOTP();
  });
}
