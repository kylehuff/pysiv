#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""	pysiv.py
	Python Simple Interactive Volume control
	Author: Kyle L. Huff
	url: http://www.curetheitch.com/projects/pysiv/
	You are free to	use this code in any way shape or form. I hold no rights to
	this code or any derrivitave thereof. This code has no intended function
	outside of usage by	(myself) the developer.
	Email: pysiv -> curetheitch.com

	THIS PROGRAM IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
	EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE
	IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
	PARTICULAR PURPOSE. THE ENTIRE RISK AS TO THE QUALITY AND
	PERFORMANCE OF THE PROGRAM IS WITH YOU. SHOULD THE PROGRAM
	PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY
	SERVICING, REPAIR OR CORRECTION. I, THE PARTY, OR PARTIES, MAKING
	THIS PROGRAM AVAILABLE ARE DOING SO AS A REFERENCE WITH NO
	INTENDED FUNCTIONAL PURPOSE.
"""
import gtk, ossaudiodev
import os

# Constants
SETTINGS_DIR = "~/.config/pysiv"
POSITION_FILE = "%s/position" % SETTINGS_DIR
ORIENTATION_FILE = "%s/orientation" % SETTINGS_DIR

if os.path.isfile( os.path.expanduser(ORIENTATION_FILE) ):
	orientation = open( os.path.expanduser(ORIENTATION_FILE) ).readline().strip()
else:
	orientation = "horizontal"

try: #os.path.exists("%s/.config/pysiv" % os.path.expanduser("~") )
	if not os.path.exists(os.path.expanduser(SETTINGS_DIR)):
		os.makedirs(os.path.expanduser(SETTINGS_DIR))
except Exception, e:
	print e


# Open a handle to the mixer device
try:
    mixer = ossaudiodev.openmixer()
    mixertype = "oss"
except:
    import alsaaudio
    mixertype = "alsa"
    mixer = alsaaudio.Mixer('Master', 0)

if mixertype == "oss":
    # Check if the mixer device has a PCM control, if so we will use that, otherwise use the "Master" volume.
    # 	This IF/ELSE is to catch devices without a PCM control.
    #	I prefer to change the value of the PCM control, however if one prefers to use the Master Control, they
    #	can swap the order of ths IF/ELSE, or statically assign it, or skip assigning it here and just use the
    #	ossaudiodev.SOUND_MIXER_MASTER constant when referencing the control..
    if mixer.controls() & ( 1 << ossaudiodev.SOUND_MIXER_PCM ):
	    mixer_device = ossaudiodev.SOUND_MIXER_PCM
    elif mixer.controls() & ( 1 << ossaudiodev.SOUND_MIXER_VOLUME ):
	    mixer_device = ossaudiodev.SOUND_MIXER_VOLUME

# Function that requests the value of the specified mixer_device control.
# 	Returns a tuple..
def get_volume( ):
    if mixertype == "oss":
    	volstr = mixer.get( mixer_device )
    else:
        volstr = mixer.getvolume()
    return volstr if len(volstr) == 1 else ( int( volstr[0] ), int( volstr[1] ) )

# Function that changes the value of the specified mixer_device control.
# 	Does not return.
def change_volume( scale, event=None ):
	adjustment = scale.get_adjustment()
	if hasattr(event, "direction" ):
		scale.handler_block( scale.changed_event_connection_id )
		scale.handler_block( scale.scroll_event_connection_id )
		if event.direction == gtk.gdk.SCROLL_UP:
			adjustment.value += 5
			scale.set_adjustment( adjustment )
		elif  event.direction == gtk.gdk.SCROLL_DOWN:
			adjustment.value -= 5
			scale.set_adjustment( adjustment )
		scale.handler_unblock( scale.changed_event_connection_id )
		scale.handler_unblock( scale.scroll_event_connection_id )
	if adjustment.value <= 100 and adjustment.value >= 0:
		newvol = adjustment.value
		if mixertype == "oss":
			mixer.set( mixer_device, ( int( str( newvol ).split( '.' )[0] ), int( str( newvol ).split( '.' )[0] ) ) )
		else:
			mixer.setvolume( int( str( newvol ).split( '.' )[0] ) )


# Function to handle mouse movement events
# 	If the drag_event flag is True, then the user is dragging the window, so drag the window.
def mouse_move( widget=None, event=None, time=None ):
	if window.drag_event == True:
		window.move( ( window.get_position()[0] + window.get_pointer()[0] ) - window.original_click[0], ( window.get_position()[1] + window.get_pointer()[1] ) - window.original_click[1] )
		store_window_pos( ( window.get_position()[0] + window.get_pointer()[0] ) - window.original_click[0], ( window.get_position()[1] + window.get_pointer()[1] ) - window.original_click[1] )

# Function to catch the mouse down event. Callback from pos_button.
# 	Sets the drag_event flag and retrieves where on the screen the drag begins,
# 	also changes the cursor to the stock "Move" cursor
def mouse_down( widget=None, event=None ):
	if event.button == 1:
		window.drag_event = True
		window.original_click = window.get_pointer()
		window.window.set_cursor( gtk.gdk.Cursor( gtk.gdk.FLEUR ) )

# Function to catch the mouse up event. Callback from pos_button.
# 	Returns cursor to WM default, and sets the drag_event flag to False
def mouse_up( widget=None, event=None ):
	window.window.set_cursor( None )
	window.drag_event = False

# Function to store the last known position of the app
# 	if it fails to find the ~/.config/pysiv/position file, it will create it, if that fails,
# 	it will raise an exception
def store_window_pos( positionX, positionY ):
	try:
		pos_fh = open( os.path.expanduser(POSITION_FILE), "w" )
		pos_fh.write( "%s,%s" % ( positionX, positionY ) )
		pos_fh.close()
	except Exception, e:
		print e

vol = get_volume()	# Get the current volume on initialization so we can populate our adjustment widget
if len(vol) > 1:
    vol = ( int( vol[0] ) + int( vol[1] ) ) / 2	# Add the Left and Right values returned together and devide that by two for a total volume to update our mono adjustment scale
else:
    vol = (int(vol))

window = gtk.Window( gtk.WINDOW_POPUP )	# Create a window without any window manager decorations, that always stays on top.
window.set_position( gtk.WIN_POS_CENTER )	# Set the initial position to the center of the screen

# Look for the file ~/.config/pysiv/position which holds the last position, if fail, use default
if os.path.isfile( os.path.expanduser(POSITION_FILE) ):
	pos = open( os.path.expanduser(POSITION_FILE) ).readline().strip().split(",")
	window.move( int( pos[0] ), int( pos[1] ) )
else:
	window.move( window.get_position()[0], 0 )	# Move the window to the x value of Center, and 0.. So Top, Center.. ( I couldnt find a gtk constant for top-center)

window.drag_event = False	# Specify the initial value of the drag_event
window.connect( "destroy", gtk.main_quit )	# Connect the destory event to killing of the gtk main loop

if orientation == "vertical":
	vbox = gtk.VBox( False, 0 )	# An horizontal box to add our widgets too.

	window.add( vbox )	# Add hbox to window

	close_image = gtk.Image()	# Image to be assigned to close_button
	gtk.icon_size_register("VOL_BUTTONS", 12, 12)	# Register a special size for usage with gtk.STOCK_* items
	close_image.set_from_stock( gtk.STOCK_CLOSE, gtk.icon_size_from_name( "VOL_BUTTONS" ) )	# Assign the STOCK_CLOSE icon
	close_button = gtk.Button()	# Create the button
	close_button.set_image( close_image )	# Set the button image to the value of close_image
	close_button.connect( "clicked", gtk.main_quit )	# Connect the clicked event to the killing of the gtk main loop
	vbox.add( close_button )	 #Add the widget to the hbox

	vol_adj = gtk.VScale( gtk.Adjustment( value=vol, lower=0, upper=100, step_incr=1, page_incr=6 ) ) # Create a scale for volume adjustment/display
	vol_adj.set_inverted(True)
	vol_adj.set_size_request( 20, 100 )	# Request the size of the widget to be 100 wide and 20 tall
	vol_adj.changed_event_connection_id = vol_adj.connect( "value_changed", change_volume )	# Connect the change event to the change_volume function (I am assigning it to the variable vol_adh.changed_event_connection_id because I need the returned ID to later block the event, since the value of the control will be changed progromatically later
	vol_adj.set_draw_value( False )	# Tell the scale not to draw the decimal value of the scales current position
	vbox.add( vol_adj )	# Add the widget to our hbox

	pos_image = gtk.Image() # Image to be assigned to our "move" button
	pos_image.set_from_stock( gtk.STOCK_DND, gtk.icon_size_from_name( "VOL_BUTTONS" ) ) # Assign the STOCK_DND (drag-n-drop) icon to the button, as I couldnt find a STOCK_MOVE or equivelant, which would be better..
	pos_button = gtk.Button()	# Create the "move" button
	pos_button.set_image( pos_image )	# Assign the image to the value of pos_image
	pos_button.set_events( gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK ) # Expose the events we would like to catch. This is not really necessary for any event except the POINTER_MOTION_MASK, as that is not by default exposed, but I list all three for compatablilty.
	pos_button.connect( "motion_notify_event", mouse_move ) # Connect the exposed events to their respective functions
	pos_button.connect( "button_press_event", mouse_down )	# ''
	pos_button.connect( "button_release_event", mouse_up )	# ''

	vbox.add( pos_button ) # Add the pos_button to our hbox
else:
	hbox = gtk.HBox( False, 0 )	# An horizontal box to add our widgets too.

	window.add( hbox )	# Add hbox to window

	close_image = gtk.Image()	# Image to be assigned to close_button
	gtk.icon_size_register("VOL_BUTTONS", 12, 12)	# Register a special size for usage with gtk.STOCK_* items
	close_image.set_from_stock( gtk.STOCK_CLOSE, gtk.icon_size_from_name( "VOL_BUTTONS" ) )	# Assign the STOCK_CLOSE icon
	close_button = gtk.Button()	# Create the button
	close_button.set_image( close_image )	# Set the button image to the value of close_image
	close_button.connect( "clicked", gtk.main_quit )	# Connect the clicked event to the killing of the gtk main loop
	hbox.add( close_button )	 #Add the widget to the hbox

	vol_adj = gtk.HScale( gtk.Adjustment( value=vol, lower=0, upper=100, step_incr=1, page_incr=6 ) ) # Create a scale for volume adjustment/display
	vol_adj.set_size_request( 100, 20 )	# Request the size of the widget to be 100 wide and 20 tall
	vol_adj.changed_event_connection_id = vol_adj.connect( "value_changed", change_volume )	# Connect the change event to the change_volume function (I am assigning it to the variable vol_adh.changed_event_connection_id because I need the returned ID to later block the event, since the value of the control will be changed progromatically later
	vol_adj.scroll_event_connection_id = vol_adj.connect( "scroll_event", change_volume )
	vol_adj.set_draw_value( False )	# Tell the scale not to draw the decimal value of the scales current position
	hbox.add( vol_adj )	# Add the widget to our hbox


	pos_image = gtk.Image() # Image to be assigned to our "move" button
	pos_image.set_from_stock( gtk.STOCK_DND, gtk.icon_size_from_name( "VOL_BUTTONS" ) ) # Assign the STOCK_DND (drag-n-drop) icon to the button, as I couldnt find a STOCK_MOVE or equivelant, which would be better..
	pos_button = gtk.Button()	# Create the "move" button
	pos_button.set_image( pos_image )	# Assign the image to the value of pos_image
	pos_button.set_events( gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK ) # Expose the events we would like to catch. This is not really necessary for any event except the POINTER_MOTION_MASK, as that is not by default exposed, but I list all three for compatablilty.
	pos_button.connect( "motion_notify_event", mouse_move ) # Connect the exposed events to their respective functions
	pos_button.connect( "button_press_event", mouse_down )	# ''
	pos_button.connect( "button_release_event", mouse_up )	# ''

	hbox.add( pos_button ) # Add the pos_button to our hbox

window.show_all()	# Show everything

gtk.main()	# We're done, start running..
