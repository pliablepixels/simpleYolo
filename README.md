What
====
Dead simple python wrapper for Yolo V3 using AlexyAB's [darknet fork](https://github.com/AlexeyAB/darknet). Works with CUDA 10.1 and OpenCV 4.1 or later (I use OpenCV master as of Jun 23, 2019)

Why
====
* OpenCV's DNN module, as of today, does not support NVIDIA GPUs. There is a [GSOC WIP](https://github.com/opencv/opencv/issues/14585) that will change this. Till then, this library is what I needed.

* Other excellent libraries such as [pyyolo](https://github.com/digitalbrain79/pyyolo), [Yolo34Py](https://github.com/madhawav/YOLO3-4-Py) did not work for me with CUDA 10.1 and OpenCV 4.1. They all had compiler issues


How to use
===========
By dead simple, I mean dead simple. 

- This module doesn't bother cloning/building darknet. Build it whichever way you want, and simplxiye make `libdarknet.so` accessible to this module.
- 

See example.py

When to use/not to use
=======================
* Use this library if you want **GPU** support for YoloV3. 
* DON'T USE THIS LIBRARY if you want **CPU** support. It will work, but OpenCV's DNN module for YoloV3 is around 10x faster than using darknet directly.  Really.
- On CPU, Intel Xeon 32GB RAM, 4 core, 3.1GHz, OpenCV DNN YoloV3 with blas/atlas takes ~2-4s
- On CPU, Intel Xeon 32GB RAM, 4 core, 3.1GHz, darkneti YoloV3 takes ~45s (gaah!)
- BUT, on GPU, NVIDIA GeForce 1050 Ti, 4GB, same CPU, darknet YoloV3 takes 91ms (woot!)


If you really want to know how to get darknet working with OpenCV 4.1
========================================================================
Assuming you have built/installed CUDA/cuDNN and optionally OpenCV 4.1:

```
git clone https://github.com/AlexeyAB/darknet
cd darknet

Edit the Makefile, set:
GPU=1
CUDNN=1
```

If you want darknet to use OPENCV (not necessary), also set

```
OPENCV=1 
```
The above will only work if you previously compiled OpenCV 4+ with `OPENCV_GENERATE_PKGCONFIG=ON` and then copied the generated pc file like so: `sudo cp unix-install/opencv4.pc /usr/lib/pkgconfig/`

Pretty, please, how do we build OpenCV 4.1 with CUDA 10.1?
==============================================================

Assuming you have built/installed CUDA/cuDNN:

```
git clone https://github.com/opencv/opencv
git clone https://github.com/opencv/opencv_contrib
cd opencv
mkdir build

cmake -D CMAKE_BUILD_TYPE=RELEASE \
        -D CMAKE_INSTALL_PREFIX=/usr/local \
        -D PYTHON_DEFAULT_EXECUTABLE=$(which python3) \
        -D INSTALL_PYTHON_EXAMPLES=OFF \
        -D INSTALL_C_EXAMPLES=OFF \
        -D OPENCV_ENABLE_NONFREE=ON \
        -D OPENCV_EXTRA_MODULES_PATH=/home/pp/opencv_contrib/modules \
        -D BUILD_EXAMPLES=OFF \
        -D WITH_CUDA=ON \
        -D ENABLE_FAST_MATH=ON \
        -D CUDA_FAST_MATH=ON \
        -D WITH_CUBLAS=ON \
        -D WITH_OPENCL=ON \
        -D BUILD_opencv_cudacodec=OFF \
        -D BUILD_opencv_world=OFF \
        -D WITH_NVCUVID=OFF \
        -D WITH_OPENGL=ON \
        -D BUILD_opencv_python3=ON \
        -D OPENCV_GENERATE_PKGCONFIG=ON \
        ..
make -j$(nproc)
sudo make install

# don't forget this, for darknet and other libs to find opencv4 later
sudo cp unix-install/opencv4.pc /usr/lib/pkgconfig/

```

Pretty pretty please, how do I build CUDA 10.1 and nvidia drivers?
===================================================================
Maybe later. 

