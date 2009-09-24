
from __future__ import division

try:
    import gtk
    import gobject
    from gtk import gdk
except:
    raise SystemExit

from gtk.gdk import CONTROL_MASK, SHIFT_MASK, BUTTON1_MASK, BUTTON2_MASK, BUTTON3_MASK

if gtk.pygtk_version < (2, 0):
    print "PyGtk 2.0 or later required for this widget"
    raise SystemExit

import Image

from image import PyntImage, PyntBrush, PyntImagePalette
from utils import make_bbox, combine_bbox, enable_devices, get_pressure

class PyntPaper(gtk.DrawingArea):
    __gsignals__ = {
       "set-scroll-adjustments": (
            gobject.SIGNAL_RUN_LAST,
            gobject.TYPE_NONE, (gtk.Adjustment, gtk.Adjustment)),
       "coords-changed": (
            gobject.SIGNAL_RUN_LAST,
            gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
       "fgcolor-picked": (
            gobject.SIGNAL_RUN_LAST,
            gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),                       
       "bgcolor-picked": (
            gobject.SIGNAL_RUN_LAST,
            gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),                        
       "set-tool": (
            gobject.SIGNAL_RUN_LAST,
            gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),                        
       }

    def __init__(self, stack):
        super(PyntPaper, self).__init__()
        
        self.stack = stack
        self.zoom = 1

        self.tool = "pencil"
        self.line_width = 1
        self.brush = PyntBrush()

        self.dx = self.dy = 0          #scrollbar offsets
        self.lx = self.ly = 0       #last mouse point (for drawing)

        self.selection = None

        #self.keys_pressed = []

        #this is needed to make PyntPaper aware of the scrollbars
        self.set_set_scroll_adjustments_signal("set-scroll-adjustments")        

# --- GUI callbacks ---

    def do_realize(self):
        print "realize!"

        self.set_flags(self.flags() | gtk.REALIZED)

        self.window = gtk.gdk.Window(
            self.get_parent_window(),
            width=self.allocation.width,
            height=self.allocation.height,
            window_type=gdk.WINDOW_CHILD,
            wclass=gdk.INPUT_OUTPUT,
            event_mask = self.get_events() | gtk.gdk.BUTTON_MOTION_MASK 
                        | gtk.gdk.EXPOSURE_MASK | gtk.gdk.CONFIGURE
                        | gtk.gdk.BUTTON1_MOTION_MASK | gtk.gdk.BUTTON_PRESS_MASK
                        | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.POINTER_MOTION_MASK
                        | gtk.gdk.POINTER_MOTION_HINT_MASK | gtk.gdk.LEAVE_NOTIFY_MASK
                        | gtk.gdk.KEY_PRESS | gtk.gdk.KEY_RELEASE) 

        self.set_flags(gtk.CAN_FOCUS)
        self.set_extension_events(gtk.gdk.EXTENSION_EVENTS_CURSOR)  #for pressure

        self.window.set_user_data(self)
        self.style.attach(self.window)
        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.window.move_resize(*self.allocation)
        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]
        
        #self.connect("key_press_event", self.do_key_press_event)
        #self.connect("key_press_event", self.do_key_press_event)
        w, h = self.window.get_size()
        #w, h = 100,100
        #print "paper w, h:", w, h
        
        self.pixmap = gtk.gdk.Pixmap(None, w, h, 24)
        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]
        enable_devices()

    def do_unrealize(self):
        # The do_unrealized method is responsible for freeing the GDK resources
        # De-associate the window we created in do_realize with ourselves
        self.window.destroy()
		
    def do_size_request(self, requisition):
        requisition.height = -1 #10*self.columns
        requisition.width = -1 #20 * (len(self.colors) // self.columns)	
	
    def do_size_allocate(self, allocation):
        self.allocation=allocation

        if self.flags() & gtk.REALIZED:
            self.window.move_resize(*allocation)
        #print "resizing:", allocation.width, allocation.height
        self.pixmap = gtk.gdk.Pixmap(None, allocation.width, allocation.height, 24)

        self.set_zoom(self.zoom)

    def do_expose_event(self, e):

        z = self.zoom

        x, y, w, h = e.area

        #print "expose!", "x0:", x0, "y0:", y0, "x1:", x1, "y1:", y1
        #print "expose!", "x:", x, "y:", y, "w:", w, "h:", h

        self.update_pixmap((x, y, x+(w//z+1)*z, y+(h//z+1)*z))
        self.window.begin_paint_rect((x,y,w,h))
        self.window.draw_drawable(self.gc, self.pixmap, x, y, x, y, w, h)      

        self.window.end_paint()
 

    def do_configure_event(self, w, e):
        print "configure!"

    def do_set_scroll_adjustments(self, hadj, vadj):
        """Connect us to the scrollbars of the container..."""
        hadj.connect("value-changed", self.on_scroll_value_changed)
        self._hadj = hadj
        vadj.connect("value-changed", self.on_scroll_value_changed)
        self._vadj = vadj


    def on_scroll_value_changed(self, e):
        """Called whenever a scrollbar is moved by the user."""
        #print "scrolled!", self._hadj.get_value(), self._vadj.get_value()
        w, h = self.window.get_size()
        #self.update_pixmap((0, 0, w, h))
        x, y = int(round(self._hadj.value)), int(round(self._vadj.value))
        wmax, hmax = int(round(self._hadj.upper)), int(round(self._vadj.upper))
        w, h = int(round(self._hadj.page_size)), int(round(self._vadj.page_size))
        dx = (x//self.zoom)*self.zoom
        dy = (y//self.zoom)*self.zoom

        #--z = self.zoom
        #region = gtk.gdk.region_rectangle((0,0,w//z*z,h//z*z))



        #self.window.move_region(region, ((self.dx-dx)//z)*z, ((self.dy-dy)//z)*z)
        #sx, sy = self.dx-dx, self.dy-dy
        
        
        #if sx > 0:
        #    self.invalidate_bbox((0,0,sx,h))
        #elif sx < 0:
        #    self.invalidate_bbox((w+sx-z,0,w,h))
    
        #if sy > 0:
        #    self.invalidate_bbox((0,0,w,sy))
        #elif sy < 0:
        #    self.invalidate_bbox((0,h+sy-z,w,h))

        

#         if x == 0 and w < wmax:
#             self.dx = -(wmax-w)//2
#         else:
#             self.dx = (x//self.zoom)*self.zoom
#         if y == 0 and h < hmax:
#             self.dy = -(hmax-h)//2
#         else:
#             self.dy = (y//self.zoom)*self.zoom

 

        self.stack.clear_scratch()
        self.window.invalidate_rect((0, 0, w, h), False)
        #print "dx, dy:", self.dx, self.dy
        self.dx, self.dy = dx, dy


 
#    def do_key_press_event(self, e):
#        self.keys_pressed.append(gtk.gdk.keyval_name(e.keyval))
#        print "keys_pressed:", self.keys_pressed

#    def do_key_release_event(self, e):
#        key = gtk.gdk.keyval_name(e.keyval)
#        if key in self.keys_pressed:
#            self.keys_pressed.remove(key)
#            print "keys_pressed:", self.keys_pressed

    def do_motion_notify_event(self, e, f=None):
        x, y = int(e.x), int(e.y)
        xi, yi = self.get_img_coord(x, y)
        if (xi, yi) == self.get_img_coord(self.lx, self.ly):
                #print "no movement"
                return None
        #a, b, state = e.window.get_pointer()
        #if all((xi >= 0, xi < self.stack.resolution[0], y >= 0, y < self.stack.resolution[1])):
        #print "Movement"

        
        draw = False
        #if self.stack.mode in ("draw_fg", "erase"):
        if e.state & BUTTON2_MASK or e.device.source == gtk.gdk.SOURCE_ERASER:
                sx = self.lx - x
                sy = self.ly - y
                w, h = self.window.get_size()
                
                self.window.freeze_updates()
                self._hadj.value = max(0, min(self.get_xlim()-w, 
                                              self._hadj.value + sx))
                self._vadj.value = max(0, min(self.get_ylim()-h, 
                                              self._vadj.value + sy))
                self.window.thaw_updates()
                self.lx = x
                self.ly = y     

        elif e.state & BUTTON1_MASK:
            draw=True
            color = self.stack.palette.fgcolor
        elif e.state & BUTTON3_MASK:
            draw=True
            if self.stack.palette.bgcolor == 0:
                color = 1
            else:
                color = self.stack.palette.bgcolor
        else:
            self.draw_brush(self.brush, self.stack.palette.fgcolor, 
                            (x, y), transient=True)
            self.emit("coords-changed", self.get_img_coord(x, y)) 
            self.lx, self.ly = x, y                
   
        filled = e.state & SHIFT_MASK

        if draw:
                if self.tool == "pencil":
                    #if self.lx is not None and self.ly is not None:
                    p = get_pressure(e)
                    if type(p) == float:
                        self.draw_line(color, 1+p*self.line_width, (self.lx, self.ly, x, y))
                    else:
                        self.draw_line(color, self.line_width, (self.lx, self.ly, x, y))
                    #self.draw_brush(self.brush, color, (x, y), update=False)
                    self.lx, self.ly = x, y
                    self.emit("coords-changed", self.get_img_coord(x, y)) 
                elif self.tool == "points":
                    self.draw_brush(self.brush, color, (x, y), transient=False)
                    self.emit("coords-changed", self.get_img_coord(x, y)) 
                elif self.tool in ("line"):
                    self.draw_line(color, self.line_width, (self.lx, self.ly, x, y), 
                                   transient=True)
                    new = self.get_img_coord(x, y)
                    old = self.get_img_coord(self.lx, self.ly)
                    self.emit("coords-changed", (new[0]-old[0]+1, new[1]-old[1]+1))  
                elif self.tool in ("rectangle", "brush"):
                    self.draw_rectangle(color, (self.lx, self.ly, x-self.lx, y-self.ly), 
                                        transient=True, filled=filled)
                    new = self.get_img_coord(x, y)
                    old = self.get_img_coord(self.lx, self.ly)
                    self.emit("coords-changed", (new[0]-old[0]+1, new[1]-old[1]+1)) 
                elif self.tool == "ellipse":
                    self.draw_ellipse(color, (self.lx, self.ly, x-self.lx, y-self.ly), 
                                      transient=True, filled=filled)
                    new = self.get_img_coord(x, y)
                    old = self.get_img_coord(self.lx, self.ly)
                    self.emit("coords-changed", (new[0]-old[0]+1, new[1]-old[1]+1)) 
                

    def do_leave_notify_event(self, event):
        """Why does this get called on mouse clicks? I sure amn't doing it..."""
        w, h = self.window.get_size()
        w = min(w, self.stack.resolution[0]*self.zoom)
        h = min(h, self.stack.resolution[1]*self.zoom)
        if not 0<=event.x<w or not 0<=event.y<h:
            self.emit("coords-changed", (-1, -1)) 
            print "outside!"
            if self.stack.mode is None:
                bbox = self.stack.clear_scratch()
                if bbox is not None:
                    self.invalidate_img_bbox(bbox)
            #else:
                #if self.tool in ("pencil", "points"):
                    #self.lx = self.ly = None

                
    def do_button_press_event(self, e):
        print "button press!", e.button
        self.grab_focus()
        #self.stack.draw_line(1, 1, (e.x, e.y, e.x+1, e.y+1))
        self.lx = int(e.x)
        self.ly = int(e.y)
        if e.button == 1:
            if self.tool == "colorpicker":
                self.pick_fgcolor((self.lx, self.ly))
            elif self.stack.mode is None:
                self.stack.mode="draw_fg"
        elif e.button == 3:
            if self.tool == "colorpicker":
                self.pick_bgcolor((self.lx, self.ly))
            elif self.stack.palette.bgcolor == 0:
                self.stack.mode="erase"
            elif self.stack.mode is None:
                self.stack.mode="draw_bg"
        elif e.button == 4:
            self.set_zoom(self.zoom-1)
        elif e.button == 5:
            self.set_zoom(self.zoom+1)
        self.stack.last_brush_bbox = None


    def do_button_release_event(self, e):
        print "button release!"
        if self.tool == "brush":
            #print "Getting new brush..."
            bbox = (self.lx, self.ly, int(e.x), int(e.y))
            tmp = self.get_img_bbox(bbox)
            img_bbox = (tmp[0], tmp[1], tmp[2]+1, tmp[3]+1)
            tmp = self.stack.get_layer().image.crop(img_bbox)
            self.brush = PyntBrush(data=tmp, transp_color=self.stack.get_layer().image.transp_color)
            
            #self.custom_brush = True
            bbox = self.stack.clear_scratch()
            #self.invalidate_img_bbox(bbox)
            self.emit("set-tool", "points")
            #self.set_tool("points")
        elif self.tool == "floodfill":
            
            if self.stack.mode in ("draw_fg", "erase"):
                color = self.stack.palette.fgcolor
            elif self.stack.mode == "draw_bg":
                color = self.stack.palette.bgcolor

            self.floodfill(color, (int(e.x), int(e.y)))
            bbox = self.stack.apply_scratch()
        else:
            bbox = self.stack.apply_scratch()
            
        #self.lx = self.ly = None
        self.stack.mode = None
        #bbox=self.stack.clear_scratch()
        if bbox is not None:
            self.invalidate_img_bbox(bbox)

    #def do_leave_notify_event(self, e):
    #    print "leave notify!"


    def on_undo(self):
        bbox = self.stack.undo_change()
        if bbox:
            self.invalidate_bbox(self.get_paper_bbox(bbox))

    def on_redo(self):
        bbox = self.stack.redo_change()
        if bbox:
            self.invalidate_bbox(self.get_paper_bbox(bbox))



# --- Drawing stuff ---

    def draw_line(self, color, width, coords, transient=False):
        x0, y0, x1, y1 = coords
        #print "X:", x1, " Y:", y1
        if x1>0 and y1>0 and x1<self.get_xlim() and y1<self.get_ylim():
            #print "drawing line:", bbox, color
            startx, starty = self.get_img_coord(x0, y0)
            endx, endy = self.get_img_coord(x1, y1)

            bbox = self.stack.draw_line(color, width,
                                 (startx, starty, endx, endy), transient)

            hw = width//2
            x0, y0, x1, y1 = bbox[0]-hw, bbox[1]-hw, bbox[2]+hw+1, bbox[3]+hw+1

            #rect = (x0*self.zoom-self.dx, y0*self.zoom-self.dy,
            #        (x1-x0)*self.zoom, (y1-y0)*self.zoom)

            #self.window.invalidate_rect(rect, False)
            self.invalidate_img_bbox(bbox)

    def draw_brush(self, brush, color, coords, transient=False, update=True):
        z = self.zoom
        w, h = brush.size
        x, y = self.get_img_coord(*coords)
        if x>0 and y>0 and x<self.stack.resolution[0] and y<self.stack.resolution[1]:
            if not brush.solid_color and brush.custom_brush:
                tmp = self.stack.draw_brush(brush, None, (x, y), transient=transient)
            else:
                tmp = self.stack.draw_brush(brush, color, (x, y), transient=transient)        
            if update:
                if tmp is not None:
                    self.invalidate_img_bbox(tmp)
                #self.invalidate_img_bbox((x-w//2, y-h//2, x+w//2+1, y+h//2+1))

    def draw_rectangle(self, color, rect, transient=False, filled=False):
        x, y, w, h = rect 
        if x+h<self.get_xlim() and y+h<self.get_ylim():            
            startx, starty = self.get_img_coord(x, y)
            endx, endy = self.get_img_coord(x+w, y+h) 
            if filled:
                fill=color
            else:
                fill=None
            coords = self.stack.draw_rect(color, (startx, starty, endx, endy), fill, transient)
            if coords is not None:
                self.invalidate_img_bbox(coords)

    def draw_ellipse(self, color, rect, transient=False, filled=False):
        x, y, w, h = rect 
        if x+h<self.get_xlim() and y+h<self.get_ylim():            
            startx, starty = self.get_img_coord(x, y)
            endx, endy = self.get_img_coord(x+w, y+h)
            if filled:
                fill=color
            else:
                fill=None
            coords = self.stack.draw_ellipse(color, (startx, starty, endx, endy), fill, transient)
            if coords is not None:
                self.invalidate_img_bbox(coords)

    def floodfill(self, color, xy):
        x, y = xy
        print "floodfill", xy
        if x<self.get_xlim() and y<self.get_ylim():
            x0y0 = self.get_img_coord(*xy)
            bbox = self.stack.floodfill(color, x0y0)
            #bbox = self.get_visible()
            #self.lx = self.ly = 0
            #print "adjustments:", self.lx, self.ly

            #print "size_request():", w, h
            
            self.invalidate_img_bbox(bbox)

    def pick_fgcolor(self, xy):
        ix, iy = self.get_img_coord(*xy)
        self.stack.palette.fgcolor = self.stack.get_area(*(ix,iy,ix+1,iy+1)).getpixel((0,0))
        self.emit("fgcolor-picked", self.stack.palette.fgcolor)
        print self.stack.palette.fgcolor

    def pick_bgcolor(self, xy):
        ix, iy = self.get_img_coord(*xy)
        self.stack.palette.bgcolor = self.stack.get_area(*(ix,iy,ix+1,iy+1)).getpixel((0,0))
        self.emit("bgcolor-picked", self.stack.palette.bgcolor)
        print self.stack.palette.fgcolor

# --- Coordinate transformations

    def get_xlim(self):
        return self.stack.resolution[0]*self.zoom 

    def get_ylim(self):
        return self.stack.resolution[1]*self.zoom

    def get_img_coord(self, x, y):
        return ((x+self.dx)//self.zoom, (y+self.dy)//self.zoom)

    def get_img_bbox(self, bbox):
        z = self.zoom
        x0, y0, x1, y1 = bbox
        dx = (self.dx//z)*z
        dy = (self.dy//z)*z
        return ((x0+dx)//z, (y0+dy)//z, 
                (x1+dx)//z, (y1+dy)//z)
    
    def get_paper_bbox(self, bbox):
        x0, y0, x1, y1 = bbox
        return (x0*self.zoom-self.dx, y0*self.zoom-self.dy,
                x1*self.zoom-self.dx, y1*self.zoom-self.dy)

    def get_update_rect(self, bbox):
        z=self.zoom
        x0, y0, x1, y1 = bbox
        x, y = (x0//z)*z, (y0//z)*z
        w, h = ((x1-x+z)//z)*z, ((y1-y+z)//z)*z
        #print "update_rect:", (x, y, w, h)
        return (x, y, w, h)



# --- Other functions ---

    def invalidate_bbox(self, bbox):
        x0, y0, x1, y1 = bbox
        self.window.invalidate_rect((x0, y0, x1-x0, y1-y0), False)

    def invalidate_img_bbox(self, bbox):
        #print "invalidate_img_bbox():", self.get_paper_bbox(bbox)
        if not bbox is None:
            self.invalidate_bbox(self.get_paper_bbox(bbox))

    def invalidate(self):
        w, h = self.window.get_size()
        self.window.invalidate_rect((0, 0, w, h), True)
        
    def set_zoom(self, zoom):

        print "zoomin'...", 

        if zoom >= 1 and zoom <= 256:  #zooming to less than 1 is flaky...

            w, h = self.window.get_size()
            x, y, state = self.window.get_pointer()
            xoffs = self._hadj.value
            yoffs = self._vadj.value
            xaim = (xoffs + x)*(zoom/self.zoom)
            yaim = (yoffs + y)*(zoom/self.zoom)
            #print "xvalue:", ((xaim-x)//zoom)*zoom
            #print "yvalue:", ((yaim-y)//zoom)*zoom

            xvalue=((xaim-x)//zoom)*zoom
            if xvalue > self.stack.resolution[0]*zoom - w:
                xvalue = (self.stack.resolution[0]*zoom - w)//zoom * zoom
            if xvalue < 0:
                xvalue = 0

            yvalue=((yaim-y)//zoom)*zoom
            if yvalue > self.stack.resolution[1]*zoom - h:
                yvalue = (self.stack.resolution[1]*zoom - h)//zoom * zoom
            if yvalue < 0:
                yvalue = 0

            self.stack.clear_scratch()
            self.pixmap.draw_rectangle(self.gc, True, 0, 0, w, h)

            print "xvalue, yvalue:", xvalue, yvalue

            self._hadj.set_all(value=xvalue,
                               lower=0, #min(0, ((xaim-x)//zoom)*zoom),
                               upper=self.stack.resolution[0]*zoom-1, 
                               step_increment=zoom, page_increment=zoom, 
                               page_size=w)
            self._vadj.set_all(value=yvalue,
                               lower=0, #min(0, ((yaim-y)//zoom)*zoom),
                               upper=self.stack.resolution[1]*zoom-1, 
                               step_increment=zoom, page_increment=zoom, 
                               page_size=h)

            #update the view
            w, h = int(round(self._hadj.page_size)), int(round(self._vadj.page_size))
            self.window.invalidate_rect((0, 0, w, h), False)

            self.zoom = zoom
            #self._hadj.upper = self.stack.resolution[0]*self.zoom
            #self._vadj.upper = self.stack.resolution[1]*self.zoom
            
            #self.stack.clear_scratch()
            #self.window.invalidate_rect((0, 0, w, h), False)            
            #self.set_adjustments(self.get_img_coord(

    def set_width(self, width):
        self.line_width = width
        self.brush = PyntBrush(size=(width, width))
            
    def update_pixmap(self, bbox):
        wtot, htot = self.stack.resolution[0]*self.zoom, self.stack.resolution[1]*self.zoom
        #print "update_pixmap:", bbox
        
        x0, y0, x1, y1 = bbox
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(wtot, x1)
        y1 = min(htot, y1)

        dx, dy = self.dx, self.dy

        z = self.zoom
        w, h = ((x1-x0)//z)*z, ((y1-y0)//z)*z
        #w, h = min((wtot-x0)*z, ((x1-x0)//z)*z), min((htot-y0), ((y1-y0)//z)*z)
        #w, h = int(self.zoom*((x1-x0)/self.zoom+0.5)), int(self.zoom*((y1-y0)/self.zoom+0.5))

        #print "updating pixmap:", w, h
        
        if self.zoom != 1:
            img_bbox = self.get_img_bbox((x0, y0, x0+w, y0+h)) 
        else:
            img_bbox = (x0+dx, y0+dy, x0+w+dx, y0+h+dy)

        #if self.zoom < 1:
        #    filter = Image.ANTIALIAS
        #else:
        #    filter = Image.NEAREST
        filter = Image.NEAREST
        imagedata = self.stack.get_area(*img_bbox).convert("RGBA").resize((w, h), filter).tostring()
        if w < x1 or h < y1:
            self.pixmap.draw_rectangle(self.gc, True, 0, 0, *self.pixmap.get_size())

        self.pixmap.draw_rgb_32_image(self.gc, x0, y0, 
                                      w, h, gtk.gdk.RGB_DITHER_NONE,
                                      imagedata, rowstride=w*4)

        return imagedata

    def get_visible_size(self):
        return self.window.get_size()
