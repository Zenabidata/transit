$(document).ready(function(){
    update()
    
    setInterval( update, 15000 );
})

function request(){
    return new Promise((resolve, reject)=>{
        $.get({
            url: "http://localhost:9876/",
            datatype: 'jsonp',
            success: function(d){
                console.log(d)
                resolve(d)
            },
            failure: function(){
                reject("Error!")
            }


        })  
    })
}

function update(){
    console.log("Updating!")
    request().then(d=>{
        $('#content').html("")
        if(typeof d != "string"){
        streetName = Object.keys(d)[0]

        sections = d[streetName]

        for(i in sections){
            sectionName = Object.keys(sections[i])[0]
            addSection(sectionName)

            for(j in sections[i][sectionName]){
                stop = sections[i][sectionName][j]
                addStop(stop)
            }

        }
        changeStreetName(streetName)
    }
    else{
        changeStreetName("Error! Could not connect to servers!")
    }
    })
    
}


function changeStreetName(name){
    $('#street-name').text(name)
}
function addSection(sectionName){
    $("#content").append(`<div class='item item-divider'><span>${sectionName}</span></div>`)
}
function addStop(stopInfo){
    line=stopInfo.line
    name = stopInfo.name
    time = unixtomins(stopInfo.time)    

    $("#content").append(`<ion-item class="item row" ng-repeat="item in subwayTime.direction1.times" style=""><div ng-if="item.route == 'FS' || item.route == 'H'" class="col-10 padding"><img ng-src="img/S_sm.png"/></div><div ng-if="item.route != &#39;SI&#39; &amp;&amp;  item.route != &#39;FS&#39; &amp;&amp;  item.route != &#39;H&#39;" class="col-10 padding"><img ng-src="img/C_sm.png" alt="" src="./assets/imgs/${line}_sm.png"></div><div class="col padding item-note">${name}</div><div class="col-20 note padding"><div ng-if="item.minutes  != &#39;Delayed&#39;">${time} mins</div></div></ion-item>`)
} 
function unixtomins(unix){
    var diff = unix - Math.round(new Date().getTime() / 1000)
    return Math.floor(diff/60)
}
