$(function(){

  // item amount slider 
  $("div.amount_slider").slider({step:0.01});
  $("div.amount_slider").slider('disable');
  $("strong.total_items_amount input.input_item").keyup(function(){
    var total_items_listing = $(this).parents("div.transaction_total").siblings("div.total_items_listing");
    var input_val = new Number($(this).val());
    total_items_listing.find("div.amount_slider").slider('option', 'max', input_val);
    total_items_listing.find("div.item_amount input").val(parseFloat(input_val).toFixed(2));
    total_items_listing.find("div.amount_slider").slider('option', 'value', input_val);

  });

  $("span.total_items_add").click(function(e){
    var total_items_listing = $(this).parents("div.transaction_total").siblings("div.total_items_listing");
    total_items_listing.find("div.item:first").clone().prependTo(total_items_listing);
    total_items_listing.find("div.item:first").each(function(i){
      $(this).find("span.total_items_remove").remove(); // will add it later
      $(this).find("div.amount_slider").slider({step:0.01});
      $(this).find("div.item_amount input.input_item").val('0.00');
      $(this).find("div.item_name input.input_item").val('');
    });
    total_items_changed(total_items_listing);
  });
  $("div.transaction_total em.total_items_remainder").bind('click', function(e) {
    var total_items_listing = $(this).parents("div.transaction_total").siblings("div.total_items_listing");
    var first_slider = total_items_listing.find("div.item div.item_amount_slider:first div.amount_slider");
    var remainder_value = new Number($(this).html());
    var first_slider_value =  new Number(first_slider.slider('option', 'value'));
    if ((remainder_value + first_slider_value) >= 0) {
      first_slider.slider('option', 'value', remainder_value + first_slider_value);
      update_input_from_slider_change(first_slider);
    }
    update_remainder(total_items_listing);
  });

  function sum_of_items(total_items_listing) {
    var items_total = 0.00;
    total_items_listing.find("div.item").each(function(i){
        var item_val = new Number($(this).find("div.item_amount input.input_item").val());
        items_total += item_val;
    });
    return items_total.toFixed(2);
  }
  function update_input_from_slider_change(this_slider) {
    var slider_input = this_slider.parents("div.item").find("div.item_amount input.input_item");
    var slider_value = new Number(parseFloat(this_slider.slider('option', 'value')).toFixed(2));
    //var slider_input_value = new Number(parseFloat(slider_input.val()).toFixed(2));
    //if (slider_value != slider_input_value) {
      //alert("update_input_from_slider_change: ("+slider_value+") != ("+slider_input_value+")");
    //}
    slider_input.val(slider_value);
  }

  function total_items_changed(total_items_listing) {
    var count_of_items = total_items_listing.find("div.item").length;
    var items_total = new Number(sum_of_items(total_items_listing));
    var transaction_total_input = total_items_listing.siblings("div.transaction_total").find("input.input_item");
    var transaction_total = new Number(transaction_total_input.val());
    //alert(count_of_items);
    update_remainder(total_items_listing);
    if (count_of_items >= 2) {
      transaction_total_input.attr("disabled", 'disabled');
      total_items_listing.find("div.item_amount input.input_item").each(function(i){
        $(this).removeAttr("disabled");
        $(this).keyup(item_amount_input_changed);
      });
      total_items_listing.find("div.amount_slider").each(function(i){
        $(this).slider('enable');
        $(this).slider('option', 'max', transaction_total_input.val());
        $(this).unbind('slidechange');
      });
      total_items_listing.find("div.item").each(function(i){
         if (!$(this).find("span.total_items_remove").html()) {
            $(this).prepend("<span class='total_items_remove button'><strong>-</strong></span>");
            $(this).find("span.total_items_remove").bind('click', function(e){
              var total_items_listing = $(this).parents("div.total_items_listing");
              var i = total_items_listing.find("div.item").index($(this).parents("div.item"));
              $(total_items_listing.find("div.item").get(i)).empty().replaceWith("");
              var count_of_items = total_items_listing.find("div.item").length;
              total_items_changed(total_items_listing);
              $(this).parents("div.item").empty().replaceWith("");
            });
         }
      });
    }

    if (count_of_items == 1) {
      transaction_total_input.removeAttr("disabled");
      total_items_listing.find("span.total_items_remove").remove();
      total_items_listing.find("div.amount_slider").slider('option', 'value', transaction_total_input.val());
      total_items_listing.find("div.amount_slider").slider('disable');
      total_items_listing.find("div.item_amount input.input_item").attr("disabled", 'disabled');
      total_items_listing.siblings("div.transaction_total").find("em.total_items_remainder").html("0.00");
    }
    else if (false && count_of_items == 2) { // off for now...
      //alert(parseFloat(items_total)+" == "+parseFloat(transaction_total_input.val()));
      if (items_total != transaction_total) {
         // add remainder to first slider
        total_items_listing.siblings("div.transaction_total").find("em.total_items_remainder").trigger("click");
      }
        // each slider adjusts value of the other.
        var first_slider = total_items_listing.find("div.item div.item_amount_slider:first div.amount_slider");
        var last_slider = total_items_listing.find("div.item div.item_amount_slider:last div.amount_slider");
        first_slider.bind('slidechange', function(event, ui){
            var difference = transaction_total - first_slider.slider('option', 'value');
            if (difference != last_slider.slider('option', 'value')) {
              last_slider.slider('option', 'value', difference);
            }
            update_input_from_slider_change($(this));
        });
        last_slider.bind('slidechange', function(event, ui){
            var difference = transaction_total - last_slider.slider('option', 'value');
            if (difference != first_slider.slider('option', 'value')) {
              first_slider.slider('option', 'value', difference);
            }
            update_input_from_slider_change($(this));
        });
    }
    else if (count_of_items >= 2) {
      total_items_listing.find("div.amount_slider").bind('slidechange', function(event, ui){
          update_input_from_slider_change($(this));
          update_remainder(total_items_listing);
      });

    }
  }
  function update_remainder(total_items_listing) {
    var total_items_remainder = total_items_listing.siblings("div.transaction_total").find("em.total_items_remainder");
    //alert(total_items_remainder.html());
    total_items_remainder.show();
    //var remainder_input = total_items_remainder.find("input.input_item");
    var items_total = new Number(sum_of_items(total_items_listing));
    var transaction_total_input = total_items_listing.siblings("div.transaction_total").find("input.input_item");
    var remainder = transaction_total_input.val()-items_total;
    total_items_remainder.html(parseFloat(remainder.toFixed(2)));
    if (remainder == 0) {
      total_items_remainder.hide();
    }
    return total_items_remainder.html();
  }
  var item_amount_input_changed = function(){
    var slider = $(this).parents("div.item_amount").siblings("div.item_amount_slider").find("div.amount_slider");
    var total_items_listing = $(this).parents("div.total_items_listing");
    var slider_value = new Number(parseFloat(slider.slider('option', 'value')).toFixed(2));
    var this_value = new Number(parseFloat($(this).val()).toFixed(2));
    if (slider_value != this_value) {
      //alert(slider_value+" != "+this_value);
      slider.slider('option', 'value', this_value);
      update_remainder(total_items_listing);
    }
  };
  $("div.item_amount input.input_item").keyup(item_amount_input_changed);
  $("div.add_transaction-box div.transaction_status a").bind('click', function(e) {
      $(this).siblings().removeClass("current");
      $(this).addClass("current");
      e.preventDefault();
  });
  function edit_transaction_status_callback(cb_data) {
    var tr_link = $("div#tr_st_"+cb_data['id']+" a[value='"+cb_data['transaction_status']+"']");
    tr_link.siblings().removeClass("current");
    tr_link.addClass("current");
  }
  $("div.transaction-box div.transaction_status a").bind('click', function(e) {
    var t_box = $(this).parents("div.transaction-box");
    my_data = {'transaction_status':$(this).attr("value")};
    t_box.find("input[type='hidden']").each(function(){
      var key = $(this).attr("name");
      var value = $(this).attr("value");
      my_data[key] = value;
    });
    my_data['javascript_on'] = true;
    $.get($(this).attr("href"), my_data, edit_transaction_status_callback, "json");
    e.preventDefault();

  });

  $("div.sort_by span.button a, div.group_by span.button a").bind('click', function(e){
    $.get($(this).attr('href'), "", function() {window.location = window.location; });
    e.preventDefault();
  });
  
  function get_form_values(my_form) {
    // returns a dict with form values
    var d = {};
    my_form.find("input[name='name'], input[name='day'], input[type='hidden']").each(function(){
      var key = $(this).attr("name");
      var value = $(this).attr("value");
      d[key] = value;
    });
    d['status'] = my_form.find("div.transaction_status a.current").attr("value");
    if (!d['status']) {
      alert('no status specified. using "receipt"');
      d['status'] = 'receipt'
    }
    d['javascript_on'] = true;
    var items = [];

    my_form.find(".item").each( function() {
      var item = {};
      $(this).find(".input_item").each( function() {
        var key = $(this).attr("name");
        var value = $(this).attr("value");
        item[key] = value;
      });
      items.push(item);
    });
        
      
    d['items'] = JSON.stringify(items);
    return d;
  }

  function verify_form_values(my_form) {
    $(".error").each(function(){
      $(this).removeClass("error");
    });
    var pass = true;
    my_form.find(".string").each(function(){
      var grep = /.+/;
      if (!grep.test($(this).attr("value"))) {
        $(this).addClass("error");
        pass = false;
      }
    });
    my_form.find(".integer").each(function(){
      var grep = /[0-9]+/;
      if (!grep.test($(this).attr("value"))) {
        $(this).addClass("error");
        pass = false;
      }
    });
    if (pass) {
      return true;
    }
    alert("errors found...");
    return false;
  }



  $("#add_transaction_form span.total_items_action").bind('click', function(event){
    var this_form = $(this).parents("#add_transaction_form");

    if (this_form.verify_form()) {
      my_data = get_form_values(this_form);
      my_method = new String(this_form.attr("method"));
      my_url = new String(this_form.attr("action"));
      //$.post(my_url, my_data, function() {window.location = window.location; });
      $.get(my_url, my_data, function() {window.location = window.location; });
    } else {
      alert("failed to verify.");
    }
    event.preventDefault();
    //window.location.reload();
  });
  $("form#add_transaction_form span.transaction_update").bind('click', function(event) {
    var this_form = $(this).parents("#add_transaction_form");

    if (this_form.verify_form()) {
      my_data = get_form_values(this_form);
      my_url = new String(this_form.attr("update"));
      $.get(my_url, my_data, function() {window.location = window.location; });
    } else {
      alert("failed to verify.");
    }
    event.preventDefault();
  });
  $("form#add_transaction_form span.transaction_delete").bind('click', function(event) {
    var this_form = $(this).parents("#add_transaction_form");

    if (this_form.verify_form()) {
      my_data = get_form_values(this_form);
      my_data['delete'] = 'true';
      my_url = new String(this_form.attr("update"));
      $.get(my_url, my_data, function() {window.location = window.location; });
    } else {
      alert("failed to verify.");
    }
    event.preventDefault();
  });

  // TODO make these 'live'
  // minimize category selection based on chart
  $(".select_type_id").change(function() {
    var type_selected = $(this).find("option:selected").attr("value");
    $(this).parents("div.item").find(".select_category optgroup").hide();
    $(this).parents("div.item").find(".select_category .optgroup_category-"+type_selected).show();
    $(this).parents("div.item").find(".select_category .optgroup_category-"+type_selected+" option").attr('selected', 'selected');
  });
  // auto select chart based on category selection
  $(".select_category").change(function() {
    var chart_selected = $(this).parents("div.item").find(".select_category option:selected").parent().attr("type_id");
    $(this).parents("div.item").find(".select_type_id option[value="+chart_selected+"]").attr('selected', 'selected');
  });
  // auto set first item name as same as transaction name
  $("form.transaction_form input[name=name]").blur(function() {
    var this_name = $(this).attr("value");
    var title = $(this).parents("form").find("input[name=title]:first").attr("value");
    if (title == "") {
      $(this).parents("form").find("input[name=title]:first").attr("value", this_name);
    }
  });

  // handle edit clicks
  $("div.transaction-box div.t_sum").bind('click', function(e) {
    var transaction = {};
    $(this).parents("div.transaction-box").find("input[type=hidden], div.transaction_status a.current[name=transaction_status], div[name=name], div[name=date], div[name=sum]").each( function() {
      var key = $(this).attr("name");
      var value = $(this).attr("value");
      transaction[key] = value;
    });
    var items = [];
    $(this).parents("div.transaction-box").find("div.t_items div.item-row").each(function() {
      var item = {};
      $(this).find("span[name=sum], span[name=title], span[name=cat_name], span[name=title]").each(function() {
        var key = $(this).attr("name");
        var value = $(this).attr("value");
        item[key] = value;
      });
      items.push(item);
    });
    transaction['items'] = items;
    $("form#add_transaction_form").find("input[type=hidden], input[name=name]").each(function() {
      $(this).attr("value", transaction[$(this).attr("name")]);
    });
    $("form#add_transaction_form input[name=total_amount]").attr("value", Math.abs(transaction['sum'])).keyup();
    var tr_link = $("form#add_transaction_form div.transaction_status a[value='"+transaction['transaction_status']+"']");
    tr_link.siblings().removeClass("current");
    tr_link.addClass("current");
    $("form#add_transaction_form input[name=day]").attr("value", transaction['date'].substring(transaction['date'].length-2));

    function fill_in_item(item) {
      var item_row = $("div.total_items_listing div.item:first-child");
      item_row.find("input[name=title]").attr("value", item['title']);
      item_row.find("select.select_category option").removeAttr("selected");
      item_row.find("select.select_category option[name='"+item['cat_name']+"']").attr("selected", "selected");
      item_row.find("select.select_category").change();
      //item_row.find("div.amount_slider").slider('option', 'value', Math.abs(item['sum']));
      item_row.find("div.item_amount input.input_item").attr("value", Math.abs(item['sum'])).keyup();
    }
    fill_in_item(transaction['items'][transaction['items'].length-1]);
    for ( i=transaction['items'].length-2; i > -1; i-- ) {
      $("span.total_items_add").click(); // create a new row
      var item = transaction['items'][i];
      fill_in_item(item);
    }
    $("form#add_transaction_form span.transaction_update").show();
    

  });


});
