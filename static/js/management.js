$(document).ready(function () {
  // type set up select
  $('.icons_select2').select2({
    width: "100%",
  });
  // baseStation_epEui set up select
  $(".js-select2").select2({
    allowClear: true,
    tags: true // 
  });
  //set up data table for location definition table
  var locationTable = $('#manageLocations').DataTable({
    "scrollX": true,
    "pageLength": 60,
    "dom": 'bfrtip',
    "bInfo": false,
    "bLengthChange": false,
    "responsive": true,
    'columnDefs': [{
      'targets': 0,
      'searchable': true,
      'orderable': true,
      'className': 'dt-body-center',
    }],
    "select": true,
  });


  // set up datatable for inventory table
  var table = $('#manageSensors');
  var tableOptions={
    "scrollX": true,
    "pageLength": 60,
    "dom": 'Bfrtip',
    "bInfo": false,
    "bLengthChange": false,
    "responsive": true,
    'columnDefs': [{
      'targets': 0,
      'searchable': true,
      'orderable': true,
      'className': 'dt-body-center',
    }],
    'stateSave': true,
    'buttons': [
      'selectAll',
      'selectNone'
  ],
  'language': {
      'buttons': {
          'selectAll': "Select all items",
          'selectNone': "Select none"
      }
  },

    "select": true,
  };
  var dt=table.DataTable(tableOptions);


  // set up transfer sensors function
  $('#sensors-select-all').on('click', function () {
   
    // Get all rows with search applied
    var rows = dt.rows({
      'search': 'applied',
      page: 'all'
    }).nodes();

    // Check/uncheck checkboxes for all rows in the table
    $('input[type="checkbox"]', rows).prop('checked', this.checked);
    select_checkBox();
    table.DataTable().destroy();
    tableOptions.bPaginate = false;
    table.DataTable(tableOptions);
  });
  //make sure select multiple records to use the function

  $('#manageSensors tbody').on('change', 'input[type="checkbox"]', function () {
    // If checkbox is not checked
    if (!this.checked) {
      var el = $('#sensors-select-all').get(0);
      // If "Select all" control is checked and has 'indeterminate' property
      if (el && el.checked && ('indeterminate' in el)) {
        // Set visual state of "Select all" control
        // as 'indeterminate'
        el.indeterminate = true;
      }
    }
  });




});
/* check if more than 1 sensor are selected, activate the button functions */
function select_checkBox(){
  if (document.querySelectorAll('input[name="id[]"]:checked').length >= 1) {
    document.getElementById("transferSensorsBtn").disabled = false;
    document.getElementById("downloadSensorsBtn").disabled = false;
  } else {
    document.getElementById("transferSensorsBtn").disabled = true;
    document.getElementById("downloadSensorsBtn").disabled = true;
  }
}

//download selected sensors information
function downloadSensors() {
  fd = new FormData();
  var ep_list= getSelectedSensors()
  fd.append("ep_list",JSON.stringify(ep_list));
  $.ajax({
    type: 'POST',
    url: '/inventory/download_sensors_as_json_file/',
    data: fd,
    processData: false,
    contentType: false,
    success: function (data) {
      data = JSON.parse(data);
      const jsonobjs = [];
      for (var i in data) {
        item = {}
        item["epEui"] = data[i][0].epEui;
        item["nwkSnKey"] = data[i][0].nwkSnKey;
        item["nwkKey"] = data[i][0].nwkKey;
        item["shAddr"] = data[i][0].shAddr;
        item["type"] = data[i][0].type;
        item["name"] = data[i][0].name;
        item["location"] = data[i][0].location;
        item["info"] = data[i][0].info;
        jsonobjs.push(item);
      }
      const jsonData = {
        "nodes": jsonobjs
      };
      download(JSON.stringify(jsonData), "nodes.json", "text/javascript");
      setTimeout(
        function () {
          window.location.reload(true);
        }, 5000);


    }
  });
}


/*update sensors by id
sns: sensor id
*/
function updateSensor(sns) {
  fd = new FormData();
  fd.append("bs_id", $('#' + sns + '_bs_id').val());
  fd.append("epEui", $('#' + sns + '_epEui').val());
  fd.append('nwkSnKey', $('#' + sns + '_nwkSnKey').val());
  fd.append('nwkKey', $('#' + sns + '_nwkKey').val());
  fd.append('shAddr', $('#' + sns + '_shAddr').val());
  fd.append("sns_num", $('#' + sns + '_sensorNumber').val());
  fd.append("location", $('#' + sns + '_location').val());
  fd.append("info", $('#' + sns + '_info').val());
  fd.append("type", $('#' + sns + '_type').val());
  fd.append("date", $('#' + sns + '_date').val());
  fd.append("company", $('#' + sns + '_company').val());
  var link = '/inventory/edit_sensor_to_inventory/' + sns;
  $.ajax({
    type: 'POST',
    url: link,
    data: fd,
    processData: false,
    contentType: false,
    success: function (data) {
      window.location.reload(true);
    }
  });
}
// return a list of selected sensors
function getSelectedSensors(){
  var ids = [];
  $("input[name='id[]']:checked").each(function () {
    var id = $(this).val();
    ids.push(id);
  });
  return ids;
}
//transfer sensors button on clik to submit the form
function transferSensors() {
  var ids = getSelectedSensors();
  var formData = new FormData($("#transferSensorsForm")[0]);
  formData.append('row_ids', JSON.stringify(ids));
  $.ajax({
    type: 'POST',
    url: '/inventory/transfer_sensors_company/',
    data: formData,
    processData: false,
    contentType: false,
    success: function (data) {
      // success msg
      $("#transferSensorsModal").modal("hide");
      $("#uploadSuccessCard h6").text("You have updated successfully.");
      $("#uploadSuccessCard button").text("Refresh Page");
      $("#uploadSuccessCard").modal("show");
      $("#transferSensorsModal").modal("hide");
      
    
    }
  });
}

/*update location by id
id:record id
*/
function updateLocation(id) {
  fd = new FormData();
  fd.append("name", $('#' + id + '_location_name').val());
  fd.append("description", $('#' + id + '_location_description').val());
  fd.append("notes", $('#' + id + '_location_notes').val());  
  fd.append("company", $('#' + id + '_location_company').val());
  // var link = "/locations/edit_location/" + id;
  $.ajax({
    type: 'POST',
    url: "/locations/edit_location/" + id,
    data: fd,
    processData: false,
    contentType: false,
    success: function (data) {
      window.location.reload(true);
    }

  });
}

