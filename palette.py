#!/usr/bin/env python


"""
StarHScale a Horizontal slider that uses stars
Copyright (C) 2006 Mark Mruss <selsine@gmail.com>

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

If you find any bugs or have any suggestions email: selsine@gmail.coim
"""

from __future__ import division 

try:
        import gtk
        import gobject
        from gtk import gdk
except:
        raise SystemExit

import copy

import pygtk
if gtk.pygtk_version < (2, 0):
        print "PyGtk 2.0 or later required for this widget"
        raise SystemExit


class PyntPaletteChange(object):
        def __init__(self, colors):
                self.colors = colors


class PyntPalette(object):
        def __init__(self, colors=None, fgcolor=1, bgcolor=0):
                self.colors = colors  #a list of 256 (R,G,B) tuples
                self.fgcolor = fgcolor
                self.bgcolor = bgcolor
                self.changes = []

                if colors is None:
                        self.colors = [
                                (255,255,255),
                                (0,0,0),
                                (255,0,0),
                                (0,255,0),
                                (0,0,255),
                                (255,255,0),
                                (0,255,255),
                                (255,0,255),
                                
                                (33,33,33),
                                (66,66,66),
                                (99,99,99),
                                (133,133,133),
                                (166,166,166),
                                (200,200,200),
                                (233,233,233),
                                (0,0,0),
                                ]*16
                else:
                        self.colors = colors

        def store_change(self):
                print "storing..."
                self.changes.append(PyntPaletteChange(copy.copy(self.colors)))
                if len(self.changes) > 10:
                        del(self.changes[0])

        def restore_change(self):
                print "restoring..."
                if len(self.changes) > 0:
                        change = self.changes.pop()
                        self.colors = change.colors

        def set_color(self, color, n=None):
                if n is None:
                        n = self.fgcolor
                self.colors[n] = color

        def set_colors(self, colors):
                self.store_change()
                self.colors = colors

        def get_fgcolor(self):
                return self.fgcolor

        def get_pil_palette(self):
                return reduce(lambda x, y: x+y, self.colors)

        def get_color(self, n=None):
                if n is None:
                        c=self.colors[self.fgcolor]
                else:
                        c=self.colors[n]
                return (c[0], c[1], c[2], 255)

        def spread(self, n0, n1):
                self.store_change()
                c0 = self.colors[n0]
                c1 = self.colors[n1]
                n = n1-n0
                step = ((c1[0]-c0[0])/n, (c1[1]-c0[1])/n, (c1[2]-c0[2])/n)
                if n0 < n1:
                        for i in range(1, n):
                                self.colors[n0+i] = (int(round(c0[0]+i*step[0])), 
                                                     int(round(c0[1]+i*step[1])), 
                                                     int(round(c0[2]+i*step[2])))
                else:
                        for i in range(-1, n, -1):
                                self.colors[n0+i] = (int(round(c0[0]+i*step[0])), 
                                                     int(round(c0[1]+i*step[1])), 
                                                     int(round(c0[2]+i*step[2])))

                

class PyntPaletteView(gtk.DrawingArea):
	"""A horizontal Scale Widget that attempts to mimic the star
	rating scheme used in iTunes"""

        __gsignals__ = {
                "color-changed": (
                        gobject.SIGNAL_RUN_LAST,
                        gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
                "fgcolor-picked": (
                        gobject.SIGNAL_RUN_LAST,
                        gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),                       
                "bgcolor-picked": (
                        gobject.SIGNAL_RUN_LAST,
                        gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),                        
                }
        
	
	def __init__(self, colors=256, columns=4, pages=4, palette=None):
		"""Initialization, numstars is the total number
		of stars that may be visible, and stars is the current
		number of stars to draw"""
		
		#Initialize the Widget
		super(PyntPaletteView, self).__init__()

                self.columns = columns
                self.pages = pages
                self.page = 0
		# Init the list to blank
                if palette is None:
                        self.palette = PyntPalette()
                else:
                        self.palette = palette

        def next_page(self):
                if self.page < 3:
                        self.page += 1
                        self.invalidate_all()
                return self.page+1

        def prev_page(self):
                if self.page > 0:
                        self.page -= 1
                        self.invalidate_all()
                return self.page+1
                
        def color_edited(self, color):
                n = self.palette.fgcolor
                print "palette: color edited:", color, n
                #self.palette.set_color(color, n)
                self.invalidate_color(n)
                #self.emit("color_changed", n)
                 

	def do_realize(self):
		"""Called when the widget should create all of its 
		windowing resources.  We will create our gtk.gdk.Window
		and load our star pixmap."""
		

                #print "REALIZED palette"
		# First set an internal flag showing that we're realized

		self.set_flags(self.flags() | gtk.REALIZED)
		
		# Create a new gdk.Window which we can draw on.
		# Also say that we want to receive exposure events 
		# and button click and button press events

		self.window = gtk.gdk.Window(
			self.get_parent_window(),
			width=self.allocation.width,
			height=self.allocation.height,
			window_type=gdk.WINDOW_CHILD,
			wclass=gdk.INPUT_OUTPUT,
			event_mask=self.get_events() | gtk.gdk.EXPOSURE_MASK | gtk.gdk.CONFIGURE
				| gtk.gdk.BUTTON1_MOTION_MASK | gtk.gdk.BUTTON_PRESS_MASK
				| gtk.gdk.POINTER_MOTION_MASK
				| gtk.gdk.POINTER_MOTION_HINT_MASK)
				
		# Associate the gdk.Window with ourselves, Gtk+ needs a reference
		# between the widget and the gdk window
		self.window.set_user_data(self)
		
		# Attach the style to the gdk.Window, a style contains colors and
		# GC contextes used for drawing
		self.style.attach(self.window)
		
		# The default color of the background should be what
		# the style (theme engine) tells us.
		self.style.set_background(self.window, gtk.STATE_NORMAL)
		self.window.move_resize(*self.allocation)
                self.gc = self.style.fg_gc[gtk.STATE_NORMAL]
        
		#self.gc = self.window.new_gc()
                
		# load the star xpm
                """
		self.pixmap = gtk.gdk.Pixmap(self.window, self.allocation.width,
                                             self.allocation.height, 24)
		"""	
		# self.style is a gtk.Style object, self.style.fg_gc is
		# an array or graphic contexts used for drawing the forground
		# colours	

		#self.connect("expose_event", self.do_expose_event)		
		#self.connect("motion_notify_event", self.motion_notify_event)

		
	def do_unrealize(self):
		# The do_unrealized method is responsible for freeing the GDK resources
		# De-associate the window we created in do_realize with ourselves
		self.window.destroy()
		
	def do_size_request(self, requisition):
		"""From Widget.py: The do_size_request method Gtk+ is calling
		 on a widget to ask it the widget how large it wishes to be. 
		 It's not guaranteed that gtk+ will actually give this size 
		 to the widget.  So we will send gtk+ the size needed for
		 the maximum amount of stars"""
		
		requisition.height = -1 #10*self.columns
		requisition.width = -1 #20 * (len(self.colors) // self.columns)
	
	
	def do_size_allocate(self, allocation):
		"""The do_size_allocate is called by when the actual 
		size is known and the widget is told how much space 
		could actually be allocated Save the allocated space
		self.allocation = allocation. The following code is
		identical to the widget.py example"""
	
		if self.flags() & gtk.REALIZED:
			self.window.move_resize(*allocation)
		
	def do_expose_event(self, event):
		"""This is where the widget must draw itself."""
		print "Drawing palettwe!!!"

                wtot, htot = self.window.get_size()

                #self.window.freeze_updates()

                #self.window.thaw_updates()

                pagesize = 256 // self.pages

                print "wtot, htot:", wtot, htot
                rows = (256//self.pages)//self.columns
                cols = self.columns
                w = (wtot-2)//cols
                h = (htot-2)//rows
                offset = pagesize * self.page
                pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, w, h)
		self.window.begin_paint_rect((0,0,wtot, htot))

                # draw the color "swatches"
                for col in range(0,self.columns):
                        for row in range(0, pagesize//self.columns):

                                n = offset+col*pagesize//self.columns+row
                                color = self.palette.get_color(n)
                                pixbuf.fill(int("0x%02x%02x%02xff"%(color[0],color[1],color[2]), 16))
                                #pixbuf.render_to_drawable(self.window, self.gc, 0, 0, 1+col*w, 1+row*h, w, h) 
                                self.window.draw_pixbuf(self.gc, pixbuf, 0, 0, 1+col*w, 1+row*h, w, h) 
                                #if n == self.selected:
                                #        self.window.draw_rectangle(self.gc, False, col*w, row*h, w+1, h+1)
                # draw the rectangle marking the selected foreground color
                c = self.palette.fgcolor
                white = self.window.get_colormap().alloc_color(gtk.gdk.Color(red=65535, green=65535, blue=65535))
                black = self.window.get_colormap().alloc_color(gtk.gdk.Color(red=0, green=0, blue=0))
                if c >= offset and c < offset+pagesize:
                        #self.gc.set_fill(gtk.gdk.STIPPLED)

                        self.gc.set_background(white)
                        self.gc.set_line_attributes(2, gtk.gdk.LINE_DOUBLE_DASH, gtk.gdk.CAP_BUTT, gtk.gdk.JOIN_MITER)

                        self.window.draw_rectangle(self.gc, False, 
                                                   1+((c-offset)//rows)*w, 
                                                   1+((c-offset)%rows)*h, w, h)
                        self.gc.set_line_attributes(1, gtk.gdk.LINE_SOLID, gtk.gdk.CAP_BUTT, gtk.gdk.JOIN_MITER) 
                 
                # draw the rectangle marking the selected background color
                c = self.palette.bgcolor
                if c >= offset and c < offset+pagesize:
                        #self.gc.set_fill(gtk.gdk.STIPPLED)
                        self.gc.set_line_attributes(1, gtk.gdk.LINE_SOLID, gtk.gdk.CAP_BUTT, gtk.gdk.JOIN_MITER)
                        self.gc.set_foreground(white)
                        self.window.draw_rectangle(self.gc, False, 
                                                   ((c-offset)//rows)*w, 
                                                   ((c-offset)%rows)*h, w, h)

                        self.gc.set_foreground(black)
                        self.window.draw_rectangle(self.gc, False, 
                                                   1+((c-offset)//rows)*w, 
                                                   1+((c-offset)%rows)*h, w, h)
                        self.gc.set_line_attributes(1, gtk.gdk.LINE_SOLID, gtk.gdk.CAP_BUTT, gtk.gdk.JOIN_MITER) 
                 
                self.window.end_paint()
                


	def motion_notify_event(self, widget, event):
		# if this is a hint, then let's get all the necessary 
		# information, if not it's all we need.
		if event.is_hint:
			x, y, state = event.window.get_pointer()
		else:
			x = event.x
			y = event.y
			state = event.state
		print "palette motion"
		#new_stars = 0
		#if (state & gtk.gdk.BUTTON1_MASK):
			# loop through the sizes and see if the
			# number of stars should change
		#	self.check_for_new_stars(event.x)	
			
        def invalidate_color(self, n):
                if self.window is not None:
                        print "invalidating", n
                        offset = (256 // self.pages) * self.page
                        if n >= offset and n <= offset+256//self.pages:
                                wtot, htot = self.window.get_size()
                                rows = (256//self.pages)//self.columns
                                cols = self.columns
                                w = (wtot-1)//cols
                                h = (htot-1)//rows
                                row = (n-offset)%rows
                                col = (n-offset)//rows
                                self.window.invalidate_rect((col*w, row*h ,w+2, h+2), False)
                                print "updating ciolor:", n, col*w, row*h
                        else:
                                print "color is off screen"

        def invalidate_all(self):
                if self.window is not None:
                        wtot, htot = self.window.get_size()
                        self.window.invalidate_rect((0, 0, wtot, htot), False)
        
	def do_button_press_event(self, event):
		"""The button press event virtual method"""
				
                wtot, htot = self.window.get_size()
                print "wtot, htot:", wtot, htot
                rows = (256//self.pages)//self.columns
                cols = self.columns
                w = (wtot-2)//cols
                h = (htot-2)//rows

		# make sure it was the first button
                column = int(event.x)//w
                row = int(event.y)//h
                oldcol = self.palette.fgcolor // rows
                oldrow = self.palette.fgcolor % rows
                offset = (256//self.pages) * self.page
                n = column * (256//self.pages)//self.columns + row + offset

                if all((event.x > 1, event.x < wtot-1, event.y > 1, event.y < htot-1)):
                        if event.button == 1:
                                #print "old selection:", oldcol, oldrow

                                self.invalidate_color(self.palette.fgcolor)
                                self.palette.fgcolor = n
                                self.invalidate_color(n)

                                self.emit("fgcolor_picked", n)
                        if event.button == 3:
                                #print "old selection:", oldcol, oldrow
                                self.invalidate_color(self.palette.bgcolor)
                                self.palette.bgcolor = n
                                print "bgcolor:", self.palette.bgcolor
                                self.invalidate_color(n)

                                self.emit("bgcolor_picked", n)

                        return True
		
	def check_for_new_stars(self, xPos):
		"""This function will determin how many stars
		will be show based on an x coordinate. If the
		number of stars changes the widget will be invalidated
		and the new number drawn"""
		
		# loop through the sizes and see if the
		# number of stars should change
		new_stars = 0
		for size in self.sizes:
			if (xPos < size):
				# we've reached the star number
				break
			new_stars = new_stars + 1
			
		#set the new value
		self.set_value(new_stars)
			
	def set_value(self, value):
		"""Sets the current number of stars that will be 
		drawn.  If the number is different then the current
		number the widget will be redrawn"""
		
                pass
                """
		if (value >= 0):
			if (self.stars != value):
				self.stars = value
				#check for the maximum
				if (self.stars > self.max_stars):
					self.stars = self.max_stars
				# redraw the widget
				self.window.invalidate_rect(self.allocation,True)
		"""
	
	def get_value(self):
		"""Get the current foreground and background colors"""
		
		return (self.palette.fgcolor, self.palette.bgcolor)
        
        """
	def set_max_value(self, max_value):
		
		if (self.max_stars != max_value):
			
			if (max_value > 0):
				self.max_stars = max_value
				#reinit the sizes list (should really be a sperate function
				self.sizes = []		
				for count in range(0,self.max_stars):
					self.sizes.append((count * PIXMAP_SIZE) + BORDER_WIDTH)

				if (self.stars > self.max_stars):
					self.set_value(self.max_stars)
	
	def get_max_value(self):

		
		return self.max_stars
	"""
	
if __name__ == "__main__":
	# register the class as a Gtk widget
	gobject.type_register(PyntPaletteView)
	
	win = gtk.Window()
	win.resize(200,50)
	win.connect('delete-event', gtk.main_quit)
	
	pal = PyntPaletteView()
	win.add(pal)
	
	win.show_all()    
	gtk.main()
	
