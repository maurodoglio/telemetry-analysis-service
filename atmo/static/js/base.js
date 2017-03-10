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
    // switch tabs that are triggered by button groups instead of tabs
    var selector = '[data-toggle="btns"]';
    var toggleTab = function() {
      $(this)
        .addClass('active')
        .tab('show')
        .siblings('.btn')
          .removeClass('active');
    }

    // swtich tab on button group click
    $(selector + ' .btn').on('click', function(e) {
      e.preventDefault();
      $(this).map(toggleTab);
    });

    // show tab matching the document hash on load
    var url = document.location.toString();
    if (url.match('#')) {
      var tab = url.split('#')[1];
      $(selector + ' [href="#' + tab + '"]').map(toggleTab);
    }

    // prevent scrolling by pushing to the history directly
    $(selector).on('shown.bs.tab', function(event) {
      history.pushState(null, null, event.target.hash);
    });
  };

  var atmoClipboard = function() {
    var selector = '.btn-clipboard';

    $(selector).tooltip({
      trigger: 'click',
      placement: 'bottom'
    });

    var setTooltip = function(trigger, message) {
      $(trigger).tooltip('hide')
        .attr('data-original-title', message)
        .tooltip('show');
    }

    var hideTooltip = function(trigger) {
      setTimeout(function() {
        $(trigger).tooltip('hide');
      }, 1000);
    }

    var clipboard = new Clipboard(selector);

    clipboard.on('success', function(e) {
      setTooltip(e.trigger, 'Copied!');
      hideTooltip(e.trigger);
    });

    clipboard.on('error', function(e) {
      setTooltip(e.trigger, 'Failed!');
      hideTooltip(e.trigger);
    });
  }

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
  AtmoCallbacks.add(atmoClipboard);
  AtmoCallbacks.add(atmoWhatsNew);
  AtmoCallbacks.add(atmoTime);

  $(document).ready(function() {
    AtmoCallbacks.fire();
  });
});
