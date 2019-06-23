
from timeit import default_timer as timer
from datetime import timedelta
import time

import simpleyolo.simpleYolo as yolo

configPath='./cfg/yolov3.cfg'
weightPath='./yolov3.weights'
metaPath='./cfg/coco.data'
imagePath='data/dog.jpg'

# initialize
m = yolo.SimpleYolo(configPath=configPath, 
                    weightPath=weightPath, 
                    metaPath=metaPath, 
                    darknetLib='./libdarknet_gpu.so', 
                    useGPU=True)
"""
m = yolo.SimpleYolo(configPath=configPath, 
                    weightPath=weightPath, 
                    metaPath=metaPath, 
                    darknetLib='./libdarknet_cpu.so', 
                    useGPU=False)
"""

# keep detecting
while True:
    start = timer()
    print ('detecting...')
    detections = m.detect(imagePath)
    print (detections)
    end = timer()
    print('Time to detect',timedelta(seconds=end-start))
    print ('sleeping...')
    time.sleep(4)
