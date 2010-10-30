jQuery.noConflict();
jQuery(document).ready(function($) {
  var CHART_TYPE_MAP = {'0':'income', '1':'expense', '2':'bill', '3':'saving'};

  $.getJSON("/"+db_name+"/user", function(data){
      html = ich.user_details(data);
      $('div#user_details').append(html);
  });

  var category_total = 0;
  function total_balance() {
    $.getJSON("/"+db_name+"/total-balance", function(data){
      //hash = {total:data};
      html = ich.total_balance_data(data);
      $('#total_balance').html(html);
      category_total = new Number(parseFloat($("#category_total").text()));
    });
  }
  total_balance();

  var available_balance = 0;
  function category_list() {
    $.getJSON("/"+db_name+"/expense-list-active", function(data){
      hash = {category:data};
      html = ich.expense_category_list(hash);
      $('#expense_category_list').html(html);
      available_balance = new Number(parseFloat($("#available-balance").text()));
      $(".category_list div.balance-slider").slider({
        step: 0.01,
        min: 0,
        max: 0,
        value: 0,
        slide: function(event, ui) {
          $(this).find("span.slider-balance-value").text(ui.value);
        },
        stop: function(event, ui) {
          //TODO: prevent from going over available balance
          var start_balance = new Number(parseFloat($(this).siblings("span.balance").text()));
          var new_balance = new Number(ui.value);
          var change_balance = new_balance - start_balance;
          //console.log("start = "+start_balance+" new = "+new_balance+" change = "+change_balance);
          if (change_balance > available_balance) {
            //$(this).slider('option', 'value', available_balance);
            ui.value = start_balance+available_balance;
            available_balance = 0;
          } else {
            available_balance = available_balance - change_balance;
          }

          //console.log(ui.value);
          $(this).siblings("span.balance").text(parseFloat(ui.value).toFixed(2));
          slider_values();
        }
      });
      slider_values();
    });
  };
  function slider_values() {
    $(".category_list div.balance-slider").each(function(){
      var b = new Number(parseFloat($(this).siblings("span.balance").text()));
      var max = new Number(parseFloat($(this).siblings("span.maximum").text()));
      var min = new Number(parseFloat($(this).siblings("span.minimum").text()));
      $(this).slider('option', 'max', max);
      $(this).slider('option', 'value', b);

      var minimum_graph = $(this).find(".minimum_graph");
      if (b < min) {
        minimum_graph.addClass('below');
      } else {
        minimum_graph.removeClass('below');
      }  
      var a = (min/max) * 100;
      minimum_graph.css({'width': a+"%"});

      var available_graph = $(this).find(".available_graph");
      var bal_pos = (b/max) * 100;
      var this_bal_available = Math.min(max - b, available_balance);
      var available_width = 0;
      if (this_bal_available > 0) {
        available_width = (this_bal_available/max) * 100;
      }
      available_graph.css({'left': bal_pos+"%", 'width':available_width+"%"});

      //$(this).find("span.slider-balance-value").css({'left': bal_pos+"%"});
      $(this).find("span.slider-balance-value").css({'left': bal_pos+"%"}).text(parseFloat(b).toFixed(2));
    });
  }
  category_list();
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
      total_balance();
      category_list();
    });
  });
});
