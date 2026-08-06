/*run data analysis
url:the url of rundataanalysis + id eg./whereto/taskId
*/
function runDataAnalysis(url) {
  $('#loading-wrapper').show(0);
  if ($('#promptModal').length > 0) {
    // Exists.
    var modal = document.getElementById("promptModal");
    modal.style.display = "none";
  }
  $.ajax({
    type: 'POST',
    url: url,   
    processData: false,
    contentType: false,
    success: function (data) {
      //
      $("#uploadSuccessCard h6").text("You have run data analysis successfully.");
      var modal = document.getElementById("uploadSuccessCard");
      modal.style.display = "block";
    },
    error: function (jqXHR, error, errorThrown) {
      $("#uploadErrorCard h6").text("Error - Failed to run data analysis due to ("+error+"----"+errorThrown+")");
      var modal = document.getElementById("uploadErrorCard");
      modal.style.display = "block";
    }
    

  });
}

/*send notfication by email 
where: url
*/
function sendNotification(where,building=0){
  if ($('#promptModal').length > 0) {
    // Exists.
    var modal = document.getElementById("promptModal");
    modal.style.display = "none";
  }
  $.ajax({
    type: 'POST',
    url: where,
    processData: false,
    contentType: false,
    success: function (data) {
      $("#uploadSuccessCard h6").text("You have sent notification successfully");
      if(building==0){
        $("#uploadSuccessCard").modal("show");
      }else{
        window.location.href = "/tasks/view_task/"+building;
      }
    },
    error: function (jqXHR, error, errorThrown) {
      $("#uploadErrorCard h6").text("Error - Failed to sent notification");
      $("#uploadErrorCard").modal("show");
    }
  });

}

/*convert the time to user local time
t: timestamp string
*/
function UTC2Local(t){
  // Intel, doesn't support safari
  try{
   var time = Date.parse(t);
   var timezone= Intl.DateTimeFormat().resolvedOptions().locale;
   var display = new Intl.DateTimeFormat(timezone,{ dateStyle: 'full', timeStyle: 'long' }).format(time);
   return display.toString();
  }catch(error){
    return t+" UTC";
  }
}


/*check current user screen size */
function getBrowserWidth(){
  if(window.innerWidth < 768){
      // Extra Small Device
      return "xs";
  } else if(window.innerWidth < 991){
      // Small Device
      return "sm"
  } else if(window.innerWidth < 1199){
      // Medium Device
      return "md"
  } else {
      // Large Device
      return "lg"
  }
};


/*view image modal usage on placement page , upload floor plan, analysis page
img_path:image location
floor: floor value
*/
function viewImage(img_path,floor){
  var modal = document.getElementById("viewImageModal");
  // Get the image and insert it inside the modal - use its "alt" text as a caption
  var modalImg = document.getElementById("viewImage");
  var captionText = document.getElementById("caption");//set the image name on the bottom of the image
  modal.style.display = "block";
  modalImg.src = img_path;
  captionText.innerHTML = floor+" image";

}

/*create image preview and update the img_type
where: the element id 
img_type: two option (change and delete, which indicate server to update or delete the image)
*/
function previewImage(where, file) {
  document.getElementById(where + '_img').src = createObjectURL(file);
  // update the image value
  $('#' + where + '_img_type').val('change');
}
/*delete image on the preview
where: the element id of where to delete the preview
*/
function deleteImage(where) {
  // replace preview value
  document.getElementById(where + '_img').src = '/media/image_upload.png';
  // update type and file value
  $('#' + where + "img_file").val('');//remove the file
  $('#' + where + '_img_type').val('delete');//indicate the server to delete the file if file exits in server
  
}
/*convert image url to base 64
where: the element id of the file field
*/
function createObjectURL(file) {
  if (window.webkitURL) {
    return window.webkitURL.createObjectURL(file);
  } else if (window.URL && window.URL.createObjectURL) {
    return window.URL.createObjectURL(file);
  } else {
    return null;
  }
}

// passing input id to get upperCase
function toUpperCase(where) {
  $(where).val(function () {
    return this.value.toUpperCase();
  })
}
// deleteRecordModal
//url: where to delete
//name: delete content name
function deleteRecord(url, name) {
  $("#deleteBtn").attr("onclick", "window.location.href='"+url+"'");
  $("#deleteRecordId").text(name);
  $("#deleteModal").modal("show");
}

/*download content by link
content:content want to download
fileName: name of the file
contentType: type of the content   eg.text/javascript
*/
function download(content, fileName, contentType) {
  const a = document.createElement("a");
  const file = new Blob([content], {
    type: contentType
  });
  a.href = URL.createObjectURL(file);
  a.download = fileName;
  a.click();
}

/*validate extension for file upload form
allowedFiles: the file types are valid
file: the uploaded file
*/
function validateExtension(allowedFiles,file) {
 var fname =file.value.toLowerCase();
 var extensions = "."+fname.slice((fname.lastIndexOf(".") - 1 >>> 0) + 2);
 //valid extensions for image type
  var fileTypes = [
    ".apng",
    ".bmp",
    ".gif",
    ".jpeg",
    ".pjpeg",
    ".png",
    ".svg+xml",
    ".tiff",
    ".webp",
    ".x-icon",
    ".jpg"
  ];
  if(allowedFiles !="image/*"){
    //get the list of the allowing file type for accept attributes
    if(allowedFiles!=undefined && allowedFiles!=null){
      fileTypes=allowedFiles.split(" ");
    }
  }

  //check if the file contains the extension
  if(!fileTypes.includes(extensions)){
    file.setCustomValidity("Please upload a valid format file");
    return false;
  }

  if(extensions){
    file.setCustomValidity("");
    return true;
  }
  file.setCustomValidity("");
  return true;
}



// form validation
(function () {
  'use strict'

  // Fetch all the forms we want to apply custom Bootstrap validation styles to
  var forms = document.querySelectorAll('.needs-validation')

  // Loop over them and prevent submission
  Array.prototype.slice.call(forms)
    .forEach(function (form) {
      form.addEventListener('submit', function (event) {
        if (!form.checkValidity()) {
          event.preventDefault()
          event.stopPropagation()
        }

        form.classList.add('was-validated')
      }, false)
    })
})();



//create drop file method
document.querySelectorAll(".drop-zone__input").forEach((inputElement) => {
  const dropZoneElement = inputElement.closest(".drop-zone");
  const type = inputElement.getAttribute("accept");// get the file accept type
  const id=inputElement.id;
  dropZoneElement.addEventListener("click", (e) => {
    inputElement.click();
  });

  inputElement.addEventListener("change", (e) => {
    if (inputElement.files.length) {
        validateExtension(type,inputElement);//validate file extension
        updateThumbnail(dropZoneElement, inputElement.files[0],id);  //create file preview
    }
  });
//invoke the drag file function
  dropZoneElement.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZoneElement.classList.add("drop-zone--over");
  });

  ["dragleave", "dragend"].forEach((type) => {
    dropZoneElement.addEventListener(type, (e) => {
      dropZoneElement.classList.remove("drop-zone--over");
    });
  });

  dropZoneElement.addEventListener("drop", (e) => {
    e.preventDefault();
    if (e.dataTransfer.files.length) {
      inputElement.files = e.dataTransfer.files;
      validateExtension(type,inputElement);//validate file extension
        updateThumbnail(dropZoneElement, e.dataTransfer.files[0],id);//create file preview
      
    }
    

    dropZoneElement.classList.remove("drop-zone--over");
  });
});

/**
 * Updates the thumbnail on a drop zone element.
 *
 * @param {HTMLElement} dropZoneElement
 * @param {File} file
 */
function updateThumbnail(dropZoneElement, file,id) {
  let thumbnailElement = dropZoneElement.querySelector(".drop-zone__thumb");

  // remove the prompt
  if (dropZoneElement.querySelector(".drop-zone__prompt")) {
    dropZoneElement.querySelector(".drop-zone__prompt").remove();
  }

  // create thubnail element for the first time
  if (!thumbnailElement) {
    thumbnailElement = document.createElement("div");
    thumbnailElement.classList.add("drop-zone__thumb");
    dropZoneElement.appendChild(thumbnailElement);
  }

  thumbnailElement.dataset.label = file.name;

  //Show thumbnail for image files
  
  if (file.type.startsWith("image/")) {

    var modal_id = id.substring(0,id.lastIndexOf("_"));
    console.log(modal_id);

    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = (e) => {
      thumbnailElement.style.backgroundImage = `url('${reader.result}')`;
       // check if it is add floor plan modal
      if($("#"+modal_id+"_width")!=null){
        var image = new Image();
        //Set the Base64 string return from FileReader as source.
        image.src = e.target.result;
        //Validate the File Height and Width.
        image.onload = function () {
          var height = this.height;
          var width = this.width;
          $("#"+modal_id+"_width").text(width);
          $("#"+modal_id+"_height").text(height);
          $("#"+modal_id+"_width_input").val(width);
          $("#"+modal_id+"_height_input").val(height);
          return true;
        };

      }
    };
  } else {
    thumbnailElement.style.backgroundImage = null;
  }
}





 