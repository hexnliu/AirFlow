$(document).ready(function() {
  // $(".js-select2").select2({
  //   allowClear: true,
  //   tags: true 
  // });
  // set the field to mutiple select
  $('#s1_q9').multiselect( {});
  
  $('.custom-file input').change(function (e) {
    if (e.target.files.length) {
      $(this).next('.custom-file-label').html(e.target.files[0].name);
    }
  });
  //show and hide the other section for user input
    $("#s_section1 .otherOption").change(function(){
         var id = $(this).attr("id");
        if(id!="s1_q11" && id!="s1_q11_2" && id!="s1_q8"){
          if($(this).val()=="other" || $(this).val()=="no"  ){
            $("."+id+"_other").show();
            $("."+id+"_other").val("");
          }else{
            $("."+id+"_other").hide();
          }
        }else{
          if($(this).val()=="yes" ){
            $("."+id+"_other").show();
            $("."+id+"_other").val("");
          }else{
            $("."+id+"_other").hide();
          }
        }
  
    });
   //show and hide the other section for user input
    $("#s_section2 .otherOption").change(function(){
      var id = $(this).attr("id");
  
       if($(this).val()=="yes"  ){
         $("."+id+"_other").show();
         $("."+id+"_other").val("");
       }else{
         $("."+id+"_other").hide();
       }
  
  });
  
  /*submit the survey form */
  $('#surveyForm').submit(function (event) {
    event.preventDefault();
    if ($('#surveyForm')[0].checkValidity() === false) {
        event.stopPropagation();
    } else {
      var formData = new FormData($("#surveyForm")[0]);
      var where=$("#surveyForm").attr("action");
      formData.set("s1_q9[]",JSON.stringify($("#s1_q9").val()));//replace the value by getting its options stringfied
      $.ajax({
        type: 'POST',
        url: where,
        data:formData,
        processData: false,
        contentType: false,
        success: function(data) {
         
          location.reload();
        }
       });
    }
  });
  


  
    
  });