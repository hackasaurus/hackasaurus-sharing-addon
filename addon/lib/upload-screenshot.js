const { Cc, Ci, Cu, Cr } = require("chrome");

exports.upload = function(options) {
  var f = Cc["@mozilla.org/files/formdata;1"]
          .createInstance(Ci.nsIDOMFormData);

  options.data.forEach(function(tuple) {
    f.append(tuple[0], tuple[1]);
  });

  var xhr = Cc["@mozilla.org/xmlextras/xmlhttprequest;1"]
            .createInstance(Ci.nsIXMLHttpRequest);

  xhr.open("POST", options.url);
  xhr.send(f);
  xhr.onload = function() {
    try {
      if (xhr.status == 200)
        options.callback(null, JSON.parse(xhr.responseText));
      else
        options.callback(xhr.status, xhr.responseText);
    } catch (e) {
      console.exception(e);
    }
  };
  xhr.onerror = function() {
    try {
      options.callback("ERROR", xhr.responseText);
    } catch(e) {
      console.exception(e);
    }
  };
};
