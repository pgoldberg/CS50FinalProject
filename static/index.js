// Checks to see if a user clicked on certain items on the website after DOM is fully loaded
document.addEventListener('DOMContentLoaded',function(){
    document.getElementById('bathroom').addEventListener('click',function(){
        // searches for bathrooms
        search("bathroom");
        
        // updates dropdown button's text
        var selection = document.getElementById("search-type");
        selection.innerHTML = "Bathroom<span class='caret'></span>";
    },false);
    
    document.getElementById('fountain').addEventListener('click',function(){
        // searches for water fountains
        search("fountain");
        
        // updates dropdown button's text
        var selection = document.getElementById("search-type");
        selection.innerHTML = "Water Fountain<span class='caret'></span>";
    },false);
    
    document.getElementById('bluelight').addEventListener('click',function(){
        // searches for blue lights
        search("bluelight");
        
        // updates dropdown button's text
        var selection = document.getElementById("search-type");
        selection.innerHTML = "Blue Light<span class='caret'></span>";
    },false);
    
    document.getElementById('submit-bathroom').addEventListener('click',function(){
        // sets type of object to submit
        var type = document.getElementById("submit-type");
        type.value = "bathroom";
        
        // updates dropdown button's text
        var selection = document.getElementById("marker-type");
        selection.innerHTML = "Bathroom<span class='caret'></span>";
    },false);
    
    document.getElementById('submit-fountain').addEventListener('click',function(){
        // sets type of object to submit
        var type = document.getElementById("submit-type");
        type.value = "fountain";
        
        // updates dropdown button's text
        var selection = document.getElementById("marker-type");
        selection.innerHTML = "Water Fountain<span class='caret'></span>";
    },false);
    
    document.getElementById('submit-bluelight').addEventListener('click',function(){
        // sets type of object to submit
        var type = document.getElementById("submit-type");
        type.value = "bluelight";
        
        // updates dropdown button's text
        var selection = document.getElementById("marker-type");
        selection.innerHTML = "Blue Light<span class='caret'></span>";
    },false);
},false);