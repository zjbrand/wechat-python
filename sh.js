//javacsript--ajax
//jquery
//json
$(function () {
  $('#sh').on('click', function () {

    $.ajax({
      url: './searchfriend',
      type: 'POST',
      data: {
        'email': $('#email').val()
      }

    })
      .done((res) => {
        $('#res').html(res);
        console.log('success')
      })
      .fail((res) => {
        $('#res').html(res.responseText);
        console.log(res, 'failure')
      })
  })

})

function add_friend() {
  var to = $('#to').text();
  //console.log(to)

  $.ajax({
    url: './add_friend',
    type: 'POST',
    data: {
      'to': to
    }
  })
    .done((res) => {
      $('#res').html(res);
      //alert('友達になりました')
    })
    .fail((res) => {
      $('#res').html(res.responseText);
    })



}