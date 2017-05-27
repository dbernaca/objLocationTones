# Joseph Lee
# Object coordinate tones

import globalPluginHandler
import eventHandler
import tones
import config
import api
from logHandler import log

def executeEvent(eventName,obj,**kwargs):
	"""Executes an NVDA event.
	@param eventName: the name of the event type (e.g. 'gainFocus', 'nameChange')
	@type eventName: string
	@param obj: the object the event is for
	@type obj: L{NVDAObjects.NVDAObject}
	@param kwargs: Additional event parameters as keyword arguments.
	"""
	try:
		sleepMode=obj.sleepMode
		if eventName=="gainFocus" and not eventHandler.doPreGainFocus(obj,sleepMode=sleepMode):
			return
		elif not sleepMode and eventName=="documentLoadComplete" and not eventHandler.doPreDocumentLoadComplete(obj):
			return
		elif not sleepMode:
			# NVDA Core issue 2559: play object location tone if requested.
			if eventName == "becomeNavigatorObject":
				try:
					l,t,w,h=obj.location
					x = l+(w/2)
					y = t+(h/2)
					screenWidth, screenHeight = api.getDesktopObject().location[2:]
					if x <= screenWidth or y <= screenHeight:
						minPitch=config.conf['mouse']['audioCoordinates_minPitch']
						maxPitch=config.conf['mouse']['audioCoordinates_maxPitch']
						curPitch=minPitch+((maxPitch-minPitch)*((screenHeight-y)/float(screenHeight)))
						brightness=config.conf['mouse']['audioCoordinates_maxVolume']
						leftVolume=int((85*((screenWidth-float(x))/screenWidth))*brightness)
						rightVolume=int((85*(float(x)/screenWidth))*brightness)
						tones.beep(curPitch,40,left=leftVolume,right=rightVolume)
				except:
					pass
			eventHandler._EventExecuter(eventName,obj,kwargs)
	except:
		log.exception("error executing event: %s on %s with extra args of %s"%(eventName,obj,kwargs))

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	def __init__(self):
		super(globalPluginHandler.GlobalPlugin, self).__init__()
		self._origExecuteEvent = eventHandler.executeEvent
		eventHandler.executeEvent = executeEvent

	def terminate(self):
		eventHandler.executeEvent = self._origExecuteEvent
