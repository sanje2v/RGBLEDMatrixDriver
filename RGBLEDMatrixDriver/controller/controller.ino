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
#define SYNC_BITS_PER_SERIAL_FRAME    2   // 1 Start and 1 stop bit
#define SERIAL_FRAME_SIZE             (BITS_PER_BYTE + SYNC_BITS_PER_SERIAL_FRAME)
#define MILLIS_PER_SECOND             1000
#define MILLIS_REQUIRED_PER_FRAME     ((BITS_PER_BYTE * ONE_FRAME_SIZE * MILLIS_PER_SECOND)/SERIAL_SPEED_BPS)
#define EXTRA_MILLIS_PADDING          5

static const int CONTROLLER_SELECT_PINS[NUM_LED_MATRICES] = SLAVE_SELECT_PINS;

// Global allocation
static byte g_pFrameBuffer[MAX_FRAME_BUFFER_SIZE];
static int g_FrameBufferSize;
static uint8_t g_CurrentFrameIndex;
static SoftwareSerial SSerial(2, 3); // RX, TX


void fillFrameBufferWithDefaultPattern()
{
  const uint8_t NUM_DEFAULT_FRAMES = 12;  // CAUTION: This value should not exceed 'MAX_FRAMES'

  byte rowStates[ONE_FRAME_SIZE];
  for (uint8_t i = 0; i < NUM_DEFAULT_FRAMES; ++i)
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
          if (i < (NUM_DEFAULT_FRAMES/2))
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
  
  // Set size of frame buffer for default pattern
  g_FrameBufferSize = NUM_DEFAULT_FRAMES * ONE_FRAME_SIZE;
  
  // Point to first frame
  g_CurrentFrameIndex = 0;
}

void ClearSerialReceiveBuffer()
{
  while (SSerial.available() > 0)
    SSerial.read();
}

void setup()
{
  // Initialize random seed generator
  randomSeed(analogRead(0));
  
  // Initialize SPI for controlling LEDs and Serial for communicating with master
  SPI.begin();
  SSerial.begin(SERIAL_SPEED_BPS);
  SSerial.setTimeout(1500);

  // Configure SPI Slave Select pins as output pins and deselected slaves in SPI
  for (uint8_t i = 0; i < NUM_LED_MATRICES; ++i)
  {
    pinMode(CONTROLLER_SELECT_PINS[i], OUTPUT);
    digitalWrite(CONTROLLER_SELECT_PINS[i], HIGH);
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
  if ((g_CurrentFrameIndex + 1) == uint8_t(g_FrameBufferSize / ONE_FRAME_SIZE))
  {
    SSerial.println(F("COMPLETED"));
  }
  
  // Draw current frame
  // NOTE: We redraw each frame multiple times as we cannot use delay (as display state don't hold)
  //unsigned long start_time = millis();
  
  for (uint8_t t = 0; t < NUM_REDRAW_EACH_FRAME; ++t)
  {
    for (uint8_t i = 0; i < NUM_LED_MATRICES; ++i)
    {
      byte *pCurrentMatrixFrameBuffer = &g_pFrameBuffer[(g_CurrentFrameIndex * ONE_FRAME_SIZE) + 
                                                        (i * ONE_MATRIX_FRAME_SIZE)];
      for (uint8_t j = 0; j < NUM_ROWS_PER_MATRIX; ++j)
      {
        digitalWrite(CONTROLLER_SELECT_PINS[i], LOW);  // Select a slave LED matrix

        for (uint8_t k = 0; k < NUM_COLORS_PER_ROW_DOT; ++k)
        {
          SPI.transfer(pCurrentMatrixFrameBuffer[j * NUM_COLORS_PER_ROW_DOT + k]);
        }
        SPI.transfer(0x01 << j);  // Send row index for current LED matrix

        digitalWrite(CONTROLLER_SELECT_PINS[i], HIGH); // Deselect the selected LED matrix
      }
      
      // Explicitly need to turn off the last row of LEDs in the matrix
      // before displaying next frame so that unwanted lingering previous
      // data for last row does not remain.
      digitalWrite(CONTROLLER_SELECT_PINS[i], LOW);
      for (uint8_t k = 0; k < NUM_COLORS_PER_ROW_DOT; ++k)
      {
        SPI.transfer(LED_ROW_OFF);
      }
      SPI.transfer(0x01 << (NUM_ROWS_PER_MATRIX - 1));
      digitalWrite(CONTROLLER_SELECT_PINS[i], HIGH);
    }
  }

  //Serial.println(millis() - start_time);
  
  // Check if there is data available in Serial port from host
  if (SSerial.available() > 0)
  {
    uint8_t CurrentFrameIndex = 0;
    
    do
    {
      // Check if max frame memory has exceeded
      if (CurrentFrameIndex == MAX_FRAMES)
      {
        SSerial.println(F("ERROR: Too many frames given!"));
        CurrentFrameIndex = 0;
      }
      
      // Read a frame of data
      byte *pBuffer = &g_pFrameBuffer[CurrentFrameIndex * ONE_FRAME_SIZE];
      size_t bytesRead = SSerial.readBytes(pBuffer, ONE_FRAME_SIZE);
      if (bytesRead == ONE_FRAME_SIZE)
      {
        SSerial.println(F("OK: Received a good frame."));
      }
      else if (bytesRead == strlen(RESET_COMMAND) && 
          strncmp((const char *)pBuffer, RESET_COMMAND, strlen(RESET_COMMAND)) == 0)
      {
        // Host has asked us to reset
        SSerial.println(F("OK: Resetting."));
        
        // NOTE: We use watchdog timer to reset the system
        wdt_enable(WDTO_15MS);
        while (true) {} // Let the watchdog timer fire
      }
      else
      {
        ClearSerialReceiveBuffer();
        SSerial.println(F("ERROR: Incorrect sized frame received!"));
        SSerial.println((int)bytesRead);
        
        // We revert to default pattern
        fillFrameBufferWithDefaultPattern();
        return;
      }
      
      // Increment frame index to input new data for new frame, if it does arrive
      ++CurrentFrameIndex;
      
      // Wait to see if more data arrives
      delay(MILLIS_REQUIRED_PER_FRAME + EXTRA_MILLIS_PADDING);
    } while (SSerial.available() > 0);

    SSerial.println(F("DONE: Receive complete."));
    
    // Set new size of frame buffer
    g_FrameBufferSize = CurrentFrameIndex * ONE_FRAME_SIZE;
  
    // Reset current frame index pointer to first frame
    g_CurrentFrameIndex = 0;
  }
  else
  {
    // Increment current frame index pointer
    g_CurrentFrameIndex = (g_CurrentFrameIndex + 1) % int(g_FrameBufferSize / ONE_FRAME_SIZE);
  }
}
