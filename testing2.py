import cozmo
from cozmo.util import Pose, degrees, distance_mm, speed_mmps
import time

async def cozmo_program(robot: cozmo.robot.Robot):
    await robot.world.create_custom_fixed_object(Pose(100, 0, 0, angle_z=degrees(0)), 10, 100, 100, relative_to_robot=True)
    while True:
        await robot.drive_straight(distance_mm(-100), speed_mmps(500)).wait_for_completed()
        await robot.drive_straight(distance_mm(100), speed_mmps(500)).wait_for_completed()
        time.sleep(0.1)

cozmo.run_program(cozmo_program, use_3d_viewer=True, use_viewer=True)