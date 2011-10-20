(function(){

// room look-up-table
var room_lut = {};

var update_room = function(room) {
        var name = room['name'];
        var rooms_seen = {};
        // create an entry for the room if it did not yet exist
        if (!room_lut[name]) {
                var el = $("<div class='meter'>"+
                                "<span class='bar'></span>"+
                                "<div class='txt1'><span class='free'></span>"+
                                                        " vrij</div>"+
                                "<div class='txt2'>"+name+"</div>"+
                                "<div class='txt4'></div>"+
                                "<div class='txt3'><span class='total'></span>"+
                                                        " totaal</div>"+
                           '</div>');
                el.find('.bar').width(0);
                room_lut[name] = el;
                $('#list').append(el);
        }
        // update entry
        var prc = room['capacity'] == 0 ? 0 :  Math.floor(
                                room['free'] * 100 / room['capacity']);
        room_lut[name].find('.free').text(room['free']);
        room_lut[name].find('.total').text(room['capacity']);
        room_lut[name].find('.bar').animate({'width': prc +'%'});
        if(room['reservation']) {
                if (room['reservation']['now']) {
                        room_lut[name].find('.txt4').text('gereserveerd tot '+
                                        room['reservation']['endtime']);
                } else {
                        room_lut[name].find('.txt4').text('gereserveerd vanaf '+
                                        room['reservation']['starttime']);
                }
        } else {
                room_lut[name].find('.txt4').text('');
        }
};

// fetches the data
var update = function() {
        $.getJSON('/api', function(data) {
                var rooms_seen = {};
                // update rooms
                for (var i = 0; i < data['rooms'].length; i++) {
                        update_room(data['rooms'][i]);
                        rooms_seen[data['rooms'][i]['name']] = true;
                }
                // remove stray rooms
                for (var room in room_lut) {
                        if (!rooms_seen[room]) {
                                room_lut[room].remove();
                                delete room_lut[room];
                        }
                }
                // set next timeout
                setTimeout(update, 5000);
        });        
};

// entrypoint
$(function(){
        update();
});

})();
