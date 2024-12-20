import java.util.ArrayList;
import oscP5.*;
import netP5.*;

int offsetForRectX = 150;
int offsetForRectY = 50;
int offsetForEllipse = 250;
int armPosition = 0;
int fireMachineValue = 0;
int lightValue = 0;
Light light;
Blinders leftBlinders, rightBlinders;
FireMachine fireMachine1, fireMachine2, fireMachine3, fireMachine4;
OscP5 oscP5;
NetAddress myRemoteLocation;
// ArrayList<Particle> particles;

void setup() {
    fullScreen();
    //size(800, 600);
    background(0);
    // particles = new ArrayList<Particle>();
    leftBlinders = new Blinders(0 + offsetForRectX, 0 + offsetForRectY, 200, 50);
    rightBlinders = new Blinders(width - offsetForRectX, 0 + offsetForRectY, 200, 50);
    fireMachine1 = new FireMachine(0 + offsetForEllipse, height - offsetForRectY);
    fireMachine2 = new FireMachine(width/4 + offsetForEllipse, height - offsetForRectY);
    fireMachine3 = new FireMachine(width/2 + offsetForEllipse, height - offsetForRectY);
    fireMachine4 = new FireMachine(width*3/4 + offsetForEllipse, height - offsetForRectY);
    light = new Light(width/2, 0 + offsetForRectY, 50);
    oscP5 = new OscP5(this, 7700);
    myRemoteLocation = new NetAddress("127.0.0.1", 7700);
}

void draw() {
    background(0);
    
    leftBlinders.drawBlinders();
    rightBlinders.drawBlinders();

    light.drawLight(lightValue);

    //System.out.println(fireMachineValue);
    fireMachine1.drawSmoke(fireMachineValue);
    fireMachine2.drawSmoke(fireMachineValue);
    fireMachine3.drawSmoke(fireMachineValue);
    fireMachine4.drawSmoke(fireMachineValue);

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
