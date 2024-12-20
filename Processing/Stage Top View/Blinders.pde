public class Blinders {
    private int x;
    private int y;
    private int sizeX;
    private int sizeY;
    private int actualColor = 0;

    // Constructor
    public Blinders(int x, int y, int sizeX, int sizeY) {
        this.x = x;
        this.y = y;
        this.sizeX = sizeX;
        this.sizeY = sizeY;
    }

    // Method to draw the blinders
    public void drawBlinders() {
        rectMode(CENTER);
        stroke(255);
        fill(actualColor);
        rect(x, y, sizeX, sizeY);
    }

    // Method to change the color of the blinders when a certain condition is verified
    public void changeColor(int inputVal, int threshold) {
        if (inputVal == threshold) {
            actualColor = 255;
        } else {
            actualColor = 0;
        }
    }
}
