import math, zlib
import Image, ImageDraw, ImageChops

class PyntImage(object):
    """Abstract class for images: only for subclassing"""
    transp_color = 0
    mask_palette = [255,255,255]*256

    def draw_rect(self, color, bbox, fill=None):
        self.draw.rectangle(bbox, outline=color, fill=fill)

    def draw_ellipse(self, color, bbox, fill=None):
        self.draw.ellipse(bbox, outline=color, fill=fill)

    def draw_line(self, color, width, bbox):
        x0, y0, x1, y1 = bbox
        #if y1 < y0:
        #    x0, x1 = x1, x0
        #    y0, y1 = y1, y0
        #bbox = (x0, y0, x1, y1)
        if width == 1:
            self.draw.line(bbox, fill=color)
        else:
            dx, dy = x1-x0, y1-y0
            l = math.sqrt(dx**2 + dy**2)
            sx = 0.5*((dx > 0 and 2) - 1)
            sy = 0.5*((dy > 0 and 2) - 1)
            if l > 0:
                dyn, dxn = int(((dx/l)*width/2+sx)), -int(((dy/l)*width/2+sy))
                poly = ((x0-dxn,y0-dyn), (x0+dxn,y0+dyn), 
                                   (x1+dxn,y1+dyn), (x1-dxn,y1-dyn))
                self.draw.polygon(poly, fill=color)
                return poly
            else:
                return None

    def floodfill(self, color, xy):
        return floodfill(self.data, xy, color)

    def crop(self, bbox):
        tmp = self.data.crop(bbox)
        tmp.load()
        return tmp
    
    def paste(self, source, bbox=(0,0), mask = None):
        if mask is None:
            self.data.paste(source, bbox)
        else:
            tmp = self.make_mask(mask)
            self.data.paste(source, bbox, tmp)

        
    def paint(self, color, bbox=(0,0), mask=None):
        if mask is None:
            self.data.paste(color, bbox)
        else:
            tmp = self.make_mask(mask)
            self.data.paste(color, bbox, tmp)


    def erase(self, bbox=(0,0), mask=None):
        #print "erasing:", self.transp_color
        if mask is None:
            self.data.paste(self.transp_color, bbox)
        else:
            tmp = self.make_mask(mask)
            self.data.paste(self.transp_color, bbox, tmp)

    def getpixel(self, pos):
        return self.data.getpixel(pos)
    
    def getbbox(self):
        return self.data.getbbox()

    def make_mask(self, img):
        tmp = img.copy()
        tmp.putpalette(self.mask_palette)
        return tmp.convert("L")

    def flip(self, vertically=False):
        print "Flipping..."
        if vertically:
            self.data = self.data.transpose(Image.FLIP_TOP_BOTTOM)
        else:
            self.data = self.data.transpose(Image.FLIP_LEFT_RIGHT)
            
    def rotate(self, angle):
        self.data = self.data.rotate(angle)
        self.size = self.data.size

    def tozstring(self):
        return zlib.compress(self.data.tostring())

    def combine(self, other):
        self.paste(other.data, mask=self.make_mask(other.data))


class PyntBrush(PyntImage):
    """Container for an arbitrary brush"""
    def __init__(self, size=(1,1), color=1, transp_color=0, data=None):
        if data is None:
            self.data = self.make_elliptic_brush(size, color, transp_color)
            self.custom_brush=False
        else:
            self.data = data
            self.custom_brush=True
        
        self.size = self.data.size
        self.set_transp_color(transp_color)
        self.solid_color = False

    def make_elliptic_brush(self, size, color, bgcolor):
        brush=Image.new("P", (size[0]+1, size[1]+1), bgcolor)
        brush_draw = ImageDraw.Draw(brush)
        brush_draw.ellipse((0,0,size[0],size[1]), fill=color)
        return brush

    def set_transp_color(self, n):
        self.mask_palette[self.transp_color*3] = 255
        self.mask_palette[self.transp_color*3+1] = 255
        self.mask_palette[self.transp_color*3+2] = 255
        self.transp_color = n
        self.mask_palette[n*3] = 0
        self.mask_palette[n*3+1] = 0
        self.mask_palette[n*3+2] = 0

    def get_mask(self):
        return self.make_mask(self.data)


    
class PyntImagePalette(PyntImage):
    """Palette based image"""
    def __init__(self, resolution=(800,600), fillcolor=0, data=None):
        self.resolution = resolution
        if data is None:
            self.data = Image.new("P", resolution, fillcolor)
            self.palette = (255,255,255, 0,0,0, 255,0,0, 0,255,0, 
                        0,0,255, 255,255,0, 0,255,255, 255,0,255) * 32
            self.data.putpalette(self.palette)
        else:
            self.data = data
        self.draw = ImageDraw.Draw(self.data)
        self.set_transp_color(0)

    def set_palette(self, colors):
        print "setting palette..."
        self.palette = colors
        if len(colors) == 256:
            colors = reduce(lambda x, y: x+y, colors)
        self.data.putpalette(colors)
        print colors[:10]
        self.draw = ImageDraw.Draw(self.data)

    def set_transp_color(self, n):
        self.mask_palette[self.transp_color*3] = 255
        self.mask_palette[self.transp_color*3+1] = 255
        self.mask_palette[self.transp_color*3+2] = 255
        self.transp_color = n
        self.mask_palette[n*3] = 0
        self.mask_palette[n*3+1] = 0
        self.mask_palette[n*3+2] = 0


class PyntImageRGBA(PyntImage):
    """RGB+alpha image"""
    def __init__(self, resolution=(640, 480), fillcolor=(255,255,255,255), data=None):
        self.resolution = resolution
        if data is None:
            self.data = Image.new("RGBA", resolution, fillcolor)
        else:
            self.data = data
        self.draw = ImageDraw.Draw(self.data)
        self.transp_color = (0,0,0,0)
        #self.data = numpy.zeros((self.resolution[0], self.resolution[1], 4), dtype=numpy.uint8)
        #self.data = 
        #self.data[:, :, :] = (255, 255, 255, 255)

    def set_transp_color(self, c):
        self.transp_color = c

