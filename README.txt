Pynt - a pixel editor

Pynt is my attempt at making a pixel-based painting program in the vein of "Deluxe Paint" on the Amiga. However, it's not intended as a "clone" and in fact it is quite different in many ways. Particularly there are lots of features missing (mostly those I seldom or never used, or have become sort of obsolete) and also some new features that may not have been possible in those days. 

Pynt is in the "alpha" stage right now (or maybe more appropriately, "prototype stage"), many features are rudimentary or missing and there is NO guarantee of usability, stability or forwards compatibility. Notably, Pynt still can't export to any normal image formats and the save/load functionality is *extremely* inefficient and basic. Don't put any trust in it.

Pynt is written in Python, and requires PyGTK for its GUI parts and PIL (Python Imaging Library) for its image handling backend.


Drawing tools

The basic drawing tools (pencil, line, fill, etc) mostly work like in DPaint and they are very simple so I won't describe them much more here. Well, one difference is that the right mousebutton now always paints with the "transparent" color, like you would expect from an eraser. 

Right now the only color mode supported is 24 bit RGB. The palette works but is very basic.

Unlike Dpaint, Pynt has multiple undo/redo, which is nice.


View

Zooming etc is found in the View menu and also work straightforwardly. 


Layers

The most intricate feature is probably the Layers. They double as traditional layers (think gimp/photoshop/almost any modern painting software) and animation frames. You can think of traditional layers as a stack of transparencies onto which you can draw separately. The resulting image is what you get when you look through the whole bunch of transparencies. Things drawn in Layers higher up in the stack cover the lower Layers. Adding and removing layers is done with "Add/Delete layer" in the Layers menu.

There is always an "active" layer; the one in which your drawing operations currently are made. The active layer is selected using the "Next/Prev layer" operations in the Layers menu. Which layer you're currently working on is displayed in the lower left corner (e.g. "Layer:1/2" means there are 2 layers and number 1, the bottom-most one, is currently active.)


Animation

Each layer can be either a "plain" Layer or a Frame. This can be toggled using the "Amination frame" toggle in the Layers menu.  A Frame, although still technically a Layer, works slightly differently in practise. Instead of just lying in its place in the stack, a Frame is only actually visible when it is the "active" Layer. That means that there is never more than one Frame visible at any given time, as opposed to any number of visible plain Layers. All non-active Frames are invisible.

By using the "Next/Prev frame" actions in the Layers menu, you can step through all Frames in the stack, skipping plain Layers. The "Frame:n/n" indicator at the bottom left corner tells you which Frame you're currently at and how many there are in total.

The point of this is that it makes it easy to do animations. You just add as many Frames as you need and then flip back and forth between them, editing them as you like. Any static background or forefround can be added as plain Layers below or above the Frames. You can even put Layers in the middle of your animation, confusing as it may be.