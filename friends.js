$(function () {
  $.ajax({
    url: './friends',
    type: 'POST',
    data: {

    }
  })
    .done((res) => {
      $('#res').html(res);

    })
    .fail((data) => {
      $('#res').html(res);
    })


})