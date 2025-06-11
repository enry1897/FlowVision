# FlowVision
<p align="center">
    <img src="deliveries/logo.png" alt="alt text">
</p>

## Group:

- ####  Andrea Arosio &nbsp;([@andreaarooo](https://github.com/andreaarooo))<br> 10741332 &nbsp;&nbsp; andrea7.arosio@mail.polimi.it

- ####  Davide Lorenzi &nbsp;([@DavideTommy](https://github.com/DavideTommy))<br> codice Davide &nbsp;&nbsp; davide1.lorenzi@mail.polimi.it

- ####  Enrico Torres &nbsp;([@enry1897](https://github.com/enry1897))<br> 10712642 &nbsp;&nbsp; enrico.torres@mail.polimi.it

- ####  Filippo Marri &nbsp;([@filippomarri](https://github.com/filippomarri))<br> 10110508 &nbsp;&nbsp; filippo.marri@mail.polimi.it

## Checklist

### Macrotasks
1.	Generazione delle reti neurali per riconoscimento gesti (completate 1/3) 🔄
2.	Sistema hardware (manca solo da fare il guanto) 🔄
3.	Implementazione codice gestione hardware ✅
4.	Implementazione codice comunicazione wi-fi ✅
5.	Implementazione main 
6.  Implementazione eventuale interfaccia


## Project description
The main claim of our project is to create a system that allow people with visual impairments to control stage effects consciously. We use a camera to detect performers' gestures by using a machine learning algorithm to easily perform it. Then we send OSC messages to comunicate with RaspberryPi to controll a feedback glove that vibrate in different way according to the type of data that we have detected. Last step we comunicate with lights and other stage machine in order to obtain the desirable effect.

### Jupyter environment
Python --- has been used to run notebook.
Tensorflow --- is used for the machine learning part. Additionally, following libraries were also installed for some specific audio-processing tasks:

* Librosa ---
* Scikit-learn ---

## Classifiers Architecture
The two AI model proposed 


## Repository structure and file list
- *Auxiliar*:
    in this fold, the jupyter notebooks to train the neural networks are reported
    >[Fist_Neural_Nets_Project](Auxiliar/Fist_Neural_Nets_Project.ipynb.ipynb)
