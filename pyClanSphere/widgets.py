# -*- coding: utf-8 -*-
"""
    pyClanSphere.widgets
    ~~~~~~~~~~~~~~~~~~~~

    This module provides the core widgets and functionality to build your
    own.  Widgets are, in the context of pyClanSphere, classes that have a
    unicode conversion function that renders a template into a string but
    have all their attributes attached to themselves.  This gives template
    designers the ability to change the general widget template but also
    render one widget differently.

    Additionally widgets could be moved around from the admin panel in the
    future.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from pyClanSphere.application import render_template


class Widget(object):
    """Baseclass for all the widgets out there!"""

    #: the name of the widget when called from a template.  This is also used
    #: if widgets are configured from the admin panel to have a unique
    #: identifier.
    name = None

    #: name of the template for this widget. Please prefix those template
    #: names with an underscore to mark it as partial. The widget is available
    #: in the template as `widget`.
    template = None

    def __unicode__(self):
        """Render the template."""
        return render_template(self.template, widget=self)

    def __str__(self):
        return unicode(self).encode('utf-8')


class IncludePage(Widget):
    """Includes a page."""

    name = 'include_page'
    template = 'widgets/include_page.html'

    def __init__(self, page_name, show_title=False):
        self.page_name = page_name
        self.page = Post.query.type('page').filter_by(slug=page_name).first()

    @property
    def exists(self):
        return self.page is not None


#: list of all core widgets
all_widgets = [IncludePage]
