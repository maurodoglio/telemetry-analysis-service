$(function() {
  AtmoCallbacks = $.Callbacks();

  // load Bootstrap popovers bubbles
  var atmoPopovers = function() {
    $('[data-popover="popover"]').popover();
  };

  // load Bootstrap confirmation
  var atmoConfirmations = function() {
    $('[data-toggle="confirmation"]').confirmation({
      rootSelector: '[data-toggle="confirmation"]',
    });
  };

  // jump to tab if tab name is found in document location
  var atmoTabs = function() {
    var url = document.location.toString();
    // show tab matching the document hash
    if (url.match('#')) {
      $('.nav-tabs a[href="#' + url.split('#')[1] + '"]').tab('show');
    }

    // prevent scrolling
    $('a[data-toggle="tab"]').on('shown.bs.tab', function(event) {
      if (history.pushState) {
          history.pushState(null, null, event.target.hash);
      } else {
          window.location.hash = event.target.hash; //Polyfill for old browsers
      }
    });
  };

  var atmoWhatsNew = function() {
    // Fill modal with content from link href
    $('#whatsnew-modal').on('show.bs.modal', function(e) {
        var link = $(e.relatedTarget);
        $(this).find('.modal-body').load(link.attr('href'));
    });
    var checker = $('#whatsnew-check'),
        checker_url = checker.attr('data-url');
    $.get(checker_url).done(function(data) {
      if (data !== 'ok') {
        checker.removeClass('hidden');
        checker.closest('li').removeClass('hidden');
      }
    });
  };

  var atmoTime = function() {
    var time = $('#time'),
        utc_now = function() {
          return moment().utcOffset(0).format('YYYY-MM-DD HH:mm:ss');
        };
    var updateTime = function() {
      time.attr('data-content', utc_now());
      window.setTimeout(updateTime, 1000);
    }
    updateTime();
  }

  AtmoCallbacks.add(atmoPopovers);
  AtmoCallbacks.add(atmoConfirmations);
  AtmoCallbacks.add(atmoTabs);
  AtmoCallbacks.add(atmoWhatsNew);
  AtmoCallbacks.add(atmoTime);
  $(document).ready(function() {
    AtmoCallbacks.fire();
  });
});
