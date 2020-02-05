/*
 * This code is to be executed in an Arduino. It was tested in Arduino UNO and 
 * intended to drive EP-0075 LED matrices using SPI.
 * 
 * Written by: Sanjeev Sharma. Copyright 2020.
 * https://sanje2v.wordpress.com/
 */

#include "Settings.h"
#include "SoftwareSerial.h"
#include<avr/wdt.h>
#include <SPI.h>


// Static constants
static const uint8_t LED_MATRIX_SELECT_PINS[NUM_LED_MATRICES] = _LED_MATRIX_SELECT_PINS;

// Global allocation
static char g_pStringBuffer[128];
static byte g_pFrameBuffer1[TOTAL_FRAME_BUFFER_SIZE/2];
static byte g_pFrameBuffer2[TOTAL_FRAME_BUFFER_SIZE/2];
static byte *g_pReadFrameBuffer, *g_pWriteFrameBuffer;
static uint8_t g_CurrentReadFrameIndex, g_CurrentWriteFrameIndex;
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
      byte *pCurrentMatrixFrameBuffer = &g_pReadFrameBuffer[(i * ONE_FRAME_SIZE) + (j * ONE_MATRIX_FRAME_SIZE)];
      
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

void setup()
{
  // Initialize random seed generator
  randomSeed(analogRead(0));
  
  // Initialize SPI for controlling LEDs and Serial for communicating with master
  SPI.begin();
  SSerial.begin(SERIAL_SPEED_BPS);
  SSerial.setTimeout(200);
  
  // Configure SPI Slave Select pins as output pins and deselected slaves in SPI
  for (uint8_t i = 0; i < NUM_LED_MATRICES; ++i)
  {
    pinMode(LED_MATRIX_SELECT_PINS[i], OUTPUT);
    digitalWrite(LED_MATRIX_SELECT_PINS[i], HIGH);
  }

  // Configure read and write frame buffer pointers
  g_pReadFrameBuffer = g_pFrameBuffer1;
  g_pWriteFrameBuffer = g_pFrameBuffer2;
  
  // Fill default pattern for frame buffer
  fillFrameBufferWithDefaultPattern();
  
  // Notify host that this LED controller has been initialized
  SSerial.println(F("INITIALIZED"));
}

void loop()
{
  // If this is the last frame, notify host
  // NOTE: This hint can allow the host to send next set of frames.
  if ((g_CurrentFrameIndex + 1) == TOTAL_FRAMES)
    SSerial.println(F("COMPLETED"));
  
  // Draw current frame
  #ifdef PRINT_MILLIS_PER_FRAME
  unsigned long start_time = millis();
  #endif

  // NOTE: We redraw each frame multiple times as we cannot use delay (as display state don't hold)
  for (uint8_t t = 0; t < NUM_REDRAW_EACH_FRAME; ++t)
  {
    for (uint8_t i = 0; i < NUM_LED_MATRICES; ++i)
    {
      byte *pCurrentMatrixFrameBuffer = &g_pFrameBuffer[(g_CurrentFrameIndex * ONE_FRAME_SIZE) + 
                                                        (i * ONE_MATRIX_FRAME_SIZE)];
      for (uint8_t j = 0; j < NUM_ROWS_PER_MATRIX; ++j)
      {
        digitalWrite(LED_MATRIX_SELECT_PINS[i], LOW);  // Select a slave LED matrix

        for (uint8_t k = 0; k < NUM_COLORS_PER_ROW_DOT; ++k)
        {
          SPI.transfer(pCurrentMatrixFrameBuffer[j * NUM_COLORS_PER_ROW_DOT + k]);
        }
        SPI.transfer(0x01 << j);  // Send row index for current LED matrix

        digitalWrite(LED_MATRIX_SELECT_PINS[i], HIGH); // Deselect the selected LED matrix
      }
      
      // Explicitly need to turn off the last row of LEDs in the matrix
      // before displaying next frame so that unwanted lingering previous
      // data for last row does not remain.
      digitalWrite(LED_MATRIX_SELECT_PINS[i], LOW);
      for (uint8_t k = 0; k < NUM_COLORS_PER_ROW_DOT; ++k)
      {
        SPI.transfer(LED_ROW_OFF);
      }
      SPI.transfer(0x01 << (NUM_ROWS_PER_MATRIX - 1));
      digitalWrite(LED_MATRIX_SELECT_PINS[i], HIGH);
    }
  }
  
  #ifdef PRINT_MILLIS_PER_FRAME
  sprintf_P(g_pStringBuffer, (PGM_P)F("INFO: 1 frame took %i ms."), (millis() - start_time));
  SSerial.println(g_pStringBuffer);
  #endif

  // Increment current frame index pointer
  g_CurrentFrameIndex = (g_CurrentFrameIndex + 1) % TOTAL_FRAMES;
  
  // Check if there is frame data (also could be reset command) available in Serial port from host.
  // If so, read one frame and write to next frame position.
  if (SSerial.available())
  {
    // Read a frame of data and put it in position of next frame
    byte *pBuffer = &g_pFrameBuffer[g_CurrentFrameIndex * ONE_FRAME_SIZE];
    size_t bytesRead = SSerial.readBytes(pBuffer, ONE_FRAME_SIZE);
    if (bytesRead == ONE_FRAME_SIZE)
    {
      SSerial.println(F("OK: Received a good frame."));
    }
    else if (bytesRead == strlen(RESET_COMMAND) && 
        strncmp((const char *)pBuffer, RESET_COMMAND, strlen(RESET_COMMAND)) == 0)
    {
      // Host has asked us to reset
      SSerial.println(F("INFO: Resetting..."));
      
      // NOTE: We use watchdog timer to reset the system
      wdt_enable(WDTO_15MS);
      while (true) {} // Let the watchdog timer fire
    }
    else
    {
      ClearSerialReceiveBuffer();
      sprintf_P(g_pStringBuffer,
                (PGM_P)F("ERROR: Incorrect sized frame received! Expected %i but got %i bytes instead."),
                (int)bytesRead,
                (int)ONE_FRAME_SIZE);
      SSerial.println(g_pStringBuffer);
      
      // We revert to default pattern
      fillFrameBufferWithDefaultPattern();
    }
  }
}
