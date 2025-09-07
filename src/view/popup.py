#!/usr/bin/python3
# file name .......... popup.py
# scope .............. create pop-up windows on the main interface
# language ........... Python 3.11.2
# author ............. Stefano Alemani
# date ............... 14-08-2025
# version ............ 0.6.0

import urwid

class PopUpDetails(urwid.WidgetWrap):
    """ 
    Class for manage popup
    Example of use: pop = popup.PopUpDetails(app_base)
                    user_interface = UiClassExample()
                    pop.showPopup(head="title of ui", layout=user_interface)

    """
    def __init__(self, app):
        self.app = app

    def show_popup(self, head, layout):
        # head is title, layout is ui
        head_text = urwid.Text(head, align='center')

        popup_frame = urwid.Frame(
            header=head_text,            
            body=layout,
            footer=urwid.Pile([urwid.Divider()]) #, close_button])
        )
        popup = urwid.LineBox(popup_frame)
        
        # overlay widget base
        self.app.loop.widget = urwid.Overlay(
            popup, self.app.loop.widget,
            align='center', width=('relative', 80),
            valign='middle', height=('relative', 70),
            min_width=80, min_height=10
        )

    def close_popup(self, data=[]):
        # close popup and return control to main app.
        self.app.loop.widget = self.app.main