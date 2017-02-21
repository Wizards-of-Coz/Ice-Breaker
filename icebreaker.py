import cozmo
import asyncio
import Common.wochelper
from Common.woc import WOC

class IceBreaker(WOC):
    
    def __init__(self):
        _isCompleted = False

    async def run(self, coz_conn: cozmo.conn.CozmoConnection):
        await Common.wochelper.initFaceHandlers(coz_conn,
                                                self.onFaceObserved,
                                                self.onFaceAppeared,
                                                self.onFaceDisappeared)
        while True:
            await asyncio.sleep(0.1)
        

    
    async def onFaceObserved(self, evt: cozmo.faces.EvtFaceObserved, obj=None, **kwargs):
        pass

    async def onFaceAppeared(self, evt: cozmo.faces.EvtFaceAppeared, obj=None, **kwargs):
        print("Face apeared")

    async def onFaceDisappeared(self, evt: cozmo.faces.EvtFaceDisappeared, obj=None, **kwargs):
        pass


def main():
    ib = IceBreaker()
    cozmo.setup_basic_logging()
    cozmo.connect_with_tkviewer(ib.run)

if __name__ == '__main__':
    main()
