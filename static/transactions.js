jQuery.noConflict();
jQuery(document).ready(function($) {
  var add_blank_transaction_item = function(){
    $.getJSON("/"+db_name+"/expense-list-active", function(data){
      hash = {category:data}
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
    console.log('change');
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

  $("div#new_transaction_date").datepicker({
      dateFormat:'yy-mm-dd',
      });


  $("#add_transaction").bind("click", function(){
      items = [];
      $("#transaction_items .transaction_item").each(function(){
        item = $(this);
        items.push({'name':item.find("input[name='transaction_item_name']").val(),
          'amount':item.find("input[name='item_amount']").val(),
          'type':item.find("#chart_type_select_list option:selected").val(),
          'category':item.find("#category_select_list option:selected").val()});
      });
      
      t_date = $("#new_transaction_date").datepicker("getDate");
      data_string = {'status':$("select#transaction_status option:selected").val(),
        'name':$("input[name='transaction_name']").val(),
        'date':t_date.getFullYear()+"-"+(t_date.getMonth()+1)+"-"+t_date.getDate(),
        'account':$("#account_select_list option:selected").val(),
        'items':items};


      d = {'data_string':JSON.stringify(data_string)};
      console.log(d['data_string']);
      $.post("/"+db_name+"/financial-transaction-item", d);
  });


});

