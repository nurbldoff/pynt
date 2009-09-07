import Image, gtk


def enable_devices():
    for device in gtk.gdk.devices_list():
        if gtk.gdk.AXIS_PRESSURE in [a[0] for a in device.axes]:
            device.set_mode(gtk.gdk.MODE_SCREEN)
            print "Enabled device"

def get_pressure(event_data):
    for x in event_data.device.axes :
        print "hoj"
        print x[0]
        if(x[0] == gtk.gdk.AXIS_PRESSURE) :
            pressure = event_data.get_axis(gtk.gdk.AXIS_PRESSURE)
            if not pressure :
                return 0
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



def floodfill(image, xy, value, border=None):
    """Fill bounded region. """
    # This function is from PIL, but modified to return a bit mask too."

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

def file_browse(dialog_action, file_name="", file_ext="pynt"):
	"""This function is used to browse for a pyWine file.
	It can be either a save or open dialog depending on
	what dialog_action is.
	The path to the file will be returned if the user
	selects one, however a blank string will be returned
	if they cancel or do not select one.
	dialog_action - The open or save mode for the dialog either
	gtk.FILE_CHOOSER_ACTION_OPEN, gtk.FILE_CHOOSER_ACTION_SAVE
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
	"""Create and add the pynt filter"""
	filter = gtk.FileFilter()
	filter.set_name("Pynt project")
	filter.add_pattern("*." + file_ext)
	file_dialog.add_filter(filter)
	"""Create and add the 'all files' filter"""
	filter = gtk.FileFilter()
	filter.set_name("All files")
	filter.add_pattern("*")
	file_dialog.add_filter(filter)
	"""Create and add the 'all image files' filter"""
	filter = gtk.FileFilter()
	filter.set_name("All image files")
	filter.add_pattern("*.png")
	file_dialog.add_filter(filter)


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
    
