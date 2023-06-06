#!/usr/bin/env python3

# Copyright (c) 2017 Anki, Inc.
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

'''This example demonstrates how you can define custom objects.

The example defines several custom objects (2 cubes, a wall and a box). When
Cozmo sees the markers for those objects he will report that he observed an
object of that size and shape there.

You can adjust the markers, marker sizes, and object sizes to fit whatever
object you have and the exact size of the markers that you print out.
'''

import time
import keyboard

import cozmo
from cozmo.objects import CustomObject, CustomObjectMarkers, CustomObjectTypes
from cozmo.util import Pose, degrees, distance_mm, speed_mmps

robot = cozmo.robot.Robot

global i
global a
global f
global stopped

def handle_object_observed(evt, **kw):
    if isinstance(evt.obj, CustomObject):
        object_pose = evt.obj.pose

def handle_object_disappeared(evt, **kw):
    # This will be called whenever an EvtObjectDisappeared is dispatched -
    # whenever an Object goes out of view.
    if isinstance(evt.obj, CustomObject):
        print("Cozmo stopped seeing a %s" % str(evt.obj.object_type))

def custom_objects(robot: robot):
    try:
        i = 0
        a = 0
        f = 0
        stopped = 0
        #robot.drive_straight(distance_mm(400), speed_mmps(400)).wait_for_completed
        
        async def handle_object_appeared(evt, **kw):
            nonlocal i
            nonlocal a
            nonlocal f
            nonlocal stopped
            # This will be called whenever an EvtObjectAppeared is dispatched -
            # whenever an Object comes into view.
            if isinstance(evt.obj, CustomObject) and evt.obj.object_type == CustomObjectTypes.CustomType01 and i == 0 :
                print("Cozmo started seeing a %s" % str(evt.obj.object_type))
                object_pose = evt.obj.pose
                print(CustomObject)
                await robot.go_to_pose(Pose(object_pose.position.x + 175, object_pose.position.y, 0, angle_z=object_pose.rotation.angle_z), relative_to_robot=False, num_retries=3).wait_for_completed()
                print(object_pose)
                i += 1
                await robot.set_head_angle(angle=degrees(-20)).wait_for_completed()
                await robot.set_lift_height(1).wait_for_completed()
                await robot.drive_wheels(-50, -50, 5000, 5000, duration=3)
                if stopped != 1:
                    i = 0
                    a = 0
                    f += 1
                    await robot.turn_in_place(degrees(175), angle_tolerance=degrees(1), speed=degrees(18)).wait_for_completed()
                
            elif isinstance(evt.obj, CustomObject) and evt.obj.object_type == CustomObjectTypes.CustomType02 and a == 0 and i == 1:
                robot.stop_all_motors()
                stopped = 1
                print("Cozmo started seeing a %s" % str(evt.obj.object_type))
                object_pose = evt.obj.pose
                print(object_pose)
                await robot.go_to_pose(Pose(object_pose.position.x, object_pose.position.y, 0, angle_z=degrees(180)), relative_to_robot=False, num_retries=3).wait_for_completed()
                await robot.turn_in_place(degrees(185), angle_tolerance=degrees(1), speed=degrees(18)).wait_for_completed()
                await robot.drive_straight(distance_mm(-200), speed_mmps(30)).wait_for_completed()
                a += 1
                if f < 3 and not robot.is_charging:
                    i = 0
                    a = 0
                    f += 1
                    await robot.drive_straight(distance_mm(300), speed_mmps(100)).wait_for_completed()
                    await robot.turn_in_place(degrees(180), angle_tolerance=degrees(1), speed=degrees(180)).wait_for_completed()

        # Add event handlers for whenever Cozmo sees a new object
        robot.add_event_handler(cozmo.objects.EvtObjectAppeared, handle_object_appeared)
        robot.add_event_handler(cozmo.objects.EvtObjectDisappeared, handle_object_disappeared)
        robot.add_event_handler(cozmo.objects.EvtObjectObserved, handle_object_observed)

        # with a 30mm x 30mm Diamonds2 image on every face
        charger_obj = robot.world.define_custom_wall(CustomObjectTypes.CustomType01, CustomObjectMarkers.Hexagons2, 62, 62, 60, 60, True)

        floor_obj = robot.world.define_custom_cube(CustomObjectTypes.CustomType02, CustomObjectMarkers.Diamonds3, 50, 50, 50, True)

        wall_obj = robot.world.define_custom_wall(CustomObjectTypes.CustomType03, CustomObjectMarkers.Diamonds5, 700, 50, 40, 40, True)
        wall2_obj = robot.world.define_custom_wall(CustomObjectTypes.CustomType04, CustomObjectMarkers.Hexagons5, 500, 50, 30, 30, True)
        wall3_obj = robot.world.define_custom_wall(CustomObjectTypes.CustomType05, CustomObjectMarkers.Diamonds4, 700, 50, 40, 40, True)
        wall4_obj = robot.world.define_custom_wall(CustomObjectTypes.CustomType06, CustomObjectMarkers.Diamonds2, 500, 50, 40, 40, True)

        box_obj = robot.world.define_custom_box(CustomObjectTypes.CustomType07,
                                            CustomObjectMarkers.Hexagons3,  # front
                                            CustomObjectMarkers.Circles3,   # back
                                            CustomObjectMarkers.Circles4,   # top
                                            CustomObjectMarkers.Circles5,   # bottom
                                            CustomObjectMarkers.Triangles2, # left
                                            CustomObjectMarkers.Triangles3, # right
                                            50, 50, 50,
                                            30, 30, True)

        print("Show the above markers to Cozmo and you will see the related objects "
            "annotated in Cozmo's view window, you will also see print messages "
            "everytime a custom object enters or exits Cozmo's view.")

        print("Press CTRL-C to quit")
        while True:
            try:
                time.sleep(0.1)
                if keyboard.is_pressed('x'):
                    print("success")
            except cozmo.ConnectionError as e:
                print("connection aborted", e)
    except cozmo.ConnectionError as e:
        print("no device found:", e)

cozmo.run_program(custom_objects, use_3d_viewer=True, use_viewer=True)