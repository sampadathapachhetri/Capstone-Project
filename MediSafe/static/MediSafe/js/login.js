let redirect_to_register = document.getElementById("redirect_to_register");

redirect_to_register.addEventListener("click", (e) => {
  window.location.href = "/register/";
});
let forget_password_href = document.getElementById("forget_password_href");
forget_password_href.addEventListener("click", (e) => {
  window.location.href = "/reset password/";
});
