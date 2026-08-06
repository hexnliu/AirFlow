

(function() {
  'use strict';
  window.addEventListener('load', function() {
    // Fetch all the forms we want to apply custom Bootstrap validation styles to

    // document.getElementById("newBuilding_countryId").onchange =  newCheckZIP ;
    if(document.getElementById("id_password1")!=null){
      document.getElementById("id_password1").oninput =validatePassword;
    }

    if(document.getElementById("id_password2")!=null){
      document.getElementById("id_password2").oninput =validatePassword2;
    }



    var forms = document.getElementsByClassName('needs-validation');
    // Loop over them and prevent submission
    var validation = Array.prototype.filter.call(forms, function(form) {
      form.addEventListener('submit', function(event) {
        if (form.checkValidity() === false) {
          event.preventDefault();
          event.stopPropagation();
        }
        form.classList.add('was-validated');

      }, false);
    });
  }, false);
})();


function validatePassword()
{
  myInput=  document.getElementById("id_password1");
  var errorMsg= $("#id_password1").closest(".form-row").find(".invalid-feedback");
  errorMsg.html("");

  // Validate lowercase letters
  var lowerCaseLetters = /[a-z]/g;
  if(!myInput.value.match(lowerCaseLetters)) {
    myInput.setCustomValidity("Must contain one lower case");
    errorMsg.append('<i class="fa fa-circle" ></i>Must contain one lower case <br>')
  }

  // Validate capital letters
  var upperCaseLetters = /[A-Z]/g;
  if(!myInput.value.match(upperCaseLetters)) {
    myInput.setCustomValidity("one upper case");
    errorMsg.append('<i class="fa fa-circle" ></i>Must contain one upper case <br>')
  }

  // Validate numbers
  var numbers = /[0-9]/g;
  if(!myInput.value.match(numbers)) {
    myInput.setCustomValidity("Must contain numbers ");
    errorMsg.append('<i class="fa fa-circle" ></i>Must contain numbers <br>')
  }

  // Validate length
  if(myInput.value.length < 8) {
    myInput.setCustomValidity("At least 8 characters ");
    errorMsg.append('<i class="fa fa-circle" ></i>At least 8 characters')
  }


  if(myInput.value.match(lowerCaseLetters) && myInput.value.match(upperCaseLetters) && myInput.value.match(numbers) && myInput.value.length >= 8){
    myInput.setCustomValidity("");
  }
}

function validatePassword2()
{
  myInput=  document.getElementById("id_password1");
  myInput2=  document.getElementById("id_password2");
  var errorMsg= $("#id_password2").closest(".form-row").find(".invalid-feedback");
  if(myInput.value!=myInput2.value){
    myInput2.setCustomValidity("Password does not match");
  }else{
    myInput2.setCustomValidity("");
  }

}

function validateUserName(){
  myInput=  document.getElementById("id_username");

}