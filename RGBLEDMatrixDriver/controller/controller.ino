/*
 * This code is to be executed in an Arduino. It was tested in Arduino UNO and 
 * intended to drive EP-0075 LED matrices using SPI.
 * Written by: Sanjeev Sharma. Copyright 2020.
 */

#include "Settings.h"
#include "SoftwareSerial.h"
#include<avr/wdt.h>
#include <SPI.h>


// Constants
#define BITS_PER_BYTE                 8
#define SYNC_BITS_PER_SERIAL_FRAME    2   // 1 start and 1 stop bit
#define SERIAL_FRAME_SIZE             (BITS_PER_BYTE + SYNC_BITS_PER_SERIAL_FRAME)
#define MILLIS_PER_SECOND             1000
#define MILLIS_REQUIRED_PER_FRAME     ((SERIAL_FRAME_SIZE * ONE_FRAME_SIZE * uint32_t(MILLIS_PER_SECOND))/SERIAL_SPEED_BPS)

static const int LEDMATRIX_SELECT_PINS[NUM_LED_MATRICES] = SLAVE_SELECT_PINS;

// Global allocation
static char g_pStringBuffer[128];
static byte g_pFrameBuffer[TOTAL_FRAME_BUFFER_SIZE];
static uint8_t g_CurrentFrameIndex;
static SoftwareSerial SSerial(2, 3); // pins in order of (RX, TX)


void fillFrameBufferWithDefaultPattern()
{
  byte rowStates[ONE_FRAME_SIZE];
  for (uint8_t i = 0; i < TOTAL_FRAMES; ++i)
  {
    /*if (i % 3 == 0)
    {
      for (uint8_t m = 0; m < ONE_FRAME_SIZE; m += NUM_COLORS_PER_ROW_DOT)
      {
        byte rowState = (byte)random(0, 256);  // Random byte value from 0 to 255
        switch (random(3))
        {
          case 0:
            rowStates[m + 0] = rowState;
            rowStates[m + 1] = 0xFF;
            rowStates[m + 2] = 0xFF;
            break;

          case 1:
            rowStates[m + 0] = 0xFF;
            rowStates[m + 1] = rowState;
            rowStates[m + 2] = 0xFF;
            break;

          case 2:
            rowStates[m + 0] = 0xFF;
            rowStates[m + 1] = 0xFF;
            rowStates[m + 2] = rowState;
            break;
        }
      }
    }*/
    
    for (uint8_t j = 0; j < NUM_LED_MATRICES; ++j)
    {
      byte *pCurrentMatrixFrameBuffer = &g_pFrameBuffer[(i * ONE_FRAME_SIZE) + (j * ONE_MATRIX_FRAME_SIZE)];
      
      for (uint8_t k = 0; k < NUM_ROWS_PER_MATRIX; ++k)
      {
        for (uint8_t l = 0; l < NUM_COLORS_PER_ROW_DOT; ++l)
        {
          byte rowState;
          if (i < (TOTAL_FRAMES/2))
          {
            rowState = (l == 1 ? 0x00 : 0xFF);
          }
          else
          {
            rowState = (l == 2 ? 0x00 : 0xFF);
          }
          pCurrentMatrixFrameBuffer[k * NUM_COLORS_PER_ROW_DOT + l] = rowState;//rowStates[k * NUM_COLORS_PER_ROW_DOT + l];
        }
      }
    }
  }
  
  // Point to first frame
  g_CurrentFrameIndex = 0;
}

void ClearSerialReceiveBuffer()
{
  while (SSerial.available())
    SSerial.read();   // Read and drop bytes in RX buffer
}

void EnableSerialIncomingDataTimer()
{
  noInterrupts();           // disable all interrupts
  TCCR1A = 0;
  TCCR1B = 0;
  TCNT1  = 0;
  
  OCR1A = 1562;             // compare match register for 25 milliseconds
  TCCR1B |= (1 << WGM12);   // CTC mode
  TCCR1B |= (1 << CS12);    // 256 prescaler 
  TIMSK1 |= (1 << OCIE1A);  // enable timer compare interrupt
  interrupts();             // enable all interrupts
}

void DisableSerialIncomingDataTimer()
{
  TCCR1B = 0;                 // disable timer1
}

/*ISR(TIMER1_COMPA_vect)      // timer compare interrupt service routine
{
  if (SSerial.available())
  {
    DisableSerialIncomingDataTimer();
    
    uint8_t NextFrameIndex = (g_CurrentFrameIndex + (TOTAL_FRAMES/2) + 1) % TOTAL_FRAMES;
    byte * const pStartNextMatrixFrameBuffer = &g_pFrameBuffer[NextFrameIndex * ONE_FRAME_SIZE];
    byte *pNextMatrixFrameBufferPos = pStartNextMatrixFrameBuffer;

    size_t bytesRead = SSerial.readBytes(pNextMatrixFrameBufferPos, RESET_COMMAND_SIZE);
    
    // Check if host is asking us to reset
    if (bytesRead == RESET_COMMAND_SIZE &&
        strncmp((const char *)pStartNextMatrixFrameBuffer, RESET_COMMAND, RESET_COMMAND_SIZE) == 0)
    {
      // TODO: More logic needed here to make sure RESET command was sent by host.
      
      // Host has asked us to reset
      SSerial.println(F("INFO: Resetting..."));
      
      // NOTE: We use watchdog timer to reset the system
      wdt_enable(WDTO_15MS);
      while (true) {} // Let the watchdog timer fire
    }
    
    // It was NOT a reset command and IS a frame buffer data, so continue to read
    // the rest of the frame data.
    int buffer;
    
    
    for (uint8_t i = RESET_COMMAND_SIZE; i < ONE_FRAME_SIZE; ++i)
    {
      while (buffer = SSerial.read(), buffer >= 0)
      {
        *pNextMatrixFrameBufferPos = (byte)buffer;
        ++pNextMatrixFrameBufferPos;
      }
    }
    
    SSerial.println(F("OK: Received a frame."));
  }
}*/

ISR(TIMER1_COMPA_vect)      // timer compare interrupt service routine
{
  if (SSerial.available())
  {
    DisableSerialIncomingDataTimer();
    
    uint8_t NextFrameIndex = (g_CurrentFrameIndex + (TOTAL_FRAMES/2) + 1) % TOTAL_FRAMES;
    byte * const pStartNextMatrixFrameBuffer = &g_pFrameBuffer[NextFrameIndex * ONE_FRAME_SIZE];
    byte *pNextMatrixFrameBufferPos = pStartNextMatrixFrameBuffer;
    int buffer;
    for (uint8_t i = 0; i < RESET_COMMAND_SIZE; ++i)
    {
      while (buffer = SSerial.read(), buffer < 0);
      
      *pNextMatrixFrameBufferPos = (byte)buffer;
      ++pNextMatrixFrameBufferPos;
    }
    
    // Check if host is asking us to reset
    if (strncmp((const char *)pStartNextMatrixFrameBuffer, RESET_COMMAND, RESET_COMMAND_SIZE) == 0)
    {
      // TODO: More logic needed here to make sure RESET command was sent by host.
      
      // Host has asked us to reset
      SSerial.println(F("INFO: Resetting..."));
      
      // NOTE: We use watchdog timer to reset the system
      wdt_enable(WDTO_15MS);
      while (true) {} // Let the watchdog timer fire
    }
    
    // It was NOT a reset command and IS a frame buffer data, so continue to read
    // the rest of the frame data.
    for (uint8_t i = RESET_COMMAND_SIZE; i < ONE_FRAME_SIZE; ++i)
    {
      while (buffer = SSerial.read(), buffer < 0);
      
      *pNextMatrixFrameBufferPos = (byte)buffer;
      ++pNextMatrixFrameBufferPos;
    }
    
    SSerial.println(F("OK: Received a frame."));
  }
}

void setup()
{
  // Initialize random seed generator
  randomSeed(analogRead(0));
  
  // Initialize SPI for controlling LEDs and Serial for communicating with master
  SPI.begin();
  SSerial.begin(SERIAL_SPEED_BPS);
  //SSerial.setTimeout(200);
  
  // Configure SPI Slave Select pins as output pins and deselected slaves in SPI
  for (uint8_t i = 0; i < NUM_LED_MATRICES; ++i)
  {
    pinMode(LEDMATRIX_SELECT_PINS[i], OUTPUT);
    digitalWrite(LEDMATRIX_SELECT_PINS[i], HIGH);
  }
  
  // Fill default pattern for frame buffer
  fillFrameBufferWithDefaultPattern();
  
  // Notify host that this LED controller has been initialized
  SSerial.println(F("INITIALIZED"));
}

void loop()
{
  // If this is the last frame, notify host
  // NOTE: This hint can allow the host to send next set of frames.
  if ((g_CurrentFrameIndex + 1) == (TOTAL_FRAMES/2))
    SSerial.println(F("SYNC"));
  
  // Draw current frame
  EnableSerialIncomingDataTimer();
  
  // NOTE: We redraw each frame multiple times as we cannot use delay (as display state don't hold)
  #ifdef PRINT_MILLIS_PER_FRAME
  unsigned long start_time = millis();
  #endif
  
  for (uint8_t t = 0; t < NUM_REDRAW_EACH_FRAME; ++t)
  {
    for (uint8_t i = 0; i < NUM_LED_MATRICES; ++i)
    {
      byte *pCurrentMatrixFrameBuffer = &g_pFrameBuffer[(g_CurrentFrameIndex * ONE_FRAME_SIZE) + 
                                                        (i * ONE_MATRIX_FRAME_SIZE)];
      for (uint8_t j = 0; j < NUM_ROWS_PER_MATRIX; ++j)
      {
        digitalWrite(LEDMATRIX_SELECT_PINS[i], LOW);  // Select a slave LED matrix

        for (uint8_t k = 0; k < NUM_COLORS_PER_ROW_DOT; ++k)
        {
          SPI.transfer(pCurrentMatrixFrameBuffer[j * NUM_COLORS_PER_ROW_DOT + k]);
        }
        SPI.transfer(0x01 << j);  // Send row index for current LED matrix

        digitalWrite(LEDMATRIX_SELECT_PINS[i], HIGH); // Deselect the selected LED matrix
      }
      
      // Explicitly need to turn off the last row of LEDs in the matrix
      // before displaying next frame so that unwanted lingering previous
      // data for last row does not remain.
      digitalWrite(LEDMATRIX_SELECT_PINS[i], LOW);
      for (uint8_t k = 0; k < NUM_COLORS_PER_ROW_DOT; ++k)
      {
        SPI.transfer(LED_ROW_OFF);
      }
      SPI.transfer(0x01 << (NUM_ROWS_PER_MATRIX - 1));
      digitalWrite(LEDMATRIX_SELECT_PINS[i], HIGH);
    }
  }
  
  #ifdef PRINT_MILLIS_PER_FRAME
  sprintf_P(g_pStringBuffer, (PGM_P)F("INFO: 1 frame took %i ms."), (millis() - start_time));
  SSerial.println(g_pStringBuffer);
  #endif
  
  DisableSerialIncomingDataTimer();
  
  // Increment current frame index pointer
  g_CurrentFrameIndex = (g_CurrentFrameIndex + 1) % TOTAL_FRAMES;
}
