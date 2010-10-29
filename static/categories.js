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
      var available_balance = new Number(parseFloat($("#available-balance").text()));
      $("#expense_category_list div.balance-slider").slider({
        step: 0.01,
        min: 0,
        max: 0,
        value: 0,
        slide: function(event, ui) {
          //$(this).siblings("span.balance").text(ui.value);
        },
        stop: function(event, ui) {
          var start_balance = new Number(parseFloat($(this).siblings("span.balance").text()));
          var new_balance = new Number(ui.value);
          var change_balance = new_balance - start_balance;
          //console.log("start = "+start_balance+" new = "+new_balance+" change = "+change_balance);
          var this_max = ui.max;
          $(this).addClass('current_slider');
          $("div.balance-slider").not(".current_slider").each(function(e){ // TODO: filter out the current slider
            var m = $(this).slider('option', 'max');
            var v = $(this).slider('option', 'value');
            var new_max = m-change_balance;
            //console.log('change = '+change_balance+' max = '+m+' new max = '+new_max);
            $(this).slider('option', 'max', new_max);
            $(this).slider('option', 'value', v);
          });
          $(this).removeClass('current_slider');
          $(this).siblings("span.balance").text(ui.value);
        }
      });
      $("#expense_category_list div.balance-slider").each(function(){
        var b = new Number(parseFloat($(this).siblings("span.balance").text()));
        $(this).slider('option', 'max', b+available_balance);
        $(this).slider('option', 'value', b);
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
    //console.log(d.data_string);
    $.post("/"+db_name+"/expense", d, function(data){
      expense_category_list();
      total_balance();
    });
  });
});
