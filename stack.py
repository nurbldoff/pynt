import math
import Image, ImageDraw, ImageChops

from image import PyntImage, PyntImagePalette, PyntBrush
from palette import PyntPalette
from utils import make_bbox, combine_bbox, floodfill

class PyntChange(object):
    """An undoable operation"""
    def __init__(self, segment, position, layer, segment2=None, operation="draw"):
        self.segment = segment
        self.position = position
        self.layer = layer
        self.segment2 = segment2
        self.operation = operation

    def get_bbox(self):
        #print "change bbox:", self.position + (self.segment.size[0]+self.position[0], self.segment.size[1]+self.position[1])
        return self.position + (self.segment.size[0]+self.position[0], self.segment.size[1]+self.position[1])


class PyntLayer(object):
    """An image Layer (or Frame)"""
    def __init__(self, data=None, opacity=1.0, resolution=None, visible=True, anim=False, fillcolor=0):
        if data is not None:
            self.image = PyntImagePalette(data=data)
        else:
            self.image = PyntImagePalette(resolution=resolution, fillcolor=fillcolor)
            
        self.opacity = opacity
        self.visible=visible
        self.anim=anim


class PyntStack(object):
    """A stack is a number of Layers in a certain order. Drawing operations 
    on the stack are performed on the active layer, and are undoable."""

    def __init__(self, resolution=(800,600), data=None, palette=None):
        
        self.layers=[]
        self.layers.append(PyntLayer(resolution=resolution, fillcolor=0))

        self.resolution = resolution

        if palette is None:
            self.palette = PyntPalette()
        else:
            self.palette = palette

        if data is not None:
            if isinstance(data, Image.Image):
                self.layers.append(PyntLayer(data=data))
            else:
                self.layers = []
                for l in data.layers:
                    self.layers.append(l.get_layer())
                self.resolution = data.resolution
                self.palette = data.palette
        else:
            self.layers.append(PyntLayer(resolution=resolution))

        self.active_layer = 1
        self.scratch = PyntLayer(resolution=self.resolution, fillcolor=0)
        self.changes = []
        self.undone_changes = []
        self.last_rect_bbox = None
        self.mode = None
        self.last_brush_bbox=None

        self.set_palette(self.palette.get_pil_palette())

    def set_transp_color(self, n):
        self.get_layer().image.set_transp_color(n)
        self.scratch.image.set_transp_color(n)
        w, h = self.scratch.image.resolution
        self.scratch.image.erase((0,0,w,h))


    def get_pixel(self, pos):
        """return the color value of a pixel from one layer."""
        return self.get_layer().image.getpixel(pos)

    def get_layer(self, n=None):
        """Get the currently active layer."""
        if n is None:
            return self.layers[self.active_layer]
        else:
            return self.layers[n]

    def clear_layer(self):
        l = self.get_layer()
        bbox = l.image.getbbox()
        part = l.image.crop(bbox)
        part.load()
        self.changes.append(PyntChange(part, (bbox[0], bbox[1]), l))
        self.get_layer().image.erase(bbox)
        return bbox

    def get_layer_stats(self):
        """Information about the stack"""
        return (self.active_layer, len(self.layers)-1)

    def get_frame_stats(self):
        n=0
        j=0
        for i, f in enumerate(self.layers[1:]):
           if f.anim:
               n+=1
               if i+1 == self.active_layer:
                   j=n
        return (j, n)

    def get_active_bbox(self):
        return self.get_layer().image.getbbox()

    def toggle_animated(self):
        self.get_layer().anim = not self.get_layer().anim 

    def add_layer(self, data=None, visible=True, anim=False):
        if data is None:
            l = PyntLayer(resolution=self.resolution, visible=visible, anim=anim)
            self.layers.insert(self.active_layer+1, l)
                               
        else:
            l = PyntLayer(resolution=self.resolution, data=data, 
                          visible=visible, anim=anim)
            self.layers.insert(self.active_layer+1, l)
        return l
            

    def delete_layer(self, n=None):
        if n is None:
            n = self.active_layer
        if len(self.layers) > 1:
            del(self.layers[n])
            self.active_layer = max(1, self.active_layer-1)
            return True
        else:  #Can't delete if there's only one layer
            return False

    def join_layers(self, a=None, b=None):
        if a is None:
            a = self.active_layer
        la = self.get_layer(a)
        if b is None:
            b =  a - 1
        if b > 0:
            lb = self.get_layer(b)
        else:
            return False
            
        bbox = la.image.getbbox()
        print "join_layers, bbox:", bbox
        if bbox is not None:
            changed_part = lb.image.crop(bbox)
            #changed_part.load()
            changed_part2 = la.image.crop(bbox)
            #changed_part2.load()
            new_change = PyntChange(changed_part, bbox[:2],
                                    lb, changed_part2, operation="join layers")
            self.changes.append(new_change)

            lb.image.combine(la.image)
        self.delete_layer(a)
        return bbox

    def move_layer_up(self, n=None):
        if n is None:
            n=self.active_layer
        tmp = self.layers[n]
        del self.layers[n]
        self.layers.insert(n+1, tmp)


    def move_layer_down(self, n=None):
        if n is None:
            n=self.active_layer
        tmp = self.layers[n]
        del self.layers[n]
        self.layers.insert(max(1,n-1), tmp)

    def set_active_layer(self, new):
        self.active_layer = new
        self.scratch.image.set_transp_color(self.get_layer().image.transp_color)
        self.clear_scratch()
        #print "Active layer:", new

    def next_layer(self):
        if self.active_layer + 1 < len(self.layers):
            #if self.get_layer().anim:
            #    self.get_layer().visible = False
            self.set_active_layer(self.active_layer + 1)
            #if self.get_layer().anim:
            #    self.get_layer().visible = True
            return True
        else:
            return False

    def prev_layer(self):
        if self.active_layer - 1 > 0 :
            #if self.get_layer().anim:
            #    self.get_layer().visible = False
            self.set_active_layer(self.active_layer - 1)
            #if self.get_layer().anim:
            #    self.get_layer().visible = True
            return True
        else:
            return False


    def next_frame(self):
        #if self.layers[self.active_layer].anim:
        #    self.layers[self.active_layer].visible = False
        for i, f in enumerate(self.layers[self.active_layer+1:]):
            if f.anim:
                self.set_active_layer(self.active_layer+1+i)
                #self.layers[self.active_layer].visible = True
                return True
        for i,f in enumerate(self.layers[1:self.active_layer+1]):
            if f.anim:
                self.set_active_layer(1+i)
                #self.layers[self.active_layer].visible = True
                return True
        return False

        

    def prev_frame(self):
        #if self.layers[self.active_layer].anim:
        #    self.layers[self.active_layer].visible = False
        for i, f in enumerate(self.layers[self.active_layer-1:0:-1]):
            if f.anim:
                self.set_active_layer(self.active_layer-1-i)
                #self.layers[self.active_layer].visible = True
                return True
        for i,f in enumerate(self.layers[-1:self.active_layer-1:-1]):
            if f.anim:
                self.set_active_layer(len(self.layers)-1-i)
                #self.layers[self.active_layer].visible = True
                return True
        return False


    def get_area(self, x0, y0, x1, y1):
        #print "get_area"
        area = self.layers[0].image.crop((x0,y0,x1,y1))
        scratch_area = self.scratch.image.crop((x0,y0,x1,y1))
        #if self.active_layer == 0:
        #    area.paste(scratch_area, scratch_area)
        for i, layer in enumerate(self.layers[1:]):
            if layer.visible:
                next_area = layer.image.crop((x0,y0,x1,y1))
                mask = next_area.copy()
                if i+1 == self.active_layer:
                    if self.mode == "erase":
                        #print "erasing"
                        mask.paste(layer.image.transp_color, mask=layer.image.make_mask(scratch_area))
                        area.paste(next_area, mask=layer.image.make_mask(mask))
                    elif self.mode in ("draw_fg", "draw_bg", None):
                        area.paste(next_area, mask=layer.image.make_mask(next_area))
                        area.paste(scratch_area, mask=layer.image.make_mask(scratch_area))
                elif not layer.anim:
                    area.paste(next_area, mask=layer.image.make_mask(next_area))
        return area

    def draw_line(self, color, width, points, transient=False):
        if not transient:
            self.scratch.image.draw_line(color, width, points)
            bbox = make_bbox(points)
            return (bbox[0]-width, bbox[1]-width, bbox[2]+width, bbox[3]+width)
        else:
            old_bbox = self.last_rect_bbox
            bbox = make_bbox(points)
            bbox = (bbox[0]-width, bbox[1]-width, bbox[2]+width, bbox[3]+width)
            if old_bbox is not None:
                self.scratch.image.erase(old_bbox)
                total_bbox = combine_bbox(old_bbox, bbox)
            else:
                total_bbox = bbox
            self.scratch.image.draw_line(color, width, points)
            self.last_rect_bbox = bbox
            return total_bbox

    def draw_rect(self, color, bbox, fill=None, transient=False):
        if not transient:
            self.scratch.image.draw_rect(color, bbox, fill)
        else:
            old_bbox = self.last_rect_bbox
            bbox = make_bbox(bbox)
            new_bbox = (bbox[0], bbox[1], bbox[2]+1, bbox[3]+1)
            if old_bbox is not None:
                self.scratch.image.erase(old_bbox)
                total_bbox = combine_bbox(old_bbox, new_bbox)
            else:
                total_bbox = new_bbox
            self.scratch.image.draw_rect(color, bbox, fill)
            self.last_rect_bbox = new_bbox
            return total_bbox

    def draw_ellipse(self, color, bbox, fill=None, transient=False):
        if not transient:
            old_bbox = self.last_rect_bbox
        else:
            old_bbox = self.last_rect_bbox
            bbox = make_bbox(bbox)
            new_bbox = (bbox[0], bbox[1], bbox[2]+1, bbox[3]+1)
            if old_bbox is not None:
                self.scratch.image.erase(old_bbox)
                total_bbox = combine_bbox(old_bbox, new_bbox)
            else:
                total_bbox = new_bbox
            self.scratch.image.draw_ellipse(color, bbox, fill)
            self.last_rect_bbox = new_bbox
            return total_bbox


    def draw_brush(self, brush, color, pos, transient=False):
        #print "drawing brush at:", pos
        #print brush
        w,h = int(brush.size[0]/2), int(brush.size[1]/2)
        if self.last_brush_bbox is not None and transient:
            self.scratch.image.erase(self.last_brush_bbox)
        if color is None:
            print "no color"
            self.scratch.image.paste(brush.data, (pos[0]-w+1, pos[1]-h+1),
                                     mask=brush.get_mask())
        else:
            self.scratch.image.paint(color, (pos[0]-w+1, pos[1]-h+1), 
                                     mask=brush.get_mask())
        last = self.last_brush_bbox
        self.last_brush_bbox = ((pos[0]-w+1, pos[1]-h+1, pos[0]+w+2, pos[1]+h+2))
        return last #combine_bbox(last, bbox)

    def erase_last_brush(self, brush):
        w,h = brush.size
        self.scratch.image.erase(self.last_brush_bbox)
        last=self.last_brush_bbox
        self.last_brush_bbox = None
        return last

    def set_palette(self, colors):
        for l in self.layers:
            l.image.set_palette(colors)
        self.scratch.image.set_palette(colors)
            
    def floodfill2(self, color, xy):
        self.scratch.image.data = self.get_layer().image.data.copy()
        #self.scratch.image.data.load()
        #self.scratch.image.data.putalpha(255)  #why doesn't this work?
        mask = self.scratch.image.floodfill(color, xy)
        #self.scratch.image.data = ImageChops.difference(self.scratch.image.data, 
        #          self.layers[self.active_layer].image.data) #OK, getting the difference instead...
        if mask is not None:
            self.scratch.image.data.putalpha(mask)
            self.scratch.image.draw = ImageDraw.Draw(self.scratch.image.data)

    def floodfill(self, color, xy):
        tmp = self.get_layer().image.data.copy()
        if self.mode == "erase":
            #make sure we're filling with a different color from the initial pixel
            color = 255 - tmp.getpixel(xy)
        mask = floodfill(tmp, xy, color)
        if mask is not None:
            bbox = mask.getbbox()
            if bbox is not None:
                self.scratch.image.paint(color, mask=mask)
                return bbox
        return None

    def clear_scratch(self):
        scratch_bbox = self.scratch.image.getbbox()
        if scratch_bbox is not None:
            self.scratch.image.erase(scratch_bbox)
        return scratch_bbox

    def apply_scratch(self):
        scratch_bbox = self.scratch.image.data.getbbox()
        l = self.get_layer()
        print "scratch_bbox:", scratch_bbox
        print "mode:", self.mode
        if scratch_bbox is not None:
            #print scratch_bbox
            changed_part = l.image.crop(scratch_bbox)
            #changed_part.load()
            new_change = PyntChange(changed_part, (scratch_bbox[0], scratch_bbox[1]), 
                                    self.get_layer())
            self.changes.append(new_change)
            cropped_scratch = self.scratch.image.crop(scratch_bbox)
            if self.mode in ("draw_fg", "draw_bg"):
                l.image.paste(cropped_scratch, scratch_bbox, mask=l.image.make_mask(cropped_scratch))
            elif self.mode == "erase":
                l.image.erase(scratch_bbox, mask=l.image.make_mask(cropped_scratch))
            self.scratch.image.erase(scratch_bbox)
            if len(self.changes) > 10:
                del(self.changes[0])
            #print "changes:", len(self.changes)
            del(self.undone_changes[:])
            return scratch_bbox
        else:
            return False

    def undo_change(self):
        if len(self.changes) > 0:
            change = self.changes.pop()
            layer = change.layer
            if change.operation == "join layers":
                layer.image.paste(change.segment, change.position)
        
                self.set_active_layer(self.layers.index(change.layer))
                l = self.add_layer()
                l.image.paste(change.segment2, change.position)
                unchange = PyntChange(segment=None, position=None, 
                                      layer=l, operation="join layers")

                self.undone_changes.append(unchange)
                
            else:
                segment = layer.image.crop(change.get_bbox())
                unchange = PyntChange(segment, change.position,
                                      layer, operation=change.operation)
                self.undone_changes.append(unchange)
                layer.image.paste(change.segment, change.position)

            return(change.get_bbox())
        else:
            return False

    def redo_change(self):
        if len(self.undone_changes) > 0:
            unchange = self.undone_changes.pop()
            layer = unchange.layer
            if unchange.operation == "join layers":
                layer_a = self.layers.index(layer)
                layer_b = layer_a - 1
                return self.join_layers(layer_a, layer_b)
            else:
                segment = layer.image.crop(unchange.get_bbox())
                #segment.load()   #make sure it's a copy
                change = PyntChange(segment, unchange.position, layer)
                layer.image.data.paste(unchange.segment, unchange.position)
                self.changes.append(change)
                return(unchange.get_bbox())
        else:
            return False
