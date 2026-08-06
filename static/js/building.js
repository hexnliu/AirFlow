

// update the postal value to uppercase
$(document).on('blur', "form input[name='postalCode']", function () {
  $(this).val(function (_, val) {
      return val.toUpperCase();
  });

});
$.noConflict();
$(document).ready(function(){
  $(document).ajaxStart(function () {
    $('#loading-wrapper').show(0);
  }).ajaxStop(function () {
    $("#loading-wrapper").hide();
  });
  
  //populate the data on update building form
  $("#updateBuildingModal").on('show.bs.modal',function(event){
    $("#updateBuilding_country").val($("#detailBuilding_country").text());
    $("#updateBuilding_province").val($("#detailBuilding_province").text());
    $("#updateBuilding_city").val($("#detailBuilding_city").text());
  });
  //set width on the class
  $(".search-select2").select2({
    width:"300px"
  });
// convert all time to local time
$(".utc2local").each(function(){
   var time =$(this).text();
   $(this).text(UTC2Local(time));
});


// Get the modal
var modal = document.getElementById("promptModal");


// Get the <span> element that closes the modal
var span = document.getElementsByClassName("promptClose")[0];

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
  modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
}

});

// Golba variables for phone number settings

var input = document.querySelector("#createBuilding_phone");
var input2 = document.querySelector("#updateBuilding_phone");
  // var iti = window.intlTelInputGlobals.getInstance(input);
  // iti.isValidNumber(); 
if(input!=null){
var iti =window.intlTelInput(input, {
  // any initialisation options go here
  onlyCountries: ["at", "ca","us"],
  utilsScript: "/static/lib/intl-tel-input/js/utils.js"
});
}
if(input2!=null){
var iti2 =window.intlTelInput(input2, {
  // any initialisation options go here
  onlyCountries: ["at", "ca","us"],
  utilsScript: "/static/lib/intl-tel-input/js/utils.js"

});

}


/* handle province change and return corresponding cities
   for create building form and update building form

  type: part of the element id (only 2 options eg.createBuilding_ or updateBuilding)
*/
function onProvinceChange(type){
  // passing country value, province value and where to store
  var province = $("#"+type+"_province").val();
  var country = $('#'+type+'_country').val();
  var where = "#"+type+"_city"; //where to store cities options
  // check value before sending ajax
  if(province!="" && country!=""){
    getCityOptions(country,province,where);
  }
}
/* when country value change for create building and update building form
  type: part of the element id (only 2 options eg.createBuilding_ or updateBuilding)
*/
function onCountryChange (type){
  // reset field value
  $("#"+type+"_province").html(`<option value="">Select Province/ State</option>`);
  $("#"+type+"_city").html(`<option value="">Select City</option>`);
  $("#"+type+"_phone_number").val("");
  // pass this country value, where to return this value
  var country = $("#"+type+"_country").val();
  // where to store the options
  var where ="#"+type+"_province";
  if(country!=""){
    getProvinceOptions( country,where);
  }
  // set the icon on phone field
  if(country == "Canada"){
    country="ca";
  }else if (country == "United States"){
    country="us";
  }else{
    country="at";
  }
  //set phone number value
  if(iti !=null){
    iti.setCountry(country);
  }
  if(iti2 !=null){
    iti2.setCountry(country);
  }
  // iti2.setCountry($("#"+type+"_country").val());

}

/*get province value
country: country value
where: the id eg.#id to store the options
old: this for update building form if the provice value exits, select the original option
getCity: default value is false, check if this is update buiilding form, if it is, select the origanl value for provinc and city
cityWhere: element id for storing city options, this applies on udpate building
cityText: the value in update building form is going to select
*/
function getProvinceOptions(country,where,old=null,getCity=false,cityWhere=null,cityText=null){
  var fd = new FormData();
  fd.append("country",country);
  $.ajax({
    type: 'POST',
    url: '/buildings/get_country_province_city/',
    data: fd,
    processData: false,
    contentType: false,
    success: function(data) {
      $(where).html(data);
      if(old!=null){
        $(where).val(old); //set the old value, selected
        if(getCity){
          getCityOptions(country,old,cityWhere,cityText);
        }
      }
    },error: function(jqXHR,error, errorThrown){
      $("#messageModal .modal-body").html('<p class="text-danger">'+error+'! </p>');
      $("#messageModal").modal('show');
    }
  });
}
/*
  ajax call for on province change
  country:selected country value
  province: selected province value
  where: the element id for storing the options
  text: optional, apply when it is in update building which select the origanl data
*/
  function getCityOptions(country,province,where,text=null){
    var form =new FormData();
    form.append('country',country);
    form.append("province",province)
    //ajax
    $.ajax({
      type: 'POST',
      url: '/buildings/get_country_province_city/',
      data:form,
      processData: false,
      contentType: false,
      success: function(data) {
        console.log(data);
        $(where).html(data);
        // selected the value if the data is in the database
        if(text!=null){
          $(where).val(text);
        }
      }, error: function(jqXHR,error, errorThrown){
      $("#messageModal .modal-body").html('<p class="text-danger">'+error+'! </p>');
      $("#messageModal").modal('show');
    }
    });
  }


  // return existing options as an array in upper case
  //where could be select box element id
  function getOptions(where){
    var options = $(where);
    var values = [];
    options.each(function () {
      values.push($(this).text().toUpperCase());
    });
    return values;
  }

/*validate building name
type: part of the element id eg.(createBuilding,updateBuilding)
*/
function validateBuildingName(type) {
  var name = document.getElementById(type+"_name");
  var feedback = $("#"+type+"_name").closest(".col-sm-9").find(".invalid-feedback");
  // feedback content
  var emptyText ="Please enter a building Name";
  var existedText ="Building name exits";
  var formatText ="Building name length should be between 1 - 20";
  //get a list of building name
  if($("#buildingBlock .card-title").length>0){
    var values=getOptions('#buildingBlock .card-title');
      if (values.includes(name.value.toUpperCase()) && name.value.trim() != "") {
        name.setCustomValidity(existedText);
        feedback.text(existedText);
      } else {

        if (name.value.length == 0) {
          feedback.text(emptyText);
          name.setCustomValidity(emptyText);
          feedback.text(emptyText);

        } else if (name.value.length > 100) {
          name.setCustomValidity(formatText);
          feedback.text(formatText);
        } else {
          name.setCustomValidity("");
          feedback.text("");
        }

      }
    }
}

/*validate postal code
type: part of the element id eg.(createBuilding,updateBuilding)
*/
function validatePostalCode(type) {
  var constraints = {
    "United States": ['^\\d{5}(-{0,1}\\d{4})?$', "Please enter a zip code"],
    "Canada": ['[a-zA-Z][0-9][a-zA-Z] ?[0-9][a-zA-Z][0-9]', "Please enter a postal code"],
    "Austria":['^\\d{4}$',"Please enter a postal code"],
  };
  var country = document.getElementById(type+"_country").value;
  // Get the NPA field
  var ZIPField = document.getElementById(type+"_postal_code");
  // Build the constraint checker
  var constraint = new RegExp(constraints[country][0], "");
  // Check it!
  if (constraint.test(ZIPField.value.trim())) {
    // The ZIP follows the constraint, we use the ConstraintAPI to tell it
    ZIPField.setCustomValidity("");
  } else {
    // The ZIP doesn't follow the constraint, we use the ConstraintAPI to
    // give a message about the format required for this country
    ZIPField.setCustomValidity(constraints[country][1]);

  }
}

/* validate building address
type: part of the element id eg.(createBuilding,updateBuilding)
*/
function validateBuildingAddress(type) {
  var name = document.getElementById(type+"_address");
  var testAddress = $("#"+type+"_address").val() + ", " + $("#"+type+"_city").val() + ", " + $("#"+type+"_province").val() + ", " +
  $("#"+type+"_country").val() + ", " + $("#"+type+"_postal_code").val();

  var feedback = $("#"+type+"_address").closest(".col-sm-9").find(".invalid-feedback");
  if($("#buildingBlock .card-text").length>0){
  var values = getOptions('#buildingBlock .card-text'); //get formatted exsiting address

  var emptyText ="Please enter a building name";
  var existedText ="Building name exits";

  if (values.includes(testAddress.toUpperCase()) && testAddress.trim() != "") {
    name.setCustomValidity(existedText);
    feedback.text(existedText);
  } else {

    if (name.value.length == 0) {
      feedback.text(emptyText);
      name.setCustomValidity(emptyText);
    } else {
      name.setCustomValidity("");
      feedback.text("");
    }

  }
}
}

/*validate phone number
type: part of the element id eg.(createBuilding,updateBuilding)
*/
function validatePhone(type) {
  var emptyText ="Please enter a valid phone number";
  var constraints = {
    "Canada": [/^\(?([0-9]{3})\)?[-. ●]?([0-9]{3})[-. ●]?([0-9]{4})$/, emptyText],
    "Austria":[/[-+]?[ 0-9]*\.?[0-9]+$/,emptyText],
    "United States":[/^[+]?(1\-|1\s|1|\d{3}\-|\d{3}\s|)?((\(\d{3}\))|\d{3})(\-|\s)?(\d{3})(\-|\s)?(\d{4})$/g,emptyText]
  };
  var country = document.getElementById(type+"_country").value;
  var feedback = $("#"+type+"_phone").closest(".col-sm-9").find(".invalid-feedback");
  var phone = document.getElementById(type+"_phone");
  // Build the constraint checker
  var constraint = new RegExp(constraints[country][0], "");
  // Check it!
  if (constraint.test(phone.value.trim())) {
    phone.setCustomValidity("");
  } else {

    // give a message about the format required for this country
    phone.setCustomValidity(constraints[country][1]);
    feedback.text(constraints[country][1]);
  }
}
function closeSettings(origanl){
  if(origanl == 'False'){
    origanl = false;
  }else{
    origanl = true;
  }
  $("#customSwitch1").prop("checked",origanl);
}

