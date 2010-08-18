#!/usr/bin/env python

"""
    Copyright 2009 Johan Forsberg

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import division

#import numpy
import pygtk, gobject
pygtk.require('2.0')
import gtk, gtk.glade
import Image, ImageDraw, ImageChops
import random, math
import cPickle
import os

#from gui import build_gui
from image import PyntImage, PyntBrush, PyntImagePalette
from stack import PyntStack, PyntLayer
from palette import PyntPalette, PyntPaletteView
from paper import PyntPaper
from utils import file_browse, make_bbox, combine_bbox
from format import PyntData


class PyntMain(object):

    def __init__(self, image=None):
        #if image is None:
        #    self.image = PyntImage()
        #else:
        #    self.image = image

        self.save_file = ""
        self.brush_file = ""

        self.stack=PyntStack()

        #self.tool = "pencil"
        #self.width = 1
        #self.color = 1
        #self.secondcolor = 0

        #self.lx = 0
        #self.ly = 0

        #self.brush = PyntBrush((self.width, self.width), color=self.color)

        # setup GUI
        #self.builder = gtk.Builder()
        #self.builder.add_from_file("pynt.glade")
        self.gladefile = "pynt.glade"
        self.mainTree = gtk.glade.XML(self.gladefile, "mainwindow")
        self.peTree = gtk.glade.XML(self.gladefile, "palette_editor")

        self.mainwindow = self.mainTree.get_widget("mainwindow")

        #self.mainTree = self.builder


        # Drawing area
	gobject.type_register(PyntPaper)
        print "paper"

        self.paper = PyntPaper(self.stack)
        print "done"

        self.scrolledwindow = self.mainTree.get_widget("scrolledwindow")
        self.scrolledwindow.add(self.paper)

        self.paper.connect("fgcolor-picked", self.set_fgcolor)
        self.paper.connect("bgcolor-picked", self.set_bgcolor)
        self.paper.connect("coords-changed", self.set_coords)
        self.paper.connect("set-tool", lambda w, t: self.set_tool(t))

        #self.set_width(1)
        self.paper.show()

        dic = {"on_mainWindow_destroy" : gtk.main_quit,
               #"on_zoom_in" :  lambda w: self.set_zoom(self.view.zoom*2),
               "on_zoom_in" :  lambda w: self.paper.set_zoom(self.paper.zoom*2),
               "on_zoom_out" :  lambda w: self.paper.set_zoom(self.paper.zoom//2),
               "on_next_layer" :  lambda w: self.next_layer(),
               "on_prev_layer" :  lambda w: self.prev_layer(),
               "on_add_layer" :  lambda w: self.add_layer(),
               "on_delete_layer" :  lambda w: self.delete_layer(),
               "on_menu_join_layers" : self.on_join_layers,
               "on_layer_up" : self.on_layer_up,
               "on_layer_down" : self.on_layer_down,
               "on_button_points_clicked" : lambda w: self.set_tool("points"),
               "on_button_pencil_clicked" : lambda w: self.set_tool("pencil"),
               "on_button_line_clicked" : lambda w: self.set_tool("line"),
               "on_button_rectangle_clicked" : lambda w: self.set_tool("rectangle"),
               "on_button_floodfill_clicked" : lambda w: self.set_tool("floodfill"),
               "on_button_ellipse_clicked" : lambda w: self.set_tool("ellipse"),
               "on_button_brush_clicked" : lambda w: self.set_tool("brush"),
               "on_button_colorpicker_clicked" : lambda w: self.set_tool("colorpicker"),
               "on_button_width_value_changed" : lambda w: self.set_width(w.get_value_as_int()),
               "on_menu_brush_hflip" : lambda w: self.paper.brush.flip(vertically=False),
               "on_menu_brush_vflip" : lambda w: self.paper.brush.flip(vertically=True),
               "on_menu_brush_rotate_plus90" : lambda w: self.paper.brush.rotate(90),
               "on_menu_brush_rotate_minus90" : lambda w: self.paper.brush.rotate(-90),
               "on_brush_solid_color_toggle" : self.on_brush_solid_color_toggle,
                "on_menu_brush_export" : self.on_export_brush,
               "on_menu_clear" : self.on_clear_layer,
               "on_menu_animated_toggled" : self.toggle_frame,
               "on_menu_layer_visible_toggled" : self.toggle_visible,
               "on_menu_paletteeditor" : self.on_menu_paletteeditor,
               "on_next_frame" : lambda w: self.next_frame(),
               "on_prev_frame" : lambda w: self.prev_frame(),
               "on_undo" : self.on_undo,
               "on_redo" : self.on_redo,
               "on_button_palette_prev_clicked" : self.palette_prev,
               "on_button_palette_next_clicked" : self.palette_next,
               "on_menu_save_activate" : self.on_save_image,
               "on_menu_load_activate" : self.on_load_image,
               "on_menu_save_as" : self.on_save_image_as,
               "on_menu_import_image_activated" : self.on_import_image,
               "on_menu_export_image_activated" : self.on_export_image,

               #"on_pe_spinbutton_red_change_value" : self.on_pe_color_edited,
               "on_pe_button_undo_clicked" : self.on_pe_button_undo
               }

        self.mainTree.signal_autoconnect(dic)


#         self.drawing_area = gtk.DrawingArea()
#         self.view = PyntView(self.drawing_area, self.stack)
#         self.viewport = self.mainTree.get_object("viewport")

#         self.drawing_area.set_size_request(*self.view.get_size())

#         #self.viewport.show()

#         # Event signals
#         self.drawing_area.connect("expose_event", self.expose_event)
#         # size/pos/stacking change
#         self.drawing_area.connect("configure_event", self.configure_event)

#         self.drawing_area.connect("motion_notify_event", self.motion_notify_event)
#         self.drawing_area.connect("button_press_event", self.button_press_event)
#         self.drawing_area.connect("button_release_event", self.button_release_event)
#         self.drawing_area.connect("leave_notify_event", self.leave_notify_event)

#         self.drawing_area.set_events(gtk.gdk.EXPOSURE_MASK
#                             | gtk.gdk.LEAVE_NOTIFY_MASK
#                             | gtk.gdk.BUTTON_PRESS_MASK
#                             | gtk.gdk.BUTTON_RELEASE_MASK
#                             | gtk.gdk.POINTER_MOTION_MASK
#                             | gtk.gdk.POINTER_MOTION_HINT_MASK)

#         self.viewport.add(self.drawing_area)

#         self.pointer_crosshair = gtk.gdk.Cursor(gtk.gdk.TCROSS)
#         self.drawing_area.window.set_cursor(self.pointer_crosshair)
#         self.drawing_area.show()

        #palette
	gobject.type_register(PyntPaletteView)

        self.vbox_palette = self.mainTree.get_widget("vbox_palette")

        #self.stack.palette = PyntPalette()
        self.paletteview = PyntPaletteView(palette=self.stack.palette)

        self.vbox_palette.pack_start(self.paletteview)
        #self.paletteview.connect("color_changed", self.on_color_changed)
        self.paletteview.connect("fgcolor_picked", self.set_fgcolor)
        self.paletteview.connect("bgcolor_picked", self.set_bgcolor)
        self.paletteview.show()
        self.label_palette = self.mainTree.get_widget("label_palette")

        self.pe_vbox_main = self.peTree.get_widget("pe_vbox_main")
        self.pe_spinbutton_red = self.peTree.get_widget("pe_spinbutton_red")
        self.pe_spinbutton_green = self.peTree.get_widget("pe_spinbutton_green")
        self.pe_spinbutton_blue = self.peTree.get_widget("pe_spinbutton_blue")
        self.pe_toggle_spread = self.peTree.get_widget("pe_toggle_spread")

        self.pe_r_adj = self.pe_spinbutton_red.get_adjustment()
        self.pe_g_adj = self.pe_spinbutton_green.get_adjustment()
        self.pe_b_adj = self.pe_spinbutton_blue.get_adjustment()
        self.pe_hscale_red = self.peTree.get_widget("pe_hscale_red")
        self.pe_hscale_green = self.peTree.get_widget("pe_hscale_green")
        self.pe_hscale_blue = self.peTree.get_widget("pe_hscale_blue")
        self.pe_hscale_red.set_adjustment(self.pe_r_adj)
        self.pe_hscale_green.set_adjustment(self.pe_g_adj)
        self.pe_hscale_blue.set_adjustment(self.pe_b_adj)
        #self.pe_r_adj.set_upper(255)
        #self.pe_r_adj.set_page_size(0)
        #self.pe_r_adj.set_all(value=0, lower=0, upper=255, step_increment=1, page_increment=1, page_size=0)
        #self.pe_g_adj.set_all(value=0, lower=0, upper=255, step_increment=1, page_increment=1, page_size=0)
        #self.pe_b_adj.set_all(value=0, lower=0, upper=255, step_increment=1, page_increment=1, page_size=0)
        self.pe_r_handlerid = self.pe_r_adj.connect("value-changed", self.on_pe_color_edited)
        self.pe_g_handlerid = self.pe_g_adj.connect("value-changed", self.on_pe_color_edited)
        self.pe_b_handlerid = self.pe_b_adj.connect("value-changed", self.on_pe_color_edited)

        self.pe_paletteview = PyntPaletteView(palette=self.stack.palette, columns=16, pages=1)
        #self.pe_paletteview.connect("color_changed", self.on_color_changed)
        self.pe_paletteview.connect("fgcolor_picked", self.set_fgcolor)
        self.pe_paletteview.connect("bgcolor_picked", self.set_bgcolor)



        self.pe_vbox_main.pack_end(self.pe_paletteview)
        self.pe_paletteview.show()
        #self.palette_editor.show()


        # menu
        self.menu_animated = self.mainTree.get_widget("menu_animated")
        self.menu_layer_visible = self.mainTree.get_widget("menu_layer_visible")

        # statusbarv stuff
        self.label_layer = self.mainTree.get_widget("label_layer")
        self.frame_layer = self.mainTree.get_widget("label_frame")
        self.label_coords = self.mainTree.get_widget("label_coords")

        # scrollbars
        #self.scrolling_window = self.mainTree.get_widget("scrolling_window")
        self.hadj = self.scrolledwindow.get_hadjustment()
        self.vadj = self.scrolledwindow.get_vadjustment()
        #self.hadjustment.connect("value_changed", lambda x: self.image_scrolled())
        #self.vadjustment.connect("value_changed", lambda x: self.image_scrolled())

        #self.hadj.set_upper(100)
        #self.hadj.set_page_size(50)
        #self.vadj.set_upper(100)

        self.button_width = self.mainTree.get_widget("button_width")
        #self.button_width.configure(None, 1, 0)
        #self.button_width.set_range(1, 99)

        print "main..."
        self.paper.grab_focus()

        gtk.main()

    def on_brush_solid_color_toggle(self, widget):
        self.paper.brush.solid_color = widget.get_active()

    def set_zoom(self, z):
        #print "set_zoom"
        x, y, tmp = self.drawing_area.window.get_pointer()


        hadj = self.hadjustment.get_value()
        vadj = self.vadjustment.get_value()
        hadj_min, hadj_max, hadj_page = self.hadjustment.get_lower(), \
            self.hadjustment.get_upper(), self.hadjustment.get_page_size()
        vadj_min, vadj_max, vadj_page = self.vadjustment.get_lower(), \
            self.vadjustment.get_upper(), self.vadjustment.get_page_size()
        if x >= 0 and x < self.view.get_xlim() and y >= 0 and y < self.view.get_ylim():
            hmiddle = x
            vmiddle = y
        else:
            hmiddle = hadj+hadj_page/2
            vmiddle = vadj+vadj_page/2

        zo = self.view.zoom

        if self.view.set_zoom(z):
            self.hadjustment.set_value(int(hmiddle*(z/zo)-hadj_page/2))
            self.vadjustment.set_value(int(vmiddle*(z/zo))-vadj_page/2)


    def set_coords(self, widget, coords):
        self.label_coords.set_text("(%d, %d)"%coords)

    def on_menu_paletteeditor(self, widget):
        self.palette_editor = self.peTree.get_widget("palette_editor")
        self.palette_editor.show()

    def on_pe_color_edited(self, widget):
        """
        Update the palette views and palette upon a color edit.
        """

        color = (int(self.pe_r_adj.get_value()), int(self.pe_g_adj.get_value()), int(self.pe_b_adj.get_value()))
        self.stack.palette.set_color(color)
        self.pe_paletteview.color_edited(color)
        #invalidate_color(self.stack.palette.fgcolor)

        self.paletteview.color_edited(color)
        self.stack.set_palette(self.stack.palette.get_pil_palette())

        imcolors = self.stack.get_colors()
        #print "imcolors:", imcolors
        if self.stack.palette.fgcolor in imcolors:
            self.paper.invalidate()

        #imcolors = self.stack.get_colors()
        #print "imcolors:", imcolors
        #if n in imcolors:
        #    self.paper.invalidate()

    def on_pe_button_undo(self, widget):
        print "palette undo"
        self.stack.palette.restore_change()
        self.stack.set_palette(self.stack.palette.get_pil_palette())
        self.pe_paletteview.invalidate_all()
        self.paletteview.invalidate_all()
        self.paper.invalidate()

    def set_fgcolor(self, widget, n):

        if widget == self.paletteview:
            self.pe_paletteview.invalidate_all()
        else:
            if self.pe_toggle_spread.get_active():
                if self.paper.fgcolor != n:
                    self.stack.palette.spread(self.paper.fgcolor, n)
                    self.stack.set_palette(self.stack.palette.get_pil_palette())
                    self.pe_toggle_spread.set_active(False)
                    self.pe_paletteview.invalidate_all()
            self.paletteview.invalidate_all()

        self.paper.fgcolor = n
        r, g, b = self.stack.palette.colors[n]
        self.pe_r_adj.handler_block(self.pe_r_handlerid)
        self.pe_g_adj.handler_block(self.pe_g_handlerid)
        self.pe_b_adj.handler_block(self.pe_b_handlerid)
        self.pe_r_adj.set_value(r)
        self.pe_g_adj.set_value(g)
        self.pe_b_adj.set_value(b)
        self.pe_r_adj.handler_unblock(self.pe_r_handlerid)
        self.pe_g_adj.handler_unblock(self.pe_g_handlerid)
        self.pe_b_adj.handler_unblock(self.pe_b_handlerid)

        print "set_color:", self.stack.palette.get_color(n)
        #self.color = (col.red//255, col.green//255, col.blue//255, 255)


    def set_bgcolor(self, widget, n):
        self.paper.bgcolor = n
        if widget == self.paletteview:
            self.pe_paletteview.invalidate_all()
        else:
            self.paletteview.invalidate_all()


    def palette_prev(self,w):
        print "palette_prev"
        p=self.paletteview.prev_page()
        self.label_palette.set_text(str(p))

    def palette_next(self,w):
        p=self.paletteview.next_page()
        self.label_palette.set_text(str(p))

    def set_width(self, width):
        #print "setting width:", width
        if width > 0:
            self.paper.set_width(width)


    def update_layer_label(self):
        stats = self.stack.get_layer_stats()
        self.label_layer.set_text("%d/%d"%stats)
        self.menu_layer_visible.handler_block_by_func(self.toggle_visible)
        #self.menu_animated.emit_stop_by_name("toggle_animated")
        if self.stack.get_layer().visible:
            self.menu_layer_visible.set_active(True)
        else:
            self.menu_layer_visible.set_active(False)
        self.menu_layer_visible.handler_unblock_by_func(self.toggle_visible)


    def update_frame_label(self):
        stats = self.stack.get_frame_stats()
        self.frame_layer.set_text("%d/%d"%stats)
        self.menu_animated.handler_block_by_func(self.toggle_frame)
        #self.menu_animated.emit_stop_by_name("toggle_animated")
        if self.stack.get_layer().anim:
            self.menu_animated.set_active(True)
        else:
            self.menu_animated.set_active(False)
        self.menu_animated.handler_unblock_by_func(self.toggle_frame)

    def update_window_title(self):
        if self.save_file is "":
            self.mainwindow.set_title("Pynt: <Unsaved>")
        else:
            self.mainwindow.set_title("Pynt: "+self.save_file)

    def toggle_visible(self, widget):
        #print "Visibility:", self.stack.get_layer().visible
        self.stack.get_layer().visible = not self.stack.get_layer().visible
        bbox = self.stack.get_active_bbox()
        self.paper.invalidate_img_bbox(bbox)


    def add_layer(self):
        self.stack.add_layer()
        self.next_layer()
        self.update_layer_label()
        self.update_frame_label()

    def delete_layer(self):
        bbox = self.stack.get_active_bbox()
        self.stack.delete_layer()
        self.update_layer_label()
        self.update_frame_label()
        self.paper.invalidate_img_bbox(bbox)

    def on_join_layers(self, w):
        bbox = self.stack.get_active_bbox()
        if self.stack.join_layers():
            self.update_layer_label()
            self.update_frame_label()
            self.paper.invalidate_img_bbox(bbox)

    def set_busy_pointer(self, state):
        pass

    def on_layer_up(self, w):
        self.stack.move_layer_up()
        self.next_layer()
        bbox = self.stack.get_active_bbox()
        if bbox is not None:
            self.paper.invalidate_bbox(self.paper.get_paper_bbox(bbox))

    def on_layer_down(self, w):
        self.stack.move_layer_down()
        self.prev_layer()
        bbox = self.stack.get_active_bbox()
        if bbox is not None:
            self.paper.invalidate_bbox(self.paper.get_paper_bbox(bbox))


    def toggle_frame(self, widget):
        self.stack.toggle_animated()
        self.update_frame_label()

    def next_layer(self):
        bbox1=self.stack.get_active_bbox()
        if self.stack.next_layer():
            bbox2=self.stack.get_active_bbox()
            combined_bbox = combine_bbox(bbox1, bbox2)
            if combined_bbox is not None:
                self.paper.invalidate_bbox(self.paper.get_paper_bbox(combined_bbox))
            self.update_layer_label()
            self.update_frame_label()

    def prev_layer(self):
        bbox1=self.stack.get_active_bbox()
        if self.stack.prev_layer():
            bbox2=self.stack.get_active_bbox()
            combined_bbox = combine_bbox(bbox1, bbox2)
            if combined_bbox is not None:
                self.paper.invalidate_bbox(self.paper.get_paper_bbox(combined_bbox))
            self.update_layer_label()
            self.update_frame_label()

    def next_frame(self):
        bbox1=self.stack.get_active_bbox()
        if self.stack.next_frame():
            bbox2=self.stack.get_active_bbox()
            combined_bbox = combine_bbox(bbox1, bbox2)
            if combined_bbox is not None:
                self.paper.invalidate_bbox(self.paper.get_paper_bbox(combined_bbox))
        self.update_layer_label()
        self.update_frame_label()

    def prev_frame(self):
        bbox1=self.stack.get_active_bbox()
        if self.stack.prev_frame():
            bbox2=self.stack.get_active_bbox()
            combined_bbox = combine_bbox(bbox1, bbox2)
            if combined_bbox is not None:
                self.paper.invalidate_bbox(self.paper.get_paper_bbox(combined_bbox))
        self.update_layer_label()
        self.update_frame_label()



    def image_scrolled(self):
        self.view.offset=(int(self.hadjustment.get_value()), int(self.vadjustment.get_value()))
        #print "hadj:" ,self.hadjustment.get_value(), self.hadjustment.get_page_size()
        #print "vadj:", self.vadjustment.get_value(), self.vadjustment.get_page_size()


    def set_random_color(self):
        self.color=(random.randint(0,255), random.randint(0,255), random.randint(0,255), 255)

    def set_tool(self, tool):
        print "Setting tool", tool
        if tool != self.paper.tool:
            last_tool_btn = self.mainTree.get_widget("button_"+self.paper.tool)
            last_tool_btn.set_active(False)
            new_tool_btn = self.mainTree.get_widget("button_"+tool)
            #new_tool_btn.set_active(True)
            self.paper.tool = tool
            print self.paper.tool

    # Create a new backing pixmap of the appropriate size
    def configure_event(self, widget, event):

        #print "configure..."
        x, y, width, height = widget.get_allocation()

        #self.view.update(widget.window, self.stack, x, y, width, height)
        #self.view.pixmap.draw_rectangle(widget.get_style().white_gc,
        #                  True, 0, 0, width, height)

        return True

    # Redraw the screen from the backing pixmap
    def expose_event(self, widget, event):
        print "expose..."
        x , y, width, height = event.area
        #print(x , y, width, height)
        #print widget

        self.view.update(widget.window, self.stack, x, y, width, height)
        #widget.window.draw_drawable(widget.get_style().fg_gc[gtk.STATE_NORMAL],
        #                        self.view.pixmap, x, y, x, y, width, height)

        return False

    def on_clear_layer(self, widget):
        bbox = self.stack.clear_layer()
        self.paper.invalidate_img_bbox(bbox)

    # Draw a rectangle on the screen
    def draw_brush(self, widget, brush, color, coords, transient=False):
        z = self.view.zoom
        w, h = brush.size
        print "brush size:", w, h
        if brush.custom_brush:
            tmp = self.stack.draw_brush(brush, None, self.view.get_img_coord(*coords), transient=transient)
        else:
            tmp = self.stack.draw_brush(brush, color, self.view.get_img_coord(*coords), transient=transient)

        #bbox = (coords[0]-w*z//2, coords[1]-h*z//2, coords[0]+w*z//2, coords[1]+h*z//2)
        #if tmp is not None and transient:
        #    oldbbox = self.view.get_canvas_bbox(*tmp)
        #    self.update_view(widget, *oldbbox)
        #    bbox = combine_bbox(oldbbox, bbox)
        self.update_view(widget, tmp)


    def draw_line(self, widget, color, bbox):

        x0, y0, x1, y1 =  bbox
        #print "X:", x1, " Y:", y1
        if x1>0 and y1>0 and x1<self.view.get_xlim() and y1<self.view.get_ylim():
            #print "drawing line:", bbox, color
            startx, starty = self.view.get_img_coord(x0, y0)
            endx, endy = self.view.get_img_coord(x1, y1)
            #self.image.draw_rect((0,0,0,255), startx, starty, endx, endy)
            self.stack.draw_line(color, self.width,
                                 (startx, starty, endx, endy))
            #z=self.view.zoom
            zp = self.view.zoom*self.width
            self.update_view(widget, x0, y0, x1, y1, padding=zp)

    def draw_rect(self, widget, color, xy):
        #print "X:", x, " Y:", y
        x, y = xy
        if x<self.view.get_xlim() and y<self.view.get_ylim():

            startx, starty = self.view.get_img_coord(self.lx, self.ly)
            endx, endy = self.view.get_img_coord(*xy)
            coords = self.stack.draw_rect(color, (startx, starty, endx, endy))
            #self.lx, self.ly += (int(self.scrolling_window.get_hadjustment().get_value()),
            #                    int(self.scrolling_window.get_vadjustment().get_value()))
            #self.lx, self.ly = coords[:2]
            if coords is not None:
                #z=self.view.zoom
                newcoords = self.view.get_canvas_bbox(*coords)
                self.update_view(widget, *newcoords)

    def draw_ellipse(self, widget, color, xy):
        #print "X:", x, " Y:", y
        x, y = xy
        if x<self.view.get_xlim() and y<self.view.get_ylim():

            startx, starty = self.view.get_img_coord(self.lx, self.ly)
            endx, endy = self.view.get_img_coord(*xy)
            coords = self.stack.draw_ellipse(color, (startx, starty, endx, endy))
            #self.lx, self.ly += (int(self.scrolling_window.get_hadjustment().get_value()),
            #                    int(self.scrolling_window.get_vadjustment().get_value()))
            #self.lx, self.ly = coords[:2]
            z=self.view.zoom
            newcoords=self.view.get_canvas_bbox(*coords)
            #self.update_view(widget, coords[0]*z-1, coords[1]*z-1, coords[2]*z+1, coords[3]*z+1)
            self.update_view(widget, *newcoords)

    def get_visible(self):
        x, y = int(self.hadjustment.get_value()), int(self.vadjustment.get_value())
        w, h = self.viewport.size_request()
        return (x, y, x+w, y+h)

    def floodfill(self, widget, color, xy):
        x, y = xy
        if x<self.view.get_xlim() and y<self.view.get_ylim():
            x0y0 = self.view.get_img_coord(*xy)
            self.stack.floodfill(color, x0y0)
            bbox = self.get_visible()
            #self.lx = self.ly = 0
            #print "adjustments:", self.lx, self.ly

            #print "size_request():", w, h

            self.update_view(widget, *bbox)


    def on_undo(self, widget):
        self.paper.on_undo()
        #this may be needed if the operation was a layer op.
        self.update_layer_label()
        self.update_frame_label()


    def on_redo(self, widget):
        self.paper.on_redo()
        #this may be needed if the operation was a layer op.
        self.update_layer_label()
        self.update_frame_label()

    def update_view(self, widget, x0, y0, x1, y1, padding=0):
        print "update_vuew", x0, y0, x1, y1

        if x0 <= x1 and y0 <= y1:
            x, y = x0, y0
            w, h = x1-x0, y1-y0
        elif x0 > x1 and y0 <= y1:
            x, y = x1-1, y0
            w, h = x0-x, y1-y0
        elif x0 <= x1 and y0 > y1:
            x, y = x0, y1-1
            w, h = x1-x, y0-y
        elif x0 > x1 and y0 > y1:
            x, y = x1-1, y1-1
            w, h = x0-x, y0-y

        p=padding
        self.view.update(self.drawing_area.window, self.stack, x-p, y-p, w+2*p, h+2*p)
        #self.drawing_area.queue_draw_area(x-p, y-p, w+2*p, h+2*p)

    def sb_push(self, message):
        pass

    def on_save_image(self, widget):
        """Save current image as a Pynt file (pickled python object)"""
        if self.save_file is "":
            self.on_save_image_as(widget)
        else:
            pyntdata = PyntData(self.stack)
            pyntdata.save(self.save_file)

    def on_save_brush(self, widget):
        """Save current image as a Pynt file (pickled python object)"""
        if self.save_file is "":
            self.on_save_image_as(widget)
        else:
            pyntdata = PyntData(self.stack)
            pyntdata.save(self.save_file)


    def on_save_image_as(self, widget):
        """Save current image as a Pynt file (pickled python object)"""
        filedir, filename = os.path.split(self.save_file)
        save_file = file_browse(gtk.FILE_CHOOSER_ACTION_SAVE, file_dir=filedir,
                                file_name=filename, file_ext="pynt")
        if save_file != "":
            if not save_file.endswith(".pynt"):
                save_file += ".pynt"
            pyntdata = PyntData(self.stack)
            pyntdata.save(save_file)

            self.save_file = save_file
            self.update_window_title()

    def on_export_brush(self, widget):
        """Export image as a palette based PNG (layers are merged in the image)"""
        filedir, filename = os.path.split(self.brush_file)
        filename = os.path.splitext(filename)[0] + ".png"
        brush_file = file_browse(gtk.FILE_CHOOSER_ACTION_SAVE, file_dir=filedir,
                                file_name=filename, file_ext="png")
        if brush_file != "":
            path, extension = os.path.splitext(brush_file)
            if extension == "":
                brush_file = path + ".png"
            #img = self.stack.get_area(*((0, 0) + self.stack.resolution))
            img = self.paper.brush.data
            img.save(brush_file, "PNG", transparency=0)
            self.brush_file = brush_file

    def on_load_image(self, widget):
        """Load a Pynt image file"""
        filedir, filename = os.path.split(self.save_file)
        load_file = file_browse(gtk.FILE_CHOOSER_ACTION_OPEN, file_dir=filedir,
                                file_name=filename, file_ext="pynt")
        if load_file != "":
            f = open(load_file, "r")
            self.save_file = load_file
            pyntdata = cPickle.load(f)

            self.stack = PyntStack(data=pyntdata)


            self.paletteview.palette = self.pe_paletteview.palette = self.stack.palette
            self.paletteview.invalidate_all()
            self.pe_paletteview.invalidate_all()
            self.paper.stack = self.stack

            self.paper.invalidate()

            self.update_frame_label()
            self.update_layer_label()
            self.update_window_title()

            f.close()


    def on_export_image(self, widget):
        """Export image as a palette based PNG (layers are merged in the image)"""
        filedir, filename = os.path.split(self.save_file)
        filename = os.path.splitext(filename)[0] + ".png"
        save_file = file_browse(gtk.FILE_CHOOSER_ACTION_SAVE, file_dir=filedir,
                                file_name=filename, file_ext="png")
        if save_file != "":
            path, extension = os.path.splitext(save_file)
            if extension == "":
                save_file = path + ".png"
            img = self.stack.get_area(*((0, 0) + self.stack.resolution))
            img.save(save_file, "PNG")


    def on_import_image(self, widget):
        """Load an image file into Pynt (replaces current image)
           Currently must be a palette based file (e.g. GIF or palette PNG)"""
        filedir, filename = os.path.split(self.save_file)
        load_file = file_browse(gtk.FILE_CHOOSER_ACTION_OPEN, file_dir=filedir,
                                file_name="", file_ext="png")
        if load_file != "":
            img = Image.open(load_file)

            if img.mode != "P":
                # Convert to "optimal" 256 color palette
                img = img.convert("P", palette=Image.ADAPTIVE, colors=256)

            lut = img.resize((256, 1))
            lut.putdata(range(256))
            lut = list(lut.convert("RGB").getdata())

            print "Image size:", img.size

            self.stack = PyntStack(resolution=img.size, data = img)
            self.stack.set_palette(lut)
            self.stack.palette.set_colors(lut)
            self.paletteview.palette = self.pe_paletteview.palette = self.stack.palette
            self.paletteview.invalidate_all()
            self.pe_paletteview.invalidate_all()

            self.paper.stack = self.stack
            self.paper.invalidate()

            self.update_frame_label()
            self.update_layer_label()


    def button_press_event(self, widget, event):
        print "button pressed..."
        if (event.button == 1 or event.button == 3) and self.view.pixmap != None and self.stack.mode is None:
            #self.stack.clear_scratch()
            bbox = self.stack.erase_last_brush(self.brush)
            if bbox is not None:
                self.update_view(widget, *self.view.get_canvas_bbox(*bbox))
            if event.button == 1:
                self.stack.mode = "draw"
            elif event.button == 3:
                self.stack.mode = "erase"
            self.lx = int(event.x)
            self.ly = int(event.y)

            if self.tool == "pencil":
                self.draw_brush(widget, self.brush, self.stack.palette.fgcolor, (self.lx, self.ly))
            elif self.tool == "points":
                self.draw_brush(widget, self.brush, self.stack.palette.fgcolor, (self.lx, self.ly), transient=True)
            return True

    def button_release_event(self, widget, event):
        #print "button reelased"

        if self.tool == "floodfill":
            color=self.stack.palette.get_index()
            #if self.stack.mode=="erase":
                #pos = self.view.get_img_coord(self.lx, self.ly)
                #color=self.stack.get_pixel(pos)
                #FIX! Can't fill with same color... this will lead to strange bugs
                #color=(255-color[0], 255-color[1], 255-color[2])

            self.floodfill(widget, color, (self.lx, self.ly))

        if self.tool == "brush":
            #print "Getting new brush..."
            bbox = (self.lx, self.ly, int(event.x), int(event.y))
            tmp = self.stack.get_layer().image.crop(self.view.get_img_bbox(*bbox))
            self.brush = PyntBrush(data=tmp, transp_color=self.stack.get_layer().image.transp_color)

            #self.custom_brush = True
            self.stack.clear_scratch()

            self.update_view(widget, *bbox)
            self.set_tool("points")

        if self.tool == "rectangle":
            self.stack.last_rect_bbox = None
            bbox=self.stack.apply_scratch()
            self.stack.clear_scratch()

        else:
            bbox=self.stack.apply_scratch()
            self.stack.clear_scratch()

        self.stack.mode = None


    def leave_notify_event(self, widget, event):
        bbox = self.label_coords.set_text("(-, -)")
        if self.stack.mode is None:
            bbox = self.stack.clear_scratch()
            if bbox is not None:

                #coords = self.view.get_img_coord(int(event.x),int(event.y))
                bbox = self.view.get_canvas_bbox(*bbox)
                self.update_view(widget, *bbox)
        else:
            if self.tool in ("pencil", "points"):
                self.lx = self.ly = None

    def motion_notify_event(self, widget, event):
        #if event.is_hint:
        #    x, y, state = event.window.get_pointer()
        #else:
        x = int(event.x)
        y = int(event.y)
        state = event.state
        #self.stack.mode = None

        #if state & gtk.gdk.BUTTON1_MASK:
        #    self.stack.mode = "draw"

        #elif state & gtk.gdk.BUTTON3_MASK:
        #    print "button 3!"
        #    self.stack.mode = "erase"

        if self.lx is None or self.ly is None:
            self.lx = x
            self.ly = y

            print "motion...", x,y

        elif True: #x != self.lx and y != self.ly:

            print "motion...", x,y
            if all((self.view.pixmap != None, x>0, y>0, x < self.view.get_xlim(), y < self.view.get_ylim())):
                coords = self.view.get_img_coord(x,y)
                lcoords = self.view.get_img_coord(self.lx, self.ly)
                if self.stack.mode is None:
                    self.label_coords.set_text("(%d, %d)"%coords)
                    if self.tool in ("points", "pencil", "line"):
                        self.draw_brush(widget, self.brush, self.stack.palette.fgcolor,
                                        (x, y), transient=True)
                    self.lx, self.ly = x, y
                else:
                    if self.tool == "points":
                        self.draw_brush(widget, self.brush, self.stack.palette.fgcolor, (x, y))
                        self.label_coords.set_text("(%d, %d)"%coords)

                    elif self.tool == "pencil":
                        lx, ly = self.lx, self.ly
                        self.lx, self.ly = x, y

                        self.draw_line(self.drawing_area, self.stack.palette.fgcolor, (lx, ly, x, y))
                        self.draw_brush(widget, self.brush, self.palette.fgcolor, (x, y))
                        self.label_coords.set_text("(%d, %d)"%coords)

                    elif self.tool in ("rectangle", "brush"):
                        self.draw_rect(widget, self.palette.fgcolor, (x, y))
                        self.label_coords.set_text("(%d, %d)"%(coords[0]-lcoords[0], coords[1]-lcoords[1]))

                    elif self.tool == "ellipse":
                        self.draw_ellipse(widget, self.palette.fgcolor, (x, y))
                        self.label_coords.set_text("(%d, %d)"%(coords[0]-lcoords[0], coords[1]-lcoords[1]))

                    elif self.tool == "line":
                        bbox = self.stack.clear_scratch()
                        if bbox is not None:
                            bbox = self.view.get_canvas_bbox(*bbox)
                            self.update_view(widget, *bbox)
                            self.draw_line(widget, self.palette.fgcolor, (self.lx, self.lx, x, y))
                            self.label_coords.set_text("%d"%(math.sqrt((coords[0]-lcoords[0])**2 + (coords[1]-lcoords[1])**2)))

                return True


if __name__ == "__main__":
    pp = PyntMain()

