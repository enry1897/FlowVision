# FlowVision

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



### Microtasks completate

 


### Microtasks da completare
-	Implementare il codice di pre-processing. Questo deve eseguire object detection (riconoscere la mano all’interno dell’immagine), normalisation and aligment (in modo che la mano sia inserita all’interno di un quadrato 120x120px). Il risultato sarà dato in pasto al modello_performante che dirà se la mano è chiusa o aperta.
-	Configurazione del guanto

## Description of the project
The main claim of our project is to create a system that allow people with visual impairments to control stage effects consciously. We use a camera to detect performers' gestures by using a machine learning algorithm to easily perform it. Then we send OSC messages to comunicate with RaspberryPi to controll a feedback glove that vibrate in different way according to the type of data that we have detected. Last step we comunicate with lights and other stage machine in order to obtain the desirable effect.
