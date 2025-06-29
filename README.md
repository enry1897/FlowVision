# FlowVision
<p align="center">
    <img src="Deliveries/Logo.png" alt="alt text">
</p>

## Group:

- ####  Andrea Arosio &nbsp;([@andreaarooo](https://github.com/andreaarooo))<br> 10741332 &nbsp;&nbsp; andrea7.arosio@mail.polimi.it

- ####  Davide Lorenzi &nbsp;([@DavideTommy](https://github.com/DavideTommy))<br> 10502570 &nbsp;&nbsp; davide1.lorenzi@mail.polimi.it

- ####  Enrico Torres &nbsp;([@enry1897](https://github.com/enry1897))<br> 10712642 &nbsp;&nbsp; enrico.torres@mail.polimi.it

- ####  Filippo Marri &nbsp;([@filippomarri](https://github.com/filippomarri))<br> 10110508 &nbsp;&nbsp; filippo.marri@mail.polimi.it


## Project description
The main claim of our project is to create a system that allow people with visual impairments to control stage effects consciously. We use a camera to detect performers' gestures by using a machine learning algorithm to easily perform it. Then we send OSC messages to communicate with RaspberryPi to controll a feedback glove that vibrate in different way according to the type of data that we have detected. Last step we communicate with lights and other stage machine in order to obtain the desirable effect.

### Jupyter environment
Python 3.12.10 has been used to run notebooks and model.
Tensorflow 2.19.0 and Keras 3.9.2 is used for the machine learning part. Additionally, following libraries were also installed for some specific audio-processing tasks:

* h5py 3.13.0    
* imageio 2.37.0
* mediapipe 0.10.21
* numpy 1.26.4
* pyrealsense2-macosx 2.54.2

### RaspberryPi set up
The RaspberryPI communicates via GPIO ports to analog 3.3V relays. This intermediate step is needed since RaspberryPI has limited current output through GPIO ports, not enough to supply properly the small motors used for the aptic feedback. The source code of OSCServer can be opened, compiled and run with QtCreator or VSCode with QtPlugin. Is also possible to launch the executable just navigating with console into the main folder in which there is the file and launch it with the following command ./OSCServer. In order to connect the RaspberryPI bodypack and the glove is also required a standard ethernet cable with 4 twisted pairs. Please note that for the current alpha developement we used a static hardcoded IP 192.168.1.19 for RaspberryPI, and so for the OSCServer. The same is applyed to the OSCServer port. The static IP is warmly recommended. If you desire to change the IP on your RaspberryPI, a correction into code and a rebuild of the project is necessary. Further improvements on the GUI will introduce more user friendly interactions and services.

### How to start the project
 - **Preliminary step**: Make sure that the OSC receiver of the Lighting software is set on the port and IP Address written in the code
 - **Step 0**: Make sure to have created a new environment with all the requirements
 - **Step 1**: Run the C++ code using QT framework on RaspberryPi
 - **Step 2**: Plug the Intel RealSense camera to the computer that will run the code
 - **Step 3**: Run the Python code (for Mac users mandatory using sudo)
 - **Step 4**: Click on the local host link that appears on the terminal
 - **Setp 5**: Press "Avvia" button on the interface
 - **Step 6**: HAVE FUN!
 - **Final step**: If you want to close the application press "ctrl + C" on the terminal

## Classifiers Architecture
The two AI model proposed are two netowrks able to recognise two gestures.

 - **Fist gesture**: this network is implemented following a transfer learning approach. The original network adapted is MobileNet. Since the image given as input to this model have different backgrounds, a high number of parameters is required.

  - **Heart gesture**: this network is implemented following a transfer learning approach. The original network adapted is MobileNet. Since the image given as input to this model have simpler backgrounds with respect to the previous one, less parameters are required.

Below, the two architectures are reported.
<p align="center">
    <img src="Deliveries/Architectures.png" alt="alt text">
</p>

## Repository structure and file list
- *Auxiliar*:
    in this fold, the jupyter notebooks to train the neural networks are reported
    >[Fist_Neural_Net](Auxiliar/Fist_Neural_Net.ipynb)

    >[Heart_Neural_Net](Auxiliar/Heart_Neural_Net.ipynb)

## Challenges & lessons learned
