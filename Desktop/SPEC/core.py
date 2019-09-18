from picamera.array import PiRGBArray
from picamera import PiCamera
from utils import send_email, TempImage
import argparse
import warnings
import datetime
import json
import time
import cv2

ap = argparse.ArgumentParser()
ap.add_argument("-c", "--conf", required=True,
	help="path to the JSON configuration file")
ap.add_argument("-d", "--debug", required=False,
	help="debug mode on/off")
args = vars(ap.parse_args())

warnings.filterwarnings("ignore")
conf = json.load(open(args["conf"]))
client = None

if args['debug']:
	print(' > Debug mode is on !')
	debug_mode = True
else:
	debug_mode = False

camera = PiCamera()
camera.resolution = tuple(conf["resolution"])
camera.framerate = conf["fps"]
rawCapture = PiRGBArray(camera, size=tuple(conf["resolution"]))

print "[INFO] warming up..."
time.sleep(conf["camera_warmup_time"])
avg = None
lastUploaded = datetime.datetime.now()
motionCounter = 0
print('[INFO] Camera started !!')

for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
	frame = f.array
	timestamp = datetime.datetime.now()
	text = "None"

        # COMPUTER VISION
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, tuple(conf['blur_size']), 0)

	if avg is None:
		print "[INFO] starting background model..."
		avg = gray.copy().astype("float")
		rawCapture.truncate(0)
		continue

	frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))
	cv2.accumulateWeighted(gray, avg, 0.5)

	thresh = cv2.threshold(frameDelta, conf["delta_thresh"], 255,
		cv2.THRESH_BINARY)[1]
	thresh = cv2.dilate(thresh, None, iterations=2)
	im2 ,cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)

	for c in cnts:
		if cv2.contourArea(c) < conf["min_area"]:
			continue
		(x, y, w, h) = cv2.boundingRect(c)
		cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
		text = "Detected"

	ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
	cv2.putText(frame, "Status: {}".format(text), (10, 20),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
	cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
		0.35, (0, 0, 255), 1)

	if text == "Detected":
                cv2.imwrite("/home/pi/tmp/SPEC_{}.jpg".format(motionCounter), frame);
                if (timestamp - lastUploaded).seconds >= conf["min_upload_seconds"]:
                        motionCounter += 1;
                        if motionCounter >= int(conf["min_motion_frames"]):
                                if conf["use_email"]:
                                        print("[INFO] Sending an alert email!!!")
                                        send_email(conf)
                                        print("[INFO] waiting {} seconds...".format(conf["camera_warmup_time"]))
                                        time.sleep(conf["camera_warmup_time"])
                                        print("[INFO] running")
                                lastUploaded = timestamp
                                motionCounter = 0
	else:
		motionCounter = 0
	if conf["show_video"]:
		cv2.imshow("Security Feed", frame)
		key = cv2.waitKey(1) & 0xFF

		if debug_mode:
			cv2.imshow('Debug blurred gray frame', gray)
			cv2.imshow('Debug threshold frame', thresh)
		if key == ord("q"):
			break
	rawCapture.truncate(0)
