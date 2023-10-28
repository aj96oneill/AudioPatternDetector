# AudioPatternDetector
Python script made to listen for specific sounds and send an email notification for any detection.

This script used the sound's frequency and amplitude to match hardcoded patterns of previosuly recorded audios.

If enabled, a camera can send a picture to go along with the email for visual confirmation of the sound being detected. 

# Future Work
Ideally I would like the pattern to be uploaded from a .wav file and used to further train a neural net. Ideally it's pretrained on some other patterns and can quickly learn new patterns to classify this way. 

That approach would eliminate analyzing the fft graphs by hand and hard coding a pattern. Working with patterns of different chunk sizes and lengths of audio would be another area I hope a neural network could help.

# Set up
This script runs on a RaspberryPi with a connected usb webcam.
The webcam is being used as a mic and as a camera for this project.

A gmail account is used to send the emails from an smtp server.
