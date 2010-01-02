/**
 * Default pyClanSphere JavaScript Driver File
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 *
 * Part of the pyClanSphere core framework. Provides default script
 * functions for the base templates.
 *
 * :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
 * :license: BSD, see LICENSE for more details.
 */

var pyClanSphere = {
  TRANSLATIONS : {},
  PLURAL_EXPR : function(n) { return n == 1 ? 0 : 1; },
  LOCALE : 'unknown',

  getJSONServiceURL : function(identifier) {
    return this.ROOT_URL + '/_services/json/' + identifier;
  },

  callJSONService : function(identifier, values, callback) {
    $.getJSON(this.getJSONServiceURL(identifier), values, callback);
  },
  
  replyToComment : function(parent_id) {
    $('form.comments input[@name="parent"]').val(parent_id);
    $('#comment-message').hide();
    this.callJSONService('get_comment', {comment_id: parent_id}, function(c) {
      $('#comment-message')
        .addClass('info')
        .text(_('Replying to comment by %s.').replace('%s', c.author) + ' ')
        .append($('<a href="#">')
          .text(_('(Create as top level comment)'))
          .click(function() {
            pyClanSphere.replyToNothing();
            return false;
          }))
      document.location = '#leave-reply';
      $('#comment-message').fadeIn();
    });
  },

  replyToNothing : function() {
    $('form.comments input[@name="parent"]').val('');
    $('#comment-message').fadeOut();
  },

  gettext : function(string) {
    var translated = pyClanSphere.TRANSLATIONS[string];
    if (typeof translated == 'undefined')
      return string;
    return (typeof translated == 'string') ? translated : translated[0];
  },

  ngettext: function(singular, plural, n) {
    var translated = pyClanSphere.TRANSLATIONS[singular];
    if (typeof translated == 'undefined')
      return (n == 1) ? singular : plural;
    return translated[pyClanSphere.PLURALEXPR(n)];
  },

  addTranslations : function(catalog) {
    for (var key in catalog.messages)
      this.TRANSLATIONS[key] = catalog.messages[key];
    this.PLURAL_EXPR = new Function('n', 'return +(' + catalog.plural_expr + ')');
    this.LOCALE = catalog.locale;
  },

  // Adds text to a given textelement.
  // Sample usage:
  // <a href="javascript:void(0);" onclick="insertText('namedField','hello world');">Say hello world</a>
  insertText : function(element,value){
    var element_dom=document.getElementsByName(element)[0];
    if(document.selection){
      element_dom.focus();
      sel=document.selection.createRange();
      sel.text=value;
      return;
    }if(element_dom.selectionStart||element_dom.selectionStart=="0"){
      var t_start=element_dom.selectionStart;
      var t_end=element_dom.selectionEnd;
      var val_start=element_dom.value.substring(0,t_start);
      var val_end=element_dom.value.substring(t_end,element_dom.value.length);
      element_dom.value=val_start+value+val_end;
    }else{
      element_dom.value+=value;
    }
  }  
};

$(function() {
  $('#comment-message').hide();
});

// TinyMCE lazyloader, only load and use it if there's a textarea with tinymce class
$().ready(function() {
	$('textarea.tinymce').tinymce({
		// Location of TinyMCE script
		script_url : '/_shared/core/js/tiny_mce/tiny_mce.js',

		// General options
		theme : "advanced",
		plugins : "safari,inlinepopups,searchreplace,contextmenu,bbcode",

		// Theme options
		theme_advanced_buttons1 : "bold,italic,underline,strikethrough,|,justifyleft,justifycenter,justifyright,justifyfull,fontsizeselect,|,forecolor",
		theme_advanced_buttons2 : "search,replace,|,bullist,numlist,|,blockquote,|,undo,redo,|,link,unlink,anchor,image,cleanup,code",
		theme_advanced_buttons3 : "",
		theme_advanced_buttons4 : "",
		theme_advanced_toolbar_location : "top",
		theme_advanced_toolbar_align : "left",
		theme_advanced_resizing : true,
	});
});

// quick alias for translations
_ = pyClanSphere.gettext;
