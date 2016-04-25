$(function() {
  // set up form element popovers
  $('[data-toggle="popover"]').popover();

  // apply validation for form controls
  $('input, select, textarea').not('[type=submit]').jqBootstrapValidation();

  // apply datetimepicker initialization
  $('.datetimepicker').datetimepicker({
    sideBySide: true, // show the time picker and date picker at the same time
    useCurrent: false, // don't automatically set the date when opening the dialog
    widgetPositioning: {vertical: 'bottom'}, // make sure the picker shows up below the control
    format: 'YYYY-MM-DD h:mm',
  });

  $(".editable-table").each(function(i, e) {
    $(e).find("tr:has(td)").first().addClass("selected");
  })
  $(".editable-table tr:has(td)").click(function() {
    // allow selecting individual rows
    $(this).parents("table").first().find("tr").removeClass("selected");
    $(this).addClass("selected");
  });
});
