# Object Location Tones
# A global plugin for NVDA
# Copyright 2017 Joseph Lee, released under GPL

# Brings NVDA Core issue 2559 to life.

import globalPluginHandler
import tones
import config
import api
import globalVars

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	def __init__(self):
		super(globalPluginHandler.GlobalPlugin, self).__init__()
		# No, I'll never let you announce obj coords in secure screens.
		if globalVars.appArgs.secure: return

	def event_becomeNavigatorObject(self, obj, nextHandler):
		# Until NVDA Core 2559 is implemented...
		try:
			l,t,w,h = obj.location
			x = l+(w/2)
			y = t+(h/2)
			screenWidth, screenHeight = api.getDesktopObject().location[2:]
			if 0 <= x <= screenWidth and 0 <= y <= screenHeight:
				minPitch = config.conf['mouse']['audioCoordinates_minPitch']
				maxPitch = config.conf['mouse']['audioCoordinates_maxPitch']
				curPitch = minPitch+((maxPitch-minPitch)*((screenHeight-y)/float(screenHeight)))
				brightness = config.conf['mouse']['audioCoordinates_maxVolume']
				leftVolume = int((85*((screenWidth-float(x))/screenWidth))*brightness)
				rightVolume = int((85*(float(x)/screenWidth))*brightness)
				tones.beep(curPitch,40,left=leftVolume,right=rightVolume)
		except:
			pass
		nextHandler()
