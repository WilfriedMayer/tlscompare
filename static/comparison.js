var rid;
var http_window;
var https_window;

$.ajaxSetup({ cache: false });

$(document).ready( function(){
    $(".btn_invalid").click(function(){
        $(".validity").text("not equal");
        end("invalid", $(this).data('reason'));
    });
    $(".btn_valid").click(function(){
        $(".validity").text("equal");
        end("valid", $(this).data('reason'));
    });
    $(".btn_start").click(start);

    $(".dataset_dropdown").click( function(){
        var that=$(this);
        $.get( "/dataset/"+$(this).data('dataset'), function() {
            $(".dataset_dropdown").parents().removeClass('active');
            that.parent().addClass('active');
        });
    });

    $(".change_reason").click( function(){
        var that=$(this);
        $.get( "/change_reason/"+that.data('rid') + "?reason=" + that.data('reason'), function() {
            that.parent().parent().parent().html( that.data('reason') );
        });
        wnd_close();
    });

    $(".reopen").click( function() {
        wnd_open($(this).data("http-url"), $(this).data("https-url"))
    });

    $(function() {
        $('.tooltip-wrapper').tooltip({delay: 500});
    });
});


function start(){
    $("#submit").hide();
    $(".btn_start").prop('disabled', true);
    $(".btn_valid").prop('disabled', false);
    $(".btn_invalid").prop('disabled', false);

    load_pages();
}

function end(endpoint, reason){
    wnd_close();
    $(".btn_start").prop('disabled', false);
    $(".btn_valid").prop('disabled', true);
    $(".btn_invalid").prop('disabled', true);

    $("#comparing").hide();

    var reason_arg = '';
    if (reason != null){
        reason_arg = '?reason=' + reason;
    }

    $.get( "/" + endpoint + "/" + rid + reason_arg, function () {
        $("#counter").text(parseInt($("#counter").text())+1);
        $("#submit").show();
    });
}

function load_pages(){
    $.get( "/comparison", function( data ) {
        $(".http_url").text(data.http_url);
        $(".https_url").text(data.https_url);
        $("#comparing").show();
        rid = data.rid;
        wnd_open(data.http_url, data.https_url)
    });
}

function wnd_open(http_url, https_url){
    var calc_h = screen.height / 2;
    var calc_top = screen.height - calc_h;
    var calc_w = screen.width/2-30;
    var calc_l = screen.width/2+100;
    http_window = window.open(http_url,"","top="+calc_top+",left=1,height="+calc_h+",width="+calc_w+",menubar=no,scrollbar=no,toolbar=no,status=no");
    https_window = window.open(https_url,"","top="+calc_top+",left="+calc_l+",height="+calc_h+",width="+calc_w+",menubar=no,scrollbar=no,toolbar=no,status=no");
}

function wnd_close(){
    http_window.close();
    https_window.close();
}