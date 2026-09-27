$(function () {

  $.ajax({
    url: './friendgroup',
    type: 'POST',
    data: {

    }
  })
    .done((data) => {
      $('#res').html(data);

    })
    .fail((error) => {
      console.error(error);
    })
})
