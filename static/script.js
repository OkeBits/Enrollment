function validateLogin() {
  return true;
}

function registerUser() {
  return true;
}

function recoverAccount() {
  return true;
}


document.querySelector('.menu-btn').addEventListener('click', function() {
  document.querySelector('.side-panel').classList.toggle('open');
});
