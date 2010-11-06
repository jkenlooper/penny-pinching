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
  var chart_category_hash = {'chart':[]};
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
  function get_all_category_list(add_blank_item) {
    $.getJSON("/"+db_name+"/all-category-list-active", function(data){
      all_category_list = data;
      for (chart_type in all_category_list) {
        var c = all_category_list[chart_type];

        var chart_hash = {'chart_name':chart_type, 'category':c};
        chart_category_hash['chart'].push(chart_hash);

        for (i=0; i<c.length; i++) {
          all_category_hash[chart_type][c[i].id] = c[i];
        }
      }
      if (add_blank_item){ add_blank_transaction_item(); }
    });
  }
  get_all_category_list(true);

  function add_blank_transaction_item() {
    html = ich.transaction_item(chart_category_hash);
    html.find("input[name='item_amount']").numeric({format:"0.00", precision : { num: 2,onblur:false} });
    $('#transaction_items').append(html);
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
    var order_by = $("input[name='sort_by']:checked").val();
    $.getJSON("/"+db_name+"/financial-transaction-list/"+status_set+"?order_by="+order_by, function(data){
      var transactions_div = $('#'+status_set+'_transactions');
      var TRANSACTION_STATUS_ENUM = ['suspect', 'no_receipt', 'receipt', 'scheduled', 'cleared', 'reconciled'];
      var TRANSACTION_STATUS_SYMBOLS_ENUM = ['?', '&larr;', '&rarr;', '&crarr;', '&harr;', '&radic;'];
      for (i=0; i<data.length; i++) {
        var status_list = [];
        for (j=0; j<TRANSACTION_STATUS_ENUM.length-1; j++) { // except reconciled
          var status_active = "";
          if (data[i]['status'] == j) {
            status_active = 'active';
          }
          status_list.push({'status_name': TRANSACTION_STATUS_ENUM[j],
            'status_symbol': TRANSACTION_STATUS_SYMBOLS_ENUM[j],
            'status_active': status_active})
        }
        data[i]['status_list'] = status_list;
      }
      hash = split_transactions(data, transactions_div);
      html = ich.transaction_listing(hash);
      transactions_div.html(html);
      transactions_div.find("div.column").css({'margin-left':hash['margin']+"px"});
    });
  }
  load_transaction_list('cleared_suspect');
  load_transaction_list('receipt_no_receipt_scheduled');

  $("input[name='sort_by']").bind('change', function(e){
    load_transaction_list('cleared_suspect');
    load_transaction_list('receipt_no_receipt_scheduled');
  });

  function clear_new_transaction_form() {
    var new_transaction = $("#new_transaction");
    new_transaction.find("#delete_transaction, #update_transaction").remove();
    new_transaction.find("#transaction_status option:first-child").attr('selected', 'selected');
    new_transaction.find("#account_select_list option:first-child").attr('selected', 'selected');
    var today = new Date();
    new_transaction.find("#new_transaction_date").datepicker("setDate", today);
    new_transaction.find("#new_transaction_name").val("");
    new_transaction.find("#transaction_amount").val(0.00);
    new_transaction.find("#transaction_amount_remainder").html("");
    $("div#transaction_items div.transaction_item").remove();
    add_blank_transaction_item();
  }


  $("div.transaction_list").delegate("span.transaction-edit", "click", function(e) {
      clear_new_transaction_form();
      var transaction = $(this).parents("div.transaction");
      var id = transaction.attr("db_id");
      $.getJSON("/"+db_name+"/financial-transaction-item/"+id, function(data){
        data = data[0];
        var new_transaction = $("#new_transaction");
        new_transaction.find("#add_transaction").after("<button id='update_transaction' db_id='"+data['id']+"'>Update</button>");
        new_transaction.find("#add_transaction").after("<button id='delete_transaction' db_id='"+data['id']+"'>Delete</button>");

        new_transaction.find("#transaction_status option[selected='selected']").removeAttr('selected');
        new_transaction.find("#transaction_status option[value='"+data['status']+"']").attr('selected', 'selected');

        new_transaction.find("#account_select_list option[selected='selected']").removeAttr('selected');
        new_transaction.find("#account_select_list option[value='"+data['account']+"']").attr('selected', 'selected');

        new_transaction.find("#new_transaction_date").datepicker("setDate", data['date']);
        new_transaction.find("#new_transaction_name").val(data['name']);
        new_transaction.find("#transaction_amount").val(Math.abs(data['total']));
        new_transaction.find("#transaction_amount_remainder").html("");

        var t_i = $("div#transaction_items div.transaction_item:first-child");
        var t_i_data = data['items'][0];

        function insert_item_data(e, d) {
          e.find("input[name='transaction_item_name']").val(d['name']);
          log(d['type']);
          var type = CHART_TYPE_MAP[d['type']];
          e.find("select.chart_category_select_list optgroup[label='"+type+"'] option[value='"+d['category']+"']").attr('selected', 'selected');
          e.find("input[name='item_amount']").val(Math.abs(d['amount']));
        }
        insert_item_data(t_i, t_i_data);
        for (i=1; i<data['items'].length; i++) {
          var cloned_item = $("div#transaction_items div.transaction_item:last-child").clone();
          $("div#transaction_items").append(cloned_item);
          var t_i = $("div#transaction_items div.transaction_item:last-child");
          insert_item_data(t_i, data['items'][i]);
        }


      });
  });





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
    var column_width = 142;
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

  var add_transaction = function(){
    items = [];
    $("#transaction_items .transaction_item").each(function(){
      item = $(this);
      type = 'income';
      category = 0;
      opt_group_type_label = item.find(".chart_category_select_list option:selected").parents("optgroup").attr('label');
      if (opt_group_type_label != undefined) {
        type = opt_group_type_label;
        category = item.find(".chart_category_select_list option:selected").val();
      }
      items.push({'name':item.find("input[name='transaction_item_name']").val(),
        'amount':item.find("input[name='item_amount']").val(),
        'type':type,
        'category':category});
    });
    
    t_date = $("#new_transaction_date").datepicker("getDate");
    data_string = {'status':$("select#transaction_status option:selected").val(),
      'name':$("input[name='transaction_name']").val(),
      'date':formatISO(t_date),
      'account':$("#account_select_list option:selected").val(),
      'items':items};


    d = {'data_string':JSON.stringify(data_string)};
    log(d['data_string']);
    $.post("/"+db_name+"/financial-transaction-item", d, function(data){
      return_data = JSON.parse(data);
      if (return_data['status'] == 0 || return_data['status'] == 4) {
        load_transaction_list('cleared_suspect');
      } else {
        load_transaction_list('receipt_no_receipt_scheduled');
      }
      load_item_group_list();
      get_all_category_list(false);
      clear_new_transaction_form();
    });
  };

  $("#add_transaction").bind("click", add_transaction);

  $("#new_transaction").delegate("#update_transaction", 'click', function(e) {
      var id = $(this).attr("db_id");
      $.post("/"+db_name+"/financial-transaction-item/"+id+"/delete", {}, function(d){
        add_transaction();
      });
  });
  $("#new_transaction").delegate("#delete_transaction", 'click', function(e) {
      var id = $(this).attr("db_id");
      $.post("/"+db_name+"/financial-transaction-item/"+id+"/delete", {}, function(d){
        load_transaction_list('cleared_suspect');
        load_transaction_list('receipt_no_receipt_scheduled');
        load_item_group_list();
        clear_new_transaction_form();
      });
  });


  $("input[name='group_by']").bind("change", function(){
      if ($(this).attr('checked')) {
        var g = $(this).val();
        load_item_group_list();
      }
  });

  $("div.transaction_list").delegate("div.transaction_status a", "click", function(e){
      t_status = $(this).attr('title');
      id = $(this).parents("div.transaction").attr("db_id");
      data_string = {'status':t_status};
      d = {'data_string':JSON.stringify(data_string)};
      $.post("/"+db_name+"/financial-transaction-status/"+id, d);
      $(this).siblings("a").removeClass('active');
      $(this).addClass('active');
      e.preventDefault();
  });


});

