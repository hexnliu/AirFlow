
$.noConflict();
$(document).ready(function () {
  // loading show when form is submitting by ajax
  $( "form" ).submit(function( event ) {
    $('#loading-wrapper').show(0);
  });
  //hide the view image model if it is opened
  $("#viewImageModal .close").click(function(){
    $("#viewImageModal").hide();
  });

  $(".search-select2_da").select2({});
  //
  $("#select_2_test").select2({
    width:"300px"
  });
  $('.select2-multiple').select2();

  //set up select 2 for sensor associate select box, so user can search
  $("select[name='sensor']").select2({
  });
  $("select[name='sensor1']").select2({
  });
  $("select[name='sensor2']").select2({
  });

  $(".custom-range").change(function(){
    $(this).parent().find("span").text("("+$(this).val()+")");
  });

  var divWidth =$("#viewImageModal .modal-content").width();
  //initialize the zoomMarker
  $('#zoom-marker-img').zoomMarker({
    src: "/media/grey.png",
    rate: 0.0,
    width:divWidth,//set it with user's screen width
    max: 3000,
    enable_drag: false,
    zoom_lock:true
  });
  
});


/*submit analysis - generate graph button click
id: element id which form is submitting eg.g-{{value.id}}-form
traget: element id that is going to render the value eg.g-plotly-{{value.id}}-{{tab.number}}
Note that {{value}} is subcategory's id referring to menu.json
*/
function submitAnalysis(id,target){
  var form= $("#"+id);
  var width_div=id.replace("g-","");
  width_div=width_div.substring(0,width_div.indexOf("-"));//finding user's screen width in tab element #{{value.id}}
  var fd = new FormData(form[0]);
  fd.append("width",$("#"+width_div).width().toString());//use user'screen width to determine how big the graph need to be generate, specially for floor map
  var where = form.attr("action");//get the url of which graph is going to be gerneated
  // check days
  var days_id =target.replace("g-plotly-","")
  var value_id = days_id.substring(0,days_id.indexOf("-"));
  days_id= "#"+value_id+"_days_"+days_id.substring(days_id.indexOf("-")+1,days_id.length);
  console.log(days_id);
  if($(days_id).length>0){
    fd.append("days",JSON.stringify($(days_id).val()));
  }
  
  if($(form)[0].checkValidity() === true){//validation of the form
  //this form contains id in url
  $.ajax({
    type: 'POST',
    url: where,
    data: fd,
    processData: false,
    contentType: false,
    success: function (data) {
      $("#"+target).html(data); //where to render the data
      $('#loading-wrapper').hide();//hide the loading icon
    },
    error: function (jqXHR, error, errorThrown) {
    }
    });
  }

}

//set the catgory active by clicking any catgeory
function liTab(id) {
    //remove the subcatgory active
    $("#menu-content a[data-toggle='tab']").removeClass("active");
    $("#menu-content a[data-toggle='tab']").parent().removeClass("active");
    //hide the tab content
    var des_id = "des_" + id;
    $(".tab-content .tab-pane").removeClass("active");
    //set the category active with its tab content
    $("#menu-content li").removeClass("active");
    $("#" + des_id).addClass("active");
    $("#" + id).addClass("active");
  
  }
  
  //set the subcategory active and its category by clicking any subcategory
  function aTab(id, v_id) {
    //find its category id
    var category = $("#menu-content li.active").attr('id');
    if (category !== id) {
      $("#menu-content li").removeClass("active");
      $("#" + id).addClass("active");
    }
    $("#menu-content a[data-toggle='tab']").removeClass("active");  
    $(".graphSection .active").removeClass("active");
    //set the first form tab active
    $("#g-"+v_id+"-1").addClass("active");
    $("#g-"+v_id+"-1-tab").addClass("active");
    $("#g-"+v_id+"-1").addClass("show");
    

  }
  /* filter perimeter by choosing location
    id: element id of the location select box
    filter_sensor: optional for filtering out specific sensor eg.B-IEQ 
    note that Air Quality and Virus Transmission module need to filter out IEQ sensor because it does not contain value
  */
  function onLocationChange(id,filter_sensor=null){
    //find the realted perimeter id 
    var primeter= id.replace("_location_","_perimeter_");
    //find the related building id
    var floor= id.replace("_location_","_floor_");
    //check if the related perimeter exists or not. if it does, get the filtered perimeter options for users 
    var exists =document.getElementById(primeter);
    if(exists !=null){
    var fd = new FormData();
    fd.append("location",$("#"+id).val());
    fd.append("floor",$("#"+floor).val());
    if(filter_sensor!=null){
      fd.append("filter_sensor",filter_sensor);
    }
    //this form contains id in url
    $.ajax({
      type: 'POST',
      url:"/analysis/get_perimeters_by_location/"+$("#select_2_test").val(),//here getting task.id
      data: fd,
      processData: false,
      contentType: false,
      success: function (data) {
        $("#"+primeter).html(data); //render options
      },
      error: function (jqXHR, error, errorThrown) {
      }
      });
    }
  }

  /*view original floor plan with markers in modal 
    floor: floor value
    floor_text: optional
  */
  function view_origianl(floor,floor_text){
    // pop up the modal
    $("#viewImageModal").show();
    //send the value of the floor 
    var fd=new FormData();
    fd.append("floor",floor);
    //get the floor plan by passing with task id
    $.ajax({
      type: 'POST',
      url:"/analysis/view_floor_plan/"+$("#select_2_test").val(),
      data: fd,
      processData: false,
      contentType: false,
      success: function (data) {
        $("#content").html(data); //render the markers js which holds all variable 
        //check if image exits, reset the image and clean all markers
        if ($("#zoom-marker-img").attr("src") != undefined) {
          $('#zoom-marker-img').zoomMarker_CleanMarker();
          // reload image
          $('#zoom-marker-img').zoomMarker_LoadImage(image_path);//load the image by image path 
          //div width is getting from render partial.html . it is global variable
          $('#zoom-marker-div').width(divWidth);
          $('#zoom-marker-img').width(divWidth);
          $('#zoom-marker-img').on("zoom_marker_img_loaded", function(event, size){
            //load all markers
            for (var i = 0; i < markers.length; i++) {
              $('#zoom-marker-img').zoomMarker_AddMarker(markers[i]);
            }
         
        });
     
     }
      
    }
     
  });
    
  }
  /* when building change, filter location, sensors if they exist
    id: element id of building floor select box
    filter_sensor: optional eg.B-IEQ. Input the sensor type that want to filter out because no value in module
  */
  function onBuildingChange(id,filter_sensor=null){
    //get all related field of element id in the same form
    var location= id.replace("_floor_","_location_");
    var sensor= id.replace("_floor_","_sensor_");
    var sensor1= id.replace("_floor_","_compareOne_");
    var sensor2= id.replace("_floor_","_compareTwo_");
    var fd = new FormData();
    fd.append("floor",$("#"+id).val());//floor value 
    if(filter_sensor!=null){
      fd.append("filter_sensor",filter_sensor);
    }
    //get the following element in the same form
    var location_exists =document.getElementById(location);
    var sensor_exists=document.getElementById(sensor);
    var sensor1_exists=document.getElementById(sensor1);

    // floor plan
    var form_id = $("#"+id).closest("form").attr("id");
    var view_f_id =form_id.replace("g-","f-");
    view_f_id=view_f_id.replace("-form","");
    var origianl_floor_plan_exists =document.getElementById(view_f_id);
    //activate the option for viewing original floor plan on selecting floor
    if(origianl_floor_plan_exists){
      if($("#"+id).val()!="Building" && $("#"+id).val()!=""){
        $("#"+view_f_id).show();
        $("#"+view_f_id).attr("onclick","view_origianl("+$("#"+id).val()+",'"+$("#"+id+" option:selected").text()+"')");
        $("#"+view_f_id).text("View Floor plan ("+$("#"+id+" option:selected").text()+")");
      }else{
        $("#"+view_f_id).hide();
      }
      
    }

    //check if location field exits or not
    if(location_exists !=null){
    //this form contains id in url
    var primeter= id.replace("_floor_","_perimeter_");
    $("#"+primeter).html("<option value=''>Please Choose</option>");
    $.ajax({
      type: 'POST',
      url:"/analysis/get_locations_by_floor/"+$("#select_2_test").val(),
      data: fd,
      processData: false,
      contentType: false,
      success: function (data) {
        $("#"+location).html(data); //render filter location data
      },
      error: function (jqXHR, error, errorThrown) {
      }
      });
    }
    //check sensor field exits or not
    if(sensor_exists !=null){
      //this form contains id in url
      $.ajax({
        type: 'POST',
        url:"/analysis/get_sensors_by_floor/"+$("#select_2_test").val(),
        data: fd,
        processData: false,
        contentType: false,
        success: function (data) {
          $("#"+sensor).html(data); //render sensor options
        },
        error: function (jqXHR, error, errorThrown) {
        }
        });
      }
      //check if compare sensors field exits
      if(sensor1_exists !=null){
        //this form contains id in url
        $.ajax({
          type: 'POST',
          url:"/analysis/get_sensors_by_floor/"+$("#select_2_test").val(),
          data: fd,
          processData: false,
          contentType: false,
          success: function (data) {
            //render sensor options to both side
            $("#"+sensor1).html(data); 
            $("#"+sensor2).html(data);
          },
          error: function (jqXHR, error, errorThrown) {
          }
          });
        }
  }