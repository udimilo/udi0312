function ajax_with_msg(url, data){
    $('#msg span').removeClass();
    $('#msg span').addClass('info');
    $('#msg span').html('Loading...');
    $('#msg').fadeIn(250);

    var $data = null;
    if (data != null) {
        $data = data.serialize();
    }
    $.ajax({
        type: "POST", 
        url: url,
        data: $data,
        success: function(msg){
            $('#msg').fadeOut(250, function(){
                $('#msg span').removeClass();
                $('#msg span').addClass('success');
                $('#msg span').html(msg);
                $('#msg').fadeIn(250, function(){setTimeout(function(){$('#msg').fadeOut(250);},3000);});
                if (msg == 'Success'){
                    location = '/';
                }
            });
        },
        error: function(data){
            if (data.status != 0){
                $('#msg').fadeOut(250, function(){
                    $('#msg span').removeClass();
                    $('#msg span').addClass('error');
                    $('#msg span').html(data.status + ': ' + data.statusText);
                    $('#msg').fadeIn(250, function(){setTimeout(function(){$('#msg').fadeOut(250);},3000);});
                });
            }
        }
    });

    return false;
};

function show_pin(id){
    $('#msg span').removeClass();
    $('#msg span').addClass('info');
    $('#msg span').html('Loading...');
    $('#msg').fadeIn(250);
    $.ajax({
        url:'/api/pin/{0}'.replace('{0}',id),
        success: function(data){
            $('#msg').fadeOut(250);
            $('#pin_modal .content').html(data);
            $('#pin_modal .inner').css('max-height', window.innerHeight - 80);
            $('body').css('overflow', 'hidden');
            $('#pin_modal').dialog('open');
            $('.easydate').easydate();
            $('.wtr').each(function(){
                $(this).watermark($(this).attr('wtr'));
            });
        },
        error: function(data){
            $('#msg').fadeOut(250, function(){
                $('#msg span').removeClass();
                $('#msg span').addClass('error');
                $('#msg span').html(data.status + ': ' + data.statusText);
                $('#msg').fadeIn(250, function(){
                    window.setTimeout("$('#msg').fadeOut(250)",3000);
                });
            });
        }
    });
}

function bind_pins(){
    $('.easydate').easydate();

    $('.repin').each(function(){
        $(this).click(function(){
            $('#repin_modal input[name="id"]').val($(this).attr('pin_id'));
            $('#repin_modal .title').html($(this).attr('title'));
            $('#repin_modal').dialog('open');
        });
    });

    $('.pin .content').click(function(){
        show_pin($(this).attr('pin_id'));
    });
    $('.pin').hover(
        function(){$(this).find('.actions').fadeIn(200);},
        function(){$(this).find('.actions').fadeOut(100);});
};

function toggle_follow(context){
    $.ajax({
        url: context.attr('href'),
        context: context,
        success: function(data){
            var $base = context.attr('base');
            var $action = 'follow';
            if (context.attr('action') == 'follow')
                $action = 'unfollow';

            var $url = '{0}/{1}'.replace('{0}', $base).replace('{1}',$action);
            context.attr('href', $url);
            context.attr('action', $action);
            context.text($action);
        }
    });

    return false;
}

function send_linkedin_invite(form){
    $('#msg span').removeClass();
    $('#msg span').addClass('info');
    $('#msg span').html('Talking to LinkedIn...');
    $('#msg').fadeIn(250);

    $.ajax({
        type: "POST",
        url: '/api/send_linkedin_invites',
        data:form.serialize(),
        success: function(data){
            $('#msg span').removeClass();
            $('#msg span').addClass('success');
            $('#msg span').html('Invitation Sent Successfully');
            setTimeout(function(){$('#msg').fadeOut(250);},3000);
            $('#invite_linkedin_modal').dialog('close');
        },
        error: function(data){
            $('#msg span').removeClass();
            $('#msg span').addClass('error');
            $('#msg span').html(data.status + ': ' + data.statusText);
            setTimeout(function(){$('#msg').fadeOut(250);},3000);
            $('#invite_linkedin_modal').dialog('close');
        }
    });
};

$(function(){
    var $wrapper = $('#wrapper');
    $wrapper.imagesLoaded(function(){
        $wrapper.masonry({
            itemSelector: '.pin',
            isFitWidth: true,
            columnWidth: 400,
            gutterWidth: 10
        });
    });

    $('.wtr').each(function(){
        $(this).watermark($(this).attr('wtr'));
    });

    $('.sub').hover(function(){$(this).find('ul').css('display', 'block');},
                    function(){$(this).find('ul').css('display', 'none');});

    $('.sub ul').hover(function(){$(this).css('display', 'block');},
                       function(){$(this).css('display', 'none');});

    $("#query").keyup(function(event){
        if(event.keyCode == 13){
            var term = $('#query').val();
            var arr = term.match(/\w+/g);
            var query = '';
            for(var i in arr){ query+= arr[i] + '+'; }
            if (query.length == 0) { return false; }
            query = query.slice(0,-1);
            window.location = '/search/articles/?q={0}'.replace('{0}',query);
        }
    });

    bind_pins();

    $('#wrapper').infinitescroll({
        navSelector  : "#pageNav",
        nextSelector : "#pageNav a",
        itemSelector : ".pin",
        loading: {
            msgText: '<em>Loading some more pins...</em>'
        }
    }, function(newElements){
        var $newElems = $(newElements).css({opacity: 0});
        $newElems.imagesLoaded(function(){
            $wrapper.masonry('appended', $newElems, true);
            $newElems.animate({opacity:1});
        });

        bind_pins();
    });

    $('#add_modal').dialog({
        modal: true,
        open: function(e, ui){$('.ui-widget-overlay').click(function(){$('.modal').dialog('close');});},
        autoOpen: false,
        draggable: false,
        resizable: false,
        closeText: '',
        position: 'top',
        show: 'fade',
        hide: 'fade',
        width: 900
    });
    $('#pin_modal').dialog({
        modal: true,
        open: function(e, ui){$('.ui-widget-overlay').click(function(){$('.modal').dialog('close');});},
        close: function(e, ui){$('body').css('overflow', 'auto')},
        autoOpen: false,
        draggable: false,
        closeText: '',
        position: 'top',
        show: 'fade',
        hide: 'fade',
        width:1100,
    });
    $('#repin_modal').dialog({
        modal: true,
        open: function(e, ui){$('.ui-widget-overlay').click(function(){$('.modal').dialog('close');});},
        autoOpen: false,
        draggable: false,
        resizable: false,
        closeText: '',
        position: 'top',
        show: 'fade',
        hide: 'fade',
        width:400
    });
    $('#invite_linkedin_modal').dialog({
        modal: true,
        open: function(e, ui){$('.ui-widget-overlay').click(function(){$('.modal').dialog('close');});},
        autoOpen: false,
        draggable: false,
        resizable: false,
        closeText: '',
        position: 'top',
        show: 'fade',
        hide: 'fade',
        width:400
    });
    $('#signin_modal').dialog({
        modal: true,
        open: function(e, ui){$('.ui-widget-overlay').click(function(){$('.modal').dialog('close');});},
        autoOpen: false,
        draggable: false,
        resizable: false,
        closeText: '',
        position: 'top',
        show: 'fade',
        hide: 'fade',
        width:400
    });

    $('.modal .close').click(function(){
        $(this).parents('.modal').dialog('close');
    });

    $('#add_article_pick').click(function(){
        $('#add_buttons li').first().addClass('selected');
        $('#add_buttons li').last().removeClass('selected');

        $('#add_board_wrapper').fadeOut('fast', function(){
            $('#add_article_wrapper').fadeIn();
        });
    });

    $('#add_board_pick').click(function(){
        $('#add_buttons li').first().removeClass('selected');
        $('#add_buttons li').last().addClass('selected');

        $('#add_article_wrapper').fadeOut('fast', function(){
            $('#add_board_wrapper').fadeIn();
        });
    });

    $('.follow').click(function(){
        return toggle_follow($(this));
    });
    $('.invite_linkedin').click(function(){
        $('#to_name').text($(this).attr('full_name'));
        $('#invite_linkedin_modal input').val($(this).attr('username'))
        $('#invite_linkedin_modal').dialog('open');
    });
    $('#send_linkedin_button').click(function(){
        return send_linkedin_invite($('#invite_linkedin_form'));
    });
});
