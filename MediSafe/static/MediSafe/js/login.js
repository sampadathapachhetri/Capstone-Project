let redirect_to_register = document.getElementById("redirect_to_register");

redirect_to_register.addEventListener("click", (e) => {
  window.location.href = "register.html";
});
let forget_password_href = document.getElementById("forget_password_href");
forget_password_href.addEventListener("click", (e) => {
  window.location.href = "resetAccount.html";
});

let password_field = document.getElementById("password_field");
let eye_icon = document.getElementById("eye_icon");
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
