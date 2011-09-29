import Image, gtk


def enable_devices():
    for device in gtk.gdk.devices_list():
        if gtk.gdk.AXIS_PRESSURE in [a[0] for a in device.axes]:
            device.set_mode(gtk.gdk.MODE_SCREEN)
            print "Enabled device"

def get_pressure(event_data):
    for x in event_data.device.axes :
        if(x[0] == gtk.gdk.AXIS_PRESSURE) :
            pressure = event_data.get_axis(gtk.gdk.AXIS_PRESSURE)
            if not pressure :
                return 1
            print pressure
            return pressure
    return 1


def get_tilt(event_data):
    xtilt=ytilt=False
    for x in event_data.device.axes :
        if(x[0] == gtk.gdk.AXIS_XTILT) :
            xtilt = event_data.get_axis(gtk.gdk.AXIS_XTILT)
        elif(x[0] == gtk.gdk.AXIS_YTILT) :
            ytilt = event_data.get_axis(gtk.gdk.AXIS_YTILT)
        if xtilt and ytilt:
            return (xtilt, ytilt)
        else:
            return 0
    return 1


def bucketfill(image, pt, color):
    print "BUCKETFILL!"
    startX, startY = pt
    width, height = image.size
    pixelStack = [(startX, startY)]
    pixel = image.load()
    mask = Image.new("L", image.size, 0)
    mask_pixel = mask.load()

    startColor = pixel[startX, startY]

    if startColor == color:
        print "Same color!"
        return

    while pixelStack:
        newPos = pixelStack.pop()
        x, y = newPos
        print "position:", x, y
        while y > 0 and pixel[x, y] == startColor:
            y -= 1
        y+=1
        reachLeft = reachRight = False
        while (y < height-1) and (pixel[x, y] == startColor):
            print "y:", y
            mask_pixel[x, y] = 255
            if x > 0:
                if pixel[x, y] == startColor:
                    if not reachLeft:
                        print "append left: ",x-1, y
                        pixelStack.append((x - 1, y))
                        reachLeft = True
                elif reachLeft:
                    reachLeft = False
            if x < width-1:
                if pixel[x, y] == startColor:
                    if not reachRight:
                        print "append right: ",x+1, y
                        pixelStack.append((x + 1, y))
                        reachRight = True
                elif reachRight:
                    reachRight = False
            pixel[x, y] = color
            y += 1
    return mask

def floodfill(image, xy, value, border=None):
    """Fill bounded region. """
    # This function is from PIL, but modified to return a bit mask too."

    # NB: It would probably be faster to only make the mask and then blit
    # the color through it at the end.

    mask = Image.new("L", image.size, 0)
    mask_pixel = mask.load()
    pixel = image.load()
    x, y = xy
    try:
        background = pixel[x, y]
        if background == value:
            return # seed point already has fill color
        mask_pixel[x, y] = 255
        pixel[x, y] = value
    except IndexError:
        return # seed point outside image
    edge = [(x, y)]
    if border is None:
        while edge:
            newedge = []
            for (x, y) in edge:
                for (s, t) in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
                    try:
                        p = pixel[s, t]
                    except IndexError:
                        pass
                    else:
                        if p == background:
                            mask_pixel[s, t] = 255
                            pixel[s, t] = value
                            newedge.append((s, t))
            edge = newedge
    else:
        while edge:
            newedge = []
            for (x, y) in edge:
                for (s, t) in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
                    try:
                        p = pixel[s, t]
                    except IndexError:
                        pass
                    else:
                        if p != value and p != border:
                            mask_pixel[s, t] = 255
                            pixel[s, t] = value
                            newedge.append((s, t))
            edge = newedge
    return mask

def file_browse(dialog_action, file_dir="", file_name="", file_ext="pynt"):
	"""This function is used to browse for a pyWine file.
	It can be either a save or open dialog depending on
	what dialog_action is.
	The path to the file will be returned if the user
	selects one, however a blank string will be returned
	if they cancel or do not select one.
	dialog_action - The open or save mode for the dialog either
	gtk.FILE_CHOOSER_ACTION_OPEN, gtk.FILE_CHOOSER_ACTION_SA
        VE
        file_name - Default name when doing a save"""

	if (dialog_action==gtk.FILE_CHOOSER_ACTION_OPEN):
		dialog_buttons = (gtk.STOCK_CANCEL
							, gtk.RESPONSE_CANCEL
							, gtk.STOCK_OPEN
							, gtk.RESPONSE_OK)
	else:
		dialog_buttons = (gtk.STOCK_CANCEL
							, gtk.RESPONSE_CANCEL
							, gtk.STOCK_SAVE
							, gtk.RESPONSE_OK)

	file_dialog = gtk.FileChooserDialog(title="Select Project"
				, action=dialog_action
				, buttons=dialog_buttons)
	"""set the filename if we are saving"""
	if (dialog_action==gtk.FILE_CHOOSER_ACTION_SAVE):
		file_dialog.set_current_name(file_name)

        if file_dir != "":
            file_dialog.set_current_folder(file_dir)
	"""Create and add the pynt filter"""
	pyntfilter = gtk.FileFilter()
	pyntfilter.set_name("Pynt projects")
	pyntfilter.add_pattern("*.pynt")
	file_dialog.add_filter(pyntfilter)
	"""Create and add the 'all files' filter"""
	allfilter = gtk.FileFilter()
	allfilter.set_name("All files")
	allfilter.add_pattern("*")
        file_dialog.add_filter(allfilter)
	"""Create and add the 'all image files' filter"""
	pngfilter = gtk.FileFilter()
	pngfilter.set_name("All image files")
	pngfilter.add_pattern("*.png")
	file_dialog.add_filter(pngfilter)

        if file_ext == "pynt":
            file_dialog.set_filter(pyntfilter)
        elif file_ext == "png":
            file_dialog.set_filter(pngfilter)
        else:
            file_dialog.set_filter(allfilter)

	"""Init the return value"""
	result = ""
	if file_dialog.run() == gtk.RESPONSE_OK:
		result = file_dialog.get_filename()
	file_dialog.destroy()

	return result


def make_bbox(box):
    x0,y0,x1,y1 = box
    if x0>x1:
        x0,x1 = x1,x0
    if y0>y1:
        y0,y1 = y1,y0
    return (x0,y0,x1,y1)

def combine_bbox(bb1, bb2):
    if bb1 is not None and bb2 is not None:
        return (min(bb1[0], bb2[0]), min(bb1[1], bb2[1]), max(bb1[2], bb2[2]), max(bb1[3], bb2[3]))
    elif bb1 is not None:
        return bb1
    elif bb2 is not None:
        return bb2
    else:
        return None


def create_custom_cursor(window):
    # custom cursor
    #cursor_image = gtk.Image()
    #cursor_image.set_from_file("default_cursor.xpm")

    cursor_pixmap=gtk.gdk.Pixmap(window,19,19,1)

    #cursor_pixmap, cursor_mask = gtk.gdk.pixmap_create_from_xpm(self.window,
    #                                                            None, "default_cursor.xpm")
    # self.gc.set_line_attributes(1, gtk.gdk.LINE_DOUBLE_DASH, gtk.gdk.CAP_BUTT, gtk.gdk.JOIN_MITER)
    colormap = gtk.gdk.colormap_get_system()
    black = colormap.alloc_color('black')
    white = colormap.alloc_color('white')

    bgc = cursor_pixmap.new_gc(foreground=black)
    wgc = cursor_pixmap.new_gc(foreground=white)
    sgc = cursor_pixmap.new_gc(foreground=white)
    sgc.set_dashes(0, (1,1))
    sgc.set_line_attributes(1, gtk.gdk.LINE_ON_OFF_DASH, gtk.gdk.CAP_BUTT, gtk.gdk.JOIN_MITER)
    #self.cursor_pixmap.draw_line(gc, True, 0, 0, 9, 9)
    cursor_pixmap.draw_line(sgc, 0, 9, 19, 9)
    #self.cursor_pixmap.draw_line(sgc, 18, 9, 11, 9)
    cursor_pixmap.draw_line(sgc, 9, 0, 9, 19)
    #self.cursor_pixmap.draw_line(sgc, 9, 18, 9, 11)

    cursor_mask=gtk.gdk.Pixmap(window,19,19,1)
    cursor_mask.draw_rectangle(bgc,True,0,0,19,19)
    cursor_mask.draw_line(wgc, 0, 9, 7, 9)
    cursor_mask.draw_line(wgc, 18, 9, 11, 9)
    cursor_mask.draw_line(wgc, 9, 0, 9, 7)
    cursor_mask.draw_line(wgc, 9, 18, 9, 11)

    cur=gtk.gdk.Cursor(cursor_pixmap, cursor_mask,
                       black, white, 9, 9)

    #pixmap = gtk.gdk.Pixmap(None, 1, 1, 1)
    #color = gtk.gdk.Color()
    #cursor = gtk.gdk.Cursor(pixmap, pixmap, color, color, 0, 0)

    return cur
