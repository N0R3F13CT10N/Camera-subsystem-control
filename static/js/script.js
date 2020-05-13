$(document).ready(function() {
    var timeout = setInterval(reloadAngle, 200);
    function reloadAngle () {
    $.ajax({
      url: '/angle_feed',
      type: 'POST',
      success: function(result){
          $("#horizAngle").text("Horizontal angle: "+ result.horiz);
          $("#vertAngle").text("Vertical angle: " + result.vert);
          }
      });
}

$("#btnLeft").click(function(){
    $.ajax({
        url: '/rotate_left',
        type: 'POST'
    });
});

$("#btnRight").click(function(){
    $.ajax({
        url: '/rotate_right',
        type: 'POST'
    });
});

$("#btnUp").click(function(){
    $.ajax({
        url: '/rotate_up',
        type: 'POST',
    });
});

$("#btnDown").click(function(){
    $.ajax({
        url: '/rotate_down',
        type: 'POST'
    });
});

$("#btnDefault").click(function(){
    $.ajax({
        url: '/rotate_default',
        type: 'POST'
    });
});

$("#btnToggleMode").click(function(){
    $.ajax({
        url: '/toggle_mode',
        type: 'POST',
        success: function(result){
              $("#mode").text(result);
             }
        });
    });
});