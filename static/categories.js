/* FireBug console.log wrapper */
function log() {
  if (typeof(console) != 'undefined' && typeof(console.log) == 'function') {
    Array.prototype.unshift.call(arguments, '[categories]');
    console.log(Array.prototype.join.call(arguments, ' '));
  }
}
jQuery.noConflict();
jQuery(document).ready(function($) {
  var CHART_TYPE_MAP = {'0':'income', '1':'expense', '2':'bill', '3':'saving'};

  $.getJSON("/"+db_name+"/user", function(data){
      html = ich.user_details(data);
      $('div#user_details').append(html);
  });

  $(".toggle_add_form").toggle(function(e){
      $(this).parents("div.category_type").find("div.form").show();
      $(this).html("hide add form");
    },
    function(e){
      $(this).parents("div.category_type").find("div.form").hide();
      $(this).html("show add form");
    });

  var category_total = 0;
  var available_balance = 0;
  function total_balance() {
    $.getJSON("/"+db_name+"/total-balance", function(data){
      //hash = {total:data};
      html = ich.total_balance_data(data);
      $('#total_balance').html(html);
      category_total = new Number(parseFloat($("#category_total").text()));
      available_balance = new Number(parseFloat($("#available-balance").text()));
    });
  }
  total_balance();

  $.getJSON("/"+db_name+"/setting/expense_allotment/", function(data){
      var v = data[0]['setting'];
      var el = $("#expense_saving_allotment");
      $("div#expense > h2 .allotment").text("["+v+"]");
      $("div#saving > h2 .allotment").text("["+(100-v)+"]");
      el.val(v);
      el.change(function(event) {
        var v = $(this).val();
        var data_string = {'setting':parseInt(el.val(), 10)};
        $("div#expense > h2 .allotment").text("["+v+"]");
        $("div#saving > h2 .allotment").text("["+(100-v)+"]");
        d = {'data_string':JSON.stringify(data_string)};
        $.post("/"+db_name+"/setting/expense_allotment/update", d, function(data){});
      });
  });


  function category_list() {
    $.getJSON("/"+db_name+"/expense-list-active", function(data){
      hash = {category:data};
      html = ich.expense_category_list(hash);
      $('#expense_category_list').html(html);
      available_balance = new Number(parseFloat($("#available-balance").text()));
      $(".balance-slider").change(function(event){
        var el = $(this);
        var expense_category_el = el.parents(".expense_category");
        expense_category_el.find("span.slider-balance-value").text(el.val());

          var start_balance = new Number(parseFloat(expense_category_el.find("span.balance").text()));
          var new_balance = new Number(el.val());
          var change_balance = new_balance - start_balance;
          if (change_balance > available_balance) {
            el.val( start_balance+available_balance );
            available_balance = 0;
          } else {
            available_balance = available_balance - change_balance;
          }

          expense_category_el.find("span.balance").text(parseFloat(el.val()).toFixed(2));
          data_string = { 'balance':parseFloat(el.val()).toFixed(2) };

          d = {'data_string':JSON.stringify(data_string)};
          var cat_id = expense_category_el.attr("db_id");
          $.post("/"+db_name+"/expense-balance/"+cat_id, d, function(data){
            total_balance();
            slider_values();
          });
      });
      slider_values();
    });
    $.getJSON("/"+db_name+"/bill-list-active", function(data){
      hash = {category:data};
      html = ich.bill_category_list(hash);
      $('#bill_category_list').html(html);
    });
    $.getJSON("/"+db_name+"/saving-list-active", function(data){
      hash = {category:data};
      html = ich.saving_category_list(hash);
      $('#saving_category_list').html(html);
      $("#saving_category_list div.saving_category").each(function(e){
        var bar = $(this).find("div.bar");
        var max = new Number(parseFloat(bar.find("span.maximum").text()));
        var balance = new Number(parseFloat(bar.find("span.balance").text()));
        if (max > 0) {
          var balance_width = (balance/max) * 100;
          bar.find("span.balance").css({'width': balance_width+"%"});
          bar.find("span.allotment_date").css({'left': balance_width+"%"});
          var allotment_amount = new Number(parseFloat(bar.find("span.allotment_amount").text()));
          var allotment_amount_width = (allotment_amount/max) * 100;
          a_a_left = balance_width - allotment_amount_width;
          bar.find("span.allotment_amount").css({'left':a_a_left+"%", 'width':allotment_amount_width+"%"});
          var minimum = new Number(parseFloat(bar.find("span.minimum").text()));
          min_width = (minimum/max) * 100;
          m = a_a_left + min_width;
          if (m > 100) { m = 100; }
          bar.find("span.minimum").css({'left': m+"%"});
        }
      });
    });
  };
  function inactive_list() {
    $.getJSON("/"+db_name+"/expense-list-inactive", function(data){
        hash = {category:data};
        html = ich.inactive_category_list(hash);
        $('#expense_category_inactive_list').html(html);
    });
    $.getJSON("/"+db_name+"/bill-list-inactive", function(data){
        hash = {category:data};
        html = ich.inactive_category_list(hash);
        $('#bill_category_inactive_list').html(html);
    });
    $.getJSON("/"+db_name+"/saving-list-inactive", function(data){
        hash = {category:data};
        html = ich.inactive_category_list(hash);
        $('#saving_category_inactive_list').html(html);
    });
  }
  function slider_values() {
    $(".category_list .expense_category").each(function(){
      var b = new Number(parseFloat($(this).find("span.balance").text()));
      var max = new Number(parseFloat($(this).find("span.maximum").text()));
      var min = new Number(parseFloat($(this).find("span.minimum").text()));
      var slider = $(this).find(".balance-slider");
      slider.attr('max', max);
      slider.val(b);

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

      $(this).find("span.slider-balance-value").css({'left': bal_pos+"%"}).text(parseFloat(b).toFixed(2));
    });
  }
  category_list();
  inactive_list();
  $("#add_expense_category").bind('click', function(e){
    data_string = {'name':$("#expense input[name='name']").val(),
      'balance':$("#expense input[name='balance']").val(),
      'minimum':$("#expense input[name='minimum']").val(),
      'maximum':$("#expense input[name='maximum']").val(),
      'allotment':$("#expense input[name='allotment']").val()
      };

    d = {'data_string':JSON.stringify(data_string)};
    $.post("/"+db_name+"/expense", d, function(data){
      total_balance();
      category_list();
    });
  });
  $("#expense_category_list").delegate(".edit-button[value='edit']", "click", function(){
      var category = $(this).parents("div.expense_category");
      var id = category.attr("db_id");
      $.getJSON("/"+db_name+"/expense/"+id, function(data){
        data = data[0];
        if (data['active'] == 1) {
          data['checked'] = "checked='checked'";
        } else {
          data['checked'] = "";
        }
          
        html = ich.expense_category_list_edit(data);
        var category = $("#expense_id-"+data['id']);
        category.append(html);
        edit_button = category.find(".edit-button");
        edit_button.val('save').text('save');
        edit_button.bind('click', function(e){
          var edit_form = category.find('.edit-form');
          var active = "0";
          if (edit_form.find("input[name='active']:checked").val()) {
            active = "1";
          }
          data_string = {'name':edit_form.find("input[name='name']").val(),
            'balance':edit_form.find("input[name='balance']").val(),
            'minimum':edit_form.find("input[name='minimum']").val(),
            'maximum':edit_form.find("input[name='maximum']").val(),
            'allotment':edit_form.find("input[name='allotment']").val(),
            'active':active
            };

          d = {'data_string':JSON.stringify(data_string)};
          $.post("/"+db_name+"/expense/"+$(this).parents("div.expense_category").attr("db_id")+"/update", d, function(data){
            total_balance();
            category_list();
            inactive_list();
          });
        });
      });
  });
  $("div#bill_category_list").delegate(".edit-button[value='edit']", "click", function(){
      var category = $(this).parents("div.bill_category");
      var id = category.attr("db_id");
      $.getJSON("/"+db_name+"/bill/"+id, function(data){
        data = data[0];
        if (data['active'] == 1) {
          data['checked'] = "checked='checked'";
        } else {
          data['checked'] = "";
        }
          
        html = ich.bill_category_list_edit(data);
        var category = $("#bill_id-"+data['id']);
        category.append(html);
        category.find("input[name='allotment_date']").datepicker({
            dateFormat:'yy-mm-dd',
            onSelect:function(dateText, inst){
              category.find("input[name='due']").datepicker("option", "minDate", dateText);
            }
        });
        category.find("input[name='due']").datepicker({
            dateFormat:'yy-mm-dd',
            onSelect:function(dateText, inst){
              category.find("input[name='allotment_date']").datepicker("option", "maxDate", dateText);
            }
        });
        edit_button = category.find(".edit-button");
        edit_button.val('save').text('save');
        edit_button.bind('click', function(e){
          var edit_form = category.find('.edit-form');
          var active = "0";
          if (edit_form.find("input[name='active']:checked").val()) {
            active = "1";
          }
          data_string = {'name':edit_form.find("input[name='name']").val(),
            'balance':edit_form.find("input[name='balance']").val(),
            'maximum':edit_form.find("input[name='maximum']").val(),
            'allotment_date':edit_form.find("input[name='allotment_date']").val(),
            'due':edit_form.find("input[name='due']").val(),
            'repeat_due_date':edit_form.find("input[name='repeat_due_date']").val(),
            'active':active
            // TODO: add delete checkbox
            };

          d = {'data_string':JSON.stringify(data_string)};
          $.post("/"+db_name+"/bill/"+$(this).parents("div.bill_category").attr("db_id")+"/update", d, function(data){
            total_balance();
            category_list();
            inactive_list();
          });
        });
      });
  });
  $("div#saving_category_list").delegate(".edit-button[value='edit']", "click", function(){
      var category = $(this).parents("div.saving_category");
      var id = category.attr("db_id");
      $.getJSON("/"+db_name+"/saving/"+id, function(data){
        data = data[0];
        if (data['active'] == 1) {
          data['checked'] = "checked='checked'";
        } else {
          data['checked'] = "";
        }
          
        html = ich.saving_category_list_edit(data);
        var category = $("#saving_id-"+data['id']);
        category.append(html);
        category.find("input[name='allotment_date']").datepicker({
            dateFormat:'yy-mm-dd'
        });
        edit_button = category.find(".edit-button");
        edit_button.val('save').text('save');
        edit_button.bind('click', function(e){
          var edit_form = category.find('.edit-form');
          var active = "0";
          if (edit_form.find("input[name='active']:checked").val()) {
            active = "1";
          }
          data_string = {'name':edit_form.find("input[name='name']").val(),
            'balance':edit_form.find("input[name='balance']").val(),
            'minimum':edit_form.find("input[name='minimum']").val(),
            'maximum':edit_form.find("input[name='maximum']").val(),
            'allotment_amount':edit_form.find("input[name='allotment_amount']").val(),
            'allotment_date':edit_form.find("input[name='allotment_date']").val(),
            'repeat_date':edit_form.find("input[name='repeat_date']").val(),
            'allotment':edit_form.find("input[name='allotment']").val(),
            'active':active
            };

          d = {'data_string':JSON.stringify(data_string)};
          $.post("/"+db_name+"/saving/"+$(this).parents("div.saving_category").attr("db_id")+"/update", d, function(data){
            total_balance();
            category_list();
            inactive_list();
          });
        });
      });
  });

  
  // bill category
  $("#bill input[name='allotment_date']").datepicker({
      dateFormat:'yy-mm-dd',
      onSelect:function(dateText, inst){
        $("#bill input[name='due']").datepicker("option", "minDate", dateText);
      }
  });
  $("#bill input[name='due']").datepicker({
      dateFormat:'yy-mm-dd',
      onSelect:function(dateText, inst){
        $("#bill input[name='allotment_date']").datepicker("option", "maxDate", dateText);
      }
  });
  $("#add_bill_category").bind('click', function(e){
    data_string = {'name':$("#bill input[name='name']").val(),
      'balance':$("#bill input[name='balance']").val(),
      'maximum':$("#bill input[name='maximum']").val(),
      'allotment_date':$("#bill input[name='allotment_date']").val(),
      'repeat_due_date':$("#bill input[name='repeat_due_date']").val(),
      'due':$("#bill input[name='due']").val()
      };

    d = {'data_string':JSON.stringify(data_string)};
    $.post("/"+db_name+"/bill", d, function(data){
      total_balance();
      category_list();
    });
  });

  // saving category
  $("#saving input[name='allotment_date']").datepicker({
      dateFormat:'yy-mm-dd'
  });
  $("#add_saving_category").bind('click', function(e){
      data_string = {'name':$("#saving input[name='name']").val(),
        'balance':$("#saving input[name='balance']").val(),
        'minimum':$("#saving input[name='minimum']").val(),
        'maximum':$("#saving input[name='maximum']").val(),
        'allotment_amount':$("#saving input[name='allotment_amount']").val(),
        'allotment_date':$("#saving input[name='allotment_date']").val(),
        'repeat_date':$("#saving input[name='repeat_date']").val(),
        'allotment':$("#saving input[name='allotment']").val()
        };
    d = {'data_string':JSON.stringify(data_string)};
    $.post("/"+db_name+"/saving", d, function(data){
      total_balance();
      category_list();
    });
  });

  // repeat_date clicks
  $(".repeat_date-example").bind('click', function(e){
      var r = $(this).text()
      $(this).parents(".label_value").find("input.repeat_date").val(r);
  });

  // inactive list
  $(".inactive_category_list").delegate(".inactive_category_list a", "click", function(e) {
      data_string = { 'active':1 };
      var category_type = $(this).parents("div.category_type").attr("id");
      d = {'data_string':JSON.stringify(data_string)};
      var cat_id = $(this).attr("db_id");
      $.post("/"+db_name+"/"+category_type+"-active/"+cat_id, d, function(data){
        //$("div#inactive_category-"+data['id']).remove();
        total_balance();
        category_list();
      });
      $(this).parents("div.inactive_category").remove();
      e.preventDefault();
  });

});
