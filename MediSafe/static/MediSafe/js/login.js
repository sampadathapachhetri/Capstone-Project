let redirect_to_register = document.getElementById("redirect_to_register");
let forget_password_href = document.getElementById("forget_password_href");
let password_field = document.getElementById("password_field");
let eye_icon = document.getElementById("eye_icon");
let loginForm = document.getElementById("login_form");
let emailField = document.getElementById("email_field");
let otpInput = document.getElementById("otpInput");
let otpError = document.getElementById("otpError");
let otpSubmitBtn = document.getElementById("otpSubmitBtn");
let resendOtpLink = document.getElementById("resendOtpLink");
let resendStatus = document.getElementById("resendStatus");
let otpDialog = document.getElementById("otpDialog");
let csrfToken = document.querySelector('[name="csrfmiddlewaretoken"]')?.value;


redirect_to_register.addEventListener("click", (e) => {
  window.location.href = "/register/";
});

forget_password_href.addEventListener("click", (e) => {
  window.location.href = "/resetAccount/";
});

eye_icon.addEventListener("click", (e) => {
  let type = password_field.getAttribute("type");
  if (type == "password") {
    eye_icon.src = eye_icon.dataset.eyeOffUrl;
    password_field.setAttribute("type", "text");
  } else {
    eye_icon.src = eye_icon.dataset.eyeOnUrl;
    password_field.setAttribute("type", "password");
  }
});

// ========== FORM SUBMISSION ==========

loginForm.addEventListener("submit", async function (e) {
  e.preventDefault();

  const email = emailField.value.trim();
  const password = password_field.value.trim();
  const remember = document.getElementById("checkbox_input")?.checked || false;

  if (!email || !password) {
    alert("Please enter both email and password");
    return;
  }

  try {
    // Step 1: Check if 2FA is enabled
    const formData = new FormData();
    formData.append("email", email);

    const tfaResponse = await fetch("/api/isTfaEnabled/", {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
      },
      body: formData,
    });

    const tfaData = await tfaResponse.json();

    if (tfaData.enabled === true) {
      // 2FA is enabled - show OTP dialog
      showOTPDialog();
      return;
    }

    // No 2FA - submit directly to validate_login
    await submitLogin(email, password, remember, null);
  } catch (error) {
    console.error("Error:", error);
    alert("An error occurred. Please try again.");
  }
});

// ========== SUBMIT LOGIN ==========

async function submitLogin(email, password, remember, otp) {
  try {
    const formData = new FormData();
    formData.append("email", email);
    formData.append("password", password);
    formData.append("remember", remember ? "on" : "off");
    if (otp) {
      formData.append("otp", otp);
    }

    const response = await fetch("/validate_login/", {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
      },
      body: formData,
    });

    const data = await response.json();

    if (data.success) {
      window.location.href = "/";
    } else {
      if (otp) {
        otpError.textContent = data.msg || "Invalid OTP. Please try again.";
        otpInput.classList.add("error");
        otpSubmitBtn.disabled = false;
        otpSubmitBtn.textContent = "Verify & Login";
      } else {
        alert(data.msg || "Login failed. Please try again.");
      }
    }
  } catch (error) {
    console.error("Login error:", error);
    if (otp) {
      otpError.textContent = "An error occurred. Please try again.";
      otpSubmitBtn.disabled = false;
      otpSubmitBtn.textContent = "Verify & Login";
    } else {
      alert("An error occurred. Please try again.");
    }
  }
}

// ========== OTP DIALOG FUNCTIONS ==========

function showOTPDialog() {
  otpDialog.style.display = "flex";
  otpInput.value = "";
  otpError.textContent = "";
  otpSubmitBtn.disabled = false;
  otpSubmitBtn.textContent = "Verify & Login";
  resendStatus.textContent = "";
  otpInput.focus();
}

function closeOTPDialog() {
  otpDialog.style.display = "none";
  otpError.textContent = "";
  resendStatus.textContent = "";
}

// ========== OTP SUBMIT ==========

otpSubmitBtn.addEventListener("click", async function () {
  const otp = otpInput.value.trim();

  if (otp.length !== 5) {
    otpError.textContent = "Please enter a valid 5-Character OTP";
    otpInput.classList.add("error");
    return;
  }

  otpError.textContent = "";
  otpInput.classList.remove("error");
  otpSubmitBtn.disabled = true;
  otpSubmitBtn.textContent = "Verifying...";

  const email = emailField.value.trim();
  const password = password_field.value.trim();
  const remember = document.getElementById("checkbox_input")?.checked || false;

  await submitLogin(email, password, remember, otp);
});

// ========== RESEND OTP ==========

resendOtpLink.addEventListener("click", async function (e) {
  e.preventDefault();

  const email = emailField.value.trim();
  if (!email) {
    resendStatus.textContent = "Email not found. Please enter your email.";
    resendStatus.className = "resend-status error";
    return;
  }

  resendStatus.textContent = "Sending...";
  resendStatus.className = "resend-status";

  try {
    // Send as JSON because your requestOTP expects JSON
    const response = await fetch("/api/requestotp", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify({ email: email }),
    });

    const data = await response.json();

    if (data.error) {
      resendStatus.textContent = data.error;
      resendStatus.className = "resend-status error";
    } else {
      resendStatus.textContent = "✓ OTP sent successfully!";
      resendStatus.className = "resend-status";
      otpError.textContent = "";
      otpInput.classList.remove("error");

      setTimeout(() => {
        resendStatus.textContent = "";
      }, 5000);
    }
  } catch (error) {
    console.error("Error resending OTP:", error);
    resendStatus.textContent = "Failed to send OTP. Please try again.";
    resendStatus.className = "resend-status error";
  }
});

// ========== ENTER KEY SUPPORT ==========

otpInput.addEventListener("keydown", function (e) {
  if (e.key === "Enter") {
    otpSubmitBtn.click();
  }
});

// Close dialog on Escape key
document.addEventListener("keydown", function (e) {
  if (e.key === "Escape") {
    closeOTPDialog();
  }
});

// Close dialog on outside click
otpDialog.addEventListener("click", function (e) {
  if (e.target === this) {
    closeOTPDialog();
  }
});
