
   
jQuery.noConflict()
$(document).ready(function () {
    //set the sensor select box searchable
    $(".search-select2").select2({
    });
});
/*submit sensor mapping 
floor: floor value
task_id: current performance task id
Note that list is global variable holding a list of marker objects
*/
function submitSensors(floor,task_id) {
    fd = new FormData();
    fd.append("floor", floor);
    fd.append("data", JSON.stringify(list));
    $.ajax({
        type: 'POST',
        url: '/tasks/sensors_mapping/'+task_id,
        data: fd,
        processData: false,
        contentType: false,
        success: function (data) {
        $("#successMsg").show();
        var modal = document.getElementById("uploadSuccessCard");
        modal.style.display = "block";
        },
        error: function (jqXHR, error, errorThrown) {
        $("#successMsg").hide();
        }
    });
}
/*return a row in table for selecting sensor
id:marker id which is a number. starting from 0

*/
function markerRecord(id){
    var num=id+1;//display the marker id starting from 1
    var text =$("#zoom-marker-img" + id + " span").text();
    $("#zoom-marker-img" + id + " span").text(num+":"+text);//update the marker caption
    return `        
    <tr class="bg-highlight" id="row_`+id+`">
    <th>`+num+`</th>
    <td>
        <select onchange="updateText(`+id+`)" class="sensor_select2" id="select_`+id+`">
            `+getSensorOptions()+`
        </select>
    </th>
    <td>
        <img class="btn-img btn-img-delete" onclick="deleteMarker(`+id+`)" src="/static/images/delete_outline-pink.svg" >
    </td>
</tr>`
}

/* get the options of available sensors
Note that: select_sensors_list is global variable which shows all available sensors for this floor in performance task,
when user click one sensor, the rest of the option will filter out any selected value.
*/
function getSensorOptions(){
    var options=`<option value="">New Sensor</option>`;
    if(select_sensors_list.length>0){
        for(var i =0;i<select_sensors_list.length;i++){
            options+=` <option value="`+select_sensors_list[i].name+`">`+select_sensors_list[i].name+` - `+select_sensors_list[i].type+ `</option>`
        }
    }
    return options;
}
/*update the marker caption text
id: marker id which is a number
*/
function updateText(id){
    var value= $("#select_"+id).val();
    var num= id+1;
    //update list id too
    list[id]["sensor"] = value;
    select_sensors_list = select_sensors_list.filter(function(el) { return el.name != value; });//remove the sensor option for the rest of the select box
    $("#zoom-marker-img" + id + " span").text(num+" : "+value);
    $("#zoom-marker-img" + id + " span").css("background","#055ba6");
    $("#row_"+id).removeClass("bg-highlight");//remove the background color from pink to blue
}
/*delete markder by id
id: marker id
*/
function deleteMarker(id) {
    //get sensor value and restore them for the rest of the select box
    var sensor_name =list[id]["sensor"];
    var sns_obj = sensors_copy_list.find(o => o.name === sensor_name);
    if(sns_obj!=undefined){
        select_sensors_list.push(sns_obj);
    }
    delete list[id];//delete it from variable
    $('#zoom-marker-img').zoomMarker_RemoveMarker(id);//remove the marker
    var myobj = document.getElementById("row_" + id);//remove the row that containing value
    myobj.remove();
  }
  