$(document).ready(function () {
  var isMobile = false; //initiate as false


  //set sensors and floors to multiple select
  $(".js-select2").select2({
    allowClear: true,
    tags: true
  });

  // ajax send
  $("#checkbox").click(function () {
    if ($("#checkbox").is(':checked')) {
      $("#test_sensors > option").prop("selected", "selected"); // Select All Options
      $("#test_sensors").trigger("change"); // Trigger change to select 2
    } else {
      $("#test_sensors > option").removeAttr("selected");
      $("#test_sensors").trigger("change"); // Trigger change to select 2
    }
  });
  $("#viewImageModal .close").click(function () {
    $("#viewImageModal").hide();
  });
  // ioT submit too long
  $(".taskUploadModal form").submit(function (event) {
    var form = $(this);
    var url = $(this).attr("url");
    var fd = new FormData(form[0]);
    var modalId = form.attr("id").replace("Form", "ModalTitle");
    var msg = $("#" + modalId).text().replace("Upload", "").toLowerCase();
    if ($(form)[0].checkValidity() === true) {
      $.ajax({
        type: 'POST',
        url: url,
        data: fd,
        processData: false,
        contentType: false,
        success: function (data) {
          //
          $("#uploadSuccessCard h6").text("You have uploaded " + msg + " successfully");
          $("#uploadSuccessCard").modal("show");
          $(".taskUploadModal").modal("hide");
        },
        error: function (jqXHR, error, errorThrown) {
          $("#uploadErrorCard h6").text("Error - Failed to upload your " + msg);
          $("#uploadErrorCard").modal("show");
          $(".taskUploadModal").modal("hide");
        }
      });
    };


  });

  $(".floorPlanModal form").submit(function (event) {
    var form = $(this);
    var url = $(this).attr("action");
    var fd = new FormData(form[0]);
    var msg = "You have uploaded floor plan successfully.";
    var verb = "upload";
    if (url.includes("edit")) {
      msg = "You have updated floor plan successfully.";
      verb = "update";
    }
    if ($(form)[0].checkValidity() === true) {
      $.ajax({
        type: 'POST',
        url: url,
        data: fd,
        processData: false,
        contentType: false,
        success: function (data) {
          $("#uploadSuccessCard h6").text(msg);
          $("#uploadSuccessCard").modal("show");
          $(".floorPlanModal").modal("hide");
        },
        error: function (jqXHR, error, errorThrown) {
          $("#uploadErrorCard h6").text("Error - Failed to " + verb + " floor plan");
          $("#uploadErrorCard").modal("show");
          $(".floorPlanModal").modal("hide");
        }
      });
    };


  });

  var tasksTable = $('#tasksTable').DataTable({
    "scrollX": true,
    "pageLength": 60,
    "dom": 'bfrtip',
    "bInfo": false,
    // "bLengthChange": false,
    "responsive": {
      "details": {
        "type": 'column'
      }
    },

    'columnDefs': [{
      'targets': 0,
      'searchable': true,
      'orderable': true,
      'className': 'dt-control',
    }],
    "order": [
      [4, "desc"]
    ],
    "select": true,
  });


  //onclick to expand the row
  $('#tasksTable tbody tr').click(function () {
    var tr = $(this);
    var row = tasksTable.row(tr);
    var t_id = parseInt(tr.attr("id").replace("version_", ""));
    var t;
    // get the specific t object through a tasks list(which is render once openup a page)
    for (var i = 0; i < tasks.length; i++) {
      var object = tasks[i];
      if (object["id"] == t_id) {
        t = object;
      }
    }
    var format = formatRow(t, user); //format the html content
    /******************* dfifferent format for small screen *************** */
    //var user_screen_size =getBrowserWidth();
    //expand the row by opening up a detail modal page
    // if(user_screen_size =='xs' || user_screen_size =='sm'){
    //   $("#detailTaskModal h5").html("Task: "+ t["name"]);//title
    //   $("#detailTaskModal .container-fluid").html(format);
    //   $("#detailTaskModal").modal("show");
    // }else{
    if (row.child.isShown()) {
      // This row is already open - close it
      row.child.hide();
      tr.removeClass('shown');
    } else {
      // Open this row
      row.child(format).show();
      tr.addClass('shown');
    }
    // }


  });

});


//detail row html
function formatRow(t, user) {
  var v = `<div id="order`+t["id"]+`" class="order` + t["id"] + ` bg-light row" style="">
  <div class="col-md-5">
    <div class="step1 p-2 border-right">

      <div class="row font-weight-bold mb-3">
        
        <span class="` + formatStatus(t["is_step1"]) + `  align-middle">fiber_manual_record</span>
        Step 1: Items Required for Data Analysis
      </div>  
      <div class="row mb-2"> 
        <div class="col-sm-4">
          ` + formatStatusWithMsg(t["is_ioT_ready"]) + `
          Sensor Data File
        </div>
        <div class="col-sm-5" >
          <span class="font-italic">Last Updated: ` + formatDate(t["ioT_time"]) + formatFileName('loT.csv', t) + `</span>
        </div>
        <div class="col-sm">
        <a href="#"`+t["id"]+`" class="btn btn-primary btn-sm" onclick="validateEndDateForData('`+t["id"]+`');">Get Data</a>
        </div>
        `+formatUploadFile(t,user)+`
        
       

      </div>      
      <div class="row mb-2">
          <div class="col-sm-4">
            ` + formatStatusWithMsg(t["is_placement_ready"]) + `
            Sensor Placement
          </div>
          <div class="col-sm-5" >
            <span class="font-italic">Last Updated: ` + formatDate(t["placement_update_time"]) + `</span>
          </div>
          <div class="col-sm-2">
            <a href="/placements/sensor_placement/` + t["id"] + `" class="btn btn-primary btn-sm">` + formatButton(t["placement_update_time"]) + `</a>
          </div>
        </div>       
      </div>
  </div>
  <div class="col-md-5">
    <div class="step2 p-2">
      <div class="row font-weight-bold mb-3">
      <span class="` + formatStatus(t["is_step2"]) + ` align-middle">fiber_manual_record</span>
        Step 2: Optional Items for Floor Plan Graphs
      </div>
      <div class="row mb-2">
        <div class="col-sm-5">
          ` + formatStatusWithMsg(t["is_floor_plan_ready"]) + `
          Floor Plan Images
        </div>
        <div class="col-sm-4" >
          <span class="font-italic">Last Updated: ` + formatDate(t["floor_plan_update_time"]) + `</span>
        </div>
        <div class="col-sm-2">
          <a href="/buildings/upload_floor_plans/` + t["building_id"] + `?task=` + t["id"] + `" class="btn btn-primary btn-sm ">Upload</a>
        </div>
      </div>

      <div class="row mb-2">
        <div class="col-sm-5">
          ` + formatStatusWithMsg(t["is_sensor_placed"]) + `
          Sensor Mapping on Floor Plan
        </div>
        <div class="col-sm-4" >
          <span class="font-italic">Last Updated: ` + formatDate(t["sensor_mapping_update_time"]) + ` </span>
        </div>
        <div class="col-sm-2">
          <a href="/tasks/sensors_mapping/` + t["id"] + `" class="btn btn-primary btn-sm ">Add</a>
        </div>
      </div>
    </div>
  </div>
  <div class="col-md pt-5 pb-5">
    <div class="d-flex justify-content-end">                     
   ` + formatFunctions(user, t) + `
    </div>
  </div>
</div>`;
  // set up admin 
  if (user == "True") {
    v = v + formatUser(t);
  }
  return v;
}

function formatUploadFile(t,user){
  if(user == "True"){
    return `<div class="col-sm">
    <a href="#loTModal" data-toggle="modal" class="btn btn-primary btn-sm" onclick="uploadTask('loT','/tasks/upload_ioT_sensor_file/` + t["id"] + `','` + t['name'] + `');">Upload</a>
    </div>`;
  }
  return ``;
}
// format the task section
function formatFunctions(user, t) {
  var merge_file = t["merge_file"];
  //  status message
  if (merge_file) {
    return `<div class="container">Your data analysis is available.<br><span class="font-italic"> Last Updated: ` + formatDate(t["merge_time"]) + `</span></div>`;
  }
  //  format the run dara analysis button for admin user
  if (user == "True") {

    if (t["is_step1"] && !merge_file) {
      return `<input class="btn btn-sm btn-primary" type="button" value="Run Data Analysis" id="runDataAnalysis" onclick="runDataAnalysis('/analysis/run_data_analysis/` + t["id"] + `');" />`;
    } else if (!t["is_step1"] && !merge_file) {
      return ``;
    }
  } else {
    // status message for regular user
    if (t["status_id"] == 4) {
      var v = "You have submitted data";

      if (t["submit_time"] != null && t["submit_time"] != "") {
        v += " on " + formatDate(t["submit_time"]);
      }
      return v + ". We are processing your data.";
    } else {
      if (t["is_step1"]) {
        // might need resubmit
        return `<button class="btn btn-primary btn-sm " onclick="sendNotification('/tasks/submit_task/` + t["id"] + `')">Submit Data for Analysis</button>`;
      } else {
        return ``;
      }
    }

  }

}
/*format date 
  date_str: the date 
*/
function formatDate(date_str) {
  if (date_str != null) {

    date_str = date_str.substring(0, date_str.indexOf("."));
    return date_str = UTC2Local(date_str);
  }
  return "";
}

/* format file section in task
file: file type's name. options['Building Test.pdf, loT.csv, Weather.csv']
t: task oject
*/
function formatFileName(file, t) {
  if (file == "Building Test.pdf") {
    if (t["is_buildingtest_report"] == true) {
      return `(<a href="/reports/view_customized_report/` + t["id"] + `">` + file + ` </a>)`;
    }
  }

  if (file == "loT.csv") {
    if (t["ioT_time"] !== null && t["ioT_time"] != "") {
      return `(<a href="` + t["ioT_link"] + `" download>` + file + ` </a>)`;
    }
  }

  if (file == "Weather.csv") {
    if (t["weather_upload_time"] !== null && t["ioT_time"] != "") {
      return `(<a href="` + t["weather_link"] + `" download>` + file + ` </a>)`;
    }
  }




  return ``;
}
/* format button text for task
date: the date
if date exits, show update text. Otherwise: add text
*/
function formatButton(date) {
  if (date == null) {
    return "Add";
  }
  return "Update"
}
/*format status icon
flag:the status of the file
*/
function formatStatus(flag) {
  if (flag == false) {
    return "material-icons status_1";
  } else {
    return "material-icons status_5";
  }
}

function formatStatusWithMsg(flag) {
  if (flag == false) {
    return `<span class="material-icons status_1 align-middle">fiber_manual_record</span>`;
  } else {
    return `<span class="material-icons status_5 align-middle">fiber_manual_record</span>`;
  }
}


//on click upload floor plan modal
function updateFloorPlan(value, text, img_path, name, width, height, target) {
  //populate form value
  //append floor value
  $('#editFloorPlan_floors option').each(function () {
    if ($(this).val() == value) {
      $(this).remove();
    }
  });
  $("#editFloorPlan_floors").append("<option value=" + value + ">" + text + "</option>");

  // sort value
  // sortSelect(document.getElementById('editFloorPlan_floors'));
  $("#editFloorPlan_floors").html($("#editFloorPlan_floors option").sort(function (a, b) {
    return a.value == b.value ? 0 : parseInt(a.value) <= parseInt(b.value) ? -2 : 1
  }));

  $("#editFloorPlan_floors").val(value).trigger("change");
  $("#editFloorPlan_width").text(width);
  $("#editFloorPlan_height").text(height);


  //create url
  var dropZoneElement = document.getElementById("editFloorPlan_file").closest(".drop-zone");
  var thumbnailElement = dropZoneElement.querySelector(".drop-zone__thumb");

  // First time - remove the prompt
  if (dropZoneElement.querySelector(".drop-zone__prompt")) {
    dropZoneElement.querySelector(".drop-zone__prompt").remove();
  }

  // First time - there is no thumbnail element, so lets create it
  if (!thumbnailElement) {
    thumbnailElement = document.createElement("div");
    thumbnailElement.classList.add("drop-zone__thumb");
    dropZoneElement.appendChild(thumbnailElement);
  }
  thumbnailElement.dataset.label = name;
  thumbnailElement.style.backgroundImage = `url('` + img_path + `')`;
  $("#editFloorPlanModal form").attr("action", "/buildings/edit_floor_plan/" + target);
  $("#editFloorPlanModal").modal("show");
}
//submit form by ajax
function submitTask(where) {
  // show these two errors with css
  // event.preventDefault();
  validateList('sensors');
  validateList('floors');
   //UPDATE VALUE
   var isSetpoint = $("#test_setpoint").val();
   var isWeekend = $("#test_weekendOccupancy").val();
   if (isSetpoint == "True") {
       convertFtoC("test_weekdayOccupiedSetpoint");
       convertFtoC("test_weekdayUnoccupiedSetpoint");
       if (isWeekend == "True") {
         convertFtoC("test_weekendOccupiedSetpoint");
         convertFtoC("test_weekendUnoccupiedSetpoint");
       }
   }
  var form = $("#performanceTestForm");

  if ($(form)[0].checkValidity() === true) {
   

    // update msg card
    $("#msgName").text($("#test_name").val());
    var fd = new FormData(form[0]);
    var sensors_list = $("#test_sensors").val();
    var floor_list = $("#test_floors").val();
    fd.append("sensors", JSON.stringify(sensors_list));
    fd.append("floors", JSON.stringify(floor_list));
    $.ajax({
      type: 'POST',
      url: where,
      data: fd,
      processData: false,
      contentType: false,
      success: function (data) {
        $("#successMsgCard").modal("show");
      },
      error: function (jqXHR, error, errorThrown) {

      }
    });
  }


}

// pupluate the upload form value
function uploadTask(where, link, name) {
  $("#" + where + "_versionName").text(name);
  $("#" + where + "Form").attr("url", link);
}



// validation for test name. the values(a list) are from the backend
function validateTestName(values) {
  var name = document.getElementById("test_name");
  var feedback = $("#test_name").closest(".col-md-2").find(".invalid-feedback");
  var testExisted = "Performance Test Exists";
  if (values.includes(name.value) && name.value.trim() != "") {
    name.setCustomValidity(testExisted);
    feedback.text(testExisted);
  } else {
    name.setCustomValidity("");
    feedback.text("");
  }
}

//validation for start date 
// past date can't less than 2019 and any schedule future test need
//to be winthin 3 years
function validateStartDate() {
  var past_date = new Date('2019-01-01');
  var today = new Date();
  var yyyy = today.getFullYear();
  var s = document.getElementById("test_startDate");
  var e = document.getElementById("test_endDate");
  var feedback2 = $("#test_endDate").closest(".col-md-2").find(".invalid-feedback");
  var inputDate = new Date(s.value);
  var feedback = $("#test_startDate").closest(".col-md-2").find(".invalid-feedback");
  var emptyText = "Please Choose a Start Date";
  var startDategreaterText = "Start Date Must Be Greater Than 2019-01-01";
  var startYearText = "Start Year Must Within 3 Years"
  if (s.value.trim() == "") {
    s.setCustomValidity(emptyText);
    feedback.text(emptyText);
    e.value = "";
    feedback2.text(emptyText);

  } else if (Date.parse(s.value) < Date.parse(past_date)) {
    s.setCustomValidity(startDategreaterText);
    feedback.text(startDategreaterText);
    e.value = "";
    feedback2.text(startDategreaterText);
  } else if (inputDate.getFullYear() > yyyy + 3) {
    s.setCustomValidity(startYearText);
    feedback.text(startYearText);
    e.value = "";
    feedback2.text(startYearText);

  } else {
    s.setCustomValidity("");
  }

}

//valdiate end date which need to be within 14 days after the start date
function validateEndDate() {
  var s = document.getElementById("test_startDate");
  var futureDate = new Date(s.value);
  futureDate.setDate(futureDate.getDate() + 14);
  console.log(futureDate);
  var e = document.getElementById("test_endDate");

  var feedback = $("#test_endDate").closest(".col-md-2").find(".invalid-feedback");
  var emptyText = "Please Choose an End Date";
  var greaterText = "End Date Must Be Greater Than Start Date";
  var rangeText = "End Date Must Be Within 14 Days From the Start Date";
  var startDateEmpty = "Please Choose an Start Date";
  if (s.value != "") {
    if (e.value.trim() == "") {
      e.setCustomValidity(emptyText);
      feedback.text(emptyText);
    } else if (Date.parse(e.value) <= Date.parse(s.value)) {
      e.setCustomValidity(greaterText);
      feedback.text(greaterText);
    } else if (Date.parse(e.value) > futureDate) {
      e.setCustomValidity(rangeText);
      feedback.text(rangeText);
    } else {
      e.setCustomValidity("");
    }
  } else {
    e.setCustomValidity(startDateEmpty);
    feedback.text(startDateEmpty);
  }
}

//valdiate set point, to set the others form values required or not
function validateSetPoint() {
  var value = $("#test_setpoint").val();
  if (value == "True") {
    $(".setpoint").show();
    $(".setpoint input").attr("required", '');
  } else {
    $(".setpoint").hide();
    $(".setpoint input").val("");
    $(".setpoint input").removeAttr('required');
  }

  var weekend = $("#test_weekendOccupancy").val();
  if (weekend == "False") {
    $(".weekend").hide();
    $(".weekend input").val("");
    $(".weekend input").removeAttr('required');
  }

}

//validate weekend occupancy, to set others form values required or not
function validateWeekendOccupancy() {
  var value = $("#test_weekendOccupancy").val();
  var setpoint = $("#test_setpoint").val();
  if (value == "True") {
    $(".weekend").show();
    $(".weekend input:eq(0)").attr("required", '');
    $(".weekend input:eq(1)").attr("required", '');
    $(".weekend input:eq(3)").attr("required", '');
    $(".weekend input:eq(4)").attr("required", '');

    if (setpoint == "True") {
      $(".weekend input:eq(2)").attr("required", '');
      $(".weekend input:eq(5)").attr("required", '');
    }
  } else {
    $(".weekend").hide();
    $(".weekend input").val("");
    $(".weekend input").removeAttr('required');
  }

}



//set sensors and floors list valdiation
//because using select2 can't show the error field
function validateList(type) {
  var values = $("#test_" + type).val();
  if (values == null) {
    $("#test_" + type).closest(".col-md-3").find(".select2-selection ").css("border-color", "red");
  } else {
    $("#test_" + type).closest(".col-md-3").find(".select2-selection ").removeAttr("style");
  }
  //update text value
  if (values != null) {
    $("#test_" + type + "_num").text(values.length);
  } else {
    $("#test_" + type + "_num").text(0);
  }

}


//validate occupied start time, to set the unoccupied end time
//type: weekend / weekday
function validateStartTime(type) {
  var c = $('#test_' + type + 'OccupiedStart').val().split(':');
  var y0 = (+c[0]);
  var y1 = (+c[1]);
  if (y1 == 0) {
    y1 = 60
    y0 = y0 - 1;

  }
  y1 = y1 - 1;
  if (y0.toString().length == 1) {
    c[0] = '0' + y0.toString();
  } else {
    c[0] = y0.toString();
  }
  if (y1.toString().length == 1) {
    c[1] = '0' + y1.toString();
  } else {
    c[1] = y1.toString();
  }

  var end_var = (c[0]) + ':' + c[1];
  $('#test_' + type + 'UnoccupiedEnd').val(end_var);

}

//validate occupied end time, to set the unoccupied start time
function validateEndTime(type) {
  var a = $('#test_' + type + 'OccupiedEnd').val().split(':');
  var x0 = (+a[0]);
  var x1 = (+a[1]);
  if (x1 == 59) {
    x1 = -1;
    if (x0 == 23) {
      x0 = 0;
    } else {
      x0 = x0 + 1;
    }
  }
  x1 = x1 + 1;
  if (x1.toString().length == 1) {
    a[1] = '0' + x1.toString();
  } else {
    a[1] = x1.toString();
  }
  if (x0.toString().length == 1) {
    a[0] = '0' + x0.toString();
  } else {
    a[0] = x0.toString();
  }


  var start_var = (a[0]) + ':' + a[1];
  $('#test_' + type + 'UnoccupiedStart').val(start_var);

}

function convertFtoC(sp_id) {
  var unit = $("#" + sp_id + "_unit").val();
  var value = $("#" + sp_id).val();
  var result;
  if (unit == "fahrenheit") {
    result = Math.round(((parseFloat(value) - 32) * 5) / 9,2);
    $("#" + sp_id).val(result);
    $("#" + sp_id + "_unit").val("celsius");
  }
}

function validateEndDateForData(id){


  var text= $("#version_"+id).find("td:nth-child(3)").text();
  var endDate = Date.parse(text);
  var today_text = new Date().toLocaleDateString();
  var today = Date.parse(today_text);
  if(today>endDate){
    
    $.ajax({
      type: 'POST',
      url:"/tasks/get_real_time_file/"+id,
      processData: false,
      contentType: false,
      success: function (data) {
        if(data=="successful"){
            $("#uploadSuccessCard h6").text("You have gotten data successfully");
            $("#uploadSuccessCard").modal("show");
        }else{
          $("#uploadErrorCard h6").text("Error - Failed to get the data");
          $("#uploadErrorCard").modal("show");

        }
    
      },
      error: function (jqXHR, error, errorThrown) {
        $("#uploadErrorCard h6").text("Error - Failed to get the data");
        $("#uploadErrorCard").modal("show");
      }
    });
    //send to message
  }else{
    //pop up message
    $("#uploadErrorCard h6").text("Error - Failed to get data since it haven't finished collecting");
    $("#uploadErrorCard").modal("show");
  }

}