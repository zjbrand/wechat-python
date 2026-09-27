$(function () {
  $.ajax({
    url: './session_welcome',
    type: 'GET',
    dataType: 'json'
  }).done(function (res) {
    if (res.loggedIn) {
      $('#welcome').text('ようこそ ' + res.email);
    } else {
      $('#welcome').text('ログインしていません');
    }
  });
});