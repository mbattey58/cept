#!/usr/bin/env python3
"""  Stream raw camera frames by appending to Ceph object then extract
  individual frame, default is to capture 640x480 3 bytes per pixel.

  __author__     = "Ugo Varetto"

  Create appendable object the append individual uncompresses frames.
  Issue byte range request to extract individual frame.

  1) ./s3-rest -c credentials.json -b opencv -m put -k output1.avi
     -t"append=;position=0"
     -p ./output.avi -f -t"append=;position=0"
  2) run code, it will stop after 100 frames
  3) retrieve frame 25:
     :> start=$((25*921600+1))
     :> end=$((25*921600 + 921600))
     :> ./s3-rest -c credentials.json -b opencv  -k output1.avi \
         -e"Range:bytes=$start-$end" -n frame25.rgb
  4) convert to png:
     :> convert -size 640x480 -depth 8 RGB:frame25.rgb out.png
  5) Add meta data with information on frame format:
     ./s3-rest -c credentials.json -b opencv -k output1.avi -m put \
     -p "" -t"append=;position=92160000" \
     -e"x-amz-meta-frame-format:640x480 8 bit RGB"
  6) stat object, mute output, search for meta-data header
     ./s3-rest -c credentials.json -b opencv -k output1.avi -m head \
     -l MUTE -H "x-amz-meta-frame-format" \

    > x-amz-meta-frame-format: 640x480 8 bit RGB

 Note that it is possible to also store compressed video, but it
 requires a more complex setup with in-memory named pipes to which
 OpenCV writes data and from which data is read and streamed to Ceph."""

import s3v4_rest as s3
import requests
import json
import os
import numpy as np
import cv2
import time

if __name__ == "__main__":
    with open("./credentials.json", "r") as f:
        credentials = json.loads(f.read())

    bucket_name = "opencv"
    key_name = "output1.avi"
    pos = 0
    N = 100
    start = time.perf_counter()
    cap = cv2.VideoCapture(0)
    while(cap.isOpened() and N > 0):
        ret, frame = cap.read()
        frame_bytes = frame.tobytes()
        frame_size = len(frame_bytes)
        request_url, headers = s3.build_request_url(
            config=credentials,
            req_method="PUT",
            parameters={'append': '', 'position': str(pos)},
            payload_hash=None,
            payload_length=frame_size,
            uri_path=f"/{bucket_name}/{key_name}",
        )
        r = requests.put(request_url, data=frame_bytes, headers=headers)
        pos += frame_size
        N -= 1
    end = time.perf_counter()
    print("Elapsed time (s): " + str(end - start))
    print("Frame size (bytes): " + str(frame_size))
