"""

Event Monitor for Cozmo
============================

Based on Event Monitor for cozmo-tools:
https://github.com/touretzkyds/cozmo-tools

Created by: David S. Touretzky, Carnegie Mellon University

Edited by: GrinningHermit
More edits and expanded on by: AcidZebra
=====

"""

import re
import threading
import time
import cozmo
from cozmo.util import degrees, distance_mm, speed_mmps, Pose
from cozmo.objects import CustomObject, CustomObjectMarkers, CustomObjectTypes

robot = None
q = None # dependency on queue variable for messaging instead of printing to event-content directly
thread_running = False # starting thread for custom events

# custom eventlistener for picked-up and falling state, more states could be added
class CheckState (threading.Thread):
	def __init__(self, thread_id, name, _q):
		threading.Thread.__init__(self)
		self.threadID = thread_id
		self.name = name
		self.q = _q

	def run(self):
		delay = 10
		is_picked_up = False
		is_falling = False
		is_on_charger = False
		is_cliff_detected = False
		is_moving = False
		is_carrying_block = False
		is_localized = False
		is_picking_or_placing = False
		is_pathing = False
		while thread_running:

#pickup detection and response

			if robot.is_picked_up:
				delay = 0
				if not is_picked_up:
					robot.abort_all_actions(log_abort_messages=False)
					robot.enable_all_reaction_triggers(False)
					robot.stop_freeplay_behaviors()
					robot.abort_all_actions(log_abort_messages=False)
					robot.wait_for_all_actions_completed()
					#robot.play_anim_trigger(cozmo.anim.Triggers.TurtleRoll, ignore_body_track=True).wait_for_completed()
					robot.play_anim_trigger(cozmo.anim.Triggers.AskToBeRightedLeft, ignore_body_track=False).wait_for_completed()
					time.sleep(0.5)
					if robot.is_cliff_detected:
						robot.play_anim_trigger(cozmo.anim.Triggers.TurtleRoll, ignore_body_track=False).wait_for_completed()
					time.sleep(0.5)
					if robot.is_cliff_detected:
						robot.set_lift_height(1,1,1,0.1).wait_for_completed()
						robot.drive_wheels(-40, -40, l_wheel_acc=30, r_wheel_acc=30, duration=1.0)
					if robot.is_cliff_detected:
						robot.set_lift_height(1,1,1,0.1).wait_for_completed()
						robot.drive_wheels(-40, -40, l_wheel_acc=30, r_wheel_acc=30, duration=1.0)
						robot.drive_wheels(-40, -40, l_wheel_acc=30, r_wheel_acc=30, duration=1.0)
						robot.play_anim_trigger(cozmo.anim.Triggers.TurtleRoll, ignore_body_track=False).wait_for_completed()
					#robot.play_anim_trigger(cozmo.anim.Triggers.FlipDownFromBack, ignore_body_track=True).wait_for_completed()
					if robot.is_cliff_detected:
						robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabUnhappy, ignore_body_track=True).wait_for_completed()
					is_picked_up = True
					msg = 'state: cozmo.robot.Robot.is_pickup_up: True'
					print(msg)
					#self.q.put(msg)
			elif is_picked_up and delay > 9:
				robot.play_anim_trigger(cozmo.anim.Triggers.VC_HowAreYouDoing_AllGood, ignore_body_track=False, ignore_head_track=False, ignore_lift_track=False).wait_for_completed()
				robot.enable_all_reaction_triggers(True)
				robot.start_freeplay_behaviors()
				is_picked_up = False
				msg = 'state: cozmo.robot.Robot.is_pickup_up: False'
				print(msg)
				#self.q.put(msg)
			elif delay <= 9:
				delay += 1
				
#block carrying detection

			if robot.is_carrying_block:
				if not is_carrying_block:
					is_carrying_block = True
					msg = 'state: cozmo.robot.Robot.is_carrying_block: True'
					print(msg)
			elif not robot.is_carrying_block:
				if is_carrying_block:
					is_carrying_block = False
					msg = 'state: cozmo.robot.Robot.is_carrying_block: False'
					print(msg)

# localization detection

			if robot.is_localized:
				if not is_localized:
					is_localized = True
					msg = 'state: cozmo.robot.Robot.is_localized: True'
					print(msg)
			elif not robot.is_localized:
				if is_localized:
					is_localized = False
					msg = 'state: cozmo.robot.Robot.is_localized: False'
					print(msg)					

# falling detection

			if robot.is_falling:
				# TODO: need some kind of check here - if we've really fallen we probably need to stop playing until we're put back
				# TODO: make sad noises while we're waiting
				if not is_falling:
					is_falling = True
					msg = 'state: cozmo.robot.Robot.is_falling: True'
					print(msg)
					#self.q.put(msg)
			elif not robot.is_falling:
				if is_falling:
					is_falling = False
					msg = 'state: cozmo.robot.Robot.is_falling: False'
					print(msg)
					#self.q.put(msg)

# on charger detection

			if robot.is_on_charger:
				if not is_on_charger:
					is_on_charger = True
					# 
					# robot.abort_all_actions(log_abort_messages=False)
					# robot.enable_all_reaction_triggers(False)
					# robot.stop_freeplay_behaviors()
					# robot.abort_all_actions(log_abort_messages=False)
					# robot.wait_for_all_actions_completed()
					msg = 'state: cozmo.robot.Robot.is_on_charger: True'
					print(msg)
					#self.q.put(msg)
			elif not robot.is_on_charger:
				if is_on_charger:
					is_on_charger = False
					msg = 'state: cozmo.robot.Robot.is_on_charger: False'
					print(msg)
					#self.q.put(msg)

# cliff detection and response

			if robot.is_cliff_detected and not robot.is_falling and not robot.is_picked_up and not robot.is_pathing:
				if not is_cliff_detected:
					is_cliff_detected = True
					msg = 'state: cozmo.robot.Robot.is_cliff_detected: True'
					print(msg)
					robot.stop_freeplay_behaviors()
					robot.abort_all_actions(log_abort_messages=False)
					robot.wait_for_all_actions_completed()
					time.sleep(1)
					robot.drive_wheels(-40, -40, l_wheel_acc=30, r_wheel_acc=30, duration=1.5)
					robot.drive_wheels(-40, -40, l_wheel_acc=30, r_wheel_acc=30, duration=1.5)
					#robot.drive_straight(distance_mm(-200), speed_mmps(30)).wait_for_completed()
					robot.start_freeplay_behaviors()
					is_cliff_detected = False
					msg = 'state: cozmo.robot.Robot.is_cliff_detected: False'
					print(msg)
			elif not robot.is_cliff_detected:
				if is_cliff_detected:
					is_cliff_detected = False
					robot.start_freeplay_behaviors()

# is_picking_or_placing
			if robot.is_picking_or_placing:
				if not is_picking_or_placing:
					is_picking_or_placing = True
					msg = 'state: cozmo.robot.Robot.is_picking_or_placing: True'
					print(msg)
			elif not robot.is_picking_or_placing:
				if is_picking_or_placing:
					is_picking_or_placing = False
					msg = 'state: cozmo.robot.Robot.is_picking_or_placing: False'
					print(msg)		
				
# is pathing
			if robot.is_pathing:
				if not is_pathing:
					is_pathing = True
					msg = 'state: cozmo.robot.Robot.is_pathing: True'
					print(msg)
			elif not robot.is_pathing:
				if is_pathing:
					is_pathing = False
					msg = 'state: cozmo.robot.Robot.is_pathing: False'
					print(msg)	
				
# movement detection
# too spammy/unreliable

			# if robot.is_moving:
				# if not is_moving:
					# is_moving = True
					# msg = 'state: cozmo.robot.Robot.is_moving: True'
					# print(msg)
			# elif not robot.is_moving:
				# if is_moving:
					# is_moving = False
					# msg = 'state: cozmo.robot.Robot.is_moving: False'
					# print(msg)		

# end of detection loop

			time.sleep(0.1)

def print_prefix(evt):
	msg = evt.event_name + ' '
	return msg

def print_object(obj):
	if isinstance(obj,cozmo.objects.LightCube):
		cube_id = next(k for k,v in robot.world.light_cubes.items() if v==obj)
		msg = 'LightCube-' + str(cube_id)
	else:
		r = re.search('<(\w*)', obj.__repr__())
		msg = r.group(1)
	return msg

def monitor_generic(evt, **kwargs):
	msg = print_prefix(evt)
	if 'behavior_type_name' in kwargs:
		msg += kwargs['behavior_type_name'] + ' '
	if 'obj' in kwargs:
		msg += print_object(kwargs['obj']) + ' '
	if 'action' in kwargs:
		action = kwargs['action']
		if isinstance(action, cozmo.anim.Animation):
			msg += action.anim_name + ' '
		elif isinstance(action, cozmo.anim.AnimationTrigger):
			msg += action.trigger.name + ' '
	msg += str(set(kwargs.keys()))
	print(msg)

def monitor_EvtActionCompleted(evt, action, state, failure_code, failure_reason, **kwargs):
	msg = print_prefix(evt)
	msg += print_object(action) + ' '
	if isinstance(action, cozmo.anim.Animation):
		msg += action.anim_name
	elif isinstance(action, cozmo.anim.AnimationTrigger):
		msg += action.trigger.name
	if failure_code is not None:
		msg += str(failure_code) + failure_reason
	print(msg)

def monitor_EvtObjectTapped(evt, *, obj, tap_count, tap_duration, tap_intensity, **kwargs):
	msg = print_prefix(evt)
	msg += print_object(obj)
	msg += ' count=' + str(tap_count) + ' duration=' + str(tap_duration) + ' intensity=' + str(tap_intensity)
	#
	# TODO: expand on this to include some kind of interaction when tapping blocks
	# TODO: buy new batteries first :) 
	print(msg)

def monitor_face(evt, face, **kwargs):
	msg = print_prefix(evt)
	name = face.name if face.name is not '' else '[unknown face]'
	expression = face.expression if face.expression is not '' else '[unknown expression]'
	msg += name + ' face_id=' + str(face.face_id) + ' looking ' + str(face.expression)
	# TODO: expand on this to include some kind of interaction when observing a face
	# TODO: roll dice, stop freeplay if it's a win, then do some stuff like offering a game or just saying hi, then go back to freeplay
	
	print(msg)
	#if not robot.is_on_charger:
	#	if not face.name:
	#		time.sleep(1)
	#		robot.abort_all_actions(log_abort_messages=False)
	#		robot.wait_for_all_actions_completed()
	#		robot.play_anim_trigger(cozmo.anim.Triggers.VC_HowAreYouDoing_AllGood, ignore_body_track=False, ignore_head_track=False, ignore_lift_track=False).wait_for_completed()



dispatch_table = {
  cozmo.action.EvtActionStarted		: monitor_generic,
  cozmo.action.EvtActionCompleted	  : monitor_EvtActionCompleted,
  cozmo.behavior.EvtBehaviorStarted	: monitor_generic,
  cozmo.behavior.EvtBehaviorStopped	: monitor_generic,
  cozmo.behavior.EvtBehaviorRequested	: monitor_generic,
  #cozmo.behavior.Behavior	: monitor_generic,
  cozmo.anim.EvtAnimationsLoaded	   : monitor_generic,
  cozmo.anim.EvtAnimationCompleted	 : monitor_EvtActionCompleted,
  # cozmo.objects.EvtObjectAvailable	 : monitor_generic, # deprecated
  cozmo.objects.EvtObjectAppeared	  : monitor_generic,
  cozmo.objects.EvtObjectDisappeared   : monitor_generic,
  cozmo.objects.EvtObjectObserved	  : monitor_generic,
  cozmo.objects.EvtObjectTapped		: monitor_EvtObjectTapped,
  cozmo.faces.EvtFaceAppeared		  : monitor_face,
  cozmo.faces.EvtFaceObserved		  : monitor_face,
  cozmo.faces.EvtFaceDisappeared	   : monitor_face,
}

excluded_events = {	# Occur too frequently to monitor by default
	cozmo.objects.EvtObjectObserved,
	cozmo.faces.EvtFaceObserved,
}

def monitor(_robot, _q, evt_class=None):
	if not isinstance(_robot, cozmo.robot.Robot):
		raise TypeError('First argument must be a Robot instance')
	if evt_class is not None and not issubclass(evt_class, cozmo.event.Event):
		raise TypeError('Second argument must be an Event subclass')
	global robot
	global q
	global thread_running
	robot = _robot
	q = _q
	thread_running = True
	if evt_class in dispatch_table:
		robot.world.add_event_handler(evt_class,dispatch_table[evt_class])
	elif evt_class is not None:
		robot.world.add_event_handler(evt_class,monitor_generic)
	else:
		for k,v in dispatch_table.items():
			if k not in excluded_events:
				robot.world.add_event_handler(k,v)
	thread_is_state_changed = CheckState(1, 'ThreadCheckState', q)
	thread_is_state_changed.start()


def unmonitor(_robot, evt_class=None):
	if not isinstance(_robot, cozmo.robot.Robot):
		raise TypeError('First argument must be a Robot instance')
	if evt_class is not None and not issubclass(evt_class, cozmo.event.Event):
		raise TypeError('Second argument must be an Event subclass')
	global robot
	global thread_running
	robot = _robot
	thread_running = False

	try:
		if evt_class in dispatch_table:
			robot.world.remove_event_handler(evt_class,dispatch_table[evt_class])
		elif evt_class is not None:
			robot.world.remove_event_handler(evt_class,monitor_generic)
		else:
			for k,v in dispatch_table.items():
				robot.world.remove_event_handler(k,v)
	except Exception:
		pass