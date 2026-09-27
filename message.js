
/*window.onload = function () {
  getMessage();
};*/

//setInterval(getMessage, 1000);

$(function () {

  $('#send').on('click', function () {
    let url = new URL(window.location.href);
    let param = url.searchParams;
    var to = param.get('email');

    // 空のメッセージは送信しない
    if ($('#content').val() === '') {
      return;
    }

    $.ajax({
      url: './sendmessage',
      type: 'POST',
      data: {
        'content': $('#content').val(),
        'to': to
      }
    })
      .done(() => {

        // 送信後、入力欄を空にしてフォーカスを戻す
        $('#content').val('').focus();

        // メッセージ履歴を更新する
        getMessage();

      })
      .fail((error) => {
        console.error(error);
      });

  });

  // Enterキーで送信する
  $('#content').on('keydown', function (event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      $('#send').click();
    }
  });

});

function getMessage() {
  let url = new URL(window.location.href);
  let param = url.searchParams;
  var to = param.get('email');

  $.ajax({
    url: './getMessage',
    type: 'POST',
    data: {
      'content': $('#content').val(),
      'to': to
    }
  })
    .done((res) => {
      $('#history').html(res);

    })
    .fail(() => {
      $('#history').html(res);

    })
}

