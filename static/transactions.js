/* FireBug console.log wrapper */
function log() {
  if (typeof(console) != 'undefined' && typeof(console.log) == 'function') {
    Array.prototype.unshift.call(arguments, '[transactions]');
    console.log(Array.prototype.join.call(arguments, ' '));
  }
}
jQuery.noConflict();
jQuery(document).ready(function($) {
  var CHART_TYPE_MAP = {'0':'income', '1':'expense', '2':'bill', '3':'saving'};
  var all_category_list = {};
  var all_category_hash = {'expense':{}, 'bill':{}, 'saving':{}};
  $("div#new_transaction_date").datepicker({
      dateFormat:'yy-mm-dd',
  });
  $("div#period-start").datepicker({
      dateFormat:'yy-mm-dd',
      defaultDate:'-1m',
  });
  $("div#period-end").datepicker({
      dateFormat:'yy-mm-dd',
  });
  function get_all_category_list() {
    $.getJSON("/"+db_name+"/all-category-list-active", function(data){
      all_category_list = data;
      for (chart_type in all_category_list) {
        var c = all_category_list[chart_type];
        for (i=0; i<c.length; i++) {
          all_category_hash[chart_type][c[i].id] = c[i];
        }
      }
    });
  }
  get_all_category_list();

  function add_blank_transaction_item() {
    $.getJSON("/"+db_name+"/expense-list-active", function(data){
      hash = {category:data};
      html = ich.transaction_item(hash);
      html.find("input[name='item_amount']").numeric({format:"0.00", precision : { num: 2,onblur:false} });
      $('#transaction_items').append(html);
    });
  };


  $.getJSON("/"+db_name+"/user", function(data){
      html = ich.user_details(data);
      $('div#user_details').append(html);
  });
  $.getJSON("/"+db_name+"/account-list-active", function(data){
    hash = {accounts:data}
    html = ich.account_select_list(hash);
    $('#account_select_list').append(html);
  });
  function split_transactions(data, target){
    var target_width = target.innerWidth()-25;
    var column_width = 212;
    var number_of_columns = Math.floor(target_width / column_width);
    var margin = Math.floor((target_width % column_width) / number_of_columns);

    hash = {'column':[], 'margin':margin};

    rem = data.length % number_of_columns;
    items_per_column = Math.floor(data.length/number_of_columns);
    for (i=0; i<number_of_columns; i++) {
      hash['column'].push({'transaction':[]});
      for (j=0; j<items_per_column; j++) {
        hash['column'][i]['transaction'].push(data.shift());
      }
      if (rem > 0) {
        hash['column'][i]['transaction'].push(data.shift());
        rem--;
      }
    }
    return hash;
  }
  function load_transaction_list(status_set) { // cleared_suspect || receipt_no_receipt_scheduled
    $.getJSON("/"+db_name+"/financial-transaction-list/"+status_set, function(data){
      var transactions_div = $('#'+status_set+'_transactions');
      hash = split_transactions(data, transactions_div);
      html = ich.transaction_listing(hash);
      transactions_div.html(html);
      transactions_div.find("div.column").css({'margin-left':hash['margin']+"px"});
    });
  }
  load_transaction_list('cleared_suspect');
  load_transaction_list('receipt_no_receipt_scheduled');

  function group_items(data, group_by) {
    var item_group = [];
    var groups = {};
    while (data.length > 0) {
      item = data.shift();
      if (group_by == 'financial_transaction') {
        group_id = item.transaction_name;
      } else if (group_by == 'category') {
        category_id = item.category;
        type_name = CHART_TYPE_MAP[item.type];
        group_id = all_category_hash[type_name][category_id].name;
      } else if (group_by == 'date') {
        group_id = item['date'];
      }

      if (!(group_id in groups)) {
        groups[group_id] = {'item':[], 'name':group_id, 'group_by':group_by}
      }
      groups[group_id]['item'].push(item);
    }
    var group_keys = [];
    for (var g in groups) {
      group_keys.push(g);
    }
    group_keys.sort();
    while (group_keys.length > 0) {
      item_group.push(groups[group_keys.shift()]);
    }
    
    var target_width = $("#item_group_list").innerWidth()-25;
    var column_width = 212;
    var number_of_columns = Math.floor(target_width / column_width);
    var margin = Math.floor((target_width % column_width) / number_of_columns);
    hash = {'column':[], 'margin':margin};
    rem = item_group.length % number_of_columns;
    groups_per_column = Math.floor(item_group.length/number_of_columns);
    for (i=0; i<number_of_columns; i++) {
      hash['column'].push({'group':[]});
      for (j=0; j<groups_per_column; j++) {
        hash['column'][i]['group'].push(item_group.shift());
      }
      if (rem > 0) {
        hash['column'][i]['group'].push(item_group.shift());
        rem--;
      }
    }
    return hash;
  }
  function formatISO(d) {
    return(d.getFullYear()+"-"+(d.getMonth()+1)+"-"+d.getDate());
  }

  function load_item_group_list() {
    var start = formatISO($("div#period-start").datepicker('getDate'));
    var end = formatISO($("div#period-end").datepicker('getDate'));
    $.getJSON("/"+db_name+"/period/"+start+"."+end+"/transaction-item-list", function(data){
        group_by = $("input[name='group_by']:checked").val();
        hash = group_items(data, group_by);
        html = ich.item_group_list(hash);
        $("#item_group_list").html(html);
        $("#item_group_list").find("div.column").css({'margin-left':hash['margin']+"px"});
    });

  }

  load_item_group_list();
  add_blank_transaction_item();

  $("#transaction_items").delegate(".chart_type_select_list", "change", function(){
    var select_list = $(this);
    var chart_selected = select_list.find("option:selected").val();
    select_list.siblings('select.category_select_list').empty();
    if (chart_selected != 'income') {
      $.getJSON("/"+db_name+"/"+chart_selected+"-list-active", function(data){
        hash = {category:data};
        html = ich.category_list(hash);
        select_list.siblings('select.category_select_list').append(html);
      });
    }
  });

  $("#new_transaction").delegate("button.add_item", "click", add_blank_transaction_item);
  $("#transaction_items").delegate("button.remove_item", "click", function(){
      $(this).parents("div.transaction_item").remove();
  });

  var update_remainder = function(){
    var transaction_items = $("#transaction_items").find(".transaction_item");
    var amount = new Number(0);
    transaction_items.each(function(){
      amount += new Number($(this).find("input[name='item_amount']").val());
    });
    var r = new Number($("#transaction_amount").val()) - amount;
    $("#transaction_amount_remainder").html(parseFloat(r.toFixed(2)));
  };

  $("#transaction_items").delegate("input[name='item_amount']", "change", update_remainder);
  $("#transaction_amount").numeric({format:"0.00", precision : { num: 2,onblur:false} });
  $("#transaction_amount").bind("change", function(){
      var transaction_items = $("#transaction_items .transaction_item");
      if (transaction_items.get().length == 1) {
        transaction_items.find("input[name='item_amount']").val($(this).val());
        $("#transaction_amount_remainder").html("");
      } else {
        update_remainder();
      }
  });

  $("button#period-button").bind("click", function(){
      load_item_group_list();
  });


  $("#add_transaction").bind("click", function(){
      items = [];
      $("#transaction_items .transaction_item").each(function(){
        item = $(this);
        items.push({'name':item.find("input[name='transaction_item_name']").val(),
          'amount':item.find("input[name='item_amount']").val(),
          'type':item.find(".chart_type_select_list option:selected").val(),
          'category':item.find(".category_select_list option:selected").val()});
      });
      
      t_date = $("#new_transaction_date").datepicker("getDate");
      data_string = {'status':$("select#transaction_status option:selected").val(),
        'name':$("input[name='transaction_name']").val(),
        'date':formatISO(t_date),
        'account':$("#account_select_list option:selected").val(),
        'items':items};


      d = {'data_string':JSON.stringify(data_string)};
      $.post("/"+db_name+"/financial-transaction-item", d, function(data){
        return_data = JSON.parse(data);
        if (return_data['status'] == 0 || return_data['status'] == 4) {
          load_transaction_list('cleared_suspect');
        } else {
          load_transaction_list('receipt_no_receipt_scheduled');
        }
        load_item_group_list();
        get_all_category_list();
      });
  });

  $("input[name='group_by']").bind("change", function(){
      if ($(this).attr('checked')) {
        var g = $(this).val();
        load_item_group_list();
      }
  });



});

