

$(document).ready(function () {




//building image need to be created with id, let frontend to process creating building,so that we can have the building ID to put the image file
$("#building_form input[type='submit']").click(function(event){
    event.preventDeault();
    var fd= new FormData($("#building_form")[0]);
    fd.append('csrfmiddlewaretoken', '{{ csrf_token }}');
    $.ajax({
        type: "POST",
        url: "/buildings/create_building",
        data:fd,
        success: function (data) {
            window.location.reload();
        }
        });
});

// set up read countries.json file ajax call when changing the city
//this applies to building model and company model

$("#id_country").change(function () {
    var countryId = $(this).val();
$.ajax({
        type: "POST",
        url: "/buildings/get-province",
        data: {
            'csrfmiddlewaretoken': '{{ csrf_token }}',
            'country': countryId
        },
        success: function (data) {
            console.log(data.provinces);
            let html_data = '';
            data.provinces.forEach(function (data) {
                html_data += `<option value="${data}">${data}</option>`
            });
            $("#id_province").html(html_data);
        }
        });
});
$("#id_province").change(function () {
    var countryId = $("#id_country").val();
    var provinceId = $(this).val();
$.ajax({
        type: "POST",
        url: "/buildings/get-city",
        data: {
            'csrfmiddlewaretoken': '{{ csrf_token }}',
            'country': countryId,
            "province":provinceId
        },
        success: function (data) {
            console.log(data.cities);
            let html_data = '';
            data.cities.forEach(function (data) {
                html_data += `<option value="${data}">${data}</option>`
            });
            $("#id_city").html(html_data);
        }
        });
});
});