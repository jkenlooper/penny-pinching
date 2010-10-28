jQuery.noConflict();
jQuery(document).ready(function($) {
  var CHART_TYPE_MAP = {'0':'income', '1':'expense', '2':'bill', '3':'saving'};

  $.getJSON("/"+db_name+"/user", function(data){
      html = ich.user_details(data);
      $('div#user_details').append(html);
  });

  function total_balance() {
    $.getJSON("/"+db_name+"/total-balance", function(data){
      //hash = {total:data};
      html = ich.total_balance_data(data);
      $('#total_balance').html(html);
    });
  }
  total_balance();

  function expense_category_list() {
    $.getJSON("/"+db_name+"/expense-list-active", function(data){
      hash = {category:data};
      html = ich.expense_category_list(hash);
      $('#expense_category_list').html(html);
      var available_balance = parseFloat($("#available-balance").text()).toFixed(2);
      $("#expense_category_list div.balance-slider").slider({step:0.01}).each(function(){
        var b = parseFloat($(this).text()).toFixed(2);
        $(this).slider('option', 'value', b);
        $(this).slider('option', 'max', b+available_balance);
      });
    });
  };
  expense_category_list();
  $("#add_expense_category").bind('click', function(e){
    data_string = {'name':$("input[name='name']").val(),
      'balance':$("input[name='balance']").val(),
      'minimum':$("input[name='minimum']").val(),
      'maximum':$("input[name='maximum']").val(),
      'allotment':$("input[name='allotment']").val()
      };

    d = {'data_string':JSON.stringify(data_string)};
    console.log(d.data_string);
    $.post("/"+db_name+"/expense", d, function(data){
      expense_category_list();
      total_balance();
    });
  });
});
