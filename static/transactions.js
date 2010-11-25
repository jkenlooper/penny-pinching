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
  var all_category_hash = {'expense':{}, 'bill':{}, 'saving':{}, 'income':{}};
  var chart_category_hash = {'chart':[]};
  $("div#new_transaction_date").datepicker({
      dateFormat:'yy-mm-dd',
  });
  var lastmonth = new Date();
  var today = new Date();
  $("input#period-start").datepicker({
      dateFormat:'yy-mm-dd',
      defaultDate:'-1m'
  });
  $("input#period-start").datepicker("setDate", '-1m');
  $("input#period-end").datepicker({
      dateFormat:'yy-mm-dd'
  });
  $("input#period-end").datepicker("setDate", today);
  function get_all_category_list(add_blank_item) {
    $.getJSON("/"+db_name+"/all-category-list", function(data){
      all_category_list = data;
      for (chart_type in all_category_list) {
        var c = all_category_list[chart_type];
        if (chart_type != 'income') {
          var chart_hash = {'chart_name':chart_type, 'category':c};
          if (add_blank_item){
            chart_category_hash['chart'].push(chart_hash);
          }

          for (i=0; i<c.length; i++) {
            all_category_hash[chart_type][parseInt(c[i].id)] = c[i];
          }
        } else {
          for (i=0; i<c.length; i++) {
            all_category_hash[chart_type][parseInt(c[i].id)] = c[i];
          }
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
  function load_accounts() {
    $.getJSON("/"+db_name+"/account-list", function(data){

      active_data = [];
      inactive_data = [];
      for (i=0; i<data.length; i++) {
        data[i]['transaction_difference'] = (parseFloat(data[i]['transaction_total']).toFixed(2) - parseFloat(data[i]['balance']).toFixed(2)).toFixed(2);
        data[i]['disable_reconcile'] = "disabled='disabled'";
        if (parseFloat(data[i]['balance_difference']).toFixed(2) == '0.00' && parseFloat(data[i]['cleared_total']).toFixed(2) != '0.00' ) {
          data[i]['disable_reconcile'] = "";
        }
        if (data[i]['active'] == 1) {
          data[i]['active_checked'] = "checked='checked'";
          active_data.push(data[i]);
        } else {
          inactive_data.push(data[i]);
          data[i]['active_checked'] = "";
        }
      }
      hash = {account:active_data};
      html = ich.account_listing(hash);
      $("#account_listing").html(html);
      // position the graph data for each account

      $("#account_listing .account-block").each(function(i){
          //i = $("#account_listing .account-block").index(this);
          var balance = parseFloat(active_data[i]['balance']);
          var transaction_total = parseFloat(active_data[i]['transaction_total']);
          var transaction_difference = parseFloat(active_data[i]['transaction_difference']);
          var balance_difference = parseFloat(active_data[i]['balance_difference']);
          var suspect_total = parseFloat(active_data[i]['suspect_total']);
          var no_receipt_total = parseFloat(active_data[i]['no_receipt_total']);
          var receipt_total = parseFloat(active_data[i]['receipt_total']);
          var cleared_total = parseFloat(active_data[i]['cleared_total']);
          var reconciled_total = parseFloat(active_data[i]['reconciled_total']);

          var max = Math.max(balance, (Math.abs(reconciled_total)+Math.abs(cleared_total)+Math.abs(suspect_total)));
          
          var bbb = $(this).find("div.bank-balance-block");
          var w = (balance/max) * 100;
          bbb.find("div.bank-balance").css({'width':w+'%'});

          var reconciled_total_w = (Math.abs(reconciled_total)/max) * 100;
          var reconciled_l = Math.min((reconciled_total/max)*100, 0);
          bbb.find("div.reconciled-total").css({'left':reconciled_l+'%', 'width':reconciled_total_w+'%'});

          var cleared_total_w = (Math.abs(cleared_total)/max) * 100;
          var overlap = 0;
          var suspect_overlap = cleared_total_w;
          if (cleared_total < 0) {
            overlap = cleared_total_w;
            suspect_overlap = cleared_total_w - cleared_total_w*2;
          }
          bbb.find("div.cleared-total").css({'left':((reconciled_total_w+reconciled_l)-overlap)+'%', 'width':cleared_total_w+'%'});

          var suspect_total_w = (Math.abs(suspect_total)/max) * 100;
          var overlap = 0;
          if (suspect_total < 0) {
            overlap = suspect_total_w;
          }
          bbb.find("div.suspect-total").css({'left':(((reconciled_total_w+reconciled_l)+suspect_overlap)-overlap)+'%', 'width':suspect_total_w+'%'});

          if (balance_difference < 0) {
            bbb.find("div.graph-difference").css({'color':'red'});
          }

            
          


      });



      if (inactive_data.length) {
        hash = {account:inactive_data};
        html = ich.inactive_account_listing(hash);
        $("#inactive_account_listing").html(html);
      }

      hash = {accounts:active_data};
      html = ich.account_select_list(hash);
      $('#account_select_list').html(html);
    });
  }
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
    var start = formatISO($("input#period-start").datepicker('getDate'));
    var end = formatISO($("input#period-end").datepicker('getDate'));
    var url = "/"+db_name+"/financial-transaction-list/period/"+start+"."+end+"/status/"+status_set+"?order_by="+order_by;
    if (status_set == 'cleared_suspect' || status_set == 'receipt_no_receipt_scheduled') {
      url = "/"+db_name+"/financial-transaction-list/"+status_set+"?order_by="+order_by;
    }
    $.getJSON(url, function(data){
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
  load_transaction_list('reconciled');
  load_accounts();

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
        if ((type_name != 'income') && (category_id != 0)) {
          group_id = all_category_hash[type_name][parseInt(category_id)].name;
        } else {
          group_id = 'income';
        }
      } else if (group_by == 'date') {
        group_id = item['date'];
      }

      if (!(group_id in groups)) {
        groups[group_id] = {'item':[], 'name':group_id, 'total':0.00, 'group_by':group_by}
      }
      groups[group_id]['item'].push(item);
    }
    var group_keys = [];
    for (var g in groups) {
      group_keys.push(g);
    }
    group_keys.sort();
    while (group_keys.length > 0) {
      var k = group_keys.shift();
      var total = 0.00;
      for (i in groups[k]['item']) {
        item = groups[k]['item'][i];
        total += new Number(item['amount']);
      }
      groups[k]['total'] = parseFloat(total.toFixed(2));
      item_group.push(groups[k]);
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
    var start = formatISO($("input#period-start").datepicker('getDate'));
    var end = formatISO($("input#period-end").datepicker('getDate'));
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
      load_transaction_list('reconciled');
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
      load_accounts();
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
        load_accounts();
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

  $("div#account_listing").delegate("input[name='update']", "click", function(e){
      var a = $(this).parents("div.account-block");
      var id = a.attr("db_id");
      var d = new Date();
      var today = formatISO(d);
      var active = 0;
      if (a.find("input[name='active']:checked").val()) {
        active = 1;
      }
      data_string = {'name':a.find(".account_name").text(), 'active':active, 'balance':a.find("input[name='balance']").val(), 'balance_date':today};
      d = {'data_string':JSON.stringify(data_string)};
      $.post("/"+db_name+"/account/"+id+"/update", d, function(d) {
        load_accounts();
      });
  });
  $("div#inactive_account_listing").delegate("input[name='active']", "click", function(e) {
      var a = $(this).parents("div.account-block");
      var id = a.attr("db_id");
      data_string = {'active':1};
      d = {'data_string':JSON.stringify(data_string)};
      $.post("/"+db_name+"/account/"+id+"/activate", d, function(d) {
        load_accounts();
      });
  });
  $("input[name='new_account']").toggle(function(e){
      $("#new_account-form").show();
      $(this).val("-");
  }, function(e){
      $("#new_account-form").hide();
      $(this).val("+");
  });
  $("input[name='create_new_account']").bind("click", function(e) {
      var a = $("#new_account-form");
      data_string = {'name':a.find("input[name='name']").val(), 'balance':a.find("input[name='balance']").val()};
      d = {'data_string':JSON.stringify(data_string)};
      $.post("/"+db_name+"/account", d, function(d) {
        var a = $("#new_account-form");
        a.find("input[name='name']").val("")
        a.find("input[name='balance']").val("")
        load_accounts();
      });
  });

  $("div#account_listing").delegate("input[name='reconcile']", "click", function(e){
      var id = $(this).parents("div.account-block").attr("db_id");
      $.post("/"+db_name+"/account/"+id+"/cleared-to-reconciled", {}, function(d){
        load_transaction_list('cleared_suspect');
      });
  });



});

