import cozmo
import asyncio
import Common.wochelper
import random
from Common.woc import WOC
from Common.wocmath import log_mapping
from cozmo.util import degrees, distance_mm, speed_mmps
from cozmo.lights import Light
from questions import Questions

# maximum head angle for looking up faces
MAX_HEAD_ANGLE = cozmo.robot.MAX_HEAD_ANGLE
# minimum head angle for looking up faces
MIN_HEAD_ANGLE = degrees(20)
# tiny gap to work around sharp maximum error
ANGLE_EPSILON = degrees(0.5)
TURN_SPEED = 20
STRAIGHT_SPEED = 25
# distance close up to human
DISTANCE_HUMAN = 80
TURN_ANGLE_AFTER_INTERACTION = degrees(90)

TURN_SPEED_FAST = 500
MIN_CRAZY_SPIN_TIME = 3.1
MAX_CRAZY_SPIN_TIME = 5.0

MIN_PITCH = -0.4
MAX_PITCH = -0.7

# duration: question length == 10, duration = 1, question length = 100, duration = 2
# in seconds
MIN_DURATION = 1
MAX_DURATION = 2

# flashing light when cube is ready to tap
CUBE_READY_LIGHT = cozmo.lights.blue_light.flash()

class IceBreaker(WOC):
    theFace = None
    
    def __init__(self):
        self._isCompleted = False
        self._face = None
        self._newRound = True
        self._questions = Questions()

    async def run(self, coz_conn: cozmo.conn.CozmoConnection):
        await Common.wochelper.initFaceHandlers(coz_conn,
                                                self.onFaceObserved,
                                                self.onFaceAppeared,
                                                self.onFaceDisappeared)
        self._robot = await coz_conn.wait_for_robot()
        self._initPose = self._robot.pose
        self._cube = None
        # start with the "next question button" cube placed in front of cozmo
        try:
            self._cube = await self._robot.world.wait_for_observed_light_cube(timeout=30)
            print("Found cube: %s" % self._cube)
        except asyncio.TimeoutError:
            print("Didn't find a cube")

        while True:
            if not self._face:
                # first spin fast, then spin slower to seek human face
                await self.crazySpin()
                await self.spin()
            else:
                # find a face, do interaction
                await self.moveCloser()
                await self.coreInteraction()
                await self.waitFinishInteraction()
                await self.afterInteraction()
            await asyncio.sleep(0.1)
        
    # spin to find any human face
    async def spin(self):
        # start spin
        if not self._robot.is_moving:
            # head up so that Cozmo can see faces
            spinAction = self._robot.set_head_angle(MAX_HEAD_ANGLE,
                                                 in_parallel=True)
            await self._robot.drive_wheels(-TURN_SPEED, TURN_SPEED)
            await spinAction.wait_for_completed()
            cozmo.logger.info("spinAction = %s", spinAction)

    # close up to human whose face is just seen by Cozmo
    async def moveCloser(self):
        # turn to human Cozmo saw
        await self._robot.turn_towards_face(self._face).wait_for_completed()
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
        
    # ask ice breaking question
    async def coreInteraction(self):
        self._question = self._questions.getRandomQuestion()
        (pitch, self._duration) = await self.customizeSpeech(self._question)
        print(self._question)
        print("pitch = %s, durationScalar = %s" % (pitch, self._duration))
        await self._robot.say_text(self._question,
                                   use_cozmo_voice=True,
                                   in_parallel=True,
                                   voice_pitch=pitch,
                                   duration_scalar=self._duration).wait_for_completed()

    # repeat question if repeating button is pressed
    async def repeatInteraction(self):
        pitch = random.uniform(MIN_PITCH, MAX_PITCH)
        await self._robot.say_text(self._question,
                                   use_cozmo_voice=True,
                                   in_parallel=True,
                                   voice_pitch=pitch,
                                   duration_scalar=self._duration).wait_for_completed()
    
    # use cubes to finish interaction with human
    async def waitFinishInteraction(self):
        finishConfirmed = False
        while not finishConfirmed:
            cube = None

            await self._robot.set_head_angle(degrees(0),
                                             in_parallel=True).wait_for_completed()
            await self._robot.play_anim_trigger(cozmo.anim.Triggers.MeetCozmoGetIn).wait_for_completed()
            
            # wait to see a cube
            try:
                cube = await self._robot.world.wait_for_observed_light_cube(timeout=30)
                print("Found cube: %s" % cube)
            except asyncio.TimeoutError:
                print("Didn't find a cube")
            finally:
                pass

            # found ANY cube
            if cube:
                # set cube flashing light
                cube.set_lights(CUBE_READY_LIGHT)
                # Cozmo being curious

                await self._robot.play_anim_trigger(cozmo.anim.Triggers.BlockReact).wait_for_completed()
                await asyncio.sleep(1)
                # finishConfirmed = True

                tapped = None

                # wait this cube to be tapped
                try:
                    tapped = await cube.wait_for_tap(timeout=30)
                    print("Cube tapped: %s" % tapped)
                except asyncio.TimeoutError:
                    print("Didn't tap the cube")

                if tapped:
                    # show the cube is tapped
                    cube.set_lights(cozmo.lights.green_light)
                    
                    # the tapped cube is the cube of "next question"
                    if cube == self._cube:
                        finishConfirmed = True
                        await self._robot.play_anim_trigger(cozmo.anim.Triggers.BuildPyramidSuccess).wait_for_completed()
                    # other cube
                    else:
                        await self.repeatInteraction()
                    cube.set_lights_off()
            else:
                # didn't find cube
                await self._robot.play_anim_trigger(cozmo.anim.Triggers.DriveStartAngry).wait_for_completed()
            
    # return to spin position to start next round
    async def afterInteraction(self):
        await self._robot.go_to_pose(self._initPose).wait_for_completed()
##        await self._robot.turn_in_place(TURN_ANGLE_AFTER_INTERACTION).wait_for_completed()
        self._newRound = True
##        await self._robot.drive_straight(distance_mm(-DISTANCE_HUMAN),
##                                         speed_mmps(STRAIGHT_SPEED),
##                                         should_play_anim=False).wait_for_completed()

    # customize speech voice pitch and length
    async def customizeSpeech(self, question):
        pitch = random.uniform(MIN_PITCH, MAX_PITCH)
        length = len(question) - question.count(' ')
        duration = log_mapping(10, MIN_DURATION, 100, MAX_DURATION, length, 10)
        return (pitch, duration)
        
    # fast spin, don't care about faces
    async def crazySpin(self):
        if self._newRound:
            t = random.uniform(MIN_CRAZY_SPIN_TIME, MAX_CRAZY_SPIN_TIME)
            await self._robot.drive_wheels(-TURN_SPEED_FAST, TURN_SPEED_FAST)
            await asyncio.sleep(t)
            self._robot.stop_all_motors()
            await asyncio.sleep(0.5)
            self._newRound = False
    
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
