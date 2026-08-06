
$(document).ready(function () {

  var _GET = (function () {
    var _get = {};
    var re = /[?&]([^=&]+)(=?)([^&]*)/g;
    while (m = re.exec(location.search))
      _get[decodeURIComponent(m[1])] = (m[2] == '=' ? decodeURIComponent(m[3]) : true);
    return _get;
  })();
  if (_GET['sortBy']) {
    $("#sortBy").val(_GET['sortBy']);
  }
  

  $('.custom-file input').change(function (e) {
    if (e.target.files.length) {
      $(this).next('.custom-file-label').html(e.target.files[0].name);
    }
  });

  $('.table-responsive').on('show.bs.dropdown', function () {
    $('.table-responsive').css("overflow", "inherit");
  });

  $('.table-responsive').on('hide.bs.dropdown', function () {
    $('.table-responsive').css("overflow", "auto");
  })


  $(document).on('show.bs.modal', '.modal', function () {
    var zIndex = 1040 + (10 * $('.modal:visible').length);
    $(this).css('z-index', zIndex);
    setTimeout(function () {
      $('.modal-backdrop').not('.modal-stack').css('z-index', zIndex - 1).addClass('modal-stack');
    }, 0);
  });

  $(document).on('hidden.bs.modal', '.modal', function () {
    $('.modal:visible').length && $(document.body).addClass('modal-open');
    if ($(this).find("form")[0] != null) {
      $(this).find("form")[0].reset();
      $(this).find('.custom-file-label').html("");
      $(this).find(".invalid-msg").html("")
      $(this).find("form").removeClass("was-validated");

    }

  });



});


function formatOptions(state) {
  if (!state.id) {
    return state.text;
  }
  var $state;
  if ($(state.element).attr('class') == "crossmark") {
    $state = $('<span ><img style="display:inline-block; width:15px;height:15px;" src="/static/accounts/images/Feedback Crossmark.svg" /> ' + state.text + '</span>');
  } else if ($(state.element).attr('class') == "checkmark") {
    $state = $('<span ><img style="display:inline-block; width:15px;height:15px;" src="/static/accounts/images/Feedback Checkmark.svg" /> ' + state.text + '</span>');
  }

  return $state;
}
// (function () {
//   'use strict';
//   window.addEventListener('load', function () {
//     // Fetch all the forms we want to apply custom Bootstrap validation styles to

//     // document.getElementById("newBuilding_countryId").onchange =  newCheckZIP ;
//     if (document.getElementById("newBuilding_postal_code") != null) {
//       document.getElementById("newBuilding_postal_code").oninput = newCheckZIP;
//     }


//     // document.getElementById("editBuilding_countryId").onchange =  editCheckZIP ;
//     if (document.getElementById("editBuilding_postal_code") != null) {
//       document.getElementById("editBuilding_postal_code").oninput = editCheckZIP;
//     }
//     if (document.getElementById("newBuilding_name") != null) {
//       document.getElementById("newBuilding_name").oninput = checkNewBuildingName;
//     }
//     if (document.getElementById("editBuilding_name") != null) {
//       document.getElementById("editBuilding_name").oninput = checkEditBuildingName;
//     }
//     if (document.getElementById("ev_endDate") != null) {
//       document.getElementById("ev_endDate").oninput = checkEVEndDate;
//     }

//     if (document.getElementById("ev_startDate") != null) {
//       document.getElementById("ev_startDate").oninput = checkEVStartDate;
//     }
//     if (document.getElementById("ev_name") != null) {
//       document.getElementById("ev_name").oninput = checkEVName;
//     }

//     if (document.getElementById("ev_weekdayOccupiedEnd") != null) {
//       document.getElementById("ev_weekdayOccupiedEnd").oninput = checkEVWeekdayOccupiedEndTime;
//     }
//     if (document.getElementById("ev_weekendOccupiedTemperature") != null) {
//       document.getElementById("ev_weekendOccupiedTemperature").oninput = checkEVOccupiedTemperature;
//     }
//     if (document.getElementById("ev_weekendUnoccupiedTemperature") != null) {
//       document.getElementById("ev_weekendUnoccupiedTemperature").oninput = checkEVUnoccupiedTemperature;
//     }

//     if (document.getElementById("ev_numOfSensors") != null) {
//       document.getElementById("ev_numOfSensors").oninput = checkEVTSN;
//     }
//     if (document.getElementById("av_endDate") != null) {
//       document.getElementById("av_endDate").oninput = checkAVEndDate;
//     }
//     if (document.getElementById("av_name") != null) {
//       document.getElementById("av_name").oninput = checkAVName;
//     }

  
//     if (document.getElementById("av_startDate") != null) {
//       document.getElementById("av_startDate").oninput = checkAVStartDate;
//     }
  
//     if (document.getElementById("av_weekdayOccupiedEnd") != null) {
//       document.getElementById("av_weekdayOccupiedEnd").oninput = checkAVWeekdayOccupiedEndTime;
//     }
//     if (document.getElementById("av_weekendOccupiedTemperature") != null) {
//       document.getElementById("av_weekendOccupiedTemperature").oninput = checkAVOccupiedTemperature;
//     }
//     if (document.getElementById("av_weekendUnoccupiedTemperature") != null) {
//       document.getElementById("av_weekendUnoccupiedTemperature").oninput = checkAVUnoccupiedTemperature;
//     }
  
//     if (document.getElementById("av_numOfSensors") != null) {
//       document.getElementById("av_numOfSensors").oninput = checkAVTSN;
//     }

    


//     if (this.document.getElementById("loT_file") != null) {
//       document.getElementById("loT_file").oninput = ValidateloTExtension;
//     }
//     if (document.getElementById("weather_file_upload_label") != null) {
//       document.getElementById("weather_file_upload_label").oninput = ValidateWeatherExtension;
//     }

//     if (this.document.getElementById("up_file") != null) {
//       document.getElementById("up_file").oninput = ValidateplacementExtension;
//     }

//     if (this.document.getElementById("blank_floor_plan_file") != null) {
//       document.getElementById("blank_floor_plan_file").oninput = ValidatePdfExtension;
//     }
//     if (this.document.getElementById("fill_floor_plan_file") != null) {
//       document.getElementById("fill_floor_plan_file").oninput = ValidatePdfExtensionfill;
//     }

//     var forms = document.getElementsByClassName('needs-validation');
//     // Loop over them and prevent submission
//     var validation = Array.prototype.filter.call(forms, function (form) {
//       form.addEventListener('submit', function (event) {
//         if (form.checkValidity() === false) {
//           event.preventDefault();
//           event.stopPropagation();
//         }

//         if (form.id == "newBuildingForm") {
//           if (!checkNewAddress()) {
//             event.preventDefault();
//             event.stopPropagation();
//           }
//         }
//         form.classList.add('was-validated');

//       }, false);
//     });
//   }, false);
// })();




function sideScroll(direction, speed, distance, step, indcators_id) {
  var element = document.getElementById(indcators_id);
  scrollAmount = 0;
  var slideTimer = setInterval(function () {
    if (direction == 'left') {
      element.scrollLeft -= step;
    } else {
      element.scrollLeft += step;
    }
    scrollAmount += step;
    if (scrollAmount >= distance) {
      window.clearInterval(slideTimer);
    }
  }, speed);
}


function jsUcfirst(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}
function checkAVEndDate() {
  var s = document.getElementById("av_startDate");
  var futureDate =new Date(s.value);
  futureDate.setDate(futureDate.getDate()+14);
  console.log(futureDate);
  var e = document.getElementById("av_endDate");
  
  var feedback = $("#av_endDate").closest(".col-sm-6").find(".invalid-feedback");
  if(s.value !=""){
    if (e.value.trim() == "") {
      e.setCustomValidity("Please Choose an end date");
      feedback.text("Please Choose an end date");
    } else if (Date.parse(e.value) <= Date.parse(s.value)) {
      e.setCustomValidity("End date must greater than start date");
      feedback.text("End date must greater than start date");
    }else if (Date.parse(e.value) > futureDate){
      e.setCustomValidity("End date must within 14 days from the start date");
      feedback.text("End date must within 14 days from the start date");
    }
    else {
      e.setCustomValidity("");
    }
}else{
  e.setCustomValidity("Please choose a start end");
  feedback.text("Please choose a start end");
}

}

function checkAVWeekdayOccupiedEndTime() {
  var e = document.getElementById("av_weekdayOccupiedEnd");
  var s = document.getElementById("av_weekdayOccupiedStart");

  var feedback = $("#av_weekdayOccupiedEnd").closest(".col-sm-6").find(".invalid-feedback");
  if (e.value.trim() == "") {
    e.setCustomValidity("Please Choose an end time");
    feedback.text("Please Choose an end time");
  } else if (e.value<=s.value) {
    e.setCustomValidity("End time must greater than start time");
    feedback.text("End time must greater than start time");
  }
  else {
    e.setCustomValidity("");
  }
}



function checkAVStartDate() {
  var past_date = new Date('2019-01-01');
  var today = new Date();
  var yyyy = today.getFullYear();
  var s = document.getElementById("av_startDate");
  var e = document.getElementById("av_endDate");
  var  feedback2 = $("#av_endDate").closest(".col-sm-6").find(".invalid-feedback");
  var inputDate = new Date(s.value);
  var feedback = $("#av_startDate").closest(".col-sm-6").find(".invalid-feedback");
  if (s.value.trim() == "") {
    s.setCustomValidity("Please Choose a start date");
    feedback.text("Please Choose a start date");
    e.value ="";
    feedback2.text("Please Choose a start date first");

  }else if (Date.parse(s.value) < Date.parse(past_date)){
    s.setCustomValidity("Start date must greater than 2019-01-01");
    feedback.text("Start date must greater than 2019-01-01");
    e.value ="";
    feedback2.text("Start date must greater than 2019-01-01");
  }
  else if (inputDate.getFullYear() >yyyy+3){
    s.setCustomValidity("Start year must within 3 years");
    feedback.text("Start year must within 3 years");
    e.value ="";
    feedback2.text("Start year must within 3 years");
 
  }
  else {
    s.setCustomValidity("");
  }

}

function checkAVOccupiedTemperature() {
  var s = document.getElementById("av_weekdayOccupiedTemperature");
  var feedback = $("#av_weekdayOccupiedTemperature").closest(".col-sm-6").find(".invalid-feedback");
  if (s.value.trim() == "") {
    s.setCustomValidity("Please input a value");
    feedback.text("Please input a value");
  }else if (s.value <0){
    s.setCustomValidity("Temperature must be greater than 0");
    feedback.text("Temperature must be greater than 0");
  }
  else {
    s.setCustomValidity("");
  }

}

function checkAVUnoccupiedTemperature() {
  var s = document.getElementById("av_weekendUnoccupiedTemperature");
  var feedback = $("#av_weekendUnoccupiedTemperature").closest(".col-sm-6").find(".invalid-feedback");
  if (s.value.trim() == "") {
    s.setCustomValidity("Please input a value");
    feedback.text("Please input a value");
  }else if (s.value <0){
    s.setCustomValidity("Temperature must be greater than 0");
    feedback.text("Temperature must be greater than 0");
  }
  else {
    s.setCustomValidity("");
  }

}




function checkAVTSN() {
  var e = document.getElementById("av_numOfSensors");
  var s = document.getElementById("av_numOfSensors");
  var feedback = $("#av_numOfSensors").closest(".col-sm-6").find(".invalid-feedback");
  if (e.value.trim() == "") {
    e.setCustomValidity("Please input the number of sensors");
    feedback.text("Please input the number of sensors");
  } else if (e.value >= 100) {
    e.setCustomValidity("This field  limit to 2 digits");
    feedback.text("This field limit to 2 digits");
  } else {
    e.setCustomValidity("");
  }

}
function checkEVName(){
  var values = [];
  var name = document.getElementById("ev_name");
  $("#detailBuildingVersion > option").each(function() {
    values.push(this.text);
  });
  
  var feedback = $("#ev_name").closest(".col-sm-6").find(".invalid-feedback");
  if (values.includes(name.value) && name.value.trim() != "") {
    name.setCustomValidity("Version Name exits");
    feedback.text("Version name exits");
  }else{
    name.setCustomValidity("");
    feedback.text("");

  }
}

function checkAVName(){
  var values = [];

$("#detailBuildingVersion > option").each(function() {
  values.push(this.text);
});
  var name = document.getElementById("av_name");
  var feedback = $("#av_name").closest(".col-sm-6").find(".invalid-feedback");
  if (values.includes(name.value) && name.value.trim() != "") {
    name.setCustomValidity("Version Name exits");
    feedback.text("Version name exits");
  }else{
    name.setCustomValidity("");
    feedback.text("");

  }
}
function checkEVEndDate() {

  var s = document.getElementById("ev_startDate");
  var futureDate =new Date(s.value);
  futureDate.setDate(futureDate.getDate()+14);
  console.log(futureDate);
  var e = document.getElementById("ev_endDate");
  
  var feedback = $("#ev_endDate").closest(".col-sm-6").find(".invalid-feedback");
  if(s.value !=""){
    if (e.value.trim() == "") {
      e.setCustomValidity("Please Choose an end date");
      feedback.text("Please Choose an end date");
    } else if (Date.parse(e.value) <= Date.parse(s.value)) {
      e.setCustomValidity("End date must greater than start date");
      feedback.text("End date must greater than start date");
    }else if (Date.parse(e.value) > futureDate){
      e.setCustomValidity("End date must within 14 days from the start date");
      feedback.text("End date must within 14 days from the start date");
    }
    else {
      e.setCustomValidity("");
    }
}else{
  e.setCustomValidity("Please choose a start end");
  feedback.text("Please choose a start end");
}

}

function checkEVWeekdayOccupiedEndTime() {
  var e = document.getElementById("ev_weekdayOccupiedEnd");
  var s = document.getElementById("ev_weekdayOccupiedStart");

  var feedback = $("#ev_weekdayOccupiedEnd").closest(".col-sm-6").find(".invalid-feedback");
  if (e.value.trim() == "") {
    e.setCustomValidity("Please Choose an end time");
    feedback.text("Please Choose an end time");
  } else if (e.value<=s.value) {
    e.setCustomValidity("End time must greater than start time");
    feedback.text("End time must greater than start time");
  }
  else {
    e.setCustomValidity("");
  }
}



function checkEVStartDate() {
  var past_date = new Date('2019-01-01');
  var today = new Date();
  var yyyy = today.getFullYear();
  var s = document.getElementById("ev_startDate");
  var e = document.getElementById("ev_endDate");
  var  feedback2 = $("#ev_endDate").closest(".col-sm-6").find(".invalid-feedback");
  var inputDate = new Date(s.value);
  var feedback = $("#ev_startDate").closest(".col-sm-6").find(".invalid-feedback");
  if (s.value.trim() == "") {
    s.setCustomValidity("Please Choose a start date");
    feedback.text("Please Choose a start date");
    e.value ="";
    feedback2.text("Please Choose a start date first");

  }else if (Date.parse(s.value) < Date.parse(past_date)){
    s.setCustomValidity("Start date must greater than 2019-01-01");
    feedback.text("Start date must greater than 2019-01-01");
    e.value ="";
    feedback2.text("Start date must greater than 2019-01-01");
  }
  else if (inputDate.getFullYear() >yyyy+3){
    s.setCustomValidity("Start year must within 3 years");
    feedback.text("Start year must within 3 years");
    e.value ="";
    feedback2.text("Start year must within 3 years");
 
  }
  else {
    s.setCustomValidity("");
  }

}

function checkEVOccupiedTemperature() {
  var s = document.getElementById("ev_weekdayOccupiedTemperature");
  var feedback = $("#ev_weekdayOccupiedTemperature").closest(".col-sm-6").find(".invalid-feedback");
 
  if (s.value.trim() == "" && $("#ev_temp_setpoint").val()=="yes") {
    s.setCustomValidity("Please input a value");
    feedback.text("Please input a value");
  }else if (s.value.trim() != "" &&s.value <0  && $("#ev_temp_setpoint").val()=="yes"){
    s.setCustomValidity("Temperature must be greater than 0");
    feedback.text("Temperature must be greater than 0");
  }
  else {
    s.setCustomValidity("");
  }

}

function checkEVUnoccupiedTemperature() {
  var s = document.getElementById("ev_weekendUnoccupiedTemperature");
  var feedback = $("#ev_weekendUnoccupiedTemperature").closest(".col-sm-6").find(".invalid-feedback");
  if (s.value.trim() == ""  && $("#ev_temp_setpoint").val()=="yes") {
    s.setCustomValidity("Please input a value");
    feedback.text("Please input a value");
  }else if (s.value.trim() != ""&&s.value <0  && $("#ev_temp_setpoint").val()=="yes"){
    s.setCustomValidity("Temperature must be greater than 0");
    feedback.text("Temperature must be greater than 0");
  }
  else {
    s.setCustomValidity("");
  }

}




function checkEVTSN() {
  var e = document.getElementById("ev_numOfSensors");
  var s = document.getElementById("ev_numOfSensors");
  var feedback = $("#ev_numOfSensors").closest(".col-sm-6").find(".invalid-feedback");
  if (e.value.trim() == "") {
    e.setCustomValidity("Please input the number of sensors");
    feedback.text("Please input the number of sensors");
  } else if (e.value >= 100) {
    e.setCustomValidity("This field  limit to 2 digits");
    feedback.text("This field limit to 2 digits");
  } else {
    e.setCustomValidity("");
  }

}








function checkEditBuildingName() {
  var name = document.getElementById("editBuilding_name");
  var feedback = $("#editBuilding_name").closest(".col-sm-9").find(".invalid-feedback");
  var options = $('#buildingBlock .card-title');
  var values = [];
  options.each(function () {
    values.push($(this).text());
  });


  if (values.includes(name.value.trim()) && name.value.trim() != "") {
    name.setCustomValidity("Building Name exits");
    feedback.text("Building Name exits");
  } else {
    name.setCustomValidity("");
    feedback.text("Please Enter A Building Name");
  }

}




function ValidateloTExtension() {
  var allowedFiles = [".csv"];
  var fileUpload = document.getElementById("loT_file");
  var lblError = document.getElementById("loT_error");
  var regex = new RegExp("([a-zA-Z0-9\s_\\.\-: ()])+(" + allowedFiles.join('|') + ")$");

  if (!regex.test(fileUpload.value.toLowerCase())) {
    lblError.innerHTML = "File format is invalid. Please upload files with <b>" + allowedFiles.join(', ') + "</b> extensions.";
    $("#loT_saveBtn").attr("disabled", true);
    fileUpload.setCustomValidity("Please upload valid csv file");
    return false;
  }
  lblError.innerHTML = "";
  fileUpload.setCustomValidity("");
  $("#loT_saveBtn").attr("disabled", false);
  return true;
}

function ValidateWeatherExtension() {
  var allowedFiles = [".csv"];
  var fileUpload = document.getElementById("weather_file");
  var lblError = document.getElementById("weather_error");
  var regex = new RegExp("([a-zA-Z0-9\s_\\.\-: ()])+(" + allowedFiles.join('|') + ")$");

  if (!regex.test(fileUpload.value.toLowerCase())) {
    lblError.innerHTML = "File format is invalid. Please upload files with <b>" + allowedFiles.join(', ') + "</b> extensions.";
    $("#weather_saveBtn").attr("disabled", true);
    fileUpload.setCustomValidity("Please upload valid csv file");
    return false;
  }
  lblError.innerHTML = "";
  fileUpload.setCustomValidity("");
  $("#weather_saveBtn").attr("disabled", false);
  return true;
}

function ValidateplacementExtension() {
  var allowedFiles = [".xlsx"];
  var fileUpload = document.getElementById("up_file");
  var lblError = document.getElementById("up_error");
  var regex = new RegExp("([a-zA-Z0-9\s_\\.\-: ()])+(" + allowedFiles.join('|') + ")$");
  if (!regex.test(fileUpload.value.toLowerCase())) {
    lblError.innerHTML = "File format is invalid. Please upload files with <b>" + allowedFiles.join(', ') + "</b> extensions.";
    $("#uploadPlacementBtn").attr("disabled", true);
    fileUpload.setCustomValidity("Please upload valid xlsx file");
    return false;
  }
  lblError.innerHTML = "";
  fileUpload.setCustomValidity("");
  $("#uploadPlacementBtn").attr("disabled", false);
  return true;
}

function ValidatePdfExtension() {
  var allowedFiles = [".pdf", ".png", ".jpeg", ".jpg"];
  var fileUpload = document.getElementById("blank_floor_plan_file");
  var lblError = document.getElementById("blank_floor_plan_file_error");
  var regex = new RegExp("([a-zA-Z0-9\s_\\.\-: ()])+(" + allowedFiles.join('|') + ")$");
  if (!regex.test(fileUpload.value.toLowerCase())) {
    lblError.innerHTML = "File format is invalid. Please upload files with <b>" + allowedFiles.join(', ') + "</b> extensions.";
    fileUpload.setCustomValidity("Please upload valid pdf file");
    $("#blank_floor_plan_file_saveBtn").attr("disabled", true);
    return false;
  }
  lblError.innerHTML = "";
  fileUpload.setCustomValidity("");
  $("#blank_floor_plan_file_saveBtn").attr("disabled", false);
  return true;
}

function ValidatePdfExtensionfill() {
  var allowedFiles = [".pdf", ".png", ".jpeg", ".jpg"];
  var fileUpload = document.getElementById("fill_floor_plan_file");
  var lblError = document.getElementById("fill_floor_plan_error");
  var regex = new RegExp("([a-zA-Z0-9\s_\\.\-: ()])+(" + allowedFiles.join('|') + ")$");
  if (!regex.test(fileUpload.value.toLowerCase())) {
    lblError.innerHTML = "File format is invalid. Please upload files with <b>" + allowedFiles.join(', ') + "</b> extensions.";
    fileUpload.setCustomValidity("Please upload valid pdf file");
    $("#fill_floor_plan_saveBtn").attr("disabled", true);
    return false;
  }
  lblError.innerHTML = "";
  fileUpload.setCustomValidity("");
  $("#fill_floor_plan_saveBtn").attr("disabled", false);
  return true;
}