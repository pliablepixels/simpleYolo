#!python3
"""
Modified https://github.com/AlexeyAB/darknet/blob/master/darknet.py to implement a dead simple
wrapper. Compile darknet however you want, just pass this the shared object to load.
Tell it to use GPU or not. That's all

- PP

Retained old notices:

On a GPU system, you can force CPU evaluation by any of:

- Set global variable DARKNET_FORCE_CPU to True
- Set environment variable CUDA_VISIBLE_DEVICES to -1
- Set environment variable "FORCE_CPU" to "true"

Original *nix 2.7: https://github.com/pjreddie/darknet/blob/0f110834f4e18b30d5f101bf8f1724c34b7b83db/python/darknet.py
Windows Python 2.7 version: https://github.com/AlexeyAB/darknet/blob/fc496d52bf22a0bb257300d3c79be9cd80e722cb/build/darknet/x64/darknet.py

@author: Philip Kahn
@date: 20180503
"""
# pylint: disable=R, W0401, W0614, W0703
from ctypes import *
import math
import random
import os

class SimpleYolo:

    def __init__(self, configPath, weightPath, metaPath, darknetLib="./libdarknet.so", useGPU=False):
        self.hasGPU = useGPU
        self.associate_with_c_lib(darknetLib)
        self.threshold = 0.25
        self.netMain = None
        self.metaMain = None
        self.altNames = None
        if not os.path.exists(configPath):
            raise ValueError("Invalid config path `" +
                             os.path.abspath(configPath)+"`")
        if not os.path.exists(weightPath):
            raise ValueError("Invalid weight path `" +
                             os.path.abspath(weightPath)+"`")
        if not os.path.exists(metaPath):
            raise ValueError("Invalid data file path `" +
                             os.path.abspath(metaPath)+"`")

        self.netMain = self.load_net_custom(configPath.encode(
            "ascii"), weightPath.encode("ascii"), 0, 1)
        self.metaMain =self.load_meta(metaPath.encode("ascii"))
        try:
            with open(metaPath) as metaFH:
                metaContents = metaFH.read()
                import re
                match = re.search("names *= *(.*)$", metaContents,
                                  re.IGNORECASE | re.MULTILINE)
                if match:
                    result = match.group(1)
                else:
                    result = None
                try:
                    if os.path.exists(result):
                        with open(result) as namesFH:
                            namesList = namesFH.read().strip().split("\n")
                            self.altNames = [x.strip() for x in namesList]
                except TypeError:
                    pass
        except Exception:
            pass

        

    def associate_with_c_lib(self, darknet_lib):
        self.lib = CDLL(darknet_lib, RTLD_GLOBAL)
        self.lib.network_width.argtypes = [c_void_p]
        self.lib.network_width.restype = c_int
        self.lib.network_height.argtypes = [c_void_p]
        self.lib.network_height.restype = c_int

        self.predict = self.lib.network_predict_ptr
        self.predict.argtypes = [c_void_p, POINTER(c_float)]
        self.predict.restype = POINTER(c_float)

        if self.hasGPU:
            self.set_gpu = self.lib.cuda_set_device
            self.set_gpu.argtypes = [c_int]

        self.make_image = self.lib.make_image
        self.make_image.argtypes = [c_int, c_int, c_int]
        self.make_image.restype = IMAGE

        self.get_network_boxes = self.lib.get_network_boxes
        self.get_network_boxes.argtypes = [c_void_p, c_int, c_int, c_float, c_float, POINTER(
            c_int), c_int, POINTER(c_int), c_int]
        self.get_network_boxes.restype = POINTER(DETECTION)

        self.make_network_boxes = self.lib.make_network_boxes
        self.make_network_boxes.argtypes = [c_void_p]
        self.make_network_boxes.restype = POINTER(DETECTION)

        self.free_detections = self.lib.free_detections
        self.free_detections.argtypes = [POINTER(DETECTION), c_int]

        self.free_ptrs = self.lib.free_ptrs
        self.free_ptrs.argtypes = [POINTER(c_void_p), c_int]

        self.network_predict = self.lib.network_predict_ptr
        self.network_predict.argtypes = [c_void_p, POINTER(c_float)]

        self.reset_rnn = self.lib.reset_rnn
        self.reset_rnn.argtypes = [c_void_p]

        self.load_net = self.lib.load_network
        self.load_net.argtypes = [c_char_p, c_char_p, c_int]
        self.load_net.restype = c_void_p

        self.load_net_custom = self.lib.load_network_custom
        self.load_net_custom.argtypes = [c_char_p, c_char_p, c_int, c_int]
        self.load_net_custom.restype = c_void_p

        self.do_nms_obj = self.lib.do_nms_obj
        self.do_nms_obj.argtypes = [POINTER(DETECTION), c_int, c_int, c_float]

        self.do_nms_sort = self.lib.do_nms_sort
        self.do_nms_sort.argtypes = [POINTER(DETECTION), c_int, c_int, c_float]

        self.free_image = self.lib.free_image
        self.free_image.argtypes = [IMAGE]

        self.letterbox_image = self.lib.letterbox_image
        self.letterbox_image.argtypes = [IMAGE, c_int, c_int]
        self.letterbox_image.restype = IMAGE

        self.load_meta = self.lib.get_metadata
        self.lib.get_metadata.argtypes = [c_char_p]
        self.lib.get_metadata.restype = METADATA

        self.load_image = self.lib.load_image_color
        self.load_image.argtypes = [c_char_p, c_int, c_int]
        self.load_image.restype = IMAGE

        self.rgbgr_image = self.lib.rgbgr_image
        self.rgbgr_image.argtypes = [IMAGE]

        self.predict_image = self.lib.network_predict_image
        self.predict_image.argtypes = [c_void_p, IMAGE]
        self.predict_image.restype = POINTER(c_float)

    def detect(self,image, thresh=.5, hier_thresh=.5, nms=.45, debug=False):
        """
        Performs the meat of the detection
        """
        #pylint: disable= C0321
        image = image.encode("ascii")
        im = self.load_image(image, 0, 0)
        if debug:
            print("Loaded image")
        ret = self.detect_image(im, thresh, hier_thresh, nms, debug)
        self.free_image(im)
        if debug:
            print("freed image")
        return ret


    def detect_image(self, im, thresh=.5, hier_thresh=.5, nms=.45, debug=False):
        meta = self.metaMain
        num = c_int(0)
        if debug:
            print("Assigned num")
        pnum = pointer(num)
        if debug:
            print("Assigned pnum")
        self.predict_image(self.netMain, im)
        if debug:
            print("did prediction")
        # dets = get_network_boxes(net, custom_image_bgr.shape[1], custom_image_bgr.shape[0], thresh, hier_thresh, None, 0, pnum, 0) # OpenCV
        dets = self.get_network_boxes(self.netMain, im.w, im.h, thresh,
                                 hier_thresh, None, 0, pnum, 0)
        if debug:
            print("Got dets")
        num = pnum[0]
        if debug:
            print("got zeroth index of pnum")
        if nms:
            self.do_nms_sort(dets, num, meta.classes, nms)
        if debug:
            print("did sort")
        res = []
        if debug:
            print("about to range")
        for j in range(num):
            if debug:
                print("Ranging on "+str(j)+" of "+str(num))
            if debug:
                print("Classes: "+str(meta), meta.classes, meta.names)
            for i in range(meta.classes):
                if debug:
                    print("Class-ranging on "+str(i)+" of " +
                          str(meta.classes)+"= "+str(dets[j].prob[i]))
                if dets[j].prob[i] > 0:
                    b = dets[j].bbox
                    if self.altNames is None:
                        nameTag = meta.names[i]
                    else:
                        nameTag = self.altNames[i]
                    if debug:
                        print("Got bbox", b)
                        print(nameTag)
                        print(dets[j].prob[i])
                        print((b.x, b.y, b.w, b.h))
                    res.append((nameTag, dets[j].prob[i], (b.x, b.y, b.w, b.h)))
        if debug:
            print("did range")
        res = sorted(res, key=lambda x: -x[1])
        if debug:
            print("did sort")
        self.free_detections(dets, num)
        if debug:
            print("freed detections")
        return res

class BOX(Structure):
    _fields_ = [("x", c_float),
                ("y", c_float),
                ("w", c_float),
                ("h", c_float)]


class DETECTION(Structure):
    _fields_ = [("bbox", BOX),
                ("classes", c_int),
                ("prob", POINTER(c_float)),
                ("mask", POINTER(c_float)),
                ("objectness", c_float),
                ("sort_class", c_int)]

class IMAGE(Structure):
    _fields_ = [("w", c_int),
                ("h", c_int),
                ("c", c_int),
                ("data", POINTER(c_float))]

class METADATA(Structure):
    _fields_ = [("classes", c_int),
                ("names", POINTER(c_char_p))]




