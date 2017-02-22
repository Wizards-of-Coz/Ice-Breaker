import cozmo
import asyncio
import Common.wochelper
from Common.woc import WOC
from cozmo.util import degrees, distance_mm, speed_mmps

MAX_HEAD_ANGLE = cozmo.robot.MAX_HEAD_ANGLE
MIN_HEAD_ANGLE = degrees(20)
ANGLE_EPSILON = degrees(0.5)
TURN_SPEED = 20
STRAIGHT_SPEED = 25
DISTANCE_HUMAN = 100
TURN_ANGLE_AFTER_INTERACTION = degrees(90)

class IceBreaker(WOC):
    theFace = None
    
    def __init__(self):
        self._isCompleted = False
        self._face = None

    async def run(self, coz_conn: cozmo.conn.CozmoConnection):
        await Common.wochelper.initFaceHandlers(coz_conn,
                                                self.onFaceObserved,
                                                self.onFaceAppeared,
                                                self.onFaceDisappeared)
        self._robot = await coz_conn.wait_for_robot()
        while True:
            if not self._face:
                await self.spin()
            else:
                await self.moveCloser()
                await self.coreInteraction()
                await self.afterInteraction()
            await asyncio.sleep(0.1)
        
    async def spin(self):
        # start spin
        if not self._robot.is_moving:
            await self._robot.drive_wheels(TURN_SPEED, -TURN_SPEED)

    async def moveCloser(self):
        # turn to human Cozmo saw
        # await self._robot.turn_towards_face(self._face).wait_for_completed()
        # move closer
        action1 = self._robot.drive_straight(distance_mm(DISTANCE_HUMAN),
                                             speed_mmps(STRAIGHT_SPEED),
                                             should_play_anim=False,
                                             in_parallel=True)
        action2 = self._robot.set_lift_height(0.0,
                                              accel=1.0,
                                              in_parallel=True)
        await action1.wait_for_completed()
        cozmo.logger.info("action1 = %s", action1)
        await action2.wait_for_completed()
        cozmo.logger.info("action2 = %s", action2)
        await asyncio.sleep(0.6)
        
    async def coreInteraction(self):
        await self._robot.say_text("What's your name?",
                                   use_cozmo_voice=False,
                                   in_parallel=True,
                                   duration_scalar=1.0).wait_for_completed()
        
    async def afterInteraction(self):
        await self._robot.drive_straight(distance_mm(-DISTANCE_HUMAN),
                                         speed_mmps(STRAIGHT_SPEED),
                                         should_play_anim=False).wait_for_completed()
        await self._robot.turn_in_place(TURN_ANGLE_AFTER_INTERACTION).wait_for_completed()
    
    async def onFaceObserved(self, evt: cozmo.faces.EvtFaceObserved, obj=None, **kwargs):
        if self._face and self._face == evt.face:
            pass

    async def onFaceAppeared(self, evt: cozmo.faces.EvtFaceAppeared, obj=None, **kwargs):
        if not self._face:
            self._face = evt.face
            self._robot.stop_all_motors()
            print("Find a face, start tracking")
        if not self.theFace:
            self.theFace = evt.face

    async def onFaceDisappeared(self, evt: cozmo.faces.EvtFaceDisappeared, obj=None, **kwargs):
        if self._face and self._face == evt.face:
            self._face = None
            print("Lose tracking face")


def main():
    ib = IceBreaker()
    cozmo.setup_basic_logging()
    cozmo.connect_with_tkviewer(ib.run)

if __name__ == '__main__':
    main()
