$(function() {
  AtmoCallbacks = $.Callbacks();
  var tooltip = function() {
    $('[data-toggle="tooltip"]').tooltip();
    $('[data-toggle="confirmation"]').confirmation({
      rootSelector: '[data-toggle="confirmation"]',
    });
  };
  AtmoCallbacks.add(tooltip);
  // jump to tab if tab name is found in document location
  var atmoTabs = function() {
    var url = document.location.toString();
    // show tab matching the document hash
    if (url.match('#')) {
      $('.nav-tabs a[href="#' + url.split('#')[1] + '"]').tab('show');
    }

    // prevent scrolling
    $('.nav-tabs a').on('shown.bs.tab', function(event) {
      if (history.pushState) {
          history.pushState(null, null, event.target.hash);
      } else {
          window.location.hash = event.target.hash; //Polyfill for old browsers
      }
    });
  };

  AtmoCallbacks.add(atmoTabs);
  $(document).ready(function() {
    AtmoCallbacks.fire();
  });
});
