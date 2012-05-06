$(function(){
    var $people = $('#people');
    $people.imagesLoaded(function(){
        $people.masonry({
            itemSelector: '.person',
            isFitWidth: true,
            columnWidth: 170,
            gutterWidth: 15
        });
    });
});