function prepareDataForSave(name,data) {
    var obj = new Object();
    obj.Name = name;
    obj.Data = data;
    return obj;
}

function prepareMultiPartPOST(data) {
    // var boundary = 'sPlItME' + Math.floor(Math.random()*10000);
    var boundary = '' + Math.floor(Math.random()*10000);
    var reqdata = '--' + boundary + '\r\n';
    //console.log(data.length);
    for (var i=0;i < data.length;i++)
	{
	    reqdata += 'content-disposition: form-data; name="' + data[i].Name + '"';
	    reqdata += "\r\n\r\n" ;
	    reqdata +=  data[i].Data;
	    reqdata += "\r\n" ;
	    reqdata += '--' + boundary + '\r\n';
	}
    return new Array(reqdata,boundary);
}

function on_error() {
    jQuery("input[name='saved_on']").attr('style','background-color:red');
    jQuery("input[name='saved_on']").val('communication error');
}

function doClickSave() {
    try {
	var data = eamy.instances[0].getText();
    } catch(e) {
	var data = area.textarea.value;
    }
    var dataForPost = prepareMultiPartPOST(new Array(
	prepareDataForSave('data', data),
	prepareDataForSave('file_hash', jQuery("input[name='file_hash']").val()),
	prepareDataForSave('saved_on', jQuery("input[name='saved_on']").val()),
	prepareDataForSave('from_ajax','true')));
    // console.info(area.textarea.value);
        jQuery("input[name='saved_on']").attr('style','background-color:yellow');
	jQuery("input[name='saved_on']").val('saving now...')
	jQuery.ajax({
	  type: "POST",
	  contentType: 'multipart/form-data;boundary="' + dataForPost[1] + '"',
	  url: self.location.href,
	  dataType: "json",
	  data: dataForPost[0],
	  timeout: 5000,
	  success: function(json){
		    try {
                        if (json.error) {
			    window.location.href=json.redirect;
			} else {
			    // console.info( json.file_hash );
			    jQuery("input[name='file_hash']").val(json.file_hash);
			    jQuery("input[name='saved_on']").val(json.saved_on);
			    jQuery("input[name='saved_on']").attr('style','background-color:#99FF99');
			    // console.info(jQuery("input[name='file_hash']").val());
			    var output = 'exposes ';
			    for ( var i in json.functions) {
				output += ' <a href="/' + json.application + '/' + json.controller + '/' + json.functions[i] + '">' + json.functions[i] + '</a>,'; 
			    }
			    if(output!='exposes ') {
				jQuery("#exposed").html( output.substring(0, output.length-1));
			    }
			}
                    } catch(e) {
			on_error();
		    }
		},
	  error: function(json) { on_error(); } 
	});
	return false;
}

function keepalive(url) {
	jQuery.ajax({
	  type: "GET",
	  url: url,
	  timeout: 1000,
	  success: function(){},
	  error: function(x) { on_error(); } });
}
