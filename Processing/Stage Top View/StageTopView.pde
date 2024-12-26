import oscP5.*;
import netP5.*;

int offsetForRectX = 150;
int offsetForRectY = 50;
int offsetForEllipse = 250;
int lightRadius = 300;
int centerX;
int centerY;
Blinders leftBlinders, rightBlinders;
FireMachine fireMachine1, fireMachine2, fireMachine3, fireMachine4;
Light[] lights;
int armPosition = 0;
int fireMachineValue = 0;
int lightValue = 0;
OscP5 oscP5;
NetAddress myRemoteLocation;
int numberOfLights = 16;

void setup() {
    fullScreen();
    // size(800, 600);
    background(0);
    leftBlinders = new Blinders(0 + offsetForRectX, height - offsetForRectY, 200, 50);
    rightBlinders = new Blinders(width - offsetForRectX, height - offsetForRectY, 200, 50);
    fireMachine1 = new FireMachine(0 + offsetForEllipse, 0 + offsetForRectY, 50);
    fireMachine2 = new FireMachine(width/4 + offsetForEllipse, 0 + offsetForRectY, 50);
    fireMachine3 = new FireMachine(width/2 + offsetForEllipse, 0 + offsetForRectY, 50);
    fireMachine4 = new FireMachine(width*3/4 + offsetForEllipse, 0 + offsetForRectY, 50);
    lights = new Light[numberOfLights];
    centerX = width/2;
    centerY = height/2;
    oscP5 = new OscP5(this, 7700);
    myRemoteLocation = new NetAddress("127.0.0.1", 7700);
}

void draw() {
    background(0);
    
    leftBlinders.drawBlinders();
    rightBlinders.drawBlinders();

    fireMachine1.drawFireMachine();
    fireMachine2.drawFireMachine();
    fireMachine3.drawFireMachine();
    fireMachine4.drawFireMachine();

    for (int i = 0; i < numberOfLights; i++) {
        float angle = TWO_PI / numberOfLights * i;

        int x = round(centerX + cos(angle) * lightRadius);
        int y = round(centerY + sin(angle) * lightRadius);

        lights[i] = new Light(x, y, 50);
        lights[i].drawLight(lightValue);
    }

    if (lightValue == 1) {
            fill(255, 0, 0);
            if(lightRadius > 100){
                lightRadius--;
            }
        } else {
            fill(255);
            if(lightRadius < 300){
                lightRadius++;
            }
        }
    
    // System.out.println(lightRadius);

    leftBlinders.changeColor(armPosition, 1);
    rightBlinders.changeColor(armPosition, 1);
}

void oscEvent(OscMessage theOscMessage) {
    if (theOscMessage.checkAddrPattern("/blinders")) {
        armPosition = theOscMessage.get(0).intValue();
    } else if (theOscMessage.checkAddrPattern("/fireMachine")) {
        fireMachineValue = theOscMessage.get(0).intValue();
    } else if (theOscMessage.checkAddrPattern("/lights")) {
        lightValue = theOscMessage.get(0).intValue();
    }
}
   
