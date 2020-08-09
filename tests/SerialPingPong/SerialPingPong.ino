static bool HostReady;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200, SERIAL_8N1);
  Serial.setTimeout(1);
  while(Serial.read() > -1);

  HostReady = false;
}

void loop() {
  int data = Serial.read();
    if (data > -1)
    {
      Serial.write(data);
    }
}

/*void loop() {
  if (!HostReady)
  {
    auto command = Serial.readStringUntil('\n');
    if (command.startsWith("READY"))
    {
      HostReady = true;
      Serial.println(F("INFO: Got READY"));
    }
  }
  else
  {
    auto timeit = millis();
    Serial.println(F("READY"));
  
    while (millis() - timeit < 300)
    {
      int data = Serial.read();
      if (data > -1)
      {
        Serial.write(data);
      }
    }
  
    noInterrupts();
    delayMicroseconds(200 * 1000);
    interrupts();
  }
}*/
