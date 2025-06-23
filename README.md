# FlowVision
<p align="center">
    <img src="Deliveries/Logo.png" alt="alt text">
</p>

## Group:

- ####  Andrea Arosio &nbsp;([@andreaarooo](https://github.com/andreaarooo))<br> 10741332 &nbsp;&nbsp; andrea7.arosio@mail.polimi.it

- ####  Davide Lorenzi &nbsp;([@DavideTommy](https://github.com/DavideTommy))<br> codice Davide &nbsp;&nbsp; davide1.lorenzi@mail.polimi.it

- ####  Enrico Torres &nbsp;([@enry1897](https://github.com/enry1897))<br> 10712642 &nbsp;&nbsp; enrico.torres@mail.polimi.it

- ####  Filippo Marri &nbsp;([@filippomarri](https://github.com/filippomarri))<br> 10110508 &nbsp;&nbsp; filippo.marri@mail.polimi.it


## Project description
The main claim of our project is to create a system that allow people with visual impairments to control stage effects consciously. We use a camera to detect performers' gestures by using a machine learning algorithm to easily perform it. Then we send OSC messages to comunicate with RaspberryPi to controll a feedback glove that vibrate in different way according to the type of data that we have detected. Last step we comunicate with lights and other stage machine in order to obtain the desirable effect.

### Jupyter environment
Python --- has been used to run notebook.
Tensorflow --- is used for the machine learning part. Additionally, following libraries were also installed for some specific audio-processing tasks:

* Librosa ---
* Scikit-learn ---

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
