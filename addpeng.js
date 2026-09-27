$(function () {

  $('#addpeng').on('click', function () {

    $.ajax({
      url: './addfriend',
      type: 'POST',
      data: {
        'content': $('#content').val()
      }
    })
      .done((data) => {
        $('#res').html(data);

      })
      .fail(() => {

      })
  })
})