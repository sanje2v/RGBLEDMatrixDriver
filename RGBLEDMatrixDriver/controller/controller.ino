/*
 * This code is to be executed in an Arduino. It was tested in Arduino UNO and 
 * intended to drive EP-0075 LED matrices using SPI.
 * Written by: Sanjeev Sharma. Copyright 2020.
 */

#include "Settings.h"
#include<avr/wdt.h>
#include <SPI.h>


// Constants
#define BITS_PER_BYTE                 8
#define SYNC_BITS_PER_SERIAL_FRAME    2   // 1 start and 1 stop bit
#define SERIAL_FRAME_SIZE             (BITS_PER_BYTE + SYNC_BITS_PER_SERIAL_FRAME)
#define MILLIS_PER_SECOND             1000
#define MILLIS_REQUIRED_PER_FRAME     ((SERIAL_FRAME_SIZE * ONE_FRAME_SIZE * uint32_t(MILLIS_PER_SECOND))/SERIAL_SPEED_BPS)
#define SerialToHost                  Serial

static const int LEDMATRIX_SELECT_PINS[NUM_LED_MATRICES] = _LEDMATRIX_SELECT_PINS;

// Global allocation
static char g_pStringBuffer[128];
static byte g_pFrameBuffer[TOTAL_FRAME_BUFFER_SIZE];
static uint8_t g_CurrentFrameIndex;
static uint16_t g_NextFrameBufferWriteBytePos;
static bool g_bResetNow;


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
  while (SerialToHost.available())
    SerialToHost.read();   // Read and drop bytes in RX buffer
}

void setup()
{
  // Initialize random seed generator
  randomSeed(analogRead(0));
  
  // Initialize SPI for controlling LEDs and Serial for communicating with master
  SPI.begin();
  SerialToHost.begin(SERIAL_SPEED_BPS);
  //SerialToHost.setTimeout(200);
  
  // Configure SPI Slave Select pins as output pins and deselected slaves in SPI
  for (uint8_t i = 0; i < NUM_LED_MATRICES; ++i)
  {
    pinMode(LEDMATRIX_SELECT_PINS[i], OUTPUT);
    digitalWrite(LEDMATRIX_SELECT_PINS[i], HIGH);
  }
  
  // Fill default pattern for frame buffer
  fillFrameBufferWithDefaultPattern();

  // Set position of next write buffer
  g_NextFrameBufferWriteBytePos = (TOTAL_FRAME_BUFFER_SIZE - ONE_FRAME_SIZE);

  // Properly set do reset flag
  g_bResetNow = false;
  
  // Notify host that this LED controller has been initialized
  ClearSerialReceiveBuffer();
  SerialToHost.println(F("INITIALIZED"));
}

inline void ReadSerialWriteToFrameBuffer()
{
  if (SerialToHost.available())
  {
    int readBuffer;
    uint8_t bytesRead = 0;
    while (readBuffer = SerialToHost.read(), readBuffer >= 0)
    {
      g_pFrameBuffer[g_NextFrameBufferWriteBytePos] = (byte)readBuffer;
      g_NextFrameBufferWriteBytePos = (g_NextFrameBufferWriteBytePos + 1) % TOTAL_FRAME_BUFFER_SIZE;
      
      ++bytesRead;
    }

    byte *const pStartFrameBufferPos = &g_pFrameBuffer[g_NextFrameBufferWriteBytePos - (g_NextFrameBufferWriteBytePos % ONE_FRAME_SIZE)];
    if (strncmp((const char *)pStartFrameBufferPos, RESET_COMMAND, RESET_COMMAND_SIZE) == 0)
    {
      // We will reset in the next invocation of this function when
      // some time has elasped and no more data is given
      g_bResetNow = true;
    }

    if ((g_NextFrameBufferWriteBytePos % ONE_FRAME_SIZE) == 0)
      SerialToHost.println(F("OK: Received a frame."));
  }
  else if (g_bResetNow)
  {
    // Host has asked us to reset
    SerialToHost.println(F("INFO: Resetting..."));
    
    // NOTE: We use watchdog timer to reset the system
    wdt_enable(WDTO_15MS);
    while (true) {} // Let the watchdog timer fire
  }
}

void loop()
{
  // If this is the last frame, notify host
  // NOTE: This hint can allow the host to send next set of frames.
  if ((g_CurrentFrameIndex + 1) == TOTAL_FRAMES)
    SerialToHost.println(F("COMPLETED"));

  // Draw current frame
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

    ReadSerialWriteToFrameBuffer();
  }
  
  #ifdef PRINT_MILLIS_PER_FRAME
  sprintf_P(g_pStringBuffer, (PGM_P)F("INFO: 1 frame took %i ms."), (millis() - start_time));
  SerialToHost.println(g_pStringBuffer);
  #endif
  
  // Check if there is data available in Serial port from host and if so record it
  //ReadSerialWriteToFrameBuffer();
  
  // Increment current frame index pointer
  g_CurrentFrameIndex = (g_CurrentFrameIndex + 1) % TOTAL_FRAMES;
}
