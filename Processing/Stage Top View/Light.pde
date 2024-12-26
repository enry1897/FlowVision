public class Light {
    private int x;
    private int y;
    private int radius;

    // Constructor
    public Light(int x, int y, int radius) {
        this.x = x;
        this.y = y;
        this.radius = radius;
    }

    // Method to draw the light
    public void drawLight(int inputVal) {
        ellipseMode(CENTER);
        if (inputVal == 1) {
            noStroke();
            fill(255, 0, 0);
        } else {
            noStroke();
            fill(255);
        }
        ellipse(x, y, radius, radius);
    }

    // Method that changes the color of the light and the radius of all the lights
    public void changeColor() {
        
    }
}
