/**
 * pyClanSphere Administration Tools
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 *
 * Part of the pyClanSphere core framework. Provides default script
 * functions for the administration interface.
 *
 * :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
 * :license: BSD, see LICENSE for more details.
 */

 $(function() {
   // fade in messages
   (function() {
     var shuttingDown = false;
     var active = false;
     var msg = null, left, top, right, bottom;
     var messages = $('div.message').hide().fadeIn('slow');

     function fadeInMsg() {
       if (msg)
         msg.css('visibility', 'visible').animate({'opacity': '1.0'}, 'fast');
       msg = null;
     }

     messages.mouseenter(function() {
       if (shuttingDown && !$(this).is('.message-error'))
         return;
       if (msg)
         fadeInMsg();
       msg = $(this);
       var pos = msg.offset();
       left = pos.left - 2, top = pos.top - 2;
       right = left + msg.width() + parseInt(msg.css('padding-left')) +
               parseInt(msg.css('padding-right')) + 4;
       bottom = top + msg.height() + parseInt(msg.css('padding-top')) +
                parseInt(msg.css('padding-bottom')) + 4;
       msg.animate({
         opacity:      '0.01'
       }, 'fast', function() { msg.css('visibility', 'hidden'); });
     });

     $(document).mousemove(function(evt) {
       if (!msg)
         return;
       if (evt.clientX < left || evt.clientX > right ||
           evt.clientY < top || evt.clientY > bottom)
         fadeInMsg();
     });

     window.setTimeout(function() {
       msg = null;
       shuttingDown = true;
       messages.each(function() {
         if (!$(this).is('.message-error')) {
           $(this).animate({height: 'hide', opacity: 'hide'}, 'slow');
         }
       });
     }, 8000);
   })();

   // support for toggleable sections
   $('div.toggleable').each(function() {
     var
       fieldset = $(this),
       children = fieldset.children().slice(1);
     // collapse it if it should be collapsed and there are no errors in there
     if ($(this).is('.collapsed') && $('.errors', this).length == 0)
       children.hide();
     $('h3', this).click(function() {
       children.toggle();
       fieldset.toggleClass('collapsed');
     });
   });

   // Make some textareas resizable
   (function() {
     var ta = $('textarea.resizable');
     if (ta.length == 0)
       return;

     ta.TextAreaResizer();

     // make all forms remember the height of the textarea.  This
     // code does funny things if multiple textareas are resizable
     // but it should work for most situations.
     var cookie_set = false;
     $('form').submit(function() {
       if (cookie_set)
         return;
       var height = parseInt($('form textarea.resizable').css('height'));
       if (height > 0)
         document.cookie = 'ta_height=' + height;
       cookie_set = true;
     });

     // if we have the textarea height in the cookie, update the
     // height for the textareas.
     var height = document.cookie.match(/ta_height=(\d+)/)[1];
     if (height != null)
       ta.css('height', height + 'px');
   })();
 });

// optional field clear on focus
// restores content on blur without change
// usage: <input class="clearMeOnFocus">
$(document).ready(function(){
  var clearMeBefore = '';

  $('.clearMeOnFocus').focus(function()
  {
    if(clearMeBefore=='')
    {
      clearMeBefore = $(this).val();
    }
    if($(this).val()!='' && $(this).val()==clearMeBefore)
    {
      clearMeBefore = $(this).val();
      $(this).val('');
    }
  });

  $('.clearMeOnFocus').blur(function()
  {
    if($(this).val()=='')
    {
      $(this).val(clearMeBefore);
    }
  });
});