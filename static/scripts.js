// markers for map
var markers = [];

// map
var map;

// type the user searched for (for map updating purposes)
var searchType;

// info window
var info;

/**
 * Breaks long lines into shorter lines
 **/
function newLine(text) {
    
    // final string to be returned
    var final = '';
    
    // iterates through string
    while (text.length > 0) {
        // creates new line every 200 characters
        final += text.substring(0, 200) + '\n';
        text = text.substring(200);
    }
    
    // returns new string
    return final;
}

/**
 * Initializes Google map
 **/
function initMap() {
    
    // infowindow for markers
    info = new google.maps.InfoWindow();
    
    // map settings
    var mapOptions = {
        center: {lat: 42.374368, lng: -71.116270}, // Harvard Yard
        zoom: 18,
        mapTypeId: 'roadmap'
    };
    
    // map
    map = new google.maps.Map(document.getElementById('map'), mapOptions);

    // Try HTML5 geolocation.
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            var pos = {
                lat: position.coords.latitude,
                lng: position.coords.longitude
            };
            
            // passes user's longitude and latitude
            document.getElementById("poslat").value = pos.lat;
            document.getElementById("poslng").value = pos.lng;
      
            // user's range of error
            var userRange = new google.maps.Circle({
                strokeColor: '#FF0000',
                strokeOpacity: 0.8,
                strokeWeight: 1,
                fillColor: '#FF0000',
                fillOpacity: 0.35,
                map: map,
                center: pos,
                radius: 10
            });
            
            // center's map on user location
            map.setCenter(pos);
      
        }, function() {
            handleLocationError(true, userRange, map.getCenter());
        });
    } else {
        // Browser doesn't support Geolocation
        handleLocationError(false, userRange, map.getCenter());
    }
  
    // configure UI once Google Map is idle (i.e., loaded)
    google.maps.event.addListenerOnce(map, "idle", configure);
}

function handleLocationError(browserHasGeolocation, infoWindow, pos) {
    infoWindow.setPosition(pos);
    infoWindow.setContent(browserHasGeolocation ?
                        'Error: Could not find your location.' :
                        'Error: Your browser doesn\'t support geolocation.');
}

/**
 * Capitalizes first letter of string
 **/ 
function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

/**
 * Vote on markers
 **/
function vote(id, voteType){
    
    // set parameters for getJSON
    var parameters = {
        id: id,
        vote: voteType
    };
    
    // updates vote info, receives new votes
    $.getJSON(Flask.url_for("vote"), parameters)
    .done(function(data, textStatus, jqXHR) {
        // updates the number of votes displayed to the user
        var elem = document.getElementById(data[0].id);
        elem.value = "Upvote " + data[0].checks;
    })
    .fail(function(jqXHR, textStatus, errorThrown) {
        // log error to browser's console
        console.log(errorThrown.toString());
    });
}

/**
 * Adds marker for place to map.
 **/
function addMarker(place)
{
    // gets coordinates of place
    var loc = {lat: place.olat, lng: place.olng};
    // marker id
    var id = place.id;
    // marker type
    var type = place.type;
    
    // cool icon
    var icon = {
        labelOrigin: new google.maps.Point(0, 40),
        url: 'https://developers.google.com/maps/documentation/javascript/examples/full/images/beachflag.png'
    };
    
    // creates marker at loc    
    var marker = new google.maps.Marker({
        position: loc,
        map: map,
        icon: icon,
        markerId: id
    });
    
    // infowindow for marker type, description, and votes
    marker.addListener('click', function() {
        var contentString = "<h3>" + capitalizeFirstLetter(place.type) + "</h3>" + "<div id='info'><h5>Description: </h5>" +
        newLine(place.descr) + "</div>" + "<a href='/user?uid=" + place.uid +"'>View User</a><br/><br/>" + "<input id='" + id + "' type='button' class='btn btn-default' onclick='vote(" +
        id + ", \"upvote\")' value='Upvote  " + place.checks + "'/>" + " <input type='button' class='btn btn-default' onclick='vote(" +
        id + ", \"downvote\")' value='Downvote'/>";
        
        info.setContent(contentString);
        info.open(map, marker);
    });
    
    // adds marker to markers
    markers.push(marker);
}

/**
 * Configures application.
 */
function configure()
{
    // update UI after map has been dragged
    google.maps.event.addListener(map, "dragend", function() {
        // if info window isn't open
        // http://stackoverflow.com/a/12410385
        if (!info.getMap || !info.getMap())
        {
            search(searchType);
        }
    });

    // update UI after zoom level changes
    google.maps.event.addListener(map, "zoom_changed", function() {
        search(searchType);
    });
    
    search(searchType);

    // re-enable ctrl- and right-clicking (and thus Inspect Element) on Google Map
    // https://chrome.google.com/webstore/detail/allow-right-click/hompjdfbfmmmgflfjdlnkohcplmboaeo?hl=en
    document.addEventListener("contextmenu", function(event) {
        event.returnValue = true; 
        event.stopPropagation && event.stopPropagation(); 
        event.cancelBubble && event.cancelBubble();
    }, true);

    // update UI
    search(searchType);

    // give focus to text box
    $("#q").focus();
}

/**
 * Removes markers from map.
 */
function removeMarkers()
{
    // iterates through markers, setting elements to null
    for (var i = 0; i < markers.length; i++) {
        markers[i].setMap(null);
    }
    
    // sets length of markers to 0
    markers.length = 0;
}

/**
 * Searches for markers of type
 **/
function search(type)
{
    // type of marker to search for
    searchType = type;
    if (typeof(type) != "undefined")
    {
        // get map's bounds
        var bounds = map.getBounds();
        var ne = bounds.getNorthEast();
        var sw = bounds.getSouthWest();
        
        var parameters = {
            q: type,
            ne: ne.lat() + "," + ne.lng(),
            sw: sw.lat() + "," + sw.lng()
        };

        // gets JSON array of markers of type in view
        $.getJSON(Flask.url_for("search"), parameters)
        .done(function(data, textStatus, jqXHR) {
            // remove old markers from map
            removeMarkers();
            
            // add new markers to map
            for (var i = 0; i < data.length; i++)
            {
                addMarker(data[i]);
            }
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
            // log error to browser's console
            console.log(errorThrown.toString());
        });
    }
}