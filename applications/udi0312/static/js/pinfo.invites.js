var options = {
    valueNames: ['name'],
    page: 5000
};

var linkedin_list = new List('linkedin_list', options);

$('.invite_linkedin').click(function(){
    $('#to_name').text($(this).attr('full_name'));
    $('#invite_linkedin_modal input').val($(this).attr('username'))
    $('#invite_linkedin_modal').dialog('open');
});
$('#send_linkedin_button').click(function(){
    return send_linkedin_invite($('#invite_linkedin_form'));
});
