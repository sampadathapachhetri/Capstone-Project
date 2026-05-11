let redirect_to_login = document.getElementById("redirect_to_login");

redirect_to_login.addEventListener("click", (e) => {
  window.location.href = "login.html";
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
