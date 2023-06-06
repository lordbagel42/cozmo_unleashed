#!/usr/bin/env python3

# based on Copyright (c) 2016 Anki, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License in the file LICENSE.txt or at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# simple_dock_with_chargermarker
# This script will use Walls & a Charger Marker to locat the Charger while using an asyncio.gather()
# The Walls, FreePlay Lights, & Charger Marker can be turned off & on as needed
# These Definitions are Asyncio Definitions and must require a Python version that can run Asyncio scripts
# This script is an attempt to get Cozmo to see either the Charger or the Charger Marker at the same time
# This script does not require any of these options to be turned on, all you need is a Charger
# forked script from: cozmo_unleashed
#
# Original perpetual Cozmo_Unleashed script by AcidZebra
# This Script is made by VictorTagayun and is heavily slimmed down to only docking
# Script based on the Cozmo SDK drive_to_charger example script 
# and raproenca's modifications of same.
#
# Additional modifications by Banteel to streamline the two 90 degree turns in one simple
# command that is linked to position.angle_z of object "charger" which contains all the info.
# Also modifications by Banteel to the goto_object by inserting a position angle into it.
#
#import required functions
import sys, os, datetime, random, time, math, re, threading
##import logging
import asyncio, cozmo, cozmo.objects, cozmo.util, cozmo.anim, cozmo.run
from cozmo.util import degrees, Angle, Distance, distance_mm, Speed, speed_mmps, Pose, pose_z_angle, rotation_z_angle
from cozmo.objects import CustomObject, CustomObjectMarkers, CustomObjectTypes, LightCube
from cozmo.behavior import BehaviorTypes
from cozmo.anim import Triggers
from cozmo.robot_alignment import RobotAlignmentTypes
from asyncio.tasks import create_task, gather

global robot, charger, freeplay, robotvolume, found_object, custom_objects, marker_time, use_cubes, use_walls
global use_scheduler, scheduled_days, scheduled_time

robot = cozmo.robot.Robot
custom_objects=[]
found_object=None
freeplay=0
marker_time=0
scheduled_days="None"
scheduled_time=0
#
#============================
# CONFIGURABLE VARIABLES HERE
#============================
#
# BATTERY VOLTAGE THRESHOLDS
#
# lowbatvolt - when voltage drops below this Cozmo will start looking for his charger
# highbatvolt - when cozmo comes off your charger fully charge, this value will self-calibrate
# maxbatvolt - the maximum battery level as recorded when cozmo is on charger but no longer charging
# tweak lowbatvolt to suit your cozmo. default value is 3.65
lowbatvolt = 3.65
#highbatvolt= 4.04 - currently not used
#maxbatvolt = 4.54 - currently not used
#
# COZMO'S VOICE VOLUME
# what volume Cozmo should play sounds at, value between 0 and 1
robotvolume = 0.05
#
# CUBE USAGE
#
# whether or not to activate the cubes (saves battery if you don't)
# I almost always leave this off, he will still stack them and mess around with them
# some games like "block guard dog" will not come up unless the blocks are active
#
# value of 0: cubes off & cube's lights off
# value of 1: cubes on & enables all games
# value of 2: cubes on & cube's freeplay lights on & in-schedule breathing lights off
# value of 3: cubes on & cube's freeplay lights on & in-schedule breathing lights on
# value between 0 and 3
use_cubes = 3
# 
# MARKER WALLS USAGE
#
# whether or not you are using printed out markers for walls on your play field
# if you are using walls, you will likely need to configure wall sizes to your play area
# values between 0 and 1
use_walls = 1
#
# SCHEDULER USAGE
#
# whether or not to use the schedule to define allowed "play times"
# this code is a bit rough, use at your own risk
# value between 0 and 1
use_scheduler = 1
#
# SCHEDULE START & STOP SETTING IN 24HR TIME FORMAT ex. 0 to 23
#
if use_scheduler == 1:
	# Initialize Scheduler Variables
	global wkDS, wkDSm, wkDE, wkDEm, wkNS, wkNSm, wkNE, wkNEm, wkEDS, wkEDSm, wkEDE, wkEDEm, wkENS, wkENSm, wkENE, wkENEm, wday
	# Week Days
	wkDS = 9		# Week (D)ay's (S)tarting time hour, default is 7AM
	wkDSm = 30		# Week (D)ay's (S)tarting time minute
	wkDE = 14		# Week (D)ay's (E)nding time hour, default is 8AM
	wkDEm = 0		# Week (D)ay's (E)nding time minute
	# Week Day Nights
	wkNS = 16		# Week (N)ight's (S)tarting time hour, default is 3PM
	wkNSm = 0		# Week (N)ight's (S)tarting time minute
	wkNE = 22		# Week (N)ight's (E)nding time hour, default is 11PM
	wkNEm = 0		# Week (N)ight's (E)nding time minute
	# Week End Days
	wkEDS = 9		# Week(E)nd (D)ay's (S)tarting time hour, default is 9AM
	wkEDSm = 30		# Week(E)nd (D)ay's (S)tarting time minute
	wkEDE = 15		# Week(E)nd (D)ay's (E)nding time hour, default is 12PM
	wkEDEm = 0		# Week(E)nd (D)ay's (E)nding time minute
	# Week End Nights
	wkENS = 9		# Week(E)nd (N)ight's (S)tarting time hour, default is 3PM
	wkENSm = 30		# Week(E)nd (N)ight's (S)tarting time minute
	wkENE = 15		# Week(E)nd (N)ight's (E)nding time hour, default is 11PM
	wkENEm = 0		# Week(E)nd (N)ight's (E)nding time minute
#
	#COZMO SCHEDULER DEFAULT TIME SETTINGS:
	## Week Days
	#wkDS = 7		# Week (D)ay's (S)tarting time hour, default is 7AM
	#wkDSm = 15		# Week (D)ay's (S)tarting time minute
	#wkDE = 8		# Week (D)ay's (E)nding time hour, default is 8AM
	#wkDEm = 35		# Week (D)ay's (E)nding time minute
	#
	## Week Day Nights
	#wkNS = 15		# Week (N)ight's (S)tarting time hour, default is 3PM
	#wkNSm = 35		# Week (N)ight's (S)tarting time minute
	#wkNE = 23		# Week (N)ight's (E)nding time hour, default is 11PM
	#wkNEm = 15		# Week (N)ight's (E)nding time minute
	#
	## Week End Days
	#wkEDS = 9		# Week(E)nd (D)ay's (S)tarting time hour, default is 9AM
	#wkEDSm = 0		# Week(E)nd (D)ay's (S)tarting time minute
	#wkEDE = 12		# Week(E)nd (D)ay's (E)nding time hour, default is 12PM
	#wkEDEm = 20	# Week(E)nd (D)ay's (E)nding time minute
	#
	## Week End Nights
	#wkENS = 15		# Week(E)nd (N)ight's (S)tarting time hour, default is 3PM
	#wkENSm = 35	# Week(E)nd (N)ight's (S)tarting time minute
	#wkENE = 23		# Week(E)nd (N)ight's (E)nding time hour, default is 11PM
	#wkENEm = 58	# Week(E)nd (N)ight's (E)nding time minute
#
# #####
# I define goto_chargermarker_pose, find_chargermarker, lookaround_behaviour, and freeplay_lookaround_behaviour
# separated into 4 definitions so a gather() can perform concurrent charger & chargermarker lookaround routines
#
## define goto_chargermarker_pose behaviour
async def goto_chargermarker_pose(robot: robot):
	global charger, custom_objects, found_object
	counter=0
	while robot.world.charger == None:
		if str(found_object.object_type) == "CustomObjectTypes.CustomType01" and charger==None:
			if found_object.is_visible==False:
				try:
					await robot.turn_in_place(degrees(found_object.pose.rotation.angle_z.degrees), num_retries=1, accel=degrees(80), angle_tolerance=None, is_absolute=True).wait_for_completed()
				except:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: failed to turn in place, battery %s" % str(round(robot.battery_voltage, 2)))
			if found_object.is_visible==False:
				raise asyncio.CancelledError()
			try:
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: custom object found, traveling, battery %s" % str(round(robot.battery_voltage, 2)))
				action = robot.go_to_pose(pose_z_angle(found_object.pose.position.x, found_object.pose.position.y, found_object.pose.position.z, angle_z=degrees(found_object.pose.rotation.angle_z.degrees)))
				await action.wait_for_completed()
			except:
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: failed to goto pose, battery %s" % str(round(robot.battery_voltage, 2)))
			await robot.wait_for_all_actions_completed()
			await asyncio.sleep(0.5)
			try:
				await robot.turn_in_place(degrees(found_object.pose.rotation.angle_z.degrees), num_retries=1, accel=degrees(80), angle_tolerance=None, is_absolute=True).wait_for_completed()
			except:
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: failed to turn in place, battery %s" % str(round(robot.battery_voltage, 2)))
			try:
				await robot.set_head_angle(degrees(0)).wait_for_completed()
			except:
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: failed to set head angle, battery %s" % str(round(robot.battery_voltage, 2)))
			await robot.wait_for_all_actions_completed()
			await asyncio.sleep(3)
			if robot.world.charger != None:
				charger = robot.world.charger
				robot.world.charger=None
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: found charger after goto chargermarker, battery %s" % str(round(robot.battery_voltage, 2)))
				await asyncio.sleep(0.5)				
				try:
					await robot.turn_in_place(degrees(found_object.pose.rotation.angle_z.degrees), num_retries=1, accel=degrees(80), angle_tolerance=None, is_absolute=True).wait_for_completed()
				except:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: failed to turn in place, battery %s" % str(round(robot.battery_voltage, 2)))
				try:
					await robot.drive_straight(distance_mm(-120), speed_mmps(40)).wait_for_completed()
					await robot.wait_for_all_actions_completed()
				except:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: failed to drive straight, battery %s" % str(round(robot.battery_voltage, 2)))
				try:
					action = robot.go_to_object(charger, distance_mm(100), RobotAlignmentTypes.LiftPlate, num_retries=3)
					await action.wait_for_completed()
					await robot.wait_for_all_actions_completed()
				except:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: failed to goto object, battery %s" % str(round(robot.battery_voltage, 2)))
				try:
					action = robot.go_to_object(charger, distance_mm(80), RobotAlignmentTypes.LiftPlate, num_retries=3)
					await action.wait_for_completed()
					await robot.wait_for_all_actions_completed()
				except:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: failed to goto object, battery %s" % str(round(robot.battery_voltage, 2)))
				try:
					action = robot.go_to_object(charger, distance_mm(60), RobotAlignmentTypes.LiftPlate, num_retries=3)
					await action.wait_for_completed()
					await robot.wait_for_all_actions_completed()
				except:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: failed to goto object, battery %s" % str(round(robot.battery_voltage, 2)))
				raise asyncio.CancelledError()
			if charger == None:
				await asyncio.sleep(0.5)
				try:
					await robot.turn_in_place(degrees(found_object.pose.rotation.angle_z.degrees), num_retries=1, accel=degrees(80), angle_tolerance=None, is_absolute=True).wait_for_completed()
				except:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: failed to turn in place, battery %s" % str(round(robot.battery_voltage, 2)))
				try:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: can't see charger, backup a bit, battery %s" % str(round(robot.battery_voltage, 2)))
					await robot.drive_straight(distance_mm(-80), speed_mmps(40)).wait_for_completed()
				except:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: failed to drive straight, battery %s" % str(round(robot.battery_voltage, 2)))
			else:
				await asyncio.sleep(0.5)
				try:
					await robot.turn_in_place(degrees(found_object.pose.rotation.angle_z.degrees), num_retries=1, accel=degrees(80), angle_tolerance=None, is_absolute=True).wait_for_completed()
				except:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: failed to turn in place, battery %s" % str(round(robot.battery_voltage, 2)))
				try:
					await robot.drive_straight(distance_mm(-40), speed_mmps(40)).wait_for_completed()
				except:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: failed to drive straight, battery %s" % str(round(robot.battery_voltage, 2)))
			try:
				await robot.turn_in_place(degrees(found_object.pose.rotation.angle_z.degrees), num_retries=1, accel=degrees(80), angle_tolerance=None, is_absolute=True).wait_for_completed()
			except:
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: failed to turn in place, battery %s" % str(round(robot.battery_voltage, 2)))
			await robot.wait_for_all_actions_completed()
			try:
				charger = await robot.world.wait_for_observed_charger(timeout=1.5, include_existing=True)
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: found charger after backup!, battery %s" % str(round(robot.battery_voltage, 2)))
				found_object=None
				custom_objects=[0]
				raise asyncio.CancelledError()
			except asyncio.TimeoutError:
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: i don't see the charger, battery %s" % str(round(robot.battery_voltage, 2)))
			await asyncio.sleep(1)
			if charger == None:
				await asyncio.sleep(0.5)
				try:
					await robot.turn_in_place(degrees(found_object.pose.rotation.angle_z.degrees), num_retries=1, accel=degrees(80), angle_tolerance=None, is_absolute=True).wait_for_completed()
				except:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: failed to turn in place, battery %s" % str(round(robot.battery_voltage, 2)))
				try:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: can't see charger, backup a bit more, battery %s" % str(round(robot.battery_voltage, 2)))
					await robot.drive_straight(distance_mm(-60), speed_mmps(40)).wait_for_completed()
				except:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: failed to drive straight, battery %s" % str(round(robot.battery_voltage, 2)))
			else:
				await asyncio.sleep(0.5)
				try:
					await robot.turn_in_place(degrees(found_object.pose.rotation.angle_z.degrees), num_retries=1, accel=degrees(80), angle_tolerance=None, is_absolute=True).wait_for_completed()
				except:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: failed to turn in place, battery %s" % str(round(robot.battery_voltage, 2)))
				try:
					await robot.drive_straight(distance_mm(-40), speed_mmps(40)).wait_for_completed()
				except:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: failed to drive straight, battery %s" % str(round(robot.battery_voltage, 2)))
			await asyncio.sleep(0.5)
			try:
				await robot.turn_in_place(degrees(found_object.pose.rotation.angle_z.degrees), num_retries=1, accel=degrees(80), angle_tolerance=None, is_absolute=True).wait_for_completed()
			except:
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: failed to turn in place, battery %s" % str(round(robot.battery_voltage, 2)))
			try:
				charger = await robot.world.wait_for_observed_charger(timeout=1.5, include_existing=True)
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: found charger after backup!, battery %s" % str(round(robot.battery_voltage, 2)))
				found_object=None
				custom_objects=[0]
				raise asyncio.CancelledError()
			except asyncio.TimeoutError:
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: i still don't see the charger, battery %s" % str(round(robot.battery_voltage, 2)))
			await asyncio.sleep(1)
			await robot.set_head_angle(degrees(10)).wait_for_completed()
			await robot.wait_for_all_actions_completed()
			await asyncio.sleep(1)
			if found_object.is_visible==False:
				await asyncio.sleep(0.5)
				try:
					await robot.turn_in_place(degrees(found_object.pose.rotation.angle_z.degrees), num_retries=1, accel=degrees(80), angle_tolerance=None, is_absolute=True).wait_for_completed()
				except:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: failed to turn in place, battery %s" % str(round(robot.battery_voltage, 2)))
				try:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: can't see chargermarker, backup a lot, battery %s" % str(round(robot.battery_voltage, 2)))
					await robot.drive_straight(distance_mm(-70), speed_mmps(40)).wait_for_completed()
				except:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: failed to drive straight, battery %s" % str(round(robot.battery_voltage, 2)))
				try:
					charger = await robot.world.wait_for_observed_charger(timeout=1.5, include_existing=True)
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: found charger after backup!, battery %s" % str(round(robot.battery_voltage, 2)))
					found_object=None
					custom_objects=[0]
					raise asyncio.CancelledError()
				except asyncio.TimeoutError:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: did not find charger, try again, battery %s" % str(round(robot.battery_voltage, 2)))
				if found_object.is_visible==False:
					raise asyncio.CancelledError()
			await robot.wait_for_all_actions_completed()
			if charger == None and robot.world.charger == None:
				counter+=1
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: chargermarker goto retry: "+str(counter))
			if counter > 1:
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: chargermarker goto failed, resetting, battery %s" % str(round(robot.battery_voltage, 2)))
				found_object=None
				custom_objects=[0]
				raise asyncio.CancelledError()
	found_object=None
	custom_objects=[0]
	robot.clear_idle_animation()
	robot.abort_all_actions(log_abort_messages=False)
	await asyncio.sleep(2)

## define look_for_chargermarker behaviour
async def find_chargermarker(robot: robot):
	global charger, freeplay, found_object, custom_objects, marker_time

	if robot.is_on_charger == 1:
		freeplay = 0
		robot.clear_idle_animation()
		robot.abort_all_actions(log_abort_messages=False)
		robot.enable_all_reaction_triggers(False)
		robot.world.disconnect_from_cubes()
		raise asyncio.CancelledError()
	end_time = time.time() + marker_time
	while str(custom_objects[0].object_type) != "CustomObjectTypes.CustomType01":
		try:
			custom_objects = await robot.world.wait_until_observe_num_objects(num=1, object_type = CustomObject, timeout=30.2, include_existing=True)
		except asyncio.CancelledError or asyncio.TimeoutError or time.time() > end_time or charger != None:
			#os.system('cls' if os.name == 'nt' else 'clear')
			print("State: chargermarker routine cancelled, battery %s" % str(round(robot.battery_voltage, 2)))
			custom_objects[0]=None
			if charger != None:
				break
			raise
		finally:
			await asyncio.sleep(0.1)
			if custom_objects != None and str(custom_objects[0].object_type) == "CustomObjectTypes.CustomType01":
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: found chargermarker in lookaround, battery %s" % str(round(robot.battery_voltage, 2)))
				found_object=custom_objects[0]
				robot.abort_all_actions(log_abort_messages=False)
				await asyncio.sleep(0.1)
				break
			if time.time() > end_time:
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: unable to find chargermarker in lookaround, battery %s" % str(round(robot.battery_voltage, 2)))
				break
			if charger != None:
				break
		custom_objects[0]=None
	for r in asyncio.all_tasks():
		r.cancel()
	await asyncio.sleep(0.1)
	raise asyncio.CancelledError()

## define freeplay_bahaviour
async def freeplay_lookaround_behaviour(robot: robot):
	global charger, freeplay

	if robot.is_on_charger == 1:
		freeplay = 0
		robot.clear_idle_animation()
		robot.abort_all_actions(log_abort_messages=False)
		robot.enable_all_reaction_triggers(False)
		robot.world.disconnect_from_cubes()
		raise asyncio.CancelledError()
	#try freeplay for 90 seconds, if found charger finally stop freeplay
	try:
		charger = await robot.world.wait_for_observed_charger(timeout=90, include_existing=True)
		#os.system('cls' if os.name == 'nt' else 'clear')
		print("State: found the charger in 90seconds playtime, battery %s" % str(round(robot.battery_voltage, 2)))
		for r in asyncio.all_tasks():
			r.cancel()
		raise
	except asyncio.TimeoutError:
		#os.system('cls' if os.name == 'nt' else 'clear')
		print("State: charger not found after 90sec fallback, battery %s" % str(round(robot.battery_voltage, 2)))
		await robot.play_anim_trigger(Triggers.CodeLabUnhappy, ignore_body_track=True).wait_for_completed()
		#await asyncio.sleep(2)
		await robot.set_head_angle(degrees(0)).wait_for_completed()
		raise
	except asyncio.CancelledError:
		#os.system('cls' if os.name == 'nt' else 'clear')
		print("State: freeplay fallback routine cancelled, battery %s" % str(round(robot.battery_voltage, 2)))
		raise
	finally:
		robot.clear_idle_animation()
		await asyncio.sleep(0.5)
		raise

## define lookaround_behaviour
async def lookaround_behaviour(robot: robot):
	global charger, freeplay, found_object, custom_objects

	if robot.is_on_charger == 1:
		freeplay = 0
		robot.clear_idle_animation()
		robot.abort_all_actions(log_abort_messages=False)
		robot.enable_all_reaction_triggers(False)
		robot.world.disconnect_from_cubes()
		raise asyncio.CancelledError()
	while robot.is_picked_up == True:
		#os.system('cls' if os.name == 'nt' else 'clear')
		print("State: robot is flipped on back, battery %s" % str(round(robot.battery_voltage, 2)))
		robot.enable_all_reaction_triggers(True)
		await asyncio.sleep(10)
	robot.enable_all_reaction_triggers(False)
	await robot.wait_for_all_actions_completed()
	try:
		charger = await robot.world.wait_for_observed_charger(timeout=30, include_existing=True)
		#os.system('cls' if os.name == 'nt' else 'clear')
		print("State: found charger in lookaround, battery %s" % str(round(robot.battery_voltage, 2)))
		for r in asyncio.all_tasks():
			r.cancel()
		raise
	except asyncio.TimeoutError:
		#os.system('cls' if os.name == 'nt' else 'clear')
		print("State: timedout in lookaround for charger, battery %s" % str(round(robot.battery_voltage, 2)))
		await robot.play_anim_trigger(Triggers.CodeLabUnhappy, ignore_body_track=True).wait_for_completed()
		await asyncio.sleep(2)
		await robot.set_head_angle(degrees(0), in_parallel=True).wait_for_completed()
		await robot.wait_for_all_actions_completed()
		raise
	except asyncio.CancelledError or str(custom_objects[0].object_type) == "CustomObjectTypes.CustomType01":
		#os.system('cls' if os.name == 'nt' else 'clear')
		print("State: lookaround routine cancelled, battery %s" % str(round(robot.battery_voltage, 2)))
		raise
	finally:
		# stop the behavior
		#os.system('cls' if os.name == 'nt' else 'clear')
		print("State: stop lookaround, battery %s" % str(round(robot.battery_voltage, 2)))
		robot.clear_idle_animation()
		await asyncio.sleep(0.5)
		raise

## define look for charger and goto routine
async def find_charger_and_goto(robot: robot):
	global charger, freeplay, found_object, custom_objects, temp_object, marker_time, lowbatvolt, scheduled_time
	# do we know where the charger is or not
	if not charger:
		# we will look around in place for the charger for 30 seconds
		#os.system('cls' if os.name == 'nt' else 'clear')
		print("State: look around for charger, battery %s" % str(round(robot.battery_voltage, 2)))
		robot.abort_all_actions(False)
		robot.clear_idle_animation()
		await robot.wait_for_all_actions_completed()
		await robot.play_anim_trigger(Triggers.SparkIdle, ignore_body_track=True).wait_for_completed()
		await asyncio.sleep(2)
		#await robot.wait_for_all_actions_completed()
		await robot.set_head_angle(degrees(0)).wait_for_completed()
		robot.move_lift(-3)
		marker_time=30.0
		#robot.start_behavior(cozmo.robot.behavior.BehaviorTypes.LookAroundInPlace)
		robot.start_behavior(BehaviorTypes.LookAroundInPlace)
		try:
			await gather(
				create_task(
				lookaround_behaviour(robot)),
				create_task(
				find_chargermarker(robot)),
				return_exceptions=True
			)
		except asyncio.CancelledError:
			pass
		robot.start_behavior(BehaviorTypes.LookAroundInPlace).stop()
		await asyncio.sleep(3)
		#os.system('cls' if os.name == 'nt' else 'clear')
		print("State: look around stopped, battery %s" % str(round(robot.battery_voltage, 2)))
		robot.clear_idle_animation()
		await robot.wait_for_all_actions_completed()
		#os.system('cls' if os.name == 'nt' else 'clear')
		print("State: waited for all actions completed, battery %s" % str(round(robot.battery_voltage, 2)))
		await asyncio.sleep(2)
		robot.abort_all_actions(False)
		#os.system('cls' if os.name == 'nt' else 'clear')
		print("State: aborted all actions, battery %s" % str(round(robot.battery_voltage, 2)))
	if found_object != None and charger==None:
		try:
			await goto_chargermarker_pose(robot)
		except asyncio.CancelledError:
			pass
	# Charger location and docking handling here
	if charger:
		#os.system('cls' if os.name == 'nt' else 'clear')
		print("State: docking mode, moving to charger, battery %s" % str(round(robot.battery_voltage, 2)))
		while (robot.is_on_charger == 0):
			# check to make sure we didn't get here from a battery spike
			if (robot.battery_voltage > lowbatvolt + 0.03) and (scheduled_time == 1):
				raise asyncio.CancelledError()
				#break
			# Yes! Attempt to drive near to the charger, and then stop.
			robot.clear_idle_animation()
			await robot.wait_for_all_actions_completed()
			await robot.play_anim_trigger(Triggers.CodeLabChatty, ignore_body_track=True, ignore_head_track=True).wait_for_completed()
			await asyncio.sleep(1)
			await robot.wait_for_all_actions_completed()
			robot.move_lift(-3)
			await robot.set_head_angle(degrees(0)).wait_for_completed()
			# If you are running Cozmo on carpet, try turning these num_retries up to 4 or 5
			try:
				action = robot.go_to_object(charger, distance_mm(160), RobotAlignmentTypes.LiftPlate, num_retries=3)
				await action.wait_for_completed()
			finally:
				pass
			try:
				action = robot.go_to_object(charger, distance_mm(100), RobotAlignmentTypes.LiftPlate, num_retries=3)
				await action.wait_for_completed()
			finally:
				pass
			try:
				action = robot.go_to_object(charger, distance_mm(80), RobotAlignmentTypes.LiftPlate, num_retries=3)
				await action.wait_for_completed()
			finally:
				pass
			try:
				action = robot.go_to_object(charger, distance_mm(60), RobotAlignmentTypes.LiftPlate, num_retries=3)
				await action.wait_for_completed()
			finally:
				pass
			#os.system('cls' if os.name == 'nt' else 'clear')
			print("State: straighten out, backup, and reposition, battery %s" % str(round(robot.battery_voltage, 2)))
			try:
				await robot.turn_in_place(degrees(charger.pose.rotation.angle_z.degrees), num_retries=3, accel=degrees(80), angle_tolerance=None, is_absolute=True).wait_for_completed()
			finally:
				pass
			try:
				await robot.drive_straight(distance_mm(-70), speed_mmps(40)).wait_for_completed()
			finally:
				pass
			try:
				action = robot.go_to_object(charger, distance_mm(100), RobotAlignmentTypes.LiftPlate, num_retries=3)
				await action.wait_for_completed()
			finally:
				pass
			try:
				action = robot.go_to_object(charger, distance_mm(60), RobotAlignmentTypes.LiftPlate, num_retries=3)
				await action.wait_for_completed()
			finally:
				pass
			try:
				action = robot.go_to_object(charger, distance_mm(40), RobotAlignmentTypes.LiftPlate, num_retries=3)
				await action.wait_for_completed()
			finally:
				pass
			# we should be right in front of the charger, can we see it?
			await asyncio.sleep(1)
			if (charger.is_visible == False):
				#we know where the charger is
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: can't see charger, position is still known, battery %s" % str(round(robot.battery_voltage, 2)))
				await robot.play_anim_trigger(Triggers.CodeLabSurprise, ignore_body_track=True, ignore_head_track=True).wait_for_completed()
				await asyncio.sleep(1)
				await robot.wait_for_all_actions_completed()
				await robot.set_head_angle(degrees(0)).wait_for_completed()
				await robot.turn_in_place(degrees(charger.pose.rotation.angle_z.degrees), accel=degrees(80), angle_tolerance=None, is_absolute=True).wait_for_completed()
				if (charger.is_visible == False):
					# we don't know where the charger is anymore
					charger = None
					robot.world.charger = None
					found_object = None
					custom_objects = [0]
					temp_object = None
					await robot.play_anim_trigger(Triggers.ReactToPokeReaction, ignore_body_track=True, ignore_head_track=True, ignore_lift_track=True).wait_for_completed()
					await asyncio.sleep(1)
					await robot.wait_for_all_actions_completed()
					await robot.drive_straight(distance_mm(-70), speed_mmps(50)).wait_for_completed()
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: charger not found, clearing charger map location. battery %s" % str(round(robot.battery_voltage, 2)))
					await asyncio.sleep(1)
					break
				try:
					action = robot.go_to_object(charger, distance_mm(110), RobotAlignmentTypes.LiftPlate, num_retries=3)
					await action.wait_for_completed()
				finally:
					pass
				try:
					action = robot.go_to_object(charger, distance_mm(80), RobotAlignmentTypes.LiftPlate, num_retries=3)
					await action.wait_for_completed()
				finally:
					pass
				await robot.turn_in_place(degrees(charger.pose.rotation.angle_z.degrees), accel=degrees(80), angle_tolerance=None, is_absolute=True).wait_for_completed()
			i = random.randint(1, 100)
			if i >= 85:
				await robot.play_anim_trigger(Triggers.FeedingReactToShake_Normal, ignore_body_track=True, ignore_head_track=True).wait_for_completed()
				await asyncio.sleep(2)
				await robot.wait_for_all_actions_completed()
			# Now in position. Turn around and drive backwards
			#os.system('cls' if os.name == 'nt' else 'clear')
			print("State: docking, battery %s" % str(round(robot.battery_voltage, 2)))
			await asyncio.sleep(2.5)
			if robot.is_animating:
				robot.clear_idle_animation()
				robot.abort_all_actions(log_abort_messages=True)
				await robot.wait_for_all_actions_completed()
			await robot.wait_for_all_actions_completed()
			await robot.turn_in_place(degrees(charger.pose.rotation.angle_z.degrees - 180), accel=degrees(100), angle_tolerance=None, is_absolute=True).wait_for_completed()
			await robot.wait_for_all_actions_completed()
			await asyncio.sleep(0.1)
			await robot.play_anim_trigger(cozmo.anim.Triggers.CubePounceFake, ignore_body_track=True, ignore_lift_track=True, ignore_head_track=True).wait_for_completed()
			await robot.set_head_angle(degrees(0)).wait_for_completed()
			await robot.wait_for_all_actions_completed()
			#robot.clear_idle_animation()
			await asyncio.sleep(1)
			backup_count = 0
			while robot.is_on_charger == 0:
				try:
					await robot.backup_onto_charger(max_drive_time=2)
					backup_count+=1
					await asyncio.sleep(0.4)
					if robot.is_on_charger == 1:
						#os.system('cls' if os.name == 'nt' else 'clear')
						print("State: Robot is on Charger, battery %s" % str(round(robot.battery_voltage, 2)))
						robot.enable_all_reaction_triggers(False)
						break
					elif backup_count == 6:
						robot.enable_all_reaction_triggers(False)
						break
				except robot.is_on_charger == 1:
					robot.stop_all_motors()
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: Contact! Stop all motors, battery %s" % str(round(robot.battery_voltage, 2)))
				await robot.wait_for_all_actions_completed()
			await robot.wait_for_all_actions_completed()
			# check if we're now docked
			if robot.is_on_charger:
				# Yes! we're docked!
				await robot.wait_for_all_actions_completed()
				await robot.play_anim("anim_sparking_success_02").wait_for_completed()
				await robot.wait_for_all_actions_completed()
				await robot.set_head_angle(degrees(0)).wait_for_completed()
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: I am now docked, battery %s" % str(round(robot.battery_voltage, 2)))
				robot.set_all_backpack_lights(cozmo.lights.off_light)
				await robot.play_anim("anim_gotosleep_getin_01").wait_for_completed()
				await robot.play_anim("anim_gotosleep_sleeping_01").wait_for_completed()
			else:
				# No, we missed. Drive forward, turn around, and try again
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: failed to dock with charger, battery %s" % str(round(robot.battery_voltage, 2)))
				await robot.wait_for_all_actions_completed()
				await robot.play_anim_trigger(Triggers.AskToBeRightedRight, ignore_body_track=True).wait_for_completed()
				await robot.wait_for_all_actions_completed()
				#robot.move_lift(-3)
				#await robot.set_head_angle(degrees(0)).wait_for_completed()
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: drive forward, turn around, and try again, battery %s" % str(round(robot.battery_voltage, 2)))
				await robot.turn_in_place(degrees(charger.pose.rotation.angle_z.degrees-180), accel=degrees(80), angle_tolerance=None, is_absolute=True).wait_for_completed()
				await robot.drive_straight(distance_mm(90), speed_mmps(90)).wait_for_completed()
				await robot.drive_straight(distance_mm(90), speed_mmps(90)).wait_for_completed()
				await robot.turn_in_place(degrees(charger.pose.rotation.angle_z.degrees), num_retries=3, accel=degrees(100), angle_tolerance=None, is_absolute=True).wait_for_completed()
				await robot.set_head_angle(degrees(0)).wait_for_completed()
				await asyncio.sleep(1)
				if (charger.is_visible == False):
					# we know where the charger is
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: can't see charger after turnaround, try again, battery %s" % str(round(robot.battery_voltage, 2)))
					await robot.play_anim_trigger(Triggers.CodeLabSurprise, ignore_body_track=True, ignore_head_track=True).wait_for_completed()
					#await robot.wait_for_all_actions_completed()
					await robot.set_head_angle(degrees(0)).wait_for_completed()
					await asyncio.sleep(0.1)
					#os.system('cls' if os.name == 'nt' else 'clear')
					print (charger)
					try:
						action = robot.go_to_object(charger, distance_mm(110), RobotAlignmentTypes.LiftPlate, num_retries=3)
						await action.wait_for_completed()
					finally:
						pass
					try:
						action = robot.go_to_object(charger, distance_mm(80), RobotAlignmentTypes.LiftPlate, num_retries=3)
						await action.wait_for_completed()
					finally:
						pass
					await robot.turn_in_place(degrees(charger.pose.rotation.angle_z.degrees), num_retries=3, accel=degrees(80), angle_tolerance=None, is_absolute=True).wait_for_completed()
					if (charger.is_visible == False):
						# we lost the charger, clearing all map variables
						charger = None
						robot.world.charger = None
						found_object = None
						custom_objects = [0]
						temp_object = None
						await robot.play_anim_trigger(Triggers.ReactToPokeReaction, ignore_body_track=True, ignore_head_track=True, ignore_lift_track=True).wait_for_completed()
						#await robot.wait_for_all_actions_completed()
						await robot.drive_straight(distance_mm(-100), speed_mmps(50)).wait_for_completed()
						#os.system('cls' if os.name == 'nt' else 'clear')
						print("State: charger lost while docking, clearing map. battery %s" % str(round(robot.battery_voltage, 2)))
						await asyncio.sleep(1)
						break
	else:
	# we have not managed to find the charger. Falling back to freeplay.
		charger = None
		#await robot.wait_for_all_actions_completed()
		await robot.play_anim_trigger(Triggers.ReactToPokeReaction, ignore_body_track=True, ignore_head_track=True, ignore_lift_track=True).wait_for_completed()
		#await robot.wait_for_all_actions_completed()
		#os.system('cls' if os.name == 'nt' else 'clear')
		print("State: charger not found, fallback to 90seconds of freeplay, battery %s" % str(round(robot.battery_voltage, 2)))
		#try freeplay for 90 seconds, if found charger finally stop freeplay
		marker_time=90.0
		robot.enable_all_reaction_triggers(True)
		robot.start_freeplay_behaviors()
		try:
			await gather(
				create_task(
				freeplay_lookaround_behaviour(robot)),
				create_task(
				find_chargermarker(robot)),
				return_exceptions=True
			)
		except asyncio.CancelledError:
			pass
		robot.stop_freeplay_behaviors()
		if found_object != None and charger==None:
			try:
				await goto_chargermarker_pose(robot)
			except asyncio.CancelledError:
				pass
		robot.move_lift(-3)
		robot.enable_all_reaction_triggers(False)
		#after 90 seconds end freeplay
#
# Cozmo's Scheduler resting time
#
async def cozmo_resting(robot: robot):
	if (robot.is_on_charger == 1) and (robot.is_charging == 1):
		# In here we make Cozmo do on or off Charger things while Charging for fun
		#os.system('cls' if os.name == 'nt' else 'clear')
		print("State: charging, waiting for scheduled playtime, battery %s" % str(round(robot.battery_voltage, 2)))
		i = random.randint(1, 100)
		if i >= 97:
			await robot.play_anim("anim_guarddog_fakeout_02").wait_for_completed()
		elif i >= 85:
			await robot.play_anim("anim_gotosleep_sleeploop_01").wait_for_completed()
		await asyncio.sleep(3)
		robot.set_all_backpack_lights(cozmo.lights.green_light)
		await asyncio.sleep(3)
		robot.set_all_backpack_lights(cozmo.lights.off_light)
	elif (robot.is_on_charger == 1) and (robot.is_charging == 0):
		# In here we make Cozmo do on or off Charger things while Charged for fun
		#os.system('cls' if os.name == 'nt' else 'clear')
		print("State: Charged! waiting for scheduled playtime, battery %s" % str(round(robot.battery_voltage, 2)))
		i = random.randint(1, 100)
		if i >= 97:
			await robot.play_anim("anim_guarddog_fakeout_02").wait_for_completed()
		elif i >= 85:
			await robot.play_anim("anim_gotosleep_sleeploop_01").wait_for_completed()
		await asyncio.sleep(3)
		robot.set_all_backpack_lights(cozmo.lights.green_light)
		await asyncio.sleep(3)
		robot.set_all_backpack_lights(cozmo.lights.off_light)
	elif (robot.is_on_charger == 0) and (robot.is_charging == 0) and scheduled_days == "Resting":
		robot.stop_freeplay_behaviors()
		await find_charger_and_goto(robot)
#
# Scheduler
#
async def scheduler(robot: robot):
	global use_scheduler, nowtime, wday, scheduled_days, scheduled_time
	global wkDS, wkDSm, wkDE, wkDEm, wkNS, wkNSm, wkNE, wkNEm, wkEDS, wkEDSm, wkEDE, wkEDEm, wkENS, wkENSm, wkENE, wkENEm
	wday = nowtime.tm_wday # 0 is Monday, 6 is Sunday
	#TempTime = datetime.datetime.now().timetuple()
	
	# Display Time Tuple for scripting usage purposes
	#os.system('cls' if os.name == 'nt' else 'clear')
	print("State: Full timetuple() is: "+str(nowtime))
	print("State: Week Day Number is: "+str(wday))
	while True:
		#os.system('cls' if os.name == 'nt' else 'clear')
		print("State: Scheduled days: "+str(scheduled_days)+", battery %s" % str(round(robot.battery_voltage, 2)))
		#weekday mornings
		if (wday < 5 and nowtime.tm_hour > wkDS or wday < 5 and (wkDE < wkDS and nowtime.tm_hour > wkDS or nowtime.tm_hour == wkDS and nowtime.tm_min >= wkDSm and nowtime.tm_sec >= 10)) and (nowtime.tm_hour < wkDE or wkDE < wkDS and nowtime.tm_hour > wkDE or nowtime.tm_hour == wkDE and nowtime.tm_min <= wkDEm and nowtime.tm_sec <= 10):
			scheduled_days = "WeekDayMorn"
			scheduled_time = 1
			#os.system('cls' if os.name == 'nt' else 'clear')
			print("State: Weekday Morning Time is: "+str(nowtime.tm_hour)+":"+str(nowtime.tm_min)+", battery %s" % str(round(robot.battery_voltage, 2)))
			await cozmo_unleashed(robot)
			#os.system('cls' if os.name == 'nt' else 'clear')
			print("State: weekday scheduled loop complete, battery %s" % str(round(robot.battery_voltage, 2)))
			break
		#weekday evenings
		elif (wday < 5 and nowtime.tm_hour > wkNS or wday < 5 and (wkNE < wkNS and nowtime.tm_hour > wkNS or nowtime.tm_hour == wkNS and nowtime.tm_min >= wkNSm and nowtime.tm_sec >= 10)) and (nowtime.tm_hour < wkNE or wkNE < wkNS and nowtime.tm_hour > wkNE or nowtime.tm_hour == wkNE and nowtime.tm_min <= wkNEm and nowtime.tm_sec <= 10):
			scheduled_days = "WeekDayEve"
			scheduled_time = 1
			#os.system('cls' if os.name == 'nt' else 'clear')
			print("State: Weekday Night Time is: "+str(nowtime.tm_hour)+":"+str(nowtime.tm_min)+", battery %s" % str(round(robot.battery_voltage, 2)))
			await cozmo_unleashed(robot)
			#os.system('cls' if os.name == 'nt' else 'clear')
			print("State: weeknight scheduled loop complete, battery %s" % str(round(robot.battery_voltage, 2)))
			break
		#weekend mornings
		elif (wday >= 5 and nowtime.tm_hour > wkEDS or wday >= 5 and (wkEDS < wkEDE and nowtime.tm_hour > wkEDS or nowtime.tm_hour == wkEDS and nowtime.tm_min >= wkEDSm and nowtime.tm_sec >= 10)) and (nowtime.tm_hour < wkEDE or wkEDE < wkEDS and nowtime.tm_hour > wkEDE or nowtime.tm_hour == wkEDE and nowtime.tm_min <= wkEDEm and nowtime.tm_sec <= 10):
			scheduled_days = "WeekEndMorn"
			scheduled_time = 1
			#os.system('cls' if os.name == 'nt' else 'clear')
			print("State: Weekend Morning Time is: "+str(nowtime.tm_hour)+":"+str(nowtime.tm_min)+", battery %s" % str(round(robot.battery_voltage, 2)))
			await cozmo_unleashed(robot)
			#os.system('cls' if os.name == 'nt' else 'clear')
			print("State: weekend scheduled loop complete, battery %s" % str(round(robot.battery_voltage, 2)))
			break
		#weekend evenings
		elif (wday >= 5 and nowtime.tm_hour > wkENS or wday >= 5 and (wkENS < wkENE and nowtime.tm_hour > wkENS or nowtime.tm_hour == wkENS and nowtime.tm_min >= wkENSm and nowtime.tm_sec >= 10)) and (nowtime.tm_hour < wkENE or wkENE < wkENS and nowtime.tm_hour > wkENE or nowtime.tm_hour == wkENE and nowtime.tm_min <= wkENEm and nowtime.tm_sec <= 10):
			scheduled_days = "WeekEndEve"
			scheduled_time = 1
			#os.system('cls' if os.name == 'nt' else 'clear')
			print("State: Weekend Evening Time is: "+str(nowtime.tm_hour)+":"+str(nowtime.tm_min)+", battery %s" % str(round(robot.battery_voltage, 2)))
			await cozmo_unleashed(robot)
			#os.system('cls' if os.name == 'nt' else 'clear')
			print("State: weekend scheduled loop complete, battery %s" % str(round(robot.battery_voltage, 2)))
			break
		else:
			nowtime = datetime.datetime.now().timetuple()
			scheduled_days = "Resting"
			scheduled_time = 0
			await cozmo_resting(robot)
			#os.system('cls' if os.name == 'nt' else 'clear')
			print("State: resting loop complete, battery %s" % str(round(robot.battery_voltage, 2)))
			break
#
#
# main program
async def cozmo_unleashed(robot: robot):
	global charger, freeplay, robotvolume, found_object, custom_objects, temp_object, marker_time, use_walls, use_cubes
	global use_scheduler, nowtime, wday, scheduled_days, scheduled_time
	if use_scheduler == 1:
		global wkDS, wkDSm, wkDE, wkDEm, wkNS, wkNSm, wkNE, wkNEm, wkEDS, wkEDSm, wkEDE, wkEDEm, wkENS, wkENSm, wkENE, wkENEm
	if scheduled_days=="None" or use_scheduler == 0:
		#
		# DEFINING MARKERS
		#
		# 1st 2 numbers are the width/height of the paper the printed marker is on
		# for the 1st dimension: measure the side of the width/height, from the printed marker's edge, then
		# multiply it by 2 then add it to the 2nd dimension
		# 2nd 2 numbers are the width/height of the printed marker on the paper
		# I suggest using a ruler to measure these dimensions, by the millimeter, after you print & cut them to get exact numbers

		# define the chargermarker for the dock
		await robot.world.define_custom_wall(CustomObjectTypes.CustomType01, CustomObjectMarkers.Hexagons2, 62, 62, 60, 60, True)

		# these define the 4 walls of my play field, it helps Cozmo not bump into the walls
		# you can set the use_walls variable at the top of the script to 0 if you are not using walls
		if use_walls >= 1:
			await robot.world.define_custom_wall(CustomObjectTypes.CustomType02, CustomObjectMarkers.Diamonds2, 500, 50, 40, 40, True)
			await robot.world.define_custom_wall(CustomObjectTypes.CustomType03, CustomObjectMarkers.Hexagons5, 700, 50, 30, 30, True)
			await robot.world.define_custom_wall(CustomObjectTypes.CustomType04, CustomObjectMarkers.Diamonds4, 700, 50, 40, 40, True)
			await robot.world.define_custom_wall(CustomObjectTypes.CustomType05, CustomObjectMarkers.Diamonds5, 500, 50, 40, 40, True)
			await robot.world.define_custom_box(CustomObjectTypes.CustomType07,
                                            CustomObjectMarkers.Hexagons3,  # front
                                            CustomObjectMarkers.Circles3,   # back
                                            CustomObjectMarkers.Circles4,   # top
                                            CustomObjectMarkers.Circles5,   # bottom
                                            CustomObjectMarkers.Triangles2, # left
                                            CustomObjectMarkers.Triangles3, # right
                                            50, 50, 50,
                                            30, 30, True)

		robot.world.charger = None
		charger = None
		found_object = None
		temp_object = None
		custom_objects=[]
		if use_scheduler == 1:
			nowtime = datetime.datetime.now().timetuple()
		await robot.wait_for_all_actions_completed()
		robot.clear_idle_animation()
		robot.stop_all_motors()
		robot.abort_all_actions(log_abort_messages=True)
		robot.enable_all_reaction_triggers(False)
		robot.enable_stop_on_cliff(True)
		robot.world.auto_disconnect_from_cubes_at_end(True)
		robot.set_robot_volume(robotvolume)
		await asyncio.sleep(1)
		if use_cubes >= 2:
			robot.enable_freeplay_cube_lights(enable=True)
	while True:
#State 1: on charger, charging
		if (robot.is_on_charger == 1) and (robot.is_charging == 1):
			#if scheduled_time != None:
			#	#os.system('cls' if os.name == 'nt' else 'clear')
			#	print("State: Scheduled Time Flag is: "+str(scheduled_time))
			freeplay=0
			if scheduled_time == 1:
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: charging, in scheduled playtime, battery %s" % str(round(robot.battery_voltage, 2)))
			else:
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: charging, battery %s" % str(round(robot.battery_voltage, 2)))
			i = random.randint(1, 100)
			if i >= 97:
				await robot.play_anim("anim_guarddog_fakeout_02").wait_for_completed()
			elif i >= 85:
				await robot.play_anim("anim_gotosleep_sleeploop_01").wait_for_completed()
			await asyncio.sleep(3)
			robot.set_all_backpack_lights(cozmo.lights.green_light)
			await asyncio.sleep(3)
			robot.set_all_backpack_lights(cozmo.lights.off_light)
#State 2: on charger, fully charged, get off charger
		if (robot.is_on_charger == 1) and (robot.is_charging == 0) and (scheduled_days != "Resting") and (scheduled_time == 1 or use_scheduler == 0):
			#os.system('cls' if os.name == 'nt' else 'clear')
			print("State: Charged! getting off charger, battery %s" % str(round(robot.battery_voltage, 2)))
			robot.set_all_backpack_lights(cozmo.lights.off_light)
			await robot.play_anim("anim_launch_altwakeup_01").wait_for_completed()
			await asyncio.sleep(4)
			robot.clear_idle_animation()
			await robot.drive_off_charger_contacts(num_retries=3, in_parallel=False).wait_for_completed()
			await asyncio.sleep(4)
			robot.move_lift(-3)
			try:
				if (robot.is_on_charger == 1):
					await robot.drive_straight(distance_mm(80), speed_mmps(25), num_retries=2).wait_for_completed()
			finally:
				pass
			await asyncio.sleep(2)
			await robot.wait_for_all_actions_completed()
		elif use_scheduler == 1 and scheduled_days == "None":
			await scheduler(robot)
#State 3: not on charger, good time play battery | default low battery is 3.65
		if (robot.battery_voltage > lowbatvolt) and (robot.is_on_charger == 0) and (scheduled_time == 1 or use_scheduler == 0):
			#if scheduled_time != None:
			#	#os.system('cls' if os.name == 'nt' else 'clear')
			#	print("State: Scheduled Time Flag is: "+str(scheduled_time))
			if use_scheduler == 1 and scheduled_days == "None":
				await scheduler(robot)
			elif freeplay == 0:
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: turn on good time play battery %s" % str(round(robot.battery_voltage, 2)))
				robot.clear_idle_animation()
				robot.abort_all_actions(log_abort_messages=False)
				if use_cubes == 1:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: turn on cubes %s" % str(round(robot.battery_voltage, 2)))
					await robot.world.connect_to_cubes()
					await asyncio.sleep(4)
				elif use_cubes >= 2:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: turn on cubes and freeplay lights %s" % str(round(robot.battery_voltage, 2)))
					robot.enable_freeplay_cube_lights(True)
					await robot.world.connect_to_cubes()
					await asyncio.sleep(4)
				await robot.wait_for_all_actions_completed()
				robot.enable_all_reaction_triggers(True)
				robot.start_freeplay_behaviors()
				freeplay=1
			elif freeplay == 1 and robot.battery_voltage > lowbatvolt - 0.03:
				pass
			if robot.is_picked_up == True:
				charger = None
				robot.world.charger = None
				temp_object = None
				found_object = None
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: robot delocalized during freeplay, resetting everything, battery %s" % str(round(robot.battery_voltage, 2)))
			#os.system('cls' if os.name == 'nt' else 'clear')
			print("State: good battery playtime, battery %s" % str(round(robot.battery_voltage, 2)))
			await asyncio.sleep(3)
#State 4: not on charger, low battery | default low battery is 3.65
		if (robot.battery_voltage <= lowbatvolt) and (robot.is_on_charger == 0):
			if freeplay == 1:
				robot.stop_freeplay_behaviors()
				robot.clear_idle_animation()
				robot.enable_all_reaction_triggers(False)
				robot.abort_all_actions(log_abort_messages=False)
				await robot.wait_for_all_actions_completed()
				if use_cubes == 1 or use_cubes == 3:
					await robot.world.disconnect_from_cubes()
					await asyncio.sleep(4)
				elif use_cubes == 2:
					robot.enable_freeplay_cube_lights(False)
					await robot.world.disconnect_from_cubes()
					await asyncio.sleep(4)
				await robot.wait_for_all_actions_completed()
				freeplay=0
				await robot.play_anim_trigger(Triggers.NeedsMildLowEnergyRequest, ignore_body_track=True).wait_for_completed()
				await asyncio.sleep(2)
				await robot.wait_for_all_actions_completed()
				robot.set_all_backpack_lights(cozmo.lights.blue_light)
				await robot.set_head_angle(degrees(0)).wait_for_completed()
				robot.move_lift(-3)
				robot.set_idle_animation(Triggers.NeedsMildLowEnergyRequest)
				#await robot.drive_straight(distance_mm(-30), speed_mmps(50)).wait_for_completed()
			#os.system('cls' if os.name == 'nt' else 'clear')
			print("State: low battery, finding charger, battery %s" % str(round(robot.battery_voltage, 2)))
			# charger location search
			# see if we already know where the charger is
			if charger != None:
				#we know where the charger is
				robot.move_lift(-3)
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: start docking loop, charger position known, battery %s" % str(round(robot.battery_voltage, 2)))
				await robot.play_anim_trigger(Triggers.CodeLabSurprise, ignore_body_track=True, ignore_head_track=True).wait_for_completed()
				await asyncio.sleep(2)
				#await robot.wait_for_all_actions_completed()
				await robot.set_head_angle(degrees(0)).wait_for_completed()
				await robot.wait_for_all_actions_completed()
				#charger = robot.world.charger
				#os.system('cls' if os.name == 'nt' else 'clear')
				print (charger)
				try:
					action = robot.go_to_object(charger, distance_mm(110), RobotAlignmentTypes.LiftPlate, num_retries=3)
					await action.wait_for_completed()
				finally:
					pass
				try:
					action = robot.go_to_object(charger, distance_mm(80), RobotAlignmentTypes.LiftPlate, num_retries=3)
					await action.wait_for_completed()
				finally:
					pass
				await robot.turn_in_place(degrees(charger.pose.rotation.angle_z.degrees), num_retries=3, accel=degrees(80), angle_tolerance=None, is_absolute=True).wait_for_completed()
				await asyncio.sleep(0.5)
			elif found_object != None:
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: start of loop, chargermarker known, battery %s" % str(round(robot.battery_voltage, 2)))
					await robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabSurprise, ignore_body_track=True, ignore_head_track=True).wait_for_completed()
					await robot.set_head_angle(degrees(0)).wait_for_completed()
					await robot.wait_for_all_actions_completed()
					asyncio.sleep(0.01)
					try:
						await goto_chargermarker_pose(robot)
					except asyncio.CancelledError:
						pass
			else:
				# we know where the charger is but we have been delocalized
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: did not find charger after clearing map, battery %s" % str(round(robot.battery_voltage, 2)))
			## decide if we need to run find charger routines or not
			await find_charger_and_goto(robot)

		## end of loop routines
		if robot.is_picked_up == True:
			charger = None
			robot.world.charger = None
			temp_object = None
			found_object = None
			#os.system('cls' if os.name == 'nt' else 'clear')
			print("State: robot delocalized during freeplay, resetting charger, battery %s" % str(round(robot.battery_voltage, 2)))
		while temp_object == None:
			try:
				custom_objects = await robot.world.wait_until_observe_num_objects(num=1, object_type=CustomObject, timeout=1, include_existing=True)
				if len(custom_objects) > 0:
					temp_object = custom_objects[0]
					custom_objects = []
				if str(temp_object.object_type) != "CustomObjectTypes.CustomType01":
					temp_object = None
			finally:
				if temp_object != None and str(temp_object.object_type) == "CustomObjectTypes.CustomType01":
					if found_object == None:
						#os.system('cls' if os.name == 'nt' else 'clear')
						print("State: found chargermarker in freeplay, battery %s" % str(round(robot.battery_voltage, 2)))
						found_object = temp_object
						temp_object = None
						break
					if temp_object != None and found_object != None:
						if temp_object.pose.is_comparable(found_object.pose) == True:
							#os.system('cls' if os.name == 'nt' else 'clear')
							print("State: updating chargermarker location, battery %s" % str(round(robot.battery_voltage, 2)))
							found_object = temp_object
						else:
							#os.system('cls' if os.name == 'nt' else 'clear')
							print("State: chargermarker pose comparison failed, battery %s" % str(round(robot.battery_voltage, 2)))
				temp_object = None
				break
		if robot.world.charger != None:
			charger = robot.world.charger
			#os.system('cls' if os.name == 'nt' else 'clear')
			print("State: updating charger location, battery %s" % str(round(robot.battery_voltage, 2)))
			#os.system('cls' if os.name == 'nt' else 'clear')
			print("State: "+str(charger)+", battery %s" % str(round(robot.battery_voltage, 2)))
			robot.world.charger = None
		#os.system('cls' if os.name == 'nt' else 'clear')
		print("State: program loop complete, battery %s" % str(round(robot.battery_voltage, 2)))
		await asyncio.sleep(3)
		if use_scheduler == 1:
			nowtime = datetime.datetime.now().timetuple()
			if (scheduled_days == "WeekDayMorn" and (nowtime.tm_hour <= wkDS and nowtime.tm_min <= wkDSm) or (wkDE < wkDS and nowtime.tm_hour <= wkDS and nowtime.tm_min <= wkDSm)) or (scheduled_days == "WeekDayMorn" and (nowtime.tm_hour >= wkDE and nowtime.tm_min >= wkDEm) or (wkDE < wkDS and nowtime.tm_hour >= wkDE and nowtime.tm_min >= wkDEm)):
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: Weekday Morning Schedule, battery %s" % str(round(robot.battery_voltage, 2)))
				await scheduler(robot)
			elif (scheduled_days == "WeekDayEve" and (nowtime.tm_hour <= wkNS and nowtime.tm_min <= wkNSm) or (wkNE < wkNS and nowtime.tm_hour <= wkNS and nowtime.tm_min <= wkNSm)) or (scheduled_days == "WeekDayEve" and (nowtime.tm_hour >= wkNE and nowtime.tm_min >= wkNEm) or (wkNE < wkNS and nowtime.tm_hour >= wkNE and nowtime.tm_min >= wkNEm)):
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: Weekday Evening Schedule, battery %s" % str(round(robot.battery_voltage, 2)))
				await scheduler(robot)
			elif (scheduled_days == "WeekEndMorn" and (nowtime.tm_hour <= wkEDS and nowtime.tm_min <= wkEDSm) or (wkEDE < wkEDS and nowtime.tm_hour <= wkEDS and nowtime.tm_min <= wkEDSm)) or (scheduled_days == "WeekEndMorn" and (nowtime.tm_hour >= wkEDE and nowtime.tm_min >= wkEDEm) or (wkEDE < wkEDS and nowtime.tm_hour >= wkEDE and nowtime.tm_min >= wkEDEm)):
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: Weekend Schedule, battery %s" % str(round(robot.battery_voltage, 2)))
				await scheduler(robot)
			elif (scheduled_days == "WeekEndEve" and (nowtime.tm_hour <= wkENS and nowtime.tm_min <= wkENSm) or (wkENE < wkENS and nowtime.tm_hour <= wkENS and nowtime.tm_min <= wkENSm)) or (scheduled_days == "WeekEndEve" and (nowtime.tm_hour >= wkENE and nowtime.tm_min >= wkENEm) or (wkENE < wkENS and nowtime.tm_hour >= wkENE and nowtime.tm_min >= wkENEm)):
				#os.system('cls' if os.name == 'nt' else 'clear')
				print("State: Weekend Schedule, battery %s" % str(round(robot.battery_voltage, 2)))
				await scheduler(robot)
			elif scheduled_days == "Resting" and scheduled_time == 0:
				if use_cubes == 3:
					robot.enable_freeplay_cube_lights(enable=True)
				if robot.is_on_charger == 0:
					robot.stop_freeplay_behaviors()
					await asyncio.sleep(3)
					#os.system('cls' if os.name == 'nt' else 'clear')
					print("State: Resting Time Schedule, Find Charger, battery %s" % str(round(robot.battery_voltage, 2)))
					await find_charger_and_goto(robot)
				else:	
					await scheduler(robot)
		#if use_scheduler == 1:
		#	#os.system('cls' if os.name == 'nt' else 'clear')
		#	print("State: End of Loop, How did we get here?, battery %s" % str(round(robot.battery_voltage, 2)))
		#	break
#
#
# START THE SHOW!
#
#cozmo.robot.Robot.drive_off_charger_on_connect = False
#cozmo.run_program(cozmo_unleashed, use_viewer=True, force_viewer_on_top=True, show_viewer_controls=True, exit_on_connection_error=True)

# if you have freeglut in the same folder as this script you can change the above line to
#cozmo.run_program(cozmo_unleashed, use_viewer=True, use_3d_viewer=True, force_viewer_on_top=True, show_viewer_controls=True, exit_on_connection_error=True)
# which will give you remote control over Cozmo via WASD+QERF while the 3d window has focus

# --- Above ^^ is the common command for running the first def.
# --- Below -- is a script from acidzebra for loading the main program, that I will
# like to eventually use to turn into a SDK Loop that can stay running in an executed
# program so that if the WiFi disconnects & reconnects again, the SDK Loop will kick
# back in when it sees a phone with an open SDK connection again, without having to
# stop and restart the script manually.

#  Run at your own RISK, using the AbstractEventLoop is dangerous.

async def run(sdk_conn_loop):
	global robot
	'''The run method runs once the Cozmo SDK is connected.'''
	robot = await sdk_conn_loop.wait_for_robot(timeout=2)
	try:
		#await cozmo_unleashed(robot)
		# ^^ this above line ^^ is the original safest call to use

		# this connect_on_loop seems to work, though i don't think it actually reconnects
		# the phone to cozmo as i intended it to. i'm still working on that part
		# this AbstractEventLoop line might cause issues, use at your own risk
		#await connect_on_loop(AbstractEventLoop.run_forever(cozmo_unleashed(robot)), sdk_conn_loop)
		# this non-Abstract connect_on_loop is much safer, use this line below
		await cozmo.connect_on_loop(await cozmo_unleashed(robot), sdk_conn_loop)

	except KeyboardInterrupt as k:
		#os.system('cls' if os.name == 'nt' else 'clear')
		print("")
		#os.system('cls' if os.name == 'nt' else 'clear')
		print("Exit requested by user")
		SystemExit("Keyboard interrupt: %s" % k)


if __name__ == '__main__':
	cozmo.setup_basic_logging()
	cozmo.robot.Robot.drive_off_charger_on_connect = False  # Cozmo can stay on charger for now SIKE
	try:
		cozmo.connect_with_3dviewer(run, enable_camera_view=True, show_viewer_controls=False)
	except cozmo.ConnectionError as e:
		SystemExit("A connection error with viewer occurred: %s" % e)