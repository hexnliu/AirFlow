$(document).ready(function () {
  //set the view image modal, close it by click the icon
  $("#viewImageModal .close").click(function(){
    $("#viewImageModal").hide();
  });
  //set up data table for sensor placement table
    var table = $('#manageSensors').DataTable({
      "scrollX": true,
      "pageLength": 60,
      "dom": 'bfrtip',
      "bInfo": false,
      "bLengthChange": false,
      "responsive": true,
      'columnDefs': [{
        'targets': 'no-sort',
        'searchable': true,
        'orderable': false,
        'className': 'dt-body-center',
      }],
       "order": [[1, 'asc']],
      "select": true,
    });
    //set up data table for location and group table
    var table = $('.manageOther').DataTable({
      "scrollX": true,
      "pageLength": 60,
      "dom": 'bfrtip',
      "bInfo": false,
      "bLengthChange": false,
      "responsive": true,
      'columnDefs': [{
        'targets': 'no-sort',
        'searchable': true,
        'orderable': false,
        'className': 'dt-body-center',
      }],
       "order": [[0, 'asc']],
      "select": true,
    });

    //process the all sensor placements
    $(document).on('click', "#addAllPlacementsBtn", function (e) {
      var errorsRec =[];
      fd = new FormData();
      var table = document.getElementById('manageSensors');//get the table
      var listOfPlacements = [];
      //get all rows
      for (var i = 1; i < table.rows.length; i++) {
        var obj = {};
        var record = table.rows[i];
        var sensor_id = record.cells[0].querySelector('input').value;
        var inputValue = record.cells[1].querySelector('select').value;
        var floorValue = record.cells[2].querySelector('select').value;
        var locationValue = record.cells[3].querySelector('select').value;
        var perimeterValue = record.cells[4].querySelector('select').value;
        var thermostatrValue = record.cells[5].querySelector('select').value;
        if (floorValue != "" && locationValue != "" && perimeterValue != "" && thermostatrValue !="") {
          obj["sensorId"] =sensor_id;
          obj["sensorNumber"] = inputValue;
          obj["floor"] = floorValue;
          obj["location"] = locationValue;
          obj["perimeter"] = perimeterValue;
          obj["thermostat"] = thermostatrValue;
          obj["groupName"] = record.cells[6].querySelector('select').value;
          obj["notes"] = record.cells[7].querySelector('textarea').value;
          listOfPlacements.push(obj);
          //valdaite the required fields
        }else if(!(floorValue == "" && locationValue == "" && perimeterValue == "" && thermostatrValue =="")){
          errorsRec.push(inputValue);
        }
      }
      //check if the there are any missing values for certain sensor
      if(errorsRec.length>0){
        //pop up the modal and show them
        $("#msgModal").modal("show");
        var s ="<ul>";
        for(var i=0;i<errorsRec.length;i++){
          s+="<li>Sensor " +errorsRec[i]+"</li>";
        }
        s+="</ul>";
        $("#error_list").html(s);//render the error list
      }else{
        //udpate them in server
        fd.append("list", JSON.stringify(listOfPlacements));
          $.ajax({
            type: 'POST',
            url: "/placements/add_sensor_placement/"+$("#select_2_test").val(),
            data: fd,
            processData: false,
            contentType: false,
            success: function (data) {
              window.location.reload(true);
            }
          });
      }
    });
});  

/*update location information
id: lcoation id
where: element id of the certain location id
*/
function updateInfo(id,where) {
  fd = new FormData();
  fd.append("name", $('#' + id + '_'+where+'_name').val());
  fd.append("description", $('#' + id + '_'+where+'_description').val());
  fd.append("notes", $('#' + id + '_'+where+'_notes').val());  
  fd.append("company", $('#' + id + '_'+where+'_company').val());
  // var link = "/locations/edit_location/" + id;
  $.ajax({
    type: 'POST',
    url: "/"+where+"s/edit_"+where+"/" + id,
    data: fd,
    processData: false,
    contentType: false,
    success: function (data) {
      window.location.reload(true);
    }

  });
}
/*update sensor placement
id: sensor placement record id
*/
function updatePlacement(id) {
  //get related field value by id
  var image = $('#sp_' + id + '_img_file').prop('files')[0];
  var type =$("#sp_"+id+"_img_type").val();
  var floor = $('#sp_' + id + '_floor').val();
  var location = $('#sp_' + id + '_location').val();
  var perimeter = $('#sp_' + id + '_perimeter').val();
  var thermostat = $('#sp_' + id + '_thermostat').val();
  var groupName = $('#sp_' + id + '_groupName').val();
  var notes = $('#sp_' + id + '_notes').val();
  var num =$('#sp_' + id + '_num').val();
  //validate the required fields
  if(num!="" && location !="" && floor !="" && thermostat!=""){
    fd = new FormData();
    fd.append("sensorNumber",num);
    fd.append("location", location);
    fd.append("floor", floor);
    fd.append("thermostat", thermostat);
    fd.append("groupName", groupName);
    fd.append("perimeter", perimeter);
    fd.append("notes", notes);
    fd.append("img", image);
    fd.append("img_type", type);
  
    $.ajax({
      type: 'POST',
      url: '/placements/edit_sensor_placement/'+id,
      data: fd,
      processData: false,
      contentType: false,
  
      success: function (data) {
        // window.location.reload(true);
        $("#uploadSuccessCard").modal("show");
        
      }
    });
  }else{
    $("#msgModal").modal("show");
    var s="<ul><li>Sensor " +num+"</li></ul>";
    $("#error_list").html(s);

  }

 
}