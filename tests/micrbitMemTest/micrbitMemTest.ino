const int COL1 = 3;     // Column #1 control
const int LED = 26;     // 'row 1' led
volatile boolean state = LOW;

void setup() {  
  Serial.begin(9600);
  
  Serial.println("microbit is ready!");

  // because the LEDs are multiplexed, we must ground the opposite side of the LED
  pinMode(COL1, OUTPUT);
  digitalWrite(COL1, LOW); 
   
  pinMode(LED, OUTPUT);

  pinMode(A1, OUTPUT);
  digitalWrite(A1, HIGH);

  /*const int pin = 6;
  pinMode(pin, OUTPUT);
  digitalWrite(pin, HIGH);*/

  pinMode(5, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(5), blink, CHANGE);
}

void blink()
{
  digitalWrite(LED, state);
  state = (state == LOW ? HIGH : LOW);
}

const int _delay = 1000;
void loop(){
  //Serial.println("blink!");
  
  /*digitalWrite(LED, HIGH);
  delay(_delay);
  digitalWrite(LED, LOW);
  delay(_delay);*/
}
