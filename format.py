import cPickle, zlib

import Image
from stack import PyntStack, PyntLayer


class PyntLayerData(object):
    """A representation of a layer, intended for saving"""
    def __init__(self, layer):
        #self.mode = layer.image.mode
        self.resolution = layer.image.resolution
        self.zdata = layer.image.tozstring()
        self.visible = layer.visible
        self.anim = layer.anim

    def unzstring(self):
        return Image.fromstring("P", self.resolution, zlib.decompress(self.zdata))

    def get_layer(self):
        return PyntLayer(data=self.unzstring(), resolution=self.resolution, 
                         visible=self.visible, anim=self.anim)


class PyntData(object):
    "A pickle-able representation of a stack."
    def __init__(self, stack=None):
        self.layers = []
        if stack is not None:
            self.resolution = stack.resolution
            self.palette = stack.palette
            for layer in stack.layers:
                self.layers.append(PyntLayerData(layer))


    def save(self, filename):
        f = open(filename, "w")
        cPickle.dump(self, f)
        f.close()

    def load(self, filename):
        f = open(filename, "r")
        self = cPickle.load(f)
        f.close()

    def on_save_image(self, widget):
        save_file = file_browse(gtk.FILE_CHOOSER_ACTION_SAVE, "test")
        if save_file != "":
            path, extension = os.path.splitext(save_file)
            if extension == "":
                save_file = path + ".pynt"
            f = open(save_file, "w")
            tmp = []
            for l in self.stack.layers[1:]:
                zdata = zlib.compress(l.image.data.tostring())
                tmp.append({"data":(l.image.data.mode, l.image.data.size, zdata), "visible":l.visible, "anim":l.anim})
            cPickle.dump(tmp, f)
            f.close()

            
    def on_load_image(self, widget):
        load_file = file_browse(gtk.FILE_CHOOSER_ACTION_OPEN, "test")
        if load_file != "":
            f = open(load_file)
            tmp = cPickle.load(f)

            layerdata = []
            for l in tmp:
                mode = l["data"][0]
                size = l["data"][1]
                data = zlib.decompress(l["data"][2])
                img = Image.fromstring(mode, size, data)
                layerdata.append({"data":(mode, size, img), "visible":l["visible"], "anim":l["anim"]})
                #self.stack.add_layer(data=img, visible=l["visible"], anim=l["anim"])
            f.close()

            self.stack = PyntStack(resolution = tmp[0]["data"][1], data=layerdata)
            self.paper.stack = self.stack
            self.paper.invalidate()

            #x0, y0 = int(self.hadjustment.get_value()), int(self.vadjustment.get_value())
            #w, h = self.viewport.size_request()            
            #self.update_view(widget, x0, y0, x0+w, y0+h)
            self.update_frame_label()
            self.update_layer_label()
