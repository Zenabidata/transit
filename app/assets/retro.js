function unixtohms(unix) {
  var date = new Date((unix + 30) * 1000);
  var hours = "0" + date.getHours();
  var minutes = "0" + date.getMinutes();
  var formattedTime = hours.substr(-2) + ':' + minutes.substr(-2);
  return formattedTime
}

var items = [{
    'line': 'A',
    'name': 'Rockaway',
    'mta_time': 1547719953,
    'z_time': 1547720103,
    'true_time': 1547720163
  },
  {
    'line': 'A',
    'name': 'Inwood',
    'mta_time': 1547719953,
    'z_time': 1547720103,
    'true_time': 1547720163
  }
];

var rows = "";
$.each(items, function() {
  rows += "<tr><td>" + this.line + "</td><td>" + this.name + "</td><td>" + unixtohms(this.mta_time) + "</td><td>" + unixtohms(this.z_time) + "</td><td>" + unixtohms(this.true_time) + "</td></tr>";
});

$(rows).appendTo("#itemList tbody");